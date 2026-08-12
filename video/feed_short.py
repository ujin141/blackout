"""
현장 영상 줄판 — 바이럴 릴스를 피드에 올려도 그리드가 안 깨지게.

    │ 현장 사진 │ 릴스 │ 정보 · 예약 │   ← 세 칸이 이어진 한 장

**영상은 세 칸으로 못 쪼갠다.** 그래서 현장 프레임 한 장으로 줄판을 만들고
**가운데 칸을 릴스 자리로** 쓴다. 릴스 커버를 이 판의 2칸으로 주면, 그리드에서
릴스가 그 자리에 정확히 앉아 세 칸이 한 장으로 이어진다.

    1칸  사진 게시물
    2칸  릴스 (커버 = shortrow_2_cover.png)
    3칸  사진 게시물

**프레임은 넓게 쓸 수 있는 것으로 고른다.** 클립 다섯을 2.4:1 로 잘라 놓고
비교하면 대부분 한쪽에 몰려 있는데, `crowd` 1.0초는 물 안이 꽉 차서 띠를
그대로 채운다. 줄판에서 제일 중요한 건 구도가 가로냐다.

**1920 을 3240 으로 늘린다(1.69배).** 원본이 영상이라 늘리면 물러지지만,
판을 어둡게 눌러 쓰기 때문에 휴대폰에서는 안 보인다 — 대신 **글자는
늘린 사진 위에 새로 그린다**. 사진을 늘린 뒤에 그려야 글자가 안 뭉갠다.

이음새(x=1080, 2160)에는 아무것도 안 올린다. 올리는 순서는 3칸 → 2칸 → 1칸.

⚠ **실제 손님 얼굴이 나온다.** 초상권은 저작권과 별개다. 아는 얼굴이 있으면
   올리기 전에 물어보는 게 안전하다. 프레임을 바꾸려면 FRAME 만 고치면 된다.

python feed_short.py  →  out/feed_event/shortrow_{1,2,3}.png · _full.png · _2_cover.png
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, grain
from fest_kit import justify, vignette
from fonts import KR, KRB
import event as EV
import short

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T = 135
SEAM = 90
FRAME = ('crowd', 1.0)            # 물 안이 제일 꽉 찬 프레임

PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
DIM = np.float32([0.62, 0.74, 0.82])


def wide():
    """영상에서 2.4:1 띠를 떠서 3240×1350 으로 늘린다."""
    key, at = FRAME
    c = short.load(key)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    c.release()
    if not ok:
        raise SystemExit('프레임을 못 읽었습니다')
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    h, w = fr.shape[:2]
    bh = int(w * TH / W)
    y0 = (h - bh) // 2
    return cv2.resize(fr[y0:y0 + bh], (W, H), interpolation=cv2.INTER_CUBIC)


def build():
    img = wide()
    # 릴스와 같은 톤으로 맞춘다 — 한 계정에서 나온 두 판이 색이 다르면 따로 논다
    img = np.clip((img - 0.5) * 1.14 + 0.5, 0, 1)
    g = img @ np.float32([0.299, 0.587, 0.114])
    img = np.clip(g[..., None] + (img - g[..., None]) * 1.20, 0, 1)
    img *= 0.60

    yy = np.arange(H, dtype=np.float32)[:, None, None]
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    img *= 1 - 0.40 * np.exp(-((xx - W / 2) / (TW * 0.55)) ** 2)   # 가운데(릴스 칸)
    img *= 1 - 0.66 * np.exp(-((xx - W * 5 / 6) / (TW * 0.52)) ** 2) * \
        np.clip((yy - 560) / 200, 0, 1)
    # **원본이 현장 사진이라 밝은 사람이 그대로 뒤에 온다** — 0.46 으로는
    # 흰 글자가 노란 옷 위에서 안 읽혔다. 표가 앉는 자리는 더 눌러야 한다
    img *= 1 - 0.66 * np.clip((yy - 1050) / 130, 0, 1)             # 발치

    # ── 1칸 · 훅 ─────────────────────────────────────────
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, 18, 0.42), TW / 2, SAFE_T + 30,
          color=DIM, a=0.85, anchor='c')
    paint(img, tmask('여기 서울이에요', KRB, 62, 0.02), TW / 2, 560,
          color=PAPER, anchor='c')
    paint(img, tmask('양재 루프탑 풀파티', KR, 30, 0.03), TW / 2, 636,
          color=AQUA, a=0.96, anchor='c')

    # ── 2칸 · 릴스가 앉는 자리 ────────────────────────────
    x0 = TW
    ns = fit(EV.NAME, BRAND, TW - SEAM * 2, 0.10)
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), x0 + TW / 2, 520, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 25, 0.36), x0 + TW / 2, 596, color=AQUA, anchor='c')
    rule(img, 660, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.20, 2)
    paint(img, tmask(EV.DATE_EN, BRAND, 40, 0.20), x0 + TW / 2, 726, color=PAPER, anchor='c')
    paint(img, tmask(EV.LINEUP_STR, BRAND,
                     int(justify(EV.LINEUP_STR, TW - SEAM * 2, 0.13)), 0.13),
          x0 + TW / 2, 806, color=PAPER, a=0.92, anchor='c')

    # ── 3칸 · 정보 · 예약 ─────────────────────────────────
    x0 = TW * 2
    y = 700
    for k, v in (('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE), ('ENTRY', EV.ENTRY),
                 ('AFTER', EV.AFTER), ('NOTICE', EV.AGE)):
        paint_bl(img, tmask_bl(k, BRAND, 15, 0.24), x0 + SEAM, y, color=AQUA, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 19,
                               0.14 if v.isascii() else 0.01),
                 x0 + SEAM + 130, y, color=PAPER, a=0.98)
        y += 40
    paint_bl(img, tmask_bl(EV.ADDR, KR, 16, 0.01), x0 + SEAM + 130, y + 2,
             color=DIM, a=0.85)

    # ── 발치 — 칸마다 한 줄. 혼자 떠도 읽히게 ─────────────
    FY = 1130
    rule(img, FY - 44, SEAM, W - SEAM, PAPER, 0.14, 1)
    paint(img, tmask('8.29 SAT', BRAND, 30, 0.22), TW / 2, FY, color=PAPER, anchor='c')
    paint(img, tmask(EV.TAGLINE, KR, 24, 0.02), TW * 1.5, FY, color=PAPER,
          a=0.94, anchor='c')
    paint(img, tmask('예약 · 프로필 링크', KR, 26, 0.02), TW * 2.5, FY,
          color=CORAL, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND,
                     min(13, fit(EV.PARTNERS_STR, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          TW / 2, FY + 46, color=DIM, a=0.62, anchor='c')
    paint(img, tmask(EV.RULES, KR, 13, 0.01), TW * 1.5, FY + 46, color=DIM,
          a=0.62, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 17, 0.24), TW * 2.5, FY + 46,
          color=DIM, a=0.85, anchor='c')

    vignette(img, 0.24, 2.4)
    grain(img, 0.006, 29)
    return np.clip(img, 0, 1)


def cover(tile):
    """릴스 커버(1080×1920). 그리드는 가운데를 4:5 로 잘라 보여주므로
    타일을 정확히 가운데(위 285px) 놓아야 줄이 이어진다."""
    CH = 1920
    top = (CH - TH) // 2
    a = np.asarray(tile).astype(np.float32) / 255.0
    canvas = np.zeros((CH, TW, 3), np.float32)
    canvas[top:top + TH] = a
    for i in range(top):
        f = (1 - i / top) ** 1.6
        canvas[top - 1 - i] = a[0] * f
        canvas[top + TH + i] = a[-1] * f
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    full = Image.fromarray((build() * 255).astype(np.uint8))
    full.save(os.path.join(OUT, 'shortrow_full.png'), optimize=True)
    tiles = []
    for i in range(3):
        t = full.crop((i * TW, 0, (i + 1) * TW, TH))
        p = os.path.join(OUT, f'shortrow_{i + 1}.png')
        t.save(p, optimize=True)
        tiles.append(t)
        print(p)
    cover(tiles[1]).save(os.path.join(OUT, 'shortrow_2_cover.png'), optimize=True)
    print(os.path.join(OUT, 'shortrow_2_cover.png'), '← 릴스 커버 (2칸 자리)')
    print('\n1칸·3칸은 사진 게시물, 2칸은 릴스. 올리는 순서: 3칸 → 2칸(릴스) → 1칸')
