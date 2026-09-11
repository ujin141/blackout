"""
**파티모아 릴스 두 번째 세트 곡 셋.** 사진 릴스용. 앞의 셋(vowel·acid·boom)과 다르게.

    python audio_partymoa2.py          →  out/partymoa/bgm_{organ,epiano,dub}.wav
    python audio_partymoa2.py dub

    organ    124BPM  하우스 오르간. 드로바 사인 합. 4/4 킥 + 오프비트 하이햇
    epiano   128BPM  FM 일렉피아노 코드 + 브레이크비트 스네어
    dub      140BPM  하프타임 더브 테크노. 필터 코드에 딜레이, 킥은 느리게

## 안 겹치게

앞 세트가 116 · 135 · 100. 여기는 124 · 128 · 140. 음색은 오르간(사인 합),
FM 이피, 딜레이 코드 — 셋 다 이 폴더에서 처음이다. 만든 뒤 audio_check.py.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, clap, hat, kick, lp, noise_riser, place, reverb
from audio_reel import sat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'partymoa')
os.makedirs(OUT, exist_ok=True)

STYLES = {'organ': (124.0, 8), 'epiano': (128.0, 8), 'dub': (140.0, 8), 'garage': (132.0, 8)}
ROOT = {'organ': 55.0, 'epiano': 49.0, 'dub': 41.2, 'garage': 58.3}   # A1 · G1 · E1 · Bb1


def _n(f, semi):
    return f * 2 ** (semi / 12)


def _env(n, a, d, s=0.0, r=0.05):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.clip(t / max(a, 1e-4), 0, 1)
    e *= np.where(t < dur - r, np.maximum(s, np.exp(-t / max(d, 1e-4))), 0)
    tail = np.clip((dur - t) / r, 0, 1)
    return e * tail


def organ(freq, dur, gain=1.0):
    """드로바 오르간. 배음을 사인으로 쌓는다. 88 8000 000 쯤."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    bars = [(0.5, 1.0), (1.0, 0.85), (2.0, 0.6), (3.0, 0.25), (4.0, 0.3)]
    y = sum(np.sin(2 * np.pi * freq * m * t + 0.3 * k) * g for k, (m, g) in enumerate(bars))
    # 키클릭
    y += np.random.default_rng(int(freq)).standard_normal(n) * np.exp(-t * 900) * 0.4
    # 레슬리 흉내. 느린 진폭·피치 흔들림
    y *= 1 + 0.08 * np.sin(2 * np.pi * 6.2 * t)
    return y * _env(n, 0.004, 9.0, 0.9, 0.03) * gain * 0.28


def chord_organ(root, semis, dur, gain=1.0):
    return sum(organ(_n(root, s), dur, gain) for s in semis)


def epiano(freq, dur, gain=1.0, bright=1.0):
    """FM 이피. 캐리어:모듈레이터 1:14 로 틴 소리, 빨리 죽는다."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    idx = (2.6 * bright) * np.exp(-t * 6) + 0.15
    mod = np.sin(2 * np.pi * freq * 14 * t) * idx
    y = np.sin(2 * np.pi * freq * t + mod)
    y += 0.35 * np.sin(2 * np.pi * freq * 2 * t + mod * 0.4)
    y *= 1 + 0.05 * np.sin(2 * np.pi * 5.5 * t)
    return y * _env(n, 0.002, 1.1, 0.0, 0.05) * gain * 0.5


def chord_ep(root, semis, dur, gain=1.0, bright=1.0):
    return sum(epiano(_n(root, s), dur, gain, bright) for s in semis)


def dub_chord(root, semis, dur, gain=1.0, cut=900):
    """더브 코드. **펄스파**(속 빈 소리)를 쌓고 컷오프를 열었다 닫는다.
    톱니로 했더니 open2 와 음색이 0.99 로 겹쳤다. 파형을 바꾼다."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for k, s in enumerate(semis):
        f = _n(root, s)
        pw = 0.18 + 0.06 * k
        y += np.where(((f * t) % 1.0) < pw, 1.0, -1.0)
        y += 0.5 * np.where(((f * 1.006 * t) % 1.0) < pw, 1.0, -1.0)
    # 컷오프가 짧게 열렸다 닫힌다 — 와우
    sweep = cut * (0.4 + 1.6 * np.exp(-t * 18))
    out = np.zeros(n, np.float32)
    step = 256
    for i in range(0, n, step):
        seg = y[i:i + step]
        out[i:i + step] = lp(np.concatenate([y[max(0, i - 64):i], seg]), float(sweep[i]), 2)[-len(seg):]
    return out * _env(n, 0.004, 0.16, 0.0, 0.03) * gain * 0.2


