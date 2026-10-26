"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 바의 상태 규칙 (Qt 사용 안 함) — 어떤 버튼이 켜지는지, 꺼졌으면 왜인지, 브러시가 무엇을 하는지.

    화면 코드 안에 if 로 흩어 두지 않고, '지금 상태' 하나를 받아 '화면이 보여 줄 것' 하나를 돌려주는 순수 함수로 둔다.
    화면은 이 결과를 그리기만 한다.
        - 브러시: 오토라벨링이 켜져 있고 유사도 탭이면 클릭이 유사도 클릭이다. 다른 펜은 늘 원래대로.
        - 모델 탭, 추론, 일괄 추론은 학습한 모델이 있어야 켜진다. 일괄 추론은 필수 case 도 필요하다.
        - 모델 학습은 학습 case 이미지를 골랐고 학습 조건을 채웠을 때 켜진다(조건 계산은 trainingPlan, 여기는 결과만 받는다).
        - 학습, 추론, 일괄 추론은 한 번에 하나만 돈다.
        - 임계값 조절은 점수 맵이 있고 라벨이 추론 결과 그대로일 때만 켜진다. SAL 이미지는 임계값이 없어 늘 잠긴다.
        - 이미지를 고르지 않았으면 모두 잠긴다.
        - 꺼진 이유는 하나만 보여 준다(evaluateBar 의 분기 순서가 우선순위).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

TAB_SIMILARITY = "similarity"
TAB_MODEL = "model"

JOB_NONE = "none"
JOB_TRAINING = "training"
JOB_INFERENCE = "inference"
JOB_BATCH = "batch"

# 꺼진 이유 키 — 화면이 언어 파일 문구(main/autolabel/reason_<키>)로 바꾼다
REASON_NO_MODEL = "noModel"
REASON_BUSY = "busy"
REASON_NO_IMAGE = "noImage"
REASON_CONDITIONS = "conditions"
REASON_MISSING_CASES = "missingCases"        # 세부: 빠진 case 번호들
REASON_NO_SCORE_MAP = "noScoreMap"
REASON_LABEL_EDITED = "labelEdited"
REASON_TRAINING_CASE = "trainingCase"
REASON_SAL_IMAGE = "salImage"


@dataclass(frozen=True)
class BarInputs:
    """화면이 지금 상태를 모아 넘기는 값. 필드는 사실이고 판단은 이 모듈이 한다."""
    isEnabled: bool = False                    # 펜 툴바의 오토라벨링 켜기
    activeTab: str = TAB_SIMILARITY
    hasImage: bool = False                     # 이미지가 선택돼 있는가
    hasModel: bool = False                     # 학습한 모델이 메모리에 있는가
    isTrainingReady: bool = False              # 학습 조건을 모두 채웠는가
    runningJob: str = JOB_NONE
    missingCases: Tuple[int, ...] = ()         # 일괄 추론 필수 case 중 빠진 것
    imageHasScoreMap: bool = False             # 선택 이미지에 점수 맵이 있는가
    isLabelInferenceResult: bool = False       # 선택 이미지 라벨이 점수 맵 + 임계값 결과 그대로인가
    isSimilarityAssistOn: bool = True          # 설정 독 '보조 라벨링' — 끄면 유사도 탭에서도 원래 브러시
    isTrainingCase: bool = True                # 선택 이미지가 학습 버튼을 켤 수 있는 case 인가
    isSalImage: bool = False                   # 선택 이미지의 추론이 SAL(임계값 없음)인가


@dataclass(frozen=True)
class Control:
    """버튼 하나의 상태. reason 은 꺼졌을 때만(툴팁), details 는 이유의 세부."""
    enabled: bool
    reason: Optional[str] = None
    details: Tuple[int, ...] = ()


@dataclass(frozen=True)
class BarView:
    """화면이 그대로 그릴 결과."""
    isVisible: bool
    brushIsSimilarity: bool
    modelTab: Control
    train: Control
    infer: Control
    batch: Control
    thresholdAdjust: Control
    hasImage: bool = True                      # False 면 바 전체를 잠근다


def _jobLock(inputs: BarInputs) -> Optional[Control]:
    return Control(False, REASON_BUSY) if inputs.runningJob != JOB_NONE else None


def evaluateBar(inputs: BarInputs) -> BarView:
    """지금 상태 → 화면에 보일 것."""
    busy = _jobLock(inputs)
    modelTab = Control(True) if inputs.hasModel else Control(False, REASON_NO_MODEL)
    if not inputs.hasImage:
        # 모델 탭은 그대로 둔다 — 잠긴 모델 탭을 보면 refresh 가 유사도 탭으로 옮긴다(화면의 render 가 잠근다)
        noImage = Control(False, REASON_NO_IMAGE)
        return BarView(isVisible=inputs.isEnabled, brushIsSimilarity=False, modelTab=modelTab, train=noImage,
                       infer=noImage, batch=noImage, thresholdAdjust=noImage, hasImage=False)

    if not inputs.isTrainingCase:
        train = Control(False, REASON_TRAINING_CASE)
    elif not inputs.isTrainingReady:
        train = Control(False, REASON_CONDITIONS)
    else:
        train = busy or Control(True)

    if not inputs.hasModel:
        infer = Control(False, REASON_NO_MODEL)
    else:
        infer = busy or Control(True)

    if not inputs.hasModel:
        batch = Control(False, REASON_NO_MODEL)
    elif inputs.missingCases:
        batch = Control(False, REASON_MISSING_CASES, tuple(inputs.missingCases))
    else:
        batch = busy or Control(True)

    if inputs.isSalImage:
        thresholdAdjust = Control(False, REASON_SAL_IMAGE)
    elif busy:                                       # 도는 동안 바꾸면 끝에 쓰는 결과와 엇갈린다
        thresholdAdjust = busy
    elif not inputs.imageHasScoreMap:
        thresholdAdjust = Control(False, REASON_NO_SCORE_MAP)
    elif not inputs.isLabelInferenceResult:
        thresholdAdjust = Control(False, REASON_LABEL_EDITED)
    else:
        thresholdAdjust = Control(True)

    return BarView(
        isVisible=inputs.isEnabled,
        brushIsSimilarity=inputs.isEnabled and inputs.activeTab == TAB_SIMILARITY and inputs.hasImage
        and inputs.isSimilarityAssistOn,
        modelTab=modelTab, train=train, infer=infer, batch=batch, thresholdAdjust=thresholdAdjust)
