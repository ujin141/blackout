"""
BLACKOUT — 오프닝 2 (1080x1920, 29초)
컨셉: 터널. 소실점에서 사각 링이 밀려나오고 글자가 카메라를 스쳐 지나간다.
오프닝 1과 시각 언어를 겹치지 않게 — 빛 기둥·관객 실루엣 없음.
python opening2.py            전체 렌더
python opening2.py 20.0 21.5  구간 미리보기
"""
import os
import subprocess
import sys
import numpy as np
import cv2

from render import (W, H, FPS, BRAND, MARK_A, WORD_A, text_mask, blit,
                    vignette, grain, chroma, shake, zoom,
                    out_expo, out_cubic, clamp01)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

BPM = 140.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 17
DUR = BAR * BARS
NF = int(round(DUR * FPS))

VX, VY = W / 2, H * 0.46          # 소실점


def T(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


S2, S3, S4 = T(3, 0), T(7, 0), T(11, 0)
DROP = T(13, 0)
GAP = T(12, 3.5)

KICKS = ([T(b, x) for b in range(3, 12) for x in range(4)] +
         [T(12, x) for x in range(3)] +
         [T(b, x) for b in range(13, 18) for x in range(4)])
OFFS = [k + BEAT * 0.5 for k in KICKS]

WORDS = ['SEOUL', 'HOUSE', 'TECHNO', 'MINIMAL', 'UNDERGROUND', 'NIGHT',
         'ENERGY', 'UNITY', 'FUTURE', 'BLACKOUT']


def since(times, t):
    past = [k for k in times if k <= t + 1e-4]
    return (t - past[-1]) if past else 9.0


def env(times, t, decay=14.0):
    return float(np.exp(-since(times, t) * decay))


# ── 터널 ───────────────────────────────────────────────────
_BW, _BH = W // 2, H // 2


def tunnel(dst, phase, count=16, a=1.0, squash=1.0, rot=0.0):
    """소실점에서 밀려나오는 사각 링"""
    if a <= 0.004:
        return
    layer = np.zeros((_BH, _BW), np.float32)
    cx, cy = VX / 2, VY / 2
    for i in range(count):
        z = ((i + phase) % count) / count          # 0(멀다) → 1(가깝다)
        s = 0.02 + (z ** 3.1) * 3.4                # 원근
        w = s * _BW * 0.95
        h = w * 0.72 * squash
        fade = np.clip(z * 2.4, 0, 1) * np.clip((1 - z) * 5.5, 0, 1)
        if fade <= 0.01:
            continue
        th = max(1, int(1 + z * 4))
        box = cv2.boxPoints(((cx, cy), (w, h), rot * z * 18))
        cv2.polylines(layer, [np.int32(box)], True, float(fade), th, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 1.1)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def spokes(dst, a=1.0, n=12, spin=0.0, length=1.5):
    """소실점에서 뻗는 방사선"""
    if a <= 0.004:
        return
    layer = np.zeros((_BH, _BW), np.float32)
    cx, cy = VX / 2, VY / 2
    for i in range(n):
        ang = spin + i * 2 * np.pi / n
        x2 = cx + np.cos(ang) * _BW * length
        y2 = cy + np.sin(ang) * _BW * length
        cv2.line(layer, (int(cx), int(cy)), (int(x2), int(y2)), 1.0, 1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 2.2)
    grad = np.linspace(0, 1, _BH, dtype=np.float32)[:, None]
    layer *= 0.35 + 0.65 * np.abs(grad - VY / H)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def core(dst, a, r=1.0):
    """소실점의 광원"""
    if a <= 0.004:
        return
    yy, xx = np.mgrid[0:H:3, 0:W:3].astype(np.float32)
    d = np.sqrt((xx - VX) ** 2 + (yy - VY) ** 2) / (W * 0.42 * r)
    g = np.clip(1 - d, 0, 1) ** 3.2
    dst += cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def bars_glitch(dst, t, a):
    """가로 스캔 밴드"""
    if a <= 0.01:
        return
    rng = np.random.default_rng(int(t * 37) % 9999)
    for _ in range(4):
        y = int(rng.random() * H)
        h = int(6 + rng.random() * 26)
        dst[max(0, y):min(H, y + h)] += a * (0.4 + rng.random() * 0.6)


# ── 프레임 ─────────────────────────────────────────────────
def frame(t, fi):
    img = np.zeros((H, W, 3), np.float32)
    k = env(KICKS, t, 13.0)
    o = env(OFFS, t, 22.0)
    flash = 0.0
    ab = 0.0
    sx = sy = 0.0
    cam = 1.0
    inv = 0.0

    speed = 0.7 if t < S2 else (2.3 if t < S3 else (3.4 if t < S4 else 4.6))
    if t >= DROP:
        speed = 6.2
    phase = t * speed

    # ── 1~2마디: 어둠 + 신호 ───────────────────────────────
    if t < S2:
        d = t
        core(img, 0.10 + max(0.0, 0.5 - d * 0.9) + k * 0.05, 0.5)
        tunnel(img, phase, 16, 0.10 + clamp01(d / 3) * 0.12)
        flash = max(0.0, 0.9 - d * 26)
        if 1.4 < t < 3.3:
            a = clamp01((t - 1.4) / 0.5) * (1 - clamp01((t - 2.7) / 0.5))
            m = text_mask('SEOUL', BRAND, target_w=280, track_em=0.5)
            blit(img, m, W / 2, VY + 330, a * 0.7, glow=0.3, glow_r=14)

    # ── 3~6마디: 터널 가동 ─────────────────────────────────
    elif t < S3:
        p = clamp01((t - S2) / (BAR * 4))
        core(img, 0.14 + k * 0.16, 0.55 + k * 0.1)
        tunnel(img, phase, 16, 0.26 + k * 0.16)
        spokes(img, 0.05 + p * 0.05, 12, t * 0.12)
        cam = 1.0 + k * 0.02
        ab = k * 3
        # 글자가 스쳐 지나감
        for i in range(4):
            at = T(3 + i, 0)
            d = t - at
            if 0 <= d < BAR * 0.95:
                z = d / (BAR * 0.9)
                sc = 0.12 + z ** 2.6 * 4.2
                a = clamp01(z * 3) * (1 - clamp01((z - 0.72) / 0.28))
                m = text_mask(WORDS[i], BRAND, target_w=760, track_em=0.1)
                blit(img, m, VX, VY, a * 0.9, glow=0.3, glow_r=18, scale=sc)

    # ── 7~10마디: 밀도 상승 ────────────────────────────────
    elif t < S4:
        p = clamp01((t - S3) / (BAR * 4))
        core(img, 0.18 + k * 0.2, 0.6)
        tunnel(img, phase, 20, 0.3 + k * 0.18, rot=1.0)
        spokes(img, 0.09, 16, t * 0.2)
        cam = 1.0 + k * 0.03 + p * 0.03
        ab = 3 + k * 8
        sh = k * 5
        sx += np.sin(t * 190) * sh
        for i in range(8):
            at = T(7, 0) + i * BEAT * 2
            d = t - at
            if 0 <= d < BEAT * 1.9:
                z = d / (BEAT * 1.8)
                sc = 0.1 + z ** 2.6 * 4.6
                a = clamp01(z * 4) * (1 - clamp01((z - 0.7) / 0.3))
                m = text_mask(WORDS[(i + 4) % len(WORDS)], BRAND, target_w=820, track_em=0.1)
                blit(img, m, VX, VY, a, glow=0.35, glow_r=20, scale=sc)
        if o > 0.5:
            bars_glitch(img, t, 0.05 * o)

    # ── 11~12마디: 빌드 ────────────────────────────────────
    elif t < DROP:
        prog = clamp01((t - S4) / (DROP - S4))
        core(img, 0.2 + prog * 0.35 + k * 0.2, 0.6 + prog * 0.5)
        tunnel(img, phase * (1 + prog * 1.8), 22, 0.3 + prog * 0.25, rot=1.0 + prog * 3)
        spokes(img, 0.1 + prog * 0.2, 16 + int(prog * 16), t * (0.3 + prog))
        cam = 1.0 + prog * 0.1 + k * 0.03
        ab = 4 + 20 * prog
        sh = (3 + 20 * prog) * k
        sx += np.sin(t * 210) * sh
        sy += np.cos(t * 176) * sh
        bars_glitch(img, t, 0.05 + 0.14 * prog)
        if prog > 0.5 and int(t / (BEAT * 0.25)) % 2 == 0:
            inv = 1.0                      # 16분음마다 흑백 반전 (하드 스트로브)
        flash = max(flash, k * 0.25 * prog)
        if t >= GAP:
            img *= max(0.0, 1 - (t - GAP) / 0.22)

    # ── 13~17마디: 드롭 — 로고가 터널을 뚫고 나온다 ─────────
    else:
        d = t - DROP
        core(img, 0.26 + k * 0.3, 0.75)
        tunnel(img, phase, 24, 0.34 + k * 0.2, rot=2.0)
        spokes(img, 0.14 + k * 0.1, 24, t * 0.5)
        cam = 1.0 + max(0.0, 0.3 * (1 - out_expo(d / 0.5))) + k * 0.02
        sh = max(0.0, 1 - d / 0.5) ** 2 * 30 + k * 3
        sx += np.sin(d * 160) * sh
        sy += np.cos(d * 133) * sh
        ab = max(0.0, 26 * (1 - d / 0.4)) + k * 4
        flash = max(0.0, 1.0 - d * 12)

        # 소실점에서 튀어나오는 엠블럼
        s = 0.12 + out_expo(d / 0.45) * 0.6
        s *= (1 + k * 0.03)
        y = VY + (1 - out_expo(d / 0.45)) * -60 + 40
        blit(img, MARK_A, VX, y if d < 0.5 else 800, 1.0,
             glow=0.5 + k * 0.5, glow_r=48, scale=s if d < 0.5 else 0.72 * (1 + k * 0.03))

        dw = t - T(14, 0)
        if dw > 0:
            m = WORD_A.copy()
            cut = int(m.shape[1] * clamp01(dw / 0.4))
            m[:, cut:] = 0
            blit(img, m, W / 2, 1215, 1.0, glow=0.4 + k * 0.3, glow_r=24)
        dc = t - T(15, 0)
        if dc > 0:
            a = clamp01(dc / 0.4)
            m = text_mask('SEOUL · DJ CREW', BRAND, target_w=430, track_em=0.3)
            blit(img, m, W / 2, 1330, a * 0.85, glow=0.28, glow_r=14)
            m2 = np.full((1, int(620 * out_expo(dc / 0.7))), 255, np.uint8)
            blit(img, m2, W / 2, 1282, a * 0.4)
        ds = t - T(16, 0)
        if ds > 0:
            a = clamp01(ds / 0.4)
            for j, txt in enumerate(('WHERE THE LIGHTS FADE,', 'THE MUSIC TAKES OVER.')):
                m = text_mask(txt, BRAND, target_w=680, track_em=0.16)
                blit(img, m, W / 2, 1425 + j * 60, a * (0.75 + 0.25 * j), glow=0.24, glow_r=14)
        de = t - T(17, 2)
        if de > 0:
            flash = max(flash, max(0.0, 0.85 - de * 9))
            img *= max(0.0, 1 - clamp01((de - 0.4) / 0.4))
        if o > 0.6:
            bars_glitch(img, t, 0.05 * o)

    # ── 후처리 ────────────────────────────────────────────
    if cam != 1.0:
        img = zoom(img, cam)
    if sx or sy:
        img = shake(img, sx, sy)
    img = np.clip(img, 0, 1)
    if inv > 0.01:                       # 흑백 반전 컷
        img = img * (1 - inv) + (1 - img) * inv
    img *= 1.0 if inv > 0.5 else vignette()
    if ab > 0.4:
        img = chroma(img, ab)
    if flash > 0.004:
        img += flash
    img += grain(fi) * 0.03
    return np.clip(img, 0, 1)


def main():
    if len(sys.argv) == 3:
        a, b = float(sys.argv[1]), float(sys.argv[2])
        prev = os.path.join(OUT, 'prev2')
        os.makedirs(prev, exist_ok=True)
        for fi in range(int(a * FPS), int(b * FPS) + 1):
            cv2.imwrite(os.path.join(prev, f'f{fi:04d}.png'),
                        (frame(fi / FPS, fi)[..., ::-1] * 255).astype(np.uint8))
        print('->', prev)
        return

    raw = os.path.join(OUT, 'raw_open2.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fi in range(NF):
        p.stdin.write((frame(fi / FPS, fi) * 255).astype(np.uint8).tobytes())
        if fi % 60 == 0:
            print(f'  {fi}/{NF}  {fi / FPS:5.1f}s', flush=True)
    p.stdin.close()
    p.wait()

    final = os.path.join(OUT, 'blackout_opening2.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', os.path.join(OUT, 'bgm_open2.wav'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print('done ->', final)


if __name__ == '__main__':
    main()
