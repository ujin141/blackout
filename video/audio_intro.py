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

DUR = 24.0
T_GAP, T_GO = 16.35, 16.75        # 정적이 시작하는 자리 · 마지막 한 방
T_SAY = 9.50                      # 기계가 BLACKOUT 을 부르는 자리
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


def horn(dur=2.6, f0=58.0, gain=1.0, seed=6, att=0.22, hold=0.0):
    """뱃고동. **이 판에서 제일 웅장한 소리다.**

    낮은 사인 몇 개를 살짝 어긋나게 겹치고 배음을 쌓은 뒤 포화시킨다.
    악기가 아니라 큰 기계가 내는 경고음이라 인트로 끝에 맞는다.
    천천히 열리고 천천히 닫혀야 크게 들린다 — 어택이 빠르면 그냥 삑 소리다.

    **`hold` 가 웅장함을 만든다.** 치자마자 줄어들면 그건 타격이지 벽이 아니다.
    큰 소리는 친 크기 그대로 몇 초를 버티다가 내려간다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for d in (-0.006, 0.0, 0.005):                    # 살짝 어긋난 세 겹 = 맥놀이
        for k, a in ((1, 1.0), (2, 0.55), (3, 0.34), (4, 0.20), (6, 0.10), (8, 0.06)):
            x += np.sin(2 * np.pi * f0 * (1 + d) * k * t + k * d * 9) * a
    x /= 6.6
    x *= 1 + 0.02 * np.sin(2 * np.pi * 5.5 * t)       # 아주 옅은 떨림
    x = np.tanh(x * 2.2) / np.tanh(2.2)
    # 어택은 **길이에 비례시키지 않는다.** 비례시키면 긴 고동일수록 정점이 뒤로 밀려
    # 한 방보다 잔향이 더 커진다 — 실제로 최대 지점이 1.5초 뒤로 밀렸다.
    # 고정된 시간에 열고, hold 동안 버티고, 그 뒤로 내려간다.
    rate = 2.3 / max(0.3, dur - hold)
    e = np.clip(t / att, 0, 1) ** 1.3 * np.where(t < hold, 1.0, np.exp(-(t - hold) * rate))
    e *= np.clip((dur - t) / 0.35, 0, 1)              # 끝을 물어야 딸깍 소리가 안 난다
    return x * e * gain


def chord(dur, gain=1.0, hold=1.8, seed=50):
    """**한 음이 아니라 화음이어야 벽이 된다.**

    뿌리·5도·옥타브·12도·17도를 겹친다(38 · 57 · 76 · 114 · 152). 배음렬 그대로라
    서로 어긋나지 않고 하나의 큰 소리로 뭉친다 — 파이프오르간이 크게 들리는 원리다.
    위쪽 음일수록 짧게 둬야 저역이 남고 윗동네가 먼저 걷힌다.

    **겹친 뒤에 반드시 포화시킨다.** 안 하면 다섯 겹의 마루가 한 자리에서 만나
    피크만 치솟고, 판 전체를 정규화할 때 그 피크 하나 때문에 다 같이 눌린다 —
    실제로 한 음을 화음으로 바꾸자 한 방이 0.582 → 0.471 로 **작아졌다.**
    포화시키면 마루가 눌리면서 밀도가 오르고, 덤으로 배음이 생겨 작은 스피커에서도 산다."""
    out = np.zeros(int(dur * SR))
    for i, (f, g, hl, dl) in enumerate((
            (38.0, 1.00, hold, 0.000),
            (57.0, 0.72, hold * 0.90, 0.030),
            (76.0, 0.58, hold * 0.70, 0.055),
            (114.0, 0.40, hold * 0.50, 0.075),
            (152.0, 0.22, hold * 0.40, 0.090))):
        h = horn(dur - dl, f, g, seed + i, 0.20 + i * 0.02, hl)
        j = int(dl * SR)
        out[j:j + len(h)] += h
    out /= 2.4
    return np.tanh(out * 2.4) / np.tanh(2.4) * gain


def bell(dur=4.5, gain=1.0, base=228.0, seed=8):
    """거대한 종. **금속 타격과 달리 오래 남는다.**

    화음만 두면 38Hz 짜리라 큰 스피커에서만 웅장하고 휴대폰에서는 아무 일도
    안 일어난다 — 실제로 재 보니 한 방 에너지의 82%가 200Hz 아래였고,
    유지 구간의 휴대폰 대역이 본체보다 **작았다.**
    228Hz 는 38 의 6배라 화음과 어긋나지 않고, 배음이 200~2kHz 를 그대로 채운다.
    부분음마다 감쇠를 다르게 줘야 종처럼 울린다 — 같이 꺼지면 그냥 삑 소리다."""
    n, t = _n(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for m, a, d in ((1.00, 1.00, 0.50), (2.01, 0.62, 0.70), (2.98, 0.44, 0.92),
                    (4.17, 0.28, 1.30), (5.43, 0.17, 1.75), (7.10, 0.10, 2.30)):
        x += np.sin(2 * np.pi * base * m * t + m) * np.exp(-t * d) * a
    x += hp(rng.standard_normal(n), 3000) * np.exp(-t * 42) * 0.35
    x *= np.clip(t / 0.004, 0, 1) * np.clip((dur - t) / 0.30, 0, 1)
    return x / 2.4 * gain


def voxchord(dur=5.0, gain=1.0, hold=2.0):
    """**기계가 화음으로 소리를 낸다.** 끝을 더 크게 만드는 마지막 수단이다.

    같은 성대·입 모양 합성기를 말이 아니라 **한 모음을 길게 끄는 데** 쓴다.
    뜻은 없고 크기만 남는다 — 합창이 웅장한 건 뜻 때문이 아니라 사람 목소리가
    한 화음에 겹치기 때문이고, 그 자리를 기계가 대신한다.
    음은 마지막 화음과 같은 배음렬(76 · 114 · 152)이라 따로 놀지 않는다."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f0, g, F in ((76.0, 1.00, VOWEL['AA']), (114.0, 0.70, VOWEL['AO']),
                     (152.0, 0.44, VOWEL['AH']), (228.0, 0.22, VOWEL['OW'])):
        # 아주 살짝 흔들어야 한 사람이 아니라 여럿으로 들린다
        v = _formant(_buzz(n, f0) * (1 + 0.03 * np.sin(2 * np.pi * 4.1 * t + f0)), F)
        out += v * g
    rate = 2.0 / max(0.3, dur - hold)
    e = np.clip(t / 0.30, 0, 1) ** 1.2 * np.where(t < hold, 1.0, np.exp(-(t - hold) * rate))
    e *= np.clip((dur - t) / 0.40, 0, 1)
    out = out / 2.3 * e
    return np.tanh(out * 1.8) / np.tanh(1.8) * gain


