"""**멈춘 사진을 움직이게 한다** — 스토리용 15초. 1080×1920 · 30fps · 128BPM.

    out/short/scene_story.mp4

**처음엔 전부 그렸다가 물렀습니다.** `scene_kit.poolscene()` 으로 하늘·도시·
사람·물을 다 그려 봤는데, 그 파일 주석에 이미 적혀 있는 그대로였습니다 —
선으로 그린 실루엣은 장면이 아니라 **도표로 읽힙니다.** 움직이면 더 그렇습니다.

그래서 포스터가 실제로 쓰는 `photoscene()` 쪽으로 갔습니다. 사진 한 장을
깔고 **그 위에서 물과 빛만 움직입니다.**

    물결    수면을 일렁이게 한다. 아래로 갈수록 크게 — 이게 전부다
    조명    파티 조명 세 덩이가 각자 다른 주기로 떠다닌다
    물빛    그물이 흐른다
    튜브    까딱인다
    카메라  15초에 7% 다가간다

**주기를 서로 나누어떨어지지 않게 둡니다**(`_T`). 맞아떨어지면 화면 전체가
한 덩어리로 펄떡여서 화면보호기가 됩니다.

사진은 `pool-cc0.jpg` — **사람이 없는 CC0 사진**입니다. 손님 얼굴이 든 클립은
광고로 크게 돌리기 어렵고, 여기서는 분위기만 있으면 되기 때문입니다.

**안쪽은 절반 크기로 그립니다.** 어차피 번지는 그림이라 키워도 차이가 없고,
글자만 원래 크기에서 얹습니다 — 글자는 키우면 바로 뭉개집니다.

python scene_motion.py
"""
import os
import subprocess
import numpy as np
import cv2
from scene_kit import _add, AQUA, ROSE, BULB
from poster_kit import BRAND, tmask, fit, paint, logo, rule, duotone, POOL, bloom
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
RW, RH = W // 2, H // 2
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM
DUR = NBEAT * BEAT                       # 15.0초

PAPER = np.float32([0.975, 0.985, 0.985])

# 겹마다 다른 주기(초). 서로 나누어떨어지면 전체가 같이 펄떡인다
_T = dict(ripple=4.3, light=9.7, caustic=13.1, bob=6.1)

# 파티 조명 — (x, y, 가로, 세로, 색, 세기, 떠다니는 폭)
LIGHTS = [(0.90, 0.14, 0.52, 0.30, (1.00, 0.22, 0.62), 0.34, 0.060),
          (0.07, 0.78, 0.46, 0.28, (1.00, 0.55, 0.18), 0.20, 0.045),
          (0.46, 0.04, 0.70, 0.15, (0.55, 0.32, 1.00), 0.16, 0.075)]

# 물에 뜬 튜브 — (x, y, 반지름, 색)
TUBES = [(0.12, 0.72, 0.100, AQUA), (0.90, 0.56, 0.072, ROSE),
         (0.70, 0.20, 0.052, BULB)]

# (몇 박에 뜨는가, 글자) — 여덟 박마다 한 줄
BEATS = [(0,  '해 지기 전엔 물에서'),
         (8,  '9시 반부터 솔로파티'),
         (16, '혼자 와도 됩니다')]


def base_photo():
    """사진을 한 번만 읽어 듀오톤으로 눌러 둔다. 매 장면 다시 읽으면 15초에
    몇 분이 더 든다."""
    return duotone(POOL, RW, RH, np.float32([0.008, 0.024, 0.040]),
                   np.float32([0.135, 0.265, 0.325]), contrast=1.32, keep=0.09,
                   focus=0.20, zoom=2.4)


BASE = base_photo()
_YY, _XX = np.mgrid[0:RH, 0:RW].astype(np.float32)
# 아래로 갈수록 크게 일렁인다. 위쪽까지 흔들면 사진이 통째로 녹아 버린다
_AMP = (np.clip((_YY / RH - 0.16) / 0.84, 0, 1) ** 1.5 * (RW * 0.018))


