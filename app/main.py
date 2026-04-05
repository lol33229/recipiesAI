from fastapi import FastAPI

from app.routers import chat, description, nutrition, recommendations

app = FastAPI(title="KulinarAI API", version="0.1.0")

app.include_router(chat.router)
app.include_router(nutrition.router)
app.include_router(description.router)
app.include_router(recommendations.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
