import hashlib
import math
from functools import lru_cache

from backend.app.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None
        self._load_error: str | None = None

    def _load_model(self):
        if self._model is not None or self._load_error is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.settings.embedding_model,
                local_files_only=not self.settings.embedding_allow_download,
            )
        except Exception as exc:
            self._load_error = str(exc)
        return self._model

    @property
    def available(self) -> bool:
        return self._load_model() is not None

    def embed(self, text: str) -> list[float]:
        clean_text = " ".join(text.split())
        model = self._load_model()
        if model is not None:
            vector = model.encode(clean_text, normalize_embeddings=True)
            return [float(value) for value in vector.tolist()]
        return self._fallback_embedding(clean_text)

    def _fallback_embedding(self, text: str, dimensions: int = 384) -> list[float]:
        vector = [0.0] * dimensions
        tokens = text.lower().split()
        for token in tokens or [text.lower()]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            sign = -1.0 if digest[4] % 2 else 1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
