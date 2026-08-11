"""
V안 — **삼중 벤.** 세 개가 겹친다는 걸 도형 하나로 말합니다.

원 셋이 서로 겹치고, 셋이 다 겹치는 가운데 자리에 행사 이름이 앉습니다.
POOL · SOLO · ELECTRONIC — 각 원에 하나씩. **설명이 필요 없는 유일한 도형**입니다.

**가운데가 제일 밝아야 합니다.** 세 원을 같은 밝기로 두면 도형 셋이고,
셋이 겹친 자리만 흰빛이어야 "여기가 이 행사다"로 읽힙니다.
빛은 겹칠수록 밝아지고, 그 규칙을 지켜야 도형이 아니라 조명이 됩니다.

원은 **속을 비운 테두리**로 그립니다. 채우면 세 색이 진흙이 되고,
비우면 겹친 자리만 계산해서 밝힐 수 있습니다.

python poster_venn.py  →  out/poster/venn_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save, info_block
from fest_kit import vignette, justify, night
from scene_kit import photoscene
from fonts import KR
import event as EV

INK   = np.float32([0.014, 0.018, 0.030])
AQUA  = np.float32([0.20, 0.92, 1.00])            # 물
ROSE  = np.float32([1.00, 0.24, 0.60])            # 혼자
LIME  = np.float32([0.72, 1.00, 0.24])            # 일렉
PAPER = np.float32([0.98, 0.99, 1.00])
DIM   = np.float32([0.58, 0.66, 0.74])


def band(H, W, cx, cy, R, t):
    """속 빈 원의 마스크. 채운 원이 아니라 **테두리**여야 겹침을 셀 수 있다."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return np.clip(1 - np.abs(d - R) / t, 0, 1) ** 0.7


def disc(H, W, cx, cy, R):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) < R).astype(np.float32)