def hall(x, pre=0.085, tail=6.0, damp=5200, seed=61):
    """**큰 방은 잔향이 길어서가 아니라 늦게 와서 크게 들린다.**

    소리와 잔향 사이에 빈 시간(프리딜레이)이 있어야 벽이 멀리 있다고 느낀다.
    바로 붙여 버리면 아무리 길게 끌어도 좁은 방에서 울리는 소리가 된다.
    초기 반사 몇 개를 드문드문 심어 방의 크기를 정한다."""
    n = int(tail * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n) * np.exp(-t * (3.0 / tail))
    for d, a in ((0.013, 0.55), (0.027, 0.44), (0.041, 0.36),
                 (0.063, 0.30), (0.088, 0.24), (0.119, 0.18)):
        ir[int(d * SR)] += a
    ir = lp(ir, damp)
    ir /= np.abs(ir).sum() ** 0.5 * 3
    wet = signal.fftconvolve(x, ir)[:len(x)]
    p = int(pre * SR)
    return np.concatenate([np.zeros(p), wet[:-p]])


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


def say(seq, f0=108.0, gain=1.0, seed=11, ring=0.38, crush=12, glide=False):
    """seq 는 (기호, 길이) 목록. 대문자 모음/자음 기호는 위 표를 쓴다.

    `ring`·`crush` 는 **기계로 만드는 장치이자 말을 부수는 장치**다. 리듬만 맞으면
    되는 마디는 세게 걸어도 되지만, 반드시 알아들어야 하는 마디는 풀어야 한다.

    `glide` 는 포먼트를 앞 소리에서 이 소리로 미끄러뜨린다.
    **말이 알아들어지는 건 정지한 포먼트가 아니라 그 사이를 옮겨 가는 궤적이다** —
    모음마다 고정된 세 주파수만 쓰면 낱말이 아니라 음 두 개로 들린다.
    같은 성대 신호를 앞 입 모양·이 입 모양 두 벌로 거른 뒤 섞어야
    위상이 안 깨진다(구간마다 따로 필터를 걸면 이음새에서 딸깍거린다)."""
    rng = np.random.default_rng(seed)
    parts = []
    prev = None
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
            F = VOWEL[sym]
            buz = _buzz(n, f0)
            if glide and prev is not None and prev != F:
                w = np.clip(t / (d * 0.45), 0, 1) ** 0.8
                x = _formant(buz, prev) * (1 - w) + _formant(buz, F) * w
            else:
                x = _formant(buz, F)
            prev = F
            # 붙었다 떨어지는 자리를 부드럽게. 각지면 딸깍 소리가 낀다
            e = np.clip(t / 0.018, 0, 1) * np.clip((d - t) / 0.030, 0, 1)
            if sym in ('N', 'M', 'L'):
                x *= 0.55
        parts.append(x * e)
    v = np.concatenate(parts) if parts else np.zeros(0)
    n = len(v)
    t = np.arange(n) / SR
    # 링 모듈레이터 — 이게 사람 목소리를 기계로 바꾼다
    if ring > 0:
        v = v * (1 - ring + ring * signal.square(2 * np.pi * 47.0 * t))
    v = np.round(v * crush) / crush                            # 비트 크러시
    v = bp(v, 220, 5200)
    return v / (np.abs(v).max() + 1e-9) * gain


