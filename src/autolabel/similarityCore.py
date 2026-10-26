"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    유사도 — 점수 계산, 클릭을 쌓은 미리보기, 화면에 얹을 미리보기 층 (Qt 사용 안 함).

    ── similarityScore ──────────────────────────────────────────
    유사도(GLE) 점수 맵 계산 — 클릭한 픽셀 하나와 이미지 전체 픽셀의 스펙트럼 유사도.
    수식은 제품 pixel_based_similarity.calculateSimilarity 와 같고(테스트가 비교), 가중치를 인자로 받는 것과
    클릭마다 미리보기를 띄우도록 torch(GPU)로 계산하는 것만 다르다.

    ── similarityPreview ────────────────────────────────────────
    유사도 미리보기 — 클릭을 쌓아 두었다가 점수 하한으로 '어느 픽셀이 어느 클래스로 칠해질지' 를 만든다.
        - 미리보기는 라벨이 아니다. Ctrl+S 를 눌러야 라벨에 적용된다(그때 이 객체는 비운다).
        - 클릭마다 결과 마스크가 아니라 점수 맵을 보관한다. 하한을 바꾸면 다시 계산하지 않고 비교만 하면 된다.
        - 새 클릭은 그 클릭만 계산해 얹고, 하한이나 상한이 바뀔 때만 전체를 다시 얹는다(currentLabel).
        - 클릭 하나의 선택 규칙은 selectClickPixels: 하한 이상 후보 → 클릭당 상한 → 이물은 클릭 지점과 이어진 덩어리만.
          상수는 autoLabelConfig, 하한과 상한은 설정 독 값을 컨트롤러가 넘긴다.
        - 클릭이 겹치면 이물이 이긴다. 같은 그룹에서는 먼저 누른 클릭이 우선한다.
        - 지우개로 미리보기를 지울 수 있고, 클릭 하나와 지우개 한 획이 되돌리기 한 단위다.

    ── previewLayer ─────────────────────────────────────────────
    미리보기 레이어 — 라벨이 아닌 미리보기를 화면에 그리기 직전에 반투명으로 얹는다.
    바탕을 따로 떠 두지 않고 디스플레이가 그릴 때마다 최신 화면 이미지 위에 다시 얹으므로, 펜, 되돌리기, 라벨 색이 바뀌어도 어긋나지 않는다.
    미리보기는 한 번에 하나만 보이며 무엇을 보일지는 오토라벨링 컨트롤러가 정한다.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable, Sequence

import numpy as np
import torch
from scipy import ndimage

from autolabel.autoLabelConfig import (SIMILARITY_GLE_EPSILON, ABNORMAL_LABEL_MIN, LABEL_IGNORED,
                                       SIMILARITY_ABNORMAL_FLOOD, SIMILARITY_AUTO_ORDER_RATIO,
                                       SIMILARITY_NORMAL_FLOOD, imageKey, PREVIEW_OPACITY)


def prepareSpectra(cube: np.ndarray, device: torch.device) -> torch.Tensor:
    """(H, W, B) 큐브를 (H*W, B) float32 텐서로 device 에 한 번만 올려 둔다(클릭마다 올리면 전송이 계산보다 느리다)."""
    if cube.ndim != 3:
        raise ValueError("큐브는 (H, W, B) 3차원이어야 한다: %r" % (cube.shape,))
    flat = np.ascontiguousarray(cube.reshape(-1, cube.shape[2]), dtype=np.float32)
    return torch.from_numpy(flat).to(device)


def gleScoreMap(spectra: torch.Tensor, seedIndex: int, imageShape, weights) -> np.ndarray:
    """기준 픽셀(seedIndex = row * W + col) 하나에 대한 GLE 유사도 맵 (H, W) float32, 0~100, 높을수록 비슷하다.
    spectra 는 prepareSpectra 결과, weights 는 (RMSE 항, 비선형 항, Linf 항) 가중치(합 1)."""
    height, width = imageShape
    if not 0 <= seedIndex < spectra.shape[0]:
        raise IndexError("기준 픽셀 위치가 이미지 밖이다: %d" % seedIndex)
    alpha, beta, gamma = weights
    reference = spectra[seedIndex]
    difference = (spectra - reference).abs()
    larger = torch.maximum(spectra, reference) + SIMILARITY_GLE_EPSILON
    rmse = ((difference / larger) ** 2).mean(dim=-1).sqrt()
    linf = difference.max(dim=-1).values / (larger.max(dim=-1).values + SIMILARITY_GLE_EPSILON)
    nonlinear = ((torch.log1p(difference) / torch.log1p(larger)) ** 2).mean(dim=-1).sqrt()
    score = (alpha * (1 - rmse) + beta * (1 - nonlinear) + gamma * (1 - linf)) * 100.0
    return score.reshape(height, width).float().cpu().numpy()


