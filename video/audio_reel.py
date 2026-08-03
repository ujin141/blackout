"""
릴스용 15초 음원 — 스타일별로 리듬 골격을 다르게 짠다.

BPM만 바꾸면 다 비슷하게 들린다. 실제로 다르게 들리려면
킥 외의 것(하이햇 분할, 스네어 위치, 베이스 싱코페이션, 음색)이 달라야 한다.

    festival  SEOUL     128  4온플로어 + 클랩 2·4 + 2마디마다 스네어 필. 넓은 코드
    techno    TECHNO    145  클랩 없음. 16분 하이햇이 계속 구르고 금속 퍼커션
    bounce    BOUNCE    132  오프비트 베이스가 주인공. 스탭이 엇박으로 튄다
    hard      HARD      155  하프타임 스네어(3박) + 박 사이를 채우는 리버스 베이스
    citypop   CITY POP  105  킥 1·3, 셔플 하이햇, 걸어다니는 베이스. 드롭 없음

python audio_reel.py           전부
python audio_reel.py techno    하나만
"""
import os
import sys
import numpy as np
from scipy import signal
from audio import (SR, place, lp, hp, bp, reverb,
                   kick as kick0, supersaw, noise_riser, impact, clap, hat)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'reel')
os.makedirs(OUT, exist_ok=True)

# 스타일: (BPM, 마디 수) — 템포 간격도 넓혔다
STYLES = {
    'festival': (128.0, 8),
    'techno':   (145.0, 9),
    'bounce':   (132.0, 8),
    'hard':     (155.0, 10),
    'citypop':  (105.0, 7),
}

# 스타일마다 조성을 다르게 (같은 조면 비슷하게 들린다)
ROOT = {'festival': 55.00,   # A
        'techno':   61.74,   # B
        'bounce':   65.41,   # C
        'hard':     58.27,   # A#
        'citypop':  73.42}   # D


def subf(freq, dur, gain=1.0, decay=0.8):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    e = np.clip(t / 0.01, 0, 1) * np.exp(-t / (dur * decay))
    return x * e * gain


def sat(x, k=2.2):
    return np.tanh(x * k) / np.tanh(k)


