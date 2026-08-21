"""
**라인업 릴스 전용 곡.** 기존 열몇 곡과 안 겹치게 새로 만든다.

    python audio_lineup.py   →  out/lineup/bgm_lineup.wav   120BPM · 10마디 · 20초

## 안 겹치게 하는 법

`audio_reel4` 가 정리해 둔 대로다 — **BPM 과 음색만 바꾸면 같은 곡으로
들린다.** 주인공 악기를 갈아야 한다.

    이미 쓴 것   pluck · perc · bass · supersaw · pad · stab
    여기서       **필터가 계속 움직이는 코드 + 사이드체인**

기존 `pad` 는 가만히 깔려 있다. 이건 컷오프가 8마디에 걸쳐 400Hz 에서
6kHz 까지 열리고, 킥이 올 때마다 눌린다(사이드체인). 같은 코드를 써도
**소리가 계속 변해서** 다른 곡으로 들린다.

BPM 도 안 쓴 값을 골랐다. 기존이 108·110·117·118·121·122·124·126·128·
130·132·133·136·138·142 라 **120** 을 쓴다 — 하우스 기본값이고,
라인업을 하나씩 넘기는 데 2초/마디가 딱 맞는다.

## 구성

    마디 0~1   필터 닫힌 코드와 하이햇만. 릴스 첫 1초가 조용해야 자막이 읽힌다
    마디 2~7   킥 · 베이스 · 아르페지오. DJ 가 한 마디에 한 명씩 넘어간다
    마디 8~9   필터 개방 + 클랩. 행사 정보가 앉는 자리
"""
import os
import wave

import numpy as np

from audio import SR, env_ad, lp, hp, kick, hat, clap, reverb, noise_riser
from audio_reel import sat, subf
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'lineup')
os.makedirs(OUT, exist_ok=True)

BPM = 120.0
# **곡 길이를 사람 수에서 뽑는다.** 10 으로 박아 뒀다가 XANTHIC 이
# 라인업에 들어오면서 한 마디가 모자랐다
BARS = 2 + len(EV.LINEUP) + 1
BEAT = 60.0 / BPM                     # 0.5초
BAR = BEAT * 4                        # 2.0초
DUR = BAR * BARS                      # 타이틀 2 + DJ + 아웃트로 1

# Am7 → Fmaj7 → Cmaj7 → G. 라인업이 넘어가는 동안 도는 네 코드다.
# **단조로 시작해 장조로 푼다** — 마지막 마디가 정보 자리라 열려야 한다
CHORDS = [[220.00, 261.63, 329.63, 392.00],
          [174.61, 220.00, 261.63, 329.63],
          [261.63, 329.63, 392.00, 493.88],
          [196.00, 246.94, 293.66, 392.00]]
BASS = [55.00, 43.65, 65.41, 49.00]   # A1 · F1 · C2 · G1


def at(bar, beat=0.0):
    return int((bar * BAR + beat * BEAT) * SR)


def put(buf, sig, i):
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def saw(freq, n, detune=0.008):
    """톱니 세 겹. 코드용이라 살짝만 벌린다."""
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, np.float32)
    for d in (-detune, 0.0, detune):
        ph = (t * freq * (1 + d)) % 1.0
        out += (2 * ph - 1)
    return out / 3


def chord(freqs, n, cut):
    """코드 한 덩어리. **컷오프를 밖에서 받는다** — 마디마다 열리게 하려고."""
    x = np.zeros(n, np.float32)
    for f in freqs:
        x += saw(f, n)
    x /= len(freqs)
    x = lp(x, cut)
    e = np.minimum(1.0, np.arange(n) / (SR * 0.03))          # 어택만 부드럽게
    e *= np.clip(1.0 - np.arange(n) / n, 0, 1) ** 0.25
    return x * e


