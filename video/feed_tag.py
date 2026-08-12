"""
번호표 판(P안)을 피드 한 줄로 — 세 칸이 이어지는 판.

    │ GUEST NO. 01 │ AFTER SUNSET │ GUEST NO. 02 │

포스터 한 장을 그대로 올리면 그리드에서 한 칸만 먹고 줄이 안 채워진다.
그렇다고 1080×1350 짜리를 셋으로 자르면 360×1350 짜리 조각이 되어 비율이 깨진다.
**세 칸짜리(3240×1350)로 다시 그린다.**

이 판은 그렇게 벌리기에 제일 맞는 시안이다. 원래 컨셉이 "이 번호와 저 번호가
만난다" 인데, 포스터에서는 두 장이 나란히 붙어 있었다. 세 칸으로 벌리면
**양 끝에 번호가 하나씩 서고 가운데에서 행사 이름이 둘을 잇는다** —
그리드에서 스크롤할 때 01 이 먼저 보이고 02 가 나중에 보인다.

**칸마다 혼자서도 읽혀야 한다.** 그리드에서는 한 줄로 보이지만 피드에서는
게시물 셋이 따로 뜬다. 가운데 칸에만 정보를 몰면 나머지 둘은 빈 그림이 된다 —
칸마다 발치에 한 줄씩 준다(날짜 / 장소 / 예약).

**이음새(x=1080, 2160)에는 아무것도 올리지 않는다.** 그리드는 타일 사이가
벌어져서 경계에 걸친 획이 잘려 사라진다. 배경 사진만 지나간다.

**올리는 순서는 거꾸로다** — 3칸 → 2칸 → 1칸. 최신이 왼쪽 위라서.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이고 포스터와 같은 톤을 쓴다.

python feed_tag.py                    사진 1번
BLACKOUT_HERO=2 python feed_tag.py    사진 2번 (파일명에 _h2)
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, HEROES, tmask, tmask_bl, fit,
                        paint, paint_bl, rule, duotone, grain)
from fest_kit import justify, vignette
from fonts import KR
from poster_tag import tag, CARD, CORAL, AQUA

# 02 카드는 포스터에서 짙은 판이었다. 여기 배경은 그보다 더 어두워서 그대로 두면
# 카드가 배경에 묻혀 사라진다 — 카드는 물건이지 그림자가 아니다. 한 단 올린다.
CARD2 = np.float32([0.19, 0.24, 0.27])
import event as EV

# **가로로 아주 긴 판(3.2:1)에서는 세로 사진이 몸의 한 부분만 남는다.**
# 어느 자리를 잡아도 그렇고, 그래서 어둡게 눌렀더니 이번엔 사진이 안 보였다.
# HEROES 중 **2번만 인물이 가로로 누워 있어서** 이 비율에 그대로 들어간다 —
# 자르는 게 아니라 원래 구도가 가로다. 그래서 줄판의 기본 사진은 2번이다.
_N = max(1, int(os.environ.get('BLACKOUT_HERO', '2')))
ROW_HERO = HEROES[min(_N, len(HEROES)) - 1][0]
ROW_TAG = '' if _N == 2 else f'_h{_N}'
ROW_FOCUS = 0.28          # 셋 다 이 자리가 제일 잘 읽힌다

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T, SAFE_B = 135, 1215
SEAM = 90
V = 1.0

DEEP = np.float32([0.014, 0.032, 0.052])
LIT = np.float32([0.320, 0.500, 0.590])
PAPER = np.float32([0.98, 0.99, 1.00])
DIM = np.float32([0.60, 0.74, 0.82])


def build():
    # 사진 한 장이 세 칸을 관통한다. **가로로 긴 판이라 세로로 얇게 잘리므로**
    # 포스터의 크롭을 그대로 쓰면 몸의 한 부분만 크게 남는다. 한 단 내리고
    # 세게 눌러 결로만 쓴다 — 여기서 읽혀야 하는 건 번호표와 이름이다.
    img = duotone(ROW_HERO, W, H, DEEP, LIT, contrast=1.16, keep=0.24,
                  focus=ROW_FOCUS, zoom=1.30)
    img *= 0.64
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    # 가운데 칸을 한 번 더 눌러 둔다 — 제일 큰 글자가 앉는 자리다
    img *= 1 - 0.40 * np.exp(-((xx - W / 2) / (TW * 0.52)) ** 2)
    # 발치는 세 칸 모두 눌러 한 줄을 세운다
    img *= 1 - 0.62 * np.clip((yy - 1040) / 130, 0, 1)

    # ── 1칸 · GUEST NO. 01 ────────────────────────────────
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, 18, 0.42), TW / 2, SAFE_T + 30,
          color=DIM, a=0.82, anchor='c')
    # 카드 크기는 **3칸 아래 정보와 겹치지 않는 선**에서 정한다.
    # 0.44 로 뒀더니 02 카드 발치가 OPEN 줄을 덮었다.
    tw, th = TW * 0.395, TW * 0.395 * 1.42
    tag(img, TW / 2, 620, tw, th, CARD, CARD2, '01', 'GUEST NO.', CORAL, V, tilt=-6)

    # ── 2칸 · 이름 ────────────────────────────────────────
    x0 = TW
    ns = fit(EV.NAME, BRAND, TW - SEAM * 2, 0.10)
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), x0 + TW / 2, 462, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 25, 0.36), x0 + TW / 2, 536, color=AQUA, anchor='c')
    rule(img, 598, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.20, 2)
    paint(img, tmask(EV.LINEUP_STR, BRAND,
                     int(justify(EV.LINEUP_STR, TW - SEAM * 2, 0.13)), 0.13),
          x0 + TW / 2, 654, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.TAGLINE, KR, 27, 0.03), x0 + TW / 2, 742, color=PAPER,
          a=0.90, anchor='c')

    # ── 3칸 · GUEST NO. 02 + 정보 ─────────────────────────
    x0 = TW * 2
    tag(img, x0 + TW / 2, 500, tw, th, CARD2, CARD, '02', 'GUEST NO.', AQUA, V, tilt=7)
    y = 900
    for k, v in (('OPEN', EV.TIME_EN), ('ENTRY', EV.ENTRY),
                 ('AFTER', EV.AFTER), ('NOTICE', EV.AGE)):
        paint_bl(img, tmask_bl(k, BRAND, 15, 0.24), x0 + SEAM, y, color=AQUA, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 19,
                               0.14 if v.isascii() else 0.01),
                 x0 + SEAM + 130, y, color=PAPER, a=0.98)
        y += 39

    # ── 발치 — 칸마다 한 줄씩. **혼자 떠도 읽히게** ────────
    FY = 1120
    rule(img, FY - 42, SEAM, W - SEAM, PAPER, 0.14, 1)
    paint(img, tmask(EV.DATE_EN, BRAND, 30, 0.20), TW / 2, FY, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, 22, 0.01), TW * 1.5, FY,
          color=PAPER, a=0.94, anchor='c')
    paint(img, tmask('예약 · 프로필 링크', KR, 26, 0.02), TW * 2.5, FY,
          color=CORAL, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 17, 0.24), TW * 2.5, FY + 46,
          color=DIM, a=0.85, anchor='c')
    paint(img, tmask(EV.RULES, KR, 13, 0.01), TW * 1.5, FY + 46, color=DIM,
          a=0.62, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND,
                     min(13, fit(EV.PARTNERS_STR, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          TW / 2, FY + 46, color=DIM, a=0.62, anchor='c')

    # **비네트는 칸마다 따로 건다.** 3240 폭 전체에 걸면 타원이 양 끝 칸의
    # 바깥쪽만 세게 눌러서, 1칸 왼쪽과 3칸 오른쪽에 어두운 띠가 생긴다 —
    # 그리드에서 보면 그 두 칸만 반쯤 그늘진 판이 된다.
    for _c in range(3):
        vignette(img[:, _c * TW:(_c + 1) * TW], 0.22, 2.4)
    grain(img, 0.006, 23)
    return np.clip(img, 0, 1)


def cover(tile):
    """릴스 커버(1080×1920) — 그리드는 가운데를 4:5 로 잘라 보여준다."""
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
    full.save(os.path.join(OUT, f'tagrow_full{ROW_TAG}.png'), optimize=True)
    tiles = []
    for i in range(3):
        t = full.crop((i * TW, 0, (i + 1) * TW, TH))
        p = os.path.join(OUT, f'tagrow_{i + 1}{ROW_TAG}.png')
        t.save(p, optimize=True)
        tiles.append(t)
        print(p)
    cover(tiles[2]).save(os.path.join(OUT, f'tagrow_3_cover{ROW_TAG}.png'), optimize=True)
    print(os.path.join(OUT, f'tagrow_3_cover{ROW_TAG}.png'), '← 릴스 커버 (1080×1920)')
    print('\n올리는 순서: 3칸 → 2칸 → 1칸')
