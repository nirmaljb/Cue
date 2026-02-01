"""Face recognition service using InsightFace for embedding extraction.

Optimized for CUDA GPU with:
- buffalo_l model for better accuracy (fast on GPU)
- Configurable detection size (speed vs accuracy tradeoff)  
- Batch processing for multi-frame recognition
- GPU memory pre-allocation
"""

import numpy as np
from typing import Optional
from PIL import Image
import cv2
import warnings
import os

# Suppress InsightFace's scikit-image deprecation warning
warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

from app.utils.image import decode_base64_image


class FaceRecognitionService:
    """Service for face detection and embedding extraction using InsightFace.
    
    GPU Optimization Notes:
    - Uses buffalo_l on GPU (high accuracy, fast on CUDA)
    - Uses buffalo_s on CPU (balanced for slower devices)
    - Detection size: 320x320 for speed, 640x640 for accuracy
    """
    
    def __init__(self):
        self.model = None
        self._initialized = False
        self.device = None
        self.is_gpu = False
        
        # Configurable via environment
        self.det_size = int(os.getenv("FACE_DET_SIZE", "480"))  # Default 480 (balanced)
        self.model_name = os.getenv("FACE_MODEL", "auto")  # auto, buffalo_s, buffalo_l
    
    def initialize(self):
        """Initialize the InsightFace model with GPU optimization."""
        if self._initialized:
            return
        
        try:
            import insightface
            from insightface.app import FaceAnalysis
            
            # Check available providers
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            self.is_gpu = 'CUDAExecutionProvider' in available_providers
            
            # Select model based on device
            if self.model_name == "auto":
                # Use buffalo_l on GPU (fast + accurate), buffalo_s on CPU
                model_name = 'buffalo_l' if self.is_gpu else 'buffalo_s'
            else:
                model_name = self.model_name
            
            print(f"🔄 Loading InsightFace {model_name} model...")
            
            # Set providers in priority order
            providers = ['CUDAExecutionProvider', 'CoreMLExecutionProvider', 'CPUExecutionProvider']
            
            # Initialize model
            self.model = FaceAnalysis(
                name=model_name,
                providers=providers,
                allowed_modules=['detection', 'recognition']  # Skip age/gender for speed
            )
            
            # Prepare with detection size
            # GPU can handle larger sizes efficiently
            det_size = (self.det_size, self.det_size)
            
            self.model.prepare(
                ctx_id=0 if self.is_gpu else -1,  # GPU ID or CPU
                det_size=det_size,
                det_thresh=0.5  # Detection confidence threshold
            )
            
            # Detect actual provider in use
            if hasattr(self.model, 'det_model') and hasattr(self.model.det_model, 'session'):
                provider = self.model.det_model.session.get_providers()[0]
                if 'CUDA' in provider:
                    self.device = "CUDA GPU"
                    self.is_gpu = True
                elif 'CoreML' in provider:
                    self.device = "Apple Silicon (CoreML)"
                else:
                    self.device = "CPU"
            else:
                self.device = "CPU"
            
            # Warm up the model (pre-allocate GPU memory)
            if self.is_gpu:
                self._warmup()
            
            self._initialized = True
            print(f"✅ InsightFace {model_name} loaded on {self.device} (det_size={self.det_size})")
            
        except Exception as e:
            print(f"❌ Failed to load InsightFace: {e}")
            raise
    
    def _warmup(self):
        """Warm up GPU by running a dummy inference."""
        dummy_image = np.zeros((self.det_size, self.det_size, 3), dtype=np.uint8)
        try:
            self.model.get(dummy_image)
            print("🔥 GPU warmed up")
        except:
            pass  # Ignore warmup errors
    
    def extract_embedding(self, image_base64: str) -> Optional[list[float]]:
        """Extract face embedding from a base64 image.
        
        Args:
            image_base64: Base64 encoded image string
        
        Returns:
            512-dimensional face embedding as list of floats, or None if no face detected
        """
        if not self._initialized:
            self.initialize()
        
        # Decode image
        image = decode_base64_image(image_base64)
        
        # Convert PIL to numpy array (RGB → BGR for OpenCV/InsightFace)
        image_np = np.array(image)
        if image_np.shape[2] == 4:  # RGBA → RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Detect faces and extract embeddings
        faces = self.model.get(image_bgr)
        
        if not faces or len(faces) == 0:
            return None
        
        # Get the largest/most confident face
        face = faces[0]
        
        # Extract embedding (already normalized by InsightFace)
        embedding = face.embedding
        
        # Convert to Python list for JSON serialization
        embedding_list = embedding.tolist()
        
        return embedding_list
    
    def extract_embedding_from_pil(self, image: Image.Image) -> Optional[list[float]]:
        """Extract face embedding from a PIL Image.
        
        Args:
            image: PIL Image object
        
        Returns:
            512-dimensional face embedding as list of floats, or None if no face detected
        """
        if not self._initialized:
            self.initialize()
        
        # Convert PIL to numpy array (RGB → BGR)
        image_np = np.array(image)
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA → RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        else:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Detect faces and extract embeddings
        faces = self.model.get(image_np)
        
        if not faces or len(faces) == 0:
            return None
        
        # Get the largest/most confident face
        face = faces[0]
        
        # Extract embedding (already normalized)
        return face.embedding.tolist()
    
    def extract_embeddings_batch(self, images_base64: list[str]) -> list[Optional[list[float]]]:
        """Extract face embeddings from multiple base64 images efficiently.
        
        Optimized for GPU: processes images sequentially but minimizes overhead.
        
        Args:
            images_base64: List of base64 encoded image strings
        
        Returns:
            List of embeddings (512-dim) or None for each image where no face was detected
        """
        if not self._initialized:
            self.initialize()
        
        results = []
        
        for image_base64 in images_base64:
            try:
                # Decode image
                image = decode_base64_image(image_base64)
                
                # Fast conversion path
                image_np = np.array(image, dtype=np.uint8)
                
                # Handle different color formats
                if len(image_np.shape) == 2:  # Grayscale
                    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                elif image_np.shape[2] == 4:  # RGBA
                    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
                else:  # RGB
                    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                
                # Detect and extract
                faces = self.model.get(image_bgr)
                
                if faces and len(faces) > 0:
                    results.append(faces[0].embedding.tolist())
                else:
                    results.append(None)
                    
            except Exception as e:
                print(f"⚠️ Batch extraction error: {e}")
                results.append(None)
        
        return results
    
    def _convert_to_bgr(self, image_np: np.ndarray) -> np.ndarray:
        """Fast conversion of numpy image to BGR format."""
        if len(image_np.shape) == 2:  # Grayscale
            return cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA
            return cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
        else:  # RGB
            return cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)


# Singleton instance
face_recognition = FaceRecognitionService()

