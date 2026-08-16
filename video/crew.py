"""여성 크루원 모집 — 스토리.

    python crew.py      →  out/crew/crew.png              한 장. 이게 기본
    python crew.py 4    →  out/crew/crew_1..4.png         넉 장짜리

**한 장이 기본이다.** 넉 장을 끝까지 넘겨 보는 건 이미 우리를 아는 사람이고,
모르는 사람은 첫 장에서 넘긴다. 넉 장은 팔로워가 늘고 나서 쓰세요.

문구는 맨 위 `WHO` · `ROLES` · `WHERE` · `SEND` 네 곳에 모아 뒀다.
**판 안에 값을 다시 적지 마세요** — 한 줄 바꾸려고 네 장을 뒤지게 된다.

**모객 판이 아니라 브랜드 판이라 흑백으로 간다.** 컬러 예외는 티켓을 파는
판에만 준다 — 3장에 들어가는 지난 행사 사진도 duotone 으로 눌러서 넣는다.

**넉 장을 한 덩어리로 읽히게 하는 게 이 판의 전부다.** 스토리는 넘기면서
보기 때문에 장마다 따로 놀면 네 개의 다른 글이 된다. 그래서 셋을 묶었다.

    1. 빛이 왼쪽에서 오른쪽으로 흐른다 — 1장은 왼쪽, 4장은 오른쪽이 밝다
    2. 머리에 `BLACKOUT` 과 `01 / 04` 가 같은 자리에 앉는다
    3. 글이 전부 같은 왼쪽 선에서 시작한다

**가운데 정렬을 하지 않는다.** 가운데로 두면 넉 장이 각자 다른 폭으로 떠서
넘길 때 글자가 좌우로 흔들린다. 왼쪽 선 하나에 걸어야 축이 안 흔들린다.

스토리는 위아래를 인스타 UI 가 덮는다 — 위 약 14%, 아래 약 25%.
그래서 글은 SAFE_TOP ~ SAFE_BOT 안에만 둔다. 아래쪽 STICKER 자리는
**답장 스티커를 붙이라고 비워 둔 것**이다. 거기에 글을 넣지 마세요 —
DM 창을 새로 여는 것보다 스티커에 바로 치는 게 지원이 몇 배 나옵니다.

문구는 mail/크루원모집_스토리.md 와 같이 갑니다. 한쪽만 고치지 마세요.

python crew.py  →  out/crew/crew_{1..4}.png
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import (BRAND, STOCK, WHITE, tmask, fit, paint, rule, logo,
                        duotone, grain, sign)
from fonts import KR, KRB
import event as EV

W, H = 1080, 1920
V = H / 1920
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'crew')
os.makedirs(OUT, exist_ok=True)

INK = np.float32([0.019, 0.019, 0.023])
PAPER = np.float32([0.97, 0.97, 0.96])
DIM = np.float32([0.52, 0.53, 0.57])

# ── 문구 ─────────────────────────────────────────────────
# **여기 네 줄만 고치면 넉 장이 다 따라온다.** 판 안에 값을 다시 적지 마세요.
WHO = '여성 크루원'          # DJ 만 뽑을 거면 '여성 DJ'
ROLES = 'DJ  ·  콘텐츠'      # 무슨 자리를 뽑는지. 늘리면 글자가 줄어든다
WHERE = '서울에서 활동 가능한 분'
SEND = ('DJ 면 믹스 하나,', '아니면 계정만.')

X = int(W * 0.105)          # 넉 장이 같이 쓰는 왼쪽 선
SAFE_TOP = int(H * 0.155)   # 위 — 프로필 막대
SAFE_BOT = int(H * 0.755)   # 아래 — 답장 막대가 올라오는 선
STICKER = (int(H * 0.66), int(H * 0.78))   # 답장 스티커 자리. 비워 둔다
N = 4


def field(i):
    """검정 판에 빛 한 겹. **빛의 자리가 장마다 옮겨간다** — 1장은 왼쪽,
    4장은 오른쪽. 넉 장을 이어서 보면 빛이 훑고 지나간 것처럼 읽힌다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = W * (0.16 + 0.68 * i / (N - 1))
    img += np.exp(-(((xx - cx) / (W * 0.70)) ** 2
                    + ((yy - H * 0.44) / (H * 0.36)) ** 2))[..., None] * PAPER * 0.135
    # 위아래를 눌러 인스타 UI 가 앉는 자리를 어둡게 비운다
    img *= (1 - 0.60 * np.clip((H * 0.12 - yy) / (H * 0.12), 0, 1))[..., None]
    img *= (1 - 0.55 * np.clip((yy - H * 0.86) / (H * 0.14), 0, 1))[..., None]
    return img


