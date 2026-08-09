"""
입장 밴드(밴딩) 인쇄용 원고.

제안서에만 있고 실물이 없어서 새로 만들었습니다.

    크기   3000 × 300 px = 254 × 25 mm @300dpi (타이벡 밴드 표준에 맞춘 값)
    출력   out/band/band_{guest,staff}.png

**손목에 감으면 한 번에 3분의 1도 안 보입니다.** 그래서 내용을 한 번만 넣으면
각도에 따라 아무것도 안 읽힙니다 — 같은 덩어리를 **두 번 반복**해서
어느 방향에서 봐도 행사명과 날짜가 걸리게 했습니다.

스태프 밴드는 색을 뒤집었습니다. 밤에 멀리서도 스태프가 구분돼야 합니다 —
글자를 읽게 하는 게 아니라 색으로 구분시키는 게 목적입니다.

인쇄 넘길 때
    · 여기서 나오는 건 RGB PNG 입니다. CMYK 변환은 인쇄소에 맡기세요.
    · 접착 탭(끝에서 약 35mm)은 겹쳐 붙는 자리라 글자를 안 넣었습니다.
    · 일련번호가 필요하면 인쇄소에 넘버링 옵션을 요청하세요 — 여기서 그리면
      전부 같은 번호가 됩니다.

python band.py  →  out/band/band_{guest,staff}.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, rule, vrule, box, logo, grain
from fonts import KR
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'band')
os.makedirs(OUT, exist_ok=True)

W, H = 3000, 300                       # 254 × 25 mm @300dpi
UNIT = W // 2                          # 같은 덩어리를 두 번 반복한다
TAB = int(W * 0.035)                   # 접착 탭 — 겹쳐 붙는 자리라 비운다

NAVY  = np.array([0.03, 0.05, 0.14], np.float32)
WHITE = np.array([1.00, 1.00, 1.00], np.float32)
AMBER = np.array([1.00, 0.74, 0.22], np.float32)

# 날짜는 event.py 에서 오지만 밴드에는 짧게 — 손목에서 긴 문장은 안 읽힌다
DATE_SHORT = '08.29 SAT'
LINE2 = f'{DATE_SHORT}  ·  19:00 – 24:00  ·  ANOTHER LOUNGE'


def draw_unit(u, bg, fg, accent, label):
    """덩어리 하나를 그린다. u 는 (H, UNIT, 3)."""
    u[:] = bg
    x = 90
    lg = logo(132)
    paint(u, lg, x, H * 0.50, color=fg, a=0.95)
    x += lg.shape[1] + 54

    # 오른쪽에 STAFF 가 붙으면 그만큼 자리를 빼고 타이틀을 맞춘다.
    # 크기를 고정해 두면 STAFF 가 타이틀 위로 올라탄다 — 실제로 한 번 겹쳤다.
    lm = tmask(label, BRAND, 58, 0.20) if label else None
    reserve = (lm.shape[1] + 90) if lm is not None else 60
    avail = UNIT - x - reserve - 90

    m1 = tmask('POOL PARTY  ×  SOLO PARTY', BRAND,
               min(54, fit('POOL PARTY  ×  SOLO PARTY', BRAND, avail, 0.06)), 0.06)
    paint(u, m1, x, H * 0.36, color=fg)
    m2 = tmask(LINE2, BRAND, min(27, fit(LINE2, BRAND, avail, 0.16)), 0.16)
    paint(u, m2, x, H * 0.68, color=accent, a=0.95)

    if lm is not None:                 # 스태프 밴드만 오른쪽 끝에 표시
        vrule(u, UNIT - reserve - 40, H * 0.22, H * 0.78, fg, 0.45, 3)
        paint(u, lm, UNIT - 90, H * 0.50, color=fg, a=0.95, anchor='r')


def build(bg, fg, accent, label=''):
    img = np.zeros((H, W, 3), np.float32)
    u = np.zeros((H, UNIT, 3), np.float32)
    draw_unit(u, bg, fg, accent, label)
    img[:, :UNIT] = u
    img[:, UNIT:] = u

    # 위아래 가는 선 — 밴드가 얇아 보이지 않게 잡아 준다
    rule(img, int(H * 0.045), 0, W, accent, 0.55, 3)
    rule(img, int(H * 0.925), 0, W, accent, 0.55, 3)

    # 접착 탭 — 겹쳐 붙는 자리라 바탕만 남긴다
    box(img, W - TAB, 0, W, H, bg)

    grain(img, 0.006, 2)
    return np.clip(img, 0, 1)


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(f'{p}  {W}×{H}px  ≈254×25mm @300dpi')


if __name__ == '__main__':
    save(build(NAVY, WHITE, AMBER), 'band_guest')
    # 스태프는 색을 뒤집는다 — 밤에 멀리서 색으로 구분돼야 한다
    save(build(AMBER, NAVY, NAVY, label='STAFF'), 'band_staff')
