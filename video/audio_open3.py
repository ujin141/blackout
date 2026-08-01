"""
BLACKOUT 오프닝 3 — 브레이크비트 / 드럼앤베이스 (174 BPM / 29초)

오프닝 1(128 하우스)·2(140 하드테크노)와 리듬 자체를 다르게 간다.
4온플로어를 쓰지 않는다. 킥은 1박, 스네어는 3박, 그 사이를 브레이크가 메운다.
리스 베이스와 서브가 중심이고 슈퍼소우·애시드는 쓰지 않는다.
"""
import numpy as np
from scipy import signal
from audio import SR, place, lp, hp, bp, reverb

BPM = 174.0
BEAT = 60.0 / BPM             # 0.3448
BAR = BEAT * 4                # 1.3793
BARS = 21
DUR = BAR * BARS              # 28.97s
N = int(DUR * SR)

STEP = BAR / 16.0             # 16분음
D1, F1, A1, C2 = 36.71, 43.65, 55.00, 65.41


def T(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


def S(bar, step):
    """16분음 단위 위치"""
    return (bar - 1) * BAR + step * STEP


def sat(x, k=2.2):
    return np.tanh(x * k) / np.tanh(k)


# ── 악기 ───────────────────────────────────────────────────
def kick(dur=0.30, gain=1.0):
    """짧고 단단한 브레이크비트 킥"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 52 + 150 * np.exp(-t * 80)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 16)
    click = hp(np.random.randn(n), 3000) * np.exp(-t * 900) * 0.45
    return sat(body * 1.1 + click, 2.6) * gain


def snare(dur=0.34, gain=1.0, tight=1.0):
    """노이즈 + 두 개의 몸통 톤"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = bp(np.random.randn(n), 1500, 8200) * np.exp(-t * (34 * tight))
    tone = (np.sin(2 * np.pi * 182 * t) + np.sin(2 * np.pi * 331 * t) * 0.7)
    tone *= np.exp(-t * (46 * tight)) * 0.5
    crack = hp(np.random.randn(n), 6000) * np.exp(-t * 260) * 0.3
    return sat(nz * 0.9 + tone + crack, 1.9) * gain


def ghost(gain=0.3):
    return snare(0.12, gain, tight=2.6)


def hat(dur=0.045, gain=1.0, open_=False):
    n = int(dur * (3.4 if open_ else 1.0) * SR)
    t = np.arange(n) / SR
    x = hp(np.random.randn(n), 9000)
    return x * np.exp(-t * (28 if open_ else 150)) * gain


def ride(dur=0.5, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (3100, 4270, 5590, 7300):
        x += np.sin(2 * np.pi * f * t) / 4
    x += hp(np.random.randn(n), 7000) * 0.6
    return x * np.exp(-t * 9) * gain


def sub(freq, dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t)
    e = np.clip(t / 0.012, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return x * e * gain


def reese(freq, dur, gain=1.0, detune=0.55, notch=True):
    """리스 베이스 — 디튠된 소우 세 개를 겹치고 노치로 훑는다"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for d in (-detune, 0.0, detune):
        lfo = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * t + d)
        x += signal.sawtooth(2 * np.pi * np.cumsum(freq * (1 + d / 100) * lfo) / SR)
    x = x / 3
    if notch:
        out = np.zeros(n)
        chunk = int(SR * 0.03)
        for i in range(0, n, chunk):
            j = min(n, i + chunk)
            k = i / max(n - 1, 1)
            c = 180 * (2400 / 180) ** (0.5 - 0.5 * np.cos(k * 2 * np.pi))
            out[i:j] = x[i:j] - bp(x[i:j], c * 0.8, min(c * 1.25, SR / 2 * 0.9)) * 0.85
        x = out
    x = lp(x, 3200)
    e = np.clip(t / 0.02, 0, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return sat(x * e * 1.3, 1.7) * gain


def blip(freq=1400, dur=0.09, gain=1.0):
    """계측기 신호음"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t)
    return x * np.exp(-t * 40) * gain


def sweep_down(dur=1.2, gain=1.0, f0=9000, f1=200):
    n = int(dur * SR)
    x = np.random.randn(n)
    out = np.zeros(n)
    st = int(SR * 0.03)
    for i in range(0, n, st):
        j = min(n, i + st)
        k = i / max(n - 1, 1)
        c = f0 * (f1 / f0) ** k
        out[i:j] = bp(x[i:j], c * 0.7, min(c * 1.6, SR / 2 * 0.96))
    t = np.arange(n) / SR
    return out * np.exp(-t * 1.6) * gain


def riser(dur, gain=1.0, f0=260, f1=10000):
    n = int(dur * SR)
    x = np.random.randn(n)
    out = np.zeros(n)
    st = int(SR * 0.025)
    for i in range(0, n, st):
        j = min(n, i + st)
        k = i / max(n - 1, 1)
        c = f0 * (f1 / f0) ** (k ** 1.3)
        out[i:j] = bp(x[i:j], c * 0.75, min(c * 1.55, SR / 2 * 0.97))
    t = np.arange(n) / SR
    return out * (t / dur) ** 2.2 * gain


def impact(dur=2.6, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-t * 2.2) + 30) / SR) * np.exp(-t * 2.1)
    body = lp(np.random.randn(n), 400) * np.exp(-t * 5) * 0.6
    air = hp(np.random.randn(n), 4000) * np.exp(-t * 8) * 0.25
    return sat(low * 1.25 + body + air, 1.6) * gain


def rev_cym(dur=1.6, gain=1.0):
    n = int(dur * SR)
    x = hp(np.random.randn(n), 5200)
    t = np.arange(n) / SR
    return x * (t / dur) ** 3 * gain


# ── 브레이크 패턴 ──────────────────────────────────────────
# 16분 그리드. 킥 1박 · 스네어 3박이 뼈대, 나머지는 변주.
PATTERNS = [
    dict(k=[0, 10], s=[8], g=[6, 14]),
    dict(k=[0, 10], s=[8], g=[3, 14]),
    dict(k=[0, 6, 10], s=[8], g=[14]),
    dict(k=[0, 10, 11], s=[8], g=[4, 14]),
]


def lay_break(drums, bar, pat, kicks, gk=1.0, gs=1.0, hats=True):
    for st in pat['k']:
        at = S(bar, st)
        place(drums, kick(0.30, gk), at)
        kicks.append(at)
    for st in pat['s']:
        place(drums, snare(0.34, gs), S(bar, st))
    for st in pat.get('g', []):
        place(drums, ghost(0.22 * gs), S(bar, st))
    if hats:
        for st in range(0, 16, 2):
            place(drums, hat(gain=0.10 if st % 4 else 0.15), S(bar, st))
        place(drums, hat(gain=0.13, open_=True), S(bar, 14))


# ── 구성 ───────────────────────────────────────────────────
def build():
    drums = np.zeros(N)
    bass = np.zeros(N)
    lead = np.zeros(N)
    fx = np.zeros(N)
    kicks = []

    # 1~2마디: 계측 신호. 리듬 없음.
    place(fx, impact(2.4, 0.7), T(1))
    for i, st in enumerate((0, 6, 12, 20, 24, 30)):
        place(fx, blip(1200 + i * 180, 0.08, 0.22), S(1, st % 16) + (BAR if st >= 16 else 0))
    place(bass, sub(D1, BAR * 2, 0.35), T(1))
    place(fx, rev_cym(1.4, 0.3), T(2, 2.6))

    # 3~6마디: 브레이크 진입
    for i, bar in enumerate(range(3, 7)):
        g = 0.75 if bar < 5 else 1.0
        lay_break(drums, bar, PATTERNS[i % 4], kicks, gk=g, gs=g, hats=bar >= 4)
        place(bass, sub(D1 if bar % 2 else F1, BAR * 0.96, 0.5), T(bar))
        if bar >= 5:
            place(bass, reese(D1 * 2 if bar % 2 else F1 * 2, BAR * 0.9, 0.20), T(bar))

    # 7~9마디: 리스 전면. 밀도 상승.
    roots = [D1, F1, A1]
    for i, bar in enumerate(range(7, 10)):
        r = roots[i]
        lay_break(drums, bar, PATTERNS[(i + 2) % 4], kicks, gk=1.0, gs=1.0)
        place(bass, sub(r, BAR * 0.96, 0.6), T(bar))
        place(bass, reese(r * 2, BAR * 0.92, 0.34), T(bar))
        place(fx, ride(0.5, 0.12), S(bar, 8))
        if bar == 9:
            place(fx, sweep_down(1.0, 0.3), T(bar, 2))

    # 10~13마디: 빌드. 12~13은 드럼을 비우고 라이저만.
    for bar in (10, 11):
        lay_break(drums, bar, PATTERNS[bar % 4], kicks, gk=1.0, gs=1.0)
        place(bass, sub(C2 / 2, BAR * 0.96, 0.6), T(bar))
        place(bass, reese(C2, BAR * 0.92, 0.36), T(bar))
    # 12: 스네어 롤
    div = [4, 4, 8, 16]
    for b in range(4):
        for k in range(div[b]):
            place(drums, snare(0.16, 0.22 + 0.3 * (b / 3), tight=1.8),
                  T(12, b + k / div[b]))
    place(drums, kick(0.30, 0.9), T(12))
    kicks.append(T(12))
    place(fx, riser(BAR * 2 - 0.05, 0.9), T(12))
    place(bass, reese(A1, BAR * 2, 0.3, detune=1.1), T(12))
    # 13: 흰 화면 구간 — 드럼 없이 라이저만 차오른다
    place(fx, rev_cym(BAR * 0.9, 0.45), T(13))

    # 드롭 직전 완전 정적
    g0, g1 = int(T(13, 3.55) * SR), int(T(14, 0) * SR)
    for buf in (drums, bass, lead, fx):
        buf[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 2

    # 14~21마디: 드롭
    place(fx, impact(3.2, 1.0), T(14))
    droot = [D1, D1, F1, F1, A1, A1, C2 / 2, D1]
    for i, bar in enumerate(range(14, 22)):
        r = droot[i]
        lay_break(drums, bar, PATTERNS[i % 4], kicks, gk=1.0, gs=1.05)
        place(bass, sub(r, BAR * 0.97, 0.78), T(bar))
        place(bass, reese(r * 2, BAR * 0.94, 0.42), T(bar))
        place(fx, ride(0.55, 0.14), S(bar, 8))
        if bar in (17, 21):
            place(fx, sweep_down(0.9, 0.26), T(bar, 3))
    place(fx, impact(2.0, 0.6), T(21, 2))

    # 사이드체인 — 킥에만 짧게
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR)
        j = min(N, i + int(0.17 * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / 0.17, 0.0, 1.0)
        duck[i:j] = np.minimum(duck[i:j], 0.32 + 0.68 * seg ** 0.6)
    bass *= duck

    mix = drums * 1.0 + bass * 1.0 + reverb(lead, 1.0, 0.2) * 0.7 + reverb(fx, 1.6, 0.28) * 0.7
    mix = hp(mix, 28, 2)
    mix = sat(mix * 0.92, 1.4)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.95
    f = int(0.35 * SR)
    mix[-f:] *= np.linspace(1, 0, f) ** 1.3
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.007 * SR)
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.95 + right * 0.05, right * 0.16 + mix * 0.84], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95


if __name__ == '__main__':
    import wave, os
    np.random.seed(74)
    st = build()
    out = os.path.join(os.path.dirname(__file__), 'out', 'bgm_open3.wav')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}  {DUR:.2f}s  peak={np.abs(st).max():.3f}')
