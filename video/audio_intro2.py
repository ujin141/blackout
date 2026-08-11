"""
행사 인트로 **B안** — 밝은 풀파티 버전. 23.0초 · 120BPM.

A안(`audio_intro.py`)은 어두운 기계실입니다. 터빈이 돌고 접점이 붙고 쇠가 울립니다.
B안은 **물속에서 수면 위로 올라오는 이야기**입니다. 낮의 물빛, 스플래시, 밝은 신스.

**격자는 한 칸도 안 바꿉니다.** 디제이가 두 판을 같은 방식으로 씁니다 —
    17.0초  마지막 한 방 (마디 첫 박)
    16.5초  통째로 비는 한 박
    21.0초  카운트인 네 박 — 낮게 셋, 마지막에 높게
    23.0초  **여기가 노래 첫 박이다**

밝게 만들면서 새로 지켜야 하는 것 셋. 어두운 판에서는 문제가 안 되던 것들입니다.

**1. 밝은 판에서는 말이 더 안 들린다**
   기계음은 2~6kHz 에 몰려 있어서 말(1~4kHz)과 겨우 비켰습니다. 그런데
   스플래시·셰이커·심머는 **말과 정확히 같은 대역에서 더 큽니다.**
   그래서 A안보다 더 세게 비웁니다 — 말이 나오는 동안 밝은 층을 0.94 까지 눌러
   말만 남깁니다. 줄이는 게 아니라 **비우는 것**이 확실합니다.

**2. 밝은 소리는 시끄러워지기 쉽다**
   고역이 많으면 같은 볼륨에서 훨씬 크게 느껴지고, 계속 들으면 피곤합니다.
   물소리는 **간격**으로 씁니다 — 깔지 않고 점으로 떨어뜨립니다.

**3. 밝다고 장조 선율을 넣으면 그 순간 촌스러워진다**
   코드는 sus2·add9 로 잡고 **3음을 움직이지 않습니다.** 아르페지오도 오르내리지
   않고 같은 순서를 돕니다. 밝음은 음정이 아니라 **배음과 잔향**에서 옵니다.

python audio_intro2.py  →  out/intro/bgm_intro2.wav
"""
import os
import wave
import numpy as np
from scipy import signal
from audio import SR, place, lp, hp, bp, reverb
# 말은 A안 것을 그대로 쓴다. 포먼트 합성을 두 벌 두면 두 판의 목소리가 갈린다 —
# 같은 크루의 같은 행사인데 인트로마다 다른 기계가 말하면 브랜드가 아니다.
from audio_intro import LINES, say, pip, hall, total

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

BPM = 120.0
BEAT = 60.0 / BPM                 # 0.5초 = 15프레임
BAR = BEAT * 4                    # 2.0초
T_SURFACE = 4.30                  # 수면을 뚫고 나오는 자리
T_SAY = 9.50                      # 기계가 BLACKOUT 을 부르는 자리
T_LOCK = 11.0                     # 행사 이름이 걸리는 자리
T_BUILD = 13.0                    # 다시 올리기 시작 — 마디 첫 박
T_GO = 17.0                       # 마지막 한 방 — 마디 첫 박
T_GAP = T_GO - BEAT               # 한 박을 통째로 비운다
DUR = T_GO + BAR * 3              # 23.0
N = int(DUR * SR)

# 조성 — A. **3음을 안 건드린다.** sus2 와 add9 만 쓴다
A1, A2, B2, E3, A3, B3, CS4, E4, A4 = 55.0, 110.0, 123.47, 164.81, 220.0, 246.94, 277.18, 329.63, 440.0
PAD = [A2, E3, B3, CS4, E4]
ARP = [A3, B3, E4, CS4, A4, E4]                       # 오르내리지 않는다. 같은 순서를 돈다


def _n(d):
    return int(d * SR)


