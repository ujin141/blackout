"""
**라인업 공개 릴스.** 20초 · 1080×1920 · 새 곡(`audio_lineup`).

    python reel_lineup.py

## 왜 이 각인가

지금 나간 소재는 값·혜택·희소성(short_ad · short_promo · short_sale)과
현장 영상(pool) 이다. **라인업을 정면으로 보여 준 판이 없다.**

라인업 판은 다른 소재가 못 하는 일을 한다 — **DJ 본인이 공유한다.**
크루 일곱 명의 계정이 같이 움직이는 게 이 판의 진짜 값이다. 우리가
한 번 올리는 것보다 그쪽이 훨씬 멀리 간다.

## 구성 — 곡이 정한다

120BPM, 한 마디 2초. 마디마다 한 명씩 넘긴다.

    마디 0~1  (0~4초)    타이틀. 곡은 코드와 하이햇뿐이라 조용하다
    마디 2~8  (4~18초)   DJ 일곱 명. 킥이 들어오는 마디 2 에서 첫 명이 뜬다
    마디 9    (18~20초)  날짜 · 장소 · 예약. 필터가 열리고 클랩이 붙는 자리

**전환은 킥 위에 놓는다.** 마디 경계가 곧 킥이라 컷이 박에 맞는다 —
소리와 그림이 같이 움직이면 그것만으로 완성도가 올라간다.

## 판은 다시 그린다

`out/poster/dj8_*_story.png` 는 인스타 UI 를 피해 위아래를 비운 판이다.
릴스는 그 여백이 그대로 보인다 — `poster_dj8.build(..., safe=False)` 로
**풀블리드 9:16 을 새로 그린다.** 같은 코드라 판이 어긋날 일이 없다.
"""
import os
import subprocess

import cv2
import numpy as np

import audio_lineup
import event as EV
import poster_dj8
from fest_kit import justify, night, vignette, rays, specks
from fonts import KR, KRB
from poster_dj import LINE
from poster_dj4 import fringe, nebula
from poster_kit import BRAND, tmask, paint, rule, glow, grain, logo, sign
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'lineup')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BAR = 2.0                                  # 120BPM
DUR = 20.0
SLIDE = 0.20                               # 판이 갈리는 시간
NAMES = EV.LINEUP                          # 일곱 명. 타임테이블 순서 그대로


def base(seed):
    """타이틀·아웃트로 공통 바탕. DJ 판과 같은 결이라야 한 세트로 보인다."""
    img = np.repeat(np.repeat(np.float32([0.015, 0.015, 0.020])[None, None, :],
                              H, 0), W, 1).copy()
    img += nebula(W, H, W * 0.5, H * 0.42, STEEL * 1.5, SILVER, seed=seed, spread=0.92)
    rays(img, W * 0.5, H * 0.42, 30, 26, int(H * 0.76), PAPER, 0.038, phase=0.13, duty=0.26)
    return img


def title_card():
    """첫 판. **행사 이름이 제일 크다** — 라인업은 그다음이다."""
    img = base(11)
    lg = logo(140)
    paint(img, lg, W / 2 - lg.shape[1] / 2, H * 0.30, color=PAPER, a=0.95)
    ns = justify(EV.NAME, W * 0.84, 0.06, cap=126)
    paint(img, tmask(EV.NAME, BRAND, ns, 0.06), W / 2, H * 0.44, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 22, 0.32), W / 2, H * 0.485,
          color=SILVER, a=0.80, anchor='c')
    rule(img, H * 0.525, W * 0.30, W * 0.70, SILVER, 0.45, 2)
    paint(img, tmask('LINE UP', BRAND, 58, 0.30), W / 2, H * 0.575,
          color=PAPER, anchor='c')
    paint(img, tmask(f'DJ {len(NAMES)}', BRAND, 20, 0.30), W / 2, H * 0.625,
          color=SILVER, a=0.70, anchor='c')
    specks(img, 140, 0, H, PAPER, 0.18, seed=5, rmax=2.6)
    vignette(img, 0.48, 2.0)
    grain(img, 0.006, 3)
    return np.clip(img, 0, 1)


