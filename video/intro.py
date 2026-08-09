"""
행사 인트로 — AFTER SUNSET. 30fps · 24초.

    stage  1920×1080  **행사장 스크린·프로젝터용.** 이게 기본이다
    story  1080×1920  인스타 스토리·릴스용

**소리가 먼저 있고 그림이 따라갑니다.** `audio_intro.py` 가 만든 기계음의
저역·고역·어택을 프레임마다 읽어서 그 값으로 그립니다 —
릴레이가 딸깍하면 화면이 튀고, 금속이 울리면 셔터가 닫힙니다.
그림을 먼저 짜고 소리를 맞추면 항상 어긋납니다.

이야기는 **기계에 전원이 들어오는 과정**입니다.

    0.0–1.2   접점이 하나씩 붙는다. 검은 화면에 가로줄만 튄다
    1.2–3.6   전원이 들어온다. 하단 게이지가 차고 숫자가 올라간다
    3.6–4.4   배기 → 금속 타격. 셔터가 한 번 닫혔다 열린다
    4.8–10.4  기계가 돈다. 가운데 조리개 링이 돌고 글자가 찍힌다
    8.6–11.0  충전. 링이 빨라지고 빛이 차오른다
    11.0      판이 걸린다 — AFTER SUNSET. 기계 음성이 이름을 부른다
    11.0–13.2 이름만 두고, 기계가 화면의 글자를 읽는다
    13.2–16.35 다시 올린다. 3 · 2 · 1 카운트다운
    16.35–16.75 소리도 화면도 통째로 비운다. **정적이 한 방의 크기를 만든다**
    16.75     마지막 한 방. **여기서 디제이가 건다**
    16.75–24  화음이 울리는 동안 이름만 남기고 나머지를 걷는다

**끝은 페이드가 아니라 한 방입니다.** 페이드로 끝나면 디제이가 언제 걸어야 할지
모릅니다. 카운트다운 뒤 한 방이면 그 프레임에 정확히 걸 수 있습니다.

**인트로는 포스터가 아닙니다.** 날짜·주소·협업 브랜드는 넣지 않습니다 —
그건 포스터가 하는 일이고, 행사장에서 트는 화면에 주소를 띄울 이유가 없습니다.
인트로가 할 일은 **이름 하나를 각인시키는 것**뿐입니다.

색은 검정 · 흰색 · 호박색 하나. 브랜드가 흑백이라 색은 강조 하나만 씁니다.

행사장에서는 **가로**가 기본입니다. 스크린·프로젝터·LED 가 전부 16:9 라
세로로만 만들어 두면 양옆이 검게 비거나 잘립니다.

python intro.py            둘 다
python intro.py stage      행사장용만
"""
import os
import wave
import subprocess
import numpy as np
import cv2
from scipy import signal
from poster_kit import BRAND, tmask, fit, paint, rule, box, logo
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'intro')
os.makedirs(OUT, exist_ok=True)

FPS, DUR = 30, 24.0
CUTS = {'stage': (1920, 1080), 'story': (1080, 1920)}
W, H = 1920, 1080                      # render() 가 매번 갈아 끼운다
M = int(W * 0.062)
S = 1.0                                # 글자 배율. 짧은 변 기준이다

INK   = np.array([0.02, 0.02, 0.03], np.float32)
WHITE = np.array([0.96, 0.96, 0.95], np.float32)
AMBER = np.array([1.00, 0.74, 0.22], np.float32)

# 소리의 마디. audio_intro.py 와 같은 값이어야 그림이 소리에 붙는다
T_POWER, T_HIT, T_RUN, T_CHARGE, T_LOCK = 1.2, 4.3, 4.8, 8.6, 11.0
T_BUILD, T_GO = 13.2, 16.75        # 다시 올리는 구간과 마지막 한 방
T_GAP = 16.35                      # 소리가 통째로 비는 자리. 화면도 같이 끈다
T_SAY = 9.50                       # 기계가 BLACKOUT 을 부르는 자리
T_SETTLE = 18.6                    # 화음이 내려오기 시작하는 자리 — 여기서 이름만 남긴다


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


