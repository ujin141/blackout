"""**인쇄물을 보여주는 스토리 판.** 1080×1920.

    out/story/story_coupon.png
    out/story/story_band.png

## 크기만 바꾸면 안 되는 이유

쿠폰은 148×68mm(2.2:1), 밴드는 251×20mm(12.6:1)다. 9:16 판에 그냥 넣으면
**위아래가 검은 띠로 남는다.** 실물을 화면에 얹은 게 아니라 스크린샷을
붙인 것으로 보인다.

여기서는 인쇄물을 **물건처럼** 놓는다 — 살짝 기울이고, 그림자를 깔고,
여러 장을 겹친다. 그래야 "우리가 이런 걸 만들었다" 가 아니라
"이게 실제로 있다" 로 읽힌다.

## 무엇을 파는 판인가

    쿠폰   팔로우 → 웰컴드링크 1+1. **팔로우가 목적이다**
    밴드   밴드 하나로 네 곳. 애프터 혜택이 목적이다

둘 다 행사 티켓을 파는 판이 아니다. 티켓 판은 이미 릴스가 하고 있고,
같은 말을 또 하면 스토리를 넘긴다.

python story_print.py
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'story')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
SAFE_TOP = int(H * 0.155)                 # 프로필 막대
SAFE_BOT = int(H * 0.770)                 # 답장 막대가 올라오는 선

INK = np.float32([0.018, 0.018, 0.022])
PAPER = np.float32([0.97, 0.97, 0.96])
CORAL = np.float32([1.00, 0.42, 0.36])
DIM = np.float32([0.52, 0.53, 0.57])


def field(seed=3):
    """검정 판에 빛 한 겹. 인쇄물이 어둠 속에 놓인 것처럼."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - W * 0.5) / (W * 0.75)) ** 2
                    + ((yy - H * 0.46) / (H * 0.34)) ** 2))[..., None] * PAPER * 0.11
    img *= (1 - 0.55 * np.clip((H * 0.12 - yy) / (H * 0.12), 0, 1))[..., None]
    img *= (1 - 0.50 * np.clip((yy - H * 0.86) / (H * 0.14), 0, 1))[..., None]
    img += np.random.default_rng(seed).standard_normal((H, W, 1)).astype(np.float32) * 0.006
    return img


def place(dst, path, cx, cy, width, angle=0.0, shadow=0.55):
    """인쇄물 한 장을 물건처럼 놓는다.

    **그림자가 없으면 붙여넣기로 보인다.** 실루엣을 흐려서 아래에 깔고
    그 위에 판을 얹는다 — 종이가 바닥에서 조금 떠 있는 것처럼 읽힌다."""
    im = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255
    h0, w0 = im.shape[:2]
    s = width / w0
    im = cv2.resize(im, (int(w0 * s), max(1, int(h0 * s))), interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    # 회전하면 모서리가 잘리므로 넉넉한 판에 올려 두고 돌린다
    pad = int(max(h, w) * 0.5)
    can = np.zeros((h + pad * 2, w + pad * 2, 3), np.float32)
    msk = np.zeros((h + pad * 2, w + pad * 2), np.float32)
    can[pad:pad + h, pad:pad + w] = im
    msk[pad:pad + h, pad:pad + w] = 1.0
    M = cv2.getRotationMatrix2D((can.shape[1] / 2, can.shape[0] / 2), angle, 1.0)
    can = cv2.warpAffine(can, M, (can.shape[1], can.shape[0]), flags=cv2.INTER_LINEAR)
    msk = cv2.warpAffine(msk, M, (msk.shape[1], msk.shape[0]), flags=cv2.INTER_LINEAR)

    x0, y0 = int(cx - can.shape[1] / 2), int(cy - can.shape[0] / 2)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + can.shape[1]), min(H, y0 + can.shape[0])
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = (slice(sy0 - y0, sy1 - y0), slice(sx0 - x0, sx1 - x0))
    dsub = (slice(sy0, sy1), slice(sx0, sx1))

    if shadow:
        sh = cv2.GaussianBlur(msk, (0, 0), max(6.0, w * 0.02))[sub][..., None]
        off = int(max(4, h * 0.05))
        d0, d1 = min(H, sy0 + off), min(H, sy1 + off)
        if d1 > d0:
            n = d1 - d0
            dst[d0:d1, sx0:sx1] *= 1 - shadow * sh[:n]
    m = msk[sub][..., None]
    dst[dsub] = dst[dsub] * (1 - m) + can[sub] * m