def hard_kick(dur=0.42, gain=1.0):
    """하드스타일 킥 — 왜곡되고 꼬리가 길다"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 46 + 260 * np.exp(-t * 46)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.0)
    return sat(body * 1.9, 5.0) * gain


def rev_bass(freq, dur, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = signal.sawtooth(2 * np.pi * freq * t)
    x = lp(x, 800)
    return sat(x * (t / dur) ** 1.5, 2.4) * gain


def stab(freqs, dur, gain=1.0, cut=2600, decay=0.30):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        x += signal.sawtooth(2 * np.pi * f * t) * 0.5 + np.sin(2 * np.pi * f * t) * 0.3
    x = lp(x / max(len(freqs), 1), cut)
    return x * np.exp(-t / (dur * decay)) * gain


def metal(dur=0.14, gain=1.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (1320, 1980, 2710, 3840, 5300):
        x += np.sin(2 * np.pi * f * (1 + rng.random() * 0.05) * t) / 5
    x += hp(rng.standard_normal(n), 5000) * 0.3
    return x * np.exp(-t * (26 / dur)) * gain


def snare(dur=0.3, gain=1.0, tight=1.0, body=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = bp(np.random.randn(n), 1400, 7800) * np.exp(-t * (30 * tight))
    tone = (np.sin(2 * np.pi * 186 * t) + np.sin(2 * np.pi * 338 * t) * 0.6)
    tone *= np.exp(-t * (44 * tight)) * 0.45 * body
    return sat(nz * 0.9 + tone, 1.8) * gain


def brush(dur=0.26, gain=1.0):
    """시티팝용 부드러운 스네어"""
    n = int(dur * SR); t = np.arange(n) / SR
    return bp(np.random.randn(n), 900, 5200) * np.exp(-t * 20) * gain


def soft_kick(dur=0.42, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 50 + 80 * np.exp(-t * 26)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * gain


def pad(freqs, dur, gain=1.0, cut=2400):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for i, f in enumerate(freqs):
        for d in (-0.004, 0.0, 0.005):
            x += np.sin(2 * np.pi * f * (1 + d) * t + i)
    x = lp(x / (len(freqs) * 3), cut)
    e = np.clip(t / 0.3, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    return x * e * gain


def rev_tail(dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return hp(np.random.randn(n), 4500) * (t / dur) ** 3 * gain


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

    # ── CITY POP — 킥 1·3, 셔플 하이햇, 걸어다니는 베이스 ──
    if style == 'citypop':
        prog = [[R * 4, R * 5, R * 6], [R * 3.36, R * 4, R * 5],
                [R * 2.67, R * 3.36, R * 4], [R * 3, R * 4, R * 5]]
        walk = [1.0, 1.5, 2.0, 1.5]
        for b in range(1, bars + 1):
            ch = prog[(b - 1) % 4]
            place(lead, pad(ch, bar * 0.98, 0.30), T(b))
            for i, mul in enumerate(walk):                 # 베이스가 박마다 움직인다
                place(bass, subf(R * mul, beat * 0.9, 0.42, 0.55), T(b, i))
            if b >= 2:
                place(drums, soft_kick(0.42, 0.9), T(b, 0)); kicks.append(T(b, 0))
                place(drums, soft_kick(0.42, 0.8), T(b, 2)); kicks.append(T(b, 2))
                place(drums, brush(0.26, 0.55), T(b, 1))
                place(drums, brush(0.26, 0.55), T(b, 3))
                for i in range(4):                          # 셔플: 8분을 2:1로 민다
                    place(drums, hat(0.05, 0.16), T(b, i))
                    place(drums, hat(0.05, 0.09), T(b, i + 0.66))
            if b == bars:
                place(fx, rev_tail(bar * 0.5, 0.2), T(b, 2))

    else:
        for b in range(1, bars + 1):
            pre, drop = b < DROP, b >= DROP
            g = 0.82 if pre else 1.0

            # ── TECHNO — 클랩 없음. 16분 하이햇이 계속 구른다 ──
            if style == 'techno':
                for x in range(4):
                    place(drums, kick0(0.40, g), T(b, x)); kicks.append(T(b, x))
                for i in range(16):                          # 16분 하이햇
                    a = 0.16 if i % 4 == 2 else 0.07
                    place(drums, hat(0.04, a * (1.0 if drop else 0.7)), T(b, i * 0.25))
                for x in range(4):                           # 오프비트 서브 스탭
                    place(bass, stab([R], 0.14, 0.55 if pre else 0.8, 380, 0.22), T(b, x + 0.5))
                for i in (1, 3):                             # 금속 퍼커션
                    place(drums, metal(0.13, 0.22 if pre else 0.32, b * 4 + i), T(b, i + 0.75))
                if drop:
                    place(lead, stab([R * 4, R * 4.76, R * 6], bar * 0.22, 0.28, 3400, 0.35), T(b, 0))
                    place(lead, stab([R * 4, R * 4.76, R * 6], bar * 0.22, 0.22, 3400, 0.35), T(b, 2.5))

            # ── HARD — 하프타임 스네어 + 박 사이 리버스 베이스 ──
            elif style == 'hard':
                for x in range(4):
                    place(drums, hard_kick(0.42, g), T(b, x)); kicks.append(T(b, x))
                    place(bass, rev_bass(R, beat * 0.62, 0.5 if pre else 0.78), T(b, x + 0.38))
                place(drums, snare(0.30, 0.85 if pre else 1.0, 1.1), T(b, 2))   # 3박에만
                if drop and b % 2 == 0:
                    place(drums, snare(0.22, 0.5, 1.6), T(b, 3.5))
                if drop:
                    place(lead, stab([R * 6, R * 8], beat * 0.8, 0.30, 4200, 0.25), T(b, 0))
                    place(lead, stab([R * 5.33, R * 8], beat * 0.8, 0.24, 4200, 0.25), T(b, 2))

            # ── BOUNCE — 오프비트 베이스가 주인공, 스탭은 엇박 ──
            elif style == 'bounce':
                for x in range(4):
                    place(drums, kick0(0.46, g), T(b, x)); kicks.append(T(b, x))
                    place(bass, stab([R * 2], 0.19, 0.7 if pre else 0.95, 1100, 0.24), T(b, x + 0.5))
                    place(drums, hat(0.045, 0.13), T(b, x + 0.5))
                place(drums, clap(0.55), T(b, 1)); place(drums, clap(0.55), T(b, 3))
                if drop:                                     # 1 · 1&3/4 · 2& · 3&1/4 로 튄다
                    for at, gg in ((0.0, 0.34), (0.75, 0.26), (1.5, 0.30), (2.25, 0.24), (3.0, 0.28)):
                        place(lead, stab([R * 4, R * 5, R * 6], beat * 0.42, gg, 4400, 0.22), T(b, at))

            # ── FESTIVAL — 4온플로어 + 2마디마다 스네어 필 ──
            else:
                for x in range(4):
                    place(drums, kick0(0.55, g), T(b, x)); kicks.append(T(b, x))
                    place(drums, hat(0.06, 0.10), T(b, x + 0.5))
                place(drums, clap(0.6), T(b, 1)); place(drums, clap(0.6), T(b, 3))
                place(bass, subf(R, bar * 0.95, 0.6 if pre else 0.85), T(b))
                if b % 2 == 0:                               # 두 마디마다 스네어 필
                    for i in range(4):
                        place(drums, snare(0.18, 0.22 + i * 0.10, 1.5), T(b, 3 + i * 0.25))
                if drop:
                    ch = [[R * 4, R * 4.76, R * 6], [R * 3.56, R * 4.76, R * 6]][(b - DROP) % 2]
                    place(lead, supersaw(ch, bar * 0.5, 3600, 0.16, 0.26), T(b, 0))
                    place(lead, supersaw(ch, bar * 0.5, 3600, 0.16, 0.20), T(b, 2))

        place(fx, noise_riser(bar * max(1, DROP - 2), 300, 9000, 0.5), T(max(1, DROP - 2)))
        place(fx, impact(2.2, 0.9), T(DROP))
        g0, g1 = int(T(DROP, -0.5) * SR), int(T(DROP) * SR)
        if g1 > g0:
            for buf in (drums, bass, lead, fx):
                buf[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 2

    # 사이드체인 — 스타일마다 세기를 다르게
    depth = {'festival': 0.26, 'techno': 0.34, 'bounce': 0.22, 'hard': 0.30, 'citypop': 0.55}[style]
    duck = np.ones(N); tt = np.arange(N) / SR
    hold = 0.24 if style in ('festival', 'bounce') else 0.18
    for at in kicks:
        i = int(at * SR); j = min(N, i + int(hold * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / hold, 0, 1)
        duck[i:j] = np.minimum(duck[i:j], depth + (1 - depth) * seg ** 0.6)
    bass *= duck
    lead *= duck ** (0.4 if style == 'citypop' else 0.85)

    mix = drums + bass + reverb(lead, 1.2, 0.26) * 0.85 + reverb(fx, 1.6, 0.3) * 0.7
    mix = hp(mix, 28, 2)
    mix = sat(mix * 0.9, 1.25 if style == 'citypop' else 1.5)
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
    st, dur = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    import wave
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    bpm, bars = STYLES[style]
    print(f'{p}  {dur:.2f}s  {bpm:.0f}BPM')
    return dur


if __name__ == '__main__':
    keys = sys.argv[1:] or list(STYLES)
    for k in keys:
        write(k)
