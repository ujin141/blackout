"""
지금 시안(사진 배경 판)을 영상으로. 스토리 1080×1920 · 피드 1080×1350 · 30fps · BGM 포함.

**포스터를 다시 그리지 않습니다.** 짜임·글자·정보는 그대로 두고 **시간축만** 얹습니다 —
포스터를 매 프레임 다시 그리면 `build()` 한 번이 2~4초라 450프레임에 30분이 넘습니다.
정지본을 한 장 만들어 두고 그 위에서 움직입니다.

**소리에 실제로 반응합니다.** BPM 으로 박만 계산하면 화면은 규칙적으로 뛰지만 곡이
하는 일과는 상관없이 움직입니다. wav 를 읽어 저역(킥)·중역·고역(하이햇)·어택을
프레임 단위로 뽑고 그 값으로 움직입니다.

파티 느낌은 다섯 겹에서 나옵니다. **판을 흔드는 게 아니라 빛을 움직입니다** —
글자가 흔들리면 정보가 안 읽히고, 정보가 안 읽히면 포스터를 영상으로 만든 뜻이 없습니다.

    물빛      수면 코스틱이 사진 위에서 계속 흐른다. 이게 있어야 물이 살아 있다
    조명 스침 색 띠가 대각선으로 지나간다. 클럽 무빙라이트가 하는 일
    빛 번짐   밝은 곳(네온·물빛)만 뽑아 저역에 맞춰 부푼다. 킥마다 판이 숨 쉰다
    카메라    아주 느린 밀기 + 흔들림. **1.5% 안쪽** — 넘으면 글자가 떨린다
    글리치    어택에서만 색분해·가로 슬라이스. 상시로 주면 고장 난 화면이 된다

python motion.py                 판 전부 × 두 사이즈
python motion.py tag ko          판만 골라서
python motion.py tag story       사이즈까지 골라서
BLACKOUT_HERO=2 python motion.py tag    사진 2번으로 (파일명에 _h2)
"""
import os
import sys
import wave
import subprocess
import numpy as np
import cv2
from scipy import signal
from poster_kit import HERO_TAG

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

FPS = 30
CUTS = {'story': (1080, 1920, True), 'feed': (1080, 1350, False)}

# 판 → (모듈, BGM). BGM 은 `audio_motion.py` 의 네 곡이다.
# 처음엔 `audio_poster.py` 를 물렸는데 "비트가 뽕짝 같다"는 지적을 받았다 —
# 킥이 네 박 다 치는데 베이스가 엇박으로 튀고 그 위에 선율이 얹혀 있었다.
# 새 곡들은 서브가 킥 밑에 깔려 지속되고, 선율이 없고, 칸을 다 안 채운다.
SPECS = {
    'tag':    ('poster_tag',    'dark'),
    'venn':   ('poster_venn',   'heavy'),
    'float':  ('poster_float',  'deep'),
    'ripple': ('poster_ripple', 'dub'),
    'night':  ('poster_night',  'deep'),
    'deck':   ('poster_deck',   'dark'),
    'dive':   ('poster_dive',   'dub'),
    'real':   ('poster_real',   'deep'),
    'ko':     ('poster_ko',     'heavy'),
    'time':   ('poster_time',   'dark'),
    'card':   ('poster_card',   'dark'),
}


# ── 소리 ──────────────────────────────────────────────────
def bgm(style):
    """wav 가 없으면 만든다. (경로, BPM, 길이)."""
    import audio_motion
    p = os.path.join(OUT, f'bgm_{style}.wav')
    if not os.path.exists(p):
        audio_motion.write(style)
    bpmv, bars = audio_motion.STYLES[style]
    return p, bpmv, (60.0 / bpmv) * 4 * bars


