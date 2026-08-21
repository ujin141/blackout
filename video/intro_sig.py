"""
**크루 시그니처 인트로.** 우진이 준 `Blackout 시그니처.mp3` 에 맞춘다.

    python intro_sig.py            → out/intro/sig_story.mp4 · sig_wide.mp4
    python intro_sig.py 3.2 3.5    → 그 구간만 PNG 로 (확인용)

## 소리를 먼저 뜯었다

**그림을 먼저 그리고 소리를 얹으면 반드시 어긋난다.** 파형을 재서 구조를
잡고 거기에 그림을 맞춘다.

    0.00 ~ 1.40   완전 무음. 파형이 0 이다
    1.47 ~ 3.05   16분음표 리듬(약 127BPM). 0.118초 간격으로 규칙적
    3.10          소리가 확 커진다 — RMS 가 0.31 에서 1.00 으로
    3.28 ~ 4.48   타격 다섯 번
    4.71     ★    스펙트럴 플럭스 최댓값. **이 판의 클라이맥스다**
    4.80 ~ 5.85   꼬리. 잦아든다

RMS 가 제일 큰 지점(3.1)과 변화가 제일 급한 지점(4.71)이 다르다.
**터뜨릴 곳은 뒤쪽**이다 — 소리가 커지는 건 준비고, 확 바뀌는 게 사건이다.

## 그림은 소리를 따라간다

    무음      아무것도 없다. 검정과 아주 미세한 입자뿐 —
              **여기서 뭘 보여 주면 뒤가 안 산다**
    빌드업    16분 리듬마다 링이 하나씩 조여든다. 로고가 어둠에서 배어 나온다
    진입      로고가 자리를 잡고 링이 멈춘다
    타격      다섯 번. 플래시 · 색분해 · 행 밀림이 번갈아 온다
    클라이맥스 로고가 터지고 워드마크가 들어선다
    꼬리      슬로건이 앉는다. 링 하나가 마지막으로 퍼진다

## 디테일

프레임마다 얹는 것들이다. 하나씩은 안 보이지만 빼면 티가 난다.

    색분해    빨강·파랑을 다른 배율로. 타격 때 세진다
    스캔라인  아주 옅게. 화면에 결이 생긴다
    입자      떠 있는 먼지. 빛이 있을 때만 보인다
    블룸      밝은 데가 번진다
    그레인    필름 입자. 절차적으로 만든 판이 '찍은 것' 처럼 보이는 최소 조건
    비네트    가장자리를 눌러 가운데로 시선을 모은다
"""
import os
import subprocess
import sys

import cv2
import numpy as np

from poster_kit import BRAND, tmask, paint, glow, outline, logo
from fonts import KR
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

SRC = os.path.join(os.path.expanduser('~'), 'Documents', '카카오톡 받은 파일',
                   'Blackout 시그니처.mp3')

FPS = 60                                  # 타격이 0.118초 간격이라 30 으로는 못 잡는다
DUR = 5.85

PAPER = np.float32([0.98, 0.98, 0.97])
SILVER = np.float32([0.74, 0.77, 0.84])
STEEL = np.float32([0.20, 0.22, 0.28])

# ── 소리에서 읽은 시각 ─────────────────────────────────────
SILENT_END = 1.40
BUILD = np.arange(1.474, 3.06, 0.1181)    # 16분 리듬
ENTER = 3.10
HITS = [(3.280, 0.49), (3.738, 0.48), (3.976, 0.55),
        (4.348, 0.51), (4.476, 0.42)]
CLIMAX = 4.714
TAIL = 4.86

SLOGAN = 'WHERE THE LIGHTS FADE,  THE MUSIC TAKES OVER.'


def envelope():
    """소리의 세기 곡선. **그림 밝기를 여기에 묶는다** — 눈과 귀가 같이 움직인다."""
    wav = os.path.join(OUT, '_sig.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-ac', '1', '-ar', '44100',
                    '-y', wav], check=True)
    import wave
    w = wave.open(wav)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    w.close()
    h = sr // FPS
    m = len(a) // h
    r = np.sqrt((a[:m * h].reshape(m, h) ** 2).mean(1))
    r = r / (r.max() + 1e-9)
    # 조금 흘려 준다 — 프레임마다 튀면 깜빡임으로 보인다
    k = np.array([0.15, 0.25, 0.3, 0.2, 0.1], np.float32)
    return np.convolve(r, k / k.sum(), 'same')


def ease(x):
    x = float(np.clip(x, 0, 1))
    return x * x * (3 - 2 * x)


