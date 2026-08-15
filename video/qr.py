"""사전예약 폼 QR — 인쇄용 · 화면용 · 판에 얹는 조각.

    qr_print.png   2000px 흑백. 포스터 인쇄·배너·전단
    qr_light.png   1200px 밝은 판에 그대로
    qr_plate.png   1200px 어두운 판에 얹는 조각. 밝은 받침 위에 검은 코드

**오류 정정은 H(30%)로 뽑는다.** 가운데에 로고를 얹을 거라 그만큼을
잃는다 — M(15%)으로 뽑고 로고를 올리면 조명이 어두운 클럽에서 안 읽힌다.

**색을 뒤집지 않는다.** 검정 판에 맞춰 흰 코드로 뽑아 봤는데 인식기가
못 읽었다(cv2 로 확인). 반전 QR 은 규격 밖이고 폰 카메라도 자주 놓친다 —
어두운 판에는 **밝은 받침을 깔고 그 위에 보통 QR** 을 얹는 게 정답이다.

**여백(quiet zone)을 지운 QR 도 안 읽힌다.** 모듈 네 칸이 규격이고,
판에 얹을 때 그 여백까지가 QR 이다. 받침이 그 여백 몫이다.

⚠ 인쇄 크기: 스캔 거리 30cm 기준 **최소 2cm 각**. 포스터에 1cm 로 넣으면
읽히다 말다 한다.

python qr.py            → out/qr/
python qr.py "URL"      → 다른 주소로
"""
import os
import sys
import cv2
import numpy as np
import segno
from PIL import Image
from poster_kit import logo
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'qr')
os.makedirs(OUT, exist_ok=True)


def build(url, px, dark, light, badge=True):
    """QR 한 장. `dark` 가 코드 색, `light` 가 바탕 색."""
    q = segno.make(url, error='h')
    n = q.symbol_size(border=4)[0]
    scale = max(1, px // n)
    buf = np.array(list(q.matrix_iter(border=4)), dtype=np.uint8)
    a = np.repeat(np.repeat(buf, scale, 0), scale, 1)
    img = np.where(a[..., None] == 1, np.float32(dark), np.float32(light))

    if badge:
        # 가운데 로고. **H 로 뽑아도 덮을 수 있는 건 코드의 1/9 까지다** —
        # 그 이상 가리면 정정이 안 따라온다
        side = int(img.shape[0] * 0.20)
        cy = cx = img.shape[0] // 2
        h = side // 2
        img[cy - h:cy + h, cx - h:cx + h] = light
        lg = logo(int(side * 0.62))
        lh, lw = lg.shape[:2]
        y0, x0 = cy - lh // 2, cx - lw // 2
        m = (lg.astype(np.float32) / 255)[..., None]
        img[y0:y0 + lh, x0:x0 + lw] = img[y0:y0 + lh, x0:x0 + lw] * (1 - m) + np.float32(dark) * m
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else EV.FORM_URL
    assert url, 'event.py 의 FORM_URL 이 비어 있습니다'
    K, W = [0.02, 0.02, 0.03], [1.0, 1.0, 1.0]
    PLATE = [0.965, 0.975, 0.985]           # 어두운 판 위에서 눈이 안 부신 흰색
    made = []
    for name, px, d, l in (('qr_print', 2000, K, W),
                           ('qr_light', 1200, K, W),
                           ('qr_plate', 1200, K, PLATE)):
        p = os.path.join(OUT, f'{name}.png')
        im = build(url, px, d, l)
        im.save(p, optimize=True)
        made.append((name, p, im))

    # **뽑았다고 읽히는 게 아니다.** 작게 인쇄된 상황까지 흉내 내서 재 본다
    det = cv2.QRCodeDetector()
    for name, p, im in made:
        a = cv2.resize(np.asarray(im.convert('RGB')), (400, 400),
                       interpolation=cv2.INTER_AREA)
        got, *_ = det.detectAndDecode(cv2.cvtColor(a, cv2.COLOR_RGB2BGR))
        assert got == url, f'{name} 이 안 읽힙니다'
        print(f'{p}  {im.size[0]}x{im.size[1]}  ✓ 읽힘')
    print(f'\n{url}')
    print('인쇄는 최소 2cm 각. 그보다 작으면 30cm 거리에서 안 읽힙니다.')
