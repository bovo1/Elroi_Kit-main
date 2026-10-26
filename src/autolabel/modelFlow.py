"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 학습 흐름(조건 세기 → 학습 → 학습 이미지 점수 맵 → 자동 임계값)과 추론(한 장, 일괄)에서 모델이 있는 동안의
    상태를 맡는다. 컨트롤러(autoLabelController)가 하나 만들고 컨트롤러는 연결만 한다. 규칙은 따로 있다:
    학습 픽셀 뽑기(trainingPlan), 임계값(thresholdRules), 바 상태(barState).

    흐름
        1) 조건: 이미지 목록의 저장된 라벨(labelFiles.TrainingLabelSummaries)을 센다.
        2) 학습: 컨트롤러가 정한 이미지 키 → 픽셀 뽑기 → 시작 전 검사 → 자식 프로세스 학습(workers.TrainingRunner). 취소 가능.
        3) 성공: 추론 스레드가 모델을 만들고 학습 이미지 점수 맵을 계산 → 자동 임계값. 이전 모델, 점수 맵은 이때 버린다.
        4) 학습이 끝나면 모델 탭으로만 넘어간다. 추론으로 라벨을 만든 뒤 임계값을 조절한다.
        5) 추론: 점수 맵 → 임계값, 적용 규칙으로 라벨 → 컨트롤러가 디스크, DB, 화면에 씀 → 점수 맵 보관(scoreStore).
           라벨이 추론 결과 그대로일 때만 임계값을 조절할 수 있다.

    입력 : controller(sync, settings, bar, text, 화면 다시 그리기). 출력 : changed 시그널(바를 다시 그리라는 뜻).