def burst(t, at, fall):
    """타격 감쇠. 그 순간 1 이고 빠르게 0 으로 떨어진다."""
    d = t - at
    return float(np.exp(-d / fall)) if 0 <= d < fall * 6 else 0.0


def ring(img, cx, cy, r, th, color, a):
    if r <= 1 or a <= 0.002:
        return
    H, W = img.shape[:2]
    lay = np.zeros((H, W), np.float32)
    cv2.circle(lay, (int(cx), int(cy)), int(r), 1.0, max(1, int(th)), cv2.LINE_AA)
    if th > 2:
        lay = cv2.GaussianBlur(lay, (0, 0), th * 0.5)
    img += lay[..., None] * color * a


def glitch(img, amt, seed):
    """행 밀림 + 색분해. **타격 때만** 준다 — 늘 있으면 고장 난 화면이다."""
    if amt <= 0.004:
        return img
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    out = img.copy()
    for _ in range(int(3 + amt * 9)):
        y = int(rng.integers(0, H - 8))
        h = int(rng.integers(4, max(6, int(H * 0.035))))
        dx = int(rng.normal(0, W * 0.035 * amt))
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    return out


def fringe(img, amt):
    if amt <= 0.0002:
        return
    H, W = img.shape[:2]
    def sc(ch, k):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + k)
        return cv2.warpAffine(ch, M, (W, H), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
    img[..., 0] = sc(img[..., 0], amt)
    img[..., 2] = sc(img[..., 2], -amt)


def dust(img, t, n, cx, cy, spread, a):
    """떠 있는 먼지. **빛이 있을 때만 보인다** — 밝기를 소리에 묶는다."""
    if a <= 0.004:
        return
    H, W = img.shape[:2]
    rng = np.random.default_rng(7)
    px = rng.uniform(-1, 1, n)
    py = rng.uniform(-1, 1, n)
    ph = rng.uniform(0, 6.28, n)
    sz = rng.uniform(0.6, 2.6, n)
    for i in range(n):
        x = int(cx + px[i] * spread + np.sin(t * 0.7 + ph[i]) * W * 0.012)
        y = int(cy + py[i] * spread * 1.4 - t * H * 0.014)
        if 2 <= x < W - 2 and 2 <= y < H - 2:
            v = a * (0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 3 + ph[i])))
            r = int(sz[i])
            img[y - r:y + r + 1, x - r:x + r + 1] += PAPER * v * 0.5


