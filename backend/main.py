import sys
import io
import os
import logging
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 抑制 torchvision 图像扩展加载失败的警告（不影响功能，facenet-pytorch 使用 PIL 处理图像）
# 这个警告是因为 torchvision 的 C++ 扩展未加载，但我们使用 PIL/Pillow 处理图像，所以可以安全忽略
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision.io.image')

# 导入 settings 时会自动设置 TORCH_HOME
from app.core.config import settings
from app.core.models import HealthResponse
from app.services.detection import DetectionService
from app.services.recognition import RecognitionService
from app.services.personnel import PersonnelService
from app.api.v1.endpoints.detect import router as detect_router, init_services as init_detect_services
from app.api.v1.endpoints.personnel import router as personnel_router, init_services as init_personnel_services
from app.api.v1.endpoints.categories import router as categories_router, init_services as init_categories_services

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
    
    # 输出设备信息
    device_str = settings.DEVICE
    logger.info(f"📱 设备配置: {device_str}")
    if device_str.startswith("musa:"):
        try:
            import torch
            import torch_musa
            if hasattr(torch, "musa") and torch.musa.is_available():
                device_id = int(device_str.split(":")[1]) if ":" in device_str else 0
                if hasattr(torch.musa, "get_device_name"):
                    device_name = torch.musa.get_device_name(device_id)
                else:
                    device_name = "MUSA GPU"
                logger.info(f"   MUSA GPU 设备: {device_name}")
                if hasattr(torch.musa, "get_device_properties"):
                    props = torch.musa.get_device_properties(device_id)
                    if hasattr(props, "total_memory"):
                        logger.info(f"   MUSA GPU 内存: {props.total_memory / 1024**3:.2f} GB")
            else:
                logger.warning("   ⚠️  MUSA 设备不可用，将使用 CPU")
        except ImportError:
            logger.warning("   ⚠️  torch_musa 未安装，将使用 CPU")
        except Exception as e:
            logger.warning(f"   ⚠️  无法获取 MUSA GPU 信息: {e}")
    elif device_str.startswith("cuda:"):
        try:
            import torch
            if torch.cuda.is_available():
                device_id = int(device_str.split(":")[1]) if ":" in device_str else 0
                logger.info(f"   CUDA GPU 设备: {torch.cuda.get_device_name(device_id)}")
                logger.info(f"   CUDA GPU 内存: {torch.cuda.get_device_properties(device_id).total_memory / 1024**3:.2f} GB")
            else:
                logger.warning("   ⚠️  CUDA 设备不可用，将使用 CPU")
        except Exception as e:
            logger.warning(f"   ⚠️  无法获取 CUDA GPU 信息: {e}")
    elif device_str == "cpu":
        logger.info("   💻 使用 CPU 设备")
    
    try:
        detection_service = DetectionService()
        detection_service.initialize()
        
        recognition_service = RecognitionService()
        recognition_service.initialize()
        
        personnel_service = PersonnelService()
        personnel_service.initialize_database()
        
        init_detect_services(detection_service, recognition_service, personnel_service)
        init_personnel_services(personnel_service, recognition_service, detection_service)
        init_categories_services(personnel_service)
        
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
app.include_router(
    categories_router,
    prefix="/api/v1",
    tags=["人员类别"]
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

