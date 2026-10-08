"""
**할로윈 릴스 곡 셋 — 두 번째 판.** 첫 판은 "재미없다" 였다.

    python audio_halloween.py          →  out/halloween/bgm_{organ,musicbox,carpenter}.wav

## 왜 재미없었나

분위기만 있고 **사건이 없었다.** 종 · 아르페지오 · 펄스가 12초 내내 같은 세기로 흘렀다.
릴스 곡은 짧은 노래다 — 첫 1초에 훅, 2~3초 빌드, 4초 전후에 **드롭**, 그 뒤 끝까지 터진다.

    organ       128BPM  천둥 → 오르간 리프(훅) → 스네어 롤 → 드롭: 4/4 킥 · 펌핑 베이스 · 종
    musicbox    150BPM  오케스트라 히트 '쾅' → 오르골 훅 → 트랩 드롭: 808 미끄럼 · 32분 하이햇 롤
    carpenter   120BPM  비명 같은 상승음 → 단조 톱니 리드 → 드롭: 16분 베이스 · 게이트 스네어

선율은 전부 새로 쓴다. 남의 할로윈 테마는 안 쓴다.
"""
import os
import sys
import wave

import numpy as np

from audio import SR, clap, hat, hp, kick, lp, noise_riser, place, reverb
from audio_reel import hard_kick, sat, snare

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'halloween')
os.makedirs(OUT, exist_ok=True)
DUR = 13.0


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, d, s=0.0, r=0.03):
    t = np.arange(n) / SR
    e = np.clip(t / max(a, 1e-4), 0, 1) * (s + (1 - s) * np.exp(-t / max(d, 1e-4)))
    e *= np.clip((n / SR - t) / max(r, 1e-4), 0, 1)
    return e.astype(np.float32)


def buf_():
    return np.zeros(int(SR * DUR), np.float32)


# ── 소리 ──────────────────────────────────────────────
def thunder(dur=2.6, gain=1.0):
    n = int(SR * dur)
    rng = np.random.default_rng(13)
    x = rng.standard_normal(n).astype(np.float32)
    t = np.arange(n) / SR
    crack = hp(x, 1800, 2) * np.exp(-t / 0.05) * 0.6
    rumble = lp(x, 160, 2) * (np.exp(-t / 0.9) * (1 + 0.6 * np.sin(2 * np.pi * 3.3 * t))) * 3.0
    return sat((crack + rumble) * gain, 1.5) * 0.8


def bell(f, dur, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, a, dec in ((1.0, 1.0, 2.2), (2.76, 0.55, 1.2), (5.40, 0.35, 0.6), (0.5, 0.45, 2.6)):
        out += a * np.sin(2 * np.pi * f * k * t) * np.exp(-t / dec)
    return out * gain * 0.35


def organ(f, dur, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, a in ((1, 1.0), (2, 0.8), (3, 0.5), (4, 0.4), (6, 0.25), (8, 0.18)):
        out += a * np.sin(2 * np.pi * f * k * t + 0.3 * np.sin(2 * np.pi * 6 * t))
    return sat(out * env(n, 0.005, 9, 1.0, 0.02) * gain * 0.10, 1.6)


def bass(f, dur, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sign(np.sin(2 * np.pi * f * t))
    return (lp(x.astype(np.float32), 600, 2) * env(n, 0.004, 0.25, 0.4, 0.02) * gain * 0.5).astype(np.float32)


def musicbox(f, dur, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.004 * np.sin(2 * np.pi * 0.7 * t))) / SR
    out = np.sin(ph) * np.exp(-t / 0.8) + 0.45 * np.sin(3 * ph) * np.exp(-t / 0.22) + 0.2 * np.sin(5.04 * ph) * np.exp(-t / 0.08)
    return out.astype(np.float32) * np.clip(t / 0.002, 0, 1) * gain * 0.34


def orch_hit(root, dur=1.2, gain=1.0):
    """오케스트라 히트. 톱니 화음 + 금관 같은 필터 + 팀파니."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in (root, root + 3, root + 7, root + 12, root - 12):
        for det in (0.995, 1.0, 1.006):
            x += 2 * ((hz(m) * det * t) % 1.0) - 1
    x = lp(x, 2600, 2) * np.exp(-t / 0.35)
    timp = np.sin(2 * np.pi * (hz(root - 24) * (1 + 0.5 * np.exp(-t / 0.05))) * t) * np.exp(-t / 0.5) * 3
    return sat((x * 0.08 + timp * 0.3) * gain, 1.8)


def sub808(f, dur, slide_to=None, gain=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    fr = f * (1 + 1.2 * np.exp(-t / 0.03))
    if slide_to:
        fr = fr + (slide_to - f) * np.clip((t - dur * 0.55) / (dur * 0.3), 0, 1)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return sat(np.sin(ph) * env(n, 0.002, 1.2, 0.0, 0.05) * gain, 2.0) * 0.75


def lead(notes, step, gain=1.0, cut=2400):
    """톱니 리드. 비브라토, 음 사이 살짝 미끄럼."""
    n = int(SR * step * len(notes))
    t = np.arange(n) / SR
    tgt = np.repeat([hz(m) for m in notes], int(SR * step))[:n].astype(np.float32)
    k = 1 - np.exp(-1 / (SR * 0.02))
    f = np.empty(n, np.float32)
    acc = tgt[0]
    for i in range(n):
        acc += (tgt[i] - acc) * k
        f[i] = acc
    f *= 1 + 0.008 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.5, 0, 1)
    ph = np.cumsum(f) / SR
    x = (2 * (ph % 1.0) - 1) + 0.7 * (2 * ((ph * 1.007) % 1.0) - 1)
    gate = np.ones(n, np.float32)
    step_n = int(SR * step)
    for i in range(len(notes)):
        g0 = i * step_n
        gate[g0:g0 + step_n] = env(min(step_n, n - g0), 0.004, 0.3, 0.55, 0.02)
    return (lp(x.astype(np.float32), cut, 2) * gate * gain * 0.22).astype(np.float32)


def scream(dur=2.2, gain=1.0):
    """비명처럼 올라가는 톱니. 빌드용."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 200 * 2 ** (t / dur * 3.2)
    ph = np.cumsum(f * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))) / SR
    x = 2 * (ph % 1.0) - 1
    return (lp(x.astype(np.float32), 3500, 2) * np.clip(t / dur, 0, 1) ** 1.5 * gain * 0.25).astype(np.float32)


