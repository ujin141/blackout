"""
BLACKOUT — 오프닝 3 (1080x1920, 29초)
컨셉: 오실로스코프. 실제로 만든 음원을 읽어 파형을 그린다.
오프닝 1(빛기둥·관객)·2(터널)와 시각 언어를 겹치지 않게 —
빛기둥, 헤이즈, 소실점, 관객 실루엣을 쓰지 않는다. 선과 격자와 데이터만 쓴다.
가운데 정렬 대신 좌측 기준 그리드에 글자를 놓고, 빌드 구간은 흑백을 뒤집는다.

python opening3.py            전체 렌더
python opening3.py 16.0 18.5  구간 미리보기
"""
import os
import subprocess
import sys
import wave
import numpy as np
import cv2

from render import (W, H, FPS, BRAND, MARK_A, WORD_A, text_mask, blit,
                    grain, chroma, shake, zoom, out_expo, clamp01)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

BPM = 174.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 21
DUR = BAR * BARS
NF = int(round(DUR * FPS))

MARGIN = 96
GX0, GX1 = MARGIN, W - MARGIN          # 계측 영역 좌우
CY = H * 0.47                          # 파형 기준선


def T(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


S2, S3, S4 = T(3, 0), T(7, 0), T(10, 0)
WHITE = T(13, 0)                       # 흑백 반전 구간
DROP = T(14, 0)

# 킥·스네어 위치 (audio_open3 의 패턴과 맞춤)
_K = [[0, 10], [0, 10], [0, 6, 10], [0, 10, 11]]
_S = [8]
KICKS, SNARES = [], []
for _b in range(3, 22):
    if _b in (12, 13):
        continue
    _p = _K[(_b - 3) % 4]
    KICKS += [(_b - 1) * BAR + s * BAR / 16 for s in _p]
    SNARES += [(_b - 1) * BAR + s * BAR / 16 for s in _S]

WORDS_L = ['SEOUL', 'HOUSE', 'TECHNO', 'MINIMAL']
WORDS_R = ['UNDERGROUND', 'ENERGY', 'UNITY', 'FUTURE']


# ── 음원 읽기 ──────────────────────────────────────────────
def _load():
    p = os.path.join(OUT, 'bgm_open3.wav')
    if not os.path.exists(p):
        print('[opening3] bgm_open3.wav 없음 — 파형을 난수로 대체합니다.')
        return None, None, 44100
    with wave.open(p, 'rb') as w:
        sr = w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768.0
    if w.getnchannels() == 2:
        raw = raw.reshape(-1, 2)
        return raw[:, 0], raw[:, 1], sr
    return raw, raw, sr


LCH, RCH, SR = _load()
_RNG = np.random.default_rng(5)
_FAKE = _RNG.standard_normal(44100 * 30).astype(np.float32) * 0.3


def win(t, n=2048, ch=0):
    """t 시점의 샘플 창"""
    src = _FAKE if LCH is None else (LCH if ch == 0 else RCH)
    i = int(t * SR)
    if i < 0:
        i = 0
    if i + n > len(src):
        out = np.zeros(n, np.float32)
        m = max(0, len(src) - i)
        out[:m] = src[i:i + m]
        return out
    return src[i:i + n]


# ── 그리기 도구 ────────────────────────────────────────────
_BW, _BH = W // 2, H // 2


def _layer():
    return np.zeros((_BH, _BW), np.float32)


def _push(dst, layer, a, blur=0.9):
    if blur > 0:
        layer = cv2.GaussianBlur(layer, (0, 0), blur)
    dst += cv2.resize(layer, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def grid(dst, a, dense=1.0, y0=0.16, y1=0.84):
    """계측 격자"""
    if a <= 0.004:
        return
    L = _layer()
    step = max(6, int(46 / dense))
    for x in range(int(GX0 / 2), int(GX1 / 2) + 1, step):
        cv2.line(L, (x, int(_BH * y0)), (x, int(_BH * y1)), 0.30, 1, cv2.LINE_AA)
    for y in range(int(_BH * y0), int(_BH * y1) + 1, step):
        cv2.line(L, (int(GX0 / 2), y), (int(GX1 / 2), y), 0.30, 1, cv2.LINE_AA)
    # 테두리와 십자
    cv2.rectangle(L, (int(GX0 / 2), int(_BH * y0)), (int(GX1 / 2), int(_BH * y1)), 0.85, 1, cv2.LINE_AA)
    _push(dst, L, a, 0.7)


def ticks(dst, a):
    """좌우 눈금"""
    if a <= 0.004:
        return
    L = _layer()
    for i in range(11):
        y = int(_BH * 0.18 + (_BH * 0.64) * i / 10)
        w = 16 if i % 5 else 30
        cv2.line(L, (int(GX0 / 2) - 4, y), (int(GX0 / 2) - 4 - w, y), 0.8, 1, cv2.LINE_AA)
        cv2.line(L, (int(GX1 / 2) + 4, y), (int(GX1 / 2) + 4 + w, y), 0.8, 1, cv2.LINE_AA)
    _push(dst, L, a, 0.6)


def scope(dst, t, a, cy=CY, amp=250.0, n=1400, th=2, ch=0, glow=0.0):
    """오실로스코프 파형"""
    if a <= 0.004:
        return
    s = win(t, 3072, ch)
    idx = np.linspace(0, len(s) - 1, n).astype(np.int32)
    v = s[idx]
    xs = np.linspace(GX0 / 2, GX1 / 2, n)
    ys = cy / 2 - v * (amp / 2)
    pts = np.stack([xs, ys], axis=1).astype(np.int32)
    L = _layer()
    cv2.polylines(L, [pts], False, 1.0, th, cv2.LINE_AA)
    _push(dst, L, a, 0.8)
    if glow > 0:
        L2 = _layer()
        cv2.polylines(L2, [pts], False, 1.0, th + 2, cv2.LINE_AA)
        _push(dst, L2, a * glow, 6.0)


def xy(dst, t, a, r=300.0, spin=0.0, th=2):
    """리사주 — 좌우 채널을 X-Y로 찍는다"""
    if a <= 0.004:
        return
    n = 2048
    x = win(t, n, 0)
    y = win(t, n, 1)
    c, s = np.cos(spin), np.sin(spin)
    px = (x * c - y * s) * (r / 2) + W / 4
    py = (x * s + y * c) * (r / 2) + CY / 2
    pts = np.stack([px, py], axis=1).astype(np.int32)
    L = _layer()
    cv2.polylines(L, [pts], False, 1.0, th, cv2.LINE_AA)
    _push(dst, L, a, 1.1)


def spectrum(dst, t, a, y=0.0, h=150.0, bands=48, gap=5):
    """FFT 막대"""
    if a <= 0.004:
        return
    s = win(t, 4096, 0) * np.hanning(4096)
    mag = np.abs(np.fft.rfft(s))
    edges = np.geomspace(3, min(len(mag) - 1, 1400), bands + 1).astype(np.int32)
    L = _layer()
    bw = (GX1 - GX0) / 2 / bands
    for i in range(bands):
        seg = mag[edges[i]:max(edges[i] + 1, edges[i + 1])]
        v = float(np.sqrt(seg.mean() + 1e-9))
        v = clamp01(v * 0.85)
        bh = max(1, int(v * h / 2))
        x0 = int(GX0 / 2 + i * bw) + gap // 2
        x1 = int(GX0 / 2 + (i + 1) * bw) - gap // 2
        cv2.rectangle(L, (x0, int(y / 2)), (x1, int(y / 2) - bh), 1.0, -1)
    _push(dst, L, a, 0.7)


def tear(dst, t, a, seed=0):
    """가로 찢김"""
    if a <= 0.01:
        return
    rng = np.random.default_rng(int(t * 53) % 9999 + seed)
    for _ in range(3):
        y = int(rng.random() * H)
        h = int(4 + rng.random() * 30)
        sh = int((rng.random() - 0.5) * 90 * a)
        y0, y1 = max(0, y), min(H, y + h)
        if y1 <= y0 or sh == 0:
            continue
        dst[y0:y1] = np.roll(dst[y0:y1], sh, axis=1)


def label(dst, txt, x, y, size, a, track=0.24, glow=0.0, left=True):
    """좌측 정렬 텍스트"""
    if a <= 0.004:
        return
    m = text_mask(txt, BRAND, size=size, track_em=track)
    cx = x + m.shape[1] / 2 if left else x - m.shape[1] / 2
    blit(dst, m, cx, y, a, glow=glow, glow_r=14)


def rule(dst, x0, x1, y, a, th=2):
    if a <= 0.004 or x1 <= x0:
        return
    m = np.full((th, int(x1 - x0)), 255, np.uint8)
    blit(dst, m, (x0 + x1) / 2, y, a)


def readout(dst, t, a):
    """모서리 계측 표시"""
    if a <= 0.004:
        return
    label(dst, 'BLACKOUT', GX0, 150, 26, a * 0.9, 0.3)
    label(dst, 'SIGNAL / 174 BPM', GX0, 190, 15, a * 0.45, 0.28)
    tc = f'{int(t // 60):02d}:{int(t % 60):02d}:{int((t % 1) * 30):02d}'
    label(dst, tc, GX1, 150, 22, a * 0.55, 0.22, left=False)
    label(dst, 'CH.L / CH.R', GX1, 190, 15, a * 0.4, 0.28, left=False)


def since(times, t):
    past = [k for k in times if k <= t + 1e-4]
    return (t - past[-1]) if past else 9.0


def env(times, t, decay=14.0):
    return float(np.exp(-since(times, t) * decay))


# ── 프레임 ─────────────────────────────────────────────────
def frame(t, fi):
    img = np.zeros((H, W, 3), np.float32)
    k = env(KICKS, t, 15.0)
    sn = env(SNARES, t, 11.0)
    flash = 0.0
    ab = 0.0
    sx = sy = 0.0
    cam = 1.0
    invw = 0.0                                  # 흰 화면 정도

    # ── 1~2마디: 신호 대기 ─────────────────────────────────
    if t < S2:
        p = clamp01(t / (BAR * 2))
        grid(img, 0.07 + p * 0.05)
        ticks(img, p * 0.20)
        readout(img, t, clamp01((t - 0.3) / 0.8) * 0.7)
        # 거의 평평한 선 + 블립
        scope(img, t, 0.55 + k * 0.2, amp=40 + 90 * p, th=2)
        rule(img, GX0, GX0 + (GX1 - GX0) * out_expo(p), CY + 250, 0.25)
        if t > 1.1:
            label(img, 'ACQUIRING SIGNAL', GX0, CY + 300,
                  17, clamp01((t - 1.1) / 0.5) * 0.5, 0.3)

    # ── 3~6마디: 브레이크 진입 ─────────────────────────────
    elif t < S3:
        p = clamp01((t - S2) / (BAR * 4))
        grid(img, 0.11 + k * 0.05)
        ticks(img, 0.24)
        readout(img, t, 0.8)
        scope(img, t, 0.85, amp=260 + k * 90, th=2, glow=0.35)
        spectrum(img, t, 0.30 + p * 0.2, y=H * 0.80, h=120 + p * 60)
        rule(img, GX0, GX1, CY + 250, 0.22)
        rule(img, GX0, GX1, H * 0.80, 0.3)
        cam = 1.0 + k * 0.006
        ab = k * 1.5
        # 좌측 단어가 한 마디마다 교체
        i = int((t - S2) / BAR) % len(WORDS_L)
        d = (t - S2) % BAR
        a = clamp01(d / 0.08) * (1 - clamp01((d - BAR * 0.72) / (BAR * 0.24)))
        label(img, WORDS_L[i], GX0, CY + 330, 62, a * 0.95, 0.14, glow=0.3)
        if sn > 0.5:
            tear(img, t, 0.25 * sn)

    # ── 7~9마디: 리사주 + 밀도 ─────────────────────────────
    elif t < S4:
        p = clamp01((t - S3) / (BAR * 3))
        grid(img, 0.13, dense=1.0 + p * 0.5)
        ticks(img, 0.26)
        readout(img, t, 0.85)
        xy(img, t, 0.55 + k * 0.2, r=360 + p * 130 + k * 40, spin=t * 0.5, th=2)
        scope(img, t, 0.5, cy=H * 0.20, amp=150, n=900, th=1, ch=0)
        scope(img, t, 0.5, cy=H * 0.74, amp=150, n=900, th=1, ch=1)
        spectrum(img, t, 0.42, y=H * 0.86, h=170)
        rule(img, GX0, GX1, H * 0.86, 0.32)
        cam = 1.0 + k * 0.01 + p * 0.02
        ab = 2 + k * 4
        sx += np.sin(t * 150) * k * 2
        # 좌우 두 컬럼
        i = int((t - S3) / (BAR / 2)) % 4
        d = (t - S3) % (BAR / 2)
        a = clamp01(d / 0.05) * (1 - clamp01((d - BAR * 0.32) / (BAR * 0.18)))
        label(img, WORDS_L[i], GX0, H * 0.90, 34, a * 0.8, 0.18)
        label(img, WORDS_R[i], GX1, H * 0.90, 34, a * 0.8, 0.18, left=False)
        if sn > 0.4:
            tear(img, t, 0.35 * sn, 3)

    # ── 10~12마디: 빌드 ────────────────────────────────────
    elif t < WHITE:
        prog = clamp01((t - S4) / (WHITE - S4))
        grid(img, 0.13 + prog * 0.12, dense=1.5 + prog * 2.2)
        ticks(img, 0.26)
        readout(img, t, 0.85)
        xy(img, t, 0.6 + prog * 0.3, r=460 + prog * 420, spin=t * (0.6 + prog * 3), th=2)
        scope(img, t, 0.55, cy=H * 0.20, amp=150 + prog * 160, n=900, th=1)
        scope(img, t, 0.55, cy=H * 0.74, amp=150 + prog * 160, n=900, th=1, ch=1)
        spectrum(img, t, 0.45 + prog * 0.25, y=H * 0.86, h=170 + prog * 130)
        cam = 1.0 + prog * 0.06 + k * 0.01
        ab = 3 + 16 * prog
        sh = (2 + 14 * prog) * max(k, sn)
        sx += np.sin(t * 200) * sh
        sy += np.cos(t * 168) * sh
        tear(img, t, 0.2 + 0.5 * prog, 7)
        label(img, 'STAND BY', GX0, H * 0.90, 30,
              (0.4 + 0.6 * (int(t / 0.12) % 2)) * prog, 0.3)
        flash = max(flash, sn * 0.18 * prog)

    # ── 13마디: 흑백 반전 — 흰 화면 ────────────────────────
    elif t < DROP:
        d = (t - WHITE) / (DROP - WHITE)
        invw = 1.0
        grid(img, 0.5 + d * 0.3, dense=3.5)
        ticks(img, 0.5)
        scope(img, t, 0.95, amp=200 + d * 500, th=3)
        xy(img, t, 0.7, r=500 + d * 700, spin=t * 5, th=3)
        # 검정 글씨(반전되므로 흰 마스크로 그린다)
        label(img, 'BLACKOUT', GX0, 150, 26, 0.95, 0.3)
        label(img, 'DROP', GX1, 150, 26, 0.95, 0.3, left=False)
        cam = 1.0 + d * 0.1
        sh = 6 + 26 * d
        sx += np.sin(t * 240) * sh
        sy += np.cos(t * 191) * sh
        tear(img, t, 0.8, 11)
        if d > 0.86:                              # 마지막 순간 완전 백색
            invw = 1.0
            img *= max(0.0, 1 - (d - 0.86) / 0.14)

    # ── 14~21마디: 드롭 ────────────────────────────────────
    else:
        d = t - DROP
        grid(img, 0.10 + k * 0.04, dense=1.2)
        ticks(img, 0.22)
        readout(img, t, 0.7)
        cam = 1.0 + max(0.0, 0.22 * (1 - out_expo(d / 0.5))) + k * 0.012
        sh = max(0.0, 1 - d / 0.45) ** 2 * 26 + max(k, sn) * 2.5
        sx += np.sin(d * 170) * sh
        sy += np.cos(d * 141) * sh
        ab = max(0.0, 22 * (1 - d / 0.4)) + k * 2.5
        flash = max(0.0, 0.95 - d * 11)

        # 엠블럼이 신호에서 솟아오른다
        s = 0.20 + out_expo(clamp01(d / 0.45)) * 0.52
        s *= (1 + k * 0.02)
        blit(img, MARK_A, W / 2, CY - 120, 1.0,
             glow=0.45 + k * 0.45, glow_r=46, scale=s)

        # 파형은 로고 위아래로 계속 흐른다
        scope(img, t, 0.6, cy=H * 0.17, amp=190 + k * 60, n=1100, th=1)
        scope(img, t, 0.6, cy=H * 0.80, amp=190 + k * 60, n=1100, th=1, ch=1)
        spectrum(img, t, 0.4 + k * 0.15, y=H * 0.92, h=150)

        dw = t - T(14, 2)
        if dw > 0:
            m = WORD_A.copy()
            cut = int(m.shape[1] * clamp01(dw / 0.35))
            m[:, cut:] = 0
            blit(img, m, W / 2, CY + 190, 1.0, glow=0.4 + k * 0.25, glow_r=24)
        dc = t - T(15, 2)
        if dc > 0:
            a = clamp01(dc / 0.35)
            rule(img, W / 2 - 300 * out_expo(clamp01(dc / 0.6)),
                 W / 2 + 300 * out_expo(clamp01(dc / 0.6)), CY + 258, a * 0.45)
            m = text_mask('SEOUL · DJ CREW', BRAND, target_w=430, track_em=0.3)
            blit(img, m, W / 2, CY + 310, a * 0.85, glow=0.26, glow_r=14)
        ds = t - T(17, 0)
        if ds > 0:
            a = clamp01(ds / 0.4)
            for j, txt in enumerate(('WHERE THE LIGHTS FADE,', 'THE MUSIC TAKES OVER.')):
                m = text_mask(txt, BRAND, target_w=680, track_em=0.16)
                blit(img, m, W / 2, CY + 420 + j * 60, a * (0.72 + 0.28 * j),
                     glow=0.22, glow_r=14)
        di = t - T(19, 0)
        if di > 0:                                  # 숏폼 UI에 가리지 않게 안전영역 안에
            a = clamp01(di / 0.4)
            m = text_mask('@BLACKOUTCREW_OFFICIAL', BRAND, target_w=520, track_em=0.14)
            blit(img, m, W / 2, CY + 560, a * 0.75, glow=0.2, glow_r=12)
        de = t - T(21, 2)
        if de > 0:
            flash = max(flash, max(0.0, 0.8 - de * 9))
            img *= max(0.0, 1 - clamp01((de - 0.35) / 0.4))
        if sn > 0.55:
            tear(img, t, 0.22 * sn, 13)

    # ── 후처리 ────────────────────────────────────────────
    if cam != 1.0:
        img = zoom(img, cam)
    if sx or sy:
        img = shake(img, sx, sy)
    img = np.clip(img, 0, 1)
    if invw > 0.01:
        img = 1.0 - img                      # 흰 바탕 · 검은 선
    if ab > 0.4:
        img = chroma(img, ab)
    if flash > 0.004:
        img += flash
    img += grain(fi) * (0.02 if invw > 0.5 else 0.03)
    return np.clip(img, 0, 1)


def main():
    if len(sys.argv) == 3:
        a, b = float(sys.argv[1]), float(sys.argv[2])
        prev = os.path.join(OUT, 'prev3')
        os.makedirs(prev, exist_ok=True)
        for fi in range(int(a * FPS), int(b * FPS) + 1):
            cv2.imwrite(os.path.join(prev, f'f{fi:04d}.png'),
                        (frame(fi / FPS, fi)[..., ::-1] * 255).astype(np.uint8))
        print('->', prev)
        return

    raw = os.path.join(OUT, 'raw_open3.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fi in range(NF):
        p.stdin.write((frame(fi / FPS, fi) * 255).astype(np.uint8).tobytes())
        if fi % 60 == 0:
            print(f'  {fi}/{NF}  {fi / FPS:5.1f}s', flush=True)
    p.stdin.close()
    p.wait()

    final = os.path.join(OUT, 'blackout_opening3.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', os.path.join(OUT, 'bgm_open3.wav'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print('done ->', final)


if __name__ == '__main__':
    main()
