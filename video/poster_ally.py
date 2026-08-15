"""협업 발표 판 — 스토리 · 피드.

**이건 모객 판이 아니라 브랜드 판이다.** 그래서 흑백으로 간다 —
컬러 예외는 행사 티켓을 파는 판에만 준다.

    ally_story.png  1080×1920  스토리
    ally_feed.png   1080×1350  피드

파는 게 없으니 넣을 것도 없다. 날짜도 가격도 안 적는다 —
**"우리가 이 네 곳과 같이 간다" 한 문장이 전부**고, 거기에 뭘 더하면
그 문장이 묽어진다.

이름은 세로로 쌓는다. 한 줄에 `A × B × C × D` 로 붙이면 글자가 작아져서
넷 다 안 읽힌다 — 쌓으면 하나씩 눈에 들어오고, 사이의 × 가 세로로 이어져
그 자체로 무늬가 된다.

이름 밑에 동네를 적는다. 같은 이름의 다른 지점이 흔해서 안 적으면
어디냐고 묻는다.

python poster_ally.py  →  out/poster/ally_{story,feed}.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, rule, logo, grain, save
from fonts import KR, KRB
import event as EV

INK = np.float32([0.020, 0.020, 0.024])
PAPER = np.float32([0.97, 0.97, 0.96])
DIM = np.float32([0.50, 0.51, 0.55])


def field(W, H):
    """검정 판에 빛 한 겹. **무늬를 안 넣는다** — 이름이 그림이다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - W * 0.5) / (W * 0.72)) ** 2
                    + ((yy - H * 0.44) / (H * 0.40)) ** 2))[..., None] * PAPER * 0.10
    # 위아래를 눌러 가운데로 눈을 모은다
    img *= (1 - 0.55 * np.clip((H * 0.13 - yy) / (H * 0.13), 0, 1))[..., None]
    img *= (1 - 0.55 * np.clip((yy - H * 0.88) / (H * 0.12), 0, 1))[..., None]
    return img


def build(W, H, story):
    V = H / 1920
    img = field(W, H)
    cx = W / 2

    lg = logo(int(66 * V))
    paint(img, lg, cx - lg.shape[1] / 2, 176 * V, color=PAPER, a=0.95)
    paint(img, tmask('BAND BENEFITS', BRAND, int(16 * V), 0.50), cx, 262 * V,
          color=DIM, anchor='c')
    # **제목이 이름 목록이 아니라 혜택이어야 한다.** 이름만 늘어놓으면
    # "그래서 뭐" 로 끝난다 — 밴드가 그날 하루짜리가 아니라는 게 요점이다
    paint(img, tmask('밴드 차고 가면', KRB, int(60 * V), 0.0), cx, 330 * V,
          color=PAPER, anchor='c')
    # **언제 되는지가 바로 밑에 붙어야 한다** — 안 적으면 아무 날에나
    # 되는 줄 알고, 그 항의는 협업사가 아니라 우리한테 온다
    paint(img, tmask(EV.BAND_WHEN, KRB, int(26 * V), 0.02), cx, 386 * V,
          color=DIM, a=1.0, anchor='c')

    # ── 이름 넷. 쌓아야 넷 다 읽힌다 ──────────────────────
    n = len(EV.ALLIES)
    top = H * (0.262 if story else 0.250)
    step = H * (0.128 if story else 0.142)
    for i, (en, ko, dong, perk) in enumerate(EV.ALLIES):
        y = top + step * (i + 1)
        rule(img, y - step * 0.50, W * 0.20, W * 0.80, PAPER, 0.13, max(1, int(V)))
        # 영문 이름이 있으면 그걸 크게, 없으면 한글을 크게
        if en:
            paint(img, tmask(en, BRAND, min(int(46 * V), fit(en, BRAND, W * 0.80, 0.14)),
                             0.14), cx, y - 24 * V, color=PAPER, anchor='c')
            sub = f'{ko}   {dong}'
        else:
            paint(img, tmask(ko, KRB, min(int(48 * V), fit(ko, KRB, W * 0.80, 0.06)),
                             0.06), cx, y - 24 * V, color=PAPER, anchor='c')
            sub = dong
        paint(img, tmask(sub, KR, int(18 * V), 0.02), cx, y + 12 * V,
              color=DIM, a=0.92, anchor='c')
        # **혜택이 제일 중요한 줄이다** — 이름보다 작아도 색이 밝으면 먼저 읽힌다
        paint(img, tmask(perk, KRB, min(int(28 * V), fit(perk, KRB, W * 0.80, 0.02)),
                         0.02), cx, y + 50 * V, color=PAPER, anchor='c')

    y = top + step * (n + 0.58)
    rule(img, y, W * 0.20, W * 0.80, PAPER, 0.20, max(1, int(V)))
    paint(img, tmask(EV.BAND_PERK, KRB, int(28 * V), 0.02), cx, y + 52 * V,
          color=PAPER, anchor='c')

    fy = H - (150 * V if story else 118 * V)
    paint(img, tmask(EV.HANDLE, BRAND,
                     min(int(22 * V), fit(EV.HANDLE, BRAND, W * 0.80, 0.24)), 0.24),
          cx, fy, color=PAPER, a=0.88, anchor='c')
    paint(img, tmask('SEOUL  ·  DJ CREW', BRAND, int(14 * V), 0.44), cx, fy + 40 * V,
          color=DIM, a=0.85, anchor='c')
    grain(img, 0.007, 23)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for name, (W, H, story) in (('story', (1080, 1920, True)),
                                ('feed', (1080, 1350, False))):
        save(build(W, H, story), f'ally_{name}')
