import re
from typing import Tuple

def simple_summary(title:str, desc:str)->Tuple[str, str]:
    text = f"{title}\n{desc or ''}"
    words = re.findall(r"[A-Za-z0-9一-龠ぁ-んァ-ヶー]{2,}", text)
    freq = {}
    for w in words:
        w = w.lower()
        if len(w) < 2: continue
        freq[w] = freq.get(w, 0) + 1
    top = [w for w,_ in sorted(freq.items(), key=lambda x: x[1], reverse=True)][:5]
    summary = f"要点: {('・'.join(top)) if top else 'キーワード抽出不可'}"
    keywords = ",".join(top)
    return summary, keywords
