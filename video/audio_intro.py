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
    음성     성대 대신 펄스, 입 모양 대신 포먼트 필터. 링모듈레이터로 기계로 만든다

**기계음은 음정이 없어서 리듬만 남습니다.** 그래서 배치가 전부입니다 —
언제 붙고 언제 비는지로만 긴장을 만듭니다.

**목소리도 기계로 만듭니다.** 사람 목소리를 녹음해 변조하는 게 아니라
성대(펄스 트레인)와 입 모양(포먼트 세 개)을 따로 합성해 붙입니다.
모음마다 F1·F2·F3 가 정해져 있어서, 그 세 주파수만 맞추면 그 모음으로 들립니다.
자음은 대역이 다른 노이즈입니다 — S 는 높고 F 는 넓고 T 는 짧게 터집니다.

말이 완전히 또렷하진 않습니다. **그래도 화면에 같은 글자가 같이 뜨면 들립니다** —
애매한 소리는 눈이 본 것으로 해석됩니다. 그래서 음성과 글자를 같은 프레임에 놓습니다.

python audio_intro.py  →  out/intro/bgm_intro.wav
"""
import os
import wave
import numpy as np
from scipy import signal
from audio import SR, place, lp, hp, bp, reverb

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

DUR = 18.0
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


def turbine(dur, f0=64, f1=104, gain=1.0, cut0=380, cut1=3400, seed=4):
    """터빈이 돌아가는 굉음. **이 판의 웅장함은 전부 여기서 나온다.**

    디튠한 톱니 일곱 개를 겹치고 로우패스를 위로 연다.
    악기가 아니라 큰 기계가 회전수를 올리는 소리다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    f = f0 * (f1 / f0) ** (t / dur)
    x = np.zeros(n)
    for d in (-0.011, -0.006, -0.002, 0.0, 0.003, 0.007, 0.012):
        x += signal.sawtooth(2 * np.pi * np.cumsum(f * (1 + d)) / SR)
    x = x / 7 + bp(rng.standard_normal(n), 300, 6500) * 0.28
    out = np.zeros(n)
    step = int(SR * 0.03)
    for i in range(0, n, step):
        c = cut0 + (cut1 - cut0) * (i / n) ** 1.5
        out[i:i + step] = lp(x[i:i + step], c)
    return out * np.clip(t / (dur * 0.45), 0, 1) ** 1.3 * gain


def horn(dur=2.6, f0=58.0, gain=1.0, seed=6):
    """뱃고동. **이 판에서 제일 웅장한 소리다.**

    낮은 사인 몇 개를 살짝 어긋나게 겹치고 배음을 쌓은 뒤 포화시킨다.
    악기가 아니라 큰 기계가 내는 경고음이라 인트로 끝에 맞는다.
    천천히 열리고 천천히 닫혀야 크게 들린다 — 어택이 빠르면 그냥 삑 소리다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for d in (-0.006, 0.0, 0.005):                    # 살짝 어긋난 세 겹 = 맥놀이
        for k, a in ((1, 1.0), (2, 0.55), (3, 0.34), (4, 0.20), (6, 0.10), (8, 0.06)):
            x += np.sin(2 * np.pi * f0 * (1 + d) * k * t + k * d * 9) * a
    x /= 6.6
    x *= 1 + 0.02 * np.sin(2 * np.pi * 5.5 * t)       # 아주 옅은 떨림
    x = np.tanh(x * 2.2) / np.tanh(2.2)
    e = np.clip(t / (dur * 0.16), 0, 1) ** 1.4 * np.clip((dur - t) / (dur * 0.45), 0, 1) ** 1.1
    return x * e * gain


def riser(dur=2.0, gain=1.0, seed=7):
    """올라가는 노이즈. 끝의 한 방을 받쳐 준다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    step = int(SR * 0.02)
    for i in range(0, n, step):
        k = (i / n) ** 1.3
        c = 400 + 9000 * k
        out[i:i + step] = bp(x[i:i + step], max(200, c * 0.45), min(SR / 2 - 500, c + 900))
    return out * (t / dur) ** 1.8 * gain


def boom(dur=2.8, gain=1.0):
    """판이 걸릴 때의 한 방. **포화를 걸어 배음을 만든다** —
    순수한 저음만 두면 작은 스피커에서는 아무 소리도 안 난다."""
    n, t = _n(dur)
    f = 132 * np.exp(-t * 2.2) + 44
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x = np.tanh(x * 2.8) / np.tanh(2.8)
    return x * np.exp(-t * 1.45) * gain


