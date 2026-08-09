"""
S안 — **찢김.** 판이 한 번 찢겨 어긋나 있습니다.

이름 한가운데를 가로로 찢고 위아래를 좌우로 밀어 놓습니다.
읽을 수는 있는데 **읽는 데 0.2초가 더 걸립니다** — 그 0.2초가 시선을 잡습니다.
펑크 전단의 오래된 수법이고, 지금도 먹히는 이유는 눈이 어긋난 걸 못 견디기 때문입니다.

**어긋남은 딱 한 번.** 여러 번 어긋내면 고장 난 화면이 되고, 고장은 자극이 아니라 불량입니다.
색분해도 W 의 1% 안쪽 — 넘기면 3D 안경 쓴 화면이 됩니다.

찢긴 자리에는 **속살**이 보입니다. 아래에 깔린 형광색 판이 그 틈으로 드러납니다.

python poster_shred.py  →  out/poster/shred_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.028, 0.026, 0.032])
TOXIC = np.float32([1.00, 0.10, 0.62])            # 독성 마젠타
CYAN  = np.float32([0.20, 0.95, 0.95])
PAPER = np.float32([0.96, 0.96, 0.95])
DIM   = np.float32([0.56, 0.54, 0.60])


def tear(W, y, amp, seed=3):
    """찢긴 선 하나. **자로 자르면 절단이고, 들쭉날쭉해야 찢김이다.**"""
    rng = np.random.default_rng(seed)
    xs = np.arange(W, dtype=np.float32)
    line = np.zeros(W, np.float32)
    for f, a in ((0.0035, 1.0), (0.011, 0.45), (0.031, 0.22)):
        line += np.sin(xs * f * 2 * np.pi + rng.random() * 6.3) * a
    line += rng.standard_normal(W) * 0.25
    line = cv2.GaussianBlur(line.reshape(1, -1), (0, 0), 2.0).ravel()
    return y + line / max(np.abs(line).max(), 1e-6) * amp


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.070)
    CWD = W - M * 2

    # ── 속살. 찢긴 틈으로 이 판이 보인다 ──────────────────
    # 속살이 어두우면 찢긴 게 안 보인다. 아래 판은 확실히 밝아야 한다
    under = np.zeros((H, W, 3), np.float32) + TOXIC * 0.80
    for i in range(0, H, int(26 * V)):              # 아래 판에도 결이 있어야 종이가 두 장이다
        box(under, 0, i, W, i + max(1, int(9 * V)), TOXIC, 0.55)

    # ── 판 내용 ──────────────────────────────────────────
    ty = H * (0.085 if story else 0.078)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.90, anchor='c')

    # **이름을 두 줄로 키워 판을 채운다.** 한 줄로 두니 위쪽이 통째로 비어
    # 찢을 자리는 있는데 찢을 게 없었다. AFTER / SUNSET 을 쌓아 찢김이 낱말을 가른다.
    ny = H * (0.300 if story else 0.290)
    w1 = justify('AFTER', CWD, 0.02, cap=int(230 * V))
    m1 = tmask('AFTER', BRAND, w1, 0.02)
    w2 = justify('SUNSET', CWD, 0.02, cap=int(230 * V))
    m2 = tmask('SUNSET', BRAND, w2, 0.02)
    off = int(W * 0.008)
    for mm, yy0 in ((m1, ny), (m2, ny + m1.shape[0] * 1.06)):
        paint(img, mm, W / 2 - off, yy0, color=TOXIC, a=0.85, anchor='c')
        paint(img, mm, W / 2 + off, yy0, color=CYAN, a=0.70, anchor='c')
        paint(img, mm, W / 2, yy0, color=PAPER, anchor='c')
    nm = m2
    ny2 = ny + m1.shape[0] * 1.06
    paint(img, tmask(EV.FORMAT, BRAND, int(25 * V), 0.34), W / 2,
          ny2 + m2.shape[0] * 0.82, color=TOXIC, anchor='c')

    ly = H * (0.560 if story else 0.545)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.96, 0.12)), 0.12),
          W / 2, ly, color=PAPER, a=0.95, anchor='c')
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    paint(img, tmask(prog, BRAND, int(22 * V), 0.30), W / 2, ly + 48 * V,
          color=CYAN, a=0.95, anchor='c')

    fy = H * (0.700 if story else 0.688)
    rule(img, fy, M, W - M, PAPER, 0.22, max(2, int(3 * V)))
    paint(img, tmask(EV.DATE, KR, int(38 * V), 0.02), W / 2, fy + 50 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(21 * V), 0.02),
          W / 2, fy + 92 * V, color=DIM, a=0.98, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, fy + 124 * V,
          color=DIM, a=0.75, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.930,
          color=DIM, a=0.60, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), W / 2, H * 0.962,
          color=TOXIC, a=0.95, anchor='c')

    # ── 찢는다. **딱 한 번** ─────────────────────────────
    ty_line = tear(W, (ny + ny2) * 0.5, H * 0.020, seed=5)
    gap = int(H * 0.026)   # 틈이 좁으면 어긋난 게 아니라 인쇄 사고로 보인다
    shift = int(W * 0.062)
    yy = np.arange(H, dtype=np.float32)[:, None]
    below = (yy > ty_line[None, :]).astype(np.float32)

    out = under.copy()
    # 위쪽은 왼쪽으로, 아래쪽은 오른쪽으로 — 한 번만 어긋난다
    top = np.roll(img, -shift, axis=1)
    bot = np.roll(np.roll(img, shift, axis=1), gap, axis=0)
    m_top = (1 - below)[..., None]
    m_bot = np.roll(below, gap, axis=0)[..., None]
    out = out * (1 - m_top) + top * m_top
    out = out * (1 - m_bot) + bot * m_bot

    # 찢긴 가장자리 — 종이 단면이 밝다
    edge = np.abs(yy - ty_line[None, :]) < 2.5 * V
    out[edge] = PAPER * 0.85
    edge2 = np.abs(yy - (ty_line[None, :] + gap)) < 2.0 * V
    out[edge2] = TOXIC

    vignette(out, 0.28, 2.6)
    grain(out, 0.010, 28)
    return np.clip(out, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'shred_{k}')
        save(im, f'shred_{k}')
