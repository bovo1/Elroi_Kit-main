"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    라벨 파일 읽고 쓰기 — 추론 결과 표시(data.json), 추론 라벨 저장, 학습용 라벨 요약 (Qt 사용 안 함).

    ── labelReview ──────────────────────────────────────────────
    '검토 전 추론 라벨' 표시 — 재학습에 어떤 라벨을 쓸지 정하는 기준.
        - 추론으로 label.npy 를 쓰면 같은 폴더의 data.json 에 UNREVIEWED_INFERENCE_KEY 를 남긴다.
        - 사용자가 검토하고 Ctrl+S 로 저장하면 앱의 저장 코드가 data.json 을 새로 써서 키가 사라진다(저장 코드를 고치지 않고 동작).
        - 재학습은 이 키가 없는 라벨만 쓴다.
        - data.json 은 앱의 다른 코드도 읽으므로 label_info 키를 반드시 두고, 기존 키는 그대로 둔 채 필요한 것만 더해 다시 쓴다.

    ── inferenceWriter ──────────────────────────────────────────
    추론 결과를 이미지 한 장에 쓰는 유일한 경로(한 장 추론, 일괄 추론 공용). 앱의 저장(save_data)은 선택 이미지만 저장하고
    실패해도 예외를 내지 않아 쓰지 않는다. 쓰기가 실패하면 예외를 내서 부르는 쪽이 알리게 한다. 화면 갱신은 부르는 쪽(컨트롤러)이 맡는다.
        순서: data.json 표시 → label.npy → 라벨링 DB.
        표시를 먼저 쓰는 것은, 라벨만 쓰이고 표시가 실패하면 추론 결과가 검토된 라벨처럼 재학습에 섞이기 때문이다.

    ── trainingLabels ───────────────────────────────────────────
    학습에 쓸 라벨을 디스크에서 읽는다. 화면(메모리)의 라벨에는 저장 안 한 수정이 섞여 있어 기준이 될 수 없다.
    어느 case 를 쓰는지는 trainingPlan 이 정하고, 여기는 이미지 한 장의 라벨 요약만 낸다.
    라벨 배열은 크므로 파일 수정 시각이 같으면 픽셀 수 요약만 재사용하고 배열은 학습할 때 다시 읽는다.