# 8-이웃 연결(대각선도 이어진 것으로 본다)
EIGHT_CONNECTIVITY = np.ones((3, 3), dtype=int)
_CLICK = "click"                 # 되돌리기 기록의 종류
_ERASE = "erase"


@dataclass(frozen=True)
class SimilarityClick:
    """클릭 한 번. scoreMap 은 그 클릭 픽셀 기준의 (H, W) 유사도, labelNumber 는 칠할 라벨."""
    row: int
    col: int
    labelNumber: int
    scoreMap: np.ndarray


def isAbnormalLabel(labelNumber: int) -> bool:
    """이물 라벨인가 — 이물은 공간 연결 규칙을 쓴다."""
    return labelNumber >= ABNORMAL_LABEL_MIN


def keepTopCount(score: np.ndarray, candidateMask: np.ndarray, cap: Optional[int], row: int, col: int) -> np.ndarray:
    """candidateMask 안에서 점수 상위 cap 개만 남긴다(cap=None 이면 제한 없음). 같은 점수면 클릭 자리(row, col)에 가까운 픽셀이 먼저다."""
    count = np.count_nonzero(candidateMask)
    if cap is None or count <= cap:
        return candidateMask
    kept = np.zeros_like(candidateMask)
    if cap <= 0:
        return kept
    rows, cols = np.nonzero(candidateMask)
    values = score[rows, cols]
    # 전체를 정렬하지 않고 cap 번째 점수(경계)만 찾는다 — 끄는 동안 클릭마다 다시 계산하므로 속도 때문
    boundary = np.partition(values, values.size - cap)[values.size - cap]
    above = values > boundary
    kept[rows[above], cols[above]] = True
    ties = np.nonzero(values == boundary)[0]
    need = cap - np.count_nonzero(above)
    if need > 0:
        nearest = ties[np.argsort((rows[ties] - row) ** 2 + (cols[ties] - col) ** 2, kind="stable")[:need]]
        kept[rows[nearest], cols[nearest]] = True
    return kept


def keepConnectedToSeed(mask: np.ndarray, row: int, col: int) -> np.ndarray:
    """mask 중 (row, col) 과 8-이웃으로 이어진 덩어리만 남긴다."""
    labeled, _ = ndimage.label(mask, structure=EIGHT_CONNECTIVITY)
    seedComponent = labeled[row, col]
    if seedComponent == 0:
        return np.zeros_like(mask)
    return labeled == seedComponent


def growFromSeed(score: np.ndarray, mask: np.ndarray, cap: int, row: int, col: int) -> np.ndarray:
    """mask 안에서 (row, col) 부터 8-이웃으로 한 겹씩 넓혀 cap 개까지(마지막 겹은 점수 높은 순).
    덩어리 전체에서 상위 cap 개를 고르면 클릭에서 먼 곳이 칠해질 수 있어 클릭 둘레부터 채운다."""
    region = np.zeros_like(mask)
    if not mask[row, col]:
        return region
    region[row, col] = True
    count = 1
    height, width = mask.shape
    top, bottom, left, right = row, row + 1, col, col + 1
    while count < cap:
        # 덩어리를 담는 사각형만 넓힌다 — 이미지 전체를 팽창하면 느리다(결과는 같다)
        top, left, bottom, right = max(top - 1, 0), max(left - 1, 0), min(bottom + 1, height), min(right + 1, width)
        window = (slice(top, bottom), slice(left, right))
        ring = ndimage.binary_dilation(region[window], structure=EIGHT_CONNECTIVITY) & mask[window] & ~region[window]
        if not ring.any():
            break
        added = keepTopCount(score[window], ring, cap - count, row - top, col - left)
        region[window] |= added
        count += np.count_nonzero(added)
    return region


def selectClickPixels(score: np.ndarray, floor: float, cap: Optional[int], row: int, col: int, useFlood: bool) -> np.ndarray:
    """클릭 하나가 가져갈 픽셀(bool 마스크)."""
    base = score >= floor
    if not useFlood:
        return keepTopCount(score, base, cap, row, col)
    if cap is None:
        return keepConnectedToSeed(base, row, col)
    capFirst = keepConnectedToSeed(keepTopCount(score, base, cap, row, col), row, col)
    if np.count_nonzero(capFirst) >= cap * SIMILARITY_AUTO_ORDER_RATIO:
        return capFirst                                  # '연결 먼저' 는 cap 개를 넘지 않아 이길 수 없다
    floodFirst = growFromSeed(score, base, cap, row, col)
    if np.count_nonzero(capFirst) < np.count_nonzero(floodFirst) * SIMILARITY_AUTO_ORDER_RATIO:
        return floodFirst
    return capFirst


