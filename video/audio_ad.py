"""
**광고 릴스 전용 곡.** 인트로 → 드롭 → 브레이크 → 재드롭.

    python audio_ad.py   →  out/ad/bgm_ad.wav   131BPM · 14마디 · 25.6초
    python audio_check.py                       만든 뒤 반드시 — 겹치는지 잰다

## 왜 구조가 필요한가

지금까지 곡은 **처음부터 끝까지 같은 세기**였다. 분위기 릴스에는 그게 맞지만
광고는 다르다 — 볼 이유를 계속 갱신해야 완주한다.

    마디 0      인트로. 라이저만. **2초 안에 터진다**
    마디 1~7    드롭. 킥·베이스·스탭 전면
    마디 8~9    브레이크. 드럼을 빼고 코드만 — 자막이 읽히는 자리다
    마디 10~13  재드롭 + 꼬리. 3차 OPEN · 정보 · CTA 가 여기 앉는다

브레이크가 이 곡의 핵심이다. **소리가 얇아지는 순간 눈이 글자로 간다** —
'1차 SOLD OUT' 을 드롭 위에 얹으면 아무도 안 읽는다.

## 안 겹치게

기존 서른아홉 곡과 BPM·악기를 갈랐다.

    BPM      **131** — 105·108·110·112·115·117·118·120·121·122·124·125·126·
             127·128·130·132·133·134·136·137·138·140·142·145·155·174 를 피했다
    주인공   **플럭 신스 + 화이트노이즈 스윕.** 톱니를 짧게 끊어 튕기는 소리다.
             기존의 로즈·마림바·오르간·브라스·애시드와 결이 다르다
"""
import os
import wave

import numpy as np

from audio import SR, env_ad, lp, hp, kick, hat, clap, reverb, noise_riser
from audio_reel import sat, subf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'ad')
os.makedirs(OUT, exist_ok=True)

BPM = 131.0
BARS = 14
BEAT = 60.0 / BPM                  # 0.458초
BAR = BEAT * 4                     # 1.832초
DUR = BAR * BARS                   # 21.98초

DROP_IN, BREAK_IN, DROP2 = 1, 8, 10     # 마디 경계

# Fm → Db → Ab → Eb. 단조로 밀고 마지막에 열린다
CH = [[174.61, 207.65, 261.63], [138.59, 174.61, 207.65],
      [207.65, 261.63, 311.13], [155.56, 196.00, 233.08]]
BASS = [43.65, 34.65, 51.91, 38.89]


def _put(buf, sig, i):
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def pluck(f, n, bright=1.0):
    """플럭. **톱니를 짧게 끊는다** — 어택이 서고 꼬리가 없어야 튕긴다."""
    t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for d in (-0.004, 0.0, 0.004):
        x += 2 * ((t * f * (1 + d)) % 1.0) - 1
    x = lp(x / 3, 1400 + 2800 * bright)
    return x * env_ad(n, 0.001, 0.13, 6.5)


def sweep(n, up=True):
    """화이트노이즈 스윕. 마디가 갈리는 자리에 얹어 컷을 밀어 준다."""
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n).astype(np.float32)
    seg, out = max(1, n // 6), np.zeros(n, np.float32)
    for k in range(6):
        a, b = k * seg, min(n, (k + 1) * seg)
        p = k / 5.0 if up else 1 - k / 5.0
        out[a:b] = hp(x[a:b], 300 + 5200 * p)
    e = np.linspace(0, 1, n, dtype=np.float32) ** (1.6 if up else 0.5)
    return out * e * 0.16


def chord(freqs, n, cut):
    x = np.zeros(n, np.float32)
    t = np.arange(n, dtype=np.float32) / SR
    for f in freqs:
        for d in (-0.006, 0.006):
            x += 2 * ((t * f * (1 + d)) % 1.0) - 1
    x = lp(x / (len(freqs) * 2), cut)
    e = np.minimum(1.0, np.arange(n) / (SR * 0.04))
    e *= np.clip(1.0 - np.arange(n) / n, 0, 1) ** 0.3
    return x * e


def build():
    n = int(DUR * SR) + SR
    dr = np.zeros(n, np.float32)
    tn = np.zeros(n, np.float32)

    def at(b, k=0.0):
        return int((b * BAR + k * BEAT) * SR)

    for b in range(BARS):
        ci = b % 4
        brk = BREAK_IN <= b < DROP2
        p = b / (BARS - 1)

        if b == 0:
            # **2초 안에 터져야 한다.** 인트로는 한 마디뿐이다
            _put(dr, noise_riser(BAR, 300, 9000, 0.34), at(b))
            _put(tn, chord(CH[ci], int(BAR * SR), 1600) * 0.28, at(b))
            continue

        if brk:
            # 브레이크 — 드럼을 뺀다. **소리가 얇아지면 눈이 글자로 간다**
            _put(tn, chord(CH[ci], int(BAR * SR), 2600 + 2000 * p) * 0.34, at(b))
            for k in (0, 2):
                _put(dr, hat(0.05, 0.10, open_=True), at(b, k + 0.5))
            if b == DROP2 - 1:
                _put(dr, noise_riser(BAR, 400, 10000, 0.36), at(b))
            continue

        # 드롭
        for k in range(4):
            _put(dr, kick(0.28, 1.0) * 1.00, at(b, k))
            _put(dr, hat(0.026, 0.10, open_=(k % 2 == 1)), at(b, k + 0.5))
            _put(tn, subf(BASS[ci], BEAT * 0.46, 0.62, 1.0), at(b, k + 0.5))
        # 플럭 아르페지오 — 16분으로 튄다
        order = [0, 2, 1, 2, 0, 1, 2, 1]
        for k, oi in enumerate(order):
            f = CH[ci][oi] * (2 if k >= 4 else 1)
            _put(tn, pluck(f, int(SR * 0.14), 0.5 + 0.5 * p) * 0.22,
                 at(b, k * 0.5))
        if b % 2 == 1:
            _put(dr, clap(0.30), at(b, 1))
            _put(dr, clap(0.30), at(b, 3))
        # 마디가 갈리는 자리에 스윕 — 컷 전환을 밀어 준다
        if b in (DROP_IN, DROP2, BARS - 2):
            _put(dr, sweep(int(SR * 0.5), up=False), at(b))

    mix = dr + tn
    mix = sat(mix, 1.8)
    mix += reverb(hp(mix, 900), tail=0.8, mix=0.13)
    mix = mix[:int(DUR * SR)]
    tail = int(SR * 0.55)
    mix[-tail:] *= np.linspace(1, 0, tail, dtype=np.float32) ** 0.7
    mix /= max(1e-9, np.abs(mix).max()) / 0.94

    p = os.path.join(OUT, 'bgm_ad.wav')
    w = wave.open(p, 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
    w.close()
    print(f'{p}  {BPM:.0f}BPM · {BARS}마디 · {DUR:.1f}초 '
          f'(드롭 {DROP_IN}마디 · 브레이크 {BREAK_IN}~{DROP2}마디)')
    return p


if __name__ == '__main__':
    build()