def head(img, i):
    """머리 — 넉 장이 같은 자리에 같은 것을 둔다. 이게 있어야 한 세트로 읽힌다."""
    y = int(H * 0.108)
    paint(img, tmask('BLACKOUT', BRAND, int(25 * V), 0.30), X, y, color=PAPER, a=0.88)
    paint(img, tmask(f'0{i + 1} / 0{N}', BRAND, int(22 * V), 0.24), W - X, y,
          color=PAPER, a=0.45, anchor='r')
    rule(img, y + int(34 * V), X, W - X, PAPER, 0.16, max(1, int(V)))


def foot(img):
    sign(img, X, int(H * 0.845), size=int(26 * V), color=PAPER, a=0.80)


def eyebrow(img, text, y):
    """머리글. **너무 흐리면 없는 것과 같다** — 처음에 회색 0.55 로 뒀다가
    폰에서 안 읽혀서 흰색 0.62 로 올렸다."""
    paint(img, tmask(text, BRAND, int(24 * V), 0.34), X, int(H * y),
          color=PAPER, a=0.62)


def ko(img, text, y, size, font=KRB, a=1.0, color=None, track=0.0, width=0.80):
    """왼쪽 선에 건다. 길면 줄여서라도 선 안에 넣는다."""
    s = min(int(size * V), fit(text, font, W * width, track))
    paint(img, tmask(text, font, s, track), X, y, color=PAPER if color is None else color, a=a)
    return y


def en(img, text, y, size, a=0.55, track=0.34, color=None):
    paint(img, tmask(text, BRAND, int(size * V), track), X, y,
          color=DIM if color is None else color, a=a)


# ── 넉 장 ────────────────────────────────────────────────

def p1(img):
    paint(img, logo(int(186 * V)), X, int(H * 0.250), color=PAPER, a=0.95, valign='t')
    eyebrow(img, 'NOW LOOKING FOR', 0.374)
    rule(img, int(H * 0.400), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, WHO, int(H * 0.472), 168)
    ko(img, '찾습니다', int(H * 0.564), 168)
    rule(img, int(H * 0.638), X, W - X, PAPER, 0.20, max(1, int(V)))
    en(img, 'SEOUL  ·  DJ CREW', int(H * 0.674), 21, a=0.55)


def p2(img):
    """**무슨 자리를 뽑는지 먼저 말한다.** '크루원' 만 적으면 뭘 하는 자린지
    몰라서 DM 을 안 한다 — 자리를 적어야 '나 저거 되는데' 가 나온다."""
    eyebrow(img, 'WHAT WE NEED', 0.268)
    rule(img, int(H * 0.294), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, ROLES, int(H * 0.372), 128)
    ko(img, '경력 안 봅니다.', int(H * 0.474), 108)
    ko(img, '지금 시작해도 됩니다.', int(H * 0.556), 108)
    rule(img, int(H * 0.618), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, WHERE, int(H * 0.658), 48, font=KR, a=0.74)


def p3(img):
    """**이 장만 사진이 들어간다.** 앞뒤가 글자뿐이라 한 장은 숨이 트여야 하고,
    "우리가 뭐 하는 크루인지" 는 말보다 사진이 빠르다."""
    ph = duotone(os.path.join(STOCK, 'crowd.jpg'), W, H,
                 INK, PAPER * 0.92, contrast=1.18, keep=0.05, focus=0.42, zoom=1.12)
    # 글이 앉는 아래쪽만 눌러서 사진을 위에 살려 둔다
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    ph *= 1 - 0.90 * np.clip((yy - H * 0.30) / (H * 0.16), 0, 1)[..., None]
    ph *= 1 - 0.55 * np.clip((H * 0.12 - yy) / (H * 0.12), 0, 1)[..., None]
    img[:] = np.clip(ph, 0, 1)
    eyebrow(img, EV.DATE_EN.rstrip('.'), 0.470)
    ko(img, '양재 루프탑에서', int(H * 0.545), 104)
    ko(img, '파티 합니다.', int(H * 0.622), 104)
    rule(img, int(H * 0.678), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, '우리가 뭐 하는 크루인지', int(H * 0.722), 46, font=KR, a=0.76)
    ko(img, '그거 보고 판단하세요.', int(H * 0.752), 46, font=KR, a=0.76)


