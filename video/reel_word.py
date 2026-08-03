"""
피드 오른쪽 칸(영문 키워드)을 릴스로 만든다 — DJ마다 결이 다르게.

    DEMIC  SEOUL     festival  큰 빌드와 드롭, 빛기둥
    V      TECHNO    techno    가로 슬랩, 흑백 반전 스트로브
    LYNN   BOUNCE    bounce    킥마다 튀는 글자와 퍼지는 링
    AROS   HARD      hard      강한 셰이크와 색수차, 사선 바
    TS     CITY POP  citypop   드롭 없음. 느린 수평 드리프트

커버는 feed_row.py 가 만든 {key}_3.png 를 그대로 쓴다 (그리드에서 이어지게).

python reel_word.py          전부
python reel_word.py v        하나만
"""
import os
import subprocess
import sys
import numpy as np
import cv2

from render import (W, H, FPS, BRAND, MARK_A, text_mask, blit,
                    vignette, grain, chroma, shake, zoom, out_expo, clamp01)
from audio_reel import STYLES
from fonts import KRB

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'reel')
os.makedirs(OUT, exist_ok=True)

SAFE_T, SAFE_B = 300, 1560          # 릴스 UI가 덮는 위·아래

REELS = [
    dict(key='demic', word='SEOUL',    style='festival', name='DEMIC',
         sub='축제부터 호텔 풀파티까지'),
    dict(key='v',     word='TECHNO',   style='techno',   name='V',
         sub='남녀불문 장르불문'),
    dict(key='lynn',  word='BOUNCE',   style='bounce',   name='LYNN',
         sub='한 세트에 장르 여섯 개'),
    dict(key='aros',  word='HARD',     style='hard',     name='AROS',
         sub='받은 만큼 돌려주는 에너지'),
    dict(key='ts',    word='CITY POP', style='citypop',  name='TS',
         sub='오픈덱에서 시작한 사람'),
]

_BW, _BH = W // 2, H // 2


def layer():
    return np.zeros((_BH, _BW), np.float32)