class SimilarityPreview:
    """한 이미지에서 쌓인 유사도 미리보기. 이미지가 바뀌면 clear() 해야 하고, 다른 이미지의 클릭이 들어오면 예외다.
    currentLabel 이 (H, W) 미리보기 라벨(0 = 없음)을 돌려준다.
    기록(ops)을 순서대로 하나씩 얹어 화면 미리보기(_label)를 만들고, 되돌리기는 op 마다 기억한 이전 값으로 돌린다(_undoData)."""

    def __init__(self):
        self.clear()

    def clear(self) -> None:
        """적용했을 때, 이미지가 바뀌었을 때."""
        self.imageKey: Optional[str] = None
        self.ops: list = []                            # (_CLICK, SimilarityClick) 또는 (_ERASE, 지운 자리 bool 마스크)
        self._redo: list = []                          # 되돌린 op
        self._label: Optional[np.ndarray] = None       # 화면 미리보기 — ops[:len(_undoData)] 를 얹은 것
        self._labeledMask: Optional[np.ndarray] = None  # _label 을 만들 때의 '이미 라벨된 자리'
        self._undoData: list = []                      # op 마다 되돌릴 값(_revert)
        self._labelKey = None                          # _label 을 만든 (하한, 원물 상한, 이물 상한)
        self._isErasing = False                        # 지우개 획이 진행 중인가

    def addClick(self, imageFolderPath: str, click: SimilarityClick) -> None:
        """클릭을 쌓는다(계산은 다음 currentLabel 때). 다른 이미지, 다른 크기, 0 이하 라벨이면 ValueError."""
        if click.labelNumber < 1:
            raise ValueError("칠할 라벨 번호는 1 이상이어야 한다: %r" % click.labelNumber)
        key = imageKey(imageFolderPath)
        clicks = self.clicks
        if self.imageKey is not None and key != self.imageKey:
            raise ValueError("다른 이미지의 클릭이 섞였다 — 이미지를 바꿀 때 clear() 를 불러야 한다")
        if clicks and click.scoreMap.shape != clicks[0].scoreMap.shape:
            raise ValueError("점수 맵 크기가 다르다: %r vs %r" % (click.scoreMap.shape, clicks[0].scoreMap.shape))
        self.imageKey = key
        self.ops.append((_CLICK, click))
        self._redo = []
        self._isErasing = False

    @property
    def clicks(self) -> List[SimilarityClick]:
        return [value for kind, value in self.ops if kind == _CLICK]

    def erase(self, indice) -> bool:
        """지우개가 지나간 자리(numpy 인덱스)를 미리보기에서 뺀다. 클릭이 없으면 False."""
        clicks = self.clicks
        if not clicks:
            return False
        if not self._isErasing:                                  # 획의 첫 이동
            isAllApplied = self._label is not None and len(self._undoData) == len(self.ops)
            self.ops.append((_ERASE, np.zeros(clicks[0].scoreMap.shape, dtype=bool)))
            self._redo = []
            self._isErasing = True
            if isAllApplied:
                self._undoData.append([])
        hit = np.zeros_like(self.ops[-1][1])
        hit[indice] = True
        self.ops[-1][1][hit] = True
        if len(self._undoData) == len(self.ops):
            self._undoData[-1].append(_clearPixels(self._label, hit))   # 이동마다 지운 자리, 이전 값만 둔다(통째 사본은 크다)
        return True

    def endStroke(self) -> None:
        """지우개 획이 끝남 — 다음 지우개는 새 되돌리기 단위. 아무것도 안 지운 획은 기록에서 뺀다."""
        if self._isErasing and len(self._undoData) == len(self.ops) and not any(len(changed) for changed, _ in self._undoData[-1]):
            self.ops.pop()
            self._undoData.pop()
        self._isErasing = False

    def canUndo(self) -> bool:
        return bool(self.ops)

    def undo(self) -> bool:
        """마지막 단위(클릭 하나, 지우개 한 획)를 취소한다."""
        if not self.ops:
            return False
        self._isErasing = False
        if len(self._undoData) == len(self.ops):
            self._revert(self.ops[-1][0], self._undoData.pop())
        self._redo.append(self.ops.pop())                        # 클릭이 다 없어져도 이미지 키는 남긴다
        return True

    def canRedo(self) -> bool:
        return bool(self._redo)

    def removeLabels(self, labelNumbers) -> bool:
        """라벨 탭에서 지운 클래스의 클릭을 기록(다시 실행 포함)에서 뺀다. 클릭이 하나도 안 남으면 비운다. 바뀌었는가를 돌려준다."""
        def isRemoved(op):
            return op[0] == _CLICK and op[1].labelNumber in labelNumbers
        if not any(isRemoved(op) for op in self.ops + self._redo):
            return False
        self.ops = [op for op in self.ops if not isRemoved(op)]
        self._redo = [op for op in self._redo if not isRemoved(op)]
        self._label, self._undoData, self._isErasing = None, [], False
        if not self.clicks:
            self.ops = []                                  # 지우개 기록만 남으면 의미가 없다
            if not any(kind == _CLICK for kind, _ in self._redo):
                self.clear()
        return True

    def redo(self) -> bool:
        """마지막으로 취소한 단위를 되살린다."""
        if not self._redo:
            return False
        self._isErasing = False
        self.ops.append(self._redo.pop())
        return True

    def isEmpty(self) -> bool:
        """적용할 미리보기가 있는가."""
        return not self.ops

    def latestCandidateScores(self, labeledMask: np.ndarray) -> Optional[np.ndarray]:
        """마지막 클릭의 점수 중 아직 라벨 안 된 픽셀의 점수(1차원, 임계값 그래프의 분포용). 클릭이 없으면 None."""
        clicks = self.clicks
        if not clicks:
            return None
        return clicks[-1].scoreMap[~labeledMask]

    def currentLabel(self, floor: float, labeledMask: np.ndarray, normalCap: Optional[int],
                     abnormalCap: Optional[int]) -> np.ndarray:
        """지금 미리보기 라벨. 하한, 상한이 그대로면 아직 안 얹은 op 만 얹고, 바뀌었으면 처음부터 얹는다.
        labeledMask 는 이미 라벨된 픽셀(클릭 후보에서 뺀다). 돌려주는 배열은 이 객체가 들고 있는 것이니 고치면 안 된다."""
        key = (floor, normalCap, abnormalCap)
        if self._label is None or key != self._labelKey or self._isFreed(labeledMask):
            self._label = np.zeros(labeledMask.shape, dtype=np.int64)
            self._undoData = []
            self._labelKey = key
            self._labeledMask = labeledMask.copy()
        for op in self.ops[len(self._undoData):]:
            self._undoData.append(_applyOp(op, self._label, floor, labeledMask, normalCap, abnormalCap))
        return self._label

    def _isFreed(self, labeledMask: np.ndarray) -> bool:
        """_label 을 만들 때 라벨돼 있던 자리가 지금 비었는가 — 그 자리를 후보에서 뺐으므로 다시 계산해야 한다."""
        return self._labeledMask is None or self._labeledMask.shape != labeledMask.shape \
            or bool((self._labeledMask & ~labeledMask).any())

    def _revert(self, kind: str, data) -> None:
        """op 하나를 되돌린다. 지우개 획은 이동마다 쌓인 묶음을 나중 것부터 되돌린다."""
        for changed, before in reversed(data if kind == _ERASE else [data]):
            self._label.flat[changed] = before


