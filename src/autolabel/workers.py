"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    화면 스레드 밖에서 도는 작업들 — 유사도 계산, 여러 장 추론, 학습 프로세스 실행기 (Qt 스레드).

    SimilarityWorker : 브러시 클릭마다 GLE 점수 맵을 화면 스레드 밖에서 계산한다(화면이 멈칫하지 않게). 클릭은 큐에 쌓아
        차례로 처리하고, 이미지 큐브는 장치(GPU)에 한 번만 올려 같은 이미지의 클릭에 다시 쓴다.
    InferenceWorker  : 여러 장 추론(모델 또는 SAL).
    WarmTrainingProcess, TrainingRunner : 학습 자식 프로세스를 띄우고 메시지를 읽어 시그널로 넘긴다. 학습 모드의
        Training_Thread 를 쓰지 않는 이유는 마지막 메시지 유실, 자식이 일찍 죽어도 '끝남' 보고, 학습 모드 결과 탭 오염 때문이다.
        어떤 예외가 나도 성공, 실패, 취소 중 하나는 반드시 알린다 — 아니면 화면이 '학습 중' 에 멈춘다.
        스레드 객체는 finished 시그널 뒤에 지워야 한다(결과 시그널 뒤에도 프로세스 정리가 남아 있다).
"""

import multiprocessing
import queue
import threading
import time
from typing import Callable, Collection, Dict, List, Tuple

import numpy as np
from PyQt5 import QtCore

from autolabel.autoLabelConfig import SAL_EXPAND_KERNEL, SIMILARITY_GLE_WEIGHTS
from autolabel.dsadModel import pickDevice, scoreMapForCube
from autolabel.similarityCore import gleScoreMap, prepareSpectra
from autolabel.trainingProcess import (ERROR_KEY, FINISHED_KEY, PROGRESS_KEY, RESULT_KEY, WARM_MODULES, runAutoLabelTraining,
                                      serveTraining)


_STOP = object()
_RELEASE = object()


class SimilarityWorker(QtCore.QThread):
    """request(imageKey, cube, row, col, labelNumber) 를 받아 scoreReadySignal(imageKey, row, col, labelNumber, 점수 맵),
    실패하면 failedSignal(한 줄)."""
    scoreReadySignal = QtCore.pyqtSignal(str, int, int, int, object)
    failedSignal = QtCore.pyqtSignal(str)

    def __init__(self, weights=SIMILARITY_GLE_WEIGHTS):
        super().__init__()
        self.weights = weights
        self._jobs = queue.Queue()

    def request(self, imageKey: str, cube, row: int, col: int, labelNumber: int) -> None:
        """클릭 한 번을 맡긴다. 큐브는 복사하지 않고 참조를 넘긴다."""
        self._jobs.put((imageKey, cube, row, col, labelNumber))
        if not self.isRunning():
            self.start()

    def releaseImage(self) -> None:
        """장치에 올려 둔 큐브를 내려놓는다."""
        self._jobs.put(_RELEASE)

    def stop(self) -> None:
        """남은 클릭은 버리고 스레드를 끝낸다."""
        while True:                          # 남은 클릭을 먼저 버린다 — 안 그러면 남은 계산을 다 하고서야 끝난다
            try:
                self._jobs.get_nowait()
            except queue.Empty:
                break
        self._jobs.put(_STOP)
        self.wait()

    def run(self) -> None:
        cachedKey, cachedSpectra = None, None
        while True:
            job = self._jobs.get()
            if job is _STOP:
                return
            if job is _RELEASE:
                cachedKey, cachedSpectra = None, None
                continue
            imageKey, cube, row, col, labelNumber = job
            try:
                if imageKey != cachedKey:                    # 장치 준비 실패도 클릭 실패로 알린다
                    cachedKey, cachedSpectra = imageKey, prepareSpectra(cube, pickDevice())
                score = gleScoreMap(cachedSpectra, row * cube.shape[1] + col, cube.shape[:2], self.weights)
                self.scoreReadySignal.emit(imageKey, row, col, labelNumber, score)
            except Exception as error:
                self.failedSignal.emit("%s: %s" % (type(error).__name__, error))


class InferenceWorker(QtCore.QThread):
    """여러 장을 차례로 추론한다.

    model 대신 modelFactory 를 주면 이 스레드에서 모델을 만든다(화면이 멈추지 않게, 만든 모델은 끝난 뒤 self.model).
    jobs = [(이미지 경로, 큐브를 돌려주는 함수)]. salPaths 의 이미지는 모델 대신 SAL(salProductMask)로 처리한다.
    finishedSignal 은 모두 성공했을 때만 {경로: 점수 맵}(SAL 은 None, 원물 마스크는 self.salMasks). 실패, 취소하면 결과는 버린다.
    """
    progressSignal = QtCore.pyqtSignal(int, int)      # (끝난 장수, 전체 장수) — 시작할 때 (0, 전체)를 먼저 보낸다
    finishedSignal = QtCore.pyqtSignal(object)
    failedSignal = QtCore.pyqtSignal(str, str)        # (멈춘 이미지 경로, 오류 한 줄) — 모델 생성 실패면 경로 ""
    canceledSignal = QtCore.pyqtSignal()

    def __init__(self, model, jobs: List[Tuple[str, Callable[[], np.ndarray]]], modelFactory: Callable[[], object] = None,
                 salPaths: Collection[str] = ()):
        super().__init__()
        self.model = model
        self.modelFactory = modelFactory
        self.jobs = list(jobs)
        self._isCanceled = False
        self.salMasks: Dict[str, np.ndarray] = {}
        self.salPaths = set(salPaths)

    def cancel(self) -> None:
        """다음 이미지로 넘어가기 전에 멈춘다(한 장 계산 중에는 끊지 않는다)."""
        self._isCanceled = True

    def run(self) -> None:
        currentPath = ""
        try:
            results: Dict[str, np.ndarray] = {}
            if self.model is None:
                self.model = self.modelFactory()
            self.progressSignal.emit(0, len(self.jobs))
            for index, (imagePath, cubeProvider) in enumerate(self.jobs):
                if self._isCanceled:
                    self.canceledSignal.emit()
                    return
                currentPath = imagePath
                cube = cubeProvider()
                if imagePath in self.salPaths:
                    results[imagePath] = None
                    self.salMasks[imagePath] = salProductMask(cube)
                else:
                    results[imagePath] = scoreMapForCube(self.model, cube)
                self.progressSignal.emit(index + 1, len(self.jobs))
            if self._isCanceled:
                self.canceledSignal.emit()
                return
            self.finishedSignal.emit(results)
        except Exception as error:
            self.failedSignal.emit(currentPath, "%s: %s" % (type(error).__name__, error))


def salProductMask(cube: np.ndarray) -> np.ndarray:
    """case2 의 '추론' — 유틸리티 탭 Simple Auto Labeling 과 같은 계산(KMeans 두 무리 중 스펙트럼이 낮은 쪽을 원물로, 영역 확장).
    (H, W, B) 큐브 → (H, W) bool, True = 원물. 군집이 실패하면 RuntimeError."""
    import cv2
    from utils.advanced import simplelabeling        # 무거워서 쓸 때 import
    height, width, _ = cube.shape
    result = simplelabeling(cube, np.zeros((height, width)))
    if not result[0]:
        raise RuntimeError(result[1])
    _, _, centers, assignment = result
    # SAL 과 같은 비교(밴드별로 중심이 더 큰 쪽이 많은 무리가 '높은' 스펙트럼) — 다른 쪽이 원물
    productCluster = 1 if np.sum(centers[0] > centers[1]) >= np.sum(centers[1] > centers[0]) else 0
    product = (assignment == productCluster).reshape(height, width).astype(np.uint8)
    kernel = np.ones((SAL_EXPAND_KERNEL, SAL_EXPAND_KERNEL), np.uint8)
    return cv2.dilate(product, kernel, iterations=1).astype(bool)


QUEUE_POLL_SECONDS = 0.2          # 큐를 기다리는 최대 시간(그동안 안 오면 프로세스 생존을 본다)
PROCESS_EXIT_GRACE_SECONDS = 2.0  # 끝 표시 없이 죽은 프로세스의 남은 메시지를 더 읽어 볼 시간

# 실패 이유 키 — 화면이 언어 파일 문구로 바꾼다
FAILURE_PROCESS_ERROR = "processError"
FAILURE_PROCESS_EXITED = "processExited"
FAILURE_NO_RESULT = "noResult"
FAILURE_RUNNER_ERROR = "runnerError"


class WarmTrainingProcess:
    """학습 자식 프로세스를 미리 하나 띄워 둔다(trainingProcess 설명 참고). Qt 를 쓰지 않아 어느 스레드에서 불러도 된다.
    take() 는 (프로세스, 작업 큐, 메시지 큐)를 꺼내 주며 학습 한 번에 쓴다."""

    def __init__(self, target=runAutoLabelTraining):
        self.target = target
        self._slot = None
        self._lock = threading.Lock()          # take 는 실행기 스레드, 나머지는 화면 스레드에서 불린다

    def prepare(self) -> None:
        with self._lock:
            self._prepareLocked()

    def _prepareLocked(self) -> None:
        if self._slot is not None and self._slot[0].is_alive():
            return
        self._closeSlot()                       # 죽은 자식의 큐 정리
        context = multiprocessing.get_context("spawn")
        jobQueue, messageQueue = context.Queue(), context.Queue()
        # daemon: 부모가 정상 종료되면 자식도 끝난다
        process = context.Process(name="AutoLabel Training", target=serveTraining, daemon=True,
                                  args=(self.target, jobQueue, messageQueue,
                                        WARM_MODULES if self.target is runAutoLabelTraining else ()))
        process.start()
        self._slot = (process, jobQueue, messageQueue)

    def take(self):
        with self._lock:
            self._prepareLocked()
            slot, self._slot = self._slot, None
        return slot

    def shutdown(self) -> None:
        with self._lock:
            self._closeSlot()

    def _closeSlot(self) -> None:
        if self._slot is None:
            return
        process, jobQueue, messageQueue = self._slot
        self._slot = None
        if process.is_alive():
            process.terminate()
            process.join(timeout=PROCESS_EXIT_GRACE_SECONDS)
        closeQueue(jobQueue)
        closeQueue(messageQueue)


def closeQueue(messageQueue) -> None:
    """큐를 닫는다. 안 읽는 큐에 큰 작업이 남아 있으면 보내는 스레드가 막혀 앱 종료가 멈추므로, 남은 것은 버리고 기다리지 않는다."""
    messageQueue.cancel_join_thread()
    messageQueue.close()


class TrainingRunner(QtCore.QThread):
    """학습 한 번을 맡는 스레드. start() 로 시작, cancel() 로 중단. 성공하면 succeededSignal(DsadTrainingResult),
    실패하면 failedSignal(FAILURE_* 키, 상세 한 줄), 취소하면 canceledSignal."""
    progressSignal = QtCore.pyqtSignal(str, float, int)   # (단계, epoch — epoch 안 진행은 소수, 전체)
    succeededSignal = QtCore.pyqtSignal(object)
    failedSignal = QtCore.pyqtSignal(str, str)
    canceledSignal = QtCore.pyqtSignal()

    def __init__(self, spectra, isAbnormal, settings, processTarget=None, warmProcess: WarmTrainingProcess = None):
        """warmProcess 가 없으면 지금 띄운다. processTarget 은 테스트에서 가짜 자식 함수를 넣는 용도(warmProcess 가 있으면 무시)."""
        super().__init__()
        self.spectra = spectra
        self.isAbnormal = isAbnormal
        self.settings = settings
        self.warmProcess = warmProcess or WarmTrainingProcess(processTarget or runAutoLabelTraining)
        self._isCanceled = False
        self._process = None

    def cancel(self) -> None:
        """자식 프로세스를 terminate 한다. 다음 학습용 자식은 ModelFlow._finishJob 이 다시 띄운다."""
        self._isCanceled = True
        if self._process is not None and self._process.is_alive():
            self._process.terminate()

    def run(self) -> None:
        messageQueue = jobQueue = None
        try:
            self._process, jobQueue, messageQueue = self.warmProcess.take()
            jobQueue.put((self.spectra, self.isAbnormal, self.settings))
            self.spectra = self.isAbnormal = None          # 자식에 넘겼으니 부모 쪽 참조는 놓는다
            self._emitOutcome(*self._readUntilFinished(messageQueue))
        except Exception as error:
            if self._isCanceled:
                self.canceledSignal.emit()
            else:
                self.failedSignal.emit(FAILURE_RUNNER_ERROR, "%s: %s" % (type(error).__name__, error))
        finally:
            self._cleanUp(messageQueue)
            if jobQueue is not None:
                closeQueue(jobQueue)

    def _readUntilFinished(self, messageQueue):
        """끝 표시, 취소, 자식의 비정상 종료 중 하나까지 큐를 읽어 (결과, 실패)를 돌려준다."""
        result, failure = None, None
        exitDeadline = None
        while not self._isCanceled:
            try:
                message = messageQueue.get(timeout=QUEUE_POLL_SECONDS)
            except queue.Empty:
                if self._process.is_alive():
                    continue
                # 끝 표시 없이 죽었으면 파이프에 남은 메시지를 잠깐 더 읽어 보고 포기한다
                exitDeadline = exitDeadline or time.monotonic() + PROCESS_EXIT_GRACE_SECONDS
                if time.monotonic() > exitDeadline:
                    return result, failure or (FAILURE_PROCESS_EXITED, str(self._process.exitcode))
                continue
            if FINISHED_KEY in message:
                return result, failure
            if ERROR_KEY in message:
                failure = (FAILURE_PROCESS_ERROR, str(message[ERROR_KEY]))
            elif RESULT_KEY in message:
                result = message[RESULT_KEY]
            elif PROGRESS_KEY in message:
                self.progressSignal.emit(*message[PROGRESS_KEY])
        return result, failure

    def _emitOutcome(self, result, failure) -> None:
        """결과를 먼저 알린다 — 프로세스 정리를 기다리게 하지 않으려고."""
        if self._isCanceled:
            self.canceledSignal.emit()
        elif failure:
            self.failedSignal.emit(*failure)
        elif result is None:
            self.failedSignal.emit(FAILURE_NO_RESULT, "")
        else:
            self.succeededSignal.emit(result)

    def _cleanUp(self, messageQueue) -> None:
        """자식 프로세스와 큐를 정리한다(남아 있으면 강제로 끝낸다)."""
        if self._process is not None:
            self._process.join(timeout=PROCESS_EXIT_GRACE_SECONDS)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=PROCESS_EXIT_GRACE_SECONDS)
        if messageQueue is not None:
            messageQueue.close()
