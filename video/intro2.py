"""
행사 인트로 **B안** 영상 — 밝은 풀파티 버전. 23.0초 · 30fps · 120BPM.

A안(`intro.py`)은 어두운 기계실입니다. B안은 **물속에서 수면 위로 올라오는 이야기**입니다.

    0.0–4.3   물속. 위에서 빛이 내려오고 기포가 올라간다. 간격이 좁아진다
    4.3       수면 돌파 — 이 판이 처음 밝아지는 자리. 흰 섬광 + 물보라
    4.8–11.0  수면 위. 물빛이 판 전체에서 흐르고 박마다 파문이 퍼진다
    9.5       BLACKOUT — 기계가 부르고 화면이 같이 뜬다
    11.0      행사 이름이 걸린다
    16.5–17.0 **정적.** 소리가 비는 한 박, 화면도 같이 빠진다
    17.0      마지막 한 방 — 판이 하얗게 터지고 이름만 남는다
    21.0–23.0 카운트인 네 칸이 화면 아래에 하나씩 켜진다
    23.0      끝. **여기가 노래 첫 박이다**

**소리를 보고 그립니다.** BPM 으로 박만 계산하면 화면은 규칙적으로 뛰지만 곡이
하는 일과 상관없이 움직입니다. wav 의 저역·고역·어택을 프레임 단위로 뽑아 씁니다.

밝은 판에서 새로 지켜야 하는 것 둘.

**1. 밝으면 글자가 먼저 죽는다**
   어두운 판에서는 흰 글자가 그냥 삽니다. 밝은 판에서는 물빛·섬광과 같은 밝기가 되어
   사라집니다. 그래서 **글자 자리는 배경을 눌러서 만듭니다** — 글자에 외곽선이나
   그림자를 두르면 지저분해지고, 배경을 죽이면 깨끗합니다. 포스터에서 지켜 온 규칙과 같습니다.

**2. 밝은 판에서 흰 섬광은 안 보인다**
   A안은 한 방에서 흰색으로 터집니다. 이미 밝은 판에서 흰색으로 터뜨리면 아무 일도
   안 일어난 것처럼 보입니다. 여기서는 **한 박을 먼저 빼서 어둡게 만들고** 터뜨립니다 —
   정적이 소리를 크게 하듯, 어둠이 섬광을 크게 합니다.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이고 사용자가 직접 요청했습니다.

먼저 `python audio_intro2.py` 로 wav 를 만든 뒤에 돌립니다.

python intro2.py          둘 다
python intro2.py stage    행사장용(가로)만
"""
import os
import wave
import subprocess
import numpy as np
import cv2
from scipy import signal
from poster_kit import BRAND, tmask, fit, paint
from fonts import KR
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

FPS = 30
BEAT, BAR = 0.5, 2.0
CUTS = {'stage': (1920, 1080), 'story': (1080, 1920)}
W, H = 1920, 1080
M, S = int(1920 * 0.062), 1.0

# audio_intro2.py 와 같은 값이어야 그림이 소리에 붙는다
T_SURFACE, T_SAY, T_LOCK = 4.30, 9.50, 11.0
T_BUILD, T_GO = 13.0, 17.0
T_GAP = T_GO - BEAT
T_SETTLE = 19.0
DUR = T_GO + BAR * 3
NBEAT = int(BAR * 3 / BEAT)

# 물속은 짙은 청록, 물 위는 노을. 색은 넷까지만 — 다섯째가 들어오면 전단지가 된다
UNDER_T = np.float32([0.06, 0.40, 0.55])     # 물속 위 (빛이 들어오는 쪽)
UNDER_B = np.float32([0.02, 0.13, 0.24])     # 물속 아래
SKY_T   = np.float32([0.98, 0.55, 0.36])     # 노을 위
SKY_B   = np.float32([0.36, 0.78, 0.92])     # 수평선 언저리
SEA_T   = np.float32([0.16, 0.62, 0.78])
SEA_B   = np.float32([0.03, 0.20, 0.34])
PAPER   = np.float32([0.99, 1.00, 1.00])
AQUA    = np.float32([0.34, 0.94, 1.00])
CORAL   = np.float32([1.00, 0.44, 0.40])

# 화면에 뜨는 글자와 그 시각 — audio_intro2.py 의 SPOKEN 과 같은 자리여야 한다
LINES = [('BLACKOUT CREW', 1.70, 1.05), ('SYSTEM ONLINE', 5.20, 0.98),
         ('SOUND CHECK', 6.62, 0.92), ('DOORS ARMED', 8.02, 0.95)]


