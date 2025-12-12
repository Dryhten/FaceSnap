"""
人员管理API端点
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from typing import Optional, List
import logging
from pathlib import Path
import cv2
from PIL import Image as PILImage

from app.services.personnel import PersonnelService
from app.services.recognition import RecognitionService
from app.services.detection import DetectionService
from app.core.config import settings
from app.utils.image import decode_image_from_bytes, validate_image

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务实例（将在main.py中初始化）
personnel_service: Optional[PersonnelService] = None
recognition_service: Optional[RecognitionService] = None
detection_service: Optional[DetectionService] = None


def init_services(
    personnel: PersonnelService,
    recognition: RecognitionService,
    detection: Optional[DetectionService] = None
):
    """初始化服务实例"""
    global personnel_service, recognition_service, detection_service
    personnel_service = personnel
    recognition_service = recognition
    detection_service = detection


@router.get("/personnel", summary="获取人员列表")
async def get_personnel_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="姓名搜索"),
    status: Optional[str] = Query("active", description="状态筛选")
):
    """
    获取人员列表
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **name**: 姓名搜索关键词
    - **status**: 状态筛选（active/inactive）
    """
    if not personnel_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if name:
            where_clauses.append("name LIKE ?")
            params.append(f"%{name}%")
        
        # 不再需要 status 筛选，因为使用硬删除，所有记录都是 active 状态
        # 保留 status 参数以兼容旧版本，但实际不筛选
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) FROM personnel_info WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT id, face_id, name, id_number, phone, address, gender, category, status, photo_path, 
                   created_at, updated_at
            FROM personnel_info
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query_sql, params + [page_size, offset])
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "face_id": row["face_id"],
                "name": row["name"],
                "id_number": row["id_number"],
                "phone": row["phone"],
                "address": row["address"],
                "gender": row["gender"],
                "category": row["category"],
                "status": row["status"],
                "photo_path": row["photo_path"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        
        conn.close()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        
    except Exception as e:
        logger.error(f"获取人员列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取人员列表失败: {str(e)}")


@router.get("/personnel/{personnel_id}", summary="获取人员详情")
async def get_personnel(personnel_id: int):
    """获取人员详情"""
    if not personnel_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, face_id, name, id_number, phone, address, gender, category, status, photo_path, created_at, updated_at FROM personnel_info WHERE id = ?",
            (personnel_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="人员不存在")
        
        return {
            "id": row["id"],
            "face_id": row["face_id"],
            "name": row["name"],
            "id_number": row["id_number"],
            "phone": row["phone"],
            "address": row["address"],
            "gender": row["gender"],
            "category": row["category"],
            "status": row["status"],
            "photo_path": row["photo_path"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取人员详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取人员详情失败: {str(e)}")


@router.post("/personnel", summary="创建人员")
async def create_personnel(
    name: str = Form(..., description="姓名"),
    id_number: Optional[str] = Form(None, description="身份证号"),
    phone: Optional[str] = Form(None, description="电话"),
    address: Optional[str] = Form(None, description="住址"),
    gender: Optional[str] = Form(None, description="性别"),
    category: Optional[str] = Form(None, description="人员类别"),
    photo: UploadFile = File(..., description="照片")
):
    """创建人员"""
    if not personnel_service or not recognition_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        # 读取并验证图片
        contents = await photo.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大{settings.MAX_UPLOAD_SIZE}字节）"
            )
        
        image = decode_image_from_bytes(contents)
        if image is None:
            raise HTTPException(status_code=400, detail="无法解码图像文件")
        
        if not validate_image(image):
            raise HTTPException(status_code=400, detail="图像格式无效")
        
        # 检测人脸
        if not detection_service:
            raise HTTPException(status_code=500, detail="检测服务未初始化")
        faces = detection_service.detect_faces(image)
        
        if not faces:
            raise HTTPException(status_code=400, detail="图片中未检测到人脸")
        
        # 获取最大的人脸
        largest_face = detection_service.get_largest_face(faces)
        if not largest_face:
            raise HTTPException(status_code=400, detail="无法提取人脸")
        
        # 提取人脸特征并保存（使用裁剪后的人脸用于特征提取）
        face_img = largest_face['face_img']
        face_id = recognition_service.add_face(face_img)
        
        if not face_id:
            raise HTTPException(status_code=500, detail="保存人脸特征失败")
        
        # 保存原图文件（不是裁剪后的人脸）
        faces_dir = settings.FACES_DIR
        photo_path = f"{face_id}.jpg"
        photo_file_path = faces_dir / photo_path
        
        # 保存原图，而不是裁剪后的人脸
        pil_image = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        pil_image.save(photo_file_path, "JPEG")
        
        # 重新加载该人脸到数据库（因为文件被原图覆盖了，需要从原图中重新提取特征）
        # 注意：add_face 已经将特征添加到内存了，但为了确保一致性，我们从保存的原图中重新加载
        recognition_service.reload_face(face_id, photo_file_path)
        
        # 保存到数据库
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor()
        
        # 检查身份证号是否已存在（如果提供了身份证号）
        if id_number:
            cursor.execute(
                "SELECT id FROM personnel_info WHERE id_number = ?",
                (id_number,)
            )
            existing = cursor.fetchone()
            if existing:
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"身份证号 {id_number} 已被使用，请检查是否已存在该人员"
                )
        
        try:
            cursor.execute(
                """INSERT INTO personnel_info (face_id, name, id_number, phone, address, gender, category, photo_path, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
                (face_id, name, id_number or None, phone or None, address or None, gender or None, category or None, photo_path)
            )
            conn.commit()
            personnel_id = cursor.lastrowid
        except Exception as db_error:
            conn.rollback()
            conn.close()
            # 如果是唯一约束错误，提供更友好的错误信息
            if "UNIQUE constraint" in str(db_error):
                if "id_number" in str(db_error):
                    raise HTTPException(
                        status_code=400,
                        detail=f"身份证号 {id_number} 已被使用，请检查是否已存在该人员"
                    )
                elif "face_id" in str(db_error):
                    raise HTTPException(
                        status_code=500,
                        detail="人脸ID冲突，请重试"
                    )
            raise
        finally:
            conn.close()
        
        # 返回创建的人员信息
        return {
            "id": personnel_id,
            "face_id": face_id,
            "name": name,
            "id_number": id_number,
            "phone": phone,
            "address": address,
            "gender": gender,
            "category": category,
            "status": "active",
            "photo_path": photo_path,
            "created_at": "",
            "updated_at": "",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建人员失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建人员失败: {str(e)}")


@router.put("/personnel/{personnel_id}", summary="更新人员")
async def update_personnel(
    personnel_id: int,
    name: Optional[str] = Form(None, description="姓名"),
    id_number: Optional[str] = Form(None, description="身份证号"),
    phone: Optional[str] = Form(None, description="电话"),
    address: Optional[str] = Form(None, description="住址"),
    gender: Optional[str] = Form(None, description="性别"),
    category: Optional[str] = Form(None, description="人员类别"),
    photo: Optional[UploadFile] = File(None, description="照片")
):
    """更新人员信息"""
    if not personnel_service or not recognition_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        # 检查人员是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT face_id, photo_path FROM personnel_info WHERE id = ?", (personnel_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="人员不存在")
        
        old_face_id = row["face_id"]
        old_photo_path = row["photo_path"]
        
        update_fields = []
        update_values = []
        
        if name is not None:
            update_fields.append("name = ?")
            update_values.append(name)
        
        if id_number is not None:
            # 检查身份证号是否与其他人员冲突（排除当前人员）
            if id_number:  # 如果提供了非空身份证号
                cursor.execute(
                    "SELECT id FROM personnel_info WHERE id_number = ? AND id != ?",
                    (id_number, personnel_id)
                )
                existing = cursor.fetchone()
                if existing:
                    conn.close()
                    raise HTTPException(
                        status_code=400,
                        detail=f"身份证号 {id_number} 已被其他人员使用"
                    )
            update_fields.append("id_number = ?")
            update_values.append(id_number)
        
        if phone is not None:
            update_fields.append("phone = ?")
            update_values.append(phone)
        
        if address is not None:
            update_fields.append("address = ?")
            update_values.append(address)
        
        if gender is not None:
            update_fields.append("gender = ?")
            update_values.append(gender)
        
        if category is not None:
            update_fields.append("category = ?")
            update_values.append(category)
        
        # 如果上传了新照片，需要重新提取特征
        if photo:
            contents = await photo.read()
            if len(contents) > settings.MAX_UPLOAD_SIZE:
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制（最大{settings.MAX_UPLOAD_SIZE}字节）"
                )
            
            image = decode_image_from_bytes(contents)
            if image is None:
                conn.close()
                raise HTTPException(status_code=400, detail="无法解码图像文件")
            
            if not validate_image(image):
                conn.close()
                raise HTTPException(status_code=400, detail="图像格式无效")
            
            # 检测人脸
            if not detection_service:
                conn.close()
                raise HTTPException(status_code=500, detail="检测服务未初始化")
            faces = detection_service.detect_faces(image)
            
            if not faces:
                conn.close()
                raise HTTPException(status_code=400, detail="图片中未检测到人脸")
            
            largest_face = detection_service.get_largest_face(faces)
            if not largest_face:
                conn.close()
                raise HTTPException(status_code=400, detail="无法提取人脸")
            
            # 删除旧的人脸特征和图片
            recognition_service.remove_face(old_face_id)
            if old_photo_path:
                old_photo_file = settings.FACES_DIR / old_photo_path
                if old_photo_file.exists():
                    old_photo_file.unlink()
            
            # 提取新的人脸特征（使用裁剪后的人脸用于特征提取）
            face_img = largest_face['face_img']
            new_face_id = recognition_service.add_face(face_img)
            
            if not new_face_id:
                conn.close()
                raise HTTPException(status_code=500, detail="保存人脸特征失败")
            
            # 保存原图（不是裁剪后的人脸）
            photo_path = f"{new_face_id}.jpg"
            photo_file_path = settings.FACES_DIR / photo_path
            
            pil_image = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image.save(photo_file_path, "JPEG")
            
            # 重新加载该人脸到数据库（因为文件被原图覆盖了，需要从原图中重新提取特征）
            recognition_service.reload_face(new_face_id, photo_file_path)
            
            update_fields.append("face_id = ?")
            update_values.append(new_face_id)
            update_fields.append("photo_path = ?")
            update_values.append(photo_path)
        
        if not update_fields:
            conn.close()
            raise HTTPException(status_code=400, detail="没有需要更新的字段")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(personnel_id)
        
        try:
            update_sql = f"UPDATE personnel_info SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(update_sql, update_values)
            conn.commit()
        except Exception as db_error:
            conn.rollback()
            conn.close()
            # 如果是唯一约束错误，提供更友好的错误信息
            if "UNIQUE constraint" in str(db_error):
                if "id_number" in str(db_error):
                    raise HTTPException(
                        status_code=400,
                        detail=f"身份证号 {id_number} 已被其他人员使用"
                    )
            raise
        finally:
            conn.close()
        
        # 返回更新后的人员信息
        return await get_personnel(personnel_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新人员失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新人员失败: {str(e)}")


@router.delete("/personnel/{personnel_id}", summary="删除人员")
async def delete_personnel(personnel_id: int):
    """删除人员（硬删除，真正删除数据库记录和相关文件）"""
    if not personnel_service or not recognition_service:
        raise HTTPException(status_code=500, detail="服务未初始化")
    
    try:
        conn = personnel_service._get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor()
        
        # 检查人员是否存在，并获取相关信息
        cursor.execute(
            "SELECT face_id, photo_path FROM personnel_info WHERE id = ?",
            (personnel_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="人员不存在")
        
        face_id = row["face_id"]
        photo_path = row["photo_path"]
        
        # 从识别服务中移除人脸特征
        try:
            recognition_service.remove_face(face_id)
        except Exception as e:
            logger.warning(f"移除人脸特征失败: {e}，继续删除记录")
        
        # 删除图片文件
        if photo_path:
            photo_file = settings.FACES_DIR / photo_path
            if photo_file.exists():
                try:
                    photo_file.unlink()
                    logger.info(f"已删除图片文件: {photo_path}")
                except Exception as e:
                    logger.warning(f"删除图片文件失败: {e}，继续删除记录")
        
        # 硬删除：真正删除数据库记录
        cursor.execute("DELETE FROM personnel_info WHERE id = ?", (personnel_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"成功删除人员 ID: {personnel_id}, face_id: {face_id}")
        return {"message": "删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除人员失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除人员失败: {str(e)}")