def build(W, H, story=False):
    V = W / 1080.0
    # **배경이 검정이면 어느 행사에나 붙는 판이다.** 밤 수영장을 깔면
    # 도형이 무슨 얘기를 하든 일단 풀파티인 게 먼저 보인다.
    # **배경은 무늬가 아니라 장면이다.** 물결·타일만 깔면 여전히 상징이라
    # "추상적"이라는 지적이 남는다. 밤 루프탑 수영장에 사람이 있고 디제이가
    # 틀고 있는 그림을 뒤에 두면, 앞의 도형이 무슨 얘기를 하든 일단
    # 무슨 행사인지가 먼저 보인다. 뒤로 물러나야 하니 한 단 눌러 둔다.
    # **그린 장면은 자연스럽지 않다.** 선으로 그린 실루엣은 도표로 읽히고
    # 그 위에 네온을 얹으면 둘이 따로 논다. 자연스러움은 **사진의 결**에서
    # 온다 — 헤이즈의 얼룩, 물결의 불규칙은 코드로 흉내 낼수록 가짜 티가 난다.
    img = photoscene(W, H, story, wy=0.60 if story else 0.575)   # 감쇠는 걷었다 — 어두움은 아래 눌림에서만 가져온다

    CX = W / 2
    # 짧은 피드에서 고리 라벨이 아래 글자와 부딪힌다. 원을 줄이고 위로 올린다
    CY = H * (0.400 if story else 0.360)
    R = W * (0.235 if story else 0.196)
    d = R * 0.60                                   # 원 사이 거리
    t = R * 0.085                                  # 테두리 두께

    # 위 하나, 아래 둘 — 삼중 벤의 표준 배치
    P = [(CX, CY - d * 0.72, AQUA, 'POOL'),
         (CX - d * 0.86, CY + d * 0.52, ROSE, 'SOLO'),
         (CX + d * 0.86, CY + d * 0.52, LIME, 'ELECTRONIC')]

    rings = []
    for cx, cy, col, _ in P:
        m = band(H, W, cx, cy, R, t)
        rings.append(m)
        img += cv2.GaussianBlur(m, (0, 0), t * 1.9)[..., None] * col * 0.55
        img[:] = img * (1 - m[..., None] * 0.92) + col * m[..., None] * 0.92

    # **셋이 다 겹치는 자리.** 여기만 흰빛이다
    core = disc(H, W, P[0][0], P[0][1], R)
    for cx, cy, _, _ in P[1:]:
        core = np.minimum(core, disc(H, W, cx, cy, R))
    img += cv2.GaussianBlur(core, (0, 0), R * 0.22)[..., None] * PAPER * 0.55
    img += cv2.GaussianBlur(core, (0, 0), R * 0.55)[..., None] * np.float32([0.7, 0.9, 1.0]) * 0.35

    # 원마다 낱말 하나 — 원 안 바깥쪽에. 가운데는 이름 자리다
    # 라벨을 고리 안쪽에 두니 선 위에 얹혔다. **바깥으로 빼야 고리도 글자도 산다**
    for (cx, cy, col, txt), dyk in zip(P, (-1.22, 1.16, 1.16)):
        sz = int((30 if len(txt) < 8 else 22) * V)
        paint(img, tmask(txt, BRAND, sz, 0.26), cx, cy + R * dyk, color=col, anchor='c')

    # ── 가운데 : 이름 ────────────────────────────────────
    M = int(W * 0.075)
    CWD = W - M * 2
    ns = justify(EV.NAME, R * 1.24, 0.06, cap=int(74 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.06), CX, CY - 14 * V, color=INK, anchor='c')
    # 한 판 안에서 날짜 표기가 두 가지면 안 된다 — 발치와 같은 형식으로
    paint(img, tmask(EV.DATE_EN, BRAND, int(19 * V), 0.14), CX, CY + 28 * V,
          color=INK, anchor='c')

    # ── 머리 · 발 ────────────────────────────────────────
    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.85, anchor='c')
    # **발치는 비율이 아니라 바닥에서 역산한다.** 0.79H 로 잡았더니 피드(1350)에서
    # 정보 네 줄 + 협업 + 핸들이 캔버스를 넘어갔다. 블록 높이가 정해져 있으니
    # 아래에서 빼는 게 맞다 — 두 사이즈에서 같은 자리에 앉는다.
    # 정보가 네 줄에서 **다섯 줄**로 늘었다(입장 조건 추가). 한 줄(46V)만큼
    # 발치를 더 올려야 캔버스를 안 넘는다.
    # 줄이 다섯에서 **여섯**으로 늘었고(애프터파티) 잔글씨 한 줄이 붙었다.
    # 발치를 그만큼 올려야 핸들이 캔버스를 안 넘는다 — 안 올렸더니 잘려 나왔다.
    fy = H - 452 * V
    # 정보는 **event.INFO 형식 그대로**. 순서·표기를 판마다 바꾸지 않는다
    # **바쁜 배경에서는 발치를 눌러야 글자가 산다.** 그림자를 덧대면 지저분해지고,
    # 배경을 죽이면 깨끗하다 — 이 판 전체에서 지켜 온 규칙과 같다.
    _fy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.68 * np.clip((_fy - (fy - 30 * V)) / (60 * V), 0, 1))
    # 발치는 라인업 아래에서 한 번만 그린다 — 여기서 한 번 더 그리면
    # 같은 자리에 두 번 얹혀 괘선 알파가 겹치고 이 판만 굵어 보인다.
    # **이름을 아래에 또 쓰지 않는다.** 가운데 교집합에 이미 있고, 두 번 쓰면
    # 큰 글자가 둘이 되어 어느 쪽을 봐야 할지 모르게 된다. 그 자리를 비우니
    # 짧은 피드(1350)에서 고리 라벨과 발치가 안 부딪힌다.
    ly = fy - 96 * V
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34), W / 2, ly - 48 * V,
          color=AQUA, anchor='c')
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.92, anchor='c')

    yb = info_block(img, M, fy + 44 * V, CWD, V, AQUA, PAPER, head_color=PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.60)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=AQUA, a=0.90)



    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 34)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'venn_{k}')
        save(im, f'venn_{k}')