def analyze(path, nf):
    """저역·중역·고역·어택을 프레임 단위로. **최댓값이 아니라 상위 3% 로 정규화한다** —
    최댓값으로 나누면 순간 피크 하나에 전체가 눌려 거의 안 움직인다."""
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    lo = signal.sosfilt(signal.butter(4, 170, 'lp', fs=sr, output='sos'), x)
    md = signal.sosfilt(signal.butter(4, [300, 3200], 'bp', fs=sr, output='sos'), x)
    hi = signal.sosfilt(signal.butter(4, 6000, 'hp', fs=sr, output='sos'), x)
    hop = len(x) / nf

    def env(v):
        e = np.array([np.sqrt(np.mean(v[int(i * hop):int((i + 1) * hop)] ** 2))
                      for i in range(nf)], np.float32)
        return np.clip(e / (np.percentile(e, 97) + 1e-9), 0, 1.6)

    A = {k: env(v) for k, v in (('low', lo), ('mid', md), ('high', hi), ('rms', x))}
    for k in ('low', 'high'):
        d = np.clip(np.diff(A[k], prepend=A[k][0]), 0, None)
        A[k + '_hit'] = np.clip(d / (np.percentile(d, 97) + 1e-9), 0, 1.6)
    return A


# ── 겹 ────────────────────────────────────────────────────
def caustics(t, W, H, amp):
    """수면 물빛. **1/3 해상도로 그려 키운다** — 원본 크기로 매 프레임 계산하면
    프레임당 몇 배가 든다. 흐려서 올리는 것이라 해상도가 안 아쉽다."""
    qw, qh = W // 3, H // 3
    yq, xq = np.mgrid[0:qh, 0:qw].astype(np.float32)
    x, y = xq * 0.048, yq * 0.048
    f = (np.sin(x * 1.6 + 1.7 * np.sin(y * 0.5 + t * 0.9)) +
         np.sin(y * 1.25 + 1.4 * np.sin(x * 0.44 - t * 0.7)) +
         0.85 * np.sin((x + y) * 0.95 + t * 1.3))
    k = np.clip(1 - np.abs(np.sin(f * 2.0)) * 7.0, 0, 1) ** 1.15
    k = cv2.resize(cv2.GaussianBlur(k, (0, 0), 1.0), (W, H), interpolation=cv2.INTER_LINEAR)
    return k * amp


def sweep(G, W, H, t, period, width, tilt=0.35):
    """대각선으로 지나가는 빛 띠. 클럽 무빙라이트가 하는 일이다.
    **판을 가로지르는 방향이 있어야** 정지한 그림이 흐르는 것으로 보인다."""
    gx, gy = G
    u = (gx / W) + (gy / H) * tilt
    p = (t / period) % 1.0
    d = np.abs(((u - p * 1.6 + 0.3) % 1.0) - 0.5)
    return np.clip(1 - d / width, 0, 1) ** 2


def cam(base, W, H, z, dx=0.0, dy=0.0, rot=0.0):
    M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, z)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def chroma(img, off):
    if off < 0.5:
        return img
    o = int(off)
    out = img.copy()
    out[:, :, 0] = np.roll(img[:, :, 0], o, axis=1)
    out[:, :, 2] = np.roll(img[:, :, 2], -o, axis=1)
    return out


def slices(img, amt, rng, W, H, ylimit):
    """가로로 잘라 어긋내는 글리치. **정보가 앉은 아래쪽은 절대 건드리지 않는다** —
    한 프레임만 밀려도 날짜·주소가 안 읽히고, 그러면 포스터를 영상으로 만든 뜻이 없다."""
    if amt < 0.35:
        return img
    top = int(ylimit)
    out = img.copy()
    for _ in range(int(2 + amt * 4)):
        y = int(rng.integers(0, max(1, top - 40)))
        h = min(int(rng.integers(10, 80)), top - y)
        if h <= 0:
            continue
        out[y:y + h] = np.roll(out[y:y + h], int(rng.integers(-1, 2) * amt * 70), axis=1)
    return out


