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
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.mtcnn: Optional[MTCNN] = None
        self.resnet: Optional[InceptionResnetV1] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the face detection and embedding models."""
        if self._initialized:
            return
        
        print("🔄 Loading FaceNet models...")
        
        # MTCNN for face detection and alignment
        self.mtcnn = MTCNN(
            image_size=160,
            margin=0,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            device=self.device,
            keep_all=False,  # Only keep the largest/most confident face
        )
        
        # InceptionResnetV1 for face embeddings (512-dim)
        self.resnet = InceptionResnetV1(
            pretrained="vggface2",
            device=self.device,
        ).eval()
        
        self._initialized = True
        print(f"✅ FaceNet models loaded on {self.device}")
    
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
        
        # Move to device
        face_tensor = face_tensor.to(self.device)
        
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
        
        # Move to device
        face_tensor = face_tensor.to(self.device)
        
        # Extract embedding
        with torch.no_grad():
            embedding = self.resnet(face_tensor)
        
        # Convert to list of floats
        embedding_list = embedding.squeeze().cpu().numpy().tolist()
        
        return embedding_list


# Singleton instance
face_recognition = FaceRecognitionService()