# ── 물 ────────────────────────────────────────────────────
def drop(f=900.0, dur=0.22, gain=1.0):
    """물방울. **음이 떨어지는 사인 하나**면 된다. 노이즈를 섞으면 물방울이 아니라
    잡음이 되고, 떨어지는 폭이 좁으면 그냥 삑 소리가 된다."""
    n = _n(dur)
    t = np.arange(n) / SR
    ph = 2 * np.pi * (f * 0.42 * t + (f * 1.9) * (1 - np.exp(-t * 26)) / 26)
    x = np.sin(ph) + 0.22 * np.sin(2 * ph)
    return x * np.exp(-t * (13 / dur)) * gain


def splash(dur=0.7, gain=1.0, seed=0, bright=1.0):
    """물 튀김. 노이즈가 **위에서 아래로 쓸려 내려간다** — 튀었다가 떨어지는 모양이다.
    대역을 고정하면 셰이커가 되고, 내려가야 물이 된다."""
    n = _n(dur)
    t = np.arange(n) / SR
    x = np.random.default_rng(seed).standard_normal(n)
    out = np.zeros(n)
    B = 7
    for i in range(B):                                 # 블록마다 다른 대역 — 쓸려 내려간다
        a, b = int(n * i / B), int(n * (i + 1) / B)
        f0 = (9000 * bright) * (0.30 ** (i / (B - 1)))
        out[a:b] = bp(x, max(180, f0 * 0.55), min(15000, f0 * 1.9))[a:b]
    return out * np.exp(-t * (4.6 / dur)) * gain


def underwater(dur, gain=1.0, cut0=300.0, cut1=5200.0, seed=1):
    """수중 → 수면. 노이즈를 통과 대역이 **열리면서** 지나간다.
    물속에서는 고역이 안 들리고, 물 밖으로 나오면 한꺼번에 열린다."""
    n = _n(dur)
    x = np.random.default_rng(seed).standard_normal(n)
    out = np.zeros(n)
    B = 34
    for i in range(B):
        a, b = int(n * i / B), int(n * (i + 1) / B)
        c = cut0 * (cut1 / cut0) ** ((i / (B - 1)) ** 1.6)
        out[a:b] = lp(x, c)[a:b]
    t = np.arange(n) / SR
    out *= 1 + 0.18 * np.sin(2 * np.pi * 0.7 * t)      # 물이 흔들린다
    return out * gain


# ── 신스 ──────────────────────────────────────────────────
def pluck(f, dur=0.34, gain=1.0, cut=6000.0):
    """밝은 뜯는 소리. 톱니를 열어 두고 빠르게 닫는다."""
    n = _n(dur)
    t = np.arange(n) / SR
    x = signal.sawtooth(2 * np.pi * f * t) + 0.5 * signal.sawtooth(2 * np.pi * f * 1.005 * t)
    out = np.zeros(n)
    B = 10
    for i in range(B):
        a, b = int(n * i / B), int(n * (i + 1) / B)
        out[a:b] = lp(x, cut * (0.16 ** (i / (B - 1))) + 400)[a:b]
    return out * np.exp(-t * (6.0 / dur)) * gain * 0.5


