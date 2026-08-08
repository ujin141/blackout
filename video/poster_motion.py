"""
포스터 다섯 시안을 영상으로 — 1080×1920 · 30fps · BGM 포함.

**소리에 실제로 반응합니다.** BPM 으로 박만 계산하면 화면은 규칙적으로 뛰지만
곡이 하는 일과는 상관없이 움직입니다. 그래서 wav 를 읽어
저역(킥) · 중역(코드) · 고역(하이햇) · 어택을 프레임마다 뽑아 그 값으로 움직입니다.
드롭에서 화면이 커지고 브레이크에서 잦아드는 건 그래서입니다.

포스터는 **매 프레임 다시 그리지 않습니다.** build() 한 번에 1~2초가 걸려서
450프레임을 다시 그리면 시안 하나에 10분이 넘습니다.
정지본을 한 장 만들어 두고 그 위에 시간축 처리를 얹습니다.
예외는 A안의 마퀴 띠 — 이건 실제로 흘러야 해서 프레임마다 다시 얹습니다
(띠는 캐시해 두고 밀기만 하므로 쌉니다).

시안마다 움직임이 다른 건 디자인 언어가 다르기 때문입니다.

    A split   물결 + 마퀴가 실제로 흐른다. 킥에 수면이 크게 인다
    B club    어택마다 흰 섬광 · 가로 슬라이스 글리치 · 스캔라인 (고역에 속도가 붙는다)
    C ticket  종이가 기울며 빛을 받고, 바코드 위로 스캐너 선이 지나간다
    D neon    켜질 때 깜빡이고, 그 뒤엔 저역에 후광이 부푼다. 고역 어택에 관이 튄다
    E grid    칸이 밀려 들어온 뒤, 박마다 칸 하나씩 돌아가며 튄다

BGM 은 `audio_reel.py` 의 다섯 곡을 나눠 물립니다. wav 가 없으면 자동으로 만듭니다.
    A festival 128 · B techno 145 · C citypop 105 · D hard 155 · E bounce 132

python poster_motion.py            다섯 개 전부
python poster_motion.py neon grid  골라서
"""
import os
import sys
import wave
import subprocess
import numpy as np
import cv2
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'poster')
REEL = os.path.join(HERE, 'out', 'reel')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30

# 시안 → (포스터 모듈, BGM 스타일, 움직임)
SPECS = {
    'split':  ('poster_split',  'festival', 'water'),
    'club':   ('poster_club',   'techno',   'strobe'),
    'ticket': ('poster_ticket', 'citypop',  'card'),
    'neon':   ('poster_neon',   'hard',     'flicker'),
    'grid':   ('poster_grid',   'bounce',   'tiles'),
}


# ── 소리 분석 ─────────────────────────────────────────────
def bgm(style):
    """wav 가 없으면 만든다. (경로, BPM, 길이) 를 돌려준다."""
    import audio_reel
    p = os.path.join(REEL, f'bgm_{style}.wav')
    if not os.path.exists(p):
        audio_reel.write(style)
    bpmv, bars = audio_reel.STYLES[style]
    return p, bpmv, (60.0 / bpmv) * 4 * bars


def _env(x, sr, nf):
    """프레임마다 RMS. 곡 전체를 한 번에 필터링한 뒤 잘라 쓰는 게 훨씬 싸다."""
    hop = len(x) / nf
    e = np.empty(nf, np.float32)
    for i in range(nf):
        w = x[int(i * hop):int((i + 1) * hop)]
        e[i] = np.sqrt(np.mean(w * w)) if len(w) else 0.0
    return e


def _norm(e):
    """상위 3% 를 1.0 으로. 최댓값으로 나누면 순간 피크 하나에 전체가 눌린다."""
    return np.clip(e / (np.percentile(e, 97) + 1e-9), 0, 1.6)


def analyze(path, nf):
    """저역·중역·고역·어택을 프레임 단위로 뽑는다."""
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    lo = signal.sosfilt(signal.butter(4, 170, 'lp', fs=sr, output='sos'), x)
    md = signal.sosfilt(signal.butter(4, [300, 3200], 'bp', fs=sr, output='sos'), x)
    hi = signal.sosfilt(signal.butter(4, 6000, 'hp', fs=sr, output='sos'), x)
    A = {k: _norm(_env(v, sr, nf)) for k, v in
         (('low', lo), ('mid', md), ('high', hi), ('rms', x))}
    # 어택 — 에너지가 늘어난 만큼만. 줄어드는 구간은 0
    for k in ('low', 'high'):
        d = np.clip(np.diff(A[k], prepend=A[k][0]), 0, None)
        A[k + '_hit'] = _norm(d)
    return A


