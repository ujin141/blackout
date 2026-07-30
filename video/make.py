"""
BLACKOUT — 숏폼 티저 (1080x1920, 30fps, 28초)
python make.py            전체 렌더 → out/blackout_teaser.mp4
python make.py 15.0 16.2  해당 구간 프레임만 PNG로 (미리보기)
"""
import os
import subprocess
import sys
import numpy as np
import cv2

from render import (W, H, FPS, BEAT, BAR, T, BRAND, KR, KRB, MARK_A, WORD_A,
                    text_mask, blit, haze, vignette, grain, chroma, shake, zoom,
                    out_expo, out_cubic, in_cubic, out_back, clamp01, pulse)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

DUR = BAR * 15
NF = int(round(DUR * FPS))

# ── 타임라인 ───────────────────────────────────────────────
HK1, HK2 = T(1, 0), T(1, 1.5)
S2, S3, S4 = T(3, 0), T(5, 0), T(7, 0)
DROP = T(9, 0)
S6, S7 = T(13, 0), T(15, 0)

KICKS = ([T(b, x) for b in (3, 4) for x in (0, 2)] +
         [T(b, x) for b in (5, 6, 7) for x in range(4)] +
         [T(b, x) for b in range(9, 15) for x in range(4)])

WORDS = ['UNDERGROUND', 'ENERGY', 'UNITY', 'FUTURE',
         'HOUSE', 'TECHNO', 'MINIMAL', 'NIGHT']
ROLES = ['DJ', 'PRODUCER', 'VISUAL ARTIST', 'PHOTOGRAPHER', 'VIDEOGRAPHER', 'CONTENT']


def since_kick(t):
    """마지막 킥 이후 경과 시간"""
    past = [k for k in KICKS if k <= t + 1e-4]
    return (t - past[-1]) if past else 9.0


def kick_env(t, decay=9.0):
    return float(np.exp(-since_kick(t) * decay))


# 빛 기둥 (절반 해상도로 만들어 확대 — 속도)
_BW, _BH = W // 2, H // 2
_grad = np.linspace(1.0, 0.0, _BH, dtype=np.float32)[:, None] ** 1.5


