"""
**컷 릴스 두 편의 곡.** 낮 편(`water`)과 밤 편(`neon`).

    python audio_cut.py            둘 다
    python audio_cut.py water      골라서

## 안 겹치게 하는 법

`audio_reel4` 가 정리해 둔 대로 **BPM 만 바꾸면 같은 곡으로 들린다.**
주인공 악기를 갈아야 한다.

    이미 쓴 것   pluck · perc · bass · supersaw · pad · stab ·
                 필터 도는 코드(lineup) · 애시드 레조넌스(sunset)
    water        **로즈 일렉피아노.** 짧은 어택에 긴 꼬리, 코드가 겹쳐 울린다
    neon         **짧은 노이즈 스탭 + 오프비트 베이스.** 음정이 거의 없다

BPM 도 안 쓴 값이다. 기존이 105·108·110·117·118·120·121·122·124·125·
126·128·130·132·133·136·138·140·142·145·155·174 라 **115** 와 **134** 를 쓴다.

## 둘이 서로 안 겹쳐야 한다

같은 날 올리는 두 편이라 이게 제일 중요하다.

    water   115BPM · 장조 · 물에 뜬 느낌. 킥이 부드럽고 하이햇이 성기다
    neon    134BPM · 단조 · 붐비는 느낌. 킥이 딱딱하고 16분 하이햇이 촘촘하다

빠르기·조성·타악기 성격 셋을 다 갈랐다. 하나만 바꾸면 같은 곡으로 들린다.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, env_ad, lp, hp, kick, hat, clap, reverb, noise_riser
from audio_reel import sat, subf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'cut')
os.makedirs(OUT, exist_ok=True)

# (BPM, 마디 수) — 마디 수 × 4비트 × (60/BPM) 이 길이다.
# **영상 길이를 여기서 정한다.** 컷 표에서 정하면 곡과 어긋난다.
PRESET = {
    'water': dict(bpm=115.0, bars=8),      # 16.7초
    'neon':  dict(bpm=134.0, bars=9),      # 16.1초
}

# Fmaj9 → Cmaj7 → Dm9 → Bb6. 장조로 열려 있다 — 물에 떠 있는 낮이다
WATER_CH = [[174.61, 220.00, 261.63, 329.63],
            [261.63, 329.63, 392.00, 493.88],
            [146.83, 220.00, 293.66, 349.23],
            [233.08, 293.66, 349.23, 440.00]]
WATER_BS = [43.65, 65.41, 36.71, 58.27]

# Am → Fm → Cm → G7. 단조로 조인다 — 사람이 몰린 밤이다
NEON_BS = [55.00, 43.65, 65.41, 49.00]


def _put(buf, sig, i):
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def rhodes(freqs, n, bright=1.0):
    """로즈 일렉피아노. **사인 두 개를 겹쳐 배음을 만든다** — 톱니로 하면
    신스가 되고, 사인 하나면 오르간이 된다. 이 사이가 로즈다."""
    out = np.zeros(n, np.float32)
    t = np.arange(n, dtype=np.float32) / SR
    for f in freqs:
        e = env_ad(n, 0.004, 0.9, 2.2)
        # 배음이 먼저 죽고 기음이 남는다 — 이게 로즈의 '띵' 이다
        e2 = env_ad(n, 0.002, 0.30, 4.5)
        out += (np.sin(2 * np.pi * f * t) * e
                + np.sin(2 * np.pi * f * 2 * t) * e2 * 0.34 * bright
                + np.sin(2 * np.pi * f * 3.01 * t) * e2 * 0.11 * bright)
    return out / len(freqs)


def stab(n, seed):
    """노이즈 스탭. **음정이 거의 없다** — 밴드패스로 통과 대역만 남긴다."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n).astype(np.float32)
    x = lp(hp(x, 900), 3800)
    return x * env_ad(n, 0.001, 0.075, 6.0)


def build(name):
    cfg = PRESET[name]
    bpm, bars = cfg['bpm'], cfg['bars']
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * bars
    n = int(dur * SR) + SR
    drums = np.zeros(n, np.float32)
    tonal = np.zeros(n, np.float32)

    def at(b, k=0.0):
        return int((b * bar + k * beat) * SR)

    for b in range(bars):
        p = b / max(1, bars - 1)
        ci = b % 4

        if name == 'water':
            # 코드가 주인공. 마디마다 한 번, 길게 울린다
            _put(tonal, rhodes(WATER_CH[ci], int(bar * SR), 0.7 + 0.5 * p) * 0.40,
                 at(b))
            # 뒷박에 한 번 더 얹어 흔들리게 — 물에 뜬 느낌이 여기서 온다
            _put(tonal, rhodes(WATER_CH[ci], int(bar * 0.5 * SR), 1.0) * 0.16,
                 at(b, 2.5))
            if b >= 1:
                _put(tonal, subf(WATER_BS[ci], bar * 0.92, 0.5, 0.85), at(b))
                for k in range(4):
                    _put(drums, kick(0.40, 0.92) * 0.80, at(b, k))
                # **하이햇이 성기다.** 뒷박에만 — 촘촘하면 급해진다
                for k in (1, 3):
                    _put(drums, hat(0.055, 0.13, open_=True), at(b, k + 0.5))
            if b == 0:
                _put(drums, noise_riser(bar, 250, 5200, 0.22), at(b))
            if b >= 3 and b % 2 == 1:
                _put(drums, clap(0.36) * 0.7, at(b, 1))
                _put(drums, clap(0.36) * 0.7, at(b, 3))

        else:                                    # neon
            if b >= 1:
                for k in range(4):
                    _put(drums, kick(0.30, 1.0) * 1.00, at(b, k))
                # **16분 하이햇.** 촘촘한 게 이 곡의 정체다
                for k in range(16):
                    op = (k % 4 == 2)
                    _put(drums, hat(0.030, 0.10 if not op else 0.15, open_=op),
                         at(b, k * 0.25))
                # 오프비트 베이스 — 킥 사이에 끼어 붐빈다
                for k in range(4):
                    _put(tonal, subf(NEON_BS[ci], beat * 0.42, 0.62, 1.0),
                         at(b, k + 0.5))
            for k in (0, 2):
                _put(tonal, stab(int(SR * 0.09), b * 7 + k) * (0.30 + 0.22 * p),
                     at(b, k + 0.75))
            if b == 0:
                _put(drums, noise_riser(bar, 400, 8000, 0.30), at(b))
            if b >= 2 and b % 2 == 1:
                _put(drums, clap(0.34), at(b, 1))
                _put(drums, clap(0.34), at(b, 3))

    mix = drums + tonal
    mix = sat(mix, 1.5 if name == 'water' else 1.8)
    mix += reverb(hp(mix, 800), tail=1.4 if name == 'water' else 0.8,
                  mix=0.20 if name == 'water' else 0.12)
    mix = mix[:int(dur * SR)]
    # 릴스가 루프될 때 뚝 끊기면 티가 난다
    tn = int(SR * 0.5)
    mix[-tn:] *= np.linspace(1, 0, tn, dtype=np.float32) ** 0.7
    mix /= max(1e-9, np.abs(mix).max()) / 0.94

    p = os.path.join(OUT, f'bgm_{name}.wav')
    w = wave.open(p, 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
    w.close()
    print(f'{p}  {bpm:.0f}BPM · {bars}마디 · {dur:.1f}초')
    return p


if __name__ == '__main__':
    for k in (sys.argv[1:] or list(PRESET)):
        if k not in PRESET:
            raise SystemExit(f'{k} 은 없습니다 — {", ".join(PRESET)}')
        build(k)
