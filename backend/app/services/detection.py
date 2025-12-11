import torch
import cv2
import numpy as np
from typing import List, Dict, Optional, Any
from PIL import Image
from threading import Lock
from facenet_pytorch import MTCNN
from app.core.config import settings


class DetectionService:
    def __init__(self):
        self.device = torch.device(settings.DEVICE)
        self.threshold = settings.FACE_DETECTION_THRESHOLD
        self.mtcnn = None
        self._initialized = False
        self._lock = Lock()
    
    def initialize(self):
        if self._initialized:
            return
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            self.mtcnn = MTCNN(
                image_size=160,
                margin=20,
                device=self.device,
                post_process=True
            ).eval()
            logger.info("检测模型已初始化")
            self._initialized = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"检测服务初始化失败: {e}", exc_info=True)
            raise
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """检测图像中的人脸位置"""
        if not self._initialized:
            return []
        
        try:
            frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)
            
            with self._lock:
                boxes, probs = self.mtcnn.detect(pil_frame)
            
            faces = []
            if boxes is not None and probs is not None:
                for box, prob in zip(boxes, probs):
                    if prob > self.threshold:
                        x, y, w, h = box.astype(int)
                        x = max(0, x)
                        y = max(0, y)
                        w = min(w, image.shape[1] - x)
                        h = min(h, image.shape[0] - y)
                        face_img = image[y:y+h, x:x+w].copy()
                        
                        if face_img.size > 0 and face_img.shape[0] > 20 and face_img.shape[1] > 20:
                            faces.append({
                                "x": int(x),
                                "y": int(y),
                                "w": int(w),
                                "h": int(h),
                                "confidence": float(prob),
                                "face_img": face_img
                            })
            
            return faces
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"人脸检测失败: {e}", exc_info=True)
            return []
    
    def get_largest_face(self, faces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """获取最大的人脸"""
        if not faces:
            return None
        return max(faces, key=lambda f: f["w"] * f["h"])

