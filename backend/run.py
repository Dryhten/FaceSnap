"""
使用 settings 配置启动 uvicorn 服务器
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # 配置 Uvicorn 日志，减少冗余输出
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
                "level": "WARNING",  # 只显示警告和错误
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "WARNING",  # 不显示访问日志
            },
        },
    }
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_config=log_config
    )

