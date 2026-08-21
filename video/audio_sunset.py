"""
**해 지는 릴스 전용 곡.** 125BPM · 10마디 · 19.2초.

    python audio_sunset.py   →  out/sunset/bgm_sunset.wav

## 또 새로 만드는 이유

`audio_reel4` 가 세워 둔 원칙 그대로다 — **주인공 악기를 갈아야 다른
곡으로 들린다.** 지금까지 쓴 것을 다 피한다.

    이미 쓴 것   pluck · perc · bass · supersaw · pad · stab ·
                 필터 도는 코드(audio_lineup)
    여기서       **애시드 베이스**. 레조넌스가 살아 있는 필터가 한 마디마다
                 열렸다 닫힌다. 303 계열 소리라 우리 곡 어디에도 없다

BPM 도 겹치지 않게 **125** 를 쓴다(기존 108·110·117·118·120·121·122·124·
126·128·130·132·133·136·138·142).

## 구성 — 그림이 낮에서 밤으로 간다

곡도 같이 간다. **앞은 열려 있고 뒤로 갈수록 조인다** — 해가 지는 것과
같은 방향이다.

    마디 0~1   하이햇과 애시드만. 필터 활짝
    마디 2~5   킥 인. 필터가 마디마다 여닫는다
    마디 6~7   레조넌스를 올린다 — 소리가 날카로워지며 밤으로 넘어간다
    마디 8~9   클랩 + 오픈햇. 제일 시끄러운 자리
"""
import os
import wave

import numpy as np

from audio import SR, env_ad, lp, hp, kick, hat, clap, reverb
from audio_reel import sat

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sunset')
os.makedirs(OUT, exist_ok=True)

BPM = 125.0
BARS = 10
BEAT = 60.0 / BPM                      # 0.48초
BAR = BEAT * 4                         # 1.92초
DUR = BAR * BARS                       # 19.2초

ROOT = 55.0                            # A1
# 16분 한 마디. 0 은 쉼, 숫자는 반음. 애시드는 **쉼이 있어야 굴러간다**
PATTERN = [0, None, 12, 0, None, 7, 0, 10,
           None, 0, 12, None, 3, 0, None, 7]


def at(bar, beat=0.0):
    return int((bar * BAR + beat * BEAT) * SR)


def put(buf, sig, i):
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def acid(freq, n, cut, res, slide=False):
    """애시드 한 음. **레조넌스가 이 곡의 정체다.**

    저역통과를 두 번 걸고 그 차이를 되먹여서 문턱 부근을 부풀린다 —
    제대로 된 공진 필터는 아니지만, 그 소리의 성격은 난다."""
    t = np.arange(n, dtype=np.float32) / SR
    ph = np.cumsum(np.full(n, freq / SR, np.float32))
    if slide:                                   # 포르타멘토 — 앞 음에서 미끄러진다
        ph = np.cumsum(np.linspace(freq * 0.72, freq, n).astype(np.float32) / SR)
    x = 2 * (ph % 1.0) - 1                      # 톱니
    lo = lp(x, cut)
    band = lp(x, cut * 2.2) - lo
    y = lo + band * res
    e = env_ad(n, 0.004, 0.16, 3.2)
    return (y * e).astype(np.float32)


def build():
    n = int(DUR * SR) + SR
    drums = np.zeros(n, np.float32)
    bass = np.zeros(n, np.float32)

    for b in range(BARS):
        p = b / (BARS - 1)
        # 필터가 마디마다 여닫고, 전체로는 조여든다 — 해가 지는 방향
        base = 2600 - 1500 * p
        swing = 1.0 + 0.55 * np.sin(b * 1.9)
        cut = float(np.clip(base * swing, 320, 5200))
        res = 0.55 + 0.85 * p                   # 뒤로 갈수록 날카롭게

        for k, semi in enumerate(PATTERN):
            if semi is None:
                continue
            f = ROOT * 2 ** (semi / 12)
            dur = BEAT / 4 * (1.7 if k % 4 == 0 else 1.0)
            s = acid(f, int(dur * SR), cut, res, slide=(k in (2, 10)))
            put(bass, s * 0.30, at(b, k / 4))

        if b >= 2:
            for beat in range(4):
                put(drums, kick(0.40, 1.0) * 0.92, at(b, beat))
                put(drums, hat(0.045, 0.15, open_=(beat % 2 == 1)), at(b, beat + 0.5))
        else:
            for beat in range(4):
                put(drums, hat(0.04, 0.12, open_=(beat % 2 == 1)), at(b, beat + 0.5))

        if b >= 8:
            put(drums, clap(0.46), at(b, 1))
            put(drums, clap(0.46), at(b, 3))
            put(drums, hat(0.16, 0.13, open_=True), at(b, 3.5))
        elif b >= 4 and b % 2 == 1:
            put(drums, clap(0.38), at(b, 3))

    mix = drums + sat(bass, 2.0) * 0.9
    mix = sat(mix, 1.5)
    mix += reverb(hp(mix, 1200), tail=0.9, mix=0.14)
    mix = mix[:int(DUR * SR)]
    tail = int(SR * 0.5)
    mix[-tail:] *= np.linspace(1, 0, tail, dtype=np.float32) ** 0.7
    mix /= max(1e-9, np.abs(mix).max()) / 0.94

    p = os.path.join(OUT, 'bgm_sunset.wav')
    w = wave.open(p, 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
    w.close()
    print(f'{p}  {BPM:.0f}BPM · {BARS}마디 · {DUR:.2f}초')
    return p


if __name__ == '__main__':
    build()
