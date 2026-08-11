"""
행사 인트로 **B안** 영상 — 밝은 풀파티. 23.0초 · 30fps · 120BPM.

A안(`intro.py`)은 어두운 기계실입니다. B안은 **색 판이 박 위에서 갈리는** 판입니다.

    0.0–4.3   짙은 물색. 아주 옅은 물빛만 흐른다
    4.3       흰 판으로 한 번 터지고 밝은 물색으로 갈린다
    9.5       다시 짙은 판. BLACKOUT 한 마디
    11.0      밝은 물색. 행사 이름이 걸린다
    13.0–16.5 **판이 갈리는 간격이 좁아진다** — 두 박 → 한 박 → 반 박
    16.5      먹판. 소리가 비는 한 박, 화면도 같이 빠진다
    17.0      흰 판으로 터지고 이름만 남는다. 마디마다 판이 갈린다
    19.0–23.0 카운트인 네 칸 (두 박마다 하나)
    23.0      끝. **여기가 노래 첫 박이다**

**처음 판은 겹이 너무 많았습니다.** 그라데이션 · 빛기둥 · 기포 · 파문 · 해 · 블룸을
다 얹고, 그 위에 글자를 살리려고 배경을 눌렀습니다. 누른 자국이 화면 가운데
검은 얼룩으로 남았고 그게 제일 지저분했습니다.

**대비는 배경을 눌러서 만들지 않습니다. 판 색을 바꿔서 만듭니다.**
밝은 판에서는 글자가 검정, 짙은 판에서는 흰색 — 자동으로 뒤집습니다.
얼룩이 원천적으로 안 생기고, 어느 프레임을 잘라도 넷 중 하나라서 정리돼 보입니다.

**파티 느낌은 장식이 아니라 템포에서 옵니다.** 물결이나 조명을 그려 넣으면
장식이 하나 더 늘 뿐입니다. 클럽에서 실제로 눈에 들어오는 건 **판이 박 위에서
통째로 갈리는 것**이고, 그 간격이 좁아지면 몸이 먼저 반응합니다. 셋만 씁니다.

    판 갈림    박 위에서 자른다. 페이드로 넘기면 무슨 일이 났는지 모른다
    간격 좁힘  13.0–16.5 에서 두 박 → 한 박 → 반 박. 이게 빌드다
    킥 펀치    저역 어택에 맞춰 판 전체가 1% 안쪽으로 튄다. 넘으면 글자가 떨린다

지키는 것 — 색은 넷뿐이고(짙은 물색 · 밝은 물색 · 흰색 · 먹색) 강조는 코랄 하나.
한 화면에 글자 한 덩어리만 둡니다. 물빛은 형태로 안 보일 만큼만 씁니다.

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
M, S = int(1920 * 0.085), 1.0

# audio_intro2.py 와 같은 값이어야 그림이 소리에 붙는다
T_SURFACE, T_SAY, T_LOCK = 4.30, 9.50, 11.0
T_BUILD, T_GO = 13.0, 17.0
T_GAP = T_GO - BEAT
T_SETTLE = 19.0
DUR = T_GO + BAR * 3

# 판 넷 + 강조 하나. 이것 말고 다른 색은 안 쓴다
DEEP = np.float32([0.035, 0.150, 0.215])
AQUA = np.float32([0.290, 0.780, 0.845])
PAPER = np.float32([0.975, 0.985, 0.985])
INK = np.float32([0.030, 0.038, 0.045])
CORAL = np.float32([0.980, 0.360, 0.300])

# 화면에 뜨는 글자 — audio_intro2.py 의 SPOKEN 과 같은 자리여야 한다
LINES = [('BLACKOUT', 1.70), ('SYSTEM ONLINE', 5.20),
         ('SOUND CHECK', 6.62), ('DOORS ARMED', 8.02)]


def setcut(w, h):
    """판을 갈아 끼운다. 글자 배율은 **짧은 변** 기준 —
    긴 변으로 잡으면 가로판에서 글자가 두 배로 커진다."""
    global W, H, M, S
    W, H = w, h
    M = int(W * (0.085 if W > H else 0.105))
    S = min(W, H) / 1080.0


def analyze(path, nf):
    with wave.open(path, 'rb') as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768.0
        x = x.reshape(-1, 2).mean(1)
    lo = signal.sosfilt(signal.butter(4, 160, 'lp', fs=sr, output='sos'), x)
    hop = len(x) / nf

    def env(v):
        e = np.array([np.sqrt(np.mean(v[int(i * hop):int((i + 1) * hop)] ** 2))
                      for i in range(nf)], np.float32)
        return np.clip(e / (np.percentile(e, 97) + 1e-9), 0, 1.6)

    A = {'low': env(lo), 'rms': env(x)}
    d = np.clip(np.diff(A['low'], prepend=A['low'][0]), 0, None)
    A['hit'] = np.clip(d / (np.percentile(d, 97) + 1e-9), 0, 1.6)
    return A


def field(t):
    """지금 판의 색. **페이드가 없다 — 박 위에서 잘린다.**

    13.0–16.5 는 판이 번갈아 갈리고 **그 간격이 좁아진다.** 소리의 라이저와
    같은 일을 화면이 한다 — 빌드를 밝기로만 하면 아무 일도 안 일어나 보인다."""
    if t < T_SURFACE:
        return DEEP
    if t < T_SAY:
        return AQUA
    if t < T_LOCK:
        return DEEP
    if t < T_BUILD:
        return AQUA
    if t < T_GAP:
        step = BEAT * 2 if t < 14.5 else (BEAT if t < 15.75 else BEAT * 0.5)
        base = 13.0 if t < 14.5 else (14.5 if t < 15.75 else 15.75)
        return DEEP if int((t - base) / step) % 2 else AQUA
    if t < T_GO:
        return INK
    # 한 방 뒤로는 **1초마다 갈린다.** 마디마다(2초) 갈랐더니 제일 센 구간이
    # 화면에서는 2초 동안 아무 일도 안 일어난 채 지나갔다 — 소리는 최대인데
    # 화면이 멈춰 있으면 그게 "마무리가 이상하다"로 읽힌다.
    # **마지막 카운트(22.5)에서 흰 판.** 판이 제일 밝아지는 자리가 곧 걸 자리다.
    if t >= T_GO + BAR + BEAT * 6:                 # 22.0 마지막 카운트
        return PAPER
    return (AQUA, DEEP, CORAL, DEEP, AQUA, DEEP)[min(5, int((t - T_GO) / 1.0))]


def ink_for(col):
    """판이 밝으면 글자는 검정, 짙으면 흰색. **자동으로 뒤집는다** —
    한쪽으로 고정하면 판이 갈릴 때마다 글자가 사라진다."""
    # 경계는 0.62 다. 0.45 로 뒀더니 코랄(0.54)에서 글자가 검정으로 나와
    # 대비가 거의 안 났다 — 채도 높은 색 위에서는 흰 글자가 훨씬 잘 읽힌다.
    return INK if float(col @ np.float32([0.299, 0.587, 0.114])) > 0.62 else PAPER


def light(t):
    """수면에서 흔들리는 빛. **윤곽이 생기면 안 된다.**

    처음엔 코스틱 공식(`1 - |sin(f)|` 을 세게 조인 것)을 썼는데, 그건 얇은 선을
    만들어서 판 위에 등고선 무늬가 깔렸다. 무늬가 보이는 순간 장식이 되고,
    장식이 하나 늘면 판이 싸구려가 된다. **낮은 주파수 세 겹을 그냥 더하고
    크게 흐린다** — 윤곽 없이 농담만 남아서 물 위에 있는 것처럼만 보인다."""
    qw, qh = W // 4, H // 4
    yq, xq = np.mgrid[0:qh, 0:qw].astype(np.float32)
    x, y = xq * 0.026, yq * 0.026
    f = (np.sin(x * 0.9 + t * 0.55) + np.sin(y * 0.75 - t * 0.42) +
         0.7 * np.sin((x + y) * 0.55 + t * 0.8))
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(f, (0, 0), W * 0.030) * 0.5


def center(img, text, size, track, cy, col, a=1.0, path=None):
    paint(img, tmask(text, path or BRAND, int(max(6, size)), track),
          W / 2, cy, color=col, a=float(a), anchor='c')


def wipe(img, text, size, track, cy, col, k, path=None):
    """왼쪽에서 오른쪽으로 열린다. 한 번에 다 뜨면 기계가 읽는 것으로 안 보인다."""
    m = tmask(text, path or BRAND, int(max(6, size)), track)
    h, w = m.shape
    cut = int(w * np.clip(k, 0, 1))
    if cut >= 1:
        paint(img, m[:, :cut], W / 2 - w / 2, cy, color=col, a=1.0)


def frame(t, i, A, rng):
    lo, hit = A['low'][i], A['hit'][i]
    col = field(t)
    ink = ink_for(col)
    img = np.repeat(np.repeat(col[None, None, :], H, 0), W, 1).copy()

    # 물빛 — 밝은 판에서는 어둡게, 짙은 판에서는 밝게. 어느 쪽이든 아주 옅게
    c = light(t)[..., None]
    img *= 1 + c * (0.075 if ink is INK else 0.16)

    # 판이 갈리는 두 자리에만 흰 섬광. 남발하면 안 보인다
    for at in (T_SURFACE, T_GO):
        g = np.clip(1 - (t - at) / 0.22, 0, 1) ** 1.6 if t >= at else 0.0
        if g > 0.004:
            img = img * (1 - g) + PAPER * g

    # ── 글자. **한 화면에 한 덩어리만** ───────────────────
    cy = H * 0.50
    if t < T_SAY:
        for txt, at in LINES:
            k = np.clip((t - at) / 0.30, 0, 1) * np.clip((at + 1.24 - t) / 0.18, 0, 1)
            if k > 0.004:
                wipe(img, txt, 30 * S, 0.42, cy, ink, k)

    elif t < T_LOCK:
        wipe(img, 'BLACKOUT', fit('BLACKOUT', BRAND, (W - M * 2) * 0.92, 0.12), 0.12,
             cy, ink, np.clip((t - T_SAY) / 0.18, 0, 1))

    elif T_GAP <= t < T_GO:
        pass                                           # 정적 — 먹판. 아무것도 없다

    else:
        k = np.clip((t - T_LOCK) / 0.22, 0, 1)
        ny = cy - H * (0.035 if W > H else 0.055)
        wipe(img, EV.NAME, fit(EV.NAME, BRAND, (W - M * 2) * 0.94, 0.10), 0.10, ny, ink, k)
        y1 = ny + H * (0.090 if W > H else 0.075)
        if t < T_SETTLE:
            # 형식은 **한 줄**. 두 줄로 쪼개면 판이 복잡해진다
            k2 = np.clip((t - 13.35) / 0.24, 0, 1)
            if k2 > 0.004:
                wipe(img, EV.FORMAT, 26 * S, 0.40, y1, ink, k2)
        else:
            # **여기도 컷이다.** 이 줄만 페이드로 들어오면 판의 규칙을 혼자 어긴다
            center(img, EV.DATE_EN, 26 * S, 0.40, y1, ink)
            center(img, EV.VENUE, 24 * S, 0.06, y1 + H * 0.048, ink, 0.86, KR)

    # 14 · 15 · 16  카운트다운. 판 아래쪽에 크게 하나 — 이름과 안 겹친다
    for j, n in enumerate(('3', '2', '1')):
        at = T_GO - BEAT * (6 - j * 2)
        k3 = np.clip((t - at) / 0.08, 0, 1) * np.clip((at + 0.80 - t) / 0.14, 0, 1)
        if k3 > 0.004:
            center(img, n, 210 * S, 0.0, H * (0.74 if W > H else 0.70), ink, k3)

    # ── 21.0–23.0  카운트인 네 칸 ─────────────────────────
    # 소리로만 세면 화면을 보던 사람이 놓친다. 같은 박을 눈으로도 준다.
    CUE = T_GO + BAR
    if t >= CUE - 0.05:
        # **두 박마다 하나.** 한 박마다 세면 네 번이 2초에 다 지나가 못 따라온다.
        n = int(np.floor((t - CUE) / (BEAT * 2))) + 1
        # **작으면 아무도 안 센다.** 폭 7.5% · 두께 16px 로 키우고 글자 바로 밑에 둔다.
        # 발치에 얇게 뒀더니 화면에서 제일 중요한 신호가 제일 안 보이는 것이 됐다.
        bw, gp = W * 0.075, W * 0.022
        x0 = W / 2 - (bw * 4 + gp * 3) / 2
        y = int(H * (0.760 if W > H else 0.715))
        th = max(4, int(16 * S))
        for j in range(4):
            x = int(x0 + j * (bw + gp))
            a = 1.0 if j < n else 0.22
            c2 = CORAL if j == 3 else ink
            sub = img[y:y + th, x:x + int(bw)]
            img[y:y + th, x:x + int(bw)] = sub * (1 - a) + c2 * a

    # **킥마다 판 전체가 튄다.** 1% 안쪽 — 넘으면 흔들리는 화면이 되고 글자가 떨린다.
    # 밝기로만 반응시키면 화면이 깜빡일 뿐 몸이 안 따라온다. 크기가 따라와야 박이다.
    z = 1.0 + 0.010 * hit
    if z > 1.0005:
        Mx = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        img = cv2.warpAffine(img, Mx, (W, H), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REPLICATE)
    img *= 1 + 0.028 * lo

    img += rng.standard_normal((H, W, 1)).astype(np.float32) * 0.0035
    if t < 0.35:
        img *= t / 0.35
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
    p.stdin.close()
    p.wait()

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