def roll(start, end, b, gain=0.8):
    """빌드 스네어 롤. 갈수록 빨라지고 커진다."""
    hits = []
    t = start
    k = 0
    while t < end:
        frac = (t - start) / (end - start)
        step = b / (2 if frac < 0.5 else 4 if frac < 0.8 else 8)
        hits.append((t, gain * (0.4 + 0.6 * frac)))
        t += step
        k += 1
    return hits


def pump(buf, beats, depth=0.6, rel=0.18):
    """사이드체인. 킥마다 다른 소리를 눌렀다 놓는다 — 그게 '펌핑'이다."""
    g = np.ones(len(buf), np.float32)
    n = int(SR * rel)
    shape = 1 - depth * (1 - np.linspace(0, 1, n) ** 0.6)
    for t in beats:
        i = int(t * SR)
        j = min(len(g), i + n)
        g[i:j] = np.minimum(g[i:j], shape[:j - i])
    return buf * g


# ══════════════════════════════════════════════════════════
#  1. 오르간 일렉트로 하우스 128
# ══════════════════════════════════════════════════════════

def organ_track():
    b = 60 / 128
    s16 = b / 4
    drop = 8 * b                       # 셋째 마디
    music, drums = buf_(), buf_()
    place(drums, thunder(3.0, 1.0), 0.0)
    # 훅: D minor 오르간 리프. 당김음이 있어야 따라 흥얼거린다
    riff = [(0, 74), (2, 74), (3, 77), (5, 74), (6, 81), (8, 79), (10, 77), (11, 76), (12, 74), (14, 72)]
    riff2 = [(0, 70), (2, 70), (3, 74), (5, 70), (6, 77), (8, 76), (10, 74), (11, 72), (12, 70), (14, 69)]
    for bar in range(int(DUR / (4 * b)) + 1):
        r = riff if bar % 2 == 0 else riff2
        for pos, m in r:
            place(music, organ(hz(m), s16 * 1.6, 1.0 if bar >= 2 else 0.95), bar * 4 * b + pos * s16)
    # 빌드: 박수 2 · 4 · 롤 · 상승음
    for k in range(8):
        place(drums, lp(kick(0.4, 0.8), 300, 2) * 0.7, k * b)       # 첫 박부터 걸음
        if k % 2 == 1:
            place(drums, clap(0.8), k * b)
    for t, g in roll(drop - 4 * b, drop, b):
        place(drums, snare(0.12, g * 0.7), t)
    place(drums, noise_riser(4 * b, 400, 9000, 0.35), drop - 4 * b)
    # 드롭
    place(music, bell(hz(50), 3.0, 1.2), drop)
    kicks = [drop + k * b for k in range(int((DUR - drop) / b))]
    roots = [38, 38, 34, 36]
    for k, t in enumerate(kicks):
        place(drums, hard_kick(0.4, 1.0), t)
        place(drums, hat(0.07, 0.55, open_=True), t + b / 2)
        if k % 2 == 1:
            place(drums, clap(0.9), t)
        r = roots[(k // 4) % 4]
        place(music, bass(hz(r), b * 0.45, 1.0), t + b / 2)
        place(music, bass(hz(r + 12), b * 0.22, 0.7), t + b * 0.75)
    music = pump(music, kicks, 0.65)
    return reverb(music, 1.4, 0.18) + drums


# ══════════════════════════════════════════════════════════
#  2. 오르골 트랩 150 (하프타임)
# ══════════════════════════════════════════════════════════

def musicbox_track():
    b = 60 / 150
    drop = 8 * b
    music, drums = buf_(), buf_()
    place(drums, orch_hit(50, 1.6, 1.2), 0.0)
    place(drums, orch_hit(49, 1.2, 0.9), 2 * b)
    mel = [76, 79, 83, 82, 79, 76, 75, 76, 79, 81, 79, 75, 72, 71, 72, 76]
    for rep in range(4):
        for i, m in enumerate(mel):
            place(music, musicbox(hz(m), 1.0, 0.85), rep * 16 * b / 2 + i * b / 2)
    # 빌드: 하이햇 점점 촘촘히 + 808 위로
    for k in range(16):
        place(drums, hat(0.03, 0.3), 4 * b + k * b / 4)
    place(drums, noise_riser(4 * b, 300, 8000, 0.3), drop - 4 * b)
    # 드롭: 킥(808) · 스네어 3박 · 하이햇 롤 · 히트
    bars = int((DUR - drop) / (4 * b)) + 1
    for bar in range(bars):
        t0 = drop + bar * 4 * b
        place(drums, orch_hit(52 if bar % 2 == 0 else 50, 1.0, 0.9), t0)
        place(music, sub808(hz(40), 1.4, hz(43) if bar % 2 else None, 1.0), t0)
        place(music, sub808(hz(40), 0.5, None, 0.8), t0 + 1.5 * b)
        place(music, sub808(hz(47), 0.7, hz(40), 0.85), t0 + 3 * b)
        place(drums, snare(0.25, 1.0), t0 + 2 * b)
        place(drums, clap(0.6), t0 + 2 * b)
        for k in range(8):
            place(drums, hat(0.025, 0.4), t0 + k * b / 2)
        for k in range(8):                                    # 32분 롤
            place(drums, hat(0.015, 0.25 + k * 0.03), t0 + 3 * b + k * b / 8)
        for k in range(3):                                    # 셋잇단 롤
            place(drums, hat(0.02, 0.35), t0 + 1.5 * b + k * b / 3)
    return reverb(music, 1.4, 0.22) + drums


# ══════════════════════════════════════════════════════════
#  3. 다크 신스웨이브 120
# ══════════════════════════════════════════════════════════

def carpenter_track():
    b = 60 / 120
    s16 = b / 4
    drop = 8 * b
    music, drums = buf_(), buf_()
    place(music, scream(drop, 1.0), 0.0)
    # 리드 훅: A minor, 단2도로 끌어내린다
    hook = [69, 72, 76, 75, 72, 69, 68, 69]
    hook2 = [69, 72, 76, 79, 77, 76, 72, 71]
    for rep in range(int(DUR / (4 * b)) + 1):
        place(music, lead(hook if rep % 2 == 0 else hook2, b / 2, 0.95), rep * 4 * b)
    # 빌드: 킥 4분 → 8분 → 16분
    for k in range(4):
        place(drums, kick(0.35, 0.7), k * b)
    for k in range(8):
        place(drums, kick(0.3, 0.6), 4 * b + k * b / 2)
    for t, g in roll(drop - 2 * b, drop, b, 0.7):
        place(drums, snare(0.1, g * 0.6), t)
    # 드롭: 16분 베이스 · 킥 4/4 · 게이트 스네어 2 · 4
    roots = [45, 45, 41, 43]
    kicks = []
    for k in range(int((DUR - drop) / b)):
        t = drop + k * b
        kicks.append(t)
        place(drums, hard_kick(0.4, 1.0), t)
        if k % 2 == 1:
            sn = reverb(snare(0.25, 1.0), 1.0, 1.0)
            n = int(SR * 0.26)
            sn[n:] *= np.exp(-np.arange(len(sn) - n) / (SR * 0.008))
            place(drums, sn * 0.7, t)
        place(drums, hat(0.03, 0.35), t + b / 2)
        r = roots[(k // 4) % 4]
        for j in range(4):
            place(music, bass(hz(r + (12 if j == 3 else 0)), s16 * 0.9, 0.9), t + j * s16)
    music = pump(music, kicks, 0.45, 0.14)
    return reverb(music, 1.2, 0.20) + drums


TRACKS = {'organ': organ_track, 'musicbox': musicbox_track, 'carpenter': carpenter_track}


def master(x):
    x = hp(x, 28, 2)
    x = sat(x / (np.abs(x).max() + 1e-6) * 1.6, 1.5)
    x = x / (np.abs(x).max() + 1e-6) * 0.93
    n = int(SR * 0.6)
    x[-n:] *= np.linspace(1, 0, n)
    return x.astype(np.float32)


def write(name):
    x = master(TRACKS[name]())
    p = os.path.join(OUT, f'bgm_{name}.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    print(p, f'{len(x) / SR:.1f}s')


if __name__ == '__main__':
    for s in (sys.argv[1:] or list(TRACKS)):
        write(s)