def p4(img):
    eyebrow(img, 'HOW TO APPLY', 0.290)
    rule(img, int(H * 0.316), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, 'DM 주세요.', int(H * 0.396), 136)
    ko(img, SEND[0], int(H * 0.492), 62, font=KR, a=0.82)
    ko(img, SEND[1], int(H * 0.537), 62, font=KR, a=0.82)
    rule(img, int(H * 0.600), X, W - X, PAPER, 0.20, max(1, int(V)))
    # **여기 아이디가 이 판의 목적이다.** 발치의 서명은 지운다 —
    # 같은 아이디가 한 판에 두 번 나오면 어느 쪽을 보라는 건지 흐려진다
    paint(img, tmask(EV.HANDLE, BRAND, min(int(40 * V), fit(EV.HANDLE, BRAND, W * 0.80, 0.16)),
                     0.16), X, int(H * 0.640), color=PAPER, a=0.95)
    # STICKER 자리(0.66~0.78)는 비워 둔다 — 답장 스티커를 여기 붙인다


def solo(img):
    """**한 장짜리.** 넉 장을 넘겨 보게 만드는 건 이미 우리를 아는 사람이고,
    모르는 사람은 첫 장에서 넘긴다 — 그래서 한 장 안에 넷을 다 넣는다.

        무엇을    여성 크루원
        어떤 자리  DJ · 콘텐츠
        문턱      경력 안 봅니다
        어디로    DM

    **넷 중 하나라도 빠지면 DM 이 안 온다.** 무엇을 뽑는지만 적고 자리를
    안 적으면 '나한테 하는 말인가' 에서 멈추고, 문턱을 안 낮추면
    '나는 아직 아니지' 로 끝난다."""
    paint(img, logo(int(176 * V)), X, int(H * 0.196), color=PAPER, a=0.95, valign='t')
    eyebrow(img, 'NOW LOOKING FOR', 0.306)
    rule(img, int(H * 0.332), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, WHO, int(H * 0.402), 162)
    ko(img, '찾습니다', int(H * 0.492), 162)
    rule(img, int(H * 0.562), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, ROLES, int(H * 0.606), 66)
    ko(img, '경력 안 봅니다. 지금 시작해도 됩니다.', int(H * 0.660), 46, font=KR, a=0.82)
    ko(img, WHERE, int(H * 0.702), 46, font=KR, a=0.70)
    rule(img, int(H * 0.740), X, W - X, PAPER, 0.20, max(1, int(V)))
    ko(img, 'DM 주세요', int(H * 0.782), 62)


PAGES = (p1, p2, p3, p4)


def build(i):
    img = field(i)
    PAGES[i](img)
    head(img, i)
    if i != 3:                      # 4장은 아이디가 본문에 크게 있다
        foot(img)
    grain(img, 0.007, 23 + i)
    return np.clip(img, 0, 1)


def build_solo():
    img = field(1)                  # 빛은 가운데 왼쪽 — 로고와 헤드라인 쪽이 밝다
    solo(img)
    y = int(H * 0.108)
    paint(img, tmask('BLACKOUT', BRAND, int(25 * V), 0.30), X, y, color=PAPER, a=0.88)
    rule(img, y + int(34 * V), X, W - X, PAPER, 0.16, max(1, int(V)))
    foot(img)
    grain(img, 0.007, 29)
    return np.clip(img, 0, 1)


def _write(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((img * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)


if __name__ == '__main__':
    import sys
    if '4' not in sys.argv[1:]:
        _write(build_solo(), 'crew')
        raise SystemExit
    for i in range(N):
        p = os.path.join(OUT, f'crew_{i + 1}.png')
        Image.fromarray((build(i) * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)
    print(f'\n4jang: {STICKER[0]}~{STICKER[1]}px is left empty for the reply sticker.')