def frame(base, glow, G, t, i, dur, A, rng, W, H, story):
    lo, mid, hi = A['low'][i], A['mid'][i], A['high'][i]
    hit, hhit = A['low_hit'][i], A['high_hit'][i]

    img = base

    # 물빛 — 사진 위를 계속 흐른다. 아래로 갈수록 세게(수면이 아래에 있다)
    gy = G[1]
    depth = np.clip(gy / H, 0, 1) ** 0.8
    cw = caustics(t, W, H, 0.055 + 0.085 * lo) * depth
    img = img + cw[..., None] * np.float32([0.45, 0.82, 1.00])

    # 조명 스침 두 줄 — 색이 하나면 조명이 아니라 반사다
    img = img + sweep(G, W, H, t, 6.5, 0.16)[..., None] * \
        np.float32([1.00, 0.30, 0.66]) * (0.035 + 0.075 * mid)
    img = img + sweep(G, W, H, t + 3.1, 9.0, 0.13, -0.25)[..., None] * \
        np.float32([0.35, 0.80, 1.00]) * (0.028 + 0.060 * mid)

    # 빛 번짐 — 밝은 곳(네온·물빛·글자)만 저역에 맞춰 부푼다. 킥마다 판이 숨 쉰다
    img = img + glow * (0.16 + 0.95 * lo)

    # 카메라. **1.5% 안쪽** — 넘으면 글자가 떨려서 정보가 안 읽힌다
    img = cam(img, W, H, 1.008 + 0.014 * (t / dur) + 0.010 * lo,
              dx=np.sin(t * 0.55) * 3.5, dy=np.cos(t * 0.41) * 2.5,
              rot=np.sin(t * 0.33) * 0.12)
    img = img * (0.95 + 0.09 * A['rms'][i])

    # 글리치는 어택에서만
    # 글자 영역 위에서만 튄다. 발치는 어느 판이든 아래 30% 안에 있다
    img = slices(img, hhit, rng, W, H, H * 0.68)
    img = chroma(img, 4.0 * hit)
    img = img + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.007

    # 시작 0.5초 열림 · 끝 0.6초 닫힘
    if t < 0.5:
        img = img * (t / 0.5)
    tail = dur - t
    if tail < 0.6:
        img = img * max(0.0, tail / 0.6)
    return np.clip(img, 0, 1)


def render(key, cut='story'):
    W, H, story = CUTS[cut]
    mod_name, style = SPECS[key]
    mod = __import__(mod_name)
    print(f'[{key} · {cut}{HERO_TAG}] 정지본…')
    base = np.ascontiguousarray(mod.build(W, H, story).astype(np.float32))

    wav, bpmv, dur = bgm(style)
    nf = int(round(dur * FPS))
    A = analyze(wav, nf)
    G = tuple(np.mgrid[0:H, 0:W].astype(np.float32)[::-1])
    rng = np.random.default_rng(11)

    # 밝은 곳만 뽑아 흐려 둔다. **매 프레임 블러하면 감당이 안 된다**
    lum = base @ np.float32([0.299, 0.587, 0.114])
    glow = cv2.GaussianBlur(np.clip(lum - 0.55, 0, 1) / 0.45, (0, 0), W * 0.020)[..., None] * \
        np.float32([0.62, 0.86, 1.00]) * 0.55

    raw = os.path.join(OUT, f'raw_{key}_{cut}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '19', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fi in range(nf):
        im = frame(base, glow, G, fi / FPS, fi, dur, A, rng, W, H, story)
        p.stdin.write((im * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f'motion_{key}_{cut}{HERO_TAG}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '22', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '224k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {dur:.1f}s  {style} {bpmv:.0f}BPM')


if __name__ == '__main__':
    args = [a.lower() for a in sys.argv[1:]]
    cuts = [c for c in args if c in CUTS] or list(CUTS)
    keys = [k for k in args if k in SPECS] or list(SPECS)
    for bad in [a for a in args if a not in CUTS and a not in SPECS]:
        print(f'모르는 이름: {bad} — 판 {", ".join(SPECS)} · 사이즈 {", ".join(CUTS)}')
    for k in keys:
        for c in cuts:
            render(k, c)
