from io import BytesIO

import numpy as np
import onnxruntime as ort
from PIL import Image

from app.config import get_settings
from app.services.vision_label_i18n import label_to_russian


_SESSION: ort.InferenceSession | None = None
_LABELS_CACHE: list[str] | None = None


def _get_session() -> ort.InferenceSession:
    global _SESSION
    if _SESSION is None:
        settings = get_settings()
        _SESSION = ort.InferenceSession(settings.vision_model_path, providers=["CPUExecutionProvider"])
    return _SESSION


def _load_labels() -> list[str]:
    global _LABELS_CACHE
    if _LABELS_CACHE is not None:
        return _LABELS_CACHE

    settings = get_settings()
    if not settings.vision_labels_path:
        _LABELS_CACHE = []
        return _LABELS_CACHE

    try:
        with open(settings.vision_labels_path, encoding="utf-8") as f:
            _LABELS_CACHE = [x.strip() for x in f if x.strip()]
    except OSError:
        _LABELS_CACHE = []
    return _LABELS_CACHE


def _label_en_by_id(class_id: int, labels: list[str]) -> str:
    if 0 <= class_id < len(labels):
        return labels[class_id]
    return f"class_{class_id}"


def _preprocess(image_bytes: bytes) -> np.ndarray:
    settings = get_settings()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img = img.resize((settings.vision_input_size, settings.vision_input_size))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, axis=0)
    return arr


def _to_xyxy(box_xywh: list[float]) -> tuple[float, float, float, float]:
    x, y, w, h = box_xywh
    half_w = w / 2.0
    half_h = h / 2.0
    return x - half_w, y - half_h, x + half_w, y + half_h


def _iou(box_a_xywh: list[float], box_b_xywh: list[float]) -> float:
    ax1, ay1, ax2, ay2 = _to_xyxy(box_a_xywh)
    bx1, by1, bx2, by2 = _to_xyxy(box_b_xywh)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def _classwise_nms(items: list[dict], iou_threshold: float) -> list[dict]:
    by_class: dict[int, list[dict]] = {}
    for item in items:
        by_class.setdefault(item["class_id"], []).append(item)

    kept: list[dict] = []
    for class_items in by_class.values():
        class_items.sort(key=lambda x: x["confidence"], reverse=True)
        accepted: list[dict] = []
        for cand in class_items:
            if all(_iou(cand["bbox_xywh"], prev["bbox_xywh"]) < iou_threshold for prev in accepted):
                accepted.append(cand)
        kept.extend(accepted)
    kept.sort(key=lambda x: x["confidence"], reverse=True)
    return kept


def _parse_detection_output(
    raw: np.ndarray,
    labels: list[str],
    top_k: int,
    conf_threshold: float | None = None,
) -> list[dict]:
    settings = get_settings()
    threshold = settings.vision_conf_threshold if conf_threshold is None else conf_threshold

    # Поддержка распространенных форматов:
    # 1) [1, B, 5+C] или [B, 5+C]
    # 2) YOLOv8 ONNX: [1, 4+C, B] (без objectness)
    data = raw
    if data.ndim == 3:
        data = data[0]

    if data.ndim != 2:
        return []

    # Приводим к [B, D]
    # Если это [D, B], где D небольшое (например 34/84), транспонируем.
    if data.shape[0] < data.shape[1] and data.shape[0] <= 512:
        data = data.T

    if data.shape[1] < 6:
        return []

    dim = data.shape[1]
    # Для моделей типа YOLOv8 ONNX часто D = 4 + num_classes (без objectness).
    # Если число классов известно из labels, используем это как главный признак.
    if labels and dim == 4 + len(labels):
        has_objectness = False
    elif labels and dim == 5 + len(labels):
        has_objectness = True
    else:
        # Фолбэк-эвристика: если 5-й столбец похож на probability [0..1], считаем objectness.
        col4 = data[:, 4]
        has_objectness = bool(np.all((col4 >= 0.0) & (col4 <= 1.0)))
    items: list[dict] = []
    for box in data:
        # bbox в формате xywh
        x, y, w, h = float(box[0]), float(box[1]), float(box[2]), float(box[3])
        if has_objectness:
            obj = float(box[4])
            cls_scores = box[5:]
        else:
            obj = 1.0
            cls_scores = box[4:]

        if cls_scores.size == 0:
            continue
        cls_id = int(np.argmax(cls_scores))
        cls_prob = float(cls_scores[cls_id])
        conf = obj * cls_prob
        if conf < threshold:
            continue
        en_label = _label_en_by_id(cls_id, labels)
        items.append(
            {
                "class_id": cls_id,
                "label": label_to_russian(en_label),
                "label_en": en_label,
                "confidence": round(conf, 4),
                "bbox_xywh": [x, y, w, h],
            }
        )
    items = _classwise_nms(items, iou_threshold=settings.vision_iou_threshold)
    return items[:top_k]


def _parse_classification_output(raw: np.ndarray, labels: list[str], top_k: int) -> list[dict]:
    flat = raw.reshape(-1)
    if flat.size == 0:
        return []
    idx = np.argsort(-flat)[:top_k]
    out = []
    for i in idx:
        class_id = int(i)
        en_label = _label_en_by_id(class_id, labels)
        out.append(
            {
                "class_id": class_id,
                "label": label_to_russian(en_label),
                "label_en": en_label,
                "confidence": round(float(flat[i]), 4),
            }
        )
    return out


def detect_products(image_bytes: bytes, top_k: int = 20, conf_threshold: float | None = None) -> list[dict]:
    session = _get_session()
    labels = _load_labels()
    inp = _preprocess(image_bytes)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: inp})
    if not outputs:
        return []

    raw = outputs[0]
    if isinstance(raw, list):
        raw = np.asarray(raw)
    if not isinstance(raw, np.ndarray):
        raw = np.asarray(raw)

    detection_like = (raw.ndim == 3 and raw.shape[-1] >= 6) or (raw.ndim == 2 and raw.shape[-1] >= 6)
    if detection_like:
        detected = _parse_detection_output(raw, labels, top_k=top_k, conf_threshold=conf_threshold)
        if detected:
            return detected

    return _parse_classification_output(raw, labels, top_k=top_k)
