"""
BLACKOUT — 티저용 EDM 트랙 + 효과음 합성.
저작권 문제 없게 전부 직접 만든 소리입니다. 128 BPM, F 마이너.
"""
import numpy as np
from scipy import signal

SR = 44100
BPM = 128.0
BEAT = 60.0 / BPM          # 0.46875s
BAR = BEAT * 4             # 1.875s
BARS = 15
DUR = BAR * BARS           # 28.125s
N = int(DUR * SR)

# F 마이너
NOTE = {'F1': 43.65, 'F2': 87.31, 'Ab2': 103.83, 'C3': 130.81, 'Db3': 138.59,
        'Eb3': 155.56, 'F3': 174.61, 'Ab3': 207.65, 'C4': 261.63, 'Db4': 277.18,
        'Eb4': 311.13, 'F4': 349.23, 'Ab4': 415.30}


def t_of(bar, beat=0.0):
    """1-based bar, 0-based beat → 초"""
    return (bar - 1) * BAR + beat * BEAT


def place(buf, sig, at):
    i = int(at * SR)
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i]


def env_ad(n, a, d, curve=3.0):
    t = np.arange(n) / SR
    atk = np.clip(t / max(a, 1e-6), 0, 1)
    dec = np.exp(-t / max(d, 1e-6) * curve)
    return atk * dec


def lp(x, cut, order=4):
    b, a = signal.butter(order, np.clip(cut / (SR / 2), 1e-4, 0.99), 'low')
    return signal.lfilter(b, a, x)


def hp(x, cut, order=4):
    b, a = signal.butter(order, np.clip(cut / (SR / 2), 1e-4, 0.99), 'high')
    return signal.lfilter(b, a, x)


def bp(x, lo, hi, order=4):
    b, a = signal.butter(order, [np.clip(lo / (SR / 2), 1e-4, 0.98),
                                 np.clip(hi / (SR / 2), 1e-3, 0.99)], 'band')
    return signal.lfilter(b, a, x)


