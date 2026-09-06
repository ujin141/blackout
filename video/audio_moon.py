"""
**AFTER MOON 릴스 곡 — 지금까지 없던 음색으로.**

    python audio_moon.py   →  out/moon/bgm_bell.wav   114BPM · 8마디 · 16.8초

## 왜 종소리인가

지금까지 만든 곡의 주인공은 supersaw · pad · stab(모션·포스터 시리즈),
pluck · perc · bass(reel4) 다. 여기서는 **FM 종**을 세운다 — 반송파에
변조파를 3.5배로 걸고 변조 깊이를 빠르게 줄이면 유리종 소리가 난다.
이 라이브러리에 없던 소리라, 나는 순간 다른 곡으로 들린다.

달 파티라 종이 맞기도 하다.

## 안 겹치게

    BPM   114. 기존은 108 · 110 · 117 · 118 · 120~142 다
    조    D 단조. 기존 곡은 A · G · E 뿌리였다
    악기  supersaw · pad · stab · pluck · tom · conga 전부 안 쓴다

만든 뒤 audio_check.py 로 스무 곡 전부와 대조한다.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, clap, hat, kick, noise_riser, place, reverb, reverse_cymbal
from audio_reel import subf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'moon')
os.makedirs(OUT, exist_ok=True)

BPM, BARS = 114.0, 8
ROOT = 36.71                                     # D1


def _n(f, semi):
    return f * 2 ** (semi / 12)


def bell(freq, dur, gain=1.0, ratio=3.5, index=2.6):
    """FM 종. 변조 깊이가 빨리 죽어서 처음만 금속성이고 뒤는 맑다."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    idx = index * np.exp(-t * 9.0)
    mod = np.sin(2 * np.pi * freq * ratio * t) * idx
    x = np.sin(2 * np.pi * freq * t + mod)
    x += 0.35 * np.sin(2 * np.pi * freq * 2.0 * t + mod * 0.5)
    e = np.clip(t / 0.004, 0, 1) * np.exp(-t / (dur * 0.42))
    return x * e * gain * 0.5


def shimmer(freq, dur, gain=1.0):
    """종의 한 옥타브 위를 아주 작게. 공기가 생긴다."""
    return bell(freq * 2, dur, gain * 0.35, ratio=2.0, index=1.2)


def build():
    beat = 60.0 / BPM
    total = BARS * 4 * beat
    buf = np.zeros(int(SR * (total + 2.5)), np.float32)
    at = lambda bar, b: (bar * 4 + b) * beat

    # D 단조 펜타토닉 위의 아르페지오. 여덟 개가 한 마디를 돈다
    seq = [0, 3, 7, 10, 12, 10, 7, 3]
    R4 = ROOT * 8                                # D4

    for bar in range(BARS):
        # ── 종. 1마디는 홀로, 그 뒤로는 킥 위에서 ──
        for i, semi in enumerate(seq):
            if bar == 0 and i % 2:
                continue                         # 첫 마디는 반만. 들어오는 느낌
            g = 0.30 if bar < 2 else 0.40
            place(buf, bell(_n(R4, semi), beat * 1.6, g), at(bar, i * 0.5))
        if bar >= 4:
            for i, semi in enumerate(seq[::2]):
                place(buf, shimmer(_n(R4, semi + 12), beat * 1.2, 0.5),
                      at(bar, i * 1.0 + 0.25))

        # ── 리듬. 2마디부터 킥, 3마디부터 박수, 4마디부터 하이햇 ──
        if bar >= 1:
            for b in range(4):
                place(buf, kick(0.50, 0.85), at(bar, b))
            place(buf, subf(ROOT * 2, beat * 3.6, 0.55), at(bar, 0))
        if bar >= 2:
            place(buf, clap(0.55), at(bar, 1))
            place(buf, clap(0.55), at(bar, 3))
        if bar >= 3:
            for k in range(8):
                place(buf, hat(0.06, 0.20 if k % 2 else 0.12), at(bar, k * 0.5 + 0.5))

        # ── 마디 넷 끝에서 올라간다 ──
        if bar == 3:
            place(buf, noise_riser(beat * 4, 400, 7000, 0.35), at(bar, 0))
            place(buf, reverse_cymbal(beat * 3, 0.4), at(bar, 1))

    buf = reverb(buf, 1.6, 0.22)
    buf = buf[:int(SR * total)]
    n = int(SR * beat)
    buf[-n:] *= np.linspace(1, 0, n)
    m = np.max(np.abs(buf)) or 1.0
    return (buf / m * 0.89).astype(np.float32)


def write():
    x = build()
    p = os.path.join(OUT, 'bgm_bell.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    print(f'{p}  {len(x)/SR:.2f}s  {BPM:.0f}BPM  {BARS*4}박')
    return p


if __name__ == '__main__':
    write()
