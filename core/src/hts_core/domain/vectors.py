import numpy as np


def cosine_dense(u: np.ndarray, v: np.ndarray) -> float:
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        return 0.0
    return float(np.dot(u, v) / (nu * nv))


def alignment_similarity(u: np.ndarray, v: np.ndarray) -> float:
    """A9, seção 3."""
    return 1.0 + cosine_dense(u, v)
