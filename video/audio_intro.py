"""
행사 인트로 사운드 — **악기를 하나도 안 쓴다.**

킥·스네어·신스 같은 악기 소리 대신 **기계가 내는 소리**만으로 짭니다.
클럽 사운드 시스템에 전원이 들어오고, 셔터가 열리고, 판이 걸리는 과정입니다.

    릴레이   접점이 붙는 딸깍. 짧은 노이즈 + 공진하는 틱
    험       전원 60Hz 와 그 배음. 아주 살짝 흔들려야 살아 있는 소리가 된다
    서보     피치가 오르는 톱니파 + 진폭 떨림. 모터가 도는 소리
    공압     밴드패스가 아래로 쓸려 내려가는 노이즈. 압축공기 배기
    금속     비조화 배음 다섯 개 + 어택 노이즈. 두드리면 나는 소리
    콘덴서   가늘게 위로 올라가는 사인. 충전되는 소리
    글리치   샘플 앤 홀드. 디지털이 튀는 소리

**기계음은 음정이 없어서 리듬만 남습니다.** 그래서 배치가 전부입니다 —
언제 붙고 언제 비는지로만 긴장을 만듭니다.

python audio_intro.py  →  out/intro/bgm_intro.wav
"""
import os
import wave
import numpy as np
from scipy import signal
from audio import SR, place, lp, hp, bp, reverb

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

DUR = 16.0
N = int(DUR * SR)


def _n(dur):
    return int(dur * SR), np.arange(int(dur * SR)) / SR


def relay(gain=1.0, seed=0):
    """접점이 붙는 딸깍. 노이즈 어택 + 짧게 공진하는 금속 틱."""
    n, t = _n(0.05)
    rng = np.random.default_rng(seed)
    click = bp(rng.standard_normal(n), 1800, 9000) * np.exp(-t * 320)
    tick = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 190) * 0.5
    return (click + tick) * gain


def hum(dur, f=60.0, gain=1.0):
    """전원 험. 배음을 홀수로 쌓고 아주 살짝 흔들어야 죽은 소리가 안 된다."""
    n, t = _n(dur)
    x = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.42), (3, 0.26), (5, 0.12), (7, 0.06)):
        x += np.sin(2 * np.pi * f * k * t + k) * a
    x *= 1 + 0.04 * np.sin(2 * np.pi * 0.7 * t)      # 전압이 흔들리는 정도
    return x / 1.9 * gain


def servo(dur, f0=140, f1=900, gain=1.0, flutter=38.0):
    """모터. 피치가 오르는 톱니파에 진폭 떨림을 얹는다."""
    n, t = _n(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    x = lp(x, 2600)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * flutter * t)  # 극(pole)을 지날 때 나는 떨림
    e = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return x * e * gain


def air(dur=0.6, gain=1.0, seed=1):
    """압축공기 배기. 밴드패스가 아래로 쓸려 내려간다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    step = int(SR * 0.02)
    for i in range(0, n, step):
        k = 1 - (i / n)
        c = 300 + 7000 * k ** 1.6
        out[i:i + step] = bp(x[i:i + step], max(120, c * 0.5), c + 600)
    return out * np.exp(-t / (dur * 0.55)) * gain


def metal(dur=0.9, gain=1.0, seed=2, base=190.0):
    """금속 타격. 배음이 정수배가 아니어야 쇳소리가 난다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for m in (1.0, 2.76, 5.40, 8.93, 13.34):          # 비조화 배음
        x += np.sin(2 * np.pi * base * m * t) * np.exp(-t * (2.2 + m * 0.9)) / (1 + m * 0.5)
    x += hp(rng.standard_normal(n), 4000) * np.exp(-t * 90) * 0.5
    return x * gain


