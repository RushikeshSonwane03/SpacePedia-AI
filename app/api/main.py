from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logger import logger
from app.api.dependencies import limiter
from app.core.errors import rate_limit_handler, global_exception_handler

from app.api.routes import query, chat, meta

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

# Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

import time

# ... (Cors middleware)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Request: {request.method} {request.url.path} | IP: {client_ip} | Status: {response.status_code} | Time: {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(query.router, prefix=settings.API_V1_STR, tags=["Query"])
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["Chat"])
app.include_router(meta.router, prefix=f"{settings.API_V1_STR}/meta", tags=["Meta"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting SpacePedia AI API...")
    # Initialize Database Tables
    try:
        from app.db.session import engine
        from app.db.models import Base
        
        # Dry-run connection check
        from sqlalchemy import text
        logger.info("Verifying database connection...")
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified.")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created (if not existed).")
    except ImportError:
        logger.error("Could not import DB modules. Clean install?")
    except Exception as e:
        import socket
        if isinstance(e, socket.gaierror) or "Name or service not known" in str(e):
             logger.critical("CRITICAL-FAILURE: Database Hostname Resolution Failed.")
             logger.critical("Please check your DATABASE_URL. It seems 'localhost' or an invalid host was used.")
        
        logger.error(f"Database initialization failed: {e}")
        # We generally do not want to exit mostly, but if DB fails app is useless. 
        # But for Spaces, we might want to stay up to show health check error.
        pass

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/status")
async def status_check():
    db_status = "unknown"
    error_msg = None
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "failed"
        error_msg = str(e)
        logger.error(f"DB Check Failed: {e}")

    return {
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "error": error_msg
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