def head(img, kicker, lines, sub=None, top=None):
    """머리 — 눈썹 한 줄, 큰 글자, 작은 설명 한 줄."""
    y = top if top is not None else SAFE_TOP + 40
    # **눈썹을 회색으로 두면 안 읽힌다.** 검정 판 위에서 DIM(0.52)은
    # 거의 배경이다 — 흰색을 낮춰 쓰는 쪽이 훨씬 잘 읽힌다
    ks = min(26, fit(kicker, BRAND, W * 0.80, 0.34))
    paint(img, tmask(kicker, BRAND, ks, 0.34), W / 2, y, color=PAPER, a=0.62, anchor='c')
    y += 62
    for line in lines:
        fs = min(96, fit(line, KRB, W * 0.84, 0.02))
        paint(img, tmask(line, KRB, fs, 0.02), W / 2, y, color=PAPER, anchor='c')
        y += fs + 22
    if sub:
        y += 6
        paint(img, tmask(sub, KR, 40, 0.02), W / 2, y, color=PAPER, a=0.68, anchor='c')
    return y


def foot(img, cta, note):
    """발치 — 무엇을 하라는지. **스토리는 답장 막대가 올라오니 그 위에 둔다.**"""
    y = SAFE_BOT + 40
    rule(img, y - 46, W * 0.16, W * 0.84, PAPER, 0.20, 2)
    paint(img, tmask(cta, KRB, min(56, fit(cta, KRB, W * 0.82, 0.02)), 0.02),
          W / 2, y, color=CORAL, anchor='c')
    paint(img, tmask(note, KR, 34, 0.02), W / 2, y + 66, color=PAPER, a=0.62, anchor='c')
    lg = logo(38)
    gap = 20
    hm = tmask(EV.HANDLE, BRAND, 22, 0.22)
    tw = lg.shape[1] + gap + hm.shape[1]
    x = W / 2 - tw / 2
    paint(img, lg, x, y + 150, color=PAPER, a=0.70)
    paint(img, hm, x + lg.shape[1] + gap, y + 150, color=PAPER, a=0.62)


def coupon_story():
    """**앞뒤를 겹쳐 놓는다.** 한 장만 두면 종이 한 장 사진이고,
    겹치면 '물건이 여러 장 있다' 로 읽힌다."""
    img = field(3)
    y = head(img, 'WELCOME DRINK', ['팔로우만 하면'], sub='줄 서서 받는 첫 잔이 1+1')
    cy = (y + SAFE_BOT) / 2 + 20
    # 뒤에 뒷면, 앞에 앞면. 각도를 반대로 줘서 두 장인 게 보이게.
    # **가로 위치를 0.46/0.54 로 벌렸더니 앞면 왼쪽이 화면 밖으로 나갔다** —
    # 기울인 판은 폭이 늘어난다는 걸 계산에 넣어야 한다
    place(img, 'out/coupon/COUPON_BACK.png', W * 0.545, cy - 60, W * 0.70, angle=-7)
    place(img, 'out/coupon/COUPON_FRONT.png', W * 0.475, cy + 80, W * 0.74, angle=4)
    foot(img, '프로필에서 팔로우', '행사 당일 현장에서 쿠폰으로 바꿔 드립니다')
    return np.clip(img, 0, 1)


def band_story():
    """**네 장을 쌓는다.** 등급이 색과 개수로 갈리는 게 한눈에 보인다 —
    한 장만 두면 그냥 띠 하나다."""
    img = field(7)
    y = head(img, EV.BAND_HEAD + '  ·  ' + EV.BAND_HEAD2, ['밴드 하나로'],
             sub=EV.BAND_WHEN_KO)
    tiers = ['BAND_1_GUEST_FRONT', 'BAND_2_VIP_FRONT',
             'BAND_3_VVIP_FRONT', 'BAND_4_STAFF_FRONT']
    top = y + 110
    step = (SAFE_BOT - 40 - top) / len(tiers)
    for i, t in enumerate(tiers):
        place(img, f'out/band/{t}.png', W * (0.50 + (0.03 if i % 2 else -0.03)),
              top + step * (i + 0.5), W * 0.86, angle=-2.2 if i % 2 else 2.2, shadow=0.5)
    foot(img, '밴드 차고 가면 계속됩니다',
         ' · '.join(en for en, _, _, _ in EV.ALLIES if en != 'ANOTHER LOUNGE'))
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for fn, name in ((coupon_story, 'story_coupon'), (band_story, 'story_band')):
        p = os.path.join(OUT, f'{name}.png')
        Image.fromarray((fn() * 255).astype(np.uint8)).save(p, optimize=True)
        print(f'{p}  {W}×{H}')