def _applyOp(op, preview: np.ndarray, floor: float, labeledMask: np.ndarray, normalCap: Optional[int],
             abnormalCap: Optional[int]):
    """op 하나를 preview 에 얹고 되돌릴 값을 돌려준다. 클릭은 이미 라벨된 픽셀과 앞 클릭 자리를 뺀 나머지에서 고른다(이물만 원물/배경 자리를 가져간다)."""
    kind, value = op
    if kind == _ERASE:
        return [_clearPixels(preview, value)]
    isAbnormal = isAbnormalLabel(value.labelNumber)
    blocked = labeledMask | (preview >= ABNORMAL_LABEL_MIN if isAbnormal else preview != 0)
    candidateScore = np.where(blocked, -np.inf, value.scoreMap)
    selected = selectClickPixels(candidateScore, floor, abnormalCap if isAbnormal else normalCap, value.row, value.col,
                                 SIMILARITY_ABNORMAL_FLOOD if isAbnormal else SIMILARITY_NORMAL_FLOOD)
    changed = np.flatnonzero(selected)
    before = preview.flat[changed].copy()
    preview.flat[changed] = value.labelNumber
    return changed, before


def _clearPixels(preview: np.ndarray, mask: np.ndarray):
    """mask 자리 중 미리보기가 있는 곳을 0 으로 하고 (바뀐 자리, 이전 값)을 돌려준다."""
    changed = np.flatnonzero(mask & (preview != 0))
    before = preview.flat[changed].copy()
    preview.flat[changed] = 0
    return changed, before


