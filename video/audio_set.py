"""
**릴스 세트 3편의 곡.** 마감(`push`) · 낮(`day`) · 밤(`dusk`).

    python audio_set.py          셋 다
    python audio_set.py push     골라서
    python audio_check.py        만든 뒤 반드시 — 기존 곡과 겹치는지 잰다

## 안 겹치게 하는 법

`audio_check` 로 서른세 곡을 재 봤더니 **BPM 만 바꾼 곡은 음색이 0.99 로
붙는다.** 주인공 악기를 갈아야 실제로 다른 곡이 된다.

    이미 쓴 것   pluck · perc · bass · supersaw · pad · stab · 필터 코드 ·
                 애시드 · 로즈 일렉피아노 · 노이즈 스탭
    push         **브라스 스탭.** 톱니에 짧은 필터 엔벨로프 — 관악기처럼 뻗는다
    day          **마림바.** 사인 + 짧은 나무 소리. 배음이 홀수만 남는다
    dusk         **오르간.** 배음을 정수배로 쌓아 계속 울린다 — 감쇠가 거의 없다

BPM 도 안 쓴 값이다. 기존이 105·108·110·115·117·118·120·121·122·124·125·
126·128·130·132·133·134·136·138·140·142·145·155·174 라 **137 · 112 · 127**.

## 셋이 서로도 달라야 한다

같은 주에 올리는 세 편이라 이게 제일 중요하다.

    push   137BPM · 단조 · 급하다. 킥이 앞으로 밀고 스탭이 박을 쪼갠다
    day    112BPM · 장조 · 느긋하다. 셔플 하이햇에 마림바가 튄다
    dusk   127BPM · 단조 · 두껍다. 오르간이 깔리고 베이스가 오프비트로 민다

빠르기·조성·악기·타악기 성격을 다 갈랐다.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, env_ad, lp, hp, kick, hat, clap, reverb, noise_riser
from audio_reel import sat, subf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'set')
os.makedirs(OUT, exist_ok=True)

PRESET = {
    'push': dict(bpm=137.0, bars=9),      # 15.8초
    'day':  dict(bpm=112.0, bars=7),      # 15.0초
    'dusk': dict(bpm=127.0, bars=8),      # 15.1초
}

# 코드 — 편마다 다른 진행. 같은 진행이면 악기를 갈아도 같은 곡처럼 들린다
CH = {
    # Am → F → C → G. 단조로 시작해 밀어붙인다
    'push': [[220.00, 261.63, 329.63], [174.61, 220.00, 261.63],
             [261.63, 329.63, 392.00], [196.00, 246.94, 293.66]],
    # C6 → Am7 → Dm7 → G. 장조, 물에 뜬 낮
    'day':  [[261.63, 329.63, 392.00, 440.00], [220.00, 261.63, 329.63, 392.00],
             [293.66, 349.23, 440.00, 523.25], [196.00, 246.94, 293.66, 392.00]],
    # Cm → Ab → Eb → Bb. 두껍고 어둡다
    'dusk': [[261.63, 311.13, 392.00], [207.65, 261.63, 311.13],
             [155.56, 196.00, 233.08], [233.08, 293.66, 349.23]],
}
BASS = {'push': [55.00, 43.65, 65.41, 49.00],
        'day':  [65.41, 55.00, 73.42, 49.00],
        'dusk': [65.41, 51.91, 77.78, 58.27]}


def _put(buf, sig, i):
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def brass(freqs, n):
    """브라스 스탭. **톱니에 짧은 필터 엔벨로프** — 열렸다 닫히면서 '뽜' 하고
    뻗는다. 필터를 안 움직이면 그냥 신스 코드가 된다."""
    t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for f in freqs:
        for d in (-0.006, 0.0, 0.006):
            x += (2 * ((t * f * (1 + d)) % 1.0) - 1)
    x /= len(freqs) * 3
    # 필터를 한 번에 다 못 움직이므로 세 토막으로 나눠 건다
    seg, out = max(1, n // 3), np.zeros(n, np.float32)
    for k in range(3):
        a, b = k * seg, min(n, (k + 1) * seg)
        out[a:b] = lp(x[a:b], 900 + 2600 * (1 - k / 2.0))
    return out * env_ad(n, 0.006, 0.24, 3.2)


def marimba(f, n):
    """마림바. 사인 + 홀수 배음 조금, 그리고 짧은 나무 소리."""
    t = np.arange(n, dtype=np.float32) / SR
    e = env_ad(n, 0.002, 0.22, 4.0)
    x = np.sin(2 * np.pi * f * t) * e
    x += np.sin(2 * np.pi * f * 3.0 * t) * env_ad(n, 0.001, 0.06, 8.0) * 0.22
    x += np.sin(2 * np.pi * f * 5.0 * t) * env_ad(n, 0.001, 0.03, 12.0) * 0.07
    return x


def organ(freqs, n):
    """오르간. **배음을 정수배로 쌓고 감쇠를 거의 안 준다** — 계속 울린다."""
    t = np.arange(n, dtype=np.float32) / SR
    x = np.zeros(n, np.float32)
    for f in freqs:
        for h, a in ((1, 1.0), (2, 0.5), (3, 0.28), (4, 0.16), (6, 0.09)):
            x += np.sin(2 * np.pi * f * h * t) * a
    x /= len(freqs) * 2.0
    e = np.minimum(1.0, np.arange(n) / (SR * 0.02))
    e *= np.minimum(1.0, (n - np.arange(n)) / (SR * 0.05))
    return x * e


def build(name):
    cfg = PRESET[name]
    bpm, bars = cfg['bpm'], cfg['bars']
    beat, bar = 60.0 / bpm, 60.0 / bpm * 4
    dur = bar * bars
    n = int(dur * SR) + SR
    dr = np.zeros(n, np.float32)
    tn = np.zeros(n, np.float32)

    def at(b, k=0.0):
        return int((b * bar + k * beat) * SR)

    for b in range(bars):
        p = b / max(1, bars - 1)
        ci = b % 4
        ch, bs = CH[name][ci], BASS[name][ci]

        if name == 'push':
            if b >= 1:
                for k in range(4):
                    _put(dr, kick(0.26, 1.0) * 1.00, at(b, k))
                    _put(dr, hat(0.028, 0.11, open_=(k % 2 == 1)), at(b, k + 0.5))
                _put(tn, subf(bs, beat * 0.9, 0.60, 1.0), at(b))
                _put(tn, subf(bs, beat * 0.9, 0.60, 1.0), at(b, 2))
            # **스탭이 박을 쪼갠다.** 뒷박에 걸쳐야 급해진다
            for k in (0.75, 2.0, 2.75):
                _put(tn, brass(ch, int(SR * 0.20)) * (0.30 + 0.20 * p), at(b, k))
            if b == 0:
                _put(dr, noise_riser(bar, 350, 8000, 0.32), at(b))
            if b >= 2 and b % 2 == 1:
                _put(dr, clap(0.30), at(b, 1))
                _put(dr, clap(0.30), at(b, 3))

        elif name == 'day':
            if b >= 1:
                for k in range(4):
                    _put(dr, kick(0.36, 0.90) * 0.78, at(b, k))
                # **셔플.** 하이햇을 3분할 뒤쪽에 놓으면 흔들린다
                for k in range(4):
                    _put(dr, hat(0.05, 0.12, open_=False), at(b, k + 0.66))
                _put(tn, subf(bs, bar * 0.9, 0.52, 0.85), at(b))
            # 마림바 아르페지오 — 코드 음을 훑는다
            order = [0, 2, 1, 3, 2, 0, 1, 2]
            for k, oi in enumerate(order):
                f = ch[oi % len(ch)] * (2 if k >= 4 else 1)
                _put(tn, marimba(f, int(SR * 0.22)) * 0.20 * (0.6 + 0.5 * p),
                     at(b, k * 0.5))
            if b >= 3 and b % 2 == 1:
                _put(dr, clap(0.34) * 0.65, at(b, 2))

        else:                                        # dusk
            if b >= 1:
                for k in range(4):
                    _put(dr, kick(0.32, 0.98) * 0.95, at(b, k))
                for k in range(8):
                    _put(dr, hat(0.034, 0.10, open_=(k % 4 == 3)), at(b, k * 0.5))
                # 오프비트 베이스 — 킥 사이를 메운다
                for k in range(4):
                    _put(tn, subf(bs, beat * 0.44, 0.58, 1.0), at(b, k + 0.5))
            _put(tn, organ(ch, int(bar * 0.96 * SR)) * (0.26 + 0.16 * p), at(b))
            if b == 0:
                _put(dr, noise_riser(bar, 280, 6000, 0.26), at(b))
            if b >= 2 and b % 2 == 1:
                _put(dr, clap(0.36), at(b, 1))
                _put(dr, clap(0.36), at(b, 3))

    mix = dr + tn
    mix = sat(mix, {'push': 1.9, 'day': 1.4, 'dusk': 1.7}[name])
    mix += reverb(hp(mix, 850),
                  tail={'push': 0.7, 'day': 1.5, 'dusk': 1.1}[name],
                  mix={'push': 0.11, 'day': 0.22, 'dusk': 0.15}[name])
    mix = mix[:int(dur * SR)]
    tail = int(SR * 0.5)
    mix[-tail:] *= np.linspace(1, 0, tail, dtype=np.float32) ** 0.7
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
