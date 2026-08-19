"""**reel4 전용 곡 셋 — 기존 라이브러리와 안 겹치게 새로 만든다.**

    out/reel4/bgm_pluck.wav    124  8마디  32박
    out/reel4/bgm_perc.wav     112  8마디  32박
    out/reel4/bgm_bass.wav     132  8마디  32박

## 왜 새로 만드나

기존 곡(`audio_motion` 5개 · `audio_poster` 6개)은 **뼈대가 다 같다** —
킥 넷에 엇박 하이햇, 그 위에 패드나 스탭. BPM 과 음색만 바꾼 것이라
연달아 들으면 같은 곡으로 들린다. 실제로 "너무 겹친다" 는 말이 나왔다.

여기서는 **주인공 악기를 바꾼다.** 그게 곡을 가르는 유일한 방법이다.

    pluck   짧게 끊어지는 플럭 아르페지오가 주선율. 킥은 뒤로 뺀다
    perc    선율이 아예 없다. 톰·콩가·림 만으로 굴린다 — 제일 안 겹친다
    bass    굵은 신스 베이스 리프가 주인공. 위쪽은 거의 비운다

## 안 쓰는 것

`supersaw` · `pad` · `stab` 은 기존 곡이 전부 쓴다. 여기서는 **한 번도
안 쓴다** — 그 소리가 나는 순간 "그 곡" 으로 들린다.

python audio_reel4.py          셋 다
python audio_reel4.py perc     하나만
"""
import os
import sys
import wave
import numpy as np
from audio import SR, place, lp, hp, bp, reverb, env_ad
from audio_reel import sat, subf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'reel4')
os.makedirs(OUT, exist_ok=True)

# (BPM, 마디). 기존 곡의 BPM(110·118·121·122·124·126·128·130·136·138·142)과
# 겹치는 걸 피한다 — 같은 템포면 같은 곡처럼 들린다
STYLES = {'pluck': (117.0, 8), 'perc': (108.0, 8), 'bass': (133.0, 8)}
ROOT = {'pluck': 55.00, 'perc': 49.00, 'bass': 41.20}   # A1 · G1 · E1


def _n(f, semi):
    return f * 2 ** (semi / 12)


def pluck(freq, dur, gain=1.0, damp=0.55):
    """카플러스-스트롱. **뜯는 소리는 이 라이브러리에 없던 음색이다** —
    노이즈를 짧은 지연선에 넣고 평균을 내면 줄을 뜯은 것처럼 감쇠한다."""
    n = int(SR * dur)
    L = max(2, int(SR / freq))
    buf = np.random.default_rng(int(freq) % 997).standard_normal(L) * 0.5
    out = np.zeros(n, np.float32)
    for i in range(n):
        out[i] = buf[i % L]
        buf[i % L] = (buf[i % L] + buf[(i + 1) % L]) * 0.5 * (1 - damp * 0.02)
    out *= np.exp(-np.linspace(0, 4.2, n))
    return (out * gain).astype(np.float32)


