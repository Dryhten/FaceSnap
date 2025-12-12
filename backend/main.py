import sys
import io
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 导入 settings 时会自动设置 TORCH_HOME
from app.core.config import settings
from app.core.models import HealthResponse
from app.services.detection import DetectionService
from app.services.recognition import RecognitionService
from app.services.personnel import PersonnelService
from app.api.v1.endpoints.detect import router as detect_router, init_services as init_detect_services
from app.api.v1.endpoints.personnel import router as personnel_router, init_services as init_personnel_services

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

detection_service: DetectionService = None
recognition_service: RecognitionService = None
personnel_service: PersonnelService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detection_service, recognition_service, personnel_service
    
    logger.info("🚀 启动人脸检测服务...")
    
    try:
        detection_service = DetectionService()
        detection_service.initialize()
        
        recognition_service = RecognitionService()
        recognition_service.initialize()
        
        personnel_service = PersonnelService()
        personnel_service.initialize_database()
        
        init_detect_services(detection_service, recognition_service, personnel_service)
        init_personnel_services(personnel_service, recognition_service, detection_service)
        
        logger.info("✅ 服务启动完成")
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("服务正在关闭...")


app = FastAPI(
    title="人脸检测服务",
    description="统一的人脸检测、识别和人员信息查询API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    detect_router,
    prefix="/api/v1",
    tags=["人脸检测"]
)
app.include_router(
    personnel_router,
    prefix="/api/v1",
    tags=["人员管理"]
)

app.mount("/api/v1/faces", StaticFiles(directory=str(settings.FACES_DIR)), name="faces")


@app.get("/health", response_model=HealthResponse, summary="健康检查")
def health_check():
    return HealthResponse(
        status="healthy",
        service="face_detection_service",
        timestamp=__import__("time").time()
    )


@app.get("/", summary="根路径")
def root():
    return {
        "service": "人脸检测服务",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1/detect"
    }


if __name__ == "__main__":
    import uvicorn
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "WARNING",
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "WARNING",
            },
        },
    }
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_config=log_config
    )

