from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.services.vision_onnx import detect_products

router = APIRouter(prefix="/api/vision", tags=["vision"])


class VisionItem(BaseModel):
    class_id: int
    label: str
    label_en: str | None = None
    confidence: float
    bbox_xywh: list[float] | None = None


class VisionResponse(BaseModel):
    items: list[VisionItem]


@router.post("/detect-products", response_model=VisionResponse)
async def detect_products_by_image(
    image: UploadFile = File(...),
    top_k: int = Query(default=20, ge=1, le=100),
    conf_threshold: float | None = Query(default=None, ge=0.0, le=1.0),
) -> VisionResponse:
    content_type = (image.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Нужен файл изображения (image/*)")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Файл изображения пустой")

    try:
        items = detect_products(image_bytes=image_bytes, top_k=top_k, conf_threshold=conf_threshold)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ошибка инференса ONNX: {exc}") from exc

    return VisionResponse(items=[VisionItem(**x) for x in items])