def duck(buf, hits, depth=0.72, hold=0.30):
    """사이드체인. **킥마다 눌렀다 푼다** — 이게 있어야 하우스로 들린다."""
    g = np.ones(len(buf), np.float32)
    n = int(SR * hold)
    curve = 1 - depth * (1 - np.linspace(0, 1, n, dtype=np.float32) ** 0.45)
    for i in hits:
        j = min(len(g), i + n)
        if j > i:
            g[i:j] = np.minimum(g[i:j], curve[:j - i])
    return buf * g


def arp(freqs, bar_i):
    """16분 아르페지오. 코드 음을 위아래로 훑는다."""
    out = np.zeros(int(BAR * SR) + SR, np.float32)
    order = [0, 1, 2, 3, 2, 1, 2, 3] * 2
    for k, oi in enumerate(order):
        f = freqs[oi % len(freqs)] * (2 if k % 8 >= 4 else 1)
        n = int(SR * 0.12)
        t = np.arange(n, dtype=np.float32) / SR
        s = np.sin(2 * np.pi * f * t) * env_ad(n, 0.002, 0.10, 4.0)
        s += 0.35 * np.sin(2 * np.pi * f * 2 * t) * env_ad(n, 0.002, 0.06, 5.0)
        put(out, s * 0.16, int(k * BEAT / 2 * SR))
    return out


def build():
    n = int(DUR * SR) + SR
    drums = np.zeros(n, np.float32)
    tonal = np.zeros(n, np.float32)
    hits = []

    for b in range(BARS):
        ci = b % len(CHORDS)
        # **컷오프가 곡 전체에 걸쳐 열린다.** 이 한 줄이 이 곡의 정체다
        p = b / (BARS - 1)
        # **처음부터 들려야 한다.** 420Hz 로 시작했더니 첫 두 마디가
        # 사실상 무음이었다 — 릴스는 첫 1초에 소리가 없으면 넘긴다
        cut = 900 + (6200 - 900) * p ** 1.5

        # 도입 두 마디는 코드가 주인공이라 더 크게 낸다
        g = 0.44 if b < 2 else 0.26
        put(tonal, chord(CHORDS[ci], int(BAR * SR), cut) * g, at(b))

        if b >= 2:
            put(tonal, arp(CHORDS[ci], b) * (0.5 + 0.5 * p), at(b))
            for beat in range(4):
                i = at(b, beat)
                put(drums, kick(0.42, 1.0) * 0.95, i)
                hits.append(i)
                put(drums, hat(0.05, 0.16, open_=(beat % 2 == 1)), at(b, beat + 0.5))
            put(tonal, subf(BASS[ci], BAR * 0.95, 0.55, 0.9), at(b))
        else:
            for beat in range(4):
                put(drums, hat(0.045, 0.13, open_=(beat % 2 == 1)), at(b, beat + 0.5))
            if b == 1:
                # 킥이 들어오기 전에 예고한다 — 없으면 마디 2 가 뜬금없다
                put(drums, noise_riser(BAR, 300, 7000, 0.30), at(b))

        if b >= 4 and b % 2 == 1:
            put(drums, clap(0.42), at(b, 1))
            put(drums, clap(0.42), at(b, 3))

    tonal = duck(tonal, hits)
    mix = drums + tonal
    mix = sat(mix, 1.6)
    mix += reverb(hp(mix, 900), tail=1.1, mix=0.16)
    mix = mix[:int(DUR * SR)]
    # 끝 한 마디는 꼬리로 흘린다 — 릴스가 루프될 때 뚝 끊기면 티가 난다
    tailn = int(SR * 0.6)
    mix[-tailn:] *= np.linspace(1, 0, tailn, dtype=np.float32) ** 0.7
    mix /= max(1e-9, np.abs(mix).max()) / 0.94

    p = os.path.join(OUT, 'bgm_lineup.wav')
    w = wave.open(p, 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
    w.close()
    print(f'{p}  {BPM:.0f}BPM · {BARS}마디 · {DUR:.1f}초')
    return p


if __name__ == '__main__':
    build()