def thump(dur=0.5, gain=1.0):
    """기계가 도는 박자. 음정이 아니라 무게만 남긴다."""
    n, t = _n(dur)
    f = 52 + 90 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) * gain


# ── 기계 음성 ─────────────────────────────────────────────
# 모음은 포먼트 세 개로 정해진다. 이 값만 맞추면 그 모음으로 들린다.
VOWEL = {
    'AE': (660, 1720, 2410), 'ER': (490, 1350, 1690), 'AH': (640, 1190, 2390),
    'EH': (550, 1770, 2490), 'IH': (390, 1990, 2550), 'AA': (730, 1090, 2440),
    'AY': (660, 1700, 2400), 'OW': (450, 1030, 2380), 'UW': (300, 870, 2240),
    'AW': (640, 1200, 2400), 'IY': (270, 2290, 3010), 'AO': (570, 840, 2410),
    'N': (250, 1250, 2500), 'M': (250, 1100, 2300), 'L': (360, 1300, 2600),
    'R': (310, 1060, 1380), 'W': (290, 610, 2200),
}
# 자음은 대역이 다른 노이즈. S 는 높고 F 는 넓고 T 는 짧게 터진다.
FRIC = {'S': (4200, 9000, 1.0), 'F': (1200, 4600, 0.62), 'T': (2200, 7000, 0.5),
        'K': (1400, 5200, 0.55), 'CH': (2600, 7800, 0.8),
        # 파열음은 대역이 낮고 더 짧다. 이게 있어야 말이 또박또박 들린다
        'B': (140, 900, 0.55), 'P': (300, 2200, 0.50), 'D': (280, 3000, 0.48),
        'G': (220, 1800, 0.48), 'Z': (2600, 7000, 0.7), 'TH': (900, 5200, 0.42)}


def _buzz(n, f0):
    """성대 대신 펄스 트레인. 폭이 좁아야 배음이 많아 포먼트가 잘 드러난다."""
    ph = np.cumsum(np.full(n, f0 / SR))
    return signal.sawtooth(2 * np.pi * ph, 0.10)


def _formant(x, F, q=11.0):
    out = np.zeros_like(x)
    for i, f in enumerate(F):
        bw = max(70.0, f / q)
        lo_, hi_ = max(60.0, f - bw), min(SR / 2 - 200, f + bw)
        sos = signal.butter(2, [lo_, hi_], 'bp', fs=SR, output='sos')
        out += signal.sosfilt(sos, x) * (1.0, 0.66, 0.36)[i]
    return out


def say(seq, f0=108.0, gain=1.0, seed=11):
    """seq 는 (기호, 길이) 목록. 대문자 모음/자음 기호는 위 표를 쓴다."""
    rng = np.random.default_rng(seed)
    parts = []
    for sym, d in seq:
        n = int(d * SR)
        t = np.arange(n) / SR
        if sym in FRIC:
            lo_, hi_, g = FRIC[sym]
            x = bp(rng.standard_normal(n), lo_, hi_) * g
            e = np.clip(t / 0.006, 0, 1) * np.exp(-t / (d * 0.55))
        elif sym == '_':
            parts.append(np.zeros(n)); continue
        else:
            x = _formant(_buzz(n, f0), VOWEL[sym])
            # 붙었다 떨어지는 자리를 부드럽게. 각지면 딸깍 소리가 낀다
            e = np.clip(t / 0.018, 0, 1) * np.clip((d - t) / 0.030, 0, 1)
            if sym in ('N', 'M', 'L'):
                x *= 0.55
        parts.append(x * e)
    v = np.concatenate(parts) if parts else np.zeros(0)
    n = len(v)
    t = np.arange(n) / SR
    # 링 모듈레이터 — 이게 사람 목소리를 기계로 바꾼다
    v = v * (0.62 + 0.38 * signal.square(2 * np.pi * 47.0 * t))
    v = np.round(v * 12) / 12                                  # 비트 크러시
    v = bp(v, 220, 5200)
    return v / (np.abs(v).max() + 1e-9) * gain