def setcut(w, h):
    """판을 갈아 끼운다. 글자 배율은 **짧은 변** 기준 —
    긴 변으로 잡으면 가로판에서 글자가 두 배로 커진다."""
    global W, H, M, S
    W, H = w, h
    M = int(W * (0.062 if W > H else 0.088))
    S = min(W, H) / 1080.0


def scanlines(img, t, amt):
    """가로줄. 기계 화면의 기본 질감이자, 릴레이가 붙을 때 튀는 자리."""
    y = np.arange(H, dtype=np.float32)
    g = (np.sin(y * 0.9 - t * 30.0) * 0.5 + 0.5) ** 3
    img += g[:, None, None] * WHITE * amt


def grid(img, a):
    """전원이 들어온 뒤 바닥에 깔리는 격자. 아주 옅게."""
    for x in range(M, W - M + 1, int(W * 0.104)):
        img[:, x:x + 1] += WHITE * a
    for y in range(int(H * 0.10), int(H * 0.92), int(W * 0.104)):
        img[y:y + 1, M:W - M] += WHITE * a


def gauge(img, k, V):
    """하단 게이지 + 숫자. 차오르는 걸 보여 주는 게 목적이라 눈금을 촘촘히 둔다."""
    y = int(H * 0.86)
    x0, x1 = M, W - M
    rule(img, y, x0, x1, WHITE, 0.22, 2)
    box(img, x0, y - 14 * S, x0 + (x1 - x0) * k, y, AMBER, 0.9)
    for i in range(21):                                   # 눈금
        gx = x0 + (x1 - x0) * i / 20
        rule(img, y + 8 * S, gx, gx + 2, WHITE, 0.30 if i % 5 else 0.6, int(8 * S))
    paint(img, tmask(f'{int(k * 100):03d}', BRAND, int(30 * S), 0.18), x1, y - 34 * S,
          color=AMBER, anchor='r')
    paint(img, tmask('POWER', BRAND, int(20 * S), 0.30), x0, y - 34 * S, color=WHITE, a=0.55)


def ring(img, cy, r, ang, seg, a, th=3):
    """점선 조리개 링. 실선으로 그리면 도는 게 안 보인다."""
    for i in range(seg):
        a0 = ang + i * 2 * np.pi / seg
        a1 = a0 + 2 * np.pi / seg * 0.55
        p = np.linspace(a0, a1, 14)
        pts = np.stack([W / 2 + np.cos(p) * r, cy + np.sin(p) * r], 1).astype(np.int32)
        cv2.polylines(img, [pts], False, tuple(float(v * a) for v in WHITE), th, cv2.LINE_AA)


def shutter(img, k):
    """위아래에서 닫히는 판. k=1 이면 완전히 닫힌다."""
    h = int(H * 0.5 * k)
    if h > 0:
        box(img, 0, 0, W, h, INK)
        box(img, 0, H - h, W, H, INK)
        rule(img, h - 3, 0, W, AMBER, 0.8, 3)
        rule(img, H - h, 0, W, AMBER, 0.8, 3)


def converge(img, p, k):
    """양쪽에서 다가오는 두 줄. **초반 집중은 여기서 만든다.**

    줄은 일정한 속도로 오는데 딸깍은 남은 거리의 0.62 배마다 나므로
    자연히 점점 빨라진다 — 사람은 언제 만나는지 세기 시작한다.
    소리(`audio_intro.py` 의 가속 박)와 같은 식에서 나온 값이라 저절로 맞는다."""
    x0, x1 = int(W / 2 - p * W * 0.44), int(W / 2 + p * W * 0.44)
    y0, y1 = int(H * 0.44), int(H * 0.56)
    a = 0.30 + 0.55 * (1 - p) + 0.45 * k
    w = max(2, int(3 * S))
    for x in (x0, x1):
        box(img, x - w, y0, x + w, y1, AMBER, min(1.0, a))
    # 가운데 만나는 자리를 미리 찍어 둔다. 목표가 보여야 기다려진다
    box(img, W / 2 - 1, H * 0.487, W / 2 + 1, H * 0.513, WHITE, 0.30)