def push(dst, lay, a, blur=0.0):
    if blur > 0:
        lay = cv2.GaussianBlur(lay, (0, 0), blur)
    dst += cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def beams(dst, a, n=3, spread=170, seed=0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        L = layer()
        x = (0.5 + (i - (n - 1) / 2) * 0.28) * _BW + rng.integers(-40, 40)
        pts = np.array([[x, -30],
                        [x - spread / 4 + rng.integers(-30, 30), _BH],
                        [x + spread / 4 + rng.integers(-30, 30), _BH]], np.int32)
        cv2.fillPoly(L, [pts], 1.0)
        L *= (np.linspace(1, 0, _BH, dtype=np.float32) ** 1.4)[:, None]
        push(dst, L, a, 14)


def glow(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.2
    dst += cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def slabs(dst, t, a, n=7):
    """가로 슬랩 — 테크노"""
    L = layer()
    rng = np.random.default_rng(int(t * 4) % 9999)
    for _ in range(n):
        y = int(rng.random() * _BH)
        h = int(3 + rng.random() * 16)
        L[max(0, y):min(_BH, y + h), :] = 0.5 + rng.random() * 0.5
    push(dst, L, a, 0.8)


def rings(dst, k, a, cy=None):
    """킥마다 퍼지는 원 — 바운스"""
    if a <= 0.004:
        return
    L = layer()
    cy = (cy if cy is not None else H * 0.46) / 2
    for i in range(3):
        p = min(1.0, (1 - k) + i * 0.22)
        r = int(60 + p * 620)
        th = max(1, int(5 * (1 - p)))
        if th <= 0:
            continue
        cv2.circle(L, (int(_BW / 2), int(cy)), r, float(1 - p), th, cv2.LINE_AA)
    push(dst, L, a, 1.4)


def diagonals(dst, t, a, n=10):
    """사선 바 — 하드"""
    L = layer()
    off = int((t * 260) % 120)
    for i in range(-2, n + 2):
        x = i * 120 - off
        cv2.line(L, (x, 0), (x + _BH, _BH), 0.7, 3, cv2.LINE_AA)
    push(dst, L, a, 1.2)


def hlines(dst, t, a, n=9):
    """느리게 흐르는 수평선 — 시티팝"""
    L = layer()
    for i in range(n):
        y = int(((i / n) * _BH + t * 12) % _BH)
        cv2.line(L, (0, y), (_BW, y), 0.6, 1, cv2.LINE_AA)
    push(dst, L, a, 1.6)


def frame_of(spec, t, fi, bpm, bars):
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * bars
    style = spec['style']
    DROP = (bars // 2) * bar if style != 'citypop' else dur * 2   # 시티팝은 드롭 없음

    # 킥 위치 (오디오와 같은 격자)
    if style == 'citypop':
        ks = [b * bar + x * beat for b in range(bars) for x in (0, 2)]
    else:
        ks = [b * bar + x * beat for b in range(bars) for x in range(4)]
    past = [k for k in ks if k <= t + 1e-4]
    since = (t - past[-1]) if past else 9.0
    k = float(np.exp(-since * (9.0 if style == 'citypop' else 14.0)))

    img = np.zeros((H, W, 3), np.float32)
    prog = clamp01(t / max(DROP, 1e-6))
    after = max(0.0, t - DROP)
    on = t >= DROP
    flash = 0.0; ab = 0.0; sx = sy = 0.0; cam = 1.0; inv = 0.0

    # ── 스타일별 배경 ─────────────────────────────────────
    if style == 'festival':
        beams(img, 0.055 + prog * 0.05 + k * 0.05, 3, 170, 1)
        glow(img, W / 2, H * 0.40, W * 0.62, 0.05 + k * 0.06 + (0.06 if on else 0))
        cam = 1.0 + k * 0.012 + (max(0.0, 0.16 * (1 - out_expo(after / 0.5))) if on else 0)
        ab = k * 2 + (12 * max(0.0, 1 - after / 0.4) if on else 0)
    elif style == 'techno':
        slabs(img, t, 0.05 + prog * 0.05 + (0.07 if on else 0))
        glow(img, W / 2, H * 0.44, W * 0.5, 0.04 + k * 0.05)
        if on and int(t / (beat / 4)) % 2 == 0:
            inv = 1.0
        sx += np.sin(t * 200) * k * (2 + (5 if on else 0))
        ab = 2 + k * 5
    elif style == 'bounce':
        glow(img, W / 2, H * 0.46, W * 0.55, 0.05 + k * 0.08)
        rings(img, k, 0.16 + (0.12 if on else 0))
        cam = 1.0 + k * (0.02 + (0.02 if on else 0))
        ab = k * 3
    elif style == 'hard':
        diagonals(img, t, 0.035 + prog * 0.03 + (0.05 if on else 0))
        glow(img, W / 2, H * 0.44, W * 0.5, 0.04 + k * 0.07)
        sh = (3 + 10 * prog) * k + (14 * max(0.0, 1 - after / 0.4) if on else 0)
        sx += np.sin(t * 230) * sh
        sy += np.cos(t * 187) * sh
        ab = 2 + 4 * prog + (20 * max(0.0, 1 - after / 0.35) if on else 0)
    else:  # citypop
        hlines(img, t, 0.05)
        glow(img, W / 2, H * 0.42, W * 0.66, 0.055 + k * 0.03)
        cam = 1.0 + 0.02 * np.sin(t * 0.5)
        ab = 1.2

    if on:
        flash = max(flash, max(0.0, 0.85 - after * 10))

    # ── 로고 ──────────────────────────────────────────────
    blit(img, MARK_A, W / 2, SAFE_T + 40, 0.85, glow=0.3, glow_r=20, scale=0.20)

    # ── 워드 ──────────────────────────────────────────────
    if style == 'citypop':
        a = clamp01(t / 1.2)
        s = 1.0
    elif on:
        a = 1.0
        s = 0.55 + out_expo(clamp01(after / 0.45)) * 0.45
        if style == 'bounce':
            s *= 1 + k * 0.06
    else:
        a = 0.28 + prog * 0.35
        s = 0.5 + prog * 0.05

    m = text_mask(spec['word'], BRAND, target_w=880, track_em=0.08)
    blit(img, m, W / 2, H * 0.46, a, glow=0.35 + (0.3 if on else 0), glow_r=30, scale=s)

    # ── 하단 ──────────────────────────────────────────────
    show = on or style == 'citypop'
    if show:
        d = after if on else max(0.0, t - 1.4)
        aa = clamp01(d / 0.5)
        m = text_mask(spec['name'], BRAND, target_w=min(360, 90 * len(spec['name']) + 120),
                      track_em=0.2)
        blit(img, m, W / 2, H * 0.62, aa * 0.95, glow=0.28, glow_r=18)
        m2 = np.full((2, int(300 * out_expo(clamp01(d / 0.8)))), 255, np.uint8)
        blit(img, m2, W / 2, H * 0.662, aa * 0.42)
        m3 = text_mask(spec['sub'], KRB, target_w=600, track_em=0.03)
        blit(img, m3, W / 2, H * 0.712, clamp01((d - 0.2) / 0.5) * 0.82, glow=0.24, glow_r=15)

    m = text_mask('@BLACKOUTCREW_OFFICIAL', BRAND, target_w=520, track_em=0.14)
    blit(img, m, W / 2, SAFE_B - 40, 0.7, glow=0.22, glow_r=12)

    # ── 후처리 ────────────────────────────────────────────
    if cam != 1.0:
        img = zoom(img, cam)
    if sx or sy:
        img = shake(img, sx, sy)
    img = np.clip(img, 0, 1)
    if inv > 0.01:
        img = img * (1 - inv) + (1 - img) * inv
    img *= 1.0 if inv > 0.5 else vignette()
    if ab > 0.4:
        img = chroma(img, ab)
    if flash > 0.004:
        img += flash
    img += grain(fi) * 0.028
    # 끝 0.4초 암전
    tail = dur - t
    if tail < 0.4:
        img *= max(0.0, tail / 0.4)
    return np.clip(img, 0, 1)


def render(spec):
    bpm, bars = STYLES[spec['style']]
    dur = (60.0 / bpm) * 4 * bars
    nf = int(round(dur * FPS))
    raw = os.path.join(OUT, f'raw_{spec["key"]}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fi in range(nf):
        p.stdin.write((frame_of(spec, fi / FPS, fi, bpm, bars) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    wav = os.path.join(OUT, f'bgm_{spec["style"]}.wav')
    final = os.path.join(OUT, f'reel_{spec["key"]}_{spec["word"].replace(" ", "")}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '23',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '224k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {dur:.1f}s')


if __name__ == '__main__':
    keys = [k.lower() for k in sys.argv[1:]]
    for r in REELS:
        if not keys or r['key'] in keys:
            render(r)
    print('->', OUT)
