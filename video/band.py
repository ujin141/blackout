"""
입장 밴드(밴딩) 인쇄용 원고 — GUEST · ARTIST · STAFF 3종.

    크기   3000 × 300 px = 254 × 25 mm @300dpi (타이벡 밴드 표준)
    출력   out/band/band_{guest,artist,staff}.png

밴드는 포스터가 아닙니다. 25mm 짜리 띠에서 지켜야 하는 게 따로 있습니다.

**1. 등급을 색으로만 나누면 안 된다**
   행사는 밤이고, 클럽 조명 아래에서 색은 뒤집힙니다 — 붉은 조명에서 호박색은
   흰색으로 보입니다. 색약(남성 약 5%)도 있습니다.
   그래서 **세는 막대**를 넣었습니다. GUEST 1개 · ARTIST 2개 · STAFF 3개.
   색을 못 믿는 상황에서도 개수는 셀 수 있습니다.

**2. 색상도 밝기도 둘 다 갈라 놓는다**
   색상환에서 이웃한 색(남색·청록)으로 나누면 조명 아래에서 둘이 같아 보입니다.
   파랑(220°) · 분홍(335°) · 호박(42°) 으로 벌렸습니다.
   밝기도 세 단 — 어두움(GUEST) → 중간(ARTIST) → 밝음(STAFF).
   흑백으로 인쇄되거나 어두운 데서 봐도 구분됩니다.

**2-1. 위아래 가로선은 뺐다**
   장식 괘선이었는데 가장자리와 나란해서 재단선으로 오해를 샀습니다.
   뺀 자리에 협업 브랜드 줄이 들어갔습니다 — 장식을 정보로 바꾼 셈입니다.
   진짜 재단·블리드는 인쇄소 사양에 맞춰 그쪽에서 잡습니다.

**3. 한 번에 3분의 1도 안 보인다**
   손목에 감기니까 같은 덩어리를 두 번 반복합니다. 접착 탭이 한쪽 반복을
   덮어도 나머지 하나가 통째로 남습니다 — 반복하는 이유가 이것입니다.

**4. 위계는 넷, 그 이상은 안 된다**
   이름(AFTER SUNSET) → 형식(풀파티×솔로파티) → 날짜·시간 → 협업 브랜드.
   협업 브랜드는 **제일 작게** 둡니다. 넣어야 하는 정보지만 이름보다 커지면
   밴드가 협찬 스티커가 됩니다. 여기에 장소·가격·핸들까지 더하면 25mm 안에서
   전부 같은 크기가 되고, 같은 크기면 아무것도 안 읽힙니다.

**5. 재단 여유(±1mm)를 먹고 들어간다**
   위아래 4mm(=48px, `SAFE`)는 비웁니다. 여기 글자를 걸면 잘려 나옵니다.

**6. 베이스라인을 공유한다**
   왼쪽 이름 블록과 오른쪽 날짜 블록은 글자 크기가 다릅니다. 각각 가운데를
   맞추면 두 덩어리가 서로 다른 높이에 뜬 것처럼 보입니다.

**7. 가르는 선은 고정 좌표로 박지 않는다**
   남는 폭 한가운데에 둡니다. 박아 두면 글자 길이가 바뀔 때 한쪽에 붙습니다.

**8. 위아래 선은 캔버스 전체에 한 번에 긋는다**
   덩어리마다 그리면 이음새에서 1px 어긋난 게 띠 전체에 줄로 보입니다.

인쇄 넘길 때
    · RGB PNG 입니다. CMYK 변환은 인쇄소에 맡기세요.
    · 접착 탭(끝 약 9mm)은 겹쳐 붙는 자리라 비워 뒀습니다.
      **감으면 이 탭이 반대쪽 시작을 덮습니다** — 그래서 두 번 반복합니다.
    · 가장 가는 선이 3px(=0.25mm)입니다. 이보다 얇게 고치지 마세요 — 인쇄에서 사라집니다.
    · 일련번호가 필요하면 인쇄소 넘버링 옵션으로. 여기서 그리면 전부 같은 번호입니다.

python band.py  →  out/band/band_{guest,artist,staff}.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask_bl, fit, paint, paint_bl, vrule, box, logo, grain
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'band')
os.makedirs(OUT, exist_ok=True)

W, H = 3000, 300                       # 254 × 25 mm @300dpi
SAFE = 48                              # 재단 여유 4mm. 이 안쪽에만 그린다
TAB = int(W * 0.035)                   # 접착 탭 — 겹쳐 붙는 자리
# 덩어리 폭은 **탭을 뺀 폭**에서 나눈다. 전체 폭으로 나눈 뒤 탭을 덧칠하면
# 두 번째 덩어리의 오른쪽 글자가 잘려 나간다 — 실제로 그렇게 잘렸다.
PRINT = W - TAB
UNIT = PRINT // 2
HAIR = 3                               # 최소 획 3px = 0.25mm. 더 얇으면 인쇄에서 사라진다

# 세 줄의 베이스라인. 좌우 블록이 공유한다.
# 가로 괘선을 빼면서 생긴 자리에 협업 브랜드 줄이 들어갔다.
BL1, BL2, BL3 = 126, 180, 234

# 세 등급은 **색상환에서 멀리 떨어뜨린다.** 남색·청록처럼 이웃한 색으로 나누면
# 조명 아래에서 둘이 같아 보인다. 파랑(220°) · 분홍(335°) · 호박(42°) 로 벌렸다.
NAVY  = np.array([0.03, 0.05, 0.16], np.float32)
PINK  = np.array([0.93, 0.20, 0.50], np.float32)
AMBER = np.array([1.00, 0.72, 0.18], np.float32)
INK   = np.array([0.06, 0.03, 0.10], np.float32)
WHITE = np.array([1.00, 1.00, 1.00], np.float32)

DATE_SHORT = '08.29 SAT'               # 밴드에서 '8월 29일 토요일'은 자리를 너무 먹는다
# 붙임표 규칙: **숫자 구간은 붙인 en dash(–), 글로 쓴 시간은 띄운 em dash(—)**.
# 포스터 타임테이블도 같은 규칙이라 밴드만 다르면 눈에 걸린다.
TIME_SHORT = '19:00–24:00'

# (등급, 세는 막대 수, 배경, 글자, 강조)  — 배경 밝기를 세 단으로 벌린다
TIERS = [
    ('GUEST',  1, NAVY,  WHITE, AMBER),
    ('ARTIST', 2, PINK,  INK,   WHITE),
    ('STAFF',  3, AMBER, INK,   INK),
]


def tier_chip(u, word, n, bg, fg):
    """오른쪽 끝 등급 표시. 색을 못 믿는 상황을 위해 **세는 막대**를 같이 넣는다."""
    wm = tmask_bl(word, BRAND, 23, 0.26)
    bw, bg_gap = HAIR * 3, 11
    bars_w = n * bw + (n - 1) * bg_gap
    pad = 30
    cw = pad + bars_w + 22 + wm[0].shape[1] + pad
    x1 = UNIT - 70
    x0 = x1 - cw
    y0, y1 = BL1 - 42, BL2 + 16
    box(u, x0, y0, x1, y1, fg)                       # 칩은 글자색으로 채운다(반전)
    bx = x0 + pad
    for i in range(n):
        box(u, bx + i * (bw + bg_gap), y0 + 20, bx + i * (bw + bg_gap) + bw, y1 - 20, bg)
    paint_bl(u, wm, x1 - pad, (y0 + y1) / 2 + wm[1] * 0.5 - 2, color=bg, anchor='r')
    return x0


def draw_unit(u, bg, fg, accent, word, n):
    u[:] = bg

    # ── 왼쪽 · 정체 ───────────────────────────────────────
    x = 80
    lg = logo(82)
    # 엠블럼은 좌우가 비대칭이라 상자 가운데로 맞추면 살짝 처져 보인다. 2px 올린다.
    paint(u, lg, x, (BL1 + BL2) / 2 - 22, color=fg, a=0.95)
    x += lg.shape[1] + 46

    # STAFF 는 강조색이 글자색과 같다(밝은 바탕이라 쓸 색이 없다).
    # 그대로 두면 둘째 줄이 첫째 줄과 같은 무게로 읽히므로 알파로 단을 만든다.
    aa = 0.68 if np.allclose(accent, fg) else 0.95

    name = tmask_bl(EV.NAME, BRAND, 42, 0.10)
    paint_bl(u, name, x, BL1, color=fg)
    fmt = tmask_bl(EV.FORMAT, BRAND, 19, 0.14)
    paint_bl(u, fmt, x, BL2, color=accent, a=aa)
    left_end = x + max(name[0].shape[1], fmt[0].shape[1])

    # ── 협업 브랜드 — 제일 작게, 전폭 한 줄 ────────────────
    # 넣어야 하지만 이름·날짜보다 커지면 안 된다. 폭에 맞춰 자동으로 줄인다.
    pw = UNIT - 70 - x
    # 형식 줄(19)보다 작아야 한다. 폭이 남는다고 키우면 위계가 뒤집힌다.
    ps = min(17, fit(EV.PARTNERS_STR, BRAND, pw, 0.05))
    paint_bl(u, tmask_bl(EV.PARTNERS_STR, BRAND, ps, 0.05), x, BL3, color=fg, a=0.62)

    # ── 오른쪽 끝 · 등급 ──────────────────────────────────
    chip_x = tier_chip(u, word, n, bg, fg)

    # ── 가운데 오른쪽 · 날짜·시간 ─────────────────────────
    rx = chip_x - 44
    d1 = tmask_bl(DATE_SHORT, BRAND, 27, 0.14)
    d2 = tmask_bl(TIME_SHORT, BRAND, 19, 0.18)
    paint_bl(u, d1, rx, BL1, color=fg, anchor='r')
    paint_bl(u, d2, rx, BL2, color=accent, a=aa, anchor='r')
    right_start = rx - max(d1[0].shape[1], d2[0].shape[1])

    # 가르는 선 — 남는 폭 한가운데. 고정 좌표로 박으면 한쪽에 붙는다.
    vrule(u, (left_end + right_start) / 2, BL1 - 36, BL2 + 12, fg, 0.35, HAIR)


def build(word, n, bg, fg, accent):
    img = np.zeros((H, W, 3), np.float32)
    u = np.zeros((H, UNIT, 3), np.float32)
    draw_unit(u, bg, fg, accent, word, n)
    img[:, :UNIT] = u
    img[:, UNIT:UNIT * 2] = u
    img[:, UNIT * 2:] = bg          # 나머지는 탭까지 바탕으로

    box(img, W - TAB, 0, W, H, bg)         # 접착 탭은 바탕만
    grain(img, 0.006, 2)
    return np.clip(img, 0, 1)


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    lum = float((img @ np.float32([0.299, 0.587, 0.114])).mean())
    print(f'{p}  {W}×{H}px ≈254×25mm@300dpi  평균밝기 {lum:.2f}')


if __name__ == '__main__':
    for word, n, bg, fg, accent in TIERS:
        save(build(word, n, bg, fg, accent), f'band_{word.lower()}')