def horizon(img, y, k):
    """해가 진 자리. **행사 이름이 AFTER SUNSET 이라 이 한 겹이 그림을 설명한다.**

    한 방 뒤 화면이 검정 하나로만 남으면 웅장한 게 아니라 그냥 빈 화면이다.
    아래쪽에 옅은 노을을 깔면 이름이 놓인 자리가 생기고 판이 넓어 보인다.
    선이 아니라 **번짐**이어야 한다 — 선을 그으면 수평선이 아니라 괘선이 된다."""
    if k <= 0.004:
        return
    g = np.exp(-((np.arange(H, dtype=np.float32) - y) / (H * 0.20)) ** 2)
    img += g[:, None, None] * AMBER * k


def typed(img, text, path, size, track, x, y, k, color=WHITE, a=1.0):
    """글자가 하나씩 찍힌다. 기계가 치는 것처럼 보이려면 통째로 나타나면 안 된다."""
    n = int(len(text) * np.clip(k, 0, 1))
    if n <= 0:
        return
    paint(img, tmask(text[:n], path, size, track), x, y, color=color, a=a)


def slices(img, amt, rng):
    if amt < 0.3:
        return img
    out = img.copy()
    for _ in range(int(2 + amt * 6)):
        y = int(rng.integers(0, H - 60))
        h = int(rng.integers(12, 110))
        out[y:y + h] = np.roll(out[y:y + h], int(rng.integers(-1, 2) * amt * 120), axis=1)
    return out