def tom(freq=150, dur=0.34, gain=1.0):
    """피치가 떨어지는 톰. 퍼커션 판의 기둥."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = freq * np.exp(-t * 5.5) + freq * 0.45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (x * env_ad(len(t), 0.002, dur, 2.6) * gain).astype(np.float32)


def conga(freq=320, dur=0.16, gain=1.0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    x = np.sin(2 * np.pi * freq * t) * 0.7 + np.sin(2 * np.pi * freq * 1.6 * t) * 0.3
    x += np.random.default_rng(3).standard_normal(len(t)) * 0.15
    return (bp(x, 200, 2600) * env_ad(len(t), 0.001, dur, 3.4) * gain).astype(np.float32)


def rim(dur=0.06, gain=1.0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    x = np.random.default_rng(11).standard_normal(len(t))
    return (bp(x, 1400, 5200) * env_ad(len(t), 0.0005, dur, 5.0) * gain).astype(np.float32)


def shaker(dur=0.05, gain=1.0, seed=0):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    x = np.random.default_rng(seed).standard_normal(len(t))
    return (hp(x, 6500) * env_ad(len(t), 0.0008, dur, 4.5) * gain).astype(np.float32)


def bassline(freq, dur, gain=1.0, cut=520):
    """굵은 톱니 베이스. **위쪽을 잘라 버려서 선율이 아니라 무게로 들린다.**"""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    x = 2 * ((t * freq) % 1.0) - 1
    x += 2 * ((t * freq * 1.005) % 1.0) - 1
    x = lp(x * 0.5, cut + 900 * np.exp(-3), 4)
    return (sat(x, 1.8) * env_ad(len(t), 0.006, dur, 1.6) * gain).astype(np.float32)


def thump(dur=0.40, gain=1.0):
    """킥. 기존 판보다 **짧고 둔하게** — 앞으로 안 나오게 한다."""
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f = 105 * np.exp(-t * 26) + 44
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (x * env_ad(len(t), 0.001, dur, 3.0) * gain).astype(np.float32)


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    total = bars * 4 * beat
    buf = np.zeros(int(SR * (total + 2.0)), np.float32)
    R = ROOT[style]
    at = lambda bar, b: (bar * 4 + b) * beat

    if style == 'pluck':
        # **플럭 아르페지오가 주선율.** 킥은 뒤에 깔리기만 한다
        seq = [0, 7, 12, 15, 12, 7, 10, 3]
        for bar in range(bars):
            for i, semi in enumerate(seq):
                if bar < 1 and i > 3:
                    continue
                g = 0.34 if bar >= 2 else 0.24
                place(buf, pluck(_n(R * 4, semi), beat * 0.9, g), at(bar, i * 0.5))
            if bar >= 1:
                for b in range(4):
                    place(buf, thump(0.40, 0.85), at(bar, b))
            if bar >= 3:
                for b in range(4):
                    place(buf, shaker(0.05, 0.16, seed=bar * 4 + b), at(bar, b + 0.5))
            if bar >= 2:
                place(buf, subf(R, beat * 3.6, 0.60), at(bar, 0))
        buf = reverb(buf, 1.1, 0.16)

    elif style == 'perc':
        # **선율이 없다.** 톰과 콩가만으로 굴린다 — 제일 안 겹치는 판
        pat = [0, 0.75, 1.5, 2.0, 2.75, 3.25]
        for bar in range(bars):
            for b in range(4):
                place(buf, thump(0.38, 0.92 if bar >= 1 else 0.5), at(bar, b))
            for i, off in enumerate(pat):
                f = (150, 190, 120, 165, 210, 140)[i]
                place(buf, tom(f, 0.32, 0.42 if bar >= 2 else 0.26), at(bar, off))
            if bar >= 1:
                for off in (0.5, 1.25, 2.5, 3.75):
                    place(buf, conga(320 if int(off) % 2 else 400, 0.16, 0.34), at(bar, off))
            if bar >= 3:
                for k in range(8):
                    place(buf, rim(0.06, 0.20), at(bar, k * 0.5 + 0.25))
            if bar >= 4:
                place(buf, subf(R, beat * 3.7, 0.55), at(bar, 0))
        buf = reverb(buf, 0.9, 0.13)

    else:  # bass
        # **베이스 리프가 주인공.** 위쪽은 거의 비운다
        riff = [(0, 0, 1.5), (0, 1.75, 0.5), (3, 2.5, 1.0), (0, 3.5, 0.5)]
        for bar in range(bars):
            semis = [0, 0, 3, 0] if bar % 4 != 3 else [0, 0, 5, 7]
            for (si, off, ln), semi in zip(riff, semis):
                place(buf, bassline(_n(R, semi), beat * ln, 0.62 if bar >= 1 else 0.4),
                      at(bar, off))
            for b in range(4):
                place(buf, thump(0.42, 1.0 if bar >= 1 else 0.55), at(bar, b))
            if bar >= 2:
                for off in (0.5, 1.5, 2.5, 3.5):
                    place(buf, shaker(0.045, 0.20, seed=bar * 8 + int(off * 2)), at(bar, off))
            if bar >= 4:
                place(buf, rim(0.06, 0.30), at(bar, 1))
                place(buf, rim(0.06, 0.30), at(bar, 3))
        buf = reverb(buf, 0.7, 0.10)

    buf = buf[:int(SR * total)]
    # 끝 한 박은 흘려 준다 — 딱 끊기면 루프가 튄다
    n = int(SR * beat)
    buf[-n:] *= np.linspace(1, 0, n)
    m = np.max(np.abs(buf)) or 1.0
    return (buf / m * 0.89).astype(np.float32)


def write(style):
    x = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    bpm, bars = STYLES[style]
    print(f'{p}  {len(x)/SR:.2f}s  {bpm:.0f}BPM  {bars*4}박')


if __name__ == '__main__':
    for s in (sys.argv[1:] or list(STYLES)):
        write(s)