def setcut(w, h):
    """판을 갈아 끼운다. 글자 배율은 **짧은 변** 기준 —
    긴 변으로 잡으면 가로판에서 글자가 두 배로 커진다."""
    global W, H, M, S
    W, H = w, h
    M = int(W * (0.062 if W > H else 0.088))
    S = min(W, H) / 1080.0


def analyze(path, nf):
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768.0
        x = x.reshape(-1, 2).mean(1)
    lo = signal.sosfilt(signal.butter(4, 160, 'lp', fs=sr, output='sos'), x)
    hi = signal.sosfilt(signal.butter(4, 3500, 'hp', fs=sr, output='sos'), x)
    hop = len(x) / nf

    def env(v):
        e = np.array([np.sqrt(np.mean(v[int(i * hop):int((i + 1) * hop)] ** 2))
                      for i in range(nf)], np.float32)
        return np.clip(e / (np.percentile(e, 97) + 1e-9), 0, 1.6)

    A = {'low': env(lo), 'high': env(hi), 'rms': env(x)}
    for k in ('low', 'high'):
        d = np.clip(np.diff(A[k], prepend=A[k][0]), 0, None)
        A[k + '_hit'] = np.clip(d / (np.percentile(d, 97) + 1e-9), 0, 1.6)
    return A


# ── 배경 ──────────────────────────────────────────────────
def vgrad(top, bot, y0=0.0, y1=1.0):
    y = np.clip((np.arange(H, dtype=np.float32) / H - y0) / max(1e-6, y1 - y0), 0, 1)
    return (top + (bot - top) * y[:, None]).astype(np.float32)[:, None, :]


def caustics(t, amp, scale=1.0):
    """수면 물빛. **1/3 해상도로 그려 키운다** — 원본 크기로 매 프레임 계산하면
    프레임당 몇 배가 든다. 어차피 흐려서 올리는 것이라 해상도가 안 아쉽다."""
    qw, qh = W // 3, H // 3
    yq, xq = np.mgrid[0:qh, 0:qw].astype(np.float32)
    x, y = xq * 0.052 * scale, yq * 0.052 * scale
    f = (np.sin(x * 1.6 + 1.7 * np.sin(y * 0.5 + t * 0.9)) +
         np.sin(y * 1.25 + 1.4 * np.sin(x * 0.44 - t * 0.7)) +
         0.85 * np.sin((x + y) * 0.95 + t * 1.3))
    k = np.clip(1 - np.abs(np.sin(f * 2.0)) * 6.4, 0, 1) ** 1.1
    k = cv2.resize(cv2.GaussianBlur(k, (0, 0), 1.0), (W, H), interpolation=cv2.INTER_LINEAR)
    return k * amp


def shafts(img, t, a):
    """물속에서 위를 보면 빛이 기둥으로 내려온다. 수면 돌파 전까지만."""
    if a <= 0.001:
        return
    xx = np.arange(W, dtype=np.float32) / W
    g = np.zeros(W, np.float32)
    for i, (c, wd) in enumerate(((0.22, 0.075), (0.44, 0.052), (0.63, 0.088), (0.84, 0.060))):
        g += np.exp(-((xx - (c + 0.014 * np.sin(t * 0.5 + i))) / wd) ** 2)
    fade = np.clip(1 - np.arange(H, dtype=np.float32) / (H * 0.86), 0, 1) ** 1.4
    img += (g[None, :] * fade[:, None])[..., None] * np.float32([0.55, 0.92, 1.00]) * a


def bubbles(img, t, a, rng_seed=3):
    """올라가는 기포. **크기가 다 다르고 속도도 다르다** — 같으면 눈이 규칙을 읽고
    그 순간 컴퓨터 그래픽으로 보인다."""
    if a <= 0.001:
        return
    rng = np.random.default_rng(rng_seed)
    L = np.zeros((H, W), np.float32)
    for i in range(46):
        sp = rng.uniform(0.055, 0.20)
        x = rng.uniform(0, 1) + 0.012 * np.sin(t * rng.uniform(0.7, 2.0) + i)
        y = (rng.uniform(0, 1) - t * sp) % 1.0
        r = max(1, int(rng.uniform(2.0, 7.5) * S))
        cv2.circle(L, (int(x * W), int(y * H)), r, float(rng.uniform(0.35, 1.0)), -1, cv2.LINE_AA)
        cv2.circle(L, (int(x * W), int(y * H)), r + max(1, int(S)), 0.30, max(1, int(S)), cv2.LINE_AA)
    img += cv2.GaussianBlur(L, (0, 0), 1.4 * S)[..., None] * np.float32([0.7, 0.95, 1.0]) * a


