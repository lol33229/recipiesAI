from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response

from app.config import get_settings
from app.routers import chat, description, nutrition, recommendations, recipes, vision
from app.services.recipe_store import recipe_source

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="KulinarAI API",
    version="0.3.0",
    description=(
        "AI-сервис: чат (Mistral), описания рецептов, vision, КБЖУ, рекомендации. "
        "Рецепты читаются из основного Recipes.API (GET); создание рецептов — в основном backend."
    ),
    openapi_tags=[
        {"name": "chat", "description": "Диалог с LLM"},
        {"name": "recipes", "description": "Прокси рецептов и подбор замен"},
        {"name": "description", "description": "Генерация текста описания"},
        {"name": "nutrition", "description": "Расчёт КБЖУ по справочнику"},
        {"name": "recommendations", "description": "Рекомендации (прототип)"},
        {"name": "vision", "description": "Детект продуктов на фото"},
    ],
    servers=[
        {"url": "http://127.0.0.1:8000", "description": "Локальная разработка"},
        {"url": "http://158.160.6.41:8000", "description": "Прод (укажите порт AI-сервиса за балансировщиком)"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(chat.router)
app.include_router(nutrition.router)
app.include_router(description.router)
app.include_router(recommendations.router)
app.include_router(recipes.router)
app.include_router(vision.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "recipe_source": recipe_source(),
        "main_api": settings.main_api_base_url,
    }
