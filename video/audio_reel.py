"""
릴스용 15초 음원 — 스타일별로 다르게 짠다.

멤버마다 결이 달라야 해서 BPM·리듬·음색을 전부 분리했다.
    festival  SEOUL     128  큰 빌드와 드롭
    techno    TECHNO    140  딱딱한 킥, 오프비트 베이스
    bounce    BOUNCE    128  통통 튀는 오프비트, 밝은 스탭
    hard      HARD      150  왜곡 킥, 리버스 베이스
    citypop   CITY POP  110  드롭 없음. 코드와 부드러운 드럼

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

# 스타일: (BPM, 마디 수)
STYLES = {
    'festival': (128.0, 8),
    'techno':   (140.0, 9),
    'bounce':   (128.0, 8),
    'hard':     (150.0, 9),
    'citypop':  (110.0, 7),
}

A1, C2, D2, E2, F2, G2, A2, C3, E3, G3 = 55.0, 65.41, 73.42, 82.41, 87.31, 98.0, 110.0, 130.81, 164.81, 196.0


def subf(freq, dur, gain=1.0):
    """주파수를 직접 받는 서브베이스 (audio.sub 는 음이름을 받아서 따로 둔다)"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    e = np.clip(t / 0.01, 0, 1) * np.exp(-t / (dur * 0.8))
    return x * e * gain


def sat(x, k=2.2):
    return np.tanh(x * k) / np.tanh(k)


