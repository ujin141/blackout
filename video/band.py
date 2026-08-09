"""
입장 밴드(밴딩) 인쇄용 원고.

    크기   3000 × 300 px = 254 × 25 mm @300dpi (타이벡 밴드 표준)
    출력   out/band/band_{guest,staff}.png

밴드는 포스터가 아닙니다. 25mm 짜리 띠에서 지켜야 하는 게 따로 있습니다.

**1. 한 번에 3분의 1도 안 보인다**
   손목에 감기니까 어느 각도에서든 행사명이 걸려야 합니다.
   같은 덩어리를 두 번 반복합니다.

**2. 위계가 셋을 넘으면 안 된다**
   이름(AFTER SUNSET) → 형식(풀파티×솔로파티) → 날짜·시간.
   여기에 장소·가격·핸들까지 넣으면 25mm 안에서 전부 같은 크기가 되고,
   같은 크기면 아무것도 안 읽힙니다. 뺄 것을 정하는 게 이 판의 설계입니다.

**3. 재단 여유(±1mm)를 먹고 들어간다**
   위아래 4mm(=48px)는 비웁니다. 여기에 글자를 걸면 잘려 나옵니다.
   `SAFE` 안에서만 그립니다.

**4. 베이스라인을 맞춘다**
   왼쪽 이름 블록과 오른쪽 날짜 블록은 글자 크기가 다릅니다.
   각각 가운데를 맞추면 두 덩어리가 서로 다른 높이에 뜬 것처럼 보입니다.
   두 줄의 베이스라인을 공유시킵니다.

**5. 스태프는 글자가 아니라 색으로 구분한다**
   밤에 멀리서 'STAFF' 를 읽을 수는 없습니다. 색을 뒤집습니다.

인쇄 넘길 때
    · RGB PNG 입니다. CMYK 변환은 인쇄소에 맡기세요.
    · 접착 탭(끝 약 9mm)은 겹쳐 붙는 자리라 비워 뒀습니다.
    · 일련번호가 필요하면 인쇄소 넘버링 옵션으로 — 여기서 그리면 전부 같은 번호입니다.

python band.py  →  out/band/band_{guest,staff}.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, vrule, box, logo, grain
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'band')
os.makedirs(OUT, exist_ok=True)

W, H = 3000, 300                       # 254 × 25 mm @300dpi
UNIT = W // 2                          # 같은 덩어리를 두 번 반복한다
SAFE = 48                              # 재단 여유 4mm. 여기 안쪽에만 그린다
TAB = int(W * 0.035)                   # 접착 탭 — 겹쳐 붙는 자리

# 두 줄의 베이스라인. 크기가 달라도 이 값을 공유해야 한 덩어리로 읽힌다
BL1, BL2 = 152, 214

NAVY  = np.array([0.03, 0.05, 0.14], np.float32)
WHITE = np.array([1.00, 1.00, 1.00], np.float32)
AMBER = np.array([1.00, 0.74, 0.22], np.float32)

DATE_SHORT = '08.29 SAT'               # 밴드에서 '8월 29일 토요일'은 자리를 너무 먹는다
TIME_SHORT = '19:00 – 24:00'


def draw_unit(u, bg, fg, accent, label):
    """덩어리 하나. u 는 (H, UNIT, 3)."""
    u[:] = bg

    # ── 왼쪽 · 정체 ───────────────────────────────────────
    x = 80
    lg = logo(104)
    paint(u, lg, x, (BL1 + BL2) / 2 - 24, color=fg, a=0.95)
    x += lg.shape[1] + 48

    name = tmask_bl(EV.NAME, BRAND, 54, 0.10)
    paint_bl(u, name, x, BL1, color=fg)
    fmt = tmask_bl(EV.FORMAT, BRAND, 23, 0.10)
    paint_bl(u, fmt, x, BL2, color=accent, a=0.95)
    left_end = x + max(name[0].shape[1], fmt[0].shape[1])

    # ── 오른쪽 · 데이터 ───────────────────────────────────
    rx = UNIT - 80
    d1 = tmask_bl(DATE_SHORT, BRAND, 34, 0.14)
    d2 = tmask_bl(label or TIME_SHORT, BRAND, 24, 0.20)
    paint_bl(u, d1, rx, BL1, color=fg, anchor='r')
    paint_bl(u, d2, rx, BL2, color=accent, a=0.95, anchor='r')
    right_start = rx - max(d1[0].shape[1], d2[0].shape[1])

    # ── 두 블록을 가르는 선. 남는 폭 한가운데에 둔다 ────────
    # 고정 좌표로 박으면 글자 길이가 바뀔 때 한쪽에 붙어 버린다.
    vrule(u, (left_end + right_start) / 2, BL1 - 40, BL2 + 14, fg, 0.35, 3)


def build(bg, fg, accent, label=''):
    img = np.zeros((H, W, 3), np.float32)
    u = np.zeros((H, UNIT, 3), np.float32)
    draw_unit(u, bg, fg, accent, label)
    img[:, :UNIT] = u
    img[:, UNIT:] = u

    # 위아래 선은 캔버스 전체에 한 번에 긋는다 — 덩어리마다 그리면
    # 이음새에서 1px 어긋난 게 띠 전체에 줄로 보인다.
    rule(img, SAFE - 14, 0, W, accent, 0.55, 3)
    rule(img, H - SAFE + 11, 0, W, accent, 0.55, 3)

    box(img, W - TAB, 0, W, H, bg)         # 접착 탭은 바탕만
    grain(img, 0.006, 2)
    return np.clip(img, 0, 1)


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(f'{p}  {W}×{H}px  ≈254×25mm @300dpi')


if __name__ == '__main__':
    save(build(NAVY, WHITE, AMBER), 'band_guest')
    save(build(AMBER, NAVY, NAVY, label='STAFF'), 'band_staff')