@dataclass(frozen=True)
class PreviewFrame:
    """지금 얹을 미리보기 한 장.

    imageKey     : 어느 이미지의 미리보기인가(다른 이미지가 화면에 있으면 얹지 않는다)
    labelArray   : (H, W) int — 0 = 없음, 그 밖 = 그 라벨 색으로 얹는다
    replaceLabels: True 면 라벨이 그려진 화면 대신 원본 이미지 위에 얹는다
    hiddenLabels : 얹지 않을 라벨 번호들
    extraMask    : 불확실 표시처럼 라벨이 아닌 강조(옵션) — extraColor 로 얹는다
    """
    imageKey: str
    labelArray: np.ndarray
    replaceLabels: bool = False
    hiddenLabels: frozenset = frozenset()
    extraMask: Optional[np.ndarray] = None
    extraColor: Sequence[int] = (255, 255, 255)


def composePreview(screenRgb: np.ndarray, originRgb: Optional[np.ndarray], frame: PreviewFrame,
                   colorOf: Callable[[int], Optional[Sequence[int]]], opacity: float = PREVIEW_OPACITY) -> np.ndarray:
    """화면 이미지 + 미리보기 → 그릴 이미지(새 배열, 입력은 고치지 않는다). colorOf 가 None 을 주는 라벨은 건너뛴다.
    크기가 안 맞으면(다른 이미지) 화면을 그대로 돌려준다."""
    if frame.labelArray.shape != screenRgb.shape[:2]:
        return screenRgb
    base = originRgb if (frame.replaceLabels and originRgb is not None and originRgb.shape == screenRgb.shape) else screenRgb
    composed = base.copy()
    labels = frame.labelArray.ravel()
    extra = frame.extraMask.ravel() if frame.extraMask is not None and frame.extraMask.shape == screenRgb.shape[:2] else None
    pixels = composed.reshape(-1, 3)
    levels = np.arange(256, dtype=np.float32)
    # 라벨 색 섞기는 0~255 표(채널마다)로 바꿔 끼운다 — 화면 전체가 칠해져도 빠르다. 강조 픽셀은 반올림 전 값으로 한 번 더 섞어야 해서 아래에서 따로 계산한다
    for labelNumber in labelsIn(labels):
        color = colorOf(labelNumber)
        if color is None or labelNumber in frame.hiddenLabels:
            continue
        mask = labels == labelNumber
        if extra is not None:
            mask &= ~extra
        table = np.clip(np.rint(opacity * np.asarray(color, dtype=np.float32)[:, None] + (1 - opacity) * levels[None, :]),
                        0, 255).astype(np.uint8)                  # 반올림(버림이면 어두워진다)
        selected = pixels[mask]
        pixels[mask] = np.stack([table[channel][selected[:, channel]] for channel in range(3)], axis=1)
    if extra is not None and extra.any():
        index = np.flatnonzero(extra)
        source = base.reshape(-1, 3)
        blended = source[index].astype(np.float32)
        extraLabels = labels[index]
        for labelNumber in labelsIn(extraLabels):
            color = colorOf(labelNumber)
            if color is None or labelNumber in frame.hiddenLabels:
                continue
            mask = extraLabels == labelNumber
            blended[mask] = opacity * np.asarray(color, dtype=np.float32) + (1 - opacity) * blended[mask]
        blended = opacity * np.asarray(frame.extraColor, dtype=np.float32) + (1 - opacity) * blended
        pixels[index] = np.clip(np.rint(blended), 0, 255).astype(np.uint8)
    return composed


def labelsIn(labels: np.ndarray):
    """칠할 라벨 번호들(0 제외). 작은 정수 라벨은 np.unique 대신 bincount 가 빠르다."""
    if labels.size == 0:
        return []
    if labels.dtype.kind in "iu" and labels.min() >= 0:                    # bincount 는 0 이상의 정수만 받는다
        return [int(value) for value in np.flatnonzero(np.bincount(labels.astype(np.int64, copy=False)))
                if value != LABEL_IGNORED]
    return [int(value) for value in np.unique(labels) if value != LABEL_IGNORED]