# **화면에 뜨는 글자를 전부 읽는다.** 기계가 자기가 띄운 걸 읽는 게 이 판의 논리다.
# 또렷하게 만들려고 욕심내면 오히려 사람 흉내가 어설퍼진다 —
# 음절 수와 리듬만 맞으면 화면의 글자가 나머지를 채운다.
LINES = {
    'BLACKOUT CREW': [('B', .05), ('L', .06), ('AE', .10), ('K', .05), ('AW', .11), ('T', .05),
                      ('_', .08), ('K', .05), ('R', .06), ('UW', .16)],
    'SYSTEM ONLINE': [('S', .09), ('IH', .07), ('S', .06), ('T', .04), ('EH', .07), ('M', .07),
                      ('_', .09), ('AA', .09), ('N', .06), ('L', .05), ('AY', .11), ('N', .10)],
    'SOUND CHECK':   [('S', .09), ('AW', .12), ('N', .06), ('D', .05),
                      ('_', .08), ('CH', .08), ('EH', .09), ('K', .06)],
    'DOORS ARMED':   [('D', .05), ('AO', .12), ('R', .07), ('Z', .08),
                      ('_', .08), ('AA', .10), ('R', .06), ('M', .08), ('D', .05)],
    'AFTER SUNSET':  [('AE', .11), ('F', .08), ('T', .04), ('ER', .13), ('_', .09),
                      ('S', .11), ('AH', .12), ('N', .07), ('S', .10), ('EH', .10), ('T', .06)],
    'POOL PARTY':    [('P', .05), ('UW', .13), ('L', .08),
                      ('_', .07), ('P', .05), ('AA', .10), ('R', .06), ('T', .04), ('IY', .12)],
    'SOLO PARTY':    [('S', .09), ('OW', .11), ('L', .06), ('OW', .11),
                      ('_', .07), ('P', .05), ('AA', .10), ('R', .06), ('T', .04), ('IY', .12)],
    # 끝의 카운트다운. 디제이가 걸 자리를 정확히 알려 준다
    'THREE':         [('TH', .08), ('R', .07), ('IY', .18)],
    'TWO':           [('T', .05), ('UW', .20)],
    'ONE':           [('W', .07), ('AH', .14), ('N', .10)],
}


def total(name):
    return sum(d for _, d in LINES[name])