def ripple(img, ph):
    """**수면을 일렁이게 한다.** 이 판이 살아 있어 보이는 건 사실상 이것 하나다.

    두 방향으로 흔든다 — 가로로만 밀면 화면이 좌우로 미끄러지는 것으로 보이고,
    세로가 섞여야 물이 출렁이는 것으로 읽힌다."""
    dx = _AMP * np.sin(_YY * 0.045 + _XX * 0.006 + ph)
    dy = _AMP * 0.42 * np.sin(_XX * 0.030 - ph * 1.3)
    return cv2.remap(img, (_XX + dx).astype(np.float32), (_YY + dy).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def lights(img, t):
    """조명 덩이가 떠다닌다. **한 색이면 수영장이고 두 색이 섞여야 파티다.**"""
    for i, (cx, cy, rx, ry, col, a, sw) in enumerate(LIGHTS):
        u = 2 * np.pi * t / _T['light'] + i * 2.2
        x = RW * (cx + sw * np.sin(u))
        y = RH * (cy + sw * 0.5 * np.cos(u * 0.8))
        # 박에 맞춰 아주 조금 세졌다 약해진다 — 곡이 도는 게 눈에도 보인다
        pulse = 1 + 0.16 * np.sin(2 * np.pi * t / BEAT / 2)
        g = np.exp(-(((_XX - x) / (RW * rx)) ** 2 + ((_YY - y) / (RH * ry)) ** 2))
        _add(img, g, np.float32(col), a * pulse)


def caustics(img, ph):
    """물빛 그물이 흐른다. 4분의 1 크기로 계산해서 키운다 — 어차피 번진다."""
    yq, xq = np.mgrid[0:RH // 2, 0:RW // 2].astype(np.float32)
    x, y = xq * 0.052 + ph * 0.32, yq * 0.052 + ph * 0.17
    f = (np.sin(x * 1.7 + 1.8 * np.sin(y * 0.55)) + np.sin(y * 1.35 + 1.5 * np.sin(x * 0.48))
         + 0.9 * np.sin((x + y) * 1.05))
    k = np.clip(1 - np.abs(np.sin(f * 2.1)) * 8.0, 0, 1) ** 1.1
    k = cv2.resize(cv2.GaussianBlur(k, (0, 0), 0.9), (RW, RH), interpolation=cv2.INTER_LINEAR)
    _add(img, k * np.clip((_YY / RH - 0.20) / 0.80, 0, 1) ** 0.6,
         np.float32([0.60, 0.95, 1.00]), 0.20)


def tubes(img, ph):
    """튜브는 **아주 조금만** 움직인다. 크게 흔들면 떠내려가는 그림이 된다."""
    for i, (cx, cy, r, col) in enumerate(TUBES):
        x = RW * cx + np.sin(ph + i * 2.1) * RW * r * 0.14
        y = RH * cy + np.cos(ph * 0.8 + i * 1.3) * RW * r * 0.10
        d = np.sqrt(((_XX - x) / (RW * r)) ** 2 + ((_YY - y) / (RW * r * 0.36)) ** 2)
        img *= (1 - ((d < 1.0).astype(np.float32) * 0.42)[..., None])
        ring = np.clip(1 - np.abs(d - 1.0) / 0.30, 0, 1) ** 0.8
        _add(img, ring, col, 0.48)
        _add(img, cv2.GaussianBlur(ring, (0, 0), RW * r * 0.26), col, 0.38)


def sparkle(img, i):
    """수면 반짝임. 매 장면 자리를 새로 뽑아야 물이 반짝이는 것으로 보인다 —
    고정하면 화면에 붙은 먼지가 된다."""
    rng = np.random.default_rng(5 + i)
    sp = np.zeros((RH, RW), np.float32)
    for _ in range(60):
        cv2.circle(sp, (int(rng.integers(0, RW)), int(rng.integers(0, RH))),
                   int(rng.uniform(1, 3)), float(rng.uniform(0.4, 1.0)), -1, cv2.LINE_AA)
    _add(img, cv2.GaussianBlur(sp, (0, 0), 1.2), np.float32([0.85, 0.98, 1.00]), 0.34)


def scene(i):
    t = i / FPS
    img = ripple(BASE, 2 * np.pi * t / _T['ripple'])
    lights(img, t)
    caustics(img, 2 * np.pi * t / _T['caustic'])
    tubes(img, 2 * np.pi * t / _T['bob'])
    sparkle(img, i)
    bloom(img, 0.60, RW * 0.028, 0.22)
    # 위아래를 눌러 글자 자리를 만든다 — 여기서 밤 톤이 정해진다
    yv = _YY / RH
    img *= (1 - 0.54 * np.clip((0.26 - yv) / 0.26, 0, 1))[..., None]
    img *= (1 - 0.60 * np.clip((yv - 0.64) / 0.36, 0, 1))[..., None]
    return np.clip(img, 0, 1)


def push(img, t):
    """**아주 천천히 다가간다.** 15초에 7% — 눈에는 안 보이지만 멈춘 그림이
    아니라는 건 느껴진다. 이게 없으면 정지 화면에 효과만 얹은 꼴이다."""
    M = cv2.getRotationMatrix2D((RW / 2, RH * 0.48), 0, 1.0 + 0.07 * (t / DUR))
    return cv2.warpAffine(img, M, (RW, RH), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def overlay(img, b):
    """글자는 **원래 크기에서 얹는다** — 절반에서 그려 키우면 바로 뭉갠다."""
    lg = logo(52)
    paint(img, lg, W / 2 - lg.shape[1] / 2, H * 0.118, color=PAPER, a=0.90)
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.22), W / 2, H * 0.872,
          color=PAPER, a=0.72, anchor='c')

    for at, txt in BEATS:
        if not (at <= b < at + 8):
            continue
        # 여덟 박 안에서 들어오고 나간다. 박에 맞아야 곡과 같이 움직인다
        u = (b - at) / 8.0
        a = float(np.clip(u / 0.10, 0, 1) * np.clip((1 - u) / 0.14, 0, 1))
        y = H * 0.560 - 16 * (1 - np.clip(u / 0.10, 0, 1))
        fs = min(98, fit(txt, KRB, W * 0.84, 0.02))
        paint(img, tmask(txt, KRB, fs, 0.02), W / 2, y, color=PAPER, a=a, anchor='c')

    if b >= 24:                                    # 마무리 판
        k = float(np.clip((b - 24) / 1.2, 0, 1))
        img *= 1 - 0.58 * k
        paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.86, 0.10), 0.10),
              W / 2, H * 0.450, color=PAPER, a=k, anchor='c')
        paint(img, tmask(EV.FORMAT, BRAND, 26, 0.36), W / 2, H * 0.450 + 62,
              color=AQUA, a=k, anchor='c')
        rule(img, H * 0.450 + 106, W * 0.26, W * 0.74, PAPER, 0.26 * k, 2)
        paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 34, 0.02), W / 2,
              H * 0.450 + 152, color=PAPER, a=k * 0.96, anchor='c')
        k2 = float(np.clip((b - 25.6) / 1.0, 0, 1))
        paint(img, tmask('프로필 링크에서 예약', KRB, 46, 0.02), W / 2,
              H * 0.450 + 244, color=ROSE, a=k2, anchor='c')
    return img


def frame(i):
    img = cv2.resize(push(scene(i), i / FPS), (W, H), interpolation=cv2.INTER_CUBIC)
    return overlay(img, (i / FPS) / BEAT)


def render():
    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    nf = int(round(DUR * FPS))
    raw = os.path.join(OUT, 'raw_scene.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rng = np.random.default_rng(7)
    for i in range(nf):
        img = frame(i)
        img += rng.standard_normal((H, W, 1)).astype(np.float32) * 0.006
        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
        if i % 90 == 0:
            print(f'  {i}/{nf}', flush=True)
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, 'scene_story.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {DUR:.2f}s')


if __name__ == '__main__':
    render()