def pad(freqs, dur, gain=1.0, hold=0.5, cut=4200.0, seed=3):
    """오래 끄는 코드. **음정이 안 움직인다** — 움직이면 노래가 되고 촌스러워진다.
    두께는 화음 개수가 아니라 **디튠**에서 온다."""
    n = _n(dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for f in freqs:
        for d in (-1, 0, 1):
            ph = rng.uniform(0, 2 * np.pi)
            x += np.sin(2 * np.pi * f * (1 + d * 0.0035) * t + ph) / len(freqs)
    x = lp(x, cut)
    env = np.clip(t / 0.25, 0, 1) * np.clip((dur - t) / max(0.35, dur - hold), 0, 1)
    return np.tanh(x * 1.6) / np.tanh(1.6) * env * gain


def shimmer(dur, gain=1.0, seed=4):
    """수면에 부서지는 빛. 아주 높은 알갱이 — **깔지 않고 점으로 떨어뜨린다.**"""
    n = _n(dur)
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for _ in range(int(dur * 11)):
        at = rng.uniform(0, max(0.01, dur - 0.25))
        f = rng.uniform(3200, 9000)
        d = rng.uniform(0.06, 0.20)
        m = _n(d)
        tt = np.arange(m) / SR
        g = np.sin(2 * np.pi * f * tt) * np.exp(-tt * (18 / d)) * rng.uniform(0.3, 1.0)
        i = _n(at)
        out[i:i + m] += g[:max(0, min(m, n - i))]
    return out * gain


def swell(dur=2.0, gain=1.0, seed=5):
    """밝은 라이저. A안의 라이저는 어둡게 조여 올라가지만 여기선 **열리면서** 올라간다."""
    n = _n(dur)
    t = np.arange(n) / SR
    p = t / dur
    x = np.random.default_rng(seed).standard_normal(n)
    out = np.zeros(n)
    B = 30
    for i in range(B):
        a, b = int(n * i / B), int(n * (i + 1) / B)
        c = 500 * (26.0 ** (i / (B - 1)))
        out[a:b] = hp(lp(x, min(15500, c * 2.4)), c)[a:b]
    tone = np.sin(2 * np.pi * (A3 * (1 + 1.6 * p ** 2.2)) * t) * 0.30
    return (out * 0.9 + tone) * (p ** 1.7) * gain


def sub(f, dur, gain=1.0, decay=0.6):
    n = _n(dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t)
    return np.tanh(x * 1.3) * np.exp(-t * decay / dur * 3) * gain


def kickish(dur=0.42, gain=1.0):
    """박을 잡아 주는 저역 한 방. 물판이라 딱딱한 킥 대신 둥근 것."""
    n = _n(dur)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 26) + 46
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * np.exp(-t * (6.5 / dur)) * gain


