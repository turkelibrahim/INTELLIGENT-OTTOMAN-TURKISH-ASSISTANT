"""
Intelligent Ottoman Turkish Assistant — Ana Uygulama Giriş Noktası.
FastAPI uygulaması, middleware'ler ve startup olayları.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.api.router import api_router


class PrivateNetworkAccessMiddleware:
    """
    Chrome Private Network Access (PNA) desteği — raw ASGI middleware.
    Chrome 94+ tarayıcılar, localhost→localhost isteklerinde preflight isteğine
    'Access-Control-Request-Private-Network: true' header'ı ekler.
    
    Bu middleware:
    1. İstekteki PNA header'ını kaldırarak CORSMiddleware'in 400 döndürmesini önler.
    2. Yanıta 'Access-Control-Allow-Private-Network: true' ekler.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # İstekteki header'ları kontrol et
        headers = dict(scope.get("headers", []))
        has_pna = headers.get(b"access-control-request-private-network") == b"true"

        if has_pna:
            # PNA header'ını request'ten kaldır (CORSMiddleware 400 dönmesin)
            filtered_headers = [
                (k, v) for k, v in scope["headers"]
                if k != b"access-control-request-private-network"
            ]
            scope = dict(scope)
            scope["headers"] = filtered_headers

        # Yanıta PNA header'ını ekle
        if has_pna:
            async def send_with_pna(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"access-control-allow-private-network", b"true"))
                    message = {**message, "headers": headers}
                await send(message)
            await self.app(scope, receive, send_with_pna)
        else:
            await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapatma olayları."""
    # Startup: Veritabanı tablolarını oluştur
    print("Veritabani tablolari olusturuluyor...")
    init_db()
    print("Veritabani hazir")
    print(f"Yukleme dizini: {settings.UPLOAD_DIR}")
    yield
    # Shutdown
    print("Uygulama kapatiliyor...")

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


app = FastAPI(
    title=settings.APP_NAME,
    description="Osmanlıca belge işleme ve RAG tabanlı sohbet sistemi API'si",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chrome Private Network Access (PNA) middleware'i
# CORS middleware'den sonra eklenmeli ki istek akışında CORS'tan önce çalışsın
app.add_middleware(PrivateNetworkAccessMiddleware)

import uuid

class RequestIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        
        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        # Log correlation could be added here to a context variable
        await self.app(scope, receive, send_with_request_id)

app.add_middleware(RequestIdMiddleware)

import os

# Statik dosyalar (yüklenen dosyaları servis etmek için)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API router'ını dahil et
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Kök endpoint — API durumu."""
    return {
        "message": f"{settings.APP_NAME} API is running!",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrolü endpoint'i."""
    return {"status": "healthy", "version": settings.APP_VERSION}
