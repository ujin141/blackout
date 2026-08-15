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
    # **제목이 이름 목록이 아니라 혜택이어야 한다.** 이름만 늘어놓으면
    # "그래서 뭐" 로 끝난다 — 밴드가 그날 하루짜리가 아니라는 게 요점이다.
    # 두 줄로 쌓아 세운다. 한 줄로 붙이면 글자가 반으로 준다
    for i, t in enumerate((EV.BAND_HEAD, EV.BAND_HEAD2)):
        paint(img, tmask(t, BRAND, min(int(78 * V), fit(t, BRAND, W * 0.84, 0.06)), 0.06),
              cx, (272 + i * 82) * V, color=PAPER, anchor='c')
    # **언제 되는지가 바로 밑에 붙어야 한다** — 안 적으면 아무 날에나
    # 되는 줄 알고, 그 항의는 협업사가 아니라 우리한테 온다
    paint(img, tmask(EV.BAND_WHEN, BRAND, int(19 * V), 0.34), cx, 424 * V,
          color=PAPER, a=0.90, anchor='c')
    paint(img, tmask(EV.BAND_WHEN_KO, KR, int(20 * V), 0.02), cx, 462 * V,
          color=PAPER, a=0.72, anchor='c')

    # ── 이름 넷. 쌓아야 넷 다 읽힌다 ──────────────────────
    n = len(EV.ALLIES)
    top = H * (0.272 if story else 0.258)
    step = H * (0.122 if story else 0.136)
    for i, (en, sub, perk, perk_ko) in enumerate(EV.ALLIES):
        y = top + step * (i + 1)
        rule(img, y - step * 0.50, W * 0.16, W * 0.84, PAPER, 0.13, max(1, int(V)))
        paint(img, tmask(en, BRAND, min(int(44 * V), fit(en, BRAND, W * 0.84, 0.14)),
                         0.14), cx, y - 34 * V, color=PAPER, anchor='c')
        # **혜택이 제일 중요한 줄이다.** 영문을 크게 쓴다
        paint(img, tmask(perk, BRAND, min(int(27 * V), fit(perk, BRAND, W * 0.84, 0.16)),
                         0.16), cx, y + 12 * V, color=PAPER, a=0.96, anchor='c')
        # **한글을 두 줄로 두면 한 칸에 넉 줄이 되어 다 뭉갠다.**
        # 가게와 혜택을 한 줄로 합치고 크기를 올려 읽히게 한다
        ko = f'{sub}  —  {perk_ko}'
        paint(img, tmask(ko, KR, min(int(19 * V), fit(ko, KR, W * 0.86, 0.02)), 0.02),
              cx, y + 50 * V, color=PAPER, a=0.68, anchor='c')

    y = top + step * (n + 0.56)
    rule(img, y, W * 0.16, W * 0.84, PAPER, 0.20, max(1, int(V)))
    paint(img, tmask(EV.BAND_PERK, BRAND,
                     min(int(24 * V), fit(EV.BAND_PERK, BRAND, W * 0.84, 0.26)), 0.26),
          cx, y + 48 * V, color=PAPER, anchor='c')

    fy = H - (150 * V if story else 118 * V)
    # **목록이 늘면 마무리 줄이 발치로 밀려 겹친다.** 눈으로는 뒤늦게 보인다 —
    # 자리를 재서 안 겹치는지 확인한다. 곳을 더 넣으면 여기서 먼저 걸린다
    assert y + 48 * V < fy - 44 * V, (
        f'마무리 줄({y + 48 * V:.0f})이 발치({fy:.0f})와 겹칩니다 — '
        f'ALLIES 가 {n} 개입니다. step 을 줄이세요')
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
