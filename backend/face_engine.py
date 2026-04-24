"""
ThirdEye — Face Intelligence Engine
RetinaFace detection + ArcFace 512D embedding extraction.
Falls back to simulation mode when InsightFace models aren't available.
"""

import io
import logging
import hashlib
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger("thirdeye.face_engine")

# ── Confidence Thresholds ──
THRESHOLDS = {
    "DEFINITE": 0.90,
    "HIGH": 0.80,
    "PROBABLE": 0.75,
    "POSSIBLE": 0.65,
    "WEAK": 0.60,
}


def get_confidence_label(score: float) -> str:
    """Convert a similarity score to a human-readable confidence label."""
    if score >= 0.90:
        return "DEFINITE MATCH"
    elif score >= 0.80:
        return "HIGH CONFIDENCE"
    elif score >= 0.75:
        return "PROBABLE MATCH"
    elif score >= 0.65:
        return "POSSIBLE MATCH"
    elif score >= 0.60:
        return "WEAK SIGNAL"
    else:
        return "DISCARD"


def should_alert(score: float) -> bool:
    """Check if a score should trigger an alert (≥ 0.75)."""
    return score >= 0.75


def should_log(score: float) -> bool:
    """Check if a score should be logged (≥ 0.65)."""
    return score >= 0.65


class FaceEngine:
    """
    Face detection and embedding engine.
    Uses InsightFace (RetinaFace + ArcFace) when available,
    falls back to deterministic simulation for development.
    """

    def __init__(self):
        self._model = None
        self._simulation_mode = False
        self._initialize()

    def _initialize(self):
        """Try to load InsightFace models, fall back to simulation."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            self._model = FaceAnalysis(
                name="buffalo_l",
                providers=["CPUExecutionProvider"]
            )
            self._model.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace loaded successfully — real face matching enabled")

        except Exception as e:
            logger.warning(
                f"InsightFace not available ({e}). "
                "Running in SIMULATION mode — face matching will use deterministic hashing."
            )
            self._simulation_mode = True

    def extract_embedding(self, image_input) -> Optional[np.ndarray]:
        """
        Extract a 512D face embedding from an image.

        Args:
            image_input: file path (str), PIL Image, or bytes

        Returns:
            512D numpy array, or None if no face detected
        """
        if self._simulation_mode:
            return self._simulate_embedding(image_input)

        try:
            img_array = self._load_image_array(image_input)
            faces = self._model.get(img_array)

            if not faces:
                logger.debug("No faces detected in image")
                return None

            # Use the largest face (most prominent)
            largest_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            embedding = largest_face.embedding

            # Normalize to unit vector for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return embedding.astype(np.float32)

        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None

    def extract_all_embeddings(self, image_input) -> list[np.ndarray]:
        """Extract embeddings for ALL faces detected in an image."""
        if self._simulation_mode:
            emb = self._simulate_embedding(image_input)
            return [emb] if emb is not None else []

        try:
            img_array = self._load_image_array(image_input)
            faces = self._model.get(img_array)

            embeddings = []
            for face in faces:
                emb = face.embedding
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                embeddings.append(emb.astype(np.float32))

            return embeddings

        except Exception as e:
            logger.error(f"Multi-face extraction failed: {e}")
            return []

    def compare_faces(
        self,
        reference_embeddings: list[np.ndarray],
        candidate_embedding: np.ndarray,
    ) -> tuple[float, str]:
        """
        Compare a candidate face against all reference embeddings.
        Returns the BEST (highest) similarity score and its label.

        Args:
            reference_embeddings: list of 512D reference vectors
            candidate_embedding: single 512D candidate vector

        Returns:
            (best_score, confidence_label) tuple
        """
        if not reference_embeddings or candidate_embedding is None:
            return 0.0, "DISCARD"

        best_score = 0.0

        for ref_emb in reference_embeddings:
            score = self._cosine_similarity(ref_emb, candidate_embedding)
            best_score = max(best_score, score)

        label = get_confidence_label(best_score)
        return round(best_score, 4), label

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    @staticmethod
    def _load_image_array(image_input) -> np.ndarray:
        """Convert various image inputs to numpy array (BGR for InsightFace)."""
        import cv2

        if isinstance(image_input, str):
            img = cv2.imread(image_input)
            if img is None:
                raise ValueError(f"Could not read image from path: {image_input}")
            return img

        if isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image bytes")
            return img

        if isinstance(image_input, Image.Image):
            img_array = np.array(image_input.convert("RGB"))
            return img_array[:, :, ::-1]  # RGB to BGR

        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    def _simulate_embedding(self, image_input) -> np.ndarray:
        """
        Generate a deterministic 512D embedding from image data.
        Same image always produces the same embedding (useful for testing).
        """
        if isinstance(image_input, str):
            try:
                with open(image_input, "rb") as f:
                    data = f.read()
            except Exception:
                data = image_input.encode()
        elif isinstance(image_input, bytes):
            data = image_input
        elif isinstance(image_input, Image.Image):
            buf = io.BytesIO()
            image_input.save(buf, format="PNG")
            data = buf.getvalue()
        else:
            data = str(image_input).encode()

        # Create deterministic embedding from hash
        hash_bytes = hashlib.sha512(data).digest()
        # Expand to 512 floats using the hash as a seed
        seed = int.from_bytes(hash_bytes[:4], byteorder="big")
        rng = np.random.RandomState(seed)
        embedding = rng.randn(512).astype(np.float32)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embedding_to_bytes(self, embedding: np.ndarray) -> bytes:
        """Serialize an embedding to bytes for database storage."""
        return embedding.tobytes()

    def bytes_to_embedding(self, data: bytes) -> np.ndarray:
        """Deserialize bytes back to a 512D embedding."""
        return np.frombuffer(data, dtype=np.float32)


# Singleton instance
face_engine = FaceEngine()