def beam(dst, x, angle, spread, a, y0=-60):
    if a <= 0.003:
        return
    x, spread, y0 = x / 2, spread / 2, y0 / 2
    L = _BH * 1.35
    pts = np.array([[x, y0],
                    [x - spread + np.sin(angle) * L, y0 + L],
                    [x + spread + np.sin(angle) * L, y0 + L]], np.int32)
    layer = np.zeros((_BH, _BW), np.float32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= _grad
    layer = cv2.GaussianBlur(layer, (0, 0), 22)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def ring(dst, cx, cy, r, thick, a):
    if a <= 0.004 or r <= 1:
        return
    layer = np.zeros((_BH, _BW), np.float32)
    cv2.circle(layer, (int(cx / 2), int(cy / 2)), int(r / 2), 1.0, max(1, int(thick / 2)))
    layer = cv2.GaussianBlur(layer, (0, 0), 3)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def sweep(dst, mask, cx, cy, p, a=1.0, width=0.22):
    """글자 안쪽을 훑고 지나가는 금속 광택"""
    m = mask.astype(np.float32) / 255.0
    h, w = m.shape
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    d = xs * 0.82 + ys * 0.18
    g = np.clip(1 - np.abs(d - p) / width, 0, 1) ** 2
    blit(dst, (m * g * 255).astype(np.uint8), cx, cy, a, glow=0.5, glow_r=9)


def line(dst, cx, cy, w, h, a, glow=0.0):
    if a <= 0.004 or w < 1:
        return
    m = np.full((max(1, int(h)), max(1, int(w))), 255, np.uint8)
    blit(dst, m, cx, cy, a, glow=glow, glow_r=14)


# ── 프레임 ─────────────────────────────────────────────────
def frame(t, fi):
    img = np.zeros((H, W, 3), np.float32)
    vig_mix = 1.0
    flash = 0.0
    ab = 0.0            # 색수차
    sx = sy = 0.0       # 흔들림
    cam = 1.0

    # 배경 빛 (구간별 강도)
    if t >= S2:
        k = kick_env(t, 7.0)
        base = 0.07 if t < S3 else (0.12 if t < S4 else 0.16)
        if t >= DROP:
            base = 0.22
        for i in range(4):
            ph = t * 0.5 + i * 1.7
            beam(img, W * (0.12 + i * 0.25) + np.sin(ph) * 90,
                 np.sin(ph * 0.7) * 0.22, 46 + i * 8,
                 base * (0.6 + 0.4 * np.sin(ph * 1.3)) * (1 + 0.5 * k))
        haze(img, W * 0.5, H * (0.42 if t < DROP else 0.44), W * 0.85,
             (0.035 if t < DROP else 0.075) * (1 + 0.6 * k))

    # ── S1 훅 ──────────────────────────────────────────────
    if t < S2:
        for at, txt, tw, yy, sc in ((HK1, 'LIGHTS', 960, 900, 1.0),
                                    (HK2, 'OUT', 700, 1020, 1.0)):
            d = t - at
            if -0.02 <= d < 0.62:
                p = out_expo(d / 0.30)
                a = 1.0 if d < 0.34 else max(0.0, 1 - (d - 0.34) / 0.24)
                m = text_mask(txt, BRAND, target_w=tw, track_em=0.06)
                blit(img, m, W / 2, yy, a, glow=0.55, glow_r=34,
                     scale=sc * (1.10 - 0.10 * p))
                flash = max(flash, max(0.0, 1.0 - d * 26))
                ab = max(ab, max(0.0, 26 * (1 - d / 0.18)))
                sh = max(0.0, 1 - d / 0.30) ** 2 * 26
                sx += np.sin(d * 190) * sh
                sy += np.cos(d * 165) * sh
        # 정적 구간: 가느다란 선 + 소개
        d = t - 1.55
        if d > 0:
            p = out_expo(d / 1.5)
            line(img, W / 2, 960, 820 * p, 2, 0.5 * (1 - clamp01((t - 3.2) / 0.55)), glow=0.6)
            if t > 2.15:
                m = text_mask('SEOUL — DJ CREW', BRAND, target_w=440, track_em=0.34)
                blit(img, m, W / 2, 1040, clamp01((t - 2.15) / 0.7) *
                     (1 - clamp01((t - 3.2) / 0.55)), glow=0.3, glow_r=16)

    # ── S2 "WHERE THE LIGHTS FADE" ─────────────────────────
    elif t < S3:
        cam = 1.0 + (t - S2) / (S3 - S2) * 0.07
        rows = [('WHERE THE', T(3, 0), 780, 760),
                ('LIGHTS', T(3, 2), 900, 930),
                ('FADE', T(4, 0), 620, 1100)]
        outp = clamp01((t - T(4, 3)) / (BEAT * 1.0))
        for txt, at, tw, yy in rows:
            d = t - at
            if d < -0.02:
                continue
            p = out_expo(d / 0.55)
            a = min(1.0, d / 0.12) * (1 - in_cubic(outp))
            m = text_mask(txt, BRAND, target_w=tw, track_em=0.10)
            blit(img, m, W / 2, yy + (1 - p) * 42 - outp * 60, a,
                 glow=0.35, glow_r=26, blur=(1 - p) * 9, scale=0.97 + p * 0.03)
        ab = kick_env(t, 26) * 5

    # ── S3 "THE MUSIC TAKES OVER." ─────────────────────────
    elif t < S4:
        cam = 1.02 + (t - S3) / (S4 - S3) * 0.08
        rows = [('THE MUSIC', T(5, 0), 860, 830),
                ('TAKES OVER.', T(5, 2), 960, 1010)]
        outp = clamp01((t - T(6, 3)) / (BEAT * 1.0))
        for txt, at, tw, yy in rows:
            d = t - at
            if d < -0.02:
                continue
            p = out_expo(d / 0.6)
            a = min(1.0, d / 0.1) * (1 - in_cubic(outp))
            m = text_mask(txt, BRAND, target_w=tw, track_em=0.10)
            s = (0.97 + p * 0.03) * (1 + outp * 0.16)
            blit(img, m, W / 2, yy, a, glow=0.4, glow_r=28,
                 blur=(1 - p) * 10, scale=s)
            sp = (t - T(6, 0)) / (BEAT * 2.2)
            if 0 <= sp <= 1.25:
                sweep(img, m, W / 2, yy, sp * 1.35 - 0.15, a * 0.95)
        ab = kick_env(t, 26) * 6

    # ── S4 키워드 스트로브 ─────────────────────────────────
    elif t < DROP:
        gap = t >= T(8, 3.4)
        if not gap:
            i = int((t - S4) / BEAT)
            i = max(0, min(7, i))
            d = (t - S4) - i * BEAT
            inv = i in (2, 5)
            txt = WORDS[i]
            tw = [980, 700, 620, 700, 640, 720, 800, 620][i]
            yy = [820, 1020, 760, 1080, 900, 980, 840, 1040][i]
            rot = [-1.5, 1.2, -0.8, 1.8, -1.2, 0.9, -1.7, 1.4][i]
            p = out_expo(d / 0.12)
            a = 1.0 if d < BEAT * 0.72 else max(0.0, 1 - (d - BEAT * 0.72) / (BEAT * 0.28))
            m = text_mask(txt, BRAND, target_w=tw, track_em=0.10)
            if inv:
                vig_mix = 0.28
                img += np.float32([1, 1, 1]) * (0.95 * a)
                blit(img, m, W / 2, yy, -0.95 * a, scale=1.02 - 0.02 * p, rot=rot)
                img = np.clip(img, 0, None)
            else:
                blit(img, m, W / 2, yy, a, glow=0.5, glow_r=24,
                     scale=1.06 - 0.06 * p, rot=rot)
            # 스캔라인 글리치
            if i in (3, 6):
                for k in range(5):
                    yb = int((np.sin(t * 60 + k * 2.1) * 0.5 + 0.5) * H)
                    hgt = 6 + k * 3
                    img[max(0, yb):min(H, yb + hgt)] += 0.22 * a
            prog = (t - S4) / (T(8, 3.4) - S4)
            flash = max(flash, max(0.0, 0.55 - d * 16) * (0.4 + prog))
            ab = max(ab, 5 + 16 * prog * kick_env(t, 30))
            sh = (2 + 12 * prog) * kick_env(t, 26)
            sx += np.sin(t * 210) * sh
            sy += np.cos(t * 178) * sh
            cam = 1.0 + 0.05 * prog + kick_env(t, 24) * 0.03
        else:
            d = t - T(8, 3.4)
            line(img, W / 2, 960, 900 * (1 - out_cubic(d / 0.34)), 3,
                 0.85 * (1 - d / 0.42), glow=0.8)

    # ── S5 드롭: 로고 ──────────────────────────────────────
    elif t < S6:
        d = t - DROP
        k = kick_env(t, 10)
        cam = 1.0 + max(0.0, 0.35 * (1 - out_expo(d / 0.55))) + k * 0.012
        sh = max(0.0, 1 - d / 0.55) ** 2 * 34
        sx += np.sin(d * 150) * sh
        sy += np.cos(d * 132) * sh
        ab = max(0.0, 22 * (1 - d / 0.4)) + k * 2.5
        flash = max(0.0, 1.0 - d * 11)

        for i, off in enumerate((0.0, 0.09, 0.2)):
            rd = d - off
            if 0 < rd < 1.5:
                ring(img, W / 2, 800, 120 + rd * 1750, 12 - i * 3,
                     0.5 * (1 - rd / 1.5) ** 2)
        haze(img, W / 2, 800, W * (0.4 + d * 0.9), max(0.0, 0.5 * (1 - d / 0.8)))

        s = (1.0 + 1.4 * (1 - out_expo(d / 0.5))) * (1 + k * 0.035)
        blit(img, MARK_A, W / 2, 800, min(1.0, d / 0.05),
             glow=0.55 + k * 0.5, glow_r=52, scale=s * 0.80)

        dw = t - T(10, 0)
        if dw > 0:
            p = out_expo(dw / 0.7)
            m = WORD_A.copy()
            cut = int(m.shape[1] * clamp01(dw / 0.5))
            m[:, cut:] = 0
            blit(img, m, W / 2, 1210, 1.0, glow=0.4 + k * 0.3, glow_r=24,
                 scale=1.0 + (1 - p) * 0.06)
        dc = t - T(11, 0)
        if dc > 0:
            a = clamp01(dc / 0.5)
            m = text_mask('SEOUL · DJ CREW · EST. 2026', BRAND, target_w=560, track_em=0.28)
            blit(img, m, W / 2, 1320, a * 0.85, glow=0.3, glow_r=14)
            line(img, W / 2, 1275, 620 * out_expo(dc / 0.8), 1, a * 0.4)
        ds = t - T(12, 0)
        if ds > 0:
            a = clamp01(ds / 0.5)
            for j, txt in enumerate(['WHERE THE LIGHTS FADE,', 'THE MUSIC TAKES OVER.']):
                m = text_mask(txt, BRAND, target_w=700, track_em=0.16)
                blit(img, m, W / 2, 1430 + j * 62, a * (0.8 + 0.2 * j),
                     glow=0.25, glow_r=14)

    # ── S6 모집 ────────────────────────────────────────────
    elif t < S7:
        d = t - S6
        k = kick_env(t, 11)
        cam = 1.0 + k * 0.014
        blit(img, MARK_A, W / 2, 560, min(1.0, d / 0.3), glow=0.35 + k * 0.35,
             glow_r=34, scale=0.30 * (1 + k * 0.03))

        p = out_back(clamp01(d / 0.6))
        m = text_mask('창립 멤버 모집', KRB, target_w=820, track_em=0.02)
        blit(img, m, W / 2, 900 + (1 - p) * 26, min(1.0, d / 0.15),
             glow=0.45 + k * 0.3, glow_r=30, scale=0.94 + p * 0.06)

        if d > 0.35:
            a = clamp01((d - 0.35) / 0.45)
            m = text_mask('FOUNDING MEMBERS WANTED', BRAND, target_w=760, track_em=0.16)
            blit(img, m, W / 2, 1010, a * 0.9, glow=0.3, glow_r=16)
            line(img, W / 2, 1075, 700 * out_expo((d - 0.35) / 0.7), 1, a * 0.45)

        # 역할: 반박자마다 하나씩 켜짐
        for j, r in enumerate(ROLES):
            at = T(13, 1.5) + j * BEAT * 0.5
            dd = t - at
            if dd < 0:
                continue
            a = clamp01(dd / 0.18) * 0.95
            m = text_mask(r, BRAND, target_w=min(560, 150 + len(r) * 34), track_em=0.2)
            blit(img, m, W / 2, 1180 + j * 66, a, glow=0.22 + kick_env(t, 30) * 0.3,
                 glow_r=12, scale=1.0 + max(0.0, 0.05 * (1 - dd / 0.25)))
        ab = kick_env(t, 26) * 4

    # ── S7 마무리 ──────────────────────────────────────────
    else:
        d = t - S7
        k = kick_env(t, 9)
        flash = max(0.0, 0.95 - d * 9)
        cam = 1.06 - out_cubic(min(1.0, d / 1.4)) * 0.06
        sh = max(0.0, 1 - d / 0.45) ** 2 * 20
        sx += np.sin(d * 140) * sh
        haze(img, W / 2, 860, W * 0.9, 0.09 + k * 0.05)
        blit(img, MARK_A, W / 2, 800, 1.0, glow=0.5 + k * 0.35, glow_r=46,
             scale=0.66 * (1 + max(0.0, 0.08 * (1 - out_expo(d / 0.5)))))
        blit(img, WORD_A, W / 2, 1190, 1.0, glow=0.35, glow_r=22)
        a = clamp01((d - 0.35) / 0.5)
        m = text_mask('@blackoutcrew_official', BRAND, target_w=620, track_em=0.1)
        blit(img, m, W / 2, 1340, a, glow=0.3, glow_r=16)
        line(img, W / 2, 1285, 640 * out_expo(d / 0.9), 1, 0.4)
        fade = clamp01((t - (S7 + 1.35)) / 0.5)
        img *= (1 - fade)

    # ── 후처리 ─────────────────────────────────────────────
    if cam != 1.0:
        img = zoom(img, cam)
    if sx or sy:
        img = shake(img, sx, sy)
    img *= (1 - vig_mix) + vig_mix * vignette()
    if ab > 0.4:
        img = chroma(img, ab)
    if flash > 0.004:
        img += flash
    img += grain(fi) * 0.028
    return np.clip(img, 0, 1)


def main():
    if len(sys.argv) == 3:                      # 구간 미리보기
        a, b = float(sys.argv[1]), float(sys.argv[2])
        prev = os.path.join(OUT, 'preview')
        os.makedirs(prev, exist_ok=True)
        for fi in range(int(a * FPS), int(b * FPS) + 1):
            im = frame(fi / FPS, fi)
            cv2.imwrite(os.path.join(prev, f'f{fi:04d}.png'),
                        (im[..., ::-1] * 255).astype(np.uint8))
        print('preview frames ->', prev)
        return

    raw = os.path.join(OUT, 'raw.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fi in range(NF):
        im = frame(fi / FPS, fi)
        p.stdin.write((im * 255).astype(np.uint8).tobytes())
        if fi % 60 == 0:
            print(f'  {fi}/{NF}  {fi / FPS:5.1f}s', flush=True)
    p.stdin.close()
    p.wait()

    final = os.path.join(OUT, 'blackout_teaser.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', os.path.join(OUT, 'bgm.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print('done ->', final)


if __name__ == '__main__':
    main()
