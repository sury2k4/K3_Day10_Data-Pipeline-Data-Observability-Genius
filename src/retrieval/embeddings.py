import hashlib
import math
from langchain_core.embeddings import Embeddings


def _hash_embed(text: str, dim: int = 384) -> list[float]:
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        words = ["empty"]
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 16) & 1) else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embed(t, 384) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return _hash_embed(text, 384)