"""

import json
import os
from dataclasses import dataclass
from typing import IO, Callable, Dict, Optional, Tuple

import numpy as np

from autolabel.autoLabelConfig import LABEL_DATA_FILE_NAME, LABEL_FILE_NAME, LABEL_IGNORED, UNREVIEWED_INFERENCE_KEY, imageKey
from autolabel.trainingPlan import ClassPixelCounts, countClassPixels


LABEL_INFO_KEY = "label_info"
DATA_INFO_KEY = "data_info"


def _dataJsonPath(imageFolderPath: str) -> str:
    return os.path.join(imageFolderPath, LABEL_DATA_FILE_NAME)


def _readDataJson(imageFolderPath: str) -> Optional[dict]:
    """data.json → dict. 없거나 json 이 아니면 빈 dict. 있는데 열지 못하면 None(일시 오류를 빈 내용으로 보고 덮으면 라벨 정보가 사라진다)."""
    try:
        with open(_dataJsonPath(imageFolderPath), "r", encoding="utf-8") as file:
            content = json.load(file)
    except (FileNotFoundError, ValueError):
        return {}
    except OSError:
        return None
    return content if isinstance(content, dict) else {}


def _replaceFile(path: str, mode: str, write: Callable[[IO], None], **openArguments) -> None:
    """임시 파일에 다 쓴 뒤 바꿔치기 — 쓰다 실패해도 원래 파일은 그대로다."""
    tempPath = path + ".tmp"
    try:
        with open(tempPath, mode, **openArguments) as file:
            write(file)
        os.replace(tempPath, path)
    except Exception:
        if os.path.exists(tempPath):
            os.remove(tempPath)
        raise


def markUnreviewedInference(imageFolderPath: str, labelInfoForNewLabels: Optional[Dict[int, dict]] = None,
                            keepNumbers: Optional[set] = None) -> None:
    """추론으로 라벨을 썼을 때 부른다. data.json 에 표시 키를 남기고 label_info 를 보장한다.
    labelInfoForNewLabels = {번호: {label_name, label_color}} (없으면 넣고 있으면 이름만 맞춘다),
    keepNumbers 를 주면 그 밖의 label_info 는 지운다."""
    content = _readDataJson(imageFolderPath)
    if content is None:
        raise OSError("data.json 을 읽지 못해 쓰지 않는다(라벨 이름 · 색을 지우지 않으려고): " + _dataJsonPath(imageFolderPath))
    content.setdefault(DATA_INFO_KEY, os.path.basename(os.path.normpath(imageFolderPath)))
    labelInfo = content.get(LABEL_INFO_KEY)
    if not isinstance(labelInfo, dict):
        labelInfo = {}
    for labelNumber, info in (labelInfoForNewLabels or {}).items():
        entry = labelInfo.setdefault(str(labelNumber), info)      # json 키는 문자열
        if isinstance(entry, dict):
            entry[LABEL_NAME_KEY] = info[LABEL_NAME_KEY]
    if keepNumbers is not None:
        labelInfo = {key: value for key, value in labelInfo.items() if key.lstrip("-").isdigit() and int(key) in keepNumbers}
    content[LABEL_INFO_KEY] = labelInfo
    content[UNREVIEWED_INFERENCE_KEY] = True
    _replaceFile(_dataJsonPath(imageFolderPath), "w", lambda file: json.dump(content, file, indent="\t", ensure_ascii=False),
                 encoding="utf-8")


def isUnreviewedInference(imageFolderPath: str) -> bool:
    """이 폴더의 라벨이 아직 검토 전 추론 결과인가."""
    return (_readDataJson(imageFolderPath) or {}).get(UNREVIEWED_INFERENCE_KEY) is True


LABEL_NAME_KEY = "label_name"        # DB label_list, data.json label_info 의 항목 이름
LABEL_COLOR_KEY = "label_color"


def modelLabelInfo(label: np.ndarray, existingLabelList: dict, defaults: Dict[int, dict]) -> Dict[int, dict]:
    """label 에 실제로 있는 모델 결과 번호의 {label_name, label_color}. 이름은 늘 defaults, 색은 이미지 라벨 목록에 있으면 그 색이다."""
    present = set(int(value) for value in np.unique(label))
    info = {}
    for number, default in defaults.items():
        if number in present:
            entry = existingLabelList.get(number) or default
            info[number] = {LABEL_NAME_KEY: default[LABEL_NAME_KEY], LABEL_COLOR_KEY: list(entry[LABEL_COLOR_KEY])}
    return info


def writeInferenceLabel(imageEntry: dict, folderPath: str, label: np.ndarray,
                        defaults: Dict[int, dict]) -> Tuple[Dict[int, dict], Dict[int, dict]]:
    """추론 라벨을 디스크, DB 에 쓴다. imageEntry = Core_DB_Labeling['image_list'] 의 항목.
    출력 : (쓴 모델 결과 라벨의 이름, 색, 라벨에 픽셀이 없어져 목록에서 뺀 클래스의 이름, 색 — 되돌리기용).
    쓰기가 실패하면 DB 는 바꾸지 않은 채 예외를 올린다(표시는 남을 수 있지만 재학습에서 빠질 뿐이다)."""
    label = np.asarray(label, dtype=np.int64)
    labelList = imageEntry['label_list']
    info = modelLabelInfo(label, labelList, defaults)
    keep = set(int(value) for value in np.unique(label)) | {LABEL_IGNORED}
    # 표시를 먼저(라벨 쓰기가 실패해도 '검토 전' 이 남게), 없어진 클래스 정리는 라벨을 쓴 뒤
    markUnreviewedInference(folderPath, {number: dict(entry) for number, entry in info.items()})
    _replaceFile(os.path.join(folderPath, LABEL_FILE_NAME), "wb", lambda file: np.save(file, label))
    imageEntry['image_info']['image_label'] = label.copy()      # DB 도 같게 — 다음 Ctrl+S 가 옛 라벨로 덮지 않게
    imageEntry['image_info']['image_label_origin'] = label.copy()
    removed = {number: dict(entry) for number, entry in labelList.items() if number not in keep}
    for number in removed:
        del labelList[number]
    addModelLabelsToList(labelList, info)
    try:
        markUnreviewedInference(folderPath, keepNumbers=keep)
    except OSError as error:                                    # 정리는 덤 — 실패해도 라벨, DB 는 이미 같다
        print("[autolabel] vanished label info cleanup failed:", folderPath, error)
    return info, removed


def addModelLabelsToList(labelList: dict, info: Dict[int, dict]) -> None:
    """DB 라벨 목록에 모델 결과 번호를 넣는다(있으면 이름만 맞춘다)."""
    for number, entry in info.items():
        labelList.setdefault(number, {**entry, LABEL_COLOR_KEY: list(entry[LABEL_COLOR_KEY])})[LABEL_NAME_KEY] = entry[LABEL_NAME_KEY]


@dataclass(frozen=True)
class LabelSummary:
    """저장된 라벨 한 장의 요약. isUsable = 재학습에 쓸 수 있는가."""
    counts: ClassPixelCounts
    isUnreviewedInference: bool

    @property
    def isUsable(self) -> bool:
        total = self.counts.background + self.counts.normal + self.counts.abnormal
        return not self.isUnreviewedInference and total > 0


def _modifiedTime(path: str) -> Optional[int]:
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def readLabel(imageFolderPath: str) -> Optional[np.ndarray]:
    """저장된 label.npy → (H, W) int64. 없거나 못 읽으면 None.
    앱은 label.npy 없는 폴더를 열 때 0 배열을 저장하므로 '파일 있음' 이 아니라 '0 아닌 픽셀' 로 판단해야 한다."""
    try:
        return np.load(os.path.join(imageFolderPath, LABEL_FILE_NAME)).astype(np.int64, copy=False)
    except (OSError, ValueError):
        return None


class TrainingLabelSummaries:
    """이미지 폴더 → LabelSummary. 파일 수정 시각이 같으면 다시 읽지 않는다."""

    def __init__(self):
        self._cache: Dict[str, Tuple[Tuple[Optional[int], Optional[int]], Optional[LabelSummary]]] = {}

    def summary(self, imageFolderPath: str) -> Optional[LabelSummary]:
        """요약. label.npy 가 없거나 못 읽으면 None."""
        key = imageKey(imageFolderPath)
        stamp = (_modifiedTime(os.path.join(imageFolderPath, LABEL_FILE_NAME)),
                 _modifiedTime(os.path.join(imageFolderPath, LABEL_DATA_FILE_NAME)))
        cached = self._cache.get(key)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        label = readLabel(imageFolderPath)
        result = None if label is None else LabelSummary(countClassPixels(label), isUnreviewedInference(imageFolderPath))
        self._cache[key] = (stamp, result)
        return result

    def keepOnly(self, imageKeys) -> None:
        """목록에 남은 이미지(키)만 기억한다."""
        self._cache = {key: value for key, value in self._cache.items() if key in imageKeys}
