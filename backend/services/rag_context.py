"""检索增强：从术语库与平行句中取与当前文本相关的片段（轻量实现）。"""
from models import GlossaryEntry, ParallelPair


def glossary_hints(user_id: int, text: str, src_lang: str, tgt_lang: str, limit: int = 24) -> str:
    """命中源文子串的术语，拼成提示行。"""
    rows = (
        GlossaryEntry.query.filter_by(user_id=user_id, src_lang=src_lang, tgt_lang=tgt_lang)
        .order_by(GlossaryEntry.id.desc())
        .limit(500)
        .all()
    )
    lines = []
    for r in rows:
        if r.src_text and r.src_text in text:
            lines.append(f"- {r.src_text} → {r.tgt_text}")
        if len(lines) >= limit:
            break
    return "\n".join(lines)


def parallel_examples(
    user_id: int, text: str, src_lang: str, tgt_lang: str, limit: int = 3
) -> str:
    """取少量平行句作为风格参考（简单按子串命中）。"""
    rows = (
        ParallelPair.query.filter_by(user_id=user_id, src_lang=src_lang, tgt_lang=tgt_lang)
        .order_by(ParallelPair.id.desc())
        .limit(200)
        .all()
    )
    parts = []
    for r in rows:
        if r.src_text and len(r.src_text) > 6 and r.src_text[:20] in text:
            parts.append(f"参考句对：{r.src_text[:120]} || {r.tgt_text[:120]}")
        if len(parts) >= limit:
            break
    if not parts and rows:
        for r in rows[:limit]:
            parts.append(f"参考句对：{r.src_text[:80]} || {r.tgt_text[:80]}")
    return "\n".join(parts)
