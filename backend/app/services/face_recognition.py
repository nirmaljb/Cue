"""Face recognition service using InsightFace for embedding extraction."""

import numpy as np
from typing import Optional
from PIL import Image
import cv2
import warnings

# Suppress InsightFace's scikit-image deprecation warning
warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')

from app.utils.image import decode_base64_image


class FaceRecognitionService:
    """Service for face detection and embedding extraction using InsightFace."""
    
    def __init__(self):
        self.model = None
        self._initialized = False
        self.device = None
    
    def initialize(self):
        """Initialize the InsightFace model."""
        if self._initialized:
            return
        
        print("🔄 Loading InsightFace buffalo_s model...")
        
        try:
            import insightface
            from insightface.app import FaceAnalysis
            
            # Initialize with buffalo_s model (balanced speed/accuracy)
            # providers: try CUDA → CoreML → CPU
            self.model = FaceAnalysis(
                name='buffalo_s',
                providers=['CUDAExecutionProvider', 'CoreMLExecutionProvider', 'CPUExecutionProvider']
            )
            
            # Prepare model with specific settings
            self.model.prepare(
                ctx_id=0,           # GPU device ID (0 = first GPU, -1 = CPU)
                det_size=(640, 640) # Detection size (larger = more accurate but slower)
            )
            
            # Detect which provider is actually being used
            if hasattr(self.model, 'det_model') and hasattr(self.model.det_model, 'session'):
                provider = self.model.det_model.session.get_providers()[0]
                if 'CUDA' in provider:
                    self.device = "CUDA GPU"
                elif 'CoreML' in provider:
                    self.device = "Apple Silicon (CoreML)"
                else:
                    self.device = "CPU"
            else:
                self.device = "CPU"
            
            self._initialized = True
            print(f"✅ InsightFace buffalo_s loaded on {self.device}")
            
        except Exception as e:
            print(f"❌ Failed to load InsightFace: {e}")
            raise
    
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
        if image_np.shape[2] == 4:  # RGBA → RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Detect faces and extract embeddings
        faces = self.model.get(image_bgr)
        
        if not faces or len(faces) == 0:
            return None
        
        # Get the largest/most confident face
        face = faces[0]
        
        # Extract embedding (already normalized)
        embedding = face.embedding
        
        # Convert to Python list
        embedding_list = embedding.tolist()
        
        return embedding_list


# Singleton instance
face_recognition = FaceRecognitionService()
