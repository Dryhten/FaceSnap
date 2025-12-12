from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.models import DetectResponse, FaceBox, PersonInfo, FaceResult
from app.services.detection import DetectionService
from app.services.recognition import RecognitionService
from app.services.personnel import PersonnelService
from app.utils.image import decode_image_from_bytes, validate_image

logger = logging.getLogger(__name__)
router = APIRouter()

detection_service: Optional[DetectionService] = None
recognition_service: Optional[RecognitionService] = None
personnel_service: Optional[PersonnelService] = None
_executor: Optional[ThreadPoolExecutor] = None


def init_services(
    detection: DetectionService,
    recognition: RecognitionService,
    personnel: PersonnelService
):
    global detection_service, recognition_service, personnel_service, _executor
    detection_service = detection
    recognition_service = recognition
    personnel_service = personnel
    
    import os
    max_workers = min(os.cpu_count() or 4, 8)
    _executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="face_detect")
    logger.debug(f"线程池执行器已初始化，工作线程数: {max_workers}")


@router.post("/detect", response_model=DetectResponse, summary="人脸检测")
async def detect_face(file: UploadFile = File(..., description="图片文件")):
    """上传图片，返回人脸检测结果和人员信息"""
    if not detection_service or not recognition_service or not personnel_service:
        raise HTTPException(
            status_code=500,
            detail="服务未初始化"
        )
    
    try:
        contents = await file.read()
        
        from app.core.config import settings
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大{settings.MAX_UPLOAD_SIZE}字节）"
            )
        
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
        if file_ext not in ['jpg', 'jpeg', 'png', 'bmp']:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式，请上传jpg、png或bmp格式的图片"
            )
        
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(_executor, decode_image_from_bytes, contents)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="无法解码图像文件，请确保文件格式正确"
            )
        
        if not validate_image(image):
            raise HTTPException(
                status_code=400,
                detail="图像格式无效，请确保图像尺寸足够大（至少20x20像素）"
            )
        
        logger.debug(f"处理图像: {file.filename}, 尺寸: {image.shape}")
        
        if _executor is None:
            raise HTTPException(
                status_code=500,
                detail="线程池执行器未初始化"
            )
        
        faces = await loop.run_in_executor(_executor, detection_service.detect_faces, image)
        
        if not faces:
            return DetectResponse(
                detected=False,
                faces=[]
            )
        
        # 按检测置信度降序排列
        faces.sort(key=lambda f: f.get("confidence", 0.0), reverse=True)
        
        logger.debug(f"检测到 {len(faces)} 个人脸")
        
        # 处理每个人脸，进行识别
        face_results = []
        for face in faces:
            face_box = FaceBox(
                x=face['x'],
                y=face['y'],
                w=face['w'],
                h=face['h'],
                confidence=face.get('confidence')
            )
            
            face_img = face['face_img']
            recognition_result = None
            person_info = None
            recognition_confidence = None
            
            try:
                recognition_result = await loop.run_in_executor(_executor, recognition_service.recognize, face_img)
            except Exception as e:
                logger.error(f"人脸识别过程出错: {e}", exc_info=True)
            
            if recognition_result:
                try:
                    face_id, confidence = recognition_result
                    recognition_confidence = confidence
                    logger.info(f"识别成功: {face_id} (置信度: {confidence:.3f})")
                    
                    try:
                        personnel_data = await loop.run_in_executor(
                            _executor,
                            personnel_service.get_personnel_by_face_id, 
                            face_id
                        )
                        if personnel_data:
                            person_info = PersonInfo(
                                name=personnel_data.get("name", ""),
                                id_number=personnel_data.get("id_number"),
                                phone=personnel_data.get("phone"),
                                address=personnel_data.get("address"),
                                gender=personnel_data.get("gender"),
                                category=personnel_data.get("category"),
                                status=personnel_data.get("status"),
                                photo_path=personnel_data.get("photo_path"),
                                created_at=personnel_data.get("created_at"),
                                updated_at=personnel_data.get("updated_at")
                            )
                            logger.debug(f"获取人员信息: {person_info.name}")
                        else:
                            logger.warning(f"未找到人员信息: face_id={face_id}")
                    except Exception as e:
                        logger.error(f"查询人员信息失败: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"处理识别结果失败: {e}", exc_info=True)
            
            face_results.append(FaceResult(
                face_box=face_box,
                person_info=person_info,
                recognition_confidence=recognition_confidence
            ))
        
        return DetectResponse(
            detected=True,
            faces=face_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理请求时出错: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"处理图像时出现错误: {str(e)}"
        )

