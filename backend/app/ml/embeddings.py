from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from collections import Counter
import numpy as np

_embedder: SentenceTransformer = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def compute_embeddings(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    return embedder.encode(texts, batch_size=32, show_progress_bar=False).tolist()


def cluster_topics(texts: list[str], embeddings: list[list[float]]) -> tuple[list[int], list[str]]:
    if len(texts) < 4:
        return [0] * len(texts), ["general"] * len(texts)
    try:
        n_clusters = min(max(2, len(texts) // 4), 8)
        arr = np.array(embeddings)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = km.fit_predict(arr).tolist()

        cluster_map: dict[int, list[int]] = {}
        for i, lbl in enumerate(labels):
            cluster_map.setdefault(lbl, []).append(i)

        stopwords = {
            "the","a","an","is","in","it","of","to","and","for","on","with",
            "this","that","are","was","be","as","at","by","from","or","but","not",
        }
        topic_labels = []
        for lbl in labels:
            words = []
            for idx in cluster_map[lbl]:
                words += [
                    w.lower().strip(".,!?'\"")
                    for w in texts[idx].split()
                    if len(w) > 3 and w.lower() not in stopwords
                ]
            top = [w for w, _ in Counter(words).most_common(3)]
            topic_labels.append(" / ".join(top) if top else "general")

        return labels, topic_labels
    except Exception:
        return [0] * len(texts), ["general"] * len(texts)
