"""릴스 커버(썸네일) — 1080×1920.

    out/short/cover_ad.png

**커버는 두 군데에서 다르게 보인다.**

    릴스 재생 화면   1080×1920 전체
    프로필 격자      가운데 1080×1350 만 (위 285px · 아래 285px 는 잘림)

그래서 **중요한 건 전부 285 ~ 1635 안에** 둔다. 이 줄(`TOP`·`TH`)을 넘긴
글자는 프로필에서 잘려 나가고, 계정을 보러 온 사람은 잘린 판을 본다.

**첫 줄이 커버의 전부다.** 격자에서는 소리도 움직임도 없고 글자 한 줄만
남는다 — 영상 안의 훅과 같은 문장을 쓴다. 다른 말을 쓰면 눌렀을 때
다른 영상이 나온 것처럼 읽힌다.

얼굴이 정면으로 잡히는 순간은 안 쓴다(`short_card.AD_SHOTS` 와 같은 이유).

python short_cover.py
"""
import os
import numpy as np
import cv2
from PIL import Image
import short as S
from short import crop916, grade, load
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from poster_kit import status_tag as _tag
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
TH = 1350                                 # 격자에 보이는 높이
TOP = (H - TH) // 2                       # 285

PAPER = np.float32([0.99, 1.00, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
AQUA = np.float32([0.34, 0.94, 1.00])

# (클립, 초, 가로 위치)
# **커버는 프로필에 계속 남는 판이다.** 영상은 지나가지만 이건 안 지나간다 —
# 손님 얼굴이 알아볼 만하게 잡힌 컷은 쓰지 않는다.
# `crowd 1.4` 로 뒀다가 앞쪽 얼굴이 또렷해서 바꿨다. 이 컷은 사람이
# 원경에 있고 앞은 튜브와 조명이라, **사람이 많다는 건 남고 얼굴은 안 남는다.**
SHOT = ('floor', 2.8, 0.46)
HEAD = '혼자 와도 되는 풀파티'            # **영상 첫 장과 같은 문장이어야 한다**


def frame():
    key, at, ox = SHOT
    c = load(key)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    c.release()
    if not ok:
        raise SystemExit(f'{key} {at}s 를 못 읽었습니다')
    return grade(crop916(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), ox, 1.02)
                 .astype(np.float32) / 255)


def build():
    img = frame()
    yy = np.arange(H, dtype=np.float32)[:, None, None]

    # **잘리는 위아래를 어둡게 눌러 둔다.** 격자에서 잘린 자리가 그대로 밝으면
    # 재생 화면에서 위아래가 붕 떠 보인다 — 눌러 두면 가운데가 판으로 읽힌다
    img *= 1 - 0.62 * np.clip((TOP + 40 - yy) / (TOP + 40), 0, 1) ** 0.9
    img *= 1 - 0.62 * np.clip((yy - (TOP + TH - 40)) / (TOP + 40), 0, 1) ** 0.9
    # 글자가 앉는 아래쪽을 통째로 떨어뜨린다. 띠를 두르지 않는다
    img *= 1 - 0.66 * np.clip((yy - H * 0.50) / (H * 0.22), 0, 1) ** 1.1
    # **제목 자리도 눌러야 한다.** 뒤에 형광 기둥이 서 있어서 흰 글자가
    # 거기서만 먹혔다 — 띠 대신 가우시안으로 부드럽게 떨어뜨린다
    img *= 1 - 0.42 * np.exp(-((yy - (TOP + 180)) / 130.0) ** 2)

    lg = logo(58)
    paint(img, lg, W / 2 - lg.shape[1] / 2, TOP + 96, color=PAPER, a=0.94)
    paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.62, 0.14), 0.14),
          W / 2, TOP + 176, color=PAPER, a=0.92, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 22, 0.34), W / 2, TOP + 222,
          color=AQUA, a=0.88, anchor='c')

    # ── 훅. 커버에서 제일 큰 것 ──────────────────────────
    fs = min(104, fit(HEAD, KRB, W * 0.86, 0.02))
    paint(img, tmask(HEAD, KRB, fs, 0.02), W / 2, TOP + 830, color=PAPER, anchor='c')

    rule(img, TOP + 918, W * 0.14, W * 0.86, PAPER, 0.26, 2)
    paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 40, 0.02), W / 2, TOP + 976,
          color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.price_str(), KR, 34, 0.02), W / 2, TOP + 1030,
          color=PAPER, a=0.76, anchor='c')

    # 상태는 왼쪽 여백선에. 가운데에 홀로 뜨면 나중에 얹은 것으로 읽힌다
    _tag(img, W * 0.085, TOP + 1140, 38, color=PAPER, accent=CORAL, width=W * 0.80)
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.22), W / 2, TOP + 1276,
          color=PAPER, a=0.70, anchor='c')

    # **격자에서 잘리는지 눈으로 못 본다** — 자리를 재서 막는다
    assert TOP + 1276 < TOP + TH - 20, '아이디 줄이 격자 밖으로 나갑니다'
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    img = build()
    p = os.path.join(OUT, 'cover_ad.png')
    Image.fromarray((img * 255).astype(np.uint8)).save(p, optimize=True)
    print(f'{p}  {W}x{H}   격자에 보이는 구간 {TOP}~{TOP + TH}px')
