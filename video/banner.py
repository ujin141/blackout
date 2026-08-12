"""
X(트위터) 프로필 배너 — 1500×500.

    x_banner.png        상시용. 크루 이름만
    x_banner_event.png  행사 기간용. 오른쪽에 AFTER SUNSET 한 줄

**왼쪽 아래를 비워 둔다.** 프로필 사진이 배너 아래 테두리에 반쯤 걸쳐서
왼쪽 아래를 덮는다 — 데스크톱에서 대략 x 40~230 · y 360~500 이다.
거기 글자를 두면 얼굴 뒤로 사라진다.

**세로 가운데 60% 안에만 글자를 둔다.** 화면 폭에 따라 배너가 위아래로 잘린다.
3:1 로 딱 맞게 보이는 건 데스크톱뿐이고, 좁은 창에서는 위아래가 먹힌다.

브랜드가 흑백이라 배너도 흑백이다. 포스터의 컬러 예외는 행사 모객용에만
해당하고, 프로필은 상시 노출이라 크루 톤을 따른다.

python banner.py  →  out/banner/x_banner{,_event}.png
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, rule, logo, grain
from fonts import KR
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'banner')
os.makedirs(OUT, exist_ok=True)

W, H = 1500, 500
# 프로필 사진이 덮는 자리. 여기엔 아무것도 안 둔다
AVATAR = (40, 360, 230, 500)
SAFE_T, SAFE_B = 90, 410          # 좁은 창에서 잘리는 위아래를 뺀 구간

INK = np.float32([0.020, 0.020, 0.024])
PAPER = np.float32([0.97, 0.97, 0.96])
DIM = np.float32([0.52, 0.53, 0.56])


def field():
    """검정 판에 아주 옅은 빛 한 겹. **무늬를 넣지 않는다** —
    배너는 프로필의 배경이지 그 자체가 그림이 아니다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W * 0.46) / (W * 0.34)) ** 2 + ((yy - H * 0.46) / (H * 0.85)) ** 2))
    img += g[..., None] * np.float32([0.16, 0.17, 0.20])
    # 가로로 지나가는 아주 옅은 띠 하나. 판이 죽지 않을 만큼만
    band = np.exp(-((yy - H * 0.42) / (H * 0.10)) ** 2) * 0.05
    img += band[..., None] * PAPER
    return img


def build(with_event=False):
    img = field()
    cy = H * 0.46

    # 로고 + 워드마크를 한 덩어리로 가운데 왼쪽에. 프로필 사진 자리는 피한다
    lh = 88
    lg = logo(lh)
    gap = 30
    x0 = AVATAR[2] + 40                           # 프로필 사진 오른쪽에서 시작한다
    # **워드마크 크기를 눈대중으로 박지 않는다.** 46 으로 뒀더니 오른쪽 글자를
    # 파고들었다 — 남은 폭에서 역산해야 두 덩어리가 안 부딪힌다.
    LEFT_END = W * 0.560
    ws = min(40, fit('BLACKOUT CREW', BRAND, LEFT_END - x0 - lg.shape[1] - gap, 0.34))
    wm = tmask('BLACKOUT CREW', BRAND, ws, 0.34)
    paint(img, lg, x0, cy - 12, color=PAPER, a=0.97)
    paint(img, wm, x0 + lg.shape[1] + gap, cy - 12, color=PAPER)
    paint(img, tmask('SEOUL  ·  SINCE 2026', BRAND, 17, 0.42),
          x0 + lg.shape[1] + gap, cy + 44, color=DIM, a=0.90)

    # 오른쪽 — 상시는 성격, 행사 기간에는 행사
    rx = W - int(W * 0.055)
    RIGHT_START = W * 0.600      # 왼쪽 덩어리와 이 사이는 비워 둔다
    if with_event:
        rule(img, cy - 66, RIGHT_START, rx, PAPER, 0.18, 1)
        paint(img, tmask(EV.NAME, BRAND,
                         min(38, fit(EV.NAME, BRAND, rx - RIGHT_START, 0.14)), 0.14), rx, cy - 22,
              color=PAPER, anchor='r')
        paint(img, tmask(EV.FORMAT, BRAND, 15, 0.36), rx, cy + 18,
              color=DIM, a=0.95, anchor='r')
        paint(img, tmask(f'{EV.DATE_EN}   {EV.VENUE}', KR,
                         min(18, fit(f'{EV.DATE_EN}   {EV.VENUE}', KR, rx - RIGHT_START, 0.02)),
                         0.02), rx, cy + 62,
              color=PAPER, a=0.90, anchor='r')
        rule(img, cy + 92, RIGHT_START, rx, PAPER, 0.18, 1)
    else:
        paint(img, tmask('MUSIC  ·  CONTENT  ·  COMMUNITY', BRAND,
                         min(16, fit('MUSIC  ·  CONTENT  ·  COMMUNITY', BRAND, rx - RIGHT_START, 0.42)),
                         0.42), rx, cy - 18,
              color=DIM, a=0.85, anchor='r')
        paint(img, tmask('HOUSE  ·  TECHNO  ·  EDM', BRAND,
                         min(16, fit('HOUSE  ·  TECHNO  ·  EDM', BRAND, rx - RIGHT_START, 0.42)),
                         0.42), rx, cy + 18,
              color=DIM, a=0.70, anchor='r')

    grain(img, 0.006, 13)
    return np.clip(img, 0, 1)


def check(a):
    """프로필 사진 자리에 밝은 것이 들어갔는지 잰다 — 들어가면 얼굴 뒤로 사라진다."""
    x0, y0, x1, y1 = AVATAR
    g = a[y0:y1, x0:x1] @ np.float32([0.299, 0.587, 0.114])
    return float(g.max())


if __name__ == '__main__':
    for ev, name in ((False, 'x_banner'), (True, 'x_banner_event')):
        a = build(ev)
        p = os.path.join(OUT, f'{name}.png')
        Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
        print(f'{p}  {W}x{H}  프로필 사진 자리 최대 밝기 {check(a):.3f} (0.25 아래면 안전)')