def build():
    t_all = np.arange(N) / SR
    br = np.zeros(N)          # 밝은 층 — 말이 나올 때 제일 세게 눌린다
    vo = np.zeros(N)          # 말
    b = np.zeros(N)           # 저역
    f = np.zeros(N)           # 공간
    plb = np.zeros(N)         # 박 — 사이드체인·더킹을 안 먹는다
    plm = np.zeros(N)

    # ── 0.0–4.3  물속. 위로 올라간다 ──────────────────────
    # 완전한 무음에서 시작하면 아직 안 켠 줄 안다. 물속 소리를 아주 작게 깔고
    # **통과 대역이 열리면서** 수면으로 올라간다. 4.3 에 수면을 뚫는다.
    place(br, underwater(T_SURFACE + 0.05, 0.30, 220, 4800, 1), 0.0)
    place(b, sub(A1, T_SURFACE, 0.22, decay=0.1), 0.0)
    # 물방울 간격이 좁아진다. **등속이면 그냥 리듬이고, 좁아지면 끝을 세게 된다.**
    for k in range(8):
        at = T_SURFACE - 2.30 * 0.66 ** k
        place(br, drop(620 + 90 * k, 0.24, 0.26 + 0.075 * k), at)
    place(br, shimmer(2.4, 0.10, 40), 1.6)

    # 4.3  수면 돌파 — 이 판에서 처음으로 밝아지는 자리
    place(br, splash(1.5, 1.00, 7, 1.10), T_SURFACE)
    place(br, splash(0.6, 0.55, 8, 0.70), T_SURFACE + 0.02)
    place(b, kickish(0.8, 0.95), T_SURFACE)
    place(b, sub(A1, 1.6, 0.55), T_SURFACE)
    place(f, shimmer(1.8, 0.26, 9), T_SURFACE)

    # ── 말 ────────────────────────────────────────────────
    # **전부 또렷하게 간다.** A안은 몇 마디만 풀고 나머지는 기계처럼 걸었는데,
    # 밝은 판에서는 링·비트크러시가 스플래시와 섞여 지저분해지기만 한다.
    CLEAR = dict(ring=0.12, crush=72, glide=True)
    SPOKEN = [('BLACKOUT', 1.70, 100, 0.84),
              ('SYSTEM ONLINE',  5.20, 104, 0.98),
              ('SOUND CHECK',    6.62, 104, 0.92),
              ('DOORS ARMED',    8.02, 100, 0.95),
              ('BLACKOUT',      T_SAY,  92, 1.46),
              ('AFTER SUNSET',  12.15,  94, 1.28),
              ('POOL PARTY',    13.35,  98, 0.96),
              ('SOLO PARTY',    14.25,  98, 0.96),
              ('THREE',  T_GO - BEAT * 6, 90, 0.94),
              ('TWO',    T_GO - BEAT * 4, 90, 0.94),
              ('ONE',    T_GO - BEAT * 2, 86, 1.04)]
    for i, (name, at, f0, g) in enumerate(SPOKEN):
        place(vo, say(LINES[name], f0, g, 11 + i, **CLEAR), at)
    # 숫자와 이름은 옥타브 위아래를 겹친다. 굵어져야 작은 스피커에서도 남는다
    for i, (name, at, f0, g) in enumerate(SPOKEN):
        if name in ('THREE', 'TWO', 'ONE'):
            place(vo, say(LINES[name], f0 * 0.5, g * 0.42, 60 + i, **CLEAR), at + 0.010)
    for i, (f0, g, dl) in enumerate(((46, 0.80, 0.010), (184, 0.36, 0.022))):
        place(vo, say(LINES['BLACKOUT'], f0, g, 91 + i, **CLEAR), T_SAY + dl)
    place(vo, say(LINES['BLACKOUT'], 92, 0.42, 11, **CLEAR), T_SAY + 0.115)


    # ── 4.8–10.4  밝은 판이 돈다 ──────────────────────────
    # **음정이 오르내리지 않는다.** 같은 순서를 도는 아르페지오와 안 움직이는 패드.
    place(br, pad(PAD, 6.2, 0.30, 3.0, 3600, 11), 4.60)
    # **말 위에 걸친 것은 옮긴다. 눌러서는 안 된다** — 눌린 소리는 사라지지 않고
    # 탁해지기만 하고, 그 탁함이 말을 먹는다. 말이 나오는 칸은 통째로 건너뛴다.
    SPEAK = [(at - 0.12, at + total(nm) + 0.14) for nm, at, _, _ in SPOKEN if at < 11.0]
    at, k = 4.75, 0
    while at < 10.6:
        if any(g0 <= at <= g1 for g0, g1 in SPEAK):
            at += BEAT * 0.5
            k += 1
            continue
        place(br, pluck(ARP[k % len(ARP)], 0.30, 0.30, 6500), at)
        if k % 2 == 0:
            place(b, kickish(0.44, 0.44), at)
        else:
            place(br, drop(1250, 0.14, 0.16), at + BEAT * 0.25)
        at += BEAT * 0.5
        k += 1

    # 11.0  판이 걸린다 — 행사 이름이 뜨는 자리
    place(br, splash(1.8, 0.86, 12, 1.05), T_LOCK)
    place(br, pad(PAD, 5.0, 0.34, 2.4, 4200, 13), T_LOCK)
    place(b, kickish(0.9, 0.90), T_LOCK)
    place(b, sub(A1, 3.0, 0.60), T_LOCK)
    place(f, shimmer(3.2, 0.24, 14), T_LOCK)

    # ── 13.0–16.5  다시 올린다 ────────────────────────────
    # 런웨이가 짧으면 아무리 큰 한 방도 밋밋하다. 3.5초에 걸쳐 끊기지 않고 올린다.
    place(br, underwater(BAR * 1.75, 0.30, 700, 9000, 15), T_BUILD)
    place(b, sub(A1, BAR * 1.75, 0.26, decay=0.2), T_BUILD)
    RB = T_GAP - BAR * 0.75
    place(br, swell(BAR * 0.75, 0.62, 16), RB)
    place(br, shimmer(BAR * 0.75, 0.24, 17), RB)
    place(b, sub(A1, BAR * 0.75, 0.30, decay=0.1), RB)

    # ── 17.0  마지막 한 방 ────────────────────────────────
    # **코드를 2.4초 버틴 뒤에 내려온다.** 치자마자 줄면 타격이지 벽이 아니다.
    place(br, pad(PAD + [A4], BAR * 2.7, 1.00, 2.4, 7000, 20), T_GO)
    place(br, splash(2.6, 1.05, 21, 1.15), T_GO)
    place(br, splash(1.1, 0.60, 22, 0.65), T_GO + 0.03)
    place(br, shimmer(BAR * 2.2, 0.34, 23), T_GO)
    place(b, kickish(1.2, 1.05), T_GO)
    place(b, sub(A1, 3.6, 0.95, decay=0.35), T_GO)
    place(f, swell(0.9, 0.26, 24), T_GO)
    # 19.0  같은 코드가 한 옥타브 위에서 되받는다 — 마디 둘째 첫 박
    place(br, pad([A3, E4, B3 * 2, CS4 * 2], BAR * 1.7, 0.26, 0.7, 9000, 25), T_GO + BAR)
    place(f, shimmer(BAR * 2, 0.18, 26), T_GO + BAR)
    place(br, drop(1400, 0.5, 0.16), T_GO + BAR * 1.5)
    place(br, drop(900, 0.6, 0.14), T_GO + BAR * 2.25)

    # ── 17.0–23.0  디제이가 맞출 박 ───────────────────────
    # 한 방만 크고 뒤가 무박이면 걸 자리를 못 정한다. 마디 셋 동안 120BPM 을 친다.
    # **세기를 줄이지 않는다.** 오히려 코드가 물러나는 만큼 올린다.
    NB = int(BAR * 3 / BEAT)
    for k in range(1, NB):
        at = T_GO + k * BEAT
        down = (k % 4 == 0)
        g = 0.30 + 0.30 * (k / NB)
        place(plb, kickish(0.34, g * (1.35 if down else 1.0)), at)
        place(plm, drop(1500 if down else 1150, 0.12, g * 0.42), at)
        if down:
            place(plm, splash(0.30, g * 0.36, 130 + k, 1.2), at)

    # ── 19.0–23.0  카운트인 ───────────────────────────────
    # 사람은 반응에 0.2초가 걸린다. "끝났다"를 보고 누르면 이미 늦다.
    # **한 박(0.5초)마다 세면 너무 빨라서 못 따라온다.** 네 번이 2초 안에 다
    # 지나가 버리고, 그 사이에 손이 갈 자리가 없다. **두 박(1.0초)마다** 센다 —
    # 마디 첫 박에 하나씩 떨어지고, 마지막(22.0)에서 다음 하나가 곧 23.0 이다.
    CUE = T_GO + BAR
    for j, f0 in enumerate((880, 880, 880, 1320)):
        place(plm, pip(0.12 if j < 3 else 0.17, f0, 0.62 if j < 3 else 0.82),
              CUE + j * BEAT * 2)

    # ── 말이 나오면 밝은 층을 비운다 ──────────────────────
    # **밝은 판에서는 A안보다 더 세게 눌러야 한다.** 스플래시·심머·플럭은
    # 말(1~4kHz)과 같은 대역에서 더 크다. 기계음은 겨우 비켰지만 이건 정면으로 겹친다.
    env = np.abs(vo)
    k = int(0.05 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    env = np.clip(env / (env.max() + 1e-9), 0, 1) ** 0.5
    soft = 1 - 0.30 * np.clip((t_all - T_BUILD) / 0.5, 0, 1)   # 크레셴도엔 구멍을 덜 낸다
    br *= 1 - 0.94 * env * soft
    b *= 1 - 0.70 * env * soft
    f *= 1 - 0.88 * env * soft

    # 박마다 덜어 낸다 — 더해서는 박이 안 선다
    ph = ((t_all - T_GO) % BEAT) / BEAT
    pump = np.where(t_all >= T_GO - 0.02,
                    1 - 0.44 * np.clip(1 - ph / 0.78, 0, 1) ** 1.5, 1.0)
    br *= pump; b *= pump; f *= pump
    br += plm; b += plb                       # 박 자체는 눌리면 안 된다

    # 작은 스피커는 200Hz 아래를 못 낸다. 포화시킨 저음의 윗부분을 섞어 준다
    br += hp(np.tanh(b * 3.2), 150) * 0.55

    # **진짜 정적.** 꼬리가 남아 있으면 정적이 아니다
    gap = np.ones(N)
    gap[(t_all >= T_GAP) & (t_all < T_GO - 0.005)] = 0.0
    k = max(1, int(0.006 * SR))
    gap = np.convolve(gap, np.ones(k) / k, mode='same')
    br *= gap; b *= gap; f *= gap

    # 한 방 앞을 눌러 상대적 크기를 만든다. 끝을 더 키울 수는 없다 —
    # 이미 리미터에 닿아 있다. **0.88 이 한계다** — 더 내리면 본체가 안 들린다
    duck = np.ones(N)
    duck[t_all < T_BUILD] = 0.88
    ramp = (t_all >= T_BUILD) & (t_all < T_GAP)
    duck[ramp] = 0.88 + 0.12 * np.clip((t_all[ramp] - T_BUILD) / 2.8, 0, 1)
    br *= duck; b *= duck; f *= duck; vo *= duck

    tail = np.zeros(N)
    i0 = int((T_GO - 0.05) * SR)
    tail[i0:] = br[i0:] + b[i0:] * 0.7

    # 말이 또렷해지는 대역은 1~4kHz. **목소리 버스에만** 건다 —
    # 전체에 걸면 스플래시까지 같이 커져 말이 다시 묻힌다
    vo = vo + bp(vo, 1200, 3800) * 0.72
    dry = (br + b * 0.55 + vo * 2.70 + reverb(vo, 0.9, 0.14) * 0.26
           + reverb(br, 2.0, 0.24) * 0.55 + reverb(f, 3.0, 0.40) * 0.6)

    wetL = hall(tail, 0.078, 5.4, 7200, 61) * 0.80
    wetR = hall(tail, 0.096, 5.8, 6800, 62) * 0.80
    chans = []
    for wet in (wetL, wetR):
        w = (dry + wet) * gap
        chans.append(hp(w, 55, 2))
    st = np.stack(chans, axis=1)

    mid = st.mean(1)
    side = (st[:, 0] - st[:, 1]) * 0.5 * (1 + 2.0 * np.clip((t_all - T_GO) / 0.3, 0, 1))
    st = np.stack([mid + side, mid - side], axis=1)
    # **포화는 폭을 벌린 뒤에.** 앞에 걸면 사이드를 키울 때 마루가 다시 솟고,
    # 그 피크 하나 때문에 정규화가 판을 눌러 한 방이 작아진다
    st = np.tanh(st * 1.05) / np.tanh(1.05)
    st /= np.abs(st).max() + 1e-9
    st *= 0.95
    fd = int(0.15 * SR)                       # 마디 첫 박에서 딱 끊는다
    st[-fd:] *= np.linspace(1, 0, fd)[:, None] ** 1.3
    k0 = int(0.01 * SR)
    st[:k0] *= np.linspace(0, 1, k0)[:, None]
    return st


if __name__ == '__main__':
    np.random.seed(9)
    st = build()
    p = os.path.join(OUT, 'bgm_intro2.wav')
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{p}  {DUR:.1f}s')
