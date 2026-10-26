"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    모델 임계값 — 점수 → 라벨 규칙, 그래프 범위와 분포, 점수 맵 보관 (Qt 사용 안 함).

    ── modelThreshold ───────────────────────────────────────────
    모델(DSAD) 점수 맵 ↔ 라벨 변환과 임계값 규칙. 점수 >= 임계값이면 비정상(3), 아니면 정상(2).
    적용 규칙(ApplyRule)이 한쪽만 적용하라고 하면 다른 쪽은 0(라벨 없음).
        - 표시 및 적용: 자동이 켜져 있으면 이미지의 case 로 어느 쪽 라벨을 적용할지 정한다(case 묶음은
          autoLabelConfig 의 *_DATA_CASES, 폴더 이름 → case 는 trainingPlan). 꺼져 있으면 적용 체크 그대로.
        - 자동 임계값: 학습 이미지 점수를 합쳐 한 번만 계산해 모델에 고정한다. 이미지마다 다시 계산하면
          이물이 없는 이미지에서도 무언가를 잘라 과검이 난다.
        - 불확실: 임계값 주변 분위수 구간의 픽셀. 보여주기 전용이라 라벨, 학습에 쓰지 않는다.

    ── thresholdScale ───────────────────────────────────────────
    임계값 칸(그래프, 슬라이더)의 범위와 분포 곡선 계산. 유사도는 고정 범위, 모델은 점수 분포와 임계값에서
    둥근 끝값을 구하고, 범위 밖 값을 넣으면 범위를 늘린다.

    ── scoreMapStore ────────────────────────────────────────────
    추론한 이미지의 점수 맵 보관소(메모리에만). 이미지마다 라벨을 만들 때 쓴 임계값, 적용 규칙, 바탕 라벨도 같이 둔다 —
    '지금의 기본 임계값' 으로 잠금을 판정하면 한 이미지에서 임계값을 바꾸는 순간 다른 이미지가 모두 '고친 것' 으로 보여 잠긴다.
    모델이 바뀌거나 이미지를 지우면 비운다. 키는 이미지 폴더 경로(imageKey).
