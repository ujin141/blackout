"""
**크루 인트로 V5.** `Blackout V5.mp3` 에 맞춰 만든 14.67초. 세로·가로.

    python intro_v5.py            둘 다
    python intro_v5.py vert       세로만
    python intro_v5.py 6.5        그 시점 한 프레임만 PNG 로

## 소리를 재서 만들었다

곡을 0.5초마다 훑어 RMS 와 스펙트럴 플럭스를 뽑았다. **눈대중으로 맞추면
반드시 어긋난다** — 아래 시점은 전부 잰 값이다.

    0.16초   최대 RMS. 곡이 임팩트로 시작한다 → 로고가 여기서 터진다
    5.0~5.5  플럭스 0.47→0.52 로 최고. 빌드업이다 → 빛이 모인다
    6.50초   RMS 0.108 로 최고 → **클라이맥스.** 플래시 + 로고 확정
    7.0~8.2  RMS 0.037 까지 떨어진다. 브레이크 → 검은 화면에 한 줄
    8.5~12.0 다시 올라온다 → 크루 여덟 이름
    12.5~    서서히 감소 → 슬로건과 핸들, 페이드아웃

**브레이크를 살리는 게 이 인트로의 핵심이다.** 소리가 비는 1.2초에 화면도
비워야 그다음이 산다 — 계속 뭔가 움직이면 클라이맥스가 안 남는다.

## 왜 60fps 인가

로고가 자간을 좁히며 조여드는 구간(0.6~5.0초)이 30fps 면 계단으로 보인다.
글자가 1px 씩 움직이는 걸 눈이 잡아낸다.

## 판은 브랜드 톤

검정 · 흰색 · 은색뿐이다. 크루 인트로라 색을 쓸 이유가 없다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np

import event as EV
from fest_kit import justify, rays, specks, vignette
from fonts import KR, KRB
from members import get
from poster_dj3 import chrome
from poster_dj4 import nebula, fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN
from poster_kit import BRAND, tmask, paint, rule, glow, outline, grain, logo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'intro_v5')
os.makedirs(OUT, exist_ok=True)
SONG = os.path.join(os.path.expanduser('~'), 'Desktop', 'Blackout V5.mp3')

FPS = 60
DUR = 14.673

# 잰 값. **여기를 고치면 그림이 소리와 어긋난다**
HIT = 0.16          # 최대 RMS — 로고가 터지는 자리
BUILD = 5.00        # 플럭스가 오르기 시작
PEAK = 6.50         # RMS 최고 — 클라이맥스
BRK0, BRK1 = 7.00, 8.20     # 브레이크(소리가 빈다)
NAMES0, NAMES1 = 8.40, 11.90
OUTRO = 12.30

SIZES = {'vert': (1080, 1920), 'wide': (1920, 1080)}


def ease(t):
    return t * t * (3 - 2 * t)


def seg(t, a, b):
    """구간 안에서의 0~1 진행."""
    return float(np.clip((t - a) / max(1e-6, b - a), 0, 1))


def frame(t, W, H):
    V = W / 1080.0 if H > W else H / 1080.0
    img = np.repeat(np.repeat(np.float32([0.012, 0.012, 0.016])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 배경 — 클라이맥스로 갈수록 밝아진다 ──────────────
    if t < BRK0 or t > BRK1:
        # **구름이 글자와 경쟁하면 안 된다.** 처음 세기로는 배경이 꽉 차서
        # BLACKOUT 이 구름 속에 묻혔다 — 절반으로 낮추고 클라이맥스에서만 올린다
        g = 0.14 + 0.34 * seg(t, 1.0, PEAK)
        if t > BRK1:
            g = 0.20 + 0.16 * seg(t, BRK1, OUTRO)
        g *= 1.0 - 0.72 * seg(t, OUTRO + 1.4, DUR)
        img += nebula(W, H, W * 0.5, H * 0.42, STEEL * 1.5, SILVER, seed=91,
                      spread=0.88) * g
        rays(img, W * 0.5, H * 0.40, 30, int(26 * V),
             int(min(W, H) * (0.55 + 0.25 * seg(t, 1.0, PEAK))), PAPER,
             0.010 + 0.016 * seg(t, BUILD, PEAK), phase=0.13, duty=0.26)

    cy = H * 0.44

    # ── 0~5초 · 로고와 이름이 조여든다 ───────────────────
    if t < BRK0:
        # 임팩트에서 터진다 — 그 전 0.16초는 거의 검정
        a0 = ease(seg(t, 0.02, HIT + 0.10))
        # 자간이 넓게 벌어져 있다가 천천히 좁혀진다
        tr = 0.34 - 0.28 * ease(seg(t, HIT, BUILD))
        ns = justify(EV.NAME_EN if hasattr(EV, 'NAME_EN') else 'BLACKOUT',
                     W * 0.86, tr, cap=int(150 * V))
        nm = tmask('BLACKOUT', BRAND, ns, tr)
        gl = 0.18 + 0.42 * seg(t, BUILD, PEAK)
        glow(img, nm, W / 2, cy, SILVER, gl * a0, int(30 * V), anchor='c')
        chrome(img, nm, W / 2, cy, PAPER * a0, STEEL * a0)
        paint(img, outline(nm, max(2, int(3.0 * V))), W / 2, cy, color=PAPER,
              a=0.92 * a0, anchor='c')
        # CREW 는 조금 늦게 들어온다
        a1 = ease(seg(t, 0.9, 2.0))
        paint(img, tmask('CREW', BRAND, int(34 * V), 0.60), W / 2,
              cy + ns * 0.62, color=SILVER, a=0.86 * a1, anchor='c')

        # 클라이맥스 플래시 — 0.18초만
        if PEAK <= t < PEAK + 0.18:
            img += PAPER * (1 - (t - PEAK) / 0.18) ** 1.6 * 0.55

    # ── 7.0~8.2 · 브레이크. **화면을 비운다** ────────────
    elif t < BRK1:
        a = ease(seg(t, BRK0 + 0.10, BRK0 + 0.45))
        a *= 1 - ease(seg(t, BRK1 - 0.30, BRK1))
        paint(img, tmask('SEOUL  ·  DJ CREW', BRAND, int(30 * V), 0.52),
              W / 2, cy, color=PAPER, a=0.92 * a, anchor='c')

    # ── 8.4~11.9 · 크루 여덟 이름 ────────────────────────
    elif t < OUTRO:
        lg = logo(int(58 * V))
        la = ease(seg(t, BRK1, BRK1 + 0.40))
        paint(img, lg, W / 2 - lg.shape[1] / 2, H * 0.20, color=PAPER,
              a=0.90 * la)
        names = EV.LINEUP
        span = (NAMES1 - NAMES0) / len(names)
        for i, n in enumerate(names):
            t0 = NAMES0 + span * i
            if not (t0 - 0.05 <= t < t0 + span + 0.22):
                continue
            p = seg(t, t0, t0 + span + 0.22)
            a = ease(min(1.0, p * 4.5)) * (1 - ease(max(0.0, (p - 0.72) / 0.28)))
            # 아래에서 살짝 올라오며 자간이 조여든다
            dy = (1 - ease(min(1.0, p * 3.2))) * 34 * V
            tr = 0.30 - 0.16 * ease(min(1.0, p * 3.2))
            paint(img, tmask(n, BRAND, int(96 * V), tr), W / 2, cy + dy,
                  color=PAPER, a=a, anchor='c')
        paint(img, tmask(f'DJ {len(names)}', BRAND, int(22 * V), 0.42),
              W / 2, cy + 120 * V, color=SILVER, a=0.60 * la, anchor='c')

    # ── 12.3~ · 아웃트로 ─────────────────────────────────
    else:
        a = ease(seg(t, OUTRO, OUTRO + 0.55))
        fade = 1 - ease(seg(t, DUR - 1.5, DUR))
        lg = logo(int(110 * V))
        paint(img, lg, W / 2 - lg.shape[1] / 2, cy - 175 * V, color=PAPER,
              a=0.95 * a * fade)
        nm = tmask('BLACKOUT', BRAND, int(112 * V), 0.10)
        glow(img, nm, W / 2, cy + 30 * V, SILVER, 0.26 * a * fade, int(26 * V),
             anchor='c')
        chrome(img, nm, W / 2, cy + 30 * V, PAPER * (a * fade),
               STEEL * (a * fade))
        rule(img, cy + 96 * V, W * 0.28, W * 0.72, SILVER, 0.42 * a * fade,
             max(1, int(2 * V)))
        paint(img, tmask(SLOGAN, BRAND, int(17 * V), 0.30), W / 2,
              cy + 152 * V, color=SILVER, a=0.86 * a * fade, anchor='c')
        paint(img, tmask(EV.HANDLE, BRAND, int(20 * V), 0.26), W / 2,
              cy + 210 * V, color=PAPER, a=0.88 * a * fade, anchor='c')

    specks(img, 90, 0, H, PAPER, 0.10, seed=int(t * 60) % 97 + 3, rmax=2.2)
    fringe(img, 0.0012)
    vignette(img, 0.42, 2.2)
    grain(img, 0.005, int(t * 60) % 53 + 7)
    return np.clip(img, 0, 1)


def build(key):
    W, H = SIZES[key]
    out = os.path.join(OUT, f'intro_v5_{key}.mp4')
    n = int(round(DUR * FPS))
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', SONG,
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
         '-pix_fmt', 'yuv420p', '-color_range', 'tv',
         '-c:a', 'aac', '-b:a', '256k', '-shortest',
         '-movflags', '+faststart', '-y', out], stdin=subprocess.PIPE)
    for k in range(n):
        f = frame(k / FPS, W, H)
        p.stdin.write((f * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'format=duration,size', '-of',
                        'csv=p=0', out], capture_output=True,
                       text=True).stdout.strip().split(',')
    print(f'{out}  {W}×{H} · {FPS}fps · {float(q[0]):.2f}초 · '
          f'{int(q[1])/1e6:.1f}MB')
    return out


if __name__ == '__main__':
    if not os.path.exists(SONG):
        raise SystemExit(f'곡이 없습니다: {SONG}')
    args = sys.argv[1:]
    # 숫자를 주면 그 시점 한 프레임만 — 확인용
    if args and args[0].replace('.', '', 1).isdigit():
        t = float(args[0])
        im = frame(t, *SIZES['vert'])
        p = os.path.join(OUT, f'f_{t:.2f}.png')
        cv2.imwrite(p, cv2.cvtColor((im * 255).astype(np.uint8),
                                    cv2.COLOR_RGB2BGR))
        print(p)
    else:
        for k in (args or list(SIZES)):
            if k not in SIZES:
                raise SystemExit(f'{k} 은 없습니다 — {", ".join(SIZES)}')
            build(k)
