"""
**파티모아 릴스 곡 셋.** 셋 다 지금까지 없던 음색·템포.

    python audio_partymoa.py          셋 다  →  out/partymoa/bgm_{vowel,acid,boom}.wav
    python audio_partymoa.py acid     하나만

    vowel   116BPM  개러지 셔플 위에 모음 신스. 사람 목소리처럼 들리는 포먼트
    acid    135BPM  303 같은 공진 필터 톱니. 스퀠치가 주인공
    boom    100BPM  808 서브 + 스네어. 붐뱁. 위쪽은 거의 비운다

## 안 겹치게

기존 BPM: 108 110 114 117 118 120~142 곳곳. 116 · 135 · 100 은 비어 있다.
음색도 셋 다 처음이다. 포먼트 필터, 공진 필터 스윕, 808 피치 드롭.
supersaw · pad · stab · pluck · bell · tom 은 안 쓴다.

만든 뒤 audio_check.py 로 전곡과 대조한다.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, clap, hat, kick, noise_riser, place, reverb
from audio_reel import sat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'partymoa')
os.makedirs(OUT, exist_ok=True)

STYLES = {'vowel': (116.0, 8), 'acid': (135.0, 8), 'boom': (100.0, 8)}
ROOT = {'vowel': 43.65, 'acid': 46.25, 'boom': 38.89}     # F1 · F#1 · D#1


def _n(f, semi):
    return f * 2 ** (semi / 12)


def _biquad_bp(x, f0, q):
    """2차 대역통과 한 개. 포먼트 하나."""
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * np.cos(w0), 1 - alpha
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        y[i] = (b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1 = x1, x[i]
        y2, y1 = y1, y[i]
    return y


def vowel(freq, dur, which='a', gain=1.0):
    """포먼트 신스. 톱니를 모음 대역 셋으로 걸러 목소리처럼."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    saw = 2 * ((freq * t) % 1.0) - 1
    saw += 0.5 * (2 * ((freq * 1.004 * t) % 1.0) - 1)
    F = {'a': (700, 1200, 2600), 'o': (450, 800, 2500), 'e': (400, 2000, 2800)}[which]
    y = sum(_biquad_bp(saw, f, 8.0) * g for f, g in zip(F, (1.0, 0.6, 0.25)))
    e = np.clip(t / 0.02, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return y * e * gain * 0.9


def acid(freq, dur, gain=1.0, cut0=2200, cut1=300, res=0.92, accent=False):
    """303 흉내. 톱니에 공진 필터를 걸고 컷오프를 급히 내린다."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    saw = 2 * ((freq * t) % 1.0) - 1
    cut = cut1 + (cut0 - cut1) * np.exp(-t * (14 if accent else 22))
    # 한 극짜리 공진 필터를 샘플마다 돌린다 (체임벌린 SVF)
    lp = bp = 0.0
    y = np.zeros(n, np.float32)
    for i in range(n):
        f = 2 * np.sin(np.pi * min(cut[i], SR * 0.45) / SR)
        q = 1 - res
        hpv = saw[i] - lp - q * bp
        bp += f * hpv
        lp += f * bp
        y[i] = lp
    e = np.clip(t / 0.005, 0, 1) * np.exp(-t / (dur * 0.9))
    return sat(y * e, 2.6) * gain * (1.3 if accent else 1.0)


def eight08(freq, dur, gain=1.0):
    """808. 피치가 뚝 떨어지고 길게 운다."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1 + 3.0 * np.exp(-t * 28))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x = sat(x * 1.6, 1.8)
    e = np.clip(t / 0.004, 0, 1) * np.exp(-t / (dur * 0.7))
    return x * e * gain


def snare(dur=0.22, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(5)
    noise = rng.standard_normal(n).astype(np.float32)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    e = np.exp(-t * 18)
    return (noise * e * 0.7 + body * 0.6) * gain


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    total = bars * 4 * beat
    buf = np.zeros(int(SR * (total + 2.5)), np.float32)
    R = ROOT[style]
    at = lambda bar, b: (bar * 4 + b) * beat

    if style == 'vowel':
        # 2스텝 셔플. 킥은 1·2.5·3, 박수는 2·4. 모음이 멜로디를 부른다
        seq = [(0, 'a', 0.0), (7, 'o', 1.0), (5, 'e', 1.75), (3, 'a', 2.5), (7, 'o', 3.25)]
        for bar in range(bars):
            for b in (0, 1.5, 2.0, 3.0):
                place(buf, kick(0.42, 0.8), at(bar, b))
            place(buf, clap(0.5), at(bar, 1))
            place(buf, clap(0.5), at(bar, 3))
            if bar >= 1:
                for k in range(8):
                    place(buf, hat(0.05, 0.16 if k % 2 else 0.09), at(bar, k * 0.5 + 0.25))
            if bar >= 1:
                for semi, v, off in seq:
                    place(buf, vowel(_n(R * 4, semi), beat * 0.7, v, 0.55 if bar >= 3 else 0.4),
                          at(bar, off))
            if bar >= 2:
                place(buf, eight08(R, beat * 1.2, 0.5), at(bar, 0))
                place(buf, eight08(_n(R, 5), beat * 0.8, 0.45), at(bar, 2.5))
        buf = reverb(buf, 1.0, 0.16)

    elif style == 'acid':
        pat = [(0, 0.0, 0), (0, 0.5, 0), (12, 1.0, 1), (0, 1.5, 0), (3, 2.0, 0),
               (0, 2.5, 0), (7, 3.0, 1), (5, 3.5, 0)]
        for bar in range(bars):
            for b in range(4):
                place(buf, kick(0.48, 0.95 if bar >= 1 else 0.6), at(bar, b))
            if bar >= 1:
                for b in range(4):
                    place(buf, hat(0.08, 0.22, open_=True), at(bar, b + 0.5))
            for semi, off, acc in pat:
                if bar == 0 and off > 2:
                    continue
                g = 0.5 if bar >= 2 else 0.32
                place(buf, acid(_n(R * 2, semi), beat * 0.48, g, accent=bool(acc)), at(bar, off))
            if bar >= 3:
                place(buf, clap(0.5), at(bar, 1))
                place(buf, clap(0.5), at(bar, 3))
            if bar == 3:
                place(buf, noise_riser(beat * 4, 300, 8000, 0.35), at(bar, 0))
        buf = reverb(buf, 0.8, 0.12)

    else:  # boom
        for bar in range(bars):
            for off, ln in ((0, 1.4), (1.75, 0.6), (2.5, 1.2)):
                place(buf, eight08(R, beat * ln, 0.95 if bar >= 1 else 0.6), at(bar, off))
            if bar >= 1:
                place(buf, snare(0.24, 0.9), at(bar, 1))
                place(buf, snare(0.24, 0.9), at(bar, 3))
            for k in range(8):
                place(buf, hat(0.05, 0.14 if k % 2 else 0.08), at(bar, k * 0.5))
            if bar >= 2:
                # 한 옥타브 위 808 을 짧게. 멜로디 대신
                place(buf, eight08(_n(R * 2, 3), beat * 0.5, 0.35), at(bar, 1.5))
                place(buf, eight08(_n(R * 2, 0), beat * 0.5, 0.35), at(bar, 3.5))
            if bar >= 4:
                place(buf, kick(0.3, 0.5), at(bar, 2.25))
        buf = reverb(buf, 0.6, 0.08)

    buf = buf[:int(SR * total)]
    n = int(SR * beat)
    buf[-n:] *= np.linspace(1, 0, n)
    m = np.max(np.abs(buf)) or 1.0
    return (buf / m * 0.89).astype(np.float32)


def write(style):
    x = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    bpm, bars = STYLES[style]
    print(f'{p}  {len(x)/SR:.2f}s  {bpm:.0f}BPM')


if __name__ == '__main__':
    for s in (sys.argv[1:] or list(STYLES)):
        write(s)