"""

import dataclasses
import math
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Dict

import numpy as np
from skimage.filters import threshold_otsu, threshold_yen

from autolabel.autoLabelConfig import (ABNORMAL_DATA_CASES, BACKGROUND_DATA_CASES, LABEL_BACKGROUND, LABEL_ABNORMAL,
                                       LABEL_IGNORED, LABEL_NORMAL, PRODUCT_DATA_CASES, UNCERTAIN_QUANTILE_HALF_WIDTH,
                                       imageKey)


@dataclass(frozen=True)
class ApplyRule:
    """이 이미지에 어느 쪽 라벨을 적용하는가."""
    applyNormal: bool = True
    applyAbnormal: bool = True
    applyBackground: bool = True


def applyRuleForImage(caseNumber: Optional[int], useAutoApply: bool, applyNormal: bool, applyAbnormal: bool,
                      applyBackground: bool = True) -> ApplyRule:
    """이미지 하나의 적용 규칙. caseNumber 는 case 밖이면 None, 자동이 꺼져 있으면 적용 체크를 그대로 쓴다."""
    if useAutoApply and caseNumber in BACKGROUND_DATA_CASES:
        return ApplyRule(applyNormal=False, applyAbnormal=False, applyBackground=True)
    if useAutoApply and caseNumber in PRODUCT_DATA_CASES:
        return ApplyRule(applyNormal=True, applyAbnormal=False, applyBackground=False)
    if useAutoApply and caseNumber in ABNORMAL_DATA_CASES:
        return ApplyRule(applyNormal=False, applyAbnormal=True, applyBackground=False)
    if useAutoApply:                                  # case 밖 — 배경은 모델이 못 가른다
        return ApplyRule(applyNormal=True, applyAbnormal=True, applyBackground=False)
    return ApplyRule(applyNormal=applyNormal, applyAbnormal=applyAbnormal, applyBackground=applyBackground)


def computeAutoThreshold(scoreMaps: Iterable[np.ndarray]) -> float:
    """점수 맵들을 합쳐 max(otsu, yen) 임계값(원래 점수 스케일)을 구한다. 두 무리로 가를 수 없으면 ValueError."""
    values = np.concatenate([np.asarray(scoreMap, dtype=np.float64).ravel() for scoreMap in scoreMaps])
    values = values[np.isfinite(values)]
    if values.size == 0 or np.unique(values).size < 2:
        raise ValueError("점수가 비었거나 값이 하나뿐이라 자동 임계값을 계산할 수 없다")
    logValues = np.log1p(np.clip(values, 0, None))        # 점수 꼬리가 길어 원래 스케일의 otsu 는 한쪽으로 쏠린다
    otsuThreshold = float(np.expm1(threshold_otsu(logValues)))
    yenThreshold = float(np.expm1(threshold_yen(logValues)))
    return max(otsuThreshold, yenThreshold)


def labelFromScore(scoreMap: np.ndarray, threshold: float, rule: ApplyRule = ApplyRule(),
                   productMask: Optional[np.ndarray] = None) -> np.ndarray:
    """점수 맵 → 라벨. productMask 는 SAL 결과의 원물 여부(모델 결과는 None). 적용하지 않는 쪽은 0.
    비교를 float32 로 하는 것은 저장할 때와 잠금 판정 때 같은 결과를 내려는 것."""
    isAbnormal = np.asarray(scoreMap, dtype=np.float32) >= np.float32(threshold)
    isNormal = ~isAbnormal
    label = np.full(isAbnormal.shape, LABEL_IGNORED, dtype=np.int64)
    if rule.applyAbnormal:
        label[isAbnormal] = LABEL_ABNORMAL
    if productMask is None:                       # 모델 결과는 원물, 배경을 못 가른다
        if rule.applyNormal:
            label[isNormal] = LABEL_NORMAL
        elif rule.applyBackground:
            label[isNormal] = LABEL_BACKGROUND
        return label
    if rule.applyNormal:
        label[isNormal & productMask] = LABEL_NORMAL
    if rule.applyBackground:
        label[isNormal & ~productMask] = LABEL_BACKGROUND
    return label


def overlayInferred(baseLabel: Optional[np.ndarray], inferred: np.ndarray) -> np.ndarray:
    """추론이 값을 낸 픽셀(0 이 아님)만 쓰고 나머지는 기존 라벨 그대로. baseLabel 이 None 이면 전부 덮어쓴다.
    전부 덮어쓰면 초기 라벨이 사라져 그 이미지를 재학습에 쓸 수 없다."""
    if baseLabel is None:
        return inferred
    return np.where(inferred != LABEL_IGNORED, inferred, baseLabel).astype(np.int64)


def isLabelInferenceResult(label: np.ndarray, scoreMap: np.ndarray, threshold: float, rule: ApplyRule = ApplyRule(),
                           baseLabel: Optional[np.ndarray] = None) -> bool:
    """현재 라벨이 점수 맵, 임계값, 적용 규칙으로 만든 라벨(baseLabel 위에 얹은 것)과 같은가. 임계값 조절 가능 여부의 기준.
    되돌리기 기록은 개수 제한으로 잘려 믿을 수 없어 직접 비교한다."""
    if baseLabel is not None and baseLabel.shape != scoreMap.shape:
        return False
    return bool(np.array_equal(label, overlayInferred(baseLabel, labelFromScore(scoreMap, threshold, rule))))


def uncertainMask(scoreMap: np.ndarray, threshold: float, halfWidth: float = UNCERTAIN_QUANTILE_HALF_WIDTH) -> np.ndarray:
    """임계값의 분위수 ±halfWidth 안에 드는 픽셀(H, W bool). 보여주기 전용."""
    values = np.asarray(scoreMap, dtype=np.float32)
    quantileOfThreshold = float((values < np.float32(threshold)).mean())
    lowScore = np.quantile(values, max(0.0, quantileOfThreshold - halfWidth))
    highScore = np.quantile(values, min(1.0, quantileOfThreshold + halfWidth))
    return (values >= lowScore) & (values <= highScore)


SIMILARITY_RANGE = (0.0, 100.0)
MODEL_RANGE_QUANTILE = 0.995
MODEL_RANGE_THRESHOLD_FACTOR = 2.0
OUT_OF_RANGE_FACTOR = 1.25
NICE_STEPS = (1.0, 2.0, 5.0, 10.0)
CURVE_BINS = 60
CURVE_SMOOTH_WINDOW = 3


def niceCeil(value: float) -> float:
    """value 이상인 가장 작은 '둥근 수'(1, 2, 5 × 10^n)."""
    if not math.isfinite(value) or value <= 0:       # 슬롯 안 예외는 앱을 끝내므로 기본 크기로
        return 1.0
    exponent = math.floor(math.log10(value))
    for step in NICE_STEPS:
        candidate = step * 10 ** exponent
        if candidate >= value - 1e-12:
            return candidate
    return 10 ** (exponent + 1)


def modelBaseRange(scores: Optional[np.ndarray], threshold: float) -> Tuple[float, float]:
    """모델 탭의 기본 범위(점수 분포와 임계값 기준, 점수가 없으면 임계값만)."""
    end = threshold * MODEL_RANGE_THRESHOLD_FACTOR if math.isfinite(threshold) else 0.0
    if scores is not None and scores.size:
        finite = scores[np.isfinite(scores)]
        if finite.size:
            end = max(end, float(np.quantile(finite, MODEL_RANGE_QUANTILE)))
    return 0.0, niceCeil(end)


def rangeIncluding(baseRange: Tuple[float, float], value: float) -> Tuple[float, float]:
    """값이 기본 범위 밖이면 그 값을 담도록 늘린다."""
    low, high = baseRange
    if not math.isfinite(value) or value <= high:
        return baseRange
    return low, niceCeil(value * OUT_OF_RANGE_FACTOR)


def sortedFinite(scores: Optional[np.ndarray]) -> Optional[np.ndarray]:
    """유한한 점수만 정렬해 둔다(densityCurve 의 isSorted 입력)."""
    if scores is None:
        return None
    finite = scores[np.isfinite(scores)]
    return np.sort(finite) if finite.size else None


def densityCurve(scores: Optional[np.ndarray], valueRange: Tuple[float, float], bins: int = CURVE_BINS,
                 clipToRange: bool = True, isSorted: bool = False) -> Optional[np.ndarray]:
    """분포 곡선 높이(0~1). 점수가 없으면 None.
    clipToRange=True 는 범위 밖 점수를 끝 칸에 모으고, False(좁은 구간)는 뺀다. 높이는 제곱근으로 눌러 큰 덩어리가 작은 덩어리를 가리지 않게 한다.
    isSorted=True 는 scores 가 sortedFinite 결과라는 뜻(같은 결과를 이진 탐색으로 빨리 센다)."""
    if scores is None or scores.size == 0:
        return None
    low, high = valueRange
    if isSorted:
        edges = np.linspace(low, high, bins + 1).astype(scores.dtype)
        positions = np.searchsorted(scores, edges, side="left")
        positions[-1] = np.searchsorted(scores, edges[-1], side="right")     # np.histogram 처럼 마지막 칸은 끝값 포함
        counts = np.diff(positions)
        if clipToRange and counts.size:
            counts[0] += positions[0]
            counts[-1] += scores.size - positions[-1]
    else:
        finite = scores[np.isfinite(scores)]
        if finite.size == 0:
            return None
        counts, _ = np.histogram(np.clip(finite, low, high) if clipToRange else finite, bins=bins, range=(low, high))
    kernel = np.ones(CURVE_SMOOTH_WINDOW) / CURVE_SMOOTH_WINDOW
    smoothed = np.sqrt(np.convolve(counts.astype(np.float64), kernel, mode="same"))
    peak = smoothed.max()
    return smoothed / peak if peak > 0 else smoothed


@dataclass(frozen=True)
class StoredScoreMap:
    """점수 맵과, 지금 이 이미지 라벨을 만든 임계값, 적용 규칙, 바탕 라벨(None = 전부 덮어쓰기)."""
    scoreMap: np.ndarray
    threshold: float
    rule: ApplyRule
    baseLabel: Optional[np.ndarray] = None

    def labelAt(self, threshold: float, rule: Optional[ApplyRule] = None) -> np.ndarray:
        """같은 점수 맵, 바탕으로 threshold 에서 만든 라벨. rule 을 안 주면 이 라벨을 만든 규칙."""
        return overlayInferred(self.baseLabel, labelFromScore(self.scoreMap, threshold, rule or self.rule))

    def isLabelAt(self, label: np.ndarray, threshold: float) -> bool:
        return isLabelInferenceResult(label, self.scoreMap, threshold, self.rule, self.baseLabel)


class ScoreMapStore:
    """이미지 경로 → StoredScoreMap. 기록은 바꿀 수 없는 값이라 바꿀 때 새 기록으로 갈아 끼운다."""

    def __init__(self):
        self._entries: Dict[str, StoredScoreMap] = {}

    def put(self, imageFolderPath: str, scoreMap: np.ndarray, threshold: float, rule: ApplyRule,
            baseLabel: Optional[np.ndarray] = None) -> None:
        """추론 결과를 넣는다(같은 이미지면 덮어쓴다). 복사본으로 보관해 부른 쪽이 원본을 고쳐도 영향이 없다."""
        base = None if baseLabel is None else np.array(baseLabel, dtype=np.int16, copy=True)
        self._entries[imageKey(imageFolderPath)] = StoredScoreMap(np.array(scoreMap, dtype=np.float32, copy=True),
                                                                  float(threshold), rule, base)

    def get(self, imageFolderPath: str) -> Optional[StoredScoreMap]:
        """없으면 None."""
        return self._entries.get(imageKey(imageFolderPath))

    def updateLabelSource(self, imageFolderPath: str, threshold: float, rule: ApplyRule) -> None:
        """임계값 조절로 라벨을 다시 만들었을 때 그 이미지의 기록만 바꾼다. 점수 맵이 없으면 KeyError."""
        key = imageKey(imageFolderPath)
        self._entries[key] = dataclasses.replace(self._entries[key], threshold=float(threshold), rule=rule)

    def keepOnly(self, imageKeys) -> None:
        """목록에 남은 이미지(키)만 남긴다."""
        self._entries = {key: entry for key, entry in self._entries.items() if key in imageKeys}

    def clear(self) -> None:
        """모델이 바뀌었을 때, 이미지를 모두 지웠을 때."""
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
