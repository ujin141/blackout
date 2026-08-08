"""
포스터 영상 전용 음원 — 멤버 릴스(`audio_reel.py`)와 한 곡도 겹치지 않는다.

처음엔 릴스 다섯 곡을 그대로 물렸는데 "예전 영상이랑 BGM이 같다"는 지적을 받았다.
같은 곡을 다른 영상에 또 쓰면 계정 전체가 같은 영상처럼 보인다.

**장르 · BPM · 조성을 전부 갈랐다.** BPM만 바꾸면 비슷하게 들린다 —
릴스에서 이미 한 번 겪은 일이라 리듬 골격부터 다르게 짰다.

    시안  스타일      BPM  골격
    A     afro        122  스윙 16분 셰이커 + 콩가. 킥 4온플로어지만 퍼커션이 앞에 선다
    B     industrial  138  왜곡 킥 + 8분 라이드. 멜로디 없음. 3박 하프타임 스네어
    C     garage      136  2스텝 — 킥 1·3&, 스네어 2·4, 하이햇에 구멍을 낸다
    D     synthwave   118  게이트 아르페지오 + 리버브 큰 스네어. 드롭 없이 흐른다
    E     breaks      110  브레이크비트 — 4온플로어를 안 쓴다. 고스트 스네어로 채운다

릴스 쪽:  festival 128 · techno 145 · bounce 132 · hard 155 · citypop 105
겹치는 BPM도, 조성도 없다.

python audio_poster.py            전부
python audio_poster.py garage     하나만
"""
import os
import sys
import numpy as np
from scipy import signal
from audio import (SR, place, lp, hp, bp, reverb,
                   kick as kick0, noise_riser, impact, clap, hat)
from audio_reel import sat, subf, snare, metal, stab, pad, rev_tail, hard_kick, soft_kick

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

# 스타일: (BPM, 마디 수) — 릴스의 128·145·132·155·105 와 하나도 안 겹친다
STYLES = {
    'afro':       (122.0, 8),
    'industrial': (138.0, 9),
    'garage':     (136.0, 8),
    'synthwave':  (118.0, 8),
    'breaks':     (110.0, 7),
}

# 조성도 다르게. 같은 조면 결국 비슷하게 들린다
ROOT = {'afro':       43.65,   # F1
        'industrial': 41.20,   # E1
        'garage':     49.00,   # G1
        'synthwave':  46.25,   # F#1
        'breaks':     51.91}   # G#1