# ── 개별 소리 ──────────────────────────────────────────────
def kick(dur=0.55, punch=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 42 + 150 * np.exp(-t * 38)                 # 피치 드롭
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = np.random.randn(n) * np.exp(-t * 420) * 0.35
    click = hp(click, 1200)
    return (body * 1.0 + click) * punch


def sub(note, dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = NOTE[note]
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    e = np.clip(t / 0.008, 0, 1) * np.exp(-t / (dur * 0.75))
    return x * e * gain


def supersaw(freqs, dur, cut=3200, detune=0.14, gain=1.0, voices=7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for v in range(voices):
            d = (v - (voices - 1) / 2) * detune / voices
            ph = np.random.rand()
            out += signal.sawtooth(2 * np.pi * (f + d * f * 0.01) * t + ph * 6.28)
    out /= (len(freqs) * voices)
    out = lp(out, cut)
    e = np.clip(t / 0.004, 0, 1) * np.exp(-t / (dur * 0.55))
    return out * e * gain


def noise_riser(dur, f0=300, f1=9000, gain=1.0):
    n = int(dur * SR)
    x = np.random.randn(n)
    out = np.zeros(n)
    step = int(SR * 0.04)
    for i in range(0, n, step):
        j = min(n, i + step)
        k = i / max(n - 1, 1)
        c = f0 * (f1 / f0) ** k
        out[i:j] = bp(x[i:j], c * 0.7, min(c * 1.6, SR / 2 * 0.98))
    t = np.arange(n) / SR
    e = (t / (dur)) ** 1.7
    return out * e * gain


def tone_riser(dur, f0=110, f1=1400, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur
    f = f0 * (f1 / f0) ** k
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    x = lp(x, 4000)
    return x * (k ** 2) * gain


def impact(dur=2.2, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 58 * np.exp(-t * 1.6) + 26
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crack = hp(np.random.randn(n), 900) * np.exp(-t * 16) * 0.5
    return (boom * 1.2 + crack) * gain


def clap(gain=1.0):
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for off, a in [(0, 0.7), (0.011, 0.85), (0.022, 1.0)]:
        i = int(off * SR)
        seg = np.random.randn(n - i) * np.exp(-np.arange(n - i) / SR * 55) * a
        x[i:] += seg
    x += np.random.randn(n) * np.exp(-t * 12) * 0.25
    return bp(x, 1100, 7500) * gain


def hat(dur=0.07, gain=1.0, open_=False):
    n = int((0.28 if open_ else dur) * SR)
    t = np.arange(n) / SR
    x = np.random.randn(n) * np.exp(-t * (14 if open_ else 90))
    return hp(x, 7000) * gain


def whoosh(dur=0.75, gain=1.0, rev=False):
    n = int(dur * SR)
    x = np.random.randn(n)
    out = np.zeros(n)
    step = int(SR * 0.03)
    for i in range(0, n, step):
        j = min(n, i + step)
        k = i / max(n - 1, 1)
        c = 400 * (7000 / 400) ** (1 - k if rev else k)
        out[i:j] = bp(x[i:j], c * 0.6, min(c * 1.9, SR / 2 * 0.98))
    t = np.arange(n) / SR
    e = np.sin(np.pi * t / dur) ** 1.5
    return out * e * gain


def glitch(gain=1.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 2400 * t)) * np.exp(-t * 60)
    x += np.random.randn(n) * np.exp(-t * 80) * 0.6
    return hp(x, 1500) * gain


def reverse_cymbal(dur=1.8, gain=1.0):
    n = int(dur * SR)
    x = hp(np.random.randn(n), 3500)
    t = np.arange(n) / SR
    return (x * np.exp(-t * 3.0))[::-1] * gain


def reverb(x, tail=1.5, mix=0.3):
    n = int(tail * SR)
    t = np.arange(n) / SR
    ir = np.random.randn(n) * np.exp(-t * (4.5 / tail))
    ir = lp(ir, 6500)
    ir[0] = 1.0
    ir /= np.abs(ir).sum() ** 0.5 * 3
    wet = signal.fftconvolve(x, ir)[:len(x)]
    return x * (1 - mix) + wet * mix


# ── 곡 구성 ────────────────────────────────────────────────
def build():
    drums = np.zeros(N)
    bass = np.zeros(N)
    lead = np.zeros(N)
    fx = np.zeros(N)

    kick_times = []

    # 인트로 임팩트 2방 (첫 훅)
    place(fx, impact(2.4, 0.95), t_of(1, 0))
    place(fx, glitch(0.7), t_of(1, 0))
    place(fx, impact(1.8, 0.7), t_of(1, 1.5))
    place(fx, glitch(0.6), t_of(1, 1.5))
    place(fx, reverse_cymbal(1.9, 0.35), t_of(2, 2))

    # 저음 드론 (긴장감)
    drone_n = int((t_of(9) - t_of(1)) * SR)
    td = np.arange(drone_n) / SR
    drone = (np.sin(2 * np.pi * NOTE['F1'] * td) * 0.5 +
             np.sin(2 * np.pi * NOTE['F1'] * 1.5 * td) * 0.12)
    drone *= np.clip(td / 2.0, 0, 1) * 0.5
    place(bass, drone, t_of(1))

    # 3~4마디: 하프타임 킥
    for bar in (3, 4):
        for b in (0, 2):
            at = t_of(bar, b)
            place(drums, kick(0.6, 0.75), at)
            kick_times.append(at)
        place(fx, hat(gain=0.12), t_of(bar, 1))
        place(fx, hat(gain=0.12), t_of(bar, 3))

    # 5~6마디: 킥 + 서브 그루브
    prog = [('F2', 'F3'), ('Db3', 'Db4')]
    for i, bar in enumerate((5, 6)):
        root = prog[i % 2][0]
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 0.95), at)
            kick_times.append(at)
            place(fx, hat(gain=0.16), t_of(bar, b + 0.5))
        place(bass, sub(root, BAR * 0.95, 0.55), t_of(bar))
        place(drums, clap(0.5), t_of(bar, 1))
        place(drums, clap(0.5), t_of(bar, 3))

    # 7~8마디: 빌드업
    place(fx, noise_riser(BAR * 2 - 0.2, 260, 11000, 0.5), t_of(7))
    place(fx, tone_riser(BAR * 2 - 0.2, 130, 1600, 0.16), t_of(7))
    for b in range(4):                     # 7마디: 4분
        at = t_of(7, b)
        place(drums, kick(0.5, 0.9), at)
        kick_times.append(at)
        place(drums, clap(0.35), at + BEAT * 0.5)
    div = [2, 2, 4, 8]                     # 8마디: 스네어 롤 가속
    for b in range(4):
        d = div[b]
        for k in range(d):
            at = t_of(8, b + k / d)
            place(drums, clap(0.28 + 0.3 * (b / 3)), at)
    place(fx, whoosh(0.9, 0.5), t_of(8, 2))

    # 8마디 마지막 반박자 = 무음 (드롭 직전 정적)
    gap0, gap1 = int(t_of(8, 3.4) * SR), int(t_of(9, 0) * SR)
    for buf in (drums, bass, lead, fx):
        buf[gap0:gap1] *= np.linspace(1, 0, gap1 - gap0) ** 2

    # 9~12마디: 드롭
    chords = [['F3', 'Ab3', 'C4'], ['Db3', 'F3', 'Ab3'],
              ['Ab2', 'C3', 'Eb3'], ['Eb3', 'Ab3', 'C4']]
    roots = ['F2', 'Db3', 'Ab2', 'Eb3']
    place(fx, impact(2.6, 1.0), t_of(9))
    for i, bar in enumerate(range(9, 13)):
        ch = [NOTE[x] for x in chords[i]]
        place(bass, sub(roots[i], BAR * 0.98, 0.75), t_of(bar))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 1.0), at)
            kick_times.append(at)
            place(fx, hat(gain=0.2), t_of(bar, b + 0.5))
            if b in (1, 3):
                place(drums, clap(0.62), at)
            # 스탭: 정박 + 엇박
            place(lead, supersaw(ch, BEAT * 0.9, 3600, 0.16, 0.28), at)
            place(lead, supersaw(ch, BEAT * 0.45, 2600, 0.16, 0.16), at + BEAT * 0.75)
        if bar == 12:
            place(fx, whoosh(0.8, 0.45, rev=True), t_of(bar, 3))

    # 13~14마디: 아웃트로 (필터 다운)
    for i, bar in enumerate((13, 14)):
        ch = [NOTE[x] for x in chords[i]]
        place(bass, sub(roots[i], BAR * 0.98, 0.5), t_of(bar))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 0.85 - i * 0.25), at)
            kick_times.append(at)
            place(lead, supersaw(ch, BEAT * 0.9, 2400 - i * 900, 0.16, 0.2), at)
        place(drums, clap(0.4 - i * 0.15), t_of(bar, 1))
        place(drums, clap(0.4 - i * 0.15), t_of(bar, 3))

    # 15마디: 마지막 임팩트 + 잔향
    place(fx, impact(2.6, 0.9), t_of(15))
    place(fx, reverse_cymbal(1.2, 0.25), t_of(14, 3))

    # 사이드체인 (킥마다 덕킹) — EDM 특유의 펌핑
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for at in kick_times:
        i = int(at * SR)
        j = min(N, i + int(0.34 * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / 0.34, 0.0, 1.0)
        duck[i:j] = np.minimum(duck[i:j], 0.22 + 0.78 * seg ** 0.55)
    bass *= duck
    lead *= duck ** 0.7

    mix = drums * 0.95 + bass * 0.9 + reverb(lead, 1.6, 0.32) * 0.85 + reverb(fx, 2.0, 0.34) * 0.7

    # 마스터: 하이패스 → 소프트클립 → 노멀라이즈 → 페이드아웃
    mix = hp(mix, 24, 2)
    mix = np.tanh(mix * 1.25) / np.tanh(1.25)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.94
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    # 살짝의 스테레오 폭
    delay = int(0.012 * SR)
    right = np.concatenate([np.zeros(delay), mix[:-delay]])
    st = np.stack([mix * 0.97 + right * 0.03, right * 0.12 + mix * 0.88], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95, sorted(set(kick_times))


if __name__ == '__main__':
    import wave, sys, os
    np.random.seed(7)
    st, kicks = build()
    out = os.path.join(os.path.dirname(__file__), 'out', 'bgm.wav')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}  {DUR:.2f}s  kicks={len(kicks)}  peak={np.abs(st).max():.3f}')
