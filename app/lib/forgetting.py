from datetime import datetime, timedelta
import math

LAMBDA = 0.20  # 減衰係数をやや緩めに調整（チューニング可能）
THETA  = 0.4

VIEWS_TARGET = 10  # 正規化で何回視聴したら engagement=1.0 とみなすか

def decay(s: float, days: float, lam=LAMBDA):
    return s * math.exp(-lam * max(days, 0))

def review_boost(s: float, alpha=0.6):
    return min(1.0, s + alpha*(1.0 - s))

def normalize_views(view_count: int, target: int = VIEWS_TARGET) -> float:
    try:
        v = int(view_count or 0)
    except Exception:
        v = 0
    # 対数正規化して 0..1 にマップ
    return min(1.0, math.log(1 + v) / math.log(1 + target))


def update_fish_state(fish, now: datetime, reviewed_today: bool, view_count: int = 0):
    """Update fish state using mixed model: time decay + engagement from views.

    Composite score = w_s * decayed_s + w_e * engagement + w_r * recency
    Returns updated fish object with fields: s, health, status, weight_g, last_update, next_due
    """
    # 経過日数
    days = (now - fish.last_update).total_seconds() / 86400 if fish.last_update else 9999
    s_decayed = decay(fish.s, days)

    # レビュー日のボーナスは記憶 s に対してだけ適用
    if reviewed_today:
        s_decayed = review_boost(s_decayed)

    # エンゲージメント（視聴回数ベース）
    engagement = normalize_views(view_count)

    # 合成スコア（重みはチューニング可能）
    w_s, w_e, w_r = 0.7, 0.25, 0.05
    recency = 1.0 if reviewed_today else 0.0
    composite = w_s * s_decayed + w_e * engagement + w_r * recency
    composite = max(0.0, min(1.0, composite))

    health = max(0, min(100, round(100 * composite)))
    status = 'dead' if health == 0 else ('weak' if health < 30 else 'alive')

    # 既存の体重ロジックは維持
    weight = fish.weight_g + (5 if reviewed_today else -2)
    weight = max(50, weight)

    # 次回 due は decayed s を使って既存ロジックを保つ
    s_for_due = max(s_decayed, 1e-6)
    next_days = max(1, round(-math.log(THETA / s_for_due) / LAMBDA))
    next_due = now + timedelta(days=next_days)

    # フィールドに書き戻す
    fish.s = s_decayed
    fish.health = health
    fish.status = status
    fish.weight_g = weight
    fish.last_update = now
    fish.next_due = next_due
    return fish
