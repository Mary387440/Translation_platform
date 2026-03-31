"""评测指标（轻量实现）：BLEU、ROUGE-L、METEOR。"""
from collections import Counter


def _tokenize(s: str):
    s = (s or "").strip()
    if not s:
        return []
    if " " in s:
        return [x for x in s.split() if x]
    return [c for c in s if c.strip()]


def bleu_unigram(candidate: str, reference: str) -> float:
    c = _tokenize(candidate)
    r = _tokenize(reference)
    if not c or not r:
        return 0.0
    c_cnt = Counter(c)
    r_cnt = Counter(r)
    overlap = sum(min(v, r_cnt.get(k, 0)) for k, v in c_cnt.items())
    precision = overlap / max(len(c), 1)
    bp = 1.0 if len(c) > len(r) else pow(2.718281828, 1 - (len(r) / max(len(c), 1)))
    return max(0.0, min(1.0, bp * precision))


def _lcs_len(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


def rouge_l_f1(candidate: str, reference: str) -> float:
    c = _tokenize(candidate)
    r = _tokenize(reference)
    if not c or not r:
        return 0.0
    lcs = _lcs_len(c, r)
    p = lcs / len(c)
    rec = lcs / len(r)
    if p + rec == 0:
        return 0.0
    return 2 * p * rec / (p + rec)


def meteor_like(candidate: str, reference: str) -> float:
    c = _tokenize(candidate)
    r = _tokenize(reference)
    if not c or not r:
        return 0.0
    c_cnt = Counter(c)
    r_cnt = Counter(r)
    overlap = sum(min(v, r_cnt.get(k, 0)) for k, v in c_cnt.items())
    p = overlap / len(c)
    rec = overlap / len(r)
    if p == 0 and rec == 0:
        return 0.0
    return (10 * p * rec) / (rec + 9 * p + 1e-12)


def evaluate_batch(preds, refs, metrics):
    out = {m: 0.0 for m in metrics}
    n = min(len(preds), len(refs))
    if n == 0:
        return out
    for p, r in zip(preds[:n], refs[:n]):
        if "BLEU" in out:
            out["BLEU"] += bleu_unigram(p, r)
        if "ROUGE" in out:
            out["ROUGE"] += rouge_l_f1(p, r)
        if "METEOR" in out:
            out["METEOR"] += meteor_like(p, r)
    for k in out:
        out[k] = round((out[k] / n) * 100, 2)
    return out