def capacitor(dur=2.4, gain=1.0):
    """충전되는 소리. 가늘게 위로 올라가는 사인 하나."""
    n, t = _n(dur)
    f = 400 * (14.0) ** (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * (t / dur) ** 2 * gain


def glitch(dur=0.22, gain=1.0, seed=3):
    """샘플 앤 홀드. 디지털이 튀는 소리."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    hold = int(SR / rng.integers(400, 2200))
    x = np.repeat(rng.uniform(-1, 1, n // hold + 1), hold)[:n]
    return hp(x, 300) * np.exp(-t * 14) * gain


def thump(dur=0.5, gain=1.0):
    """기계가 도는 박자. 음정이 아니라 무게만 남긴다."""
    n, t = _n(dur)
    f = 52 + 90 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) * gain


def build():
    m = np.zeros(N)                                   # 기계 · 전면
    b = np.zeros(N)                                   # 저역 · 바닥
    f = np.zeros(N)                                   # 공간

    # 0.0–1.2  접점이 하나씩 붙는다. 비어 있는 시간이 길수록 다음 소리가 커진다
    for i, at in enumerate((0.10, 0.62, 1.05)):
        place(m, relay(0.85, i), at)

    # 1.2–16   전원 험이 깔린다. 뒤로 갈수록 커진다
    hm = hum(DUR - 1.2, 60.0, 0.5)
    hm *= np.clip(np.linspace(0, 1, len(hm)) * 2.2, 0, 1) ** 0.7
    place(b, hm, 1.2)

    # 1.4–3.6  모터가 돈다
    place(m, servo(2.2, 130, 760, 0.34), 1.4)
    place(m, relay(0.7, 9), 3.55)

    # 3.7–4.4  배기 → 금속 한 방
    place(m, air(0.7, 0.42, 5), 3.70)
    place(m, metal(1.0, 0.50, 6, 210), 4.30)
    place(b, thump(0.6, 0.55), 4.30)

    # 4.8–10.4 기계가 규칙적으로 돈다. 0.6초 간격 = 100BPM 느낌이지만 악기는 없다
    at = 4.8
    k = 0
    while at < 10.4:
        place(b, thump(0.5, 0.42 + 0.03 * k), at)
        place(m, relay(0.30, 20 + k), at + 0.30)
        if k % 2 == 1:
            place(m, metal(0.5, 0.16, 30 + k, 320), at + 0.45)
        at += 0.6
        k += 1

    # 8.6–11.0 콘덴서가 충전된다. 이 구간이 길어야 터질 때 크게 들린다
    place(m, capacitor(2.4, 0.20), 8.60)
    place(m, servo(1.6, 200, 1600, 0.16, 26), 9.40)
    for i, at in enumerate((10.55, 10.72, 10.86)):
        place(m, glitch(0.16, 0.30, 40 + i), at)

    # 11.0  판이 걸린다 — 여기가 이름이 나오는 자리
    place(m, metal(1.8, 0.95, 7, 150), 11.0)
    place(m, air(1.1, 0.40, 8), 11.0)
    place(b, thump(1.4, 1.0), 11.0)
    place(b, thump(1.2, 0.55), 11.02)

    # 11.0–16  험만 남기고 접점이 가끔 튄다
    for i, at in enumerate((12.3, 13.6, 14.9)):
        place(m, relay(0.24, 60 + i), at)
    place(f, air(2.4, 0.10, 9), 13.4)

    mix = m + b * 1.15 + reverb(m, 1.8, 0.20) * 0.55 + reverb(f, 2.6, 0.35) * 0.5
    mix = hp(mix, 26, 2)
    mix = np.tanh(mix * 1.25) / np.tanh(1.25)
    mix /= np.abs(mix).max() + 1e-9
    mix *= 0.95
    fade = int(0.35 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.3
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.009 * SR)                               # 아주 좁은 스테레오. 기계는 넓으면 가짜 같다
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.96 + right * 0.04, right * 0.12 + mix * 0.88], axis=1)
    return st / (np.abs(st).max() + 1e-9) * 0.95


if __name__ == '__main__':
    np.random.seed(7)
    st = build()
    p = os.path.join(OUT, 'bgm_intro.wav')
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{p}  {DUR:.1f}s')
