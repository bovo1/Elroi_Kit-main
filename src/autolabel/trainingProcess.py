"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 학습 — 자식 프로세스에서 도는 부분 (spawn 프로세스의 target).

    왜 별도 프로세스인가: 스레드로 학습하면 화면이 멈칫하고 메모리가 늘며 강제로 끊을 방법이 없다. 프로세스면 취소 = terminate.

    주고받는 것
        부모 → 자식 : 학습 픽셀(trainingPlan.buildTrainingSamples 결과), 설정
        자식 → 부모 : {PROGRESS_KEY: ...} 여러 번 → {RESULT_KEY: ...} 또는 {ERROR_KEY: 문구} → 맨 끝에 {FINISHED_KEY: True}
        모델은 파일로 저장하지 않는다 — 가중치를 numpy 로 넘기고 부모가 메모리에서 다시 만든다.
    부모가 죽으면 자식이 스스로 끝낸다(GPU 를 잡은 채 남지 않게).

    미리 띄워 두기: spawn 자식은 import 에 시간이 걸려, 오토라벨링을 켤 때 serveTraining 으로 먼저 띄워 두고
    버튼을 누르면 작업만 넘긴다. 자식 하나 = 학습 한 번.
"""

import importlib
import multiprocessing
import os
import queue
import traceback

FINISHED_KEY = "autoLabelTrainingFinished"   # 큐의 마지막 메시지
PROGRESS_KEY = "autoLabelProgress"
RESULT_KEY = "autoLabelResult"
ERROR_KEY = "autoLabelError"
ORPHAN_EXIT_CODE = 3


WARM_MODULES = ("autolabel.dsadModel",)    # 기다리는 동안 미리 import 할 모듈(torch 포함)
JOB_POLL_SECONDS = 1.0                       # 작업을 기다리며 부모 생존을 확인하는 간격


def serveTraining(target, jobQueue, messageQueue, warmModules=()) -> None:
    """미리 띄운 자식의 진입점: warmModules 를 먼저 import 하고 작업 하나를 기다렸다가 target 으로 학습한다.
    jobQueue 로 (spectra, isAbnormal, settings) 가 오고, target 은 결과를 messageQueue 로 보낸다."""
    for name in warmModules:
        importlib.import_module(name)
    while True:
        _exitIfParentGone()
        try:
            job = jobQueue.get(timeout=JOB_POLL_SECONDS)
        except queue.Empty:                      # 아직 작업이 없다 — 부모 확인 후 계속 기다린다
            continue
        except Exception as error:
            # 알리고 끝낸다 — 그냥 두면 부모가 끝없이 기다린다
            messageQueue.put({ERROR_KEY: "%s: %s" % (type(error).__name__, error)})
            messageQueue.put({FINISHED_KEY: True})
            return
        target(*job, messageQueue)
        return


def _exitIfParentGone() -> None:
    parent = multiprocessing.parent_process()
    if parent is not None and not parent.is_alive():
        os._exit(ORPHAN_EXIT_CODE)


def runAutoLabelTraining(spectra, isAbnormal, settings, messageQueue) -> None:
    """자식 프로세스 진입점. 메시지는 위 '주고받는 것' 대로, 어떤 예외든 ERROR_KEY 로 바꿔 보내고 끝 표시는 반드시 보낸다."""
    def onProgress(phase, epoch, total):
        _exitIfParentGone()
        messageQueue.put({PROGRESS_KEY: (phase, epoch, total)})

    try:
        from autolabel.dsadModel import pickDevice, trainDsad
        result = trainDsad(spectra, isAbnormal, settings, pickDevice(), progressCallback=onProgress)
        messageQueue.put({RESULT_KEY: result})
    except Exception as error:
        # 메시지를 먼저 — 창 앱에서는 stderr 출력이 예외를 낼 수 있다
        messageQueue.put({ERROR_KEY: "%s: %s" % (type(error).__name__, error)})
        try:
            traceback.print_exc()
        except Exception:
            pass
    finally:
        messageQueue.put({FINISHED_KEY: True})
