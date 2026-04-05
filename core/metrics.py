import numpy as np


def compute_metrics(returns):
    ann_return = returns.mean() * 252
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = ann_return / ann_vol
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    max_dd = ((cumulative - rolling_max) / rolling_max).min()
    return dict(
        ann_return=ann_return,
        ann_vol=ann_vol,
        sharpe=sharpe,
        max_dd=max_dd,
        cumulative=cumulative,
    )


def hex_to_rgba(hex_color, alpha=0.08):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