def rings(img, cx, cy, rs, a, col, ymin=None):
    """퍼지는 파문. 물판에서 박을 보여 주는 제일 자연스러운 방법이다.

    **물 안에서만 퍼진다.** 수평선을 중심으로 타원을 그렸더니 위쪽 반이 하늘로
    올라가 파문이 아니라 공중에 뜬 링으로 보였다."""
    L = np.zeros((H, W), np.float32)
    for r, g in rs:
        if r <= 1 or g <= 0.004:
            continue
        cv2.ellipse(L, (int(cx), int(cy)), (int(r), int(r * 0.34)), 0, 0, 360,
                    float(g), max(2, int(3 * S)), cv2.LINE_AA)
    if ymin is not None:
        L[:int(ymin)] = 0
    img += cv2.GaussianBlur(L, (0, 0), 1.6 * S)[..., None] * col * a


def sundisc(img, cy, k, glow):
    """지는 해. 이름이 걸린 뒤부터 수평선 위에 뜬다."""
    if k <= 0.004:
        return
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.115)) ** 2 + ((yy - cy) / (W * 0.115)) ** 2)
    # **수평선 아래는 안 그린다.** 반쯤 잠긴 원을 그대로 두면 지는 해가 아니라
    # 물속에 뜬 공으로 보인다 — 물빛까지 겹쳐서 기포와 구분이 안 됐다.
    above = (yy < cy + H * 0.004).astype(np.float32)
    disc = np.clip(1 - (r - 0.94) / 0.10, 0, 1) * above
    img += disc[..., None] * np.float32([1.00, 0.72, 0.42]) * k
    img += (np.exp(-r * 1.05) * (0.30 + 0.70 * above))[..., None] * np.float32([1.00, 0.58, 0.30]) * glow


def press(img, cy, half, amt):
    """**글자 자리는 배경을 눌러 만든다.** 밝은 판에서 흰 글자를 살리는 유일한 방법이다.
    외곽선이나 그림자를 두르면 대비는 안 생기고 글자만 지저분해진다."""
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= 1 - amt * np.exp(-((yy - cy) / half) ** 2)


def reveal(img, text, size, track, cy, k, color=PAPER, a=1.0, x=None):
    """왼쪽에서 오른쪽으로 열리는 글자. 한 번에 다 뜨면 기계가 읽는 것으로 안 보인다."""
    if k <= 0.004:
        return
    m = tmask(text, BRAND, int(size), track)
    h, w = m.shape
    cut = int(w * np.clip(k, 0, 1))
    if cut < 1:
        return
    paint(img, m[:, :cut], (W / 2 - w / 2) if x is None else x, cy, color=color, a=a)


def bloom(img, thr, sigma, amt, tint):
    lum = img @ np.float32([0.299, 0.587, 0.114])
    g = cv2.GaussianBlur(np.clip(lum - thr, 0, 1) / max(1e-3, 1 - thr), (0, 0), sigma)
    img += g[..., None] * tint * amt


