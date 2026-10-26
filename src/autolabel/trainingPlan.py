"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    학습, 일괄 추론 계획 — 학습 픽셀 고르기, 폴더 이름으로 case 판단 (Qt 사용 안 함).

    ── trainingPlan ─────────────────────────────────────────────
    어떤 이미지의 어떤 픽셀로 DSAD 를 학습할지 정한다(학습 자체는 dsadModel).
        - 라벨 픽셀 수(배경, 원물, 이물)를 세어 학습 조건(바 세그먼트) 판정에 쓴다. 최소값은 autoLabelConfig 의 TRAINING_MIN_*.
        - 학습 대상 = 대상 case(autoLabelConfig 의 TRAINING_CASE, TRAINING_EXTRA_CASES) 중 디스크에 저장된 라벨이 있고
          검토 전 추론 라벨이 아닌 이미지(사람이 확인하지 않은 모델 출력을 다시 배우면 자기 실수를 정답으로 배운다).
          고르는 코드는 autoLabelController._trainingKeys.
        - 학습 픽셀은 라벨링 DB 의 큐브(image_raw)에서 뽑는다. 클래스별 상한을 넘으면 고정 씨앗으로 무작위 추출해 학습 데이터가 커지는 것을 막는다.

    ── caseRules ────────────────────────────────────────────────
    일괄 추론의 case 규칙 — 이미지 상위 폴더 이름으로 case 를 정하고 일괄 추론 가능 여부를 판단한다.
        - 필수 case 가 모두 있어야 일괄 추론을 할 수 있다(상수는 autoLabelConfig). 없으면 버튼을 끄고 빠진 case 를 알려 준다.
        - case 밖 이미지는 시작 전에 포함 여부를 사용자에게 묻는다.
        - 현재 선택된 이미지도 대상에 들어간다.
        - 폴더 이름 해석은 caseNumberFromFolderName.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple, List

import numpy as np

from autolabel.autoLabelConfig import (ABNORMAL_LABEL_MIN, LABEL_BACKGROUND, LABEL_NORMAL, SAL_CASE,
                                       TRAINING_MAX_PIXELS_PER_CLASS, TRAINING_MIN_ABNORMAL_PIXELS, TRAINING_SAMPLE_SEED,
                                       TRAINING_MIN_BACKGROUND_PIXELS, TRAINING_MIN_NORMAL_PIXELS,
                                       ALL_CASES,
                                       CASE_FOLDER_PREFIX, REQUIRED_CASES, TRAINING_CASE, TRAINING_EXTRA_CASES)


@dataclass(frozen=True)
class ClassPixelCounts:
    """학습 조건 세그먼트에 보여 줄 세 숫자."""
    background: int = 0
    normal: int = 0
    abnormal: int = 0

    def add(self, other: "ClassPixelCounts") -> "ClassPixelCounts":
        return ClassPixelCounts(self.background + other.background, self.normal + other.normal,
                                self.abnormal + other.abnormal)


@dataclass(frozen=True)
class TrainingMinimums:
    background: int = TRAINING_MIN_BACKGROUND_PIXELS
    normal: int = TRAINING_MIN_NORMAL_PIXELS
    abnormal: int = TRAINING_MIN_ABNORMAL_PIXELS


def countClassPixels(label: np.ndarray) -> ClassPixelCounts:
    """라벨 한 장 → 배경(1), 원물(2), 이물(3 이상) 픽셀 수."""
    return ClassPixelCounts(int((label == LABEL_BACKGROUND).sum()), int((label == LABEL_NORMAL).sum()),
                            int((label >= ABNORMAL_LABEL_MIN).sum()))


def isTrainingReady(counts: ClassPixelCounts, minimums: Optional[TrainingMinimums] = None) -> bool:
    """세 조건을 모두 채웠는가 — 학습 버튼을 켜는 기준."""
    minimums = minimums or TrainingMinimums()
    return (counts.background >= minimums.background and counts.normal >= minimums.normal
            and counts.abnormal >= minimums.abnormal)