def delay(buf, time, fb=0.5, mix=0.45, cut=2500):
    d = int(SR * time)
    out = buf.copy()
    wet = np.zeros_like(buf)
    x = buf.copy()
    g = 1.0
    for _ in range(6):
        x = np.concatenate([np.zeros(d, np.float32), lp(x, cut, 1)[:-d]]).astype(np.float32)
        g *= fb
        wet += x * g
    return out + wet * mix


def snare_break(dur=0.2, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(11)
    noise = rng.standard_normal(n).astype(np.float32)
    body = np.sin(2 * np.pi * 210 * t) * np.exp(-t * 34)
    return sat((noise * np.exp(-t * 22) * 0.8 + body * 0.5) * gain, 1.8)


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    total = bars * 4 * beat
    buf = np.zeros(int(SR * (total + 3.0)), np.float32)
    R = ROOT[style]
    at = lambda bar, b: (bar * 4 + b) * beat

    if style == 'organ':
        # 4/4 하우스. 코드는 Am7 → Fmaj7 → G6 → Am7. 마디마다 한 번, 뒤 반박에 스탭
        prog = [(0, (0, 3, 7, 10)), (-4, (0, 4, 7, 11)), (-2, (0, 4, 7, 9)), (0, (0, 3, 7, 10))]
        for bar in range(bars):
            root, semis = prog[bar % 4]
            for b in range(4):
                place(buf, kick(0.5, 0.95 if bar >= 1 else 0.7), at(bar, b))
            if bar >= 1:
                for b in range(4):
                    place(buf, hat(0.09, 0.2, open_=True), at(bar, b + 0.5))
                place(buf, clap(0.45), at(bar, 1))
                place(buf, clap(0.45), at(bar, 3))
            g = 0.9 if bar >= 2 else 0.6
            place(buf, chord_organ(_n(R * 4, root), semis, beat * 1.4, g), at(bar, 0))
            place(buf, chord_organ(_n(R * 4, root), semis, beat * 0.45, g * 0.8), at(bar, 1.5))
            place(buf, chord_organ(_n(R * 4, root), semis, beat * 0.45, g * 0.8), at(bar, 2.5))
            if bar >= 3:
                place(buf, chord_organ(_n(R * 8, root), semis[:2], beat * 0.3, 0.5), at(bar, 3.5))
            # 베이스. 사인 서브
            for b in (0, 1.5, 2.5, 3.0):
                n = int(SR * beat * 0.5)
                t = np.arange(n) / SR
                place(buf, np.sin(2 * np.pi * _n(R, root) * t) * _env(n, 0.005, 0.4, 0.2) * 0.7, at(bar, b))
            if bar == 3:
                place(buf, noise_riser(beat * 4, 400, 6000, 0.25), at(bar, 0))
        buf = reverb(buf, 0.9, 0.14)

    elif style == 'epiano':
        # 브레이크비트. 킥 1·2.75, 스네어 2·4, 고스트 스네어. 이피 코드는 2·4 뒤
        prog = [(0, (0, 4, 7, 11)), (5, (0, 3, 7, 10)), (7, (0, 4, 7, 10)), (2, (0, 3, 7, 10))]
        for bar in range(bars):
            root, semis = prog[bar % 4]
            for b in (0, 2.75):
                place(buf, kick(0.4, 0.9 if bar >= 1 else 0.6), at(bar, b))
            if bar >= 1:
                place(buf, snare_break(0.2, 0.9), at(bar, 1))
                place(buf, snare_break(0.2, 0.9), at(bar, 3))
                place(buf, snare_break(0.12, 0.35), at(bar, 1.75))
                place(buf, snare_break(0.12, 0.3), at(bar, 3.25))
                for k in range(8):
                    place(buf, hat(0.05, 0.14 if k % 2 else 0.08), at(bar, k * 0.5))
            g = 0.8 if bar >= 2 else 0.55
            place(buf, chord_ep(_n(R * 4, root), semis, beat * 1.2, g, 1.0), at(bar, 0.5))
            place(buf, chord_ep(_n(R * 4, root), semis, beat * 0.8, g * 0.7, 0.7), at(bar, 2.5))
            if bar >= 4:
                place(buf, epiano(_n(R * 8, root + semis[2]), beat * 0.4, 0.4, 1.4), at(bar, 3.5))
            # 서브
            for b in (0, 2.75):
                n = int(SR * beat * 0.9)
                t = np.arange(n) / SR
                place(buf, np.sin(2 * np.pi * _n(R, root) * t) * _env(n, 0.004, 0.5, 0.15) * 0.75, at(bar, b))
        buf = reverb(buf, 0.7, 0.10)

    elif style == 'garage':
        # 2스텝. 킥 1·2.5, 스네어 2·4, 하이햇 셔플. 오르간 스탭이 뒤박에, 이피가 답한다
        prog = [(0, (0, 4, 7, 11)), (-3, (0, 3, 7, 10)), (5, (0, 4, 7, 11)), (-5, (0, 4, 7, 10))]
        for bar in range(bars):
            root, semis = prog[bar % 4]
            for b in (0, 2.5):
                place(buf, kick(0.4, 0.9 if bar >= 1 else 0.6), at(bar, b))
            if bar >= 1:
                place(buf, snare_break(0.16, 0.7), at(bar, 1))
                place(buf, snare_break(0.16, 0.7), at(bar, 3))
                for k in range(8):
                    off = k * 0.5 + (0.08 if k % 2 else 0)
                    place(buf, hat(0.05, 0.16 if k % 2 else 0.09), at(bar, off))
            g = 0.75 if bar >= 2 else 0.5
            place(buf, chord_organ(_n(R * 4, root), semis[:3], beat * 0.3, g), at(bar, 0.75))
            place(buf, chord_organ(_n(R * 4, root), semis[:3], beat * 0.3, g), at(bar, 1.75))
            place(buf, chord_organ(_n(R * 4, root), semis[:3], beat * 0.3, g * 0.8), at(bar, 3.25))
            if bar >= 2:
                place(buf, epiano(_n(R * 8, root + semis[1]), beat * 0.5, 0.35, 1.2), at(bar, 2.75))
            for b in (0, 1.5, 2.5):
                n = int(SR * beat * 0.6)
                t = np.arange(n) / SR
                place(buf, np.sin(2 * np.pi * _n(R, root) * t) * _env(n, 0.004, 0.45, 0.15) * 0.75, at(bar, b))
            if bar == 3:
                place(buf, noise_riser(beat * 4, 400, 7000, 0.22), at(bar, 0))
        buf = reverb(buf, 0.8, 0.12)

    else:  # dub — 하프타임. 킥 1·2.5, 스네어 3 하나. 코드는 1.75·3.5 에 딜레이
        semis = (0, 3, 7, 10)
        chords = np.zeros_like(buf)
        for bar in range(bars):
            root = 0 if bar % 4 < 2 else -2
            place(buf, kick(0.6, 1.0 if bar >= 1 else 0.7), at(bar, 0))
            place(buf, kick(0.5, 0.8 if bar >= 1 else 0.5), at(bar, 1.5))
            if bar >= 1:
                place(buf, snare_break(0.26, 0.8), at(bar, 2))
                for k in range(8):
                    if k % 2:
                        place(buf, hat(0.05, 0.1), at(bar, k * 0.5))
                place(buf, hat(0.12, 0.16, open_=True), at(bar, 3.5))
            g = 0.9 if bar >= 2 else 0.6
            place(chords, dub_chord(_n(R * 4, root), semis, beat * 0.4, g), at(bar, 0.75))
            place(chords, dub_chord(_n(R * 4, root), semis, beat * 0.4, g * 0.85), at(bar, 2.5))
            if bar >= 3:
                place(chords, dub_chord(_n(R * 4, root), semis, beat * 0.25, g * 0.6, 1600), at(bar, 3.25))
            if bar >= 4:
                # 사인 핑. 높은 데서 한 번, 딜레이가 물고 간다
                n2 = int(SR * beat * 0.3)
                t2 = np.arange(n2) / SR
                place(chords, np.sin(2 * np.pi * _n(R * 16, root + 7) * t2) * _env(n2, 0.002, 0.15) * 0.3, at(bar, 1.25))
            # 깊은 서브. 마디 첫 박에 길게
            n = int(SR * beat * 1.8)
            t = np.arange(n) / SR
            place(buf, np.sin(2 * np.pi * _n(R, root) * t) * _env(n, 0.01, 1.2, 0.3) * 0.85, at(bar, 0))
            if bar == 3:
                place(buf, noise_riser(beat * 4, 200, 5000, 0.2), at(bar, 0))
        chords = delay(chords, beat * 0.75, 0.55, 0.6, 2200)
        buf += chords
        buf = reverb(buf, 1.6, 0.22)

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