def frame(t, i, A, rng):
    lo, hi = A['low'][i], A['high'][i]
    hit, hhit = A['low_hit'][i], A['high_hit'][i]

    # p = 0 물속 · 1 물 위. 수면 돌파에서 0.45초에 걸쳐 넘어간다
    p = float(np.clip((t - T_SURFACE) / 0.45, 0, 1))
    hz = H * (0.585 if W > H else 0.545)          # 수평선

    # 배경 — 물속 그라데이션에서 하늘+바다로 넘어간다
    under = vgrad(UNDER_T, UNDER_B)
    sky = np.concatenate([
        vgrad(SKY_T, SKY_B)[:int(hz)],
        vgrad(SEA_T, SEA_B)[int(hz):]], axis=0)
    img = np.repeat(under * (1 - p) + sky * p, W, axis=1).copy()

    # 물빛 — 물속에서는 위쪽(수면)에, 물 위에서는 수평선 아래에 걸린다
    yy = np.arange(H, dtype=np.float32)[:, None]
    depth = ((1 - np.clip(yy / (H * 0.8), 0, 1)) * (1 - p) +
             np.clip((yy - hz) / (H - hz + 1e-6), 0, 1) ** 0.8 * p)
    cw = caustics(t, 0.10 + 0.30 * lo, 1.0 + 0.5 * p) * depth
    img += cw[..., None] * np.float32([0.50, 0.88, 1.00])

    shafts(img, t, 0.30 * (1 - p) * (0.55 + 0.45 * hi))
    bubbles(img, t, 0.36 * (1 - p))

    # 수평선 한 줄 — 물 위로 나온 뒤에만
    if p > 0.01:
        img[int(hz):int(hz) + max(1, int(2 * S))] += PAPER * 0.30 * p

    # ── 박마다 퍼지는 파문 ────────────────────────────────
    if t >= T_SURFACE - 0.1:
        rs = []
        for k in range(14):
            at = T_SURFACE + k * BEAT if t < T_LOCK else T_LOCK + (k - 7) * BEAT
            age = t - at
            if 0 <= age < 1.5:
                rs.append((W * 0.10 + W * 0.62 * age / 1.5, 0.26 * (1 - age / 1.5) ** 1.8))
        rings(img, W / 2, hz if p > 0.5 else H * 0.62, rs, 0.55 + 0.5 * lo, AQUA,
              ymin=hz if p > 0.5 else None)

    # 수면 돌파 — 흰 섬광 한 번
    fl = np.clip(1 - abs(t - T_SURFACE) / 0.22, 0, 1) ** 1.6
    img += PAPER * fl * 0.85

    # 해 — 이름이 걸린 뒤부터
    ks = np.clip((t - T_LOCK) / 1.2, 0, 1) * (0.34 + 0.22 * lo)
    sundisc(img, hz, ks * 0.55, ks * 0.30)

    # ── 정적 — 한 박을 통째로 뺀다 ────────────────────────
    # **밝은 판에서 흰색으로 터뜨리려면 먼저 어두워져야 한다.** 이미 밝은 판에서
    # 흰 섬광을 치면 아무 일도 안 일어난 것으로 보인다.
    if T_GAP <= t < T_GO:
        img *= 0.12 + 0.10 * np.clip((T_GO - t) / BEAT, 0, 1)

    # ── 17.0  한 방 ───────────────────────────────────────
    if t >= T_GO:
        g = np.clip(1 - (t - T_GO) / 0.30, 0, 1) ** 1.4
        img += PAPER * g * 1.15
        img *= 1 + 0.30 * np.clip(1 - (t - T_GO) / 2.2, 0, 1)

    # ── 글자 ──────────────────────────────────────────────
    # 밝은 판에서는 글자 자리를 눌러야 산다
    if t < T_GAP:
        for txt, at, sz in LINES:
            k = np.clip((t - at) / 0.34, 0, 1) * np.clip((at + 1.28 - t) / 0.22, 0, 1)
            if k > 0.004:
                cy = H * (0.865 if W > H else 0.885)
                press(img, cy, H * 0.055, 0.62 * min(1, k * 2))
                reveal(img, txt, 34 * S * sz, 0.30, cy, k, PAPER, 0.96)

    # 9.5  BLACKOUT — 기계가 부르는 자리. 제일 크게
    kb = np.clip((t - T_SAY) / 0.20, 0, 1) * np.clip((T_SAY + 1.5 - t) / 0.30, 0, 1)
    if kb > 0.004:
        cy = H * 0.46
        press(img, cy, H * 0.10, 0.70 * min(1, kb * 2))
        nw = (W - M * 2) * 0.90
        reveal(img, 'BLACKOUT', fit('BLACKOUT', BRAND, nw, 0.12), 0.12, cy, kb, PAPER)

    # 11.0–  행사 이름. 걸린 뒤 끝까지 남는다
    kn = np.clip((t - T_LOCK) / 0.26, 0, 1)
    if kn > 0.004 and not (T_GAP <= t < T_GO):
        cy = H * (0.44 if W > H else 0.42)
        # **섬광이 클수록 더 눌러야 한다.** 판이 흰데 글자도 희면 아무것도 안 보인다.
        fg = np.clip(1 - (t - T_GO) / 0.30, 0, 1) ** 1.4 if t >= T_GO else 0.0
        press(img, cy, H * 0.115, min(0.94, 0.66 * min(1, kn * 2) + 0.30 * fg))
        nw = (W - M * 2) * 0.94
        reveal(img, EV.NAME, fit(EV.NAME, BRAND, nw, 0.10), 0.10, cy, kn, PAPER)

        # **이름 아래 한 칸은 하나만 쓴다.** 형식 두 줄과 날짜·장소를 둘 다 두면
        # 같은 자리에서 겹친다 — 실제로 19초부터 넉 줄이 포개져 있었다.
        y1 = cy + H * 0.075
        y2 = cy + H * 0.127
        if t < T_SETTLE:
            for j, (txt, at, col) in enumerate((('POOL PARTY', 13.35, AQUA),
                                                ('SOLO PARTY', 14.25, CORAL))):
                k2 = np.clip((t - at) / 0.22, 0, 1)
                if k2 > 0.004:
                    yy2 = y1 if j == 0 else y2
                    press(img, yy2, H * 0.038, min(0.90, 0.55 * min(1, k2 * 2) + 0.32 * fg))
                    reveal(img, txt, 40 * S, 0.26, yy2, k2, col, 0.98)
        else:
            kf = np.clip((t - T_SETTLE) / 0.5, 0, 1)
            press(img, (y1 + y2) / 2, H * 0.058, 0.62 * kf)
            paint(img, tmask(EV.DATE_EN, BRAND, int(30 * S), 0.24),
                  W / 2, y1, color=AQUA, a=float(kf) * 0.96, anchor='c')
            # **한글은 BRAND(Michroma)에 없다.** 그대로 넘기면 전부 □ 로 나온다
            paint(img, tmask(EV.VENUE, KR, int(26 * S), 0.02),
                  W / 2, y2, color=PAPER, a=float(kf) * 0.90, anchor='c')

    # 14 · 15 · 16  카운트다운 — 두 박마다 하나
    for j, n in enumerate(('3', '2', '1')):
        at = T_GO - BEAT * (6 - j * 2)
        k3 = np.clip((t - at) / 0.10, 0, 1) * np.clip((at + 0.85 - t) / 0.18, 0, 1)
        if k3 > 0.004:
            cy = H * (0.72 if W > H else 0.68)
            press(img, cy, H * 0.075, 0.72 * min(1, k3 * 2))
            m = tmask(n, BRAND, int(190 * S), 0.0)
            paint(img, m, W / 2, cy, color=PAPER, a=float(k3), anchor='c')

    # 17.0–  카운트인만 얹는다. 이름·형식·정보는 위 블록이 이미 그렸다
    if t >= T_GO:
        # ── 21.0–23.0  카운트인 네 칸 ──────────────────────
        # 소리로만 세면 화면을 보고 있던 사람이 놓친다. 같은 박을 눈으로도 준다.
        CUE = T_GO + BAR * 2
        if t >= CUE - 0.1:
            n = int(np.floor((t - CUE) / BEAT)) + 1
            bw, gp = W * 0.055, W * 0.020
            x0 = W / 2 - (bw * 4 + gp * 3) / 2
            ycue = H * (0.845 if W > H else 0.815)
            for j in range(4):
                on = j < n
                x = x0 + j * (bw + gp)
                a = 0.22 + 0.78 * (1 if on else 0)
                if on and (t - (CUE + j * BEAT)) < 0.14:
                    a = 1.0
                img[int(ycue):int(ycue + 9 * S), int(x):int(x + bw)] = \
                    img[int(ycue):int(ycue + 9 * S), int(x):int(x + bw)] * (1 - a) + \
                    (PAPER if j < 3 else CORAL) * a

    bloom(img, 0.72, 26 * S, 0.30 + 0.30 * hi, np.float32([1.00, 0.86, 0.72]))
    img += rng.standard_normal((H, W, 1)).astype(np.float32) * 0.006
    if t < 0.4:
        img *= t / 0.4
    return np.clip(img, 0, 1)


def render(cut):
    setcut(*CUTS[cut])
    wav = os.path.join(OUT, 'bgm_intro2.wav')
    if not os.path.exists(wav):
        raise SystemExit('먼저 python audio_intro2.py 를 돌리세요')
    nf = int(round(DUR * FPS))
    A = analyze(wav, nf)
    rng = np.random.default_rng(5)

    raw = os.path.join(OUT, f'raw2_{cut}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '19', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(nf):
        p.stdin.write((frame(i / FPS, i, A, rng) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f'intro2_{cut}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '22', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '224k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {DUR:.1f}s')


if __name__ == '__main__':
    import sys
    for c in ([a for a in sys.argv[1:] if a in CUTS] or list(CUTS)):
        render(c)
