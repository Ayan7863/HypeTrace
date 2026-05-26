from transformers import pipeline
import re

_sentiment_pipe = None


def get_sentiment_pipeline():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
    return _sentiment_pipe


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^\w\s.,!?]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def analyze_sentiment(texts: list[str]) -> list[dict]:
    pipe = get_sentiment_pipeline()
    results = []
    for text in texts:
        try:
            cleaned = clean_text(text)[:512]
            out = pipe(cleaned)[0]
            label = out["label"].lower()
            confidence = out["score"]
            if confidence < 0.70:
                results.append({"sentiment": "neutral", "sentiment_score": 0.0, "confidence": confidence})
            else:
                score = confidence if label == "positive" else -confidence
                results.append({"sentiment": label, "sentiment_score": round(score, 4), "confidence": round(confidence, 4)})
        except Exception:
            results.append({"sentiment": "neutral", "sentiment_score": 0.0, "confidence": 0.0})
    return results


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    stopwords = {
        "the","a","an","is","in","it","of","to","and","for","on","with",
        "this","that","are","was","be","as","at","by","from","or","but",
        "not","have","has","i","you","we","they","my","your","just","been",
        "will","can","its","about","after","all","also","do","get","got",
        "how","if","into","more","new","no","now","one","our","out","over",
        "so","some","than","their","there","up","use","what","when","who",
    }
    words = [
        w.lower().strip(".,!?'\"")
        for w in text.split()
        if len(w) > 3 and w.lower().strip(".,!?'\"") not in stopwords
    ]
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:top_n]