def build():
    m = np.zeros(N)                                   # 기계 · 전면
    vo = np.zeros(N)                                  # 음성 — 따로 둬야 밑을 누를 수 있다
    b = np.zeros(N)                                   # 저역 · 바닥
    f = np.zeros(N)                                   # 공간

    # 0.0–1.2  접점이 하나씩 붙는다. 비어 있는 시간이 길수록 다음 소리가 커진다
    for i, at in enumerate((0.10, 0.62, 1.05)):
        place(m, relay(0.85, i), at)

    # 1.2–16   전원 험이 깔린다. 뒤로 갈수록 커진다
    hm = hum(DUR - 1.2, 60.0, 0.12)
    hm *= np.clip(np.linspace(0, 1, len(hm)) * 2.2, 0, 1) ** 0.7
    place(b, hm, 1.2)
    HUM_START = 1.2

    # 1.4–3.6  모터가 돈다
    place(m, servo(2.2, 130, 760, 0.34), 1.4)
    place(m, relay(0.7, 9), 3.55)

    # 3.7–4.4  배기 → 금속 한 방
    place(m, air(0.7, 0.42, 5), 3.70)
    place(m, metal(1.0, 0.50, 6, 210), 4.30)
    place(b, thump(0.6, 0.55), 4.30)

    # 4.8–10.4 기계가 규칙적으로 돈다. 0.6초 간격 = 100BPM 느낌이지만 악기는 없다
    # ── 기계가 화면의 글자를 읽는다 ────────────────────────
    # (문구, 시작, 높이, 세기) — 화면에 그 글자가 뜨는 프레임과 맞춰야 한다.
    SPOKEN = [('BLACKOUT CREW', 1.70, 100, 0.80),
              ('SYSTEM ONLINE', 5.20, 104, 1.00),
              ('SOUND CHECK',   6.62, 104, 0.92),
              ('DOORS ARMED',   8.02, 100, 0.95),
              ('AFTER SUNSET', 12.15,  94, 1.25),
              ('POOL PARTY',   13.35,  98, 0.92),
              ('SOLO PARTY',   14.25,  98, 0.92),
              ('THREE',        15.35,  92, 1.05),
              ('TWO',          15.90,  92, 1.05),
              ('ONE',          16.42,  88, 1.15)]
    for i2, (name, at, f0, g) in enumerate(SPOKEN):
        place(vo, say(LINES[name], f0, g, 11 + i2), at)
    # 말하는 구간 — 여기선 기계를 반만 친다. 아예 끄면 리듬이 끊긴다
    SPEAK = [(at - 0.10, at + total(name) + 0.15) for name, at, _, _ in SPOKEN]

    # **음성이 나올 구간(5.1–6.3)에는 아예 안 친다.** 소리를 줄이는 것보다
    # 비우는 게 확실하다 — 사람은 빈자리에 들어온 소리를 놓치지 않는다.
    at = 4.8
    k = 0
    while at < 10.4:
        q = 0.35 if any(g0 <= at <= g1 for g0, g1 in SPEAK) else 1.0
        place(b, thump(0.5, (0.42 + 0.03 * k) * q), at)
        place(m, relay(0.30 * q, 20 + k), at + 0.30)
        if k % 2 == 1:
            place(m, metal(0.5, 0.16 * q, 30 + k, 320), at + 0.45)
        at += 0.6
        k += 1

    # 4.8–11.0 터빈이 회전수를 올린다. 웅장함은 여기서 나온다
    place(m, turbine(6.4, 58, 96, 0.62, 520, 3400, 4), 4.70)
    place(m, turbine(2.2, 88, 150, 0.55, 1200, 6000, 14), 8.90)

    # 8.6–11.0 콘덴서가 충전된다. 이 구간이 길어야 터질 때 크게 들린다
    place(m, capacitor(2.4, 0.20), 8.60)
    place(m, servo(1.6, 200, 1600, 0.16, 26), 9.40)
    for i, at in enumerate((10.55, 10.72, 10.86)):
        place(m, glitch(0.16, 0.30, 40 + i), at)

    # 11.0  판이 걸린다 — 여기가 이름이 나오는 자리
    place(m, metal(1.3, 0.95, 7, 150), 11.0)
    place(m, metal(1.6, 0.55, 17, 92), 11.0)          # 한 옥타브 아래를 겹쳐 무게를 준다
    place(m, air(0.7, 0.34, 8), 11.0)
    place(b, boom(2.8, 0.95), 11.0)
    place(b, thump(1.2, 0.45), 11.02)
    place(f, turbine(4.6, 96, 62, 0.42, 3600, 700, 24), 11.0)   # 회전수가 떨어지며 남는 굉음
    place(m, horn(2.8, 62, 0.62, 6), 11.0)                      # 이름이 걸릴 때 고동 한 번

    # ── 14.8–16.75  다시 올린다. 끝은 페이드가 아니라 한 방으로 ──
    # 페이드로 끝나면 디제이가 언제 걸어야 할지 모른다. 카운트다운 뒤 한 방이면
    # 그 프레임에 정확히 걸 수 있다.
    place(m, riser(1.95, 0.34, 7), 14.80)
    place(m, turbine(1.95, 70, 190, 0.46, 800, 7000, 34), 14.80)
    place(b, hum(1.95, 60.0, 0.10), 14.80)

    # 16.75  마지막 한 방 — 이 판에서 제일 큰 소리
    place(m, horn(1.25, 46, 1.00, 16), 16.75)
    place(m, metal(1.2, 0.85, 27, 120), 16.75)
    place(b, boom(1.25, 1.00), 16.75)
    place(f, air(0.9, 0.34, 18), 16.75)


    # **말이 나올 땐 기계를 눌러야 한다.** 안 누르면 음성이 기계음에 묻혀
    # 무슨 말인지도 모르고 소리만 지저분해진다 — 실제로 처음엔 안 들렸다.
    # 방송 장비가 하는 일과 같다.
    env = np.abs(vo)
    k = int(0.05 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    env = np.clip(env / (env.max() + 1e-9), 0, 1) ** 0.5
    m *= 1 - 0.92 * env
    b *= 1 - 0.72 * env
    f *= 1 - 0.85 * env          # 잦아드는 터빈도 눌러야 한다 — 안 누르면 말 위에 남는다

    # 11.0–16  험만 남기고 접점이 가끔 튄다
    for i, at in enumerate((12.6, 14.1)):
        place(m, relay(0.24, 60 + i), at)
    place(f, air(2.0, 0.10, 9), 13.6)

    # **저음의 배음을 만들어 준다.** 작은 스피커는 200Hz 아래를 못 내므로
    # 저음만 크면 "소리가 없다"가 된다. 포화시킨 저음의 윗부분을 섞어 주면
    # 스피커가 못 내는 저음을 귀가 배음으로 채워 듣는다.
    m += hp(np.tanh(b * 3.2), 150) * 0.60

    mix = (m + b * 0.55 + vo * 2.30 + reverb(vo, 1.1, 0.16) * 0.30
           + reverb(m, 2.4, 0.26) * 0.62 + reverb(f, 3.2, 0.40) * 0.6)
    mix = hp(mix, 55, 2)                              # 42Hz 아래는 못 듣고 헤드룸만 먹는다
    mix = np.tanh(mix * 1.25) / np.tanh(1.25)
    mix /= np.abs(mix).max() + 1e-9
    mix *= 0.95
    fade = int(0.18 * SR)
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
