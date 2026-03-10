from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from .api import characters, chat, auth
from .models.base import init_db

app = FastAPI(title="AIlover API", version="0.1.0")


@app.on_event("startup")
def startup():
    init_db()

ALLOWED_IMAGE_HOSTS = ("patchwiki.biligame.com", "i0.hdslb.com", "i1.hdslb.com", "i2.hdslb.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CHARACTERS_FILE = DATA_DIR / "characters.json"
IMAGES_DIR = DATA_DIR / "images"

app.include_router(characters.router, prefix="/api", tags=["characters"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

# 本地图片：请求 .png 时若不存在则回退到 .webp（兼容 JSON 里仍是 .png 的情况）
CACHE_HEADERS = {"Cache-Control": "public, max-age=31536000, immutable"}


@app.get("/api/images/{path:path}")
async def serve_image(path: str):
    path = path.lstrip("/")
    if ".." in path:
        return Response(status_code=404)
    if not IMAGES_DIR.exists():
        return Response(status_code=404)
    base = IMAGES_DIR / path
    if base.is_file():
        media_type = "image/webp" if path.lower().endswith(".webp") else None
        return FileResponse(base, media_type=media_type, headers=CACHE_HEADERS)
    if path.lower().endswith(".webp"):
        fallback = IMAGES_DIR / (path[: -5] + ".jpg")
        if fallback.is_file():
            return FileResponse(fallback, media_type="image/jpeg", headers=CACHE_HEADERS)
    for ext in (".png", ".jpg", ".jpeg"):
        if path.lower().endswith(ext):
            fallback = IMAGES_DIR / (path[: -len(ext)] + ".webp")
            if fallback.is_file():
                return FileResponse(fallback, media_type="image/webp", headers=CACHE_HEADERS)
            break
    return Response(status_code=404)


@app.get("/")
async def root():
    """根路径说明，实际接口在 /api 下"""
    return {
        "message": "AIlover API",
        "docs": "/docs",
        "api": "/api",
    }


@app.get("/api/image-proxy")
async def image_proxy(url: str = Query(..., description="图片 URL")):
    """代理外部图片，解决跨域与防盗链"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.hostname not in ALLOWED_IMAGE_HOSTS:
            return Response(status_code=403, content="Host not allowed")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AIlover/1.0)"})
            r.raise_for_status()
            return Response(content=r.content, media_type=r.headers.get("content-type", "image/png"))
    except Exception:
        return Response(status_code=502, content="Failed to fetch image")
