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
            
            # 输出设备信息
            device_str = str(self.device)
            original_device = self.device
            mtcnn_device = self.device
            
            # MTCNN 在 MUSA 设备上不支持某些操作（如 trunc），需要强制使用 CPU
            if self.device.type == 'musa':
                # MUSA GPU - MTCNN 检测使用 CPU，因为某些操作不支持
                try:
                    import torch_musa
                    if hasattr(torch, "musa") and torch.musa.is_available():
                        device_id = int(self.device.index) if self.device.index is not None else 0
                        if hasattr(torch.musa, "get_device_name"):
                            device_name = torch.musa.get_device_name(device_id)
                        else:
                            device_name = "MUSA GPU"
                        logger.info(f"MUSA GPU 设备名称: {device_name}")
                        if hasattr(torch.musa, "get_device_properties"):
                            props = torch.musa.get_device_properties(device_id)
                            if hasattr(props, "total_memory"):
                                logger.info(f"MUSA GPU 内存: {props.total_memory / 1024**3:.2f} GB")
                        # MTCNN 在 MUSA 上不支持，使用 CPU
                        mtcnn_device = torch.device('cpu')
                        logger.info("⚠️  MTCNN 检测在 MUSA 设备上不支持某些操作，将使用 CPU 进行检测")
                    else:
                        logger.warning("MUSA 设备不可用，将回退到 CPU")
                        self.device = torch.device('cpu')
                        mtcnn_device = torch.device('cpu')
                        device_str = 'cpu'
                except ImportError:
                    logger.warning("torch_musa 未安装，将回退到 CPU")
                    self.device = torch.device('cpu')
                    mtcnn_device = torch.device('cpu')
                    device_str = 'cpu'
            elif self.device.type == 'cuda':
                # CUDA GPU
                if torch.cuda.is_available():
                    logger.info(f"CUDA GPU 设备名称: {torch.cuda.get_device_name(self.device)}")
                    logger.info(f"CUDA GPU 内存: {torch.cuda.get_device_properties(self.device).total_memory / 1024**3:.2f} GB")
                else:
                    logger.warning("CUDA 设备不可用，将回退到 CPU")
                    self.device = torch.device('cpu')
                    mtcnn_device = torch.device('cpu')
                    device_str = 'cpu'
            elif self.device.type == 'cpu':
                logger.info("使用 CPU 设备")
            
            self.mtcnn = MTCNN(
                image_size=160,
                margin=20,
                device=mtcnn_device,  # 使用 mtcnn_device（MUSA 时使用 CPU）
                post_process=True
            ).eval()
            logger.info(f"检测模型已初始化 (MTCNN设备: {mtcnn_device}, 原始设备: {device_str})")
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

