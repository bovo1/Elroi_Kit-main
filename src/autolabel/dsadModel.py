"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    DSAD 모델 — 학습(trainDsad), 한 장 추론(scoreMapForCube) (torch, Qt 사용 안 함).

    학습 모드(trainer/DA.py T_DSAD)와 같은 네트워크, 순서(AE 사전학습 → 정상 픽셀로 중심 c → DSAD 학습 → 매 epoch 검증)를
    쓰되, 모델을 파일로 저장하지 않고 메모리로만 넘긴다. 종류 분류(CDSAD)는 없다 — 오토라벨링은 정상/비정상만 쓴다.
    검증 세트 = 학습 세트라서 best threshold 는 학습 라벨 기준 F1 최적값이다. 학습 픽셀의 비정상 비율이 실제 이미지보다
    높아 이 값은 과검 쪽으로 낮게 나올 수 있다(그래서 기본 표시 임계값은 자동 임계값).

    결과는 torch 텐서가 아니라 numpy 배열로 돌려준다 — 텐서를 프로세스 큐로 보내면 윈도에서 공유 메모리 핸들로 넘어가,
    자식이 먼저 끝나면 부모가 결과를 못 읽는다.
"""

import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, precision_recall_curve
from torch.utils.data import DataLoader, TensorDataset

from autolabel.autoLabelConfig import (CALIBRATION_RATE_DEFAULT, CALIBRATION_RATE_RANGE, INFERENCE_BATCH_PIXELS,
                                       TRAINING_MAX_BATCH_SIZE, TRAINING_MIN_BATCH_SIZE, AutoLabelSettings)


ABNORMAL_TARGET = 1      # DSAD 부호 규약(학습 모드와 같음): +1 = 비정상
NORMAL_TARGET = -1       # -1 = 정상
CENTER_MIN_MAGNITUDE = 0.1   # 중심 c 성분의 최소 크기(학습 모드와 같음)
INPUT_SCALE = 4095.0     # AE 재구성 목표 = 입력 / 4095 (모델 안의 Scaling 레이어와 같은 값)
VALIDATION_BATCH = 8192
PHASE_PRETRAIN = "pretrain"   # 진행 알림의 단계 이름
PHASE_TRAIN = "train"
BATCH_PROGRESS_INTERVAL_S = 0.1   # epoch 안 진행 알림의 최소 간격


@dataclass(frozen=True)
class DsadTrainingResult:
    """학습 결과(메모리). 부모 프로세스가 같은 모델을 다시 만든다. stateDict 는 가장 좋은 epoch 의 가중치(numpy), bestEpoch 는 1부터.
    calibrationRate 는 학습 픽셀에 쓴 보정 배율 — 이 모델로 추론할 때도 같은 배율의 큐브를 넣어야 입력 척도가 같다."""
    stateDict: Dict[str, np.ndarray]
    bestThreshold: float
    bestEpoch: int
    numBands: int
    numLayers: int
    repDim: int
    normalization: bool
    calibrationRate: float = CALIBRATION_RATE_DEFAULT


def calibratedCube(cube: np.ndarray, rate: float, sources: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None) -> np.ndarray:
    """학습, 추론에 쓸 큐브 — 학습 모드의 Calibration Rate 와 같은 식(clip((원본 - 검은판) / (흰판 - 검은판) × 4095 × 배율)).
    sources = (원본, 검은판, 흰판) 이 있으면 원본에서 다시 계산한다(큐브는 이미 잘려 있어 곱하면 학습 모드와 달라진다).
    없으면 큐브에 곱해 자른다. 배율 기본값이면 cube 를 그대로 돌려준다."""
    if rate == CALIBRATION_RATE_DEFAULT:
        return cube
    if sources is None:
        return np.clip(cube * rate, 0, INPUT_SCALE).astype(np.float32)
    origin, dark, white = sources
    return np.clip(((origin - dark) / (white - dark)) * INPUT_SCALE * rate, 0, INPUT_SCALE).astype(np.float32)


class NoUsableEpochError(RuntimeError):
    """검증 AUPR 이 한 번도 0 을 넘지 못함."""


def buildModel(numBands: int, numLayers: int, repDim: int, normalization: bool):
    """학습 모드와 같은 DSAD 네트워크(픽셀 단위 MLP, 패치 크기 1)."""
    from training.module.models.DA import DSAD
    return DSAD(numBands, numLayers, repDim, patch_size=1, normalization=normalization)


def modelFromResult(result: DsadTrainingResult, device: torch.device):
    """학습 결과 → 추론용 모델(평가 모드). 입력은 raw 0~4095 그대로(모델 안에서 /4095)."""
    model = buildModel(result.numBands, result.numLayers, result.repDim, result.normalization)
    model.load_state_dict({name: torch.from_numpy(np.array(value)) for name, value in result.stateDict.items()})
    return model.to(device).eval()


def auprAndBestThreshold(isAbnormal: np.ndarray, scores: np.ndarray):
    """검증 점수 → (AUPR, F1 최적 임계값). 정상, 비정상 중 하나라도 없으면 (0, None)."""
    labels = isAbnormal.astype(np.int64)
    if labels.min() == labels.max():
        return 0.0, None
    precision, recall, thresholds = precision_recall_curve(labels, scores)
    f1 = 2.0 * precision * recall / (precision + recall + np.finfo(np.float32).eps)
    return float(average_precision_score(labels, scores)), float(thresholds[int(np.argmax(f1[:-1]))])


def _validate(model, spectra: torch.Tensor, targets: torch.Tensor, device: torch.device):
    """모든 샘플의 거리 → (AUPR, F1 최적 임계값). 거리가 NaN, inf 면(발산) 예외."""
    model.eval()
    distances = []
    with torch.no_grad():
        for start in range(0, spectra.shape[0], VALIDATION_BATCH):
            distances.append(model(spectra[start:start + VALIDATION_BATCH].to(device)).float().cpu())
    scores = torch.cat(distances).numpy()
    if not np.isfinite(scores).all():
        raise FloatingPointError("학습이 발산했다(거리가 NaN 또는 무한대) — 학습률을 낮추거나 라벨을 확인할 것")
    return auprAndBestThreshold(targets.numpy() == ABNORMAL_TARGET, scores)


def validateInputs(spectra: np.ndarray, isAbnormal: np.ndarray, settings: AutoLabelSettings) -> None:
    """학습 시작 전 검사 — 문제가 있으면 원인을 담은 ValueError."""
    if spectra.ndim != 2 or spectra.shape[0] != isAbnormal.shape[0]:
        raise ValueError("픽셀 수와 라벨 수가 다르다")
    if not isAbnormal.any() or isAbnormal.all():
        raise ValueError("정상과 비정상 픽셀이 모두 있어야 학습할 수 있다")
    if not np.isfinite(spectra).all():
        raise ValueError("스펙트럼에 NaN 또는 무한대가 있다 — 보정 데이터(WHITEREF/DARKREF)를 확인할 것")
    if not TRAINING_MIN_BATCH_SIZE <= settings.batchSize <= TRAINING_MAX_BATCH_SIZE:
        raise ValueError("배치 크기는 %d ~ %d 사이여야 한다" % (TRAINING_MIN_BATCH_SIZE, TRAINING_MAX_BATCH_SIZE))
    if settings.batchSize > spectra.shape[0]:
        raise ValueError("배치 크기(%d)가 학습 픽셀 수(%d)보다 크다" % (settings.batchSize, spectra.shape[0]))
    if spectra.shape[1] <= settings.repDim:
        raise ValueError("밴드 수(%d)가 표현 차원(%d)보다 커야 한다" % (spectra.shape[1], settings.repDim))
    if not CALIBRATION_RATE_RANGE[0] <= settings.calibrationRate <= CALIBRATION_RATE_RANGE[1]:
        raise ValueError("보정 배율은 %g ~ %g 사이여야 한다" % CALIBRATION_RATE_RANGE)
    if settings.epochs < 1 or settings.aeEpochs < 0 or settings.patience < 1:
        raise ValueError("epoch 은 1 이상, 사전학습 epoch 은 0 이상, 대기 epoch 은 1 이상이어야 한다")


def trainDsad(spectra: np.ndarray, isAbnormal: np.ndarray, settings: AutoLabelSettings, device: torch.device,
              progressCallback: Optional[Callable[[str, int, int], None]] = None, seed: int = 0) -> DsadTrainingResult:
    """DSAD 를 학습해 가장 좋은 epoch 의 결과를 돌려준다.

    spectra (N, B) float32 raw 0~4095, isAbnormal (N,) bool. progressCallback(단계, epoch, 전체)는 epoch 끝(정수)과
    epoch 안(소수)에 불린다. 같은 장치, 입력, seed 면 같은 결과.
    예외 : ValueError(validateInputs), FloatingPointError(쓸 만한 epoch 전에 발산), NoUsableEpochError
    """
    from training.module.models.Module import AutoEncoder
    validateInputs(spectra, isAbnormal, settings)
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)
    spectraTensor = torch.from_numpy(np.ascontiguousarray(spectra, dtype=np.float32))
    targets = torch.from_numpy(np.where(isAbnormal, ABNORMAL_TARGET, NORMAL_TARGET).astype(np.int64))
    # drop_last: 1개짜리 배치는 BatchNorm 이 학습 모드에서 예외를 낸다
    loader = DataLoader(TensorDataset(spectraTensor, targets), batch_size=settings.batchSize, shuffle=True,
                        drop_last=True, generator=generator)
    numBands = spectra.shape[1]
    batchCount = len(loader)
    lastReport = [time.monotonic()]

    def reportBatch(phase: str, epoch: int, batchIndex: int, total: int) -> None:
        """epoch 안의 진행(소수)을 일정 간격으로 알린다. 마지막 배치는 epoch 끝 알림(정수)이 맡아 받는 쪽이 둘을 구분한다."""
        now = time.monotonic()
        if progressCallback is None or batchIndex + 1 >= batchCount or now - lastReport[0] < BATCH_PROGRESS_INTERVAL_S:
            return
        lastReport[0] = now
        progressCallback(phase, epoch - 1 + (batchIndex + 1) / batchCount, total)

    # ---- 1) AE 사전학습
    autoEncoder = AutoEncoder(numBands, settings.numLayers, settings.repDim, 1, normalization=settings.normalization).to(device)
    aeOptimizer = torch.optim.AdamW(autoEncoder.parameters(), lr=settings.learningRate, weight_decay=0.0)
    aeScheduler = torch.optim.lr_scheduler.CosineAnnealingLR(aeOptimizer, T_max=max(1, settings.aeEpochs))
    reconstructionLoss = nn.MSELoss()
    autoEncoder.train()
    for aeEpoch in range(1, settings.aeEpochs + 1):
        for batchIndex, (batch, _) in enumerate(loader):
            batch = batch.to(device)
            aeOptimizer.zero_grad(set_to_none=True)
            reconstructionLoss(autoEncoder(batch), batch / INPUT_SCALE).backward()
            aeOptimizer.step()
            reportBatch(PHASE_PRETRAIN, aeEpoch, batchIndex, settings.aeEpochs)
        aeScheduler.step()
        if progressCallback is not None:
            progressCallback(PHASE_PRETRAIN, aeEpoch, settings.aeEpochs)
    autoEncoder.eval()

    # ---- 2) DSAD 초기화: 인코더 복사 + 정상 픽셀 평균으로 중심 c
    model = buildModel(numBands, settings.numLayers, settings.repDim, settings.normalization).to(device)
    model.encoder.load_state_dict(autoEncoder.encoder.state_dict())
    with torch.no_grad():
        normalSpectra = spectraTensor[targets == NORMAL_TARGET]
        center = torch.zeros(settings.repDim, device=device)
        for start in range(0, normalSpectra.shape[0], VALIDATION_BATCH):
            center += autoEncoder.encoder(normalSpectra[start:start + VALIDATION_BATCH].to(device)).sum(dim=0)
        center /= normalSpectra.shape[0]
        model.c.copy_(clampCenter(center))

    # ---- 3) DSAD 학습 + 매 epoch 검증
    optimizer = torch.optim.AdamW(model.parameters(), lr=settings.learningRate, weight_decay=0.0)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, settings.epochs))
    epsilon = torch.finfo(torch.float32).eps
    bestScore, bestState, bestThreshold, bestEpoch = 0.0, None, None, 0
    epochsWithoutImprovement = 0
    for epoch in range(1, settings.epochs + 1):
        model.train()
        for batchIndex, (batch, batchTargets) in enumerate(loader):
            batch, batchTargets = batch.to(device), batchTargets.to(device)
            optimizer.zero_grad(set_to_none=True)
            distance = model(batch)
            loss = torch.where(batchTargets == ABNORMAL_TARGET, torch.reciprocal(distance + epsilon), distance).mean()
            loss.backward()
            optimizer.step()
            reportBatch(PHASE_TRAIN, epoch, batchIndex, settings.epochs)
        scheduler.step()
        # 검증 = 학습 픽셀 그대로(따로 떼면 이물 픽셀이 적어 F1 이 오히려 나빴다)
        try:
            aupr, threshold = _validate(model, spectraTensor, targets, device)
        except FloatingPointError:
            if bestState is None:
                raise
            break                                    # 늦게 발산해도 앞 epoch 의 결과는 쓴다
        if aupr > bestScore:
            bestScore, bestThreshold, bestEpoch = aupr, threshold, epoch
            bestState = {name: tensor.detach().cpu().numpy().copy() for name, tensor in model.state_dict().items()}
            epochsWithoutImprovement = 0
        else:
            epochsWithoutImprovement += 1
        if progressCallback is not None:
            progressCallback(PHASE_TRAIN, epoch, settings.epochs)
        if settings.earlyStop and epochsWithoutImprovement >= settings.patience:
            break
    if bestState is None:
        raise NoUsableEpochError("검증 AUPR 이 한 번도 0 을 넘지 못했다")
    return DsadTrainingResult(bestState, bestThreshold, bestEpoch, numBands, settings.numLayers, settings.repDim,
                              settings.normalization, settings.calibrationRate)


def clampCenter(center: torch.Tensor) -> torch.Tensor:
    """중심 c 의 0 에 가까운 성분을 부호는 두고 크기만 CENTER_MIN_MAGNITUDE 로 민다(학습 모드와 같은 규칙). 받은 텐서를 고쳐 돌려준다."""
    isSmall = center.abs() < CENTER_MIN_MAGNITUDE
    center[isSmall & (center < 0)] = -CENTER_MIN_MAGNITUDE
    center[isSmall & (center > 0)] = CENTER_MIN_MAGNITUDE
    return center


def pickDevice() -> torch.device:
    """GPU 가 있으면 GPU, 없으면 CPU — 유사도, 학습, 추론이 같이 쓴다."""
    return torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")


def scoreMapForCube(model, cube: np.ndarray, batchPixels: int = INFERENCE_BATCH_PIXELS) -> np.ndarray:
    """큐브 한 장 (H, W, B) → 점수 맵 (H, W) float32(DSAD 거리, 클수록 이상). 큐브는 학습 때의 보정 배율을 적용한 것이어야 한다.
    GPU 메모리를 위해 batchPixels 씩 나눠 넣는다. (분류, 거리) 튜플을 돌려주는 모델이면 거리만 꺼낸다."""
    device = next(model.parameters()).device
    height, width, bands = cube.shape
    flat = torch.from_numpy(np.ascontiguousarray(cube.reshape(-1, bands), dtype=np.float32))
    scores = torch.empty(flat.shape[0], dtype=torch.float32)
    with torch.no_grad():
        for start in range(0, flat.shape[0], batchPixels):
            output = model(flat[start:start + batchPixels].to(device))
            output = output[1] if isinstance(output, tuple) else output
            scores[start:start + batchPixels] = output.detach().float().reshape(-1).cpu()
    return scores.numpy().reshape(height, width)
