"""
P안 — **번호표.** 솔로파티에서 실제로 쓰는 물건을 그대로 포스터로 만듭니다.

혼자 온 사람에게 번호를 주고, 번호로 서로를 찾습니다. 그 물건이 물에 떠 있으면
풀파티이고, 번호가 적혀 있으면 솔로파티입니다 — **물건 하나가 둘 다 말합니다.**

번호표로 읽히려면 넷이 다 있어야 합니다.
구멍 · 끈 · 큰 번호 · 작은 안내. 하나라도 빠지면 그냥 둥근 사각형입니다.

**번호는 두 개를 놓습니다.** 하나면 그냥 표이고, 나란히 둘이면
"이 번호와 저 번호가 만난다"가 됩니다. 이 판의 컨셉이 거기 있습니다.

python poster_tag.py  →  out/poster/tag_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, fit, paint, rule, box, grain, save, info_block
from fest_kit import reflect, specks, vignette, justify, night
from scene_kit import photoscene
from fonts import KR
import event as EV

DEEP    = (0.012, 0.030, 0.052)
SHALLOW = (0.024, 0.058, 0.090)
CARD    = np.float32([0.80, 0.83, 0.82])   # 흰 카드를 그대로 두면 밝은 픽셀이 12%
CARD2   = np.float32([0.14, 0.18, 0.20])
CORAL   = np.float32([1.00, 0.42, 0.36])
AQUA    = np.float32([0.30, 0.88, 0.96])
PAPER   = np.float32([0.97, 0.99, 1.00])
DIM     = np.float32([0.60, 0.74, 0.82])


def tag(img, cx, cy, w, h, face, ink, num, label, accent, V, tilt=0.0):
    """번호표 한 장. 구멍·끈·번호·안내가 다 있어야 번호표로 읽힌다."""
    layer = np.zeros(img.shape[:2], np.float32)
    r = int(min(w, h) * 0.14)
    cv2.rectangle(layer, (int(cx - w / 2), int(cy - h / 2)),
                  (int(cx + w / 2), int(cy + h / 2)), 1.0, -1, cv2.LINE_AA)
    # 모서리를 둥글게 — 사각형 모서리를 지우고 원으로 채운다
    for sx in (-1, 1):
        for sy in (-1, 1):
            cv2.circle(layer, (int(cx + sx * (w / 2 - r)), int(cy + sy * (h / 2 - r))),
                       r, 1.0, -1, cv2.LINE_AA)
    cv2.rectangle(layer, (int(cx - w / 2), int(cy - h / 2 + r)),
                  (int(cx + w / 2), int(cy + h / 2 - r)), 1.0, -1)
    cv2.rectangle(layer, (int(cx - w / 2 + r), int(cy - h / 2)),
                  (int(cx + w / 2 - r), int(cy + h / 2)), 1.0, -1)
    hole = (int(cx), int(cy - h / 2 + h * 0.115))
    cv2.circle(layer, hole, int(h * 0.052), 0.0, -1, cv2.LINE_AA)   # 구멍

    if tilt:                                        # 살짝 기울여 물에 뜬 느낌
        Mx = cv2.getRotationMatrix2D((cx, cy), tilt, 1.0)
        layer = cv2.warpAffine(layer, Mx, (img.shape[1], img.shape[0]))

    m = layer[..., None]
    img[:] = img * (1 - m) + face * m
    # 끈 — **구멍에 꿴 고리**로 그린다. 위로 뻗은 줄로 그렸더니 허공에서 끊겨
    # 어디에 매달린 건지 모르는 그림이 됐다. 고리는 그 자체로 닫혀 있어 안 어색하다.
    cv2.ellipse(img, (hole[0], int(hole[1] - h * 0.055)),
                (int(h * 0.042), int(h * 0.062)), 0, 0, 360,
                tuple(float(v) for v in accent), max(2, int(3 * V)), cv2.LINE_AA)

    paint(img, tmask(label, BRAND, int(17 * V), 0.34), cx, cy - h * 0.235,
          color=ink, a=0.65, anchor='c')
    # **번호 크기는 카드 높이가 아니라 폭에서 뽑는다.** 높이 기준으로 두면
    # 카드를 좁힐 때 글자가 그대로 남아 옆으로 넘친다 — 실제로 그렇게 잘렸다.
    paint(img, tmask(num, BRAND, fit(num, BRAND, w * 0.62, 0.02), 0.02),
          cx, cy + h * 0.045, color=ink, anchor='c')
    rule(img, cy + h * 0.255, cx - w * 0.30, cx + w * 0.30, accent, 0.95, max(2, int(3 * V)))
    paint(img, tmask('SOLO', BRAND, int(19 * V), 0.34), cx, cy + h * 0.345,
          color=accent, anchor='c')
    return layer


def build(W, H, story=False):
    V = W / 1080.0
    # **배경은 무늬가 아니라 장면이다.** 물결·타일만 깔면 여전히 상징이라
    # "추상적"이라는 지적이 남는다. 밤 루프탑 수영장에 사람이 있고 디제이가
    # 틀고 있는 그림을 뒤에 두면, 앞의 도형이 무슨 얘기를 하든 일단
    # 무슨 행사인지가 먼저 보인다. 뒤로 물러나야 하니 한 단 눌러 둔다.
    # **그린 장면은 자연스럽지 않다.** 선으로 그린 실루엣은 도표로 읽히고
    # 그 위에 네온을 얹으면 둘이 따로 논다. 자연스러움은 **사진의 결**에서
    # 온다 — 헤이즈의 얼룩, 물결의 불규칙은 코드로 흉내 낼수록 가짜 티가 난다.
    img = photoscene(W, H, story, wy=0.52 if story else 0.495) * 0.94

    CYm = H * (0.410 if story else 0.405)
    # **가운데를 비운다.** 배경이 인물 사진일 때 카드가 정면에 오면 얼굴·몸을
    # 정확히 가린다. 양옆으로 밀면 가운데가 열리고, 두 장이 '핀으로 꽂힌 표'
    # 처럼 읽혀서 컨셉도 안 죽는다.
    tw, th = W * 0.245, W * 0.245 * 1.42
    dx = W * 0.285

    # **두 장.** 한 장이면 그냥 표이고, 나란히 둘이면 만나는 이야기가 된다
    tag(img, W / 2 - dx, CYm + th * 0.05, tw, th, CARD, CARD2, '01', 'GUEST NO.', CORAL, V, tilt=-6)
    tag(img, W / 2 + dx, CYm - th * 0.05, tw, th, CARD2, CARD, '02', 'GUEST NO.', AQUA, V, tilt=7)

    # 둘 사이의 빛 — 만나는 자리
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W / 2) / (W * 0.105)) ** 2 + ((yy - CYm) / (H * 0.090)) ** 2))
    img += g[..., None] * np.float32([0.9, 0.95, 1.0]) * 0.20

    reflect(img, CYm + th * 0.60, int(H * 0.16), wob=6.0 * V, damp=0.30, seed=5)
    specks(img, 70, H * 0.08, H * 0.80, PAPER, 0.13, seed=51, rmax=1.7)

    M = int(W * 0.085)
    CWD = W - M * 2
    ty = H * (0.078 if story else 0.070)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.80, anchor='c')

    # 자리는 **발치에서 역산한다** — 비율로 두면 짧은 피드에서 정보와 겹친다
    # 정보가 네 줄에서 **다섯 줄**로 늘었다(입장 조건 추가). 한 줄(46V)만큼
    # 발치를 더 올려야 캔버스를 안 넘는다.
    fy = H - 404 * V
    ny = fy - 168 * V
    img *= (1 - 0.55 * np.exp(-((yy - (ny + 26 * V)) / (H * 0.070)) ** 2))[..., None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(138 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + 56 * V,
          color=AQUA, anchor='c')

    ly = fy - 52 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.90, anchor='c')

    # **바쁜 배경에서는 발치를 눌러야 글자가 산다.** 그림자를 덧대면 지저분해지고,
    # 배경을 죽이면 깨끗하다 — 이 판 전체에서 지켜 온 규칙과 같다.
    _fy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.68 * np.clip((_fy - (fy - 30 * V)) / (60 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    # 정보는 **event.INFO 형식 그대로**. 순서·표기를 판마다 바꾸지 않는다
    yb = info_block(img, M, fy + 44 * V, CWD, V, AQUA, PAPER, head_color=PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.60)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=AQUA, a=0.90)


    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 22)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'tag_{k}')
        save(im, f'tag_{k}')