def samplePixelIndices(label: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """라벨 한 장 → (학습 픽셀의 평평한 인덱스, 비정상 여부). 정상(배경+원물)과 이물 각각 상한을 넘으면 고정 씨앗으로 무작위."""
    flat = label.ravel()
    generator = np.random.default_rng(TRAINING_SAMPLE_SEED)
    abnormalIndex = _capped(np.flatnonzero(flat >= ABNORMAL_LABEL_MIN), generator)
    normalIndex = _capped(np.flatnonzero((flat == LABEL_BACKGROUND) | (flat == LABEL_NORMAL)), generator)
    indices = np.concatenate([normalIndex, abnormalIndex])
    isAbnormal = np.concatenate([np.zeros(normalIndex.size, dtype=bool), np.ones(abnormalIndex.size, dtype=bool)])
    return indices, isAbnormal


def _capped(index: np.ndarray, generator: np.random.Generator) -> np.ndarray:
    if index.size <= TRAINING_MAX_PIXELS_PER_CLASS:
        return index
    return np.sort(generator.choice(index, TRAINING_MAX_PIXELS_PER_CLASS, replace=False))


def buildTrainingSamples(images: Sequence[Tuple[str, np.ndarray, np.ndarray]]) -> Tuple[np.ndarray, np.ndarray]:
    """[(이미지 경로, 큐브 (H, W, B) 0~4095, 라벨 (H, W))] → (스펙트럼 (N, B) float32, isAbnormal (N,))."""
    spectraParts, abnormalParts = [], []
    for folderPath, cube, label in images:
        if cube.shape[:2] != label.shape:
            raise ValueError("큐브와 라벨 크기가 다르다: %r vs %r" % (cube.shape[:2], label.shape))
        indices, isAbnormal = samplePixelIndices(label)
        spectraParts.append(np.asarray(cube.reshape(-1, cube.shape[2])[indices], dtype=np.float32))
        abnormalParts.append(isAbnormal)
    return np.concatenate(spectraParts), np.concatenate(abnormalParts)


# 'case' 앞에 글자나 숫자가 오면 안 된다. [0-9] 로 적는다 — \d 는 전각 숫자까지 받는다
_CASE_PATTERN = re.compile(r"(?<![^\W_])%s[\s_]*([0-9]+)" % re.escape(CASE_FOLDER_PREFIX))


def caseNumberFromFolderName(folderName: str) -> Optional[int]:
    """폴더 이름 → case 번호. 대소문자 무시, 'case' + (공백, 밑줄) + 숫자 모양이 아니거나 범위 밖이면 None."""
    normalized = (folderName or "").lower()
    match = _CASE_PATTERN.search(normalized)
    if match is None:
        return None
    caseNumber = int(match.group(1))
    return caseNumber if caseNumber in ALL_CASES else None


def caseNumberFromImagePath(imageFolderPath: str) -> Optional[int]:
    """이미지 폴더 경로 → 그 상위 폴더 이름의 case 번호. 끝의 / \\ 는 무시한다."""
    trimmed = os.path.normpath(imageFolderPath.rstrip("/\\"))
    return caseNumberFromFolderName(os.path.basename(os.path.dirname(trimmed)))


def isTrainingStartCase(imageFolderPath: str) -> bool:
    """학습 버튼을 켤 수 있는 case 의 이미지인가."""
    return caseNumberFromImagePath(imageFolderPath) == TRAINING_CASE


def isTrainingTargetCase(imageFolderPath: str) -> bool:
    """학습 대상 case 의 이미지인가(라벨이 저장, 검토됐는지는 따로 본다)."""
    return caseNumberFromImagePath(imageFolderPath) in (TRAINING_CASE,) + TRAINING_EXTRA_CASES


def isSalImage(imageFolderPath: str) -> bool:
    """추론이 모델 대신 SAL 인 이미지인가."""
    return caseNumberFromImagePath(imageFolderPath) == SAL_CASE


def missingRequiredCases(imageFolderPaths: Sequence[str]) -> List[int]:
    """불러온 이미지들에 없는 필수 case 번호들. 비어 있으면 일괄 추론 가능."""
    presentCases = {caseNumberFromImagePath(path) for path in imageFolderPaths}
    return [caseNumber for caseNumber in REQUIRED_CASES if caseNumber not in presentCases]


@dataclass
class BatchPlan:
    """일괄 추론 계획. caseTargets = case 에 속한 이미지(무조건 추론), outsideTargets = case 밖 이미지(사용자가 포함하면 추론),
    missingCases = 빠진 필수 case(있으면 일괄 추론 불가)."""
    caseTargets: List[str] = field(default_factory=list)
    outsideTargets: List[str] = field(default_factory=list)
    missingCases: List[int] = field(default_factory=list)

    @property
    def isAllowed(self) -> bool:
        return not self.missingCases

    def targets(self, includeOutside: bool) -> List[str]:
        """실제로 추론할 이미지들. includeOutside = case 밖 포함 여부의 답."""
        return self.caseTargets + (self.outsideTargets if includeOutside else [])


def planBatch(imageFolderPaths: Sequence[str]) -> BatchPlan:
    """이미지 폴더 경로들(이미지 테이블 순서, 선택된 이미지 포함) → 일괄 추론 계획."""
    plan = BatchPlan(missingCases=missingRequiredCases(imageFolderPaths))
    for path in imageFolderPaths:
        (plan.caseTargets if caseNumberFromImagePath(path) is not None else plan.outsideTargets).append(path)
    return plan