def frame(t, env, W, H, cache):
    V = min(W, H) / 1080.0
    cx, cy = W / 2, H / 2
    e = float(env[min(int(t * FPS), len(env) - 1)])

    img = np.zeros((H, W, 3), np.float32)
    # 바탕 — 완전한 검정은 화면에서 죽는다. 아주 옅은 결을 깐다
    yy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    img += (0.012 + 0.010 * np.exp(-(xx ** 2 + yy ** 2) * 1.6))[..., None] * SILVER

    # ── 빌드업: 16분마다 링이 하나씩 조여든다 ────────────
    for i, bt in enumerate(BUILD):
        if t < bt:
            break
        age = t - bt
        if age > 1.5:
            continue
        p = ease(age / 1.5)
        r = (1 - p) * min(W, H) * 0.95 + p * min(W, H) * 0.30
        ring(img, cx, cy, r, 2.0 * V, SILVER, (1 - p) ** 2 * 0.30)

    # ── 로고가 배어 나온다 ────────────────────────────────
    lg = cache['logo']
    if t > SILENT_END:
        p = ease((t - SILENT_END) / (ENTER - SILENT_END))
        a = p * (0.25 + 0.75 * p)
        pulse = 1.0 + 0.05 * e
        if t >= CLIMAX:
            # **터지면 바로 비운다.** 0.55초에 걸쳐 뺐더니 워드마크가
            # 들어서는 동안 로고가 그 위에 겹쳐 지저분했다
            q = ease((t - CLIMAX) / 0.26)
            a *= (1 - q) ** 1.6
            pulse *= 1 + q * 1.4
        if a > 0.004:
            m = lg if abs(pulse - 1) < 0.01 else cv2.resize(
                lg, (max(2, int(lg.shape[1] * pulse)), max(2, int(lg.shape[0] * pulse))))
            glow(img, m, cx, cy, SILVER, a * (0.25 + 0.55 * e), int(60 * V), anchor='c')
            paint(img, m, cx, cy, color=PAPER, a=min(1.0, a), anchor='c')

    # ── 진입 이후: 고정 링 ────────────────────────────────
    if t >= ENTER:
        rr = min(W, H) * 0.30 * (1 + 0.035 * e)
        ring(img, cx, cy, rr, 2.4 * V, SILVER, 0.30 + 0.35 * e)

    # ── 타격 ─────────────────────────────────────────────
    hit = 0.0
    for at, w in HITS:
        hit = max(hit, burst(t, at, 0.075) * w)
    cl = burst(t, CLIMAX, 0.16)
    if cl > 0.01:
        # 클라이맥스 — 링이 밖으로 터진다
        for k in range(3):
            p = ease(min(1.0, (t - CLIMAX) / (0.5 + k * 0.22)))
            ring(img, cx, cy, min(W, H) * (0.30 + p * 1.35), (5 - k) * V,
                 PAPER, (1 - p) ** 2 * 0.85)
        img += PAPER * cl * 0.55

    img += PAPER * hit * 0.22

    # ── 워드마크 ─────────────────────────────────────────
    # **끝 화면이 브랜드다.** 마크 · 이름 · 정체 · 슬로건 순으로 쌓는다 —
    # 로고만 남기면 누군지 모르고, 이름만 남기면 마크가 안 남는다
    if t >= CLIMAX + 0.10:
        p = ease((t - CLIMAX - 0.10) / 0.42)
        sm = cache['mark']
        paint(img, sm, cx, cy - H * 0.082, color=PAPER, a=p * 0.95, anchor='c')
        wm = cache['word']
        glow(img, wm, cx, cy + H * 0.012, SILVER, p * 0.30, int(30 * V), anchor='c')
        paint(img, wm, cx, cy + H * 0.012, color=PAPER, a=p, anchor='c')
        if t >= TAIL:
            q = ease((t - TAIL) / 0.7)
            paint(img, cache['sub'], cx, cy + H * 0.062, color=SILVER,
                  a=q * 0.80, anchor='c')
            paint(img, cache['slo'], cx, cy + H * 0.112, color=SILVER,
                  a=q * 0.64, anchor='c')

    # ── 마감 ─────────────────────────────────────────────
    dust(img, t, 90, cx, cy, min(W, H) * 0.45, (0.25 + 0.55 * e) * 0.5)
    img = glitch(img, hit * 0.9 + cl * 0.5, int(t * 1000))
    fringe(img, 0.0009 + hit * 0.006 + cl * 0.004)
    # 블룸
    b = cv2.GaussianBlur(np.clip(img - 0.72, 0, None), (0, 0), 16 * V)
    img += b * (0.5 + 0.5 * e)
    # 스캔라인 · 비네트 · 그레인
    img[::3] *= 0.955
    r2 = (xx ** 2 + yy ** 2)
    img *= (1 - 0.42 * np.clip(r2, 0, 1) ** 1.8)[..., None]
    img += np.random.default_rng(int(t * 997)).standard_normal((H, W, 1)).astype(np.float32) * 0.006
    return np.clip(img, 0, 1)


def build(W, H, name):
    V = min(W, H) / 1080.0
    env = envelope()
    cache = {
        'logo': logo(int(300 * V)),
        'mark': logo(int(112 * V)),
        'word': tmask('BLACKOUT', BRAND, int(96 * V), 0.16),
        'sub': tmask('SEOUL  ·  DJ CREW', BRAND, int(27 * V), 0.42),
        'slo': tmask(SLOGAN, BRAND, int(17 * V), 0.30),
    }
    out = os.path.join(OUT, f'{name}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', SRC,
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
         '-pix_fmt', 'yuv420p', '-color_range', 'tv',
         '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', '-y', out], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        f = frame(i / FPS, env, W, H, cache)
        p.stdin.write((f * 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print(f'{out}  {W}×{H} · {FPS}fps · {DUR:.2f}초')
    return out


if __name__ == '__main__':
    if len(sys.argv) > 2:
        a, b = float(sys.argv[1]), float(sys.argv[2])
        env = envelope()
        W, H = 1080, 1920
        V = min(W, H) / 1080.0
        cache = {'logo': logo(int(300 * V)), 'mark': logo(int(112 * V)),
                 'word': tmask('BLACKOUT', BRAND, int(96 * V), 0.16),
                 'sub': tmask('SEOUL  ·  DJ CREW', BRAND, int(27 * V), 0.42),
                 'slo': tmask(SLOGAN, BRAND, int(17 * V), 0.30)}
        t = a
        while t <= b + 1e-6:
            f = frame(t, env, W, H, cache)
            q = os.path.join(OUT, f'f_{t:05.2f}.png')
            cv2.imwrite(q, cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
            print(q)
            t += 1 / FPS * 3
    else:
        build(1080, 1920, 'sig_story')
        build(1920, 1080, 'sig_wide')
