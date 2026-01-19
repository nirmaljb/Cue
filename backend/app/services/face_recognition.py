"""Face recognition service using FaceNet for embedding extraction."""

import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import numpy as np
from typing import Optional

from app.utils.image import decode_base64_image


class FaceRecognitionService:
    """Service for face detection and embedding extraction using FaceNet."""
    
    def __init__(self):
        # Device selection priority: MPS (Apple Silicon) > CUDA > CPU
        # Note: We use hybrid approach due to MPS limitations with MTCNN
        if torch.backends.mps.is_available():
            self.embedding_device = torch.device("mps")  # For InceptionResnetV1
            self.detection_device = torch.device("cpu")  # For MTCNN (has MPS bug)
            print("🍎 Apple Silicon GPU (MPS) detected - using hybrid CPU+MPS")
            print("   - Face detection (MTCNN): CPU")
            print("   - Embedding extraction (ResNet): MPS")
        elif torch.cuda.is_available():
            self.embedding_device = torch.device("cuda")
            self.detection_device = torch.device("cuda")
            print("🎮 CUDA GPU detected")
        else:
            self.embedding_device = torch.device("cpu")
            self.detection_device = torch.device("cpu")
            print("💻 Using CPU (no GPU acceleration)")
        
        self.mtcnn: Optional[MTCNN] = None
        self.resnet: Optional[InceptionResnetV1] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the face detection and embedding models."""
        if self._initialized:
            return
        
        print("🔄 Loading FaceNet models...")
        
        # MTCNN for face detection and alignment (on CPU to avoid MPS bug)
        self.mtcnn = MTCNN(
            image_size=160,
            margin=0,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            device=self.detection_device,
            keep_all=False,  # Only keep the largest/most confident face
        )
        
        # InceptionResnetV1 for face embeddings (512-dim) - on MPS/CUDA if available
        self.resnet = InceptionResnetV1(
            pretrained="vggface2",
            device=self.embedding_device,
        ).eval()
        
        self._initialized = True
        print(f"✅ FaceNet models loaded (detection: {self.detection_device}, embedding: {self.embedding_device})")
    
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
        
        # Detect face and get aligned face tensor
        face_tensor = self.mtcnn(image)
        
        if face_tensor is None:
            return None
        
        # Ensure batch dimension
        if face_tensor.dim() == 3:
            face_tensor = face_tensor.unsqueeze(0)
        
        # Move to embedding device (MPS/CUDA/CPU)
        face_tensor = face_tensor.to(self.embedding_device)
        
        # Extract embedding
        with torch.no_grad():
            embedding = self.resnet(face_tensor)
        
        # Convert to list of floats
        embedding_list = embedding.squeeze().cpu().numpy().tolist()
        
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
        
        # Detect face and get aligned face tensor
        face_tensor = self.mtcnn(image)
        
        if face_tensor is None:
            return None
        
        # Ensure batch dimension
        if face_tensor.dim() == 3:
            face_tensor = face_tensor.unsqueeze(0)
        
        # Move to embedding device (MPS/CUDA/CPU)
        face_tensor = face_tensor.to(self.embedding_device)
        
        # Extract embedding
        with torch.no_grad():
            embedding = self.resnet(face_tensor)
        
        # Convert to list of floats
        embedding_list = embedding.squeeze().cpu().numpy().tolist()
        
        return embedding_list


# Singleton instance
face_recognition = FaceRecognitionService()
