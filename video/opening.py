"""
BLACKOUT — 오프닝 (1080x1920, 30초)
긴 빌드업 → 22.5초 드롭 → 로고가 끝까지 버팀.
python opening.py            전체 렌더 → out/blackout_opening.mp4
python opening.py 22.0 23.5  구간 미리보기 PNG
"""
import os
import subprocess
import sys
import numpy as np
import cv2

from render import (W, H, FPS, BEAT, BAR, T, BRAND, MARK_A, WORD_A,
                    text_mask, blit, haze, vignette, grain, chroma, shake, zoom,
                    out_expo, out_cubic, in_cubic, clamp01)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

BARS = 16
DUR = BAR * BARS              # 30.0초
NF = int(round(DUR * FPS))

DROP = T(13, 0)               # 22.5
S2, S3, S4 = T(5, 0), T(9, 0), T(11, 0)
GAP = T(12, 3.45)

KICKS = ([T(b, x) for b in (3, 4) for x in (0, 2.5)] +
         [T(b, x) for b in (5, 6, 7, 8, 9, 10, 11) for x in range(4)] +
         [T(b, x) for b in range(13, 17) for x in range(4)])


def since_kick(t):
    past = [k for k in KICKS if k <= t + 1e-4]
    return (t - past[-1]) if past else 9.0


def kick_env(t, decay=9.0):
    return float(np.exp(-since_kick(t) * decay))


_BW, _BH = W // 2, H // 2
_grad = np.linspace(1.0, 0.0, _BH, dtype=np.float32) ** 1.5