# ── 이 파일에서만 쓰는 소리 ────────────────────────────────
def shaker(dur=0.06, gain=1.0, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    return bp(rng.standard_normal(n), 4200, 11000) * np.exp(-t * (30 / dur)) * gain


def conga(freq, dur=0.22, gain=1.0):
    """손으로 치는 타악. 피치가 살짝 떨어지며 몸통이 울린다."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = freq * (1 + 0.35 * np.exp(-t * 40))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16)
    skin = bp(np.random.randn(n), 900, 4000) * np.exp(-t * 60) * 0.35
    return (body + skin) * gain


def rim(gain=1.0):
    n = int(0.06 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1750 * t) + np.sin(2 * np.pi * 420 * t) * 0.5
    return x * np.exp(-t * 130) * gain


def pluck(freq, dur=0.22, gain=1.0, cut=2600):
    """튕기는 소리. 아르페지오·마림바 자리에 쓴다."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = signal.sawtooth(2 * np.pi * freq * t) * 0.6 + np.sin(2 * np.pi * freq * t) * 0.7
    x = lp(x, cut * np.exp(-0.0) )
    e = np.clip(t / 0.004, 0, 1) * np.exp(-t * (7.5 / dur))
    return x * e * gain


def ride(dur=0.55, gain=1.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (2100, 3170, 4530, 6100):
        x += np.sin(2 * np.pi * f * (1 + rng.random() * 0.04) * t) / 4
    x += hp(rng.standard_normal(n), 7000) * 0.5
    return x * np.exp(-t * (5.0 / dur)) * gain


def big_snare(dur=0.42, gain=1.0):
    """신스웨이브용 — 몸통이 크고 꼬리가 길다"""
    n = int(dur * SR); t = np.arange(n) / SR
    nz = bp(np.random.randn(n), 1100, 6800) * np.exp(-t * 13)
    tone = (np.sin(2 * np.pi * 172 * t) + np.sin(2 * np.pi * 260 * t) * 0.7) * np.exp(-t * 20)
    return (nz * 0.9 + tone * 0.5) * gain


def ghost(gain=1.0):
    n = int(0.09 * SR); t = np.arange(n) / SR
    return bp(np.random.randn(n), 1600, 6000) * np.exp(-t * 55) * gain


def sweep(dur, gain=1.0, up=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.random.randn(n)
    k = (t / dur) if up else (1 - t / dur)
    out = np.zeros(n)
    step = int(SR * 0.05)
    for i in range(0, n, step):
        c = 400 + 8000 * (k[min(i, n - 1)] ** 2)
        out[i:i + step] = bp(x[i:i + step], max(120, c * 0.5), c + 900)
    return out * np.clip(t / 0.1, 0, 1) * gain


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * bars
    N = int(dur * SR)
    T = lambda b, x=0.0: (b - 1) * bar + x * beat
    R = ROOT[style]

    drums = np.zeros(N); bass = np.zeros(N); lead = np.zeros(N); fx = np.zeros(N)
    kicks = []
    DROP = bars // 2 + 1

    # ── AFRO — 퍼커션이 앞에 선다. 킥은 바닥만 깐다 ──────────
    if style == 'afro':
        prog = [[R * 4, R * 4.76, R * 6], [R * 3.56, R * 4.76, R * 6],
                [R * 4, R * 5.33, R * 6.35], [R * 3.56, R * 4.49, R * 5.33]]
        for b in range(1, bars + 1):
            ch = prog[(b - 1) % 4]
            for x in range(4):
                place(drums, kick0(0.44, 0.85 if b < 3 else 1.0), T(b, x)); kicks.append(T(b, x))
            for i in range(8):                              # 스윙 16분 셰이커
                place(drums, shaker(0.05, 0.13, b * 8 + i), T(b, i * 0.5))
                place(drums, shaker(0.04, 0.07, b * 8 + i + 99), T(b, i * 0.5 + 0.32))
            for at, f in ((1.75, 196), (2.5, 262), (3.25, 165), (3.75, 220)):
                place(drums, conga(f, 0.20, 0.30), T(b, at))
            place(drums, rim(0.24), T(b, 1)); place(drums, rim(0.24), T(b, 3))
            for at in (0.0, 1.5, 2.5):                      # 엇박으로 걸리는 서브
                place(bass, subf(R, beat * 0.85, 0.72), T(b, at))
            place(lead, pad(ch, bar * 0.96, 0.22, 2200), T(b))
            if b >= DROP:                                   # 마림바처럼 튕기는 선율
                for at, mul in ((0.25, 4), (1.0, 6), (1.75, 5.33), (2.75, 4), (3.5, 6)):
                    place(lead, pluck(R * mul, 0.26, 0.26, 3000), T(b, at))

    # ── INDUSTRIAL — 멜로디 없음. 쇠와 왜곡만 ──────────────
    elif style == 'industrial':
        for b in range(1, bars + 1):
            drop = b >= DROP
            g = 0.80 if not drop else 1.0
            for x in range(4):
                place(drums, hard_kick(0.40, g), T(b, x)); kicks.append(T(b, x))
                place(drums, ride(0.30, 0.16 if not drop else 0.24, b * 4 + x), T(b, x + 0.5))
            place(drums, snare(0.34, 0.9 * g, 0.9), T(b, 2))          # 3박 하프타임
            for i in (0, 2):
                place(drums, metal(0.11, 0.20 * g, b * 7 + i), T(b, i + 0.75))
            for at in (0.5, 1.5, 2.5, 3.5):
                place(bass, stab([R], 0.16, 0.55 * g, 300, 0.20), T(b, at))
            if drop:
                place(bass, subf(R, bar * 0.95, 0.6), T(b))
            if b % 4 == 0:
                place(fx, sweep(bar * 0.9, 0.28, up=True), T(b))
        place(fx, impact(2.0, 0.8), T(DROP))

    # ── GARAGE — 2스텝. 하이햇에 구멍을 내야 굴러간다 ────────
    elif style == 'garage':
        for b in range(1, bars + 1):
            drop = b >= DROP
            g = 0.85 if not drop else 1.0
            place(drums, kick0(0.40, g), T(b, 0)); kicks.append(T(b, 0))
            place(drums, kick0(0.36, g * 0.9), T(b, 2.5)); kicks.append(T(b, 2.5))
            if b % 2 == 0:
                place(drums, kick0(0.32, g * 0.7), T(b, 1.75)); kicks.append(T(b, 1.75))
            place(drums, snare(0.26, 0.9 * g, 1.3, 0.7), T(b, 1))
            place(drums, snare(0.26, 0.9 * g, 1.3, 0.7), T(b, 3))
            for i in range(16):                             # 4·11·14번째를 비운다
                if i % 8 in (3, 6):
                    continue
                a = 0.15 if i % 4 == 2 else 0.07
                place(drums, hat(0.04, a * (1.0 if drop else 0.7)), T(b, i * 0.25 + (0.06 if i % 2 else 0)))
            for at in (0.0, 1.5, 2.5, 3.25):
                place(bass, subf(R * (2 if at == 2.5 else 1), beat * 0.55, 0.75 * g), T(b, at))
            if drop:                                        # 잘라 붙인 오르간 코드
                for at, mul in ((0.5, 1), (1.75, 1), (2.75, 1.19), (3.5, 1)):
                    place(lead, stab([R * 4 * mul, R * 4.76 * mul, R * 6 * mul],
                                     beat * 0.34, 0.26, 2400, 0.26), T(b, at))

    # ── SYNTHWAVE — 드롭 없이 계속 흐른다 ──────────────────
    elif style == 'synthwave':
        prog = [[R * 4, R * 4.76, R * 6], [R * 3.36, R * 4, R * 5.05],
                [R * 3.56, R * 4.49, R * 5.33], [R * 3, R * 4, R * 4.76]]
        arp = [4, 6, 4.76, 8]
        for b in range(1, bars + 1):
            ch = prog[(b - 1) % 4]
            root = ch[0] / 4
            for x in range(4):
                place(drums, soft_kick(0.42, 0.95), T(b, x)); kicks.append(T(b, x))
            place(drums, big_snare(0.42, 0.85), T(b, 1))
            place(drums, big_snare(0.42, 0.85), T(b, 3))
            for i in range(8):                              # 8분 아날로그 베이스
                place(bass, subf(root * (1 if i % 4 else 2), beat * 0.42, 0.60), T(b, i * 0.5))
                place(drums, hat(0.045, 0.10), T(b, i * 0.5 + 0.25))
            place(lead, pad(ch, bar * 0.98, 0.20, 2600), T(b))
            if b >= 2:                                      # 16분 아르페지오
                for i in range(16):
                    place(lead, pluck(root * arp[i % 4] * (2 if i >= 8 else 1),
                                      0.16, 0.20, 3800), T(b, i * 0.25))
        place(fx, rev_tail(bar * 0.5, 0.18), T(bars, 2))

    # ── BREAKS — 4온플로어를 안 쓴다 ───────────────────────
    else:
        for b in range(1, bars + 1):
            drop = b >= DROP
            g = 0.85 if not drop else 1.0
            for at in (0.0, 1.75, 2.5):
                place(drums, kick0(0.46, g), T(b, at)); kicks.append(T(b, at))
            place(drums, snare(0.30, 0.95 * g, 1.0), T(b, 1))
            place(drums, snare(0.30, 0.95 * g, 1.0), T(b, 3))
            for at in (0.75, 2.25, 3.5, 3.75):
                place(drums, ghost(0.22 * g), T(b, at))
            for i in range(8):
                place(drums, hat(0.05, 0.13 if i % 2 == 0 else 0.07, open_=(i == 5)), T(b, i * 0.5))
            for at in (0.0, 1.75, 3.0):
                place(bass, subf(R, beat * 0.9, 0.78 * g), T(b, at))
            if drop:
                place(lead, stab([R * 4, R * 4.76, R * 6], beat * 0.5, 0.24, 3000, 0.30), T(b, 0.5))
                place(lead, stab([R * 3.56, R * 4.49, R * 5.33], beat * 0.5, 0.20, 3000, 0.30), T(b, 2.75))
            if b % 3 == 0:
                place(fx, sweep(bar * 0.7, 0.20, up=False), T(b, 1))
        place(fx, noise_riser(bar * 1.4, 260, 8000, 0.34), T(max(1, DROP - 1)))

    # 사이드체인 — 스타일마다 세기를 다르게
    depth = {'afro': 0.30, 'industrial': 0.34, 'garage': 0.26,
             'synthwave': 0.42, 'breaks': 0.28}[style]
    hold = 0.20 if style in ('industrial', 'garage') else 0.26
    duck = np.ones(N); tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR); j = min(N, i + int(hold * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / hold, 0, 1)
        duck[i:j] = np.minimum(duck[i:j], depth + (1 - depth) * seg ** 0.6)
    bass *= duck
    lead *= duck ** (0.45 if style == 'synthwave' else 0.85)

    mix = drums + bass + reverb(lead, 1.3, 0.28) * 0.85 + reverb(fx, 1.7, 0.32) * 0.7
    mix = hp(mix, 28, 2)
    mix = sat(mix * 0.9, 1.2 if style == 'synthwave' else 1.5)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.95
    f = int(0.3 * SR)
    mix[-f:] *= np.linspace(1, 0, f) ** 1.2
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.008 * SR)
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.95 + right * 0.05, right * 0.16 + mix * 0.84], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95, dur


def write(style):
    np.random.seed(abs(hash(style)) % 2 ** 31)
    st, d = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    import wave
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    bpm, bars = STYLES[style]
    print(f'{p}  {d:.2f}s  {bpm:.0f}BPM')
    return d


if __name__ == '__main__':
    keys = sys.argv[1:] or list(STYLES)
    for k in keys:
        write(k)