# ── 공통 처리 ─────────────────────────────────────────────
def cam(base, z, dx=0.0, dy=0.0, rot=0.0):
    Mx = cv2.getRotationMatrix2D((W / 2, H / 2), rot, z)
    Mx[0, 2] += dx
    Mx[1, 2] += dy
    return cv2.warpAffine(base, Mx, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def chroma(img, off):
    """색분해 흔들림. 정지본의 색분해와 달리 이건 시간축이라 따로 논다."""
    if off < 0.5:
        return img
    o = int(off)
    out = img.copy()
    out[:, :, 0] = np.roll(img[:, :, 0], o, axis=1)
    out[:, :, 2] = np.roll(img[:, :, 2], -o, axis=1)
    return out


def slices(img, amt, rng):
    """가로로 잘라 어긋내는 글리치. 어택에서만 튀어야 고장으로 안 보인다."""
    if amt < 0.25:
        return img
    out = img.copy()
    for _ in range(int(2 + amt * 5)):
        y = int(rng.integers(0, H - 40))
        h = int(rng.integers(10, 90))
        out[y:y + h] = np.roll(out[y:y + h], int(rng.integers(-1, 2) * amt * 90), axis=1)
    return out


def notch(g, c, half):
    """c ± half 안에서 0, 밖에서 1. 띠가 지나가는 자리는 흔들지 않으려고 쓴다."""
    return np.clip((np.abs(g - c) - half) / (half * 0.5), 0, 1)


# ── 시안별 움직임 ─────────────────────────────────────────
def m_water(base, t, i, dur, A, G, seam=None, bands=None):
    gx, gy = G
    amp = 4.0 + 11.0 * A['low'][i]
    fade = np.clip(1 - (gy / H - 0.42) / 0.10, 0, 1) * notch(gy, H * 0.212, 108) * notch(gy, seam, 118)
    dx = np.sin(gy * 0.021 + t * 2.6).astype(np.float32) * amp * fade
    dy = np.sin(gx * 0.013 + t * 1.9).astype(np.float32) * amp * 0.5 * fade
    img = cv2.remap(base, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    import poster_split as PS
    for text, cy, bh, bg, ang, spd in bands:
        PS.marquee(img, text, cy, bh, bg, PS.INK, 1.0, ang, phase=-t * spd)

    img = cam(img, 1.02 + 0.05 * (t / dur) + 0.018 * A['low'][i])
    img *= 0.94 + 0.10 * A['rms'][i]
    return chroma(img, 5.0 * A['low_hit'][i])


def m_strobe(base, t, i, dur, A, G, rng=None):
    lo, hi = A['low'][i], A['high'][i]
    img = cam(base, 1.06 - 0.04 * (t / dur) + 0.030 * lo,
              dx=np.sin(t * 37.0) * 7.0 * A['low_hit'][i],
              rot=np.sin(t * 5.0) * 0.35 * lo)
    sc = (np.sin(np.arange(H, dtype=np.float32) * 0.55 - t * (18.0 + 34.0 * hi)) * 0.5 + 0.5) ** 3
    img = img * (1.0 - sc[:, None, None] * (0.08 + 0.10 * hi))
    img = slices(img, A['high_hit'][i], rng)
    img = img + A['low_hit'][i] ** 2 * 0.45
    return chroma(img, 12.0 * A['low_hit'][i])


def m_card(base, t, i, dur, A, G, bar=None):
    gx, gy = G
    a = np.sin(t * 0.9) * 0.013 + 0.006 * A['mid'][i]
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    dst = np.float32([[W * a, 0], [W * (1 - a), H * 0.007],
                      [W * (1 + a), H], [-W * a, H * (1 - 0.007)]])
    img = cv2.warpPerspective(base, cv2.getPerspectiveTransform(src, dst), (W, H),
                              flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    band = (gx / W) * 0.7 + (gy / H) * 0.3 - (t / dur * 1.9 - 0.45)
    img = img + np.clip(1 - np.abs(band) / 0.13, 0, 1)[..., None] ** 2 * (0.10 + 0.16 * A['rms'][i])
    # 바코드 위를 지나가는 스캐너 선 — 2초에 한 번
    sx = ((t % 2.0) / 2.0) * W
    m = np.clip(1 - np.abs(gx - sx) / (26.0), 0, 1) * ((gy > bar[0]) & (gy < bar[1]))
    img = img + m[..., None] * np.float32([0.10, 0.35, 1.00]) * 0.55
    return cam(img, 1.012 + 0.022 * (t / dur) + 0.012 * A['low'][i])


def m_flicker(base, t, i, dur, A, G, glow=None, rng=None):
    if t < 1.2:
        seq = [0.08, 0.90, 0.10, 1.00, 0.22, 1.00, 0.45, 1.00, 0.70, 1.00]
        k = seq[min(int(t / 1.2 * len(seq)), len(seq) - 1)]
    else:
        k = 0.82 + 0.30 * A['low'][i]
        if A['high_hit'][i] > 0.8 and rng.random() < 0.35:      # 관이 한 번 튄다
            k *= 0.45
    img = cam(base, 1.02 + 0.045 * (t / dur) + 0.020 * A['low'][i],
              dx=np.sin(t * 53.0) * 2.2)
    img = img * (0.42 + 0.58 * k)
    if glow is not None:
        img = img + glow * k * (0.30 + 1.10 * A['low'][i])
    return chroma(img, 5.0 * A['high_hit'][i])


def m_tiles(base, t, i, dur, A, G, rects=None, bpmv=None):
    img = cam(base, 1.012 + 0.026 * (t / dur))
    if t < 1.7:
        canvas = np.zeros_like(img)
        canvas[:] = img[0, 0]
        for j, (y0, y1) in enumerate(rects):
            s = np.clip((t - j * 0.13) / 0.42, 0, 1)
            s = 1 - (1 - s) ** 3
            if s <= 0:
                continue
            off = int((1 - s) * W * (0.55 if j % 2 == 0 else -0.55))
            row = np.roll(img[y0:y1], off, axis=1)
            if off > 0:
                row[:, :off] = canvas[y0:y1, :off]
            elif off < 0:
                row[:, off:] = canvas[y0:y1, off:]
            canvas[y0:y1] = row * s + canvas[y0:y1] * (1 - s)
        return canvas
    # 박마다 칸 하나가 돌아가며 튄다
    beat = int(t / (60.0 / bpmv))
    j = beat % len(rects)
    y0, y1 = rects[j]
    e = A['low'][i]
    tile = img[y0:y1]
    z = 1.0 + 0.035 * e
    hgt, wid = tile.shape[:2]
    Mx = cv2.getRotationMatrix2D((wid / 2, hgt / 2), 0, z)
    img[y0:y1] = cv2.warpAffine(tile, Mx, (wid, hgt), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE) * (1 + 0.30 * e)
    return img * (0.95 + 0.09 * A['rms'][i])


MOTION = {'water': m_water, 'strobe': m_strobe, 'card': m_card,
          'flicker': m_flicker, 'tiles': m_tiles}


def render(key):
    mod_name, style, motion = SPECS[key]
    mod = __import__(mod_name)
    print(f'[{key}] 정지본 렌더…')
    base = np.ascontiguousarray(mod.build(W, H, True).astype(np.float32))

    wav, bpmv, dur = bgm(style)
    nf = int(round(dur * FPS))
    A = analyze(wav, nf)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(11)

    extra = {}
    if motion == 'water':
        import poster_split as PS
        extra['seam'] = H * 0.44
        extra['bands'] = [
            ('DAY TO NIGHT  ×  SEOUL  ×  ', H * 0.212, 40, PS.MAGENTA, -PS.ANGLE, 150.0),
            ('POOL PARTY  ×  SOLO PARTY  ×  ', H * 0.44, 52, PS.CYAN, PS.ANGLE, -190.0)]
    if motion == 'strobe':
        extra['rng'] = rng
    if motion == 'card':
        extra['bar'] = (H * 0.826, H * 0.826 + 52 * (H / 1350.0))
    if motion == 'flicker':
        lum = base @ np.float32([0.299, 0.587, 0.114])
        hi = np.clip(lum - 0.50, 0, 1) / 0.5
        extra['glow'] = cv2.GaussianBlur(hi, (0, 0), 26)[..., None] * \
            np.float32([0.42, 0.85, 0.20]) * 0.55
        extra['rng'] = rng
    if motion == 'tiles':
        import poster_grid
        _, _, _, ys = poster_grid.layout(W, H)
        extra['rects'] = [(int(a), int(b)) for a, b in ys.values()]
        extra['bpmv'] = bpmv

    fn = MOTION[motion]
    raw = os.path.join(OUT, f'raw_{key}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for fi in range(nf):
        t = fi / FPS
        img = fn(base, t, fi, dur, A, (gx, gy), **extra)
        img = img + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.008
        if t < 0.45:
            img = img * (t / 0.45)
        tail = dur - t
        if tail < 0.5:
            img = img * max(0.0, tail / 0.5)
        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f'motion_{key}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '22',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '224k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {dur:.1f}s  {style} {bpmv:.0f}BPM')


if __name__ == '__main__':
    keys = [k.lower() for k in sys.argv[1:]] or list(SPECS)
    for k in keys:
        if k not in SPECS:
            print(f'모르는 시안: {k} — {", ".join(SPECS)}')
            continue
        render(k)
