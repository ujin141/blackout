"""게스트 등록 판 — **직원이 현장에서 쓰는 물건이다.**

    guest_phone.png  1080×1920  직원 폰에 띄워 손님한테 보여준다
    guest_print.png  2480×3508  A4 300dpi. 입구·부스에 붙인다
    guest_card.png   1050×600   명함 크기. 손에 들고 다닌다

**흰 판에 검은 글자다.** 브랜드는 흑백이라 톤은 맞고, 그보다 현장에서
이게 제일 잘 읽힌다 — 어두운 클럽에서 검은 판을 폰으로 띄우면 화면이
반사돼서 QR 이 안 잡힌다. 흰 판은 폰 밝기가 그대로 조명이 된다.

**QR 이 판의 절반을 먹는다.** 안내 문구를 늘리는 것보다 QR 이 큰 게
현장에서 훨씬 빠르다 — 팔 뻗어 보여 주는 거리(50cm)에서도 한 번에 잡힌다.

⚠ 인쇄판의 QR 은 A4 에서 약 9cm 각이다. 축소 복사하면 2cm 아래로 내려가지
않게 확인할 것.

python guest.py  →  out/guest/
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, rule, logo
from fonts import KR, KRB
import qr
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'guest')
os.makedirs(OUT, exist_ok=True)

PAPER = np.float32([1.00, 1.00, 1.00])
INK = np.float32([0.045, 0.045, 0.052])
DIM = np.float32([0.46, 0.46, 0.50])

_QR = None


def code(px):
    global _QR
    if _QR is None:
        _QR = qr.build(EV.FORM_GUEST_URL, 1400, [0.02, 0.02, 0.03], [1.0, 1.0, 1.0])
    return np.asarray(_QR.convert('RGB').resize((px, px), Image.NEAREST)
                      ).astype(np.float32) / 255


def build(W, H, qf=0.56, card=False):
    """`qf` 는 QR 이 먹는 판 폭의 비율. 판이 작을수록 QR 비중을 키운다."""
    V = H / 1920
    img = np.repeat(np.repeat(PAPER[None, None, :], H, 0), W, 1).copy()
    cx = W / 2

    if card:
        # 명함은 가로다 — 왼쪽 글자, 오른쪽 QR
        q = code(int(H * 0.84))
        qx = W - q.shape[1] - int(H * 0.08)
        img[(H - q.shape[0]) // 2:(H - q.shape[0]) // 2 + q.shape[0],
            qx:qx + q.shape[1]] = q
        x = int(H * 0.11)
        # **왼쪽 글자는 QR 자리를 넘으면 안 된다.** 눈대중으로 크기를 박으면
        # 행사 이름이 길어질 때마다 QR 을 덮는다 — 남은 폭에서 역산한다
        lw = qx - x - int(H * 0.07)
        lg = logo(int(H * 0.15))
        paint(img, lg, x, H * 0.22, color=INK, a=0.95)
        for t, f, sz, tr, col, yy in (
                ('GUEST LIST', BRAND, 0.086, 0.28, INK, 0.46),
                ('찍고 이름 적어주세요', KRB, 0.070, 0.02, INK, 0.65),
                (f'{EV.NAME}  ·  {EV.DATE_EN}', BRAND, 0.036, 0.16, DIM, 0.82)):
            paint(img, tmask(t, f, min(int(H * sz), fit(t, f, lw, tr)), tr),
                  x, H * yy, color=col)
        return np.clip(img, 0, 1)

    lg = logo(int(64 * V))
    paint(img, lg, cx - lg.shape[1] / 2, 150 * V, color=INK, a=0.95)
    paint(img, tmask('GUEST LIST', BRAND, int(30 * V), 0.44), cx, 268 * V,
          color=DIM, anchor='c')
    paint(img, tmask('게스트 등록', KRB, int(112 * V), 0.0), cx, 380 * V,
          color=INK, anchor='c')
    rule(img, 480 * V, W * 0.16, W * 0.84, INK, 0.20, max(1, int(2 * V)))

    q = code(int(W * qf))
    qy = int(560 * V)
    img[qy:qy + q.shape[0], (W - q.shape[1]) // 2:(W - q.shape[1]) // 2 + q.shape[1]] = q

    y = qy + q.shape[0] + int(96 * V)
    paint(img, tmask('카메라로 찍어주세요', KRB, int(56 * V), 0.02), cx, y,
          color=INK, anchor='c')
    y += 74 * V
    paint(img, tmask('이름과 인원만 적으면 끝입니다', KR, int(32 * V), 0.02), cx, y,
          color=DIM, anchor='c')

    # 발치 — 어느 행사의 게스트인지. 이게 없으면 다른 날 판과 안 갈린다
    fy = H - 190 * V
    rule(img, fy - 56 * V, W * 0.16, W * 0.84, INK, 0.18, max(1, int(V)))
    paint(img, tmask(EV.NAME, BRAND,
                     min(int(46 * V), fit(EV.NAME, BRAND, W * 0.76, 0.10)), 0.10),
          cx, fy, color=INK, anchor='c')
    paint(img, tmask(f'{EV.DATE_EN}   {EV.VENUE}', KR,
                     min(int(26 * V), fit(f'{EV.DATE_EN}   {EV.VENUE}', KR, W * 0.80, 0.02)),
                     0.02), cx, fy + 52 * V, color=DIM, anchor='c')
    paint(img, tmask(EV.AGE, KR, int(19 * V), 0.01), cx, fy + 102 * V,
          color=DIM, a=0.85, anchor='c')
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    assert EV.FORM_GUEST_URL, 'event.py 의 FORM_GUEST_URL 이 비어 있습니다'
    import cv2
    det = cv2.QRCodeDetector()
    for name, W, H, qf, card in (('guest_phone', 1080, 1920, 0.56, False),
                                 ('guest_print', 2480, 3508, 0.44, False),
                                 ('guest_card', 1050, 600, 0.0, True)):
        a = build(W, H, qf, card)
        p = os.path.join(OUT, f'{name}.png')
        im = Image.fromarray((a * 255).astype(np.uint8))
        im.save(p, optimize=True)
        # **판에 얹은 QR 이 읽히는지 잰다.** 뽑아 놓고 현장에서 안 잡히면 늦다
        s = 700 / max(W, H)                     # 긴 변 700px — 실제 스캔보다 빡빡하다
        t = cv2.resize(np.asarray(im.convert('RGB')),
                       (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
        got, *_ = det.detectAndDecode(cv2.cvtColor(t, cv2.COLOR_RGB2BGR))
        ok = 'OK' if got == EV.FORM_GUEST_URL else '── 안 읽힘'
        print(f'{p}  {W}x{H}  {ok}')
    print(f'\n{EV.FORM_GUEST_URL}')
    print('guest_print 는 A4 300dpi. 축소 복사하면 QR 이 2cm 아래로 안 가게 확인하세요.')
