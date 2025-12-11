"""
人脸库管理API端点
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from pathlib import Path
from app.core.config import settings
from app.services.recognition import RecognitionService

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务实例（将在main.py中初始化）
recognition_service: RecognitionService = None


def init_services(recognition: RecognitionService):
    """初始化服务实例"""
    global recognition_service
    recognition_service = recognition


@router.get("/faces", summary="获取人脸库列表")
async def get_face_list():
    """
    获取人脸库列表（返回所有face_id）
    """
    try:
        faces_dir = settings.FACES_DIR
        if not faces_dir.exists():
            return []
        
        face_ids = []
        for file_path in faces_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                face_id = file_path.stem
                face_ids.append(face_id)
        
        return face_ids
        
    except Exception as e:
        logger.error(f"获取人脸库列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取人脸库列表失败: {str(e)}")


@router.delete("/faces/{face_id}", summary="删除人脸")
async def delete_face(face_id: str):
    """删除人脸"""
    if not recognition_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        # 从识别服务中移除
        recognition_service.remove_face(face_id)
        
        # 删除图片文件
        photo_path = settings.FACES_DIR / f"{face_id}.jpg"
        if photo_path.exists():
            photo_path.unlink()
        
        # 也尝试删除其他格式
        for ext in ['.png', '.jpeg']:
            alt_path = settings.FACES_DIR / f"{face_id}{ext}"
            if alt_path.exists():
                alt_path.unlink()
        
        return {"message": "删除成功"}
        
    except Exception as e:
        logger.error(f"删除人脸失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除人脸失败: {str(e)}")