"""

import dataclasses
import os
import time
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from PyQt5 import QtCore

from autolabel.autoLabelConfig import CALIBRATION_RATE_DEFAULT, WRITE_DECLINED, WRITE_DONE, WRITE_FAILED, imageKey
from autolabel.barState import JOB_BATCH, JOB_INFERENCE, JOB_NONE, JOB_TRAINING, TAB_MODEL
from autolabel.dsadModel import PHASE_PRETRAIN, modelFromResult, pickDevice, validateInputs
from autolabel.labelFiles import TrainingLabelSummaries, readLabel
from autolabel.thresholdRules import (ApplyRule, ScoreMapStore, StoredScoreMap, applyRuleForImage, computeAutoThreshold,
                                      labelFromScore, overlayInferred, uncertainMask)
from autolabel.trainingPlan import ClassPixelCounts, buildTrainingSamples, caseNumberFromImagePath, isSalImage
from autolabel.workers import InferenceWorker, TrainingRunner, WarmTrainingProcess
from notification.notificationCenter import (NOTIFICATION_FAILURE, NOTIFICATION_INFO, NOTIFICATION_SUCCESS,
                                             getNotificationCenter)

REMAINING_MIN_FRACTION = 0.03     # 이만큼 진행한 뒤부터 남은 시간을 어림한다
BATCH_REMAINING_MIN_DONE = 2      # 일괄 추론은 두 장째가 끝나야 어림한다(첫 장은 모델, 장치 준비가 섞인다)
SECONDS_PER_MINUTE = 60
DISTRIBUTION_SAMPLE_SIZE = 200000     # 임계값 그래프의 분포 — 학습 이미지 전체 점수에서 이만큼만 뽑는다(그래프 모양엔 충분)
IMAGE_LIST_SEPARATOR = " · "
FAILURE_NO_IMAGES = "noImages"        # 실패 이유 키(언어 파일 trainingFailure_<키>)
FAILURE_INVALID = "invalidInput"
FAILURE_SCORING = "scoring"
TRAINING_TITLE_KEY = "trainingFailedTitle"
INFERENCE_TITLE_KEY = "inferenceFailedTitle"
INFERENCE_FAILURE_PROCESS = "process"   # 추론 실패 이유 키(언어 파일 inferenceFailure_<키>)


def _labelOf(scoreMap: Optional[np.ndarray], threshold: float, rule, salMask: Optional[np.ndarray]) -> np.ndarray:
    """점수 맵 → 라벨. 점수 맵이 None 이면 SAL 결과 — 모두 정상으로 두고 SAL 원물 마스크로 원물, 배경을 정한다."""
    if scoreMap is None:
        return labelFromScore(np.zeros(salMask.shape, np.float32), np.inf, rule, salMask)
    return labelFromScore(scoreMap, threshold, rule)


class ModelFlow(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.summaries = TrainingLabelSummaries()
        self.runningJob = JOB_NONE
        self.model = None
        self.calibrationRate = CALIBRATION_RATE_DEFAULT      # 지금 모델을 학습할 때의 보정 배율 — 추론 때 같은 배율을 쓴다
        self.autoThreshold: Optional[float] = None
        self.bestThreshold: Optional[float] = None
        self.userThreshold: Optional[float] = None       # 사용자가 고른 값 — 다음 추론의 기본값
        self.previewThreshold: Optional[float] = None    # 슬라이더를 끄는 동안의 값(미리보기만)
        self.trainingScoreMaps: Dict[str, np.ndarray] = {}   # 학습 이미지 키 → 점수 맵
        # 도는 스레드는 finished 까지 여기서 붙잡는다 — 참조가 먼저 0 이 되면 'QThread: Destroyed while thread is still running' 으로 앱이 죽는다
        self._liveThreads = set()
        self._runner: Optional[TrainingRunner] = None
        self.warmProcess = WarmTrainingProcess()     # 학습 자식을 미리 띄워 둔다(prepareTraining)
        self._scorer: Optional[InferenceWorker] = None
        self._pendingResult = None
        self._trainingJobs: List[Tuple[str, np.ndarray]] = []
        self._isCanceled = False
        self._distribution: Optional[np.ndarray] = None   # distributionScores 캐시 — 점수 맵이 바뀌면 None
        self.scoreStore = ScoreMapStore()                 # 추론한 이미지의 점수 맵, 그 라벨을 만든 임계값, 규칙
        self._uncertainCache = (None, None, None, None)   # (이미지 키, 임계값, 점수 맵, 마스크)
        # 이미지 키 → 그 이미지 라벨을 만든 적 있는 임계값들(되돌리기가 어느 단계로 돌아가도 알아보게 개수를 제한하지 않는다)
        self._usedThresholds: Dict[str, List[float]] = {}
        self._pretrainEpochs = 0
        self._trainingSettings = None
        self._progressTotal = 0
        self._batchFirstDoneTime = 0.0
        self._batchPlanAtStart: Dict[str, Tuple[float, ApplyRule, Optional[np.ndarray]]] = {}   # 일괄 추론: 경로 → (임계값, 규칙, 바탕 라벨)

    # ------------------------------------------------------------------ 상태
    @property
    def hasModel(self) -> bool:
        return self.model is not None

    def threshold(self) -> Optional[float]:
        """지금 쓰는 임계값: 끄는 중 값 > 사용자가 고른 값 > 자동/best 설정."""
        for value in (self.previewThreshold, self.userThreshold):
            if value is not None:
                return value
        return self.autoThreshold if self.controller.settings.useAutoThreshold else self.bestThreshold

    def distributionScores(self) -> Optional[np.ndarray]:
        """학습 이미지 점수 일부(그래프 분포). 점수 맵이 바뀔 때만 다시 만든다(합치는 데 메모리가 크다)."""
        if self._distribution is None and self.trainingScoreMaps:
            scores = np.concatenate([scoreMap.ravel() for scoreMap in self.trainingScoreMaps.values()])
            if scores.size > DISTRIBUTION_SAMPLE_SIZE:
                scores = np.random.default_rng(0).choice(scores, DISTRIBUTION_SAMPLE_SIZE, replace=False)
            self._distribution = scores
        return self._distribution

    def conditionCounts(self, keys: Set[str], excludePath: Optional[str] = None) -> ClassPixelCounts:
        """학습 조건 픽셀 수 — keys 중 목록에 있고 쓸 수 있는 라벨의 합. excludePath 는 컨트롤러가 따로 세므로 뺀다."""
        total = ClassPixelCounts()
        excludeKey = imageKey(excludePath) if excludePath else None
        for _, path in self.controller.listedImages():
            if imageKey(path) == excludeKey or imageKey(path) not in keys:
                continue
            summary = self.summaries.summary(path)
            if summary is not None and summary.isUsable:
                total = total.add(summary.counts)
        return total

    # ------------------------------------------------------------------ 학습
    def startTraining(self, keys: Set[str]) -> None:
        """'모델 학습', '재학습'. keys = 학습에 쓸 이미지 키(컨트롤러가 정한다). 이미지 → 픽셀 → 검사 → 알림 → 자식 프로세스.
        다른 작업이 도는 중이면 말없이 돌아오고, 쓸 이미지가 없거나 검사에서 걸리면 실패 알림."""
        if self.runningJob != JOB_NONE:
            return
        samples = self._collectTrainingImages(keys)
        if not samples:
            self._notifyFailure(FAILURE_NO_IMAGES, "")
            return
        settings = self.controller.settings
        try:
            spectra, isAbnormal = buildTrainingSamples(samples)        # 밴드 수가 다르면 ValueError
            validateInputs(spectra, isAbnormal, settings)
        except ValueError as error:
            self._notifyFailure(FAILURE_INVALID, str(error))
            return
        self._progressTotal = settings.aeEpochs + settings.epochs
        self._isCanceled = False
        self._trainingJobs = [(path, cube) for path, cube, _ in samples]
        self._pretrainEpochs = settings.aeEpochs
        text = self.controller.text
        getNotificationCenter().notify(NOTIFICATION_INFO, lambda: text("trainingStartedTitle"))
        # 시작할 때의 설정 복사본으로 학습한다(학습 중 설정을 고쳐도 흔들리지 않게)
        self._trainingSettings = dataclasses.replace(settings)
        self._setRunning(JOB_TRAINING)
        self._trainingStartTime = time.monotonic()
        self.controller.bar.setTrainingProgress(True, 0, self._progressTotal)
        self._runner = TrainingRunner(spectra, isAbnormal, self._trainingSettings, warmProcess=self.warmProcess)
        self._runner.progressSignal.connect(self._onProgress)
        self._runner.succeededSignal.connect(self._onTrained)
        self._runner.failedSignal.connect(lambda key, detail: self._finishJob(lambda: self._notifyFailure(key, detail)))
        self._runner.canceledSignal.connect(self._finishCanceled)
        self._startThread(self._runner)

    def cancelJob(self) -> None:
        """도는 작업을 취소한다(성공 신호가 오는 중이어도 _isCanceled 로 막는다). 도는 작업이 없으면 표시도 세우지 않는다 —
        늦게 온 취소 신호가 취소 알림을 띄우지 않게."""
        if self.runningJob == JOB_NONE:
            return
        self._isCanceled = True
        for worker in (self._runner, self._scorer):
            if worker is not None:
                worker.cancel()

    def _collectTrainingImages(self, keys: Set[str]) -> List[Tuple[str, np.ndarray, np.ndarray]]:
        """keys 중 쓸 수 있는 라벨이 있고 큐브가 라벨과 같은 크기인 이미지 [(경로, 큐브, 라벨)]. 큐브는 보정 배율을 적용해 넘긴다."""
        samples = []
        for number, path in self.controller.listedImages():
            if imageKey(path) not in keys:
                continue
            summary = self.summaries.summary(path)
            if summary is None or not summary.isUsable:
                continue
            label, cube = readLabel(path), self.controller.cubeOf(number)
            if label is None or cube is None or cube.shape[:2] != label.shape:
                continue                     # 학습에 못 쓴다
            samples.append((path, self.controller.cubeProvider(number, cube, self.controller.settings.calibrationRate)(), label))
        return samples

    def _onProgress(self, phase: str, epoch: float, total: int) -> None:
        """사전학습 + 본학습을 한 줄로 합쳐 바에 알린다. epoch 은 epoch 안 진행이면 소수."""
        done = epoch if phase == PHASE_PRETRAIN else self._pretrainEpochs + epoch
        self.controller.bar.setTrainingProgress(True, done, self._progressTotal)
        self.controller.bar.setTrainingRemaining(self._remainingText(done / self._progressTotal))

    def _remainingText(self, fraction: float) -> str:
        """남은 시간 = 걸린 시간과 진행 비율로 어림. 처음에는 준비 시간이 섞여 틀리므로 비워 둔다."""
        if fraction < REMAINING_MIN_FRACTION:
            return ""
        return self._formatRemaining((time.monotonic() - self._trainingStartTime) * (1 - fraction) / fraction)

    def _formatRemaining(self, seconds: float) -> str:
        text = self.controller.text
        if seconds >= SECONDS_PER_MINUTE:
            return text("remainingMinutes").replace("{minutes}", str(round(seconds / SECONDS_PER_MINUTE)))
        return text("remainingSeconds").replace("{seconds}", str(max(1, round(seconds))))

    def _onBatchProgress(self, done: int, total: int) -> None:
        """일괄 추론 진행 — 막대 + 남은 시간(첫 장의 준비 시간은 뺀다)."""
        self.controller.bar.setBatchProgress(True, done, total)
        if done == 1:
            self._batchFirstDoneTime = time.monotonic()
        isEstimable = BATCH_REMAINING_MIN_DONE <= done < total
        self.controller.bar.setBatchRemaining(self._formatRemaining(
            (time.monotonic() - self._batchFirstDoneTime) / (done - 1) * (total - done)) if isEstimable else "")

    def _onTrained(self, result) -> None:
        """학습 끝 → 같은 '학습 중' 안에서 학습 이미지 점수 맵까지 계산한다."""
        self._runner = None                  # 아직 프로세스를 정리 중일 수 있다 — _liveThreads 가 붙잡는다
        if self._isCanceled:
            self._finishCanceled()
            return
        self._pendingResult = result
        self._scoreTrainingImages()

    def _scoreTrainingImages(self) -> None:
        """새 모델로 학습 이미지 점수 맵을 계산한다."""
        result = self._pendingResult
        jobs = [(path, (lambda cube=cube: cube)) for path, cube in self._trainingJobs]
        self._scorer = InferenceWorker(None, jobs, modelFactory=lambda: modelFromResult(result, pickDevice()))
        self._scorer.finishedSignal.connect(self._onScored)
        self._scorer.failedSignal.connect(
            lambda path, detail: self._finishJob(lambda: self._notifyFailure(FAILURE_SCORING, detail)))
        self._scorer.canceledSignal.connect(self._finishCanceled)
        self._startThread(self._scorer)

    def _onScored(self, scoreMaps: Dict[str, np.ndarray]) -> None:
        """새 모델로 바꾼다. 이전 모델의 점수 맵, 사용자 임계값은 버린다(점수 척도가 모델마다 다르다).
        자동 임계값을 못 구하면 바꾸지 않고 실패로 끝낸다(이전 모델 유지)."""
        if self._isCanceled:
            self._finishCanceled()
            return
        try:
            autoThreshold = computeAutoThreshold(scoreMaps.values())
        except ValueError as error:
            detail = str(error)
            self._finishJob(lambda: self._notifyFailure(FAILURE_SCORING, detail))
            return
        self.model = self._scorer.model
        self.trainingScoreMaps = {imageKey(path): scoreMap for path, scoreMap in scoreMaps.items()}
        self._distribution = None
        self.scoreStore.clear()
        self.autoThreshold = autoThreshold
        self.bestThreshold = self._pendingResult.bestThreshold
        self.calibrationRate = self._pendingResult.calibrationRate
        self.userThreshold = self.previewThreshold = None
        self.pruneImages([path for _, path in self.controller.listedImages()])
        self.controller.onScoreMapsChanged()
        text = self.controller.text
        self._finishJob(lambda: getNotificationCenter().notify(
            NOTIFICATION_SUCCESS, lambda: text("trainingDoneTitle"), lambda: text("trainingDoneBody")))
        self.controller.bar.selectTab(TAB_MODEL)

    def _startThread(self, thread) -> None:
        """스레드를 시작하고 finished 까지 참조를 붙잡아 둔다(_liveThreads)."""
        self._liveThreads.add(thread)
        thread.finished.connect(lambda: self._liveThreads.discard(thread))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _finishJob(self, notify) -> None:
        self._runner = self._scorer = None
        self._pendingResult = None
        self._trainingJobs = []              # 큐브 참조를 놓는다
        self._batchPlanAtStart = {}
        self.controller.bar.setTrainingProgress(False)
        self.controller.bar.setBatchProgress(False)
        self._setRunning(JOB_NONE)
        self.prepareTraining(getattr(self.controller, "isEnabled", False))
        if notify is not None:
            notify()

    def _finishCanceled(self) -> None:
        """취소로 끝남 → 취소 알림. 앱 종료(shutdown)는 _isCanceled 를 세우지 않아 알리지 않는다."""
        job, isUserCancel = self.runningJob, self._isCanceled     # _finishJob 이 바꾸기 전에 읽는다
        self._finishJob(lambda: self._notifyCanceled(job) if isUserCancel else None)

    def _notifyCanceled(self, job: str) -> None:
        text = self.controller.text
        if job == JOB_BATCH:
            getNotificationCenter().notify(NOTIFICATION_INFO, lambda: text("batchCanceledTitle"),
                                           lambda: text("batchCanceledBody"))
        else:
            getNotificationCenter().notify(NOTIFICATION_INFO, lambda: text("trainingCanceledTitle"))

    def _setRunning(self, job: str) -> None:
        self.runningJob = job
        self.changed.emit()

    def _notifyFailure(self, reasonKey: str, detail: str, titleKey: str = TRAINING_TITLE_KEY) -> None:
        """실패 알림. 이유 문구는 언어 파일 '<training|inference>Failure_<키>', 그 아래 상세 한 줄."""
        text = self.controller.text
        prefix = "inferenceFailure_" if titleKey == INFERENCE_TITLE_KEY else "trainingFailure_"
        getNotificationCenter().notify(NOTIFICATION_FAILURE, lambda: text(titleKey),
                                       lambda: (text(prefix + reasonKey) or reasonKey) + ("\n" + detail if detail else ""))

    def notifyInferenceFailure(self, reasonKey: str, detail: str = "") -> None:
        self._notifyFailure(reasonKey, detail, INFERENCE_TITLE_KEY)

    # ------------------------------------------------------------------ 한 장 추론
    def partialBase(self, imageFolderPath: str, currentLabel: np.ndarray) -> np.ndarray:
        """'해당 클래스만' 추론의 바탕. 지금 라벨이 이전 추론 결과 그대로면 그때의 바탕, 아니면 지금 라벨."""
        stored = self.storedScore(imageFolderPath)
        if stored is not None and stored.baseLabel is not None and self.isAdjustable(imageFolderPath, currentLabel):
            return stored.baseLabel.astype(np.int64)
        return np.array(currentLabel, dtype=np.int64, copy=True)

    def startInference(self, imageNumber: int, imageFolderPath: str, cube: np.ndarray,
                       baseLabel: Optional[np.ndarray] = None) -> None:
        """'추론' 버튼. 점수 계산은 스레드에서 한다. baseLabel = '해당 클래스만' 의 바탕(None = 전부 덮어쓰기).
        모델이 없거나 다른 작업 중이면 말없이 돌아온다. SAL 이미지는 모델 대신 군집으로 원물 마스크를 만든다."""
        if self.runningJob != JOB_NONE or not self.hasModel:
            return
        self._isCanceled = False
        threshold, rule = self.threshold(), self.applyRuleFor(imageFolderPath)   # 시작할 때 값으로 고정
        worker = InferenceWorker(self.model, [(imageFolderPath, self.controller.cubeProvider(imageNumber, cube, self.calibrationRate))],
                                 salPaths=[imageFolderPath] if isSalImage(imageFolderPath) else [])
        worker.finishedSignal.connect(lambda scoreMaps: self._onInferred(imageNumber, imageFolderPath, scoreMaps, threshold, rule,
                                                                         baseLabel, worker.salMasks))
        worker.failedSignal.connect(lambda path, detail: self._finishJob(
            lambda: self.notifyInferenceFailure(INFERENCE_FAILURE_PROCESS, detail)))
        worker.canceledSignal.connect(lambda: self._finishJob(None))
        self._scorer = worker
        self._setRunning(JOB_INFERENCE)
        self._startThread(worker)

    def _onInferred(self, imageNumber: int, imageFolderPath: str, scoreMaps: Dict[str, np.ndarray], threshold: float, rule: ApplyRule,
                    baseLabel: Optional[np.ndarray] = None, salMasks: Optional[Dict[str, np.ndarray]] = None) -> None:
        """점수 맵 → 라벨 → 컨트롤러가 쓴다 → 썼으면 점수 맵 보관."""
        isCanceled = self._isCanceled
        self._finishJob(None)
        if isCanceled:
            return
        scoreMap = scoreMaps[imageFolderPath]
        label = overlayInferred(baseLabel, _labelOf(scoreMap, threshold, rule, (salMasks or {}).get(imageFolderPath)))
        if self.controller.applyInferenceLabel(imageNumber, imageFolderPath, label):
            self._remember(imageFolderPath, scoreMap, threshold, rule, baseLabel)
            self.controller.onScoreMapsChanged()

    def _remember(self, path: str, scoreMap: Optional[np.ndarray], threshold: float, rule, baseLabel) -> None:
        """쓴 추론 결과의 점수 맵을 보관한다(임계값 조절용). SAL 은 점수가 없어 보관하지 않는다."""
        if scoreMap is None:
            return
        self.scoreStore.put(path, scoreMap, threshold, rule, baseLabel)
        self._usedThresholds[imageKey(path)] = [threshold]

    # ------------------------------------------------------------------ 일괄 추론
    def startBatch(self, jobs, baseLabels: Optional[Dict[str, np.ndarray]] = None) -> None:
        """일괄 추론. jobs = [(번호, 경로, 큐브)], baseLabels = {경로: '해당 클래스만' 의 바탕}(None = 전부 덮어쓰기).
        끝날 때 한꺼번에 쓴다 — 취소, 실패면 아무것도 안 쓴다. 어떤 이미지를 넣는지는 컨트롤러가 trainingPlan.planBatch 로 정한다.
        임계값, 적용 규칙은 시작할 때 정해 둔다."""
        if self.runningJob != JOB_NONE or not self.hasModel or not jobs:
            return
        self._isCanceled = False
        threshold = self.threshold()           # 시작할 때 값으로 고정 — 도는 동안 설정을 바꿔도 결과가 흔들리지 않게
        bases = baseLabels or {}
        self._batchPlanAtStart = {path: (threshold, self.applyRuleFor(path), bases.get(path)) for _, path, _ in jobs}
        providers = [(path, self.controller.cubeProvider(number, cube, self.calibrationRate)) for number, path, cube in jobs]
        worker = InferenceWorker(self.model, providers, salPaths=[path for _, path, _ in jobs if isSalImage(path)])
        worker.progressSignal.connect(self._onBatchProgress)
        worker.finishedSignal.connect(lambda scoreMaps: self._onBatchScored(scoreMaps, worker.salMasks))
        worker.failedSignal.connect(lambda path, detail: self._finishJob(
            lambda: self._notifyBatchFailure("process", detail)))
        worker.canceledSignal.connect(self._finishCanceled)
        self._scorer = worker
        self._setRunning(JOB_BATCH)
        self.controller.bar.setBatchProgress(True, 0, len(jobs))
        self.controller.bar.setBatchRemaining("")
        self._startThread(worker)

    def _onBatchScored(self, scoreMaps: Dict[str, np.ndarray], salMasks: Optional[Dict[str, np.ndarray]] = None) -> None:
        """모두 계산됨 → 이미지마다 라벨을 만들어 쓴다. 그 사이 목록에서 뺀 이미지는 건너뛴다."""
        if self._isCanceled:
            self._finishCanceled()
            return
        plans = dict(self._batchPlanAtStart)
        # 번호는 지금 목록에서 다시 찾는다(도는 동안 목록이 바뀌면 같은 번호가 다른 이미지일 수 있다)
        numberOfKey = {imageKey(path): number for number, path in self.controller.listedImages()}
        written, failedNames = 0, []
        try:
            # 작업은 다 쓴 뒤에 끝낸다 — 먼저 끝내면 refresh 가 시작 라벨 사본을 비워 고친 이미지를 묻지 않고 덮어쓴다
            for path, scoreMap in scoreMaps.items():
                number = numberOfKey.get(imageKey(path))
                if number is None:
                    continue
                threshold, rule, baseLabel = plans[path]
                try:
                    label = overlayInferred(baseLabel, _labelOf(scoreMap, threshold, rule, (salMasks or {}).get(path)))
                    outcome = self.controller.writeBatchLabel(number, path, label)
                except Exception as error:               # 한 장이 실패해도 나머지는 쓴다(슬롯 예외는 앱을 끝낸다)
                    print("[autolabel] batch write failed:", path, error)
                    outcome = WRITE_FAILED
                if outcome == WRITE_DONE:
                    self._remember(path, scoreMap, threshold, rule, baseLabel)
                    written += 1
                elif outcome != WRITE_DECLINED:          # 사용자가 지키기로 한 이미지는 실패가 아니다
                    failedNames.append(os.path.basename(os.path.normpath(path)))
        finally:
            self._finishJob(None)
        text = self.controller.text
        if written:
            getNotificationCenter().notify(NOTIFICATION_SUCCESS, lambda: text("batchDoneTitle"),
                                           lambda: text("batchDoneBody").replace("{count}", str(written)))
        if failedNames:
            self._notifyBatchFailure("write", "", IMAGE_LIST_SEPARATOR.join(failedNames))
        self.controller.onScoreMapsChanged()

    def _notifyBatchFailure(self, reasonKey: str, detail: str = "", names: str = "") -> None:
        text = self.controller.text
        getNotificationCenter().notify(NOTIFICATION_FAILURE, lambda: text("batchFailedTitle"),
                                       lambda: (text("batchFailure_" + reasonKey) or reasonKey).replace("{names}", names)
                                       + ("\n" + detail if detail else ""))

    def notifyBatchProblem(self, reasonKey: str, names: str = "") -> None:
        self._notifyBatchFailure(reasonKey, "", names)

    def notifyPreviewDiscarded(self) -> None:
        text = self.controller.text
        getNotificationCenter().notify(NOTIFICATION_INFO, lambda: text("previewDiscardedTitle"), lambda: text("previewDiscardedBody"))

    def storedScore(self, imageFolderPath: Optional[str]) -> Optional[StoredScoreMap]:
        return self.scoreStore.get(imageFolderPath) if imageFolderPath else None

    def isAdjustable(self, imageFolderPath: Optional[str], currentLabel: np.ndarray) -> bool:
        """이 이미지 라벨이 보관한 점수 맵으로 만든 라벨 그대로인가(펜으로 고쳤으면 False).
        기록된 임계값뿐 아니라 썼던 임계값들도 본다 — 되돌리기 후 라벨과 기록이 어긋나 잠기는 것을 막는다. 맞는 값을 찾으면 기록을 되돌린다."""
        stored = self.storedScore(imageFolderPath)
        if stored is None:
            return False
        if stored.isLabelAt(currentLabel, stored.threshold):
            return True
        for threshold in reversed(self._usedThresholds.get(imageKey(imageFolderPath), [])):
            if threshold != stored.threshold and stored.isLabelAt(currentLabel, threshold):
                self.scoreStore.updateLabelSource(imageFolderPath, threshold, stored.rule)
                return True
        return False

    def _rememberThreshold(self, imageFolderPath: str, threshold: float) -> None:
        used = self._usedThresholds.setdefault(imageKey(imageFolderPath), [])
        if threshold in used:                                    # 같은 값은 가장 최근으로 옮긴다
            used.remove(threshold)
        used.append(threshold)

    def relabelWithThreshold(self, imageFolderPath: str, value: float, currentLabel: np.ndarray) -> Optional[np.ndarray]:
        """임계값을 놓았을 때. 라벨이 추론 결과 그대로면 새 임계값의 라벨을 돌려주고 기록을 바꾼다. 아니면 None —
        펜으로 고친 것을 덮어쓰지 않는다(바 잠금은 바로 갱신되지 않으므로 여기서 다시 확인한다)."""
        label = self._relabel(imageFolderPath, value, currentLabel)
        if label is not None:
            self.commitThreshold(value)
        return label

    def relabelWithCurrentThreshold(self, imageFolderPath: str, currentLabel: np.ndarray) -> Optional[np.ndarray]:
        """[자동] 을 켜거나 껐을 때 — 지금 쓰는 임계값으로 이 이미지 라벨을 다시 만든다(고른 값으로 굳히지 않는다).
        추론하지 않은 이미지, 라벨을 고친 이미지, 같은 값이면 None."""
        value, stored = self.threshold(), self.storedScore(imageFolderPath)
        if value is None or stored is None or value == stored.threshold:
            return None
        return self._relabel(imageFolderPath, value, currentLabel)

    def _relabel(self, imageFolderPath: str, value: float, currentLabel: np.ndarray) -> Optional[np.ndarray]:
        if not self.isAdjustable(imageFolderPath, currentLabel):
            return None
        stored = self.storedScore(imageFolderPath)
        self.scoreStore.updateLabelSource(imageFolderPath, value, stored.rule)
        self._rememberThreshold(imageFolderPath, value)
        return stored.labelAt(value)

    def inferenceDragPreview(self, imageFolderPath: Optional[str]) -> Optional[np.ndarray]:
        """추론한 이미지에서 슬라이더를 끄는 동안의 미리보기 라벨. 끄는 중이 아니면 None.
        직접 모드(자동 끔)면 '표시' 만 켠 클래스도 넣는다(어디가 그 클래스가 될지 보이게). 놓으면 적용한 클래스로만 만든다."""
        stored = self.storedScore(imageFolderPath)
        if stored is None or self.previewThreshold is None:
            return None
        settings, rule = self.controller.settings, stored.rule
        if not settings.useAutoApply:
            rule = ApplyRule(rule.applyNormal or settings.showNormal, rule.applyAbnormal or settings.showAbnormal,
                             rule.applyBackground or settings.showBackground)
        return stored.labelAt(self.previewThreshold, rule)

    def displayedThreshold(self, imageFolderPath: Optional[str]) -> Optional[float]:
        """임계값 칸에 보일 값: 추론한 이미지면 그 라벨을 만든 값, 아니면 지금 임계값."""
        stored = self.storedScore(imageFolderPath)
        return stored.threshold if stored is not None else self.threshold()

    def displayedScores(self, imageFolderPath: Optional[str]) -> Optional[np.ndarray]:
        """그래프 분포: 추론한 이미지면 그 이미지 점수, 아니면 학습 이미지 점수."""
        stored = self.storedScore(imageFolderPath)
        if stored is None:
            return self.distributionScores()
        scores = stored.scoreMap.ravel()
        if scores.size > DISTRIBUTION_SAMPLE_SIZE:
            scores = np.random.default_rng(0).choice(scores, DISTRIBUTION_SAMPLE_SIZE, replace=False)
        return scores

    def uncertainFor(self, imageFolderPath: Optional[str]) -> Optional[np.ndarray]:
        """불확실 픽셀(보여주기 전용): 추론한 이미지에서 지금 임계값 근처."""
        stored = self.storedScore(imageFolderPath)
        if stored is None:
            return None
        scoreMap = stored.scoreMap
        threshold = self.previewThreshold if self.previewThreshold is not None else stored.threshold
        key, cachedThreshold, cachedMap, mask = self._uncertainCache
        # 점수 맵은 id() 가 아니라 객체로 비교한다(지운 배열의 id 를 새 배열이 받을 수 있다)
        if key != imageKey(imageFolderPath) or cachedThreshold != threshold or cachedMap is not scoreMap:
            mask = uncertainMask(scoreMap, threshold)
            self._uncertainCache = (imageKey(imageFolderPath), threshold, scoreMap, mask)
        return mask

    # ------------------------------------------------------------------ 적용 규칙
    def applyRuleFor(self, imageFolderPath: str) -> ApplyRule:
        # 자동이 켜져 있으면 이미지의 case 로, 아니면 설정 체크대로(thresholdRules.applyRuleForImage)
        settings = self.controller.settings
        return applyRuleForImage(caseNumberFromImagePath(imageFolderPath), settings.useAutoApply,
                                 settings.applyNormal, settings.applyAbnormal, settings.applyBackground)

    def setThresholdChanging(self, value: float) -> None:
        self.previewThreshold = value

    def dropThresholdChanging(self) -> None:
        """끄는 중이던 값을 버린다(놓지 않고 탭을 바꾼 경우)."""
        self.previewThreshold = None

    def commitThreshold(self, value: float) -> None:
        """놓거나 입력한 값 = 앞으로 추론의 기본 임계값."""
        self.previewThreshold = None
        self.userThreshold = value

    def useAutoThreshold(self, isAuto: bool) -> None:
        """[자동] 켬 = 자동 임계값, 끔 = best. 사용자가 고른 값은 버린다."""
        self.controller.settings.useAutoThreshold = isAuto
        self.userThreshold = self.previewThreshold = None

    # ------------------------------------------------------------------ 이미지 목록, 종료
    def pruneImages(self, listedPaths: List[str]) -> None:
        """목록에 없는 이미지의 점수 맵, 요약을 지운다."""
        listedKeys = {imageKey(path) for path in listedPaths}
        for key in [key for key in self.trainingScoreMaps if key not in listedKeys]:
            del self.trainingScoreMaps[key]
            self._distribution = None
        self.summaries.keepOnly(listedKeys)
        self.scoreStore.keepOnly(listedKeys)
        self._usedThresholds = {key: used for key, used in self._usedThresholds.items() if key in listedKeys}

    def discardModel(self) -> None:
        """오토라벨링을 끔 — 모델과 점수 맵, 임계값을 버린다. 도는 작업은 취소한다(늦게 온 결과가 버린 모델을 되살리지 않게)."""
        self.cancelJob()
        self.model = None
        self.calibrationRate = CALIBRATION_RATE_DEFAULT
        self.autoThreshold = self.bestThreshold = self.userThreshold = self.previewThreshold = None
        self.trainingScoreMaps = {}
        self.scoreStore.clear()
        self._distribution = None
        self._uncertainCache = (None, None, None, None)
        self._usedThresholds = {}
        self.changed.emit()

    def prepareTraining(self, isEnabled: bool) -> None:
        """오토라벨링을 켜면 학습 자식을 미리 띄우고(import 시간을 미리 치른다), 끄면 끝낸다."""
        if not isEnabled:
            if self.runningJob != JOB_TRAINING:
                self.warmProcess.shutdown()
            return
        try:
            self.warmProcess.prepare()
        except Exception as error:           # 슬롯 예외는 앱을 끝낸다. 학습 버튼 때 다시 시도한다
            print("[autolabel] warm training process failed:", error)

    def shutdown(self) -> None:
        """앱 종료 — 자식 프로세스, 스레드를 끝낸다(살아 있는 QThread 가 지워지면 Qt 가 앱을 죽인다)."""
        self.warmProcess.shutdown()
        for worker in list(self._liveThreads):
            try:
                worker.cancel()
                worker.wait()
            except RuntimeError:             # 이미 끝나 지워진 스레드
                pass
