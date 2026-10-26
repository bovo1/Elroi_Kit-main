"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링의 기본값과 규칙 상수를 한 곳에 모은다 (하드코딩 금지).
    값의 근거가 검증 결과면 그 문서 이름만 적고, 예시 값은 실제 데이터로 정한 것이 아니므로 바꿔도 된다.

    ── imagePath ────────────────────────────────────────────────
    이미지 폴더 경로를 비교용 키로 바꾼다 — 오토라벨링 코어 전체가 같은 규칙을 쓰게 한 곳에 둔다.
"""

import os
from dataclasses import dataclass
from typing import Tuple


# ---------------------------------------------------------------- 라벨 번호 (ElroiKit 라벨 규약)
LABEL_IGNORED = 0          # 무시, 아직 라벨 안 됨
LABEL_BACKGROUND = 1       # 배경
LABEL_NORMAL = 2           # 원물 = 정상. 모델 추론 결과의 '정상' 도 2
LABEL_ABNORMAL = 3         # 이물 = 비정상. 모델은 종류를 모르므로 추론 결과는 모두 3
ABNORMAL_LABEL_MIN = 3     # 이 번호 이상은 모두 이물(종류별 번호)

# ---------------------------------------------------------------- 미리보기
# 모델 결과(원물, 이물)의 색 — 그 이미지 라벨 목록에 해당 번호가 없을 때만 쓴다(이미지마다 라벨 번호 체계가 달라 흔하다)
MODEL_LABEL_DEFAULT_COLORS = {LABEL_NORMAL: (34, 160, 107), LABEL_ABNORMAL: (229, 72, 77)}
PREVIEW_OPACITY = 0.6      # 유사도, 임계값 조절 중 미리보기 불투명도

# ---------------------------------------------------------------- 유사도 (보조 라벨링)
# GLE 가중치 (RMSE 항, 비선형 항, Linf 항). 제품 기본과 다르다(similarity_labeling_validation)
SIMILARITY_GLE_WEIGHTS = (0.8, 0.1, 0.1)
# 점수 하한(임계값) 기본값 (similarity_labeling_validation)
SIMILARITY_DEFAULT_FLOOR = 85.0
# 클릭 한 번에 찍는 최대 픽셀 수 (설정 독 '클릭당 최대 픽셀 수')
SIMILARITY_DEFAULT_NORMAL_CAP = 100
SIMILARITY_DEFAULT_ABNORMAL_CAP = 20
# 공간 연결(클릭 지점과 이어진 덩어리만) — 이물만 켠다. 설정에서 뺐고 고정(결과정리_flood_비교)
SIMILARITY_ABNORMAL_FLOOD = True
SIMILARITY_NORMAL_FLOOD = False
# cap 과 공간 연결을 둘 다 켠 그룹에서 '상한 먼저' 결과가 '연결 먼저' 의 이 비율도 못 건지면 '연결 먼저' 로 바꾼다
SIMILARITY_AUTO_ORDER_RATIO = 0.5
# GLE 수식의 분모 보호용 작은 값
SIMILARITY_GLE_EPSILON = 1e-8

# ---------------------------------------------------------------- 학습 조건 (바의 세그먼트)
# 학습 버튼이 켜지는 최소 픽셀 수. 예시 값이다 — 실측으로 정한 값 아님(active_learning_validation 참고)
TRAINING_MIN_BACKGROUND_PIXELS = 300
TRAINING_MIN_NORMAL_PIXELS = 500
TRAINING_MIN_ABNORMAL_PIXELS = 100

# ---------------------------------------------------------------- 학습 데이터 구성
# 이미지 한 장에서 정상(배경+원물), 이물 각각 이만큼까지만 쓴다(넘으면 무작위). 추론 결과를 검토한 이미지는 전부 칠해져 있어 상한이 없으면 학습 데이터가 너무 커진다
TRAINING_MAX_PIXELS_PER_CLASS = 10000
TRAINING_SAMPLE_SEED = 0                # 같은 라벨이면 같은 학습 픽셀이 뽑히게 하는 고정 씨앗

# ---------------------------------------------------------------- 학습 기본값 (DSAD) — active_learning_validation 권장
TRAINING_DEFAULT_EPOCHS = 30
TRAINING_DEFAULT_AE_EPOCHS = 3
TRAINING_DEFAULT_BATCH_SIZE = 64
TRAINING_DEFAULT_NORMALIZATION = True
TRAINING_DEFAULT_LEARNING_RATE = 0.001
CALIBRATION_RATE_DEFAULT = 1.0       # 보정한 큐브 값에 곱하는 배율(학습 모드의 Calibration Rate 와 같은 뜻)
CALIBRATION_RATE_RANGE = (0.1, 1.0)   # 학습 모드의 입력 규칙에 맞춘 범위
TRAINING_DEFAULT_EARLY_STOP = True
TRAINING_DEFAULT_PATIENCE = 15
TRAINING_DEFAULT_NUM_LAYERS = 5
TRAINING_DEFAULT_REP_DIM = 64
BACKGROUND_LABEL_COLOR = (128, 128, 128)   # 배경 설정 색 기본값
TRAINING_MIN_BATCH_SIZE = 2      # 배치 1개짜리는 BatchNorm 이 학습 모드에서 예외를 낸다
TRAINING_MAX_BATCH_SIZE = 1024   # 설정 독 칸, 학습 전 검사의 위 한계

# ---------------------------------------------------------------- 일괄 추론 case 규칙
CASE_FOLDER_PREFIX = "case"
REQUIRED_CASES = (1, 2, 3, 4, 8)    # 모두 있어야 일괄 추론이 켜진다
OPTIONAL_CASES = (5, 6, 7)          # 있으면 같이 추론
ALL_CASES = tuple(sorted(REQUIRED_CASES + OPTIONAL_CASES))

# ---------------------------------------------------------------- 표시 및 적용 '자동'
# 자동이 켜져 있으면 이미지의 case 로 어느 쪽 라벨만 적용할지 정한다(thresholdRules.applyRuleForImage)
BACKGROUND_DATA_CASES = (1, 7)         # 배경만
PRODUCT_DATA_CASES = (2,)              # 원물만(추론은 SAL)
ABNORMAL_DATA_CASES = (3, 4, 5, 6, 8)  # 비정상만

# ---------------------------------------------------------------- 학습 대상, case2 추론
# 학습 대상 규칙은 trainingPlan.py 맨 위, 쓰는 곳은 autoLabelController._trainingKeys
TRAINING_CASE = 4                      # 학습 버튼은 이 case 이미지를 골랐을 때만 켜진다
TRAINING_EXTRA_CASES = (5, 6)          # TRAINING_CASE 와 같이 학습에 쓰는 case
SAL_CASE = 2                           # 이 case 의 '추론' 은 모델 대신 Simple Auto Labeling(임계값 없음)
SAL_EXPAND_KERNEL = 3                  # SAL 'Expand' 커널 크기

# ---------------------------------------------------------------- 일괄 추론 쓰기 결과 (이미지 한 장)
WRITE_DONE, WRITE_FAILED, WRITE_DECLINED = "done", "failed", "declined"   # 거절 = 도는 동안 고친 라벨을 지키려고 사용자가 거절

# ---------------------------------------------------------------- 불확실 표시 (보여주기 전용 — 라벨, 학습과 무관)
# 임계값의 점수 순위 위아래 이 비율 안의 픽셀을 '불확실' 로 보여 준다(active_learning_validation). 고정 점수 마진은 모델마다 구간이 달라 쓰지 않는다
UNCERTAIN_QUANTILE_HALF_WIDTH = 0.02
UNCERTAIN_COLOR = (245, 158, 11)       # 모델 결과 색과 구분되는 주황

# ---------------------------------------------------------------- 검토 표시 (재학습 대상)
# 추론으로 만든 라벨은 data.json 에 이 키를 남긴다. Ctrl+S 저장은 data.json 을 새로 써서 키가 사라진다 = 검토됨(labelFiles 참고)
LABEL_DATA_FILE_NAME = "data.json"
LABEL_FILE_NAME = "label.npy"
UNREVIEWED_INFERENCE_KEY = "autoLabelUnreviewedInference"

# ---------------------------------------------------------------- 추론
INFERENCE_BATCH_PIXELS = 8192       # 한 번에 모델에 넣는 픽셀 수(GPU 메모리 보호)


@dataclass
class AutoLabelSettings:
    """설정 독에서 사용자가 바꾸는 값. 기본값은 위 상수. dict 키 문자열은 오타가 조용히 기본값이 되어 dataclass 로 둔다."""
    # 라벨링 — 보조 라벨링(유사도)
    similarityAssist: bool = True          # 끄면 유사도 탭에서도 브러시는 원래대로 칠한다
    similarityFloor: float = SIMILARITY_DEFAULT_FLOOR
    normalCapPerClick: int = SIMILARITY_DEFAULT_NORMAL_CAP
    abnormalCapPerClick: int = SIMILARITY_DEFAULT_ABNORMAL_CAP
    # 학습 — 기본
    epochs: int = TRAINING_DEFAULT_EPOCHS
    aeEpochs: int = TRAINING_DEFAULT_AE_EPOCHS
    batchSize: int = TRAINING_DEFAULT_BATCH_SIZE
    normalization: bool = TRAINING_DEFAULT_NORMALIZATION
    calibrationRate: float = CALIBRATION_RATE_DEFAULT      # 학습, 점수 계산, 추론이 같은 배율을 쓴다
    # 학습 — 고급
    learningRate: float = TRAINING_DEFAULT_LEARNING_RATE
    earlyStop: bool = TRAINING_DEFAULT_EARLY_STOP
    patience: int = TRAINING_DEFAULT_PATIENCE
    numLayers: int = TRAINING_DEFAULT_NUM_LAYERS
    repDim: int = TRAINING_DEFAULT_REP_DIM
    # 임계값
    useAutoThreshold: bool = True
    # 표시 및 적용
    useAutoApply: bool = True              # 켜면 이미지의 case 로 적용할 클래스를 정한다
    applyNormal: bool = True               # 아래 apply*, show* 는 자동을 끈 직접 모드에서만 쓴다
    applyAbnormal: bool = True
    showNormal: bool = True                # 모델 미리보기에 보일 클래스
    showAbnormal: bool = True
    applyBackground: bool = True
    showBackground: bool = True
    showUncertain: bool = False            # 불확실 픽셀 보여 주기
    # 색
    normalColor: Tuple[int, int, int] = MODEL_LABEL_DEFAULT_COLORS[LABEL_NORMAL]
    abnormalColor: Tuple[int, int, int] = MODEL_LABEL_DEFAULT_COLORS[LABEL_ABNORMAL]
    backgroundColor: Tuple[int, int, int] = BACKGROUND_LABEL_COLOR
    uncertainColor: Tuple[int, int, int] = UNCERTAIN_COLOR


def imageKey(imageFolderPath: str) -> str:
    """경로 표기 차이(구분자, 대소문자, 끝의 구분자)가 있어도 같은 이미지는 같은 키가 되게 한다."""
    return os.path.normcase(os.path.normpath(imageFolderPath.rstrip("/\\")))
