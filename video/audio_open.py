"""
BLACKOUT 오프닝용 트랙 (30초 / 128BPM / F 마이너).
티저보다 느리게 깔고, 22.5초에 드롭 후 끝까지 유지.
"""
import numpy as np
from audio import (SR, BEAT, BAR, NOTE, place, kick, sub, supersaw, noise_riser,
                   tone_riser, impact, clap, hat, whoosh, glitch, reverse_cymbal,
                   reverb, lp, hp)

BARS = 16
DUR = BAR * BARS            # 정확히 30.0초
N = int(DUR * SR)


def t_of(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


def pad(freqs, dur, cut=1400, gain=1.0, attack=0.6):
    """느리게 부풀어 오르는 패드 — 웅장함 담당"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for d in (-0.11, 0.0, 0.13):
            x += np.sin(2 * np.pi * (f + d) * t + np.random.rand() * 6.28)
            x += 0.35 * np.sin(2 * np.pi * (f + d) * 2 * t)
    x /= (len(freqs) * 3)
    x = lp(x, cut)
    e = np.clip(t / attack, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    return x * e * gain


def brass(freqs, dur, gain=1.0):
    """묵직한 신스 브라스 스탭"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        ph = 2 * np.pi * f * t
        x += np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.28 * np.sin(3 * ph) + 0.15 * np.sin(4 * ph)
    x /= len(freqs)
    e = np.clip(t / 0.09, 0, 1) * np.exp(-t / (dur * 0.5))
    return lp(x, 2600) * e * gain


def build():
    drums = np.zeros(N)
    bass = np.zeros(N)
    lead = np.zeros(N)
    fx = np.zeros(N)
    kicks = []

    # ── 1~2마디: 어둠. 첫 한 방 + 드론 ────────────────────
    place(fx, impact(3.2, 1.0), t_of(1))
    place(fx, glitch(0.5), t_of(1))
    place(fx, reverse_cymbal(2.4, 0.3), t_of(2, 2))

    dn = int((t_of(13) - t_of(1)) * SR)
    td = np.arange(dn) / SR
    drone = (np.sin(2 * np.pi * NOTE['F1'] * td) * 0.55 +
             np.sin(2 * np.pi * NOTE['F1'] * 1.5 * td) * 0.1)
    drone *= np.clip(td / 3.0, 0, 1) * 0.5
    place(bass, drone, t_of(1))

    # ── 3~4마디: 심장박동 같은 킥 ─────────────────────────
    for bar in (3, 4):
        at = t_of(bar, 0)
        place(drums, kick(0.9, 0.7), at)
        kicks.append(at)
        place(drums, kick(0.7, 0.4), t_of(bar, 2.5))
        kicks.append(t_of(bar, 2.5))
    place(fx, whoosh(1.1, 0.35, rev=True), t_of(4, 2))

    # ── 5~6마디: 패드 + 브라스로 무게 ─────────────────────
    place(lead, pad([NOTE['F3'], NOTE['Ab3'], NOTE['C4']], BAR * 2, 1300, 0.32), t_of(5))
    for bar in (5, 6):
        place(lead, brass([NOTE['F2'], NOTE['F3']], BEAT * 2.4, 0.3), t_of(bar, 0))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.6, 0.72), at)
            kicks.append(at)
            place(fx, hat(gain=0.1), t_of(bar, b + 0.5))
        place(bass, sub('F2', BAR * 0.95, 0.5), t_of(bar))

    # ── 7~8마디: 4온플로어 + 클랩 ─────────────────────────
    place(lead, pad([NOTE['Db3'], NOTE['F3'], NOTE['Ab3']], BAR * 2, 1700, 0.34), t_of(7))
    for i, bar in enumerate((7, 8)):
        root = 'Db3' if i == 0 else 'Ab2'
        place(bass, sub(root, BAR * 0.95, 0.6), t_of(bar))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 0.9), at)
            kicks.append(at)
            place(fx, hat(gain=0.15), t_of(bar, b + 0.5))
        place(drums, clap(0.45), t_of(bar, 1))
        place(drums, clap(0.45), t_of(bar, 3))

    # ── 9~10마디: 본격 그루브 + 라이저 시작 ───────────────
    prog = [('F2', ['F3', 'Ab3', 'C4']), ('Db3', ['Db3', 'F3', 'Ab3'])]
    for i, bar in enumerate((9, 10)):
        root, ch = prog[i]
        place(bass, sub(root, BAR * 0.95, 0.7), t_of(bar))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 0.95), at)
            kicks.append(at)
            place(fx, hat(gain=0.18), t_of(bar, b + 0.5))
            place(lead, supersaw([NOTE[x] for x in ch], BEAT * 0.8, 2400, 0.16, 0.14), at)
        place(drums, clap(0.5), t_of(bar, 1))
        place(drums, clap(0.5), t_of(bar, 3))
    place(fx, noise_riser(BAR * 4 - 0.2, 200, 12000, 0.52), t_of(9))
    place(fx, tone_riser(BAR * 4 - 0.2, 110, 1800, 0.15), t_of(9))

    # ── 11~12마디: 빌드업 (스네어 롤 가속) ────────────────
    place(lead, pad([NOTE['F3'], NOTE['Ab3'], NOTE['C4'], NOTE['F4']], BAR * 2, 3200, 0.3, 1.2), t_of(11))
    for b in range(4):
        at = t_of(11, b)
        place(drums, kick(0.5, 0.92), at)
        kicks.append(at)
        place(drums, clap(0.34), at + BEAT * 0.5)
    for b, d in enumerate([2, 4, 8, 16]):
        for k in range(d):
            place(drums, clap(0.22 + 0.36 * (b / 3)), t_of(12, b + k / d))
    place(fx, whoosh(1.0, 0.5), t_of(12, 2))

    # 드롭 직전 정적
    g0, g1 = int(t_of(12, 3.45) * SR), int(t_of(13, 0) * SR)
    for buf in (drums, bass, lead, fx):
        buf[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 2

    # ── 13~16마디: 드롭 유지 ──────────────────────────────
    place(fx, impact(3.0, 1.0), t_of(13))
    chords = [['F3', 'Ab3', 'C4'], ['Db3', 'F3', 'Ab3'],
              ['Ab2', 'C3', 'Eb3'], ['Eb3', 'Ab3', 'C4']]
    roots = ['F2', 'Db3', 'Ab2', 'Eb3']
    for i, bar in enumerate(range(13, 17)):
        ch = [NOTE[x] for x in chords[i]]
        place(bass, sub(roots[i], BAR * 0.98, 0.78), t_of(bar))
        place(lead, brass([NOTE[roots[i]]], BEAT * 1.6, 0.22), t_of(bar))
        for b in range(4):
            at = t_of(bar, b)
            place(drums, kick(0.55, 1.0), at)
            kicks.append(at)
            place(fx, hat(gain=0.2), t_of(bar, b + 0.5))
            if b in (1, 3):
                place(drums, clap(0.6), at)
            place(lead, supersaw(ch, BEAT * 0.9, 3600, 0.16, 0.3), at)
            place(lead, supersaw(ch, BEAT * 0.42, 2500, 0.16, 0.16), at + BEAT * 0.75)
    place(fx, impact(2.0, 0.75), t_of(16, 3))

    # 사이드체인
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR)
        j = min(N, i + int(0.32 * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / 0.32, 0.0, 1.0)
        duck[i:j] = np.minimum(duck[i:j], 0.24 + 0.76 * seg ** 0.55)
    bass *= duck
    lead *= duck ** 0.7

    mix = drums * 0.95 + bass * 0.92 + reverb(lead, 1.8, 0.34) * 0.9 + reverb(fx, 2.2, 0.36) * 0.72
    mix = hp(mix, 24, 2)
    mix = np.tanh(mix * 1.22) / np.tanh(1.22)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.94
    f = int(0.45 * SR)
    mix[-f:] *= np.linspace(1, 0, f) ** 1.4
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.012 * SR)
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.97 + right * 0.03, right * 0.12 + mix * 0.88], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95


if __name__ == '__main__':
    import wave, os
    np.random.seed(11)
    st = build()
    out = os.path.join(os.path.dirname(__file__), 'out', 'bgm_open.wav')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{out}  {DUR:.2f}s  peak={np.abs(st).max():.3f}')
