"""
BLACKOUT 오프닝 2 — 하드 테크노 (140 BPM / A 마이너 / 29초)
오프닝 1(128 BPM EDM)과 완전히 다른 색: 왜곡된 킥, 오프비트 베이스,
금속 타격음, 애시드 스윕. 슈퍼소우 없음.
"""
import numpy as np
from scipy import signal
from audio import SR, place, lp, hp, bp, reverb

BPM = 140.0
BEAT = 60.0 / BPM            # 0.4286
BAR = BEAT * 4               # 1.7143
BARS = 17
DUR = BAR * BARS             # 29.14s
N = int(DUR * SR)

A1, A2, C3, D2, E2, G2 = 55.00, 110.00, 130.81, 73.42, 82.41, 98.00


def T(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


def sat(x, k=2.6):
    return np.tanh(x * k) / np.tanh(k)


# ── 악기 ───────────────────────────────────────────────────
def kick(dur=0.42, gain=1.0):
    """딱딱하고 짧은 테크노 킥"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 46 + 190 * np.exp(-t * 55)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    click = hp(np.random.randn(n), 2200) * np.exp(-t * 700) * 0.5
    return sat(body * 1.15 + click, 3.2) * gain


def rumble(dur, gain=1.0):
    """드럼 뒤에 깔리는 저역 울림"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(np.random.randn(n), 90) * 2.2
    x += np.sin(2 * np.pi * 41 * t) * 0.5
    e = np.clip(t / 0.05, 0, 1) * np.exp(-t / (dur * 0.7))
    return x * e * gain


def offbass(freq, dur=0.16, gain=1.0):
    """오프비트 베이스 스탭"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = signal.sawtooth(2 * np.pi * freq * t) * 0.6 + np.sin(2 * np.pi * freq * t)
    x = lp(x, 340)
    e = np.clip(t / 0.004, 0, 1) * np.exp(-t / (dur * 0.34))
    return sat(x * e, 1.8) * gain


def metal(dur=0.22, gain=1.0, seed=0):
    """금속 타격음 — 비조화 사인 다발"""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (1180, 1732, 2451, 3310, 4720, 6140):
        x += np.sin(2 * np.pi * f * (1 + rng.random() * 0.06) * t) / 6
    x += hp(rng.standard_normal(n), 4000) * 0.35
    return x * np.exp(-t * (28 / dur)) * gain


def acid(freqs, dur, gain=1.0, f0=220, f1=2600, q=6.0):
    """레조넌트 필터가 훑고 지나가는 애시드 라인"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    step = max(1, len(freqs))
    seg = n // step
    for i, f in enumerate(freqs):
        s0, s1 = i * seg, min(n, (i + 1) * seg)
        tt = np.arange(s1 - s0) / SR
        x[s0:s1] = signal.sawtooth(2 * np.pi * f * tt)
        x[s0:s1] *= np.exp(-tt * 6)
    out = np.zeros(n)
    chunk = int(SR * 0.02)
    for i in range(0, n, chunk):
        j = min(n, i + chunk)
        k = i / max(n - 1, 1)
        c = f0 * (f1 / f0) ** (np.sin(k * np.pi) ** 0.7)
        lo, hi = c / (1 + 1 / q), c * (1 + 1 / q)
        out[i:j] = bp(x[i:j], max(60, lo), min(hi, SR / 2 * 0.95))
    return sat(out * 1.4, 2.0) * gain


def hoover(freq, dur, gain=1.0):
    """내려꽂는 후버 — 드롭 직전 신호"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    bend = freq * (1 + 1.2 * np.exp(-t * 2.0))
    x = np.zeros(n)
    for d in (-0.14, -0.06, 0.0, 0.07, 0.15):
        x += signal.sawtooth(2 * np.pi * np.cumsum(bend * (1 + d)) / SR)
    x = lp(x / 5, 2600)
    return x * np.clip(t / 0.02, 0, 1) * np.exp(-t / (dur * 0.6)) * gain


def noise_up(dur, gain=1.0, f0=300, f1=11000):
    n = int(dur * SR)
    x = np.random.randn(n)
    out = np.zeros(n)
    step = int(SR * 0.03)
    for i in range(0, n, step):
        j = min(n, i + step)
        k = i / max(n - 1, 1)
        c = f0 * (f1 / f0) ** k
        out[i:j] = bp(x[i:j], c * 0.75, min(c * 1.5, SR / 2 * 0.97))
    t = np.arange(n) / SR
    return out * (t / dur) ** 2 * gain


def clang(dur=2.6, gain=1.0):
    """드롭용 대형 금속 임팩트"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * np.cumsum(52 * np.exp(-t * 1.4) + 28) / SR) * np.exp(-t * 1.9)
    met = metal(dur, 0.55, seed=9)
    return sat(low * 1.3 + met, 1.6) * gain


def hat(dur=0.05, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return hp(np.random.randn(n), 8500) * np.exp(-t * 130) * gain


def tape_stop(dur=0.5, gain=1.0, f=180):
    """테이프 멈추듯 피치가 떨어지는 소리"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = np.clip(1 - t / dur, 0, 1) ** 1.6
    x = signal.sawtooth(2 * np.pi * np.cumsum(f * k) / SR)
    return lp(x, 2600) * k * gain


# ── 구성 ───────────────────────────────────────────────────
def build():
    drums = np.zeros(N)
    bass = np.zeros(N)
    lead = np.zeros(N)
    fx = np.zeros(N)
    kicks = []

    # 1~2마디: 어둠 속 신호음
    place(fx, clang(2.8, 0.85), T(1))
    place(fx, metal(0.5, 0.4, 3), T(2, 0))
    place(fx, metal(0.5, 0.3, 5), T(2, 2))
    place(bass, rumble(BAR * 2, 0.5), T(1))

    # 3~6마디: 킥 입장 (4온플로어) + 오프비트 베이스
    for bar in range(3, 7):
        for b in range(4):
            at = T(bar, b)
            g = 0.72 if bar < 5 else 0.95
            place(drums, kick(0.42, g), at)
            kicks.append(at)
            if bar >= 4:
                place(bass, offbass(A1 if bar % 2 else G2 / 2, 0.16, 0.62), at + BEAT * 0.5)
            place(fx, hat(gain=0.10 if bar < 5 else 0.16), at + BEAT * 0.5)
        place(bass, rumble(BAR, 0.42), T(bar))
        if bar in (4, 6):
            place(drums, metal(0.3, 0.35, bar), T(bar, 2))

    # 7~10마디: 애시드 + 클랩 대신 금속 타격
    prog = [A2, A2, G2 * 2, E2 * 2]
    for i, bar in enumerate(range(7, 11)):
        root = prog[i]
        for b in range(4):
            at = T(bar, b)
            place(drums, kick(0.42, 1.0), at)
            kicks.append(at)
            place(bass, offbass(root / 2, 0.16, 0.7), at + BEAT * 0.5)
            place(fx, hat(gain=0.18), at + BEAT * 0.5)
            if b in (1, 3):
                place(drums, metal(0.24, 0.42, b + bar), at)
        place(lead, acid([root, root * 1.5, root, root * 1.2, root * 0.75, root, root * 2, root * 1.5],
                         BAR * 0.98, 0.3, 200, 3000), T(bar))
        place(bass, rumble(BAR, 0.5), T(bar))

    # 11~12마디: 빌드 — 킥 사라지고 노이즈만 차오름
    place(fx, noise_up(BAR * 2 - 0.1, 0.85), T(11))
    place(lead, hoover(A2, BAR * 1.6, 0.34), T(11, 2))
    for b in range(4):
        at = T(11, b)
        place(drums, kick(0.42, 0.9), at)
        kicks.append(at)
    for b in range(3):                       # 빌드 구간에도 킥은 남긴다
        at = T(12, b)
        place(drums, kick(0.42, 0.85 - b * 0.15), at)
        kicks.append(at)
    div = [2, 4, 8, 16]
    for b in range(4):
        for k in range(div[b]):
            place(drums, metal(0.12, 0.14 + 0.2 * (b / 3), k + b), T(12, b + k / div[b]))
    place(fx, tape_stop(0.45, 0.4, 220), T(12, 3))

    # 드롭 직전 정적
    g0, g1 = int(T(12, 3.5) * SR), int(T(13, 0) * SR)
    for buf in (drums, bass, lead, fx):
        buf[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 2

    # 13~17마디: 드롭
    place(fx, clang(3.0, 1.0), T(13))
    droot = [A2, A2, G2 * 2, E2 * 2, A2]
    for i, bar in enumerate(range(13, 18)):
        root = droot[i]
        place(bass, rumble(BAR, 0.72), T(bar))
        for b in range(4):
            at = T(bar, b)
            place(drums, kick(0.42, 1.0), at)
            kicks.append(at)
            place(bass, offbass(root / 2, 0.17, 0.85), at + BEAT * 0.5)
            place(fx, hat(gain=0.2), at + BEAT * 0.5)
            if b in (1, 3):
                place(drums, metal(0.26, 0.5, b * 3 + bar), at)
        if bar < 17:
            place(lead, acid([root, root * 1.5, root * 0.75, root, root * 2, root * 1.5, root, root * 1.25],
                             BAR * 0.98, 0.34, 260, 3600), T(bar))
    place(fx, clang(2.2, 0.7), T(17, 2))

    # 사이드체인
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR)
        j = min(N, i + int(0.26 * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / 0.26, 0.0, 1.0)
        duck[i:j] = np.minimum(duck[i:j], 0.18 + 0.82 * seg ** 0.5)
    bass *= duck
    lead *= duck ** 0.8

    mix = drums * 1.0 + bass * 0.95 + reverb(lead, 1.2, 0.24) * 0.8 + reverb(fx, 1.8, 0.3) * 0.7
    mix = hp(mix, 26, 2)
    mix = sat(mix * 0.9, 1.5)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.95
    f = int(0.4 * SR)
    mix[-f:] *= np.linspace(1, 0, f) ** 1.3
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.009 * SR)
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.96 + right * 0.04, right * 0.14 + mix * 0.86], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95


if __name__ == '__main__':
    import wave, os
    np.random.seed(31)
    st = build()
    out = os.path.join(os.path.dirname(__file__), 'out', 'bgm_open2.wav')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}  {DUR:.2f}s  peak={np.abs(st).max():.3f}')