# **화면에 뜨는 글자를 전부 읽는다.** 기계가 자기가 띄운 걸 읽는 게 이 판의 논리다.
# 또렷하게 만들려고 욕심내면 오히려 사람 흉내가 어설퍼진다 —
# 음절 수와 리듬만 맞으면 화면의 글자가 나머지를 채운다.
LINES = {
    'BLACKOUT CREW': [('B', .05), ('L', .06), ('AE', .10), ('K', .05), ('AW', .11), ('T', .05),
                      ('_', .08), ('K', .05), ('R', .06), ('UW', .16)],
    # 가운데에서 한 번, **누구나 알아들어야 하는 한 마디.** 다른 줄보다 두 배 느리다 —
    # 포먼트 합성은 빠르면 뭉개진다. 모음을 길게 끌어야 입 모양이 드러난다.
    # **파열음 앞에는 반드시 무음을 둔다.** B·K·T 는 입을 막았다 터뜨리는 소리라,
    # 막는 시간이 없으면 터지는 게 안 들리고 낱말 경계가 사라진다.
    'BLACKOUT':      [('_', .05), ('B', .05), ('L', .09), ('AE', .21),
                      ('_', .05), ('K', .05), ('AW', .25),
                      ('_', .05), ('T', .07)],
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
    # **카운트다운은 천천히 세야 카운트다운이다.** 0.33초짜리 낱말을 0.55초 간격으로
    # 늘어놓으니 세는 게 아니라 지나가는 소리가 됐다. 낱말도 간격도 늘렸다.
    'THREE':         [('TH', .11), ('R', .10), ('IY', .31)],
    'TWO':           [('_', .05), ('T', .06), ('UW', .34)],
    'ONE':           [('W', .10), ('AH', .25), ('N', .15)],
}


def total(name):
    return sum(d for _, d in LINES[name])