def frame(t, i, A, rng):
    img = np.zeros((H, W, 3), np.float32) + INK
    lo, hi = A['low'][i], A['high'][i]
    hit, hhit = A['low_hit'][i], A['high_hit'][i]

    # ── 0.0–1.2 접점 ──────────────────────────────────────
    if t < T_POWER:
        scanlines(img, t, 0.05 + 0.55 * hhit)
        if hhit > 0.5:                                     # 딸깍할 때만 로고가 한 번 스친다
            paint(img, logo(int(120 * S)), W / 2, H * 0.5, color=WHITE, a=0.35 * hhit, anchor='c')
        return np.clip(img, 0, 1)

    # ── 전원이 들어온 뒤 공통 바닥 ─────────────────────────
    on = np.clip((t - T_POWER) / 1.4, 0, 1)
    # 한 방 뒤에는 격자와 형식 줄을 걷어 낸다. 다만 **머리글까지 지웠더니 허전했다** —
    # 이름 하나만 남은 화면은 집중되는 게 아니라 비어 보인다.
    # 지울 건 정보(형식·격자)고, 남길 건 누가 만든 판인지다.
    st = np.clip((t - T_SETTLE) / 2.4, 0, 1) ** 0.8
    grid(img, 0.028 * on * (1 - st))
    scanlines(img, t, 0.020 + 0.10 * hhit)

    # 상단 고정 표식
    hy = H * (0.085 if W > H else 0.062)
    paint(img, logo(int(46 * S)), M, hy, color=WHITE, a=0.85 * on)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(18 * S), 0.30), M + int(64 * S), hy,
          color=WHITE, a=0.75 * on)
    paint(img, tmask('SEOUL', BRAND, int(18 * S), 0.30), W - M, hy,
          color=AMBER, a=0.7 * on, anchor='r')

    # ── 1.2–4.3 게이지가 찬다 ─────────────────────────────
    if t < T_LOCK:
        gauge(img, np.clip((t - T_POWER) / (T_CHARGE + 2.4 - T_POWER), 0, 1), 1.0)

    # ── 2.4–4.3 두 줄이 다가온다. 딸깍이 빨라지는 구간 ─────
    if T_HIT - 1.90 < t < T_HIT:
        converge(img, np.clip((T_HIT - t) / 1.90, 0, 1), hhit)

    # ── 4.8–11.0 기계가 돈다 ──────────────────────────────
    if T_RUN - 0.4 < t < T_LOCK:
        k = np.clip((t - T_RUN + 0.4) / 0.6, 0, 1)
        spin = 1.0 + 4.5 * np.clip((t - T_CHARGE) / (T_LOCK - T_CHARGE), 0, 1) ** 2
        # 링 반지름은 **짧은 변** 기준. 긴 변으로 잡으면 가로판에서 화면 밖으로 나간다
        cy = H * (0.46 if W > H else 0.44)
        R = min(W, H)
        ring(img, cy, R * 0.30 * k, t * 0.9 * spin, 12, (0.30 + 0.45 * lo) * k)
        ring(img, cy, R * 0.24 * k, -t * 1.4 * spin, 8, (0.22 + 0.35 * lo) * k, 2)
        ring(img, cy, R * 0.10 * k, t * 2.2 * spin, 4, (0.35 + 0.5 * lo) * k, 4)
        # 상태 문구가 한 줄씩 찍힌다
        for j, (txt, t0) in enumerate((('SYSTEM ONLINE', 5.2), ('SOUND CHECK', 6.6),
                                       ('DOORS ARMED', 8.0))):
            typed(img, txt, BRAND, int(24 * S), 0.28, M,
                  H * ((0.615 if W > H else 0.655) + j * (0.048 if W > H else 0.035)),
                  (t - t0) / 0.5, WHITE, 0.55)
        # ── 9.58 기계가 이름을 부른다 ─────────────────────
        # **글자를 같이 띄워야 들린다.** 포먼트 합성은 완전히 또렷하진 않지만
        # 눈이 본 글자로 귀가 소리를 해석한다. 소리 쪽도 이 구간을 비워 뒀다.
        bq = (t - T_SAY) / 0.87
        if -0.08 <= bq < 1.40:
            a = np.clip((bq + 0.08) / 0.12, 0, 1) * np.clip((1.40 - bq) / 0.38, 0, 1)
            bw = int((W - M * 2) * (0.70 if W > H else 1.0))
            paint(img, tmask('BLACKOUT', BRAND, fit('BLACKOUT', BRAND, bw, 0.10), 0.10),
                  W / 2, cy, color=WHITE, a=a, anchor='c')

        # 충전 구간 — 빛이 차오른다
        ch = np.clip((t - T_CHARGE) / (T_LOCK - T_CHARGE), 0, 1)
        img += (ch ** 3) * 0.18 * AMBER

    # ── 4.3 금속 타격에 셔터가 한 번 닫힌다 ────────────────
    if T_HIT - 0.02 < t < T_HIT + 0.42:
        shutter(img, 1 - abs(t - (T_HIT + 0.2)) / 0.22)

    # ── 11.0 판이 걸린다 ──────────────────────────────────
    if t >= T_LOCK:
        k = np.clip((t - T_LOCK) / 0.5, 0, 1)
        img += (1 - k) ** 2 * 0.9 * WHITE                  # 터지는 순간의 백색
        # 가로판은 폭이 넉넉해서 이름을 꽉 채우면 오히려 싸 보인다. 62% 까지만.
        nw = int((W - M * 2) * (0.62 if W > H else 1.0))
        nm = tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, nw, 0.06), 0.06)
        ny = H * (0.36 if W > H else 0.40)
        paint(img, nm, M, ny, color=WHITE, a=k)
        rule(img, ny + 62 * S, M, M + (W - M * 2) * k, AMBER, 0.75 * (1 - st), int(3 * S))
        paint(img, tmask(EV.FORMAT, BRAND, int(30 * S), 0.10), M, ny + 108 * S,
              color=AMBER, a=k * 0.95 * (1 - st))

        # 끝의 빈자리는 **정보가 아니라 브랜드 마크로** 채운다. 날짜·주소를 붙이면
        # 인트로가 아니라 포스터가 되고, 아무것도 안 두면 허전하다.
        # 엠블럼은 글자가 아니라 형태라 이름과 싸우지 않는다. 아주 옅게.
        if st > 0.01:
            paint(img, logo(int(min(W, H) * 0.46)), W / 2, H * (0.66 if W > H else 0.70),
                  color=WHITE, a=0.12 * st, anchor='c')

        img *= 0.94 + 0.10 * A['rms'][i]

        # ── 13.2–16.35 다시 올린다 ────────────────────────
        if t >= T_BUILD:
            # 차오른 호박빛은 **한 방과 함께 빠져야 한다.** 안 빼면 그대로 남아
            # 검정이 갈색이 되고, 밤 행사 화면이 흙빛으로 보인다.
            rz = (np.clip((t - T_BUILD) / (T_GO - T_BUILD), 0, 1)
                  * (1 - np.clip((t - T_GO) / 0.8, 0, 1)))
            img += (rz ** 3) * 0.26 * AMBER
            # 3 · 2 · 1 — 크게 떴다가 줄어들며 사라진다. 디제이가 볼 시계다
            # audio_intro.py 의 SPOKEN 과 같은 값이어야 입과 화면이 맞는다
            for num, t0 in (('3', 14.95), ('2', 15.50), ('1', 16.02)):
                q = (t - t0) / 0.48
                if 0 <= q < 1:
                    # 이름·형식 줄 아래에 놓는다. 가운데에 크게 두면 이름을 덮는다
                    sz = int(min(W, H) * 0.34 * (1.20 - 0.20 * q))
                    paint(img, tmask(num, BRAND, sz), W / 2, H * (0.68 if W > H else 0.68),
                          color=WHITE, a=(1 - q) ** 0.55, anchor='c')

        # ── 16.35–16.75 소리가 통째로 비는 구간 ───────────
        # 화면도 같이 끈다. **정적과 암전이 겹쳐야 다음 한 방이 두 배로 크다** —
        # 소리만 비우고 화면을 켜 두면 그냥 음이 끊긴 것처럼 들린다.
        if T_GAP <= t < T_GO:
            img *= max(0.0, 1.0 - (t - T_GAP) / 0.08)

        # ── 16.75 마지막 한 방 ────────────────────────────
        if t >= T_GO:
            g = np.clip((t - T_GO) / 0.32, 0, 1)
            img += ((1 - g) ** 2) * 1.15 * WHITE
            # **큰 화면에서는 번짐이 크기다.** 밝은 데를 뽑아 흐려 더하면
            # 글자가 빛을 내는 것처럼 보인다 — 화음이 버티는 동안 같이 버틴다.
            bl = np.exp(-(t - T_GO) / 2.6) * (0.30 + 0.55 * A['rms'][i])
            if bl > 0.02:
                img += cv2.GaussianBlur(np.clip(img - 0.42, 0, 1), (0, 0),
                                        int(min(W, H) * 0.024)) * bl * 2.4
            # 화면 아래에서 노을이 부풀었다 7초에 걸쳐 물러난다. 소리에 맞춰 숨 쉰다.
            # **검정 하나만 남기면 웅장한 게 아니라 빈 화면이다.**
            horizon(img, H * 1.02,
                    0.34 * np.exp(-(t - T_GO) / 3.4) * (0.55 + 0.45 * A['rms'][i]))

    if t > 10.4:
        img = slices(img, hhit if t < T_LOCK else hhit * 0.5, rng)
    img += rng.standard_normal((H, W, 1)).astype(np.float32) * 0.010
    tail = DUR - t
    if tail < 0.75:                       # 화음 꼬리와 같이 걷힌다
        img *= max(0.0, tail / 0.75)
    return np.clip(img, 0, 1)


def render(cut):
    setcut(*CUTS[cut])
    wav = os.path.join(OUT, 'bgm_intro.wav')
    if not os.path.exists(wav):
        raise SystemExit('먼저 python audio_intro.py 를 돌리세요')
    nf = int(round(DUR * FPS))
    A = analyze(wav, nf)
    rng = np.random.default_rng(5)

    raw = os.path.join(OUT, f'raw_{cut}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '19', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(nf):
        p.stdin.write((frame(i / FPS, i, A, rng) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f'intro_{cut}.mp4')
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
