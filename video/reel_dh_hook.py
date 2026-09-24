"""
**AFTER MOON 릴스 · 후크판.** 조회수를 노린 한 편. 딥하우즈 촬영본.

    python reel_dh_hook.py   →  out/moon/D4_후크.mp4 (9초 · 무음) · DC4.jpg (커버)

## 왜 앞 세 편과 다르게 짜는가

앞 세 편은 정보를 정리해서 보여 준다. 이건 **멈추게** 하는 판이다.
릴스 조회수는 셋이 정한다 — 첫 1초에 멈추는가, 끝까지 보는가, 다시 도는가.

    첫 1초     로고 없이 후크부터. "내일 밤 10시" 가 0.1초에 박힌다
    0.4초 컷   16컷. 손·불빛·술·얼굴이 쉴 새 없이 바뀐다. 컷마다 살짝 튄다
    9초        12초보다 짧다. 완주율이 오른다
    끝판 없음   마지막 컷이 첫 컷과 같은 클립이라 돌아갈 때 안 끊긴다
    글자 하나   한 컷에 한 마디. 읽기 전에 넘어가면 다시 본다

곡은 안 넣는다. 인스타에서 **뜨는 음원**을 얹어야 추천에 탄다.
"""
import os

import cv2
import numpy as np
from PIL import Image

from fonts import KR, KRB
from poster_hook import silver_text
from poster_moon import BRAND_FONT, DATE, OUT, TITLE
from reel_dh import LEFT_F, LEFT_M, clip, frame
from reel_moon import DIM, FPS, H, INK, M, U, W, darken, fade, finish, font, plate, put, step, text_rgba
from reel_moon2 import encode_silent, logo
from render import out_expo

DUR = 9.0
NF = int(DUR * FPS)
CUT = 0.4

# (컷, 시작). 손 → 불빛 → 술 → 얼굴 순으로 섞는다. 마지막은 첫 컷과 같은 클립
SHOTS = [(1426, 20.0), (1414, 6.0), (1415, 4.0), (1422, 3.0), (1421, 3.0), (1436, 10.0),
         (1420, 8.0), (1423, 3.0), (1427, 5.0), (1408, 4.0), (1428, 10.0), (1438, 4.0),
         (1419, 6.0), (1424, 6.0), (1433, 8.0), (1429, 30.0), (1407, 30.0), (1410, 3.0),
         (1416, 20.0), (1431, 6.0), (1413, 12.0), (1437, 8.0), (1426, 20.4)]

# (시작, 끝, 큰 글, 작은 글)
WORDS = [(0.0, 1.2, '내일 밤 10시', '9.26 토 · 추석 마지막 밤'),
         (1.2, 2.0, '압구정', '딥하우즈'),
         (2.0, 2.8, '9,900원', '입장'),
         (2.8, 3.4, '웰컴샷', '한 잔 포함'),
         (3.4, 4.0, 'DJ 5명', '테크하우스 · 베이스하우스 · 테크노'),
         (4.0, 4.8, '새벽 2시까지', '22:00 — 02:10'),
         (4.8, 6.0, f'여 {LEFT_F} · 남 {LEFT_M}', '자리 남았어요'),
         (6.0, 7.0, '혼자 와도 됨', '1인 예매 환영'),
         (7.0, 9.0, 'AFTER MOON', '예매 → 프로필 링크')]


def main():
    seq = []
    for n, t0 in SHOTS:
        seq.append(clip(n, t0, CUT + 0.1))
    big = {}
    for _, _, a, b in WORDS:
        if a.isascii():
            big[a] = plate(a, step(5), 0.14)
        else:
            big[a] = silver_text(a, font(KRB, 150 if len(a) <= 5 else 120), 0.0)
    small = {b: text_rgba(b, KR, step(1), DIM) for _, _, _, b in WORDS}
    cover = None

    def frames():
        nonlocal cover
        for i in range(NF):
            t = i / FPS
            ci = min(len(seq) - 1, int(t / CUT))
            k = (t - ci * CUT) / CUT
            files = seq[ci]
            fi = min(len(files) - 1, int((t - ci * CUT) * FPS))
            # 컷이 넘어갈 때 살짝 크게 들어와서 줄어든다. 박에 맞춘 느낌
            img = frame(files[fi], 1.10 - 0.10 * out_expo(min(1, k * 2)))
            img *= 1.0 + 0.18 * max(0, 1 - k * 4)
            # 간판·패널 컷은 밝아서 글자가 묻힌다. 그 컷만 더 누른다
            darken(img, int(H * 0.34), int(H * 0.68), 0.85 if SHOTS[ci][0] in (1415, 1408, 1424, 1433) else 0.6)
            for t0, t1, a, b in WORDS:
                if t0 <= t < t1:
                    kk = fade(t, t0, 0.18)
                    s = 1.22 - 0.22 * out_expo(kk)
                    r = cv2.resize(big[a], None, fx=s, fy=s)
                    put(img, r, (W - r.shape[1]) / 2, H * 0.50 - r.shape[0] / 2, kk)
                    sm = small[b]
                    put(img, sm, (W - sm.shape[1]) / 2, H * 0.50 + r.shape[0] / 2 + U * 2, fade(t, t0 + 0.1, 0.2))
            if t >= 7.0:
                logo(img, M, H * 0.20, 0.30, fade(t, 7.0, 0.3))
                d = plate(DATE, step(3), 0.06)
                put(img, d, (W - d.shape[1]) / 2, H * 0.62, fade(t, 7.2, 0.3))
            out = finish(img)
            if i == 4:
                cover = out
            yield out

    encode_silent('D4_후크', frames())
    Image.fromarray(cover).save(os.path.join(OUT, 'DC4.jpg'), quality=94)
    print('커버: DC4.jpg')


if __name__ == '__main__':
    main()