def hard_kick(dur=0.34, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 48 + 240 * np.exp(-t * 42)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    return sat(body * 1.6, 4.5) * gain


def rev_bass(freq, dur, gain=1.0):
    """하드스타일 리버스 베이스"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = signal.sawtooth(2 * np.pi * freq * t)
    x = lp(x, 900)
    e = (t / dur) ** 1.6
    return sat(x * e, 2.2) * gain


def stab(freqs, dur, gain=1.0, cut=2600):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        x += signal.sawtooth(2 * np.pi * f * t) * 0.5 + np.sin(2 * np.pi * f * t) * 0.3
    x = lp(x / max(len(freqs), 1), cut)
    return x * np.exp(-t / (dur * 0.30)) * gain


def pad(freqs, dur, gain=1.0, cut=2200):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for i, f in enumerate(freqs):
        for d in (-0.004, 0.0, 0.005):
            x += np.sin(2 * np.pi * f * (1 + d) * t + i)
    x = lp(x / (len(freqs) * 3), cut)
    e = np.clip(t / 0.25, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    return x * e * gain


def soft_kick(dur=0.4, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 52 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * gain


def snare_soft(dur=0.25, gain=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bp(np.random.randn(n), 1200, 6000) * np.exp(-t * 26)
    return x * gain


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * bars
    N = int(dur * SR)
    T = lambda b, x=0.0: (b - 1) * bar + x * beat

    drums = np.zeros(N); bass = np.zeros(N); lead = np.zeros(N); fx = np.zeros(N)
    kicks = []
    DROP = bars // 2 + 1                      # 절반 지점에서 터진다

    if style == 'citypop':
        # 드롭 없음. 처음부터 끝까지 같은 결.
        chords = [[C3, E3, G3], [A2, C3, E3], [F2 * 2, A2, C3], [G2 * 2, C3, E3]]
        for b in range(1, bars + 1):
            ch = chords[(b - 1) % 4]
            place(lead, pad(ch, bar * 0.98, 0.30), T(b))
            place(bass, subf(ch[0] / 2, bar * 0.95, 0.5), T(b))
            if b >= 2:
                for x in (0, 2):
                    place(drums, soft_kick(0.4, 0.85), T(b, x)); kicks.append(T(b, x))
                for x in (1, 3):
                    place(drums, snare_soft(0.25, 0.5), T(b, x))
                for x in range(8):
                    place(drums, hat(0.05, 0.10 if x % 2 else 0.16), T(b, x * 0.5))
            if b == bars:
                place(fx, reverse_tail(bar * 0.5, 0.2), T(b, 2))
    else:
        for b in range(1, bars + 1):
            pre, drop = b < DROP, b >= DROP
            if style == 'techno':
                g = 0.8 if pre else 1.0
                for x in range(4):
                    place(drums, kick0(0.42, g), T(b, x)); kicks.append(T(b, x))
                    place(bass, stab([A1], 0.16, 0.5 if pre else 0.75, 420), T(b, x + 0.5))
                    place(drums, hat(0.05, 0.12 if pre else 0.18), T(b, x + 0.5))
                if drop:
                    place(lead, stab([A2, C3, E3], bar * 0.24, 0.30, 3200), T(b, 0))
                    place(lead, stab([A2, C3, E3], bar * 0.24, 0.24, 3200), T(b, 2.5))
            elif style == 'hard':
                for x in range(4):
                    place(drums, hard_kick(0.34, 0.9 if pre else 1.0), T(b, x)); kicks.append(T(b, x))
                    place(bass, rev_bass(A1, beat * 0.75, 0.45 if pre else 0.7), T(b, x + 0.25))
                if drop:
                    place(lead, stab([A2, E3], beat * 0.9, 0.34, 3600), T(b, 0))
                    place(lead, stab([G2 * 2, D2 * 4], beat * 0.9, 0.28, 3600), T(b, 2))
            elif style == 'bounce':
                for x in range(4):
                    place(drums, kick0(0.5, 0.85 if pre else 1.0), T(b, x)); kicks.append(T(b, x))
                    place(bass, stab([A1 * 2], 0.2, 0.55 if pre else 0.8, 900), T(b, x + 0.5))
                    place(drums, hat(0.05, 0.14), T(b, x + 0.5))
                if b % 2 == 0:
                    place(drums, clap(0.5), T(b, 1)); place(drums, clap(0.5), T(b, 3))
                if drop:
                    place(lead, stab([A2, C3, E3], beat * 0.55, 0.34, 4200), T(b, 0))
                    place(lead, stab([C3, E3, G3], beat * 0.55, 0.30, 4200), T(b, 1.5))
                    place(lead, stab([A2, C3, E3], beat * 0.55, 0.30, 4200), T(b, 2.5))
            else:  # festival
                for x in range(4):
                    place(drums, kick0(0.55, 0.85 if pre else 1.0), T(b, x)); kicks.append(T(b, x))
                    place(drums, hat(0.06, 0.12), T(b, x + 0.5))
                if b % 2 == 0:
                    place(drums, clap(0.55), T(b, 1)); place(drums, clap(0.55), T(b, 3))
                place(bass, subf(A1, bar * 0.95, 0.55 if pre else 0.8), T(b))
                if drop:
                    place(lead, supersaw([A2, C3, E3], bar * 0.5, 3400, 0.16, 0.26), T(b, 0))
                    place(lead, supersaw([G2 * 2, C3, E3], bar * 0.5, 3400, 0.16, 0.22), T(b, 2))

        # 빌드 → 드롭
        place(fx, noise_riser(bar * (DROP - 1) * 0.5, 300, 9000, 0.5), T(max(1, DROP - 2)))
        place(fx, impact(2.2, 0.9), T(DROP))
        g0, g1 = int(T(DROP, -0.5) * SR), int(T(DROP) * SR)
        if g1 > g0:
            for buf in (drums, bass, lead, fx):
                buf[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 2

    # 사이드체인
    duck = np.ones(N); tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR); j = min(N, i + int(0.22 * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / 0.22, 0, 1)
        duck[i:j] = np.minimum(duck[i:j], 0.28 + 0.72 * seg ** 0.6)
    bass *= duck
    lead *= duck ** (0.5 if style == 'citypop' else 0.85)

    mix = drums + bass + reverb(lead, 1.2, 0.26) * 0.85 + reverb(fx, 1.6, 0.3) * 0.7
    mix = hp(mix, 28, 2)
    mix = sat(mix * 0.9, 1.3 if style == 'citypop' else 1.5)
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


def reverse_tail(dur, gain=1.0):
    n = int(dur * SR)
    x = hp(np.random.randn(n), 4500)
    t = np.arange(n) / SR
    return x * (t / dur) ** 3 * gain


def write(style):
    np.random.seed(hash(style) % 2 ** 31)
    st, dur = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    import wave
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{p}  {dur:.2f}s')
    return dur


if __name__ == '__main__':
    keys = sys.argv[1:] or list(STYLES)
    for k in keys:
        write(k)