def outro_card():
    """끝 판. **여기만 정보를 판다** — 앞은 전부 사람 보여 주는 자리다."""
    img = base(23)
    lg = logo(110)
    paint(img, lg, W / 2 - lg.shape[1] / 2, H * 0.285, color=PAPER, a=0.95)
    paint(img, tmask(EV.NAME, BRAND, 76, 0.10), W / 2, H * 0.40, color=PAPER, anchor='c')
    rule(img, H * 0.435, W * 0.24, W * 0.76, SILVER, 0.45, 2)
    y = H * 0.485
    for line in (EV.DATE_EN, EV.VENUE, EV.ADDR):
        paint(img, tmask(line, KR, 27, 0.02), W / 2, y, color=PAPER, a=0.92, anchor='c')
        y += 46
    y += 18
    paint(img, tmask(EV.STATUS_LINES[1], KRB, 32, 0.01), W / 2, y,
          color=PAPER, anchor='c')
    y += 46
    paint(img, tmask(EV.RESERVE, KRB, 27, 0.01), W / 2, y, color=SILVER,
          a=0.92, anchor='c')
    sign(img, W / 2, H * 0.70, size=17, color=PAPER, a=0.88, anchor='c')
    paint(img, tmask(SLOGAN, BRAND, 15, 0.30), W / 2, H * 0.745,
          color=SILVER, a=0.55, anchor='c')
    specks(img, 140, 0, H, PAPER, 0.18, seed=9, rmax=2.6)
    vignette(img, 0.48, 2.0)
    grain(img, 0.006, 4)
    return np.clip(img, 0, 1)


def cards():
    """판 아홉 장. 타이틀 두 마디 · DJ 일곱 · 아웃트로 한 마디."""
    out = [title_card()]
    for n in NAMES:
        print(f'  {n} …')
        out.append(poster_dj8.build(n, W, H, safe=False))
    out.append(outro_card())
    return out


def frame(t, cs):
    """시간 t 의 한 장. 마디 경계에서 아래 판이 올라온다."""
    # 0~4초 타이틀(두 마디), 4~18초 DJ 일곱, 18~20초 아웃트로
    if t < BAR * 2:
        i, local = 0, t
    elif t < BAR * 9:
        i, local = 1 + int((t - BAR * 2) // BAR), (t - BAR * 2) % BAR
    else:
        i, local = 8, t - BAR * 9
    i = min(i, len(cs) - 1)

    # 판마다 아주 천천히 밀어 넣는다 — 정지 화면이면 여덟 장 넘기기가 된다
    span = BAR * 2 if i == 0 else BAR
    z = 1.0 + 0.045 * (local / span)
    img = zoom(cs[i], z)

    if local < SLIDE and i > 0:
        p = local / SLIDE
        e = p * p * (3 - 2 * p)
        prev = zoom(cs[i - 1], 1.0 + 0.045)
        off = int(H * (1 - e))
        out = np.empty_like(img)
        out[:off] = prev[H - off:] if off else prev[:0]
        out[off:] = img[:H - off]
        img = out
        img += PAPER * (1 - e) ** 3 * 0.10          # 갈리는 순간만 아주 옅게
    return np.clip(img, 0, 1)


def zoom(card, z):
    if z <= 1.001:
        return card.copy()
    w, h = int(W / z), int(H / z)
    x, y = (W - w) // 2, (H - h) // 2
    return cv2.resize(card[y:y + h, x:x + w], (W, H), interpolation=cv2.INTER_LINEAR)


def build():
    bgm = audio_lineup.build()
    print('판 그리는 중')
    cs = cards()
    out = os.path.join(OUT, 'lineup.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', bgm,
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
         '-pix_fmt', 'yuv420p', '-color_range', 'tv',
         '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', '-y', out], stdin=subprocess.PIPE)
    for k in range(int(DUR * FPS)):
        f = frame(k / FPS, cs)
        p.stdin.write((f * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'format=size,bit_rate', '-of', 'csv=p=0', out],
                       capture_output=True, text=True).stdout.strip().split(',')
    print(f'{out}  {W}×{H} · {FPS}fps · {DUR:.0f}초 · '
          f'{int(q[0])/1e6:.1f}MB · {int(q[1])/1e6:.1f}Mbps')
    return out


if __name__ == '__main__':
    build()