def build():
    t_all = np.arange(N) / SR
    m = np.zeros(N)                                   # 기계 · 전면
    vo = np.zeros(N)                                  # 음성 — 따로 둬야 밑을 누를 수 있다
    b = np.zeros(N)                                   # 저역 · 바닥
    f = np.zeros(N)                                   # 공간

    # 0.0–4.3  **기대감은 소리 크기가 아니라 간격이 좁아지는 데서 나온다.**
    # 방이 살아 있다는 신호를 아주 작게 깔고 시작한다. 완전한 무음에서 출발하면
    # 사람은 아직 안 시작한 줄 알고, 소리가 깔려 있으면 곧 뭔가 온다고 읽는다.
    # 26Hz 로 깔았더니 55Hz 하이패스에 그대로 잘려 나가 아무것도 안 들렸다.
    # 48Hz 로 올려도 마찬가지였다 — **깔아 두는 소리의 기음은 반드시 잘리는 대역 위에.**
    place(m, turbine(4.4, 74, 120, 0.40, 400, 1600, 71), 0.00)

    # 아주 가는 고음 하나. 크기는 작지만 **어떤 스피커에서도 들린다** —
    # 저역 룸톤은 노트북·휴대폰에서 통째로 사라지지만 3kHz 는 안 사라진다.
    # 사람은 이 소리를 "켜져 있고 대기 중"으로 읽는다. 4.3 금속 타격에서 끊긴다.
    n0 = int(4.34 * SR)
    tt = np.arange(n0) / SR
    whine = np.sin(2 * np.pi * 3140 * tt) + 0.35 * np.sin(2 * np.pi * 6280 * tt + 1)
    whine *= 0.060 * np.clip(tt / 0.55, 0, 1) * np.clip((4.34 - tt) / 0.04, 0, 1)
    whine *= 1 + 0.06 * np.sin(2 * np.pi * 5.3 * tt)   # 살짝 떨려야 죽은 소리가 안 된다
    place(m, whine, 0.00)

    # 접점이 하나씩 붙는다. **뒤로 갈수록 커져야** 다음 것을 기다리게 된다
    for i, (at, g) in enumerate(((0.10, 0.55), (0.62, 0.78), (1.05, 1.00))):
        place(m, relay(g, i), at)

    # 1.2–16   전원 험이 깔린다. 뒤로 갈수록 커진다
    hm = hum(DUR - 1.2, 60.0, 0.12)
    hm *= np.clip(np.linspace(0, 1, len(hm)) * 2.2, 0, 1) ** 0.7
    # 정적 구간은 통째로 비운다. 험까지 끊어야 진짜 정적이 된다
    tt0 = np.arange(len(hm)) / SR + 1.2
    hm *= 1 - np.clip(1 - np.abs(tt0 - (T_GAP + T_GO) / 2) / 0.22, 0, 1)
    place(b, hm, 1.2)
    HUM_START = 1.2

    # 1.4–3.6  모터가 돈다
    place(m, servo(2.2, 130, 760, 0.62), 1.4)
    place(m, relay(0.95, 9), 3.55)

    # 2.4–4.3  **간격이 좁아지는 박.** 등속으로 치면 그냥 리듬이지만
    # 점점 빨라지면 사람은 끝이 언제인지 세기 시작한다 — 그게 집중력이다.
    # 4.3 초에 정확히 수렴하도록 뒤에서부터 0.62 배씩 당겨 잡는다.
    for k in range(7):
        at = 4.30 - 1.90 * 0.62 ** k
        g = 0.30 + 0.10 * k
        place(m, relay(g, 80 + k), at)
        place(b, thump(0.42, 0.22 + 0.05 * k), at)
    # 같이 올라가는 가는 소리 하나. 어디로 가는지 알려 준다
    place(m, capacitor(1.9, 0.20), 2.40)

    # 3.7–4.4  배기 → 금속 한 방
    place(m, air(0.7, 0.60, 5), 3.70)
    place(m, metal(1.2, 0.95, 6, 210), 4.30)
    place(m, metal(1.5, 0.42, 16, 96), 4.30)
    place(b, boom(1.6, 0.62), 4.30)
    place(b, thump(0.6, 0.60), 4.30)

    # 4.8–10.4 기계가 규칙적으로 돈다. 0.6초 간격 = 100BPM 느낌이지만 악기는 없다
    # ── 기계가 화면의 글자를 읽는다 ────────────────────────
    # (문구, 시작, 높이, 세기) — 화면에 그 글자가 뜨는 프레임과 맞춰야 한다.
    SPOKEN = [('BLACKOUT', T_SAY, 92, 1.42),
              ('BLACKOUT CREW', 1.70, 100, 0.80),
              ('SYSTEM ONLINE', 5.20, 104, 1.00),
              ('SOUND CHECK',   6.62, 104, 0.92),
              ('DOORS ARMED',   8.02, 100, 0.95),
              ('AFTER SUNSET', 12.15,  94, 1.25),
              ('POOL PARTY',   13.35,  98, 0.92),
              ('SOLO PARTY',   14.25,  98, 0.92),
              # **카운트다운은 정적 앞에서 끝나야 한다.** ONE 을 16.42 에 뒀더니
              # 정적 구간(16.35~) 안에 통째로 들어가 한 마디가 사라졌다.
              # **말은 기계보다 크되 한 방보다는 작아야 한다.** 1.40 으로 올렸더니
              # 전체 최대 지점이 14.75 초(카운트다운)로 옮겨가 끝이 죽었다.
              # 또렷함은 절대 크기가 아니라 **바로 옆 기계음과의 차이**에서 나온다.
              ('THREE',        13.90,  90, 0.92),
              ('TWO',          14.85,  90, 0.92),
              ('ONE',          15.80,  86, 1.02)]
    # BLACKOUT 만 기계 장치를 풀고 궤적을 넣는다. 나머지는 리듬만 맞으면 되고,
    # 오히려 세게 걸어야 기계로 들린다.
    CLEAR = dict(ring=0.14, crush=64, glide=True)
    SAYCLEAR = ('BLACKOUT', 'THREE', 'TWO', 'ONE')      # 반드시 알아들어야 하는 마디
    for i2, (name, at, f0, g) in enumerate(SPOKEN):
        kw = CLEAR if name in SAYCLEAR else {}
        place(vo, say(LINES[name], f0, g, 11 + i2, **kw), at)
    # 숫자는 옥타브 아래를 한 겹 깔아 무게를 준다. 얇으면 세는 소리로 안 들린다
    for i2, (name, at, f0, g) in enumerate(SPOKEN):
        if name in ('THREE', 'TWO', 'ONE'):
            place(vo, say(LINES[name], f0 * 0.5, g * 0.40, 60 + i2, **CLEAR), at + 0.010)
    # **이 한 마디만은 겹쳐서 말한다.** 옥타브 위아래를 같이 얹으면 소리가 굵어져
    # 큰 스피커에서도 작은 스피커에서도 남는다 — 예고편 목소리가 하는 일과 같다.
    for i2, (f0, g, dl) in enumerate(((46, 0.78, 0.010), (184, 0.34, 0.022))):
        place(vo, say(LINES['BLACKOUT'], f0, g, 91 + i2, **CLEAR), T_SAY + dl)
    # 0.11 초 뒤에 한 번 되돌아온다. **행사장 방송이 늘 이렇게 들린다** —
    # 짧은 반사가 붙으면 말이 '안내 방송'으로 읽히고 오히려 또렷해진다.
    place(vo, say(LINES['BLACKOUT'], 92, 0.40, 11, **CLEAR), T_SAY + 0.115)

    # 말하는 구간 — 여기선 기계를 반만 친다. 아예 끄면 리듬이 끊긴다
    SPEAK = [(at - 0.10, at + total(name) + 0.15) for name, at, _, _ in SPOKEN]
    # **BLACKOUT 앞뒤는 아예 비운다.** 반만 눌러서는 이 한 마디가 안 또렷해진다.
    # 8.95 부터 비운다 — 9.0 박의 금속이 말 바로 앞에 떨어져 대비가 안 났다.
    # **말 앞의 한 박을 비우는 게 말 자체를 키우는 것보다 효과가 크다.**
    QUIET = (8.95, 10.42)

    # **음성이 나올 구간(5.1–6.3)에는 아예 안 친다.** 소리를 줄이는 것보다
    # 비우는 게 확실하다 — 사람은 빈자리에 들어온 소리를 놓치지 않는다.
    at = 4.8
    k = 0
    while at < 10.4:
        if QUIET[0] <= at <= QUIET[1]:
            at += 0.6
            k += 1
            continue
        q = 0.35 if any(g0 <= at <= g1 for g0, g1 in SPEAK) else 1.0
        place(b, thump(0.5, (0.42 + 0.03 * k) * q), at)
        place(m, relay(0.62 * q, 20 + k), at + 0.30)
        if k % 2 == 1:
            place(m, metal(0.5, 0.36 * q, 30 + k, 320), at + 0.45)
        at += 0.6
        k += 1

    # 4.8–11.0 터빈이 회전수를 올린다. 웅장함은 여기서 나온다
    place(m, turbine(6.4, 58, 96, 0.46, 520, 3400, 4), 4.70)
    # **한 마디를 또렷하게 하려면 그 위에 걸친 것을 옮겨야 한다.** 눌러서는 안 된다 —
    # 눌린 소리는 사라지지 않고 탁해지기만 하고, 그 탁함이 말을 먹는다.
    # 터빈·콘덴서·서보를 전부 9.4 앞에서 끝내고 10.4 뒤에서 다시 올린다.
    place(m, turbine(0.55, 88, 132, 0.34, 1200, 4200, 14), 8.90)
    place(m, turbine(0.7, 120, 200, 0.40, 2000, 7000, 15), 10.36)

    # 8.6–11.0 콘덴서가 충전된다. 이 구간이 길어야 터질 때 크게 들린다
    place(m, capacitor(0.75, 0.26), 8.60)
    place(m, servo(0.9, 200, 1400, 0.26, 26), 8.45)
    place(m, capacitor(0.60, 0.32), 10.38)
    for i, at in enumerate((10.55, 10.72, 10.86)):
        place(m, glitch(0.16, 0.64, 40 + i), at)

    # 11.0  판이 걸린다 — 여기가 이름이 나오는 자리
    place(m, metal(1.3, 0.95, 7, 150), 11.0)
    place(m, metal(1.6, 0.55, 17, 92), 11.0)          # 한 옥타브 아래를 겹쳐 무게를 준다
    place(m, air(0.7, 0.48, 8), 11.0)
    place(b, boom(2.8, 0.95), 11.0)
    place(b, thump(1.2, 0.45), 11.02)
    place(f, turbine(4.6, 96, 62, 0.32, 3600, 700, 24), 11.0)   # 회전수가 떨어지며 남는 굉음
    place(m, horn(2.8, 62, 0.62, 6), 11.0)                      # 이름이 걸릴 때 고동 한 번

    # ── 13.2–16.35  다시 올린다. 끝은 페이드가 아니라 한 방으로 ──
    # **런웨이가 짧으면 아무리 큰 한 방도 밋밋하다.** 1.55초만 올렸더니
    # 크레셴도가 카운트다운 세 마디에서만 솟고 사이가 꺼지는 톱니가 됐다.
    # 3.15초에 걸쳐 끊기지 않고 오르는 바닥을 먼저 깔고, 마지막 1.55초에 얹는다.
    # 페이드로 끝나면 디제이가 언제 걸어야 할지 모른다. 카운트다운 뒤 한 방이면
    # 그 프레임에 정확히 걸 수 있다.
    # 라이저는 16.35 에서 끝난다 — **한 방 앞의 0.4초 정적이 크기를 만든다.**
    # 소리를 키우는 것보다 직전을 비우는 게 훨씬 크게 들린다.
    place(m, turbine(3.15, 40, 132, 0.40, 300, 4200, 36), 13.20)   # 끊기지 않는 바닥
    place(b, hum(3.15, 60.0, 0.16), 13.20)
    place(m, riser(1.55, 0.54, 7), 14.80)
    place(m, turbine(1.55, 70, 210, 0.58, 800, 7500, 34), 14.80)
    place(m, turbine(1.55, 34, 78, 0.34, 260, 1100, 35), 14.80)   # 밑을 같이 올린다
    place(b, hum(1.55, 60.0, 0.10), 14.80)

    # ── 16.75  마지막 한 방 ────────────────────────────────
    # **화음을 1.8초 버틴 뒤에 내려온다.** 치자마자 줄어들면 타격이지 벽이 아니다.
    place(m, chord(6.4, 1.15, 2.4, 50), T_GO)
    place(m, voxchord(5.6, 0.52, 2.2), T_GO + 0.05)
    place(m, metal(2.4, 0.90, 27, 118), T_GO)
    place(m, metal(2.0, 0.55, 37, 76), T_GO + 0.03)
    place(m, bell(5.2, 0.62, 228, 8), T_GO)        # 화음 위에 중역을 오래 끌어 준다
    place(m, bell(4.0, 0.28, 342, 18), T_GO + 0.04)
    place(b, boom(3.6, 1.05), T_GO)
    place(b, thump(1.6, 0.55), T_GO)
    place(f, air(1.6, 0.55, 18), T_GO)
    place(f, riser(0.9, 0.28, 19), T_GO)           # 위로 흩어지는 잔해
    # **중역에 남는 굉음.** 화음만 두면 38Hz 짜리라 휴대폰에서는 아무 일도 안 일어난다.
    # 회전수가 떨어지는 터빈을 3초 깔아 두면 그 자리에서 크기가 유지된다.
    place(f, turbine(4.2, 150, 82, 0.34, 5200, 1300, 44), T_GO)

    # 19.9  같은 화음이 한 옥타브 위에서 되받는다. 벽이 물러나는 소리
    place(m, chord(4.0, 0.30, 0.7, 70), 19.90)
    place(f, air(2.0, 0.14, 28), 19.90)

    # ── 19.2–23  기계가 잦아든다 ───────────────────────────
    # **끝이 허전한 건 조용해서가 아니라 아무 일도 안 일어나서다.**
    # 화음만 줄어들다 끝나면 판이 그냥 꺼진 것처럼 들린다.
    # 전원이 들어오던 이야기를 거꾸로 돌려 닫는다 — 모터가 서고, 압이 빠지고,
    # 접점이 하나씩 떨어지고, 험만 남는다. 시작한 자리로 돌아오는 셈이다.
    place(m, servo(1.6, 640, 150, 0.26, 20), 19.20)
    place(m, air(1.2, 0.26, 48), 20.35)
    place(m, bell(3.0, 0.20, 171, 28), 20.90)
    place(b, hum(4.0, 60.0, 0.13), 19.50)
    for i, (at, g) in enumerate(((20.95, 0.34), (21.75, 0.26), (22.55, 0.18))):
        place(m, relay(g, 100 + i), at)
    place(m, servo(0.9, 240, 96, 0.14, 18), 22.60)


    # **말이 나올 땐 기계를 눌러야 한다.** 안 누르면 음성이 기계음에 묻혀
    # 무슨 말인지도 모르고 소리만 지저분해진다 — 실제로 처음엔 안 들렸다.
    # 방송 장비가 하는 일과 같다.
    env = np.abs(vo)
    k = int(0.05 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    env = np.clip(env / (env.max() + 1e-9), 0, 1) ** 0.5
    # **마지막 크레셴도에서는 덜 누른다.** 카운트다운 세 마디마다 기계를 92% 씩
    # 눌러 버리면 올라가야 할 구간에 구멍이 세 개 뚫린다 — 실제로 16.0 초에서
    # 소리가 오히려 줄고 있었다. 크레셴도에 구멍이 나면 끝이 아무리 커도 밋밋하다.
    # 카운트다운은 짧고 높아서 절반만 눌러도 들린다.
    # 카운트다운 간격을 0.55 → 0.95 초로 벌리면서 사이에 기계가 드러날 자리가
    # 생겼다. 그래서 덜 눌러야 할 이유가 없어졌다 — 0.58 → 0.32 로 되돌린다.
    soft = 1 - 0.32 * np.clip((t_all - 13.2) / 0.5, 0, 1)
    m *= 1 - 0.92 * env * soft
    b *= 1 - 0.72 * env * soft
    f *= 1 - 0.85 * env * soft    # 잦아드는 터빈도 눌러야 한다 — 안 누르면 말 위에 남는다

    # 11.0–16  험만 남기고 접점이 가끔 튄다
    for i, at in enumerate((12.6, 14.1)):
        place(m, relay(0.38, 60 + i), at)
    place(f, air(1.2, 0.10, 9), 12.9)

    # **저음의 배음을 만들어 준다.** 작은 스피커는 200Hz 아래를 못 내므로
    # 저음만 크면 "소리가 없다"가 된다. 포화시킨 저음의 윗부분을 섞어 주면
    # 스피커가 못 내는 저음을 귀가 배음으로 채워 듣는다.
    m += hp(np.tanh(b * 3.2), 150) * 0.60

    # **진짜 정적을 만든다.** 라이저·터빈 꼬리가 남아 있으면 정적이 아니다.
    # 한 방 앞 0.4초를 통째로 0 으로 눌러야 다음 한 방이 벽처럼 선다.
    gap = np.ones(N)
    gap[(t_all >= T_GAP) & (t_all < T_GO - 0.005)] = 0.0
    k = max(1, int(0.006 * SR))
    gap = np.convolve(gap, np.ones(k) / k, mode='same')
    m *= gap
    b *= gap
    f *= gap

    # **한 방 앞을 통째로 눌러 상대적 크기를 만든다.** 마지막을 더 키울 수는 없다 —
    # 이미 리미터에 닿아 있어서 올리면 뭉갠다. 앞을 내리면 끝이 커진다.
    duck = np.ones(N)
    # 처음엔 0.62 까지 눌렀는데 **본체가 한 방보다 11dB 아래로 내려가
    # 기계음이 아예 안 들렸다.** 행사장에서는 끝에 맞춰 볼륨을 잡으니
    # 앞이 통째로 사라진다. 대비는 정적과 유지가 만드는 것이지
    # 본체를 죽여서 만드는 게 아니다. 0.88 이 한계다.
    duck[t_all < 13.2] = 0.88
    ramp = (t_all >= 13.2) & (t_all < T_GAP)
    duck[ramp] = 0.88 + 0.12 * np.clip((t_all[ramp] - 13.2) / 2.8, 0, 1)
    m *= duck; b *= duck; f *= duck; vo *= duck

    # 마지막 한 방만 큰 홀로 보낸다. 전체에 걸면 판이 흐려진다
    tail_bus = np.zeros(N)
    i0 = int((T_GO - 0.05) * SR)
    tail_bus[i0:] = m[i0:] + b[i0:] * 0.7

    # **말이 또렷해지는 대역은 1~4kHz 다.** 전체 존재감 대역(1.9kHz~)을 올리면
    # 기계음까지 같이 커져 말이 다시 묻힌다. 목소리 버스에만 따로 건다.
    vo = vo + bp(vo, 1200, 3800) * 0.60
    dry = (m + b * 0.55 + vo * 2.55 + reverb(vo, 1.1, 0.16) * 0.30
           + reverb(m, 2.4, 0.26) * 0.62 + reverb(f, 3.2, 0.40) * 0.6)

    # **기계는 가운데 붙어 있고 홀만 넓다.** 이게 "작은 기계가 거대한 공간에 있다"로
    # 읽힌다. 전체를 넓히면 기계까지 흐물해져서 가짜처럼 들리고, 전부 모노로 두면
    # 방이 안 커진다. 좌우에 **서로 다른 방**을 걸어야 폭이 생긴다 —
    # 같은 잔향을 지연만 시켜 넣으면 폭이 아니라 위상 문제만 생긴다.
    wetL = hall(tail_bus, 0.082, 6.5, 5200, 61) * 0.85
    wetR = hall(tail_bus, 0.101, 6.9, 4900, 62) * 0.85

    chans = []
    for wet in (wetL, wetR):
        w = (dry + wet) * gap        # 잔향까지 끊어야 진짜 정적이다. 버스만 눌러 두면
                                     # 앞서 친 소리의 잔향이 빈자리를 채워 버린다
        # **존재감 대역을 올린다.** 기계음의 성격은 딸깍·쇳소리처럼 2~6kHz 에 있고,
        # 작은 스피커가 가장 잘 내는 대역도 여기다. 안 올리면 웅웅거리기만 한다.
        w = w + hp(w, 1900, 2) * 0.45
        chans.append(hp(w, 55, 2))                # 55Hz 아래는 못 듣고 헤드룸만 먹는다

    st = np.stack(chans, axis=1)

    # 좌우에 다른 홀을 걸어도 마른 소리가 대부분이라 폭이 거의 안 생긴다(상관 0.95).
    # **한 방 뒤에만 사이드를 키운다** — 가운데 붙은 기계는 그대로 두고
    # 좌우로 갈린 홀만 벌어진다. 벽이 양옆으로 물러나는 소리가 된다.
    mid = st.mean(1)
    side = (st[:, 0] - st[:, 1]) * 0.5 * (1 + 2.2 * np.clip((t_all - T_GO) / 0.3, 0, 1))
    st = np.stack([mid + side, mid - side], axis=1)

    # **포화는 폭을 벌린 뒤에 건다.** 앞에 걸면 사이드를 키울 때 마루가 다시 솟고,
    # 그 피크 하나 때문에 정규화가 판을 통째로 눌러 한 방이 0.577 → 0.496 으로 작아진다.
    st = np.tanh(st * 1.05) / np.tanh(1.05)
    st /= np.abs(st).max() + 1e-9                 # 좌우를 같은 값으로 나눠야 상이 안 틀어진다
    st *= 0.95
    fade = int(0.45 * SR)
    st[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.3
    k0 = int(0.01 * SR)
    st[:k0] *= np.linspace(0, 1, k0)[:, None]
    return st


if __name__ == '__main__':
    np.random.seed(7)
    st = build()
    p = os.path.join(OUT, 'bgm_intro.wav')
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{p}  {DUR:.1f}s')