def beam(dst, x, angle, spread, a, y0=-60):
    if a <= 0.003:
        return
    x, spread, y0 = x / 2, spread / 2, y0 / 2
    L = _BH * 1.4
    pts = np.array([[x, y0],
                    [x - spread + np.sin(angle) * L, y0 + L],
                    [x + spread + np.sin(angle) * L, y0 + L]], np.int32)
    layer = np.zeros((_BH, _BW), np.float32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= _grad[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 22)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def ring(dst, cx, cy, r, thick, a):
    if a <= 0.004 or r <= 1:
        return
    layer = np.zeros((_BH, _BW), np.float32)
    cv2.circle(layer, (int(cx / 2), int(cy / 2)), int(r / 2), 1.0, max(1, int(thick / 2)))
    layer = cv2.GaussianBlur(layer, (0, 0), 3)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def line(dst, cx, cy, w, h, a, glow=0.0):
    if a <= 0.004 or w < 1:
        return
    blit(dst, np.full((max(1, int(h)), max(1, int(w))), 255, np.uint8),
         cx, cy, a, glow=glow, glow_r=16)


# ── 관객 실루엣 (사이트의 캔버스 아트와 같은 언어) ─────────
def _make_crowd():
    ch = 560
    m = np.zeros((ch, W), np.float32)
    rng = np.random.default_rng(21)
    # 들어올린 팔
    for _ in range(26):
        x = rng.random() * W
        top = ch * (0.10 + rng.random() * 0.35)
        lw = int(5 + rng.random() * 6)
        pts = np.array([[x, ch], [x + (rng.random() - .5) * 60, (top + ch) / 2],
                        [x + (rng.random() - .5) * 40, top]], np.int32)
        cv2.polylines(m, [pts], False, 1.0, lw)
        cv2.circle(m, (int(pts[-1][0]), int(top)), int(lw * 0.8), 1.0, -1)
    # 머리 + 어깨
    for _ in range(70):
        x = rng.random() * W * 1.1 - W * 0.05
        s = 0.6 + rng.random() * 0.8
        r = int(24 * s)
        y = int(ch * 0.62 + (rng.random() - 0.5) * ch * 0.16)
        cv2.circle(m, (int(x), y), r, 1.0, -1)
        cv2.ellipse(m, (int(x), y + int(r * 2.1)), (int(r * 2.0), int(r * 1.9)),
                    0, 180, 360, 1.0, -1)
        cv2.rectangle(m, (int(x - r * 2.0), y + int(r * 2.1)),
                      (int(x + r * 2.0), ch), 1.0, -1)
    return np.clip(m, 0, 1)


CROWD = _make_crowd()


_floor = None


def floor_glow(dst, a, top=0.60):
    """바닥에서 올라오는 빛 — 실루엣이 이 위에 얹혀야 보인다"""
    global _floor
    if a <= 0.004:
        return
    if _floor is None:
        g = np.zeros((H, 1), np.float32)
        y0 = int(H * top)
        g[y0:, 0] = np.linspace(0, 1, H - y0) ** 1.6
        _floor = cv2.GaussianBlur(g, (1, 121), 0)
    dst += _floor[..., None] * a


def crowd(dst, y_off, a):
    """검은 실루엣이라 배경에서 '빼는' 방식으로 올린다"""
    if a <= 0.01:
        return
    ch = CROWD.shape[0]
    y0 = int(H - ch + y_off)
    y0 = max(-ch + 1, min(H - 1, y0))
    sy0, sy1 = max(0, y0), min(H, y0 + ch)
    if sy1 <= sy0:
        return
    sub = CROWD[sy0 - y0:sy1 - y0][..., None]
    dst[sy0:sy1] *= (1 - sub * a)


# ── 엠블럼이 그려지는 레이더 와이프 ────────────────────────
_ang = None


def _angle_map():
    global _ang
    if _ang is None:
        h, w = MARK_A.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        a = np.arctan2(xx - w / 2, -(yy - h / 2))      # 위쪽 12시부터 시계방향
        _ang = ((a + np.pi * 2) % (np.pi * 2)) / (np.pi * 2)
    return _ang


def mark_wipe(p):
    """p: 0→1 만큼 그려진 엠블럼 마스크 + 선단 하이라이트"""
    ang = _angle_map()
    soft = np.clip((p - ang) * 26, 0, 1)
    body = MARK_A * soft
    head = MARK_A * np.clip(1 - np.abs(ang - p) * 42, 0, 1)
    return body, head


# ── 프레임 ─────────────────────────────────────────────────
def frame(t, fi):
    img = np.zeros((H, W, 3), np.float32)
    flash = 0.0
    ab = 0.0
    sx = sy = 0.0
    cam = 1.0
    k = kick_env(t, 9.0)

    # ── 배경: 빛 기둥 ─────────────────────────────────────
    if t >= S2:
        p2 = clamp01((t - S2) / (BAR * 2))
        base = 0.06 * p2
        if t >= S3:
            base = 0.11 + 0.05 * clamp01((t - S3) / (BAR * 2))
        if t >= S4:
            base = 0.17
        if t >= DROP:
            base = 0.26
        n = 4 if t < DROP else 5
        for i in range(n):
            ph = t * 0.42 + i * 1.6
            beam(img, W * (0.1 + i * (0.8 / max(n - 1, 1))) + np.sin(ph) * 110,
                 np.sin(ph * 0.65) * 0.26, 44 + i * 7,
                 base * (0.55 + 0.45 * np.sin(ph * 1.2)) * (1 + 0.55 * k))
        haze(img, W * 0.5, H * 0.45, W * 0.9,
             (0.03 + 0.05 * p2 + (0.05 if t >= DROP else 0)) * (1 + 0.6 * k))

    # ── S1 암전 ───────────────────────────────────────────
    if t < S2:
        d = t
        flash = max(0.0, 0.95 - d * 30)
        if d < 1.2:                       # 로고 잔상 한 번
            a = max(0.0, (1 - d / 1.1)) ** 2 * 0.3
            blit(img, MARK_A, W / 2, 860, a, glow=0.8, glow_r=60,
                 scale=0.95 + d * 0.06, blur=6)
        haze(img, W * 0.5, 880, W * (0.35 + 0.05 * np.sin(t * 1.1)), 0.028 + k * 0.03)
        br = 0.45 + 0.35 * np.sin(t * 1.6) + k * 0.4
        line(img, W / 2, 960, 760 * out_expo(clamp01((t - 0.5) / 2.2)), 2,
             0.35 * br, glow=0.7)
        if 4.4 < t < 7.5:
            a = clamp01((t - 4.4) / 0.8) * (1 - clamp01((t - 6.6) / 0.7))
            m = text_mask('SEOUL', BRAND, target_w=300, track_em=0.46)
            blit(img, m, W / 2, 1050, a * 0.75, glow=0.3, glow_r=16)
        cam = 1.0 + k * 0.006

    # ── S2 공간이 드러남 ──────────────────────────────────
    elif t < S3:
        p = clamp01((t - S2) / (BAR * 2))
        cam = 1.0 + p * 0.05 + k * 0.008
        floor_glow(img, (0.05 + 0.09 * p) * (1 + 0.5 * k))
        crowd(img, 260 * (1 - out_cubic(p)) + 30, 0.9 * clamp01(p * 1.6))
        line(img, W / 2, 960, 760, 2, 0.3 * (1 - clamp01((t - S2) / 1.4)), glow=0.5)
        if t < T(6, 2):
            a = 1 - clamp01((t - T(6, 0)) / 0.8)
            m = text_mask('SEOUL', BRAND, target_w=300, track_em=0.46)
            blit(img, m, W / 2, 1050, a * 0.75, glow=0.3, glow_r=16)
        d = t - T(7, 0)
        if d > 0:
            a = clamp01(d / 0.7) * (1 - clamp01((t - T(8, 2)) / 0.8))
            m = text_mask('EST. 2026', BRAND, target_w=420, track_em=0.4)
            blit(img, m, W / 2, 1050, a * 0.8, glow=0.3, glow_r=16)
        ab = k * 2

    # ── S3 엠블럼이 그려진다 ──────────────────────────────
    elif t < S4:
        d = t - S3
        p = clamp01(d / (BAR * 1.7))
        cam = 1.05 + p * 0.05 + k * 0.012
        floor_glow(img, (0.14 + 0.05 * p) * (1 + 0.5 * k))
        crowd(img, 30 - p * 40, 0.9)
        body, head = mark_wipe(p)
        blit(img, body, W / 2, 830, 1.0, glow=0.4 + k * 0.35, glow_r=40, scale=0.62)
        if p < 1:
            blit(img, head, W / 2, 830, 1.0, glow=1.1, glow_r=26, scale=0.62)
        ab = k * 4
        sh = k * 5
        sx += np.sin(t * 180) * sh
        flash = max(flash, k * 0.05)

    # ── S4 빌드업 + 카운트다운 ────────────────────────────
    elif t < DROP:
        d = t - S4
        prog = clamp01(d / (DROP - S4))
        cam = 1.10 + prog * 0.10 + k * 0.02
        floor_glow(img, (0.19 + 0.06 * prog) * (1 + 0.6 * k))
        crowd(img, -10 - prog * 30, 0.92)
        pulse = 1 + k * 0.05
        blit(img, MARK_A, W / 2, 830, 1.0, glow=0.5 + k * 0.6, glow_r=44,
             scale=0.62 * pulse)
        sh = (3 + 16 * prog) * k
        sx += np.sin(t * 200) * sh
        sy += np.cos(t * 172) * sh
        ab = 3 + 14 * prog * k
        flash = max(flash, k * (0.08 + 0.3 * prog))

        for i, txt in enumerate(('03', '02', '01')):
            at = T(12, 0.5 + i)
            dd = t - at
            if 0 <= dd < BEAT * 0.95:
                pp = out_expo(dd / 0.16)
                a = 1 - clamp01(dd / (BEAT * 0.8)) ** 2
                m = text_mask(txt, BRAND, target_w=300 + i * 60, track_em=0.1)
                blit(img, m, W / 2, 1320, a, glow=0.85, glow_r=34,
                     scale=1.25 - 0.25 * pp)
        if t >= GAP:                       # 정적
            img *= max(0.0, 1 - (t - GAP) / 0.28)

    # ── S5 드롭 + 유지 ────────────────────────────────────
    else:
        d = t - DROP
        cam = 1.0 + max(0.0, 0.42 * (1 - out_expo(d / 0.6))) + k * 0.014
        sh = max(0.0, 1 - d / 0.6) ** 2 * 36
        sx += np.sin(d * 150) * sh
        sy += np.cos(d * 128) * sh
        ab = max(0.0, 24 * (1 - d / 0.45)) + k * 3
        flash = max(0.0, 1.0 - d * 10)

        for i, off in enumerate((0.0, 0.1, 0.22)):
            rd = d - off
            if 0 < rd < 1.7:
                ring(img, W / 2, 800, 130 + rd * 1900, 13 - i * 3,
                     0.5 * (1 - rd / 1.7) ** 2)
        haze(img, W / 2, 800, W * (0.42 + d * 0.8), max(0.0, 0.5 * (1 - d / 0.9)))
        floor_glow(img, 0.26 * (1 + 0.5 * k))
        crowd(img, -40 + d * 6, 0.92)

        s = (1.0 + 1.2 * (1 - out_expo(d / 0.55))) * (1 + k * 0.03)
        blit(img, MARK_A, W / 2, 800, 1.0, glow=0.55 + k * 0.5, glow_r=50,
             scale=s * 0.72)

        dw = t - T(14, 0)
        if dw > 0:
            m = WORD_A.copy()
            cut = int(m.shape[1] * clamp01(dw / 0.45))
            m[:, cut:] = 0
            blit(img, m, W / 2, 1215, 1.0, glow=0.4 + k * 0.3, glow_r=24,
                 scale=1.0 + (1 - out_expo(dw / 0.6)) * 0.05)
        dc = t - T(15, 0)
        if dc > 0:
            a = clamp01(dc / 0.5)
            line(img, W / 2, 1282, 620 * out_expo(dc / 0.8), 1, a * 0.4)
            m = text_mask('SEOUL · DJ CREW', BRAND, target_w=430, track_em=0.3)
            blit(img, m, W / 2, 1330, a * 0.85, glow=0.28, glow_r=14)
        ds = t - T(15, 2)
        if ds > 0:
            a = clamp01(ds / 0.5)
            for j, txt in enumerate(('WHERE THE LIGHTS FADE,', 'THE MUSIC TAKES OVER.')):
                m = text_mask(txt, BRAND, target_w=680, track_em=0.16)
                blit(img, m, W / 2, 1425 + j * 60, a * (0.75 + 0.25 * j),
                     glow=0.24, glow_r=14)
        de = t - T(16, 3)
        if de > 0:
            flash = max(flash, max(0.0, 0.9 - de * 8))
            img *= max(0.0, 1 - clamp01((de - 0.5) / 0.42))

    # ── 후처리 ────────────────────────────────────────────
    if cam != 1.0:
        img = zoom(img, cam)
    if sx or sy:
        img = shake(img, sx, sy)
    img *= vignette()
    if ab > 0.4:
        img = chroma(img, ab)
    if flash > 0.004:
        img += flash
    img += grain(fi) * 0.026
    return np.clip(img, 0, 1)


def main():
    if len(sys.argv) == 3:
        a, b = float(sys.argv[1]), float(sys.argv[2])
        prev = os.path.join(OUT, 'preview_open')
        os.makedirs(prev, exist_ok=True)
        for fi in range(int(a * FPS), int(b * FPS) + 1):
            cv2.imwrite(os.path.join(prev, f'f{fi:04d}.png'),
                        (frame(fi / FPS, fi)[..., ::-1] * 255).astype(np.uint8))
        print('->', prev)
        return

    raw = os.path.join(OUT, 'raw_open.mp4')
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

    final = os.path.join(OUT, 'blackout_opening.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', os.path.join(OUT, 'bgm_open.wav'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print('done ->', final)


if __name__ == '__main__':
    main()
