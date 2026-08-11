"""
AF안 — **밤.** 한글 헤드라인이 제일 크고, 그 아래가 장면입니다.

**도형이 아니라 장면입니다.** 벤 다이어그램·물결·튜브는 컨셉을 상징으로 옮긴 것이라
보는 사람이 한 번 해석해야 뜻이 옵니다 — 그게 "추상적" 의 정체입니다.
이 판은 해석할 게 없습니다. 밤 루프탑 수영장에 사람이 있고 디제이가 틀고 있습니다.

한국 사람이 보는 판이라 **"루프탑 풀파티" 가 제일 큽니다.**
영문 행사명은 브랜드지 정보가 아니라 그 아래에 둡니다.

장면은 `scene_kit.poolscene()` 이 그리고, 이 파일은 **그 위에 글자를 어떻게 앉히는지**만
정합니다. 세 판(night · deck · dive)이 같은 장면을 쓰고 짜임만 다릅니다.

python poster_night.py  →  out/poster/night_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, SIZES, tmask, paint, rule, grain, save, info_block)
from fest_kit import vignette, justify, night
from scene_kit import photoscene
from fonts import KR, KRD
import event as EV

PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.36, 0.92, 1.00])
DIM   = np.float32([0.62, 0.74, 0.82])

HEADLINE = '루프탑 풀파티'


def build(W, H, story=False):
    V = W / 1080.0
    # **그린 장면은 자연스럽지 않다.** 선으로 그린 실루엣은 도표로 읽히고
    # 그 위에 네온을 얹으면 둘이 따로 논다. 자연스러움은 **사진의 결**에서
    # 온다 — 헤이즈의 얼룩, 물결의 불규칙은 코드로 흉내 낼수록 가짜 티가 난다.
    img = photoscene(W, H, story, wy=0.615 if story else 0.585)
    M = int(W * 0.075)
    CWD = W - M * 2
    yy = np.arange(H, dtype=np.float32)[:, None, None]

    # 위쪽 하늘을 눌러 헤드라인 자리를 만든다. **장면은 그대로 두고 배경만 죽인다**
    img *= (1 - 0.72 * np.clip((H * 0.335 - yy) / (H * 0.335), 0, 1) ** 0.9)

    ty = H * (0.062 if story else 0.055)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)

    hy = H * (0.152 if story else 0.140)
    hs = justify(HEADLINE, CWD, 0.08, path=KRD, cap=int(118 * V))
    paint(img, tmask(HEADLINE, KRD, hs, 0.08), M, hy, color=PAPER)
    ns = justify(EV.NAME, CWD * 0.78, 0.10, cap=int(52 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), M, hy + hs * 0.82, color=AQUA)
    paint(img, tmask(EV.FORMAT, BRAND, int(18 * V), 0.30), M, hy + hs * 0.82 + 34 * V,
          color=PAPER, a=0.80)

    # 라인업은 수면 바로 위 — 데크에 걸린 것처럼 보인다
    ly = H * (0.585 if story else 0.552)
    img *= (1 - 0.60 * np.exp(-((yy - ly) / (H * 0.030)) ** 2))
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.96, 0.12)), 0.12),
          W / 2, ly, color=PAPER, a=0.97, anchor='c')

    # 정보가 네 줄에서 **다섯 줄**로 늘었다(입장 조건 추가). 한 줄(46V)만큼
    # 발치를 더 올려야 캔버스를 안 넘는다.
    # 줄이 다섯에서 **여섯**으로 늘었고(애프터파티) 잔글씨 한 줄이 붙었다.
    # 발치를 그만큼 올려야 핸들이 캔버스를 안 넘는다 — 안 올렸더니 잘려 나왔다.
    fy = H - 452 * V
    img *= (1 - 0.74 * np.clip((yy - (fy - 34 * V)) / (68 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    yb = info_block(img, M, fy + 44 * V, CWD, V, AQUA, PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.62)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=AQUA, a=0.92)
    # 예매 경로. **핸들과 같은 줄 오른쪽 끝**에 둔다 — 세로 자리를 안 먹어서
    # 짜임이 안 흔들리고, 눈은 핸들과 한 덩어리로 읽는다.
    paint(img, tmask(EV.RESERVE, KR, int(13 * V), 0.02), W - M, yb + 70 * V,
          color=AQUA, a=0.90, anchor='r')

    vignette(img, 0.34, 2.2)
    grain(img, 0.007, 60)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'night_{k}')
        save(im, f'night_{k}')
