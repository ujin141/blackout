"""**릴스 세 편 + 이어지는 커버 세 장.** 1080×1920 · 30fps.

    out/reel3/reel_1.mp4 ~ reel_3.mp4
    out/reel3/cover_1.png ~ cover_3.png

## 왜 새로 짰나

기존 판(`short.py`)은 **컷 길이가 전부 같았다.** 두 박씩 열두 번.
박에는 맞는데 12초쯤에서 사람이 넘긴다 — 리듬이 예측되기 때문이다.

여기서는 컷 길이를 **편마다 다른 곡선**으로 준다.

    1편  가속    4·4·2·2·2·1·1·1·1·1·2  뒤로 갈수록 빨라진다
    2편  시간    4·4·4·2·2·2·1·1·2      해 질 녘은 길게, 밤은 짧게
    3편  대비    8·1·1·1·1·8·2·2        길게 보다가 확 몰아친다

같은 곡, 같은 소재인데 **셋이 완전히 다르게 읽힌다.**

## 컷 하나가 가진 것

    clip   숏폼/ 폴더의 몇 번째 파일인가 (파일명이 바뀌어도 도는 이유)
    at     시작 초
    beats  몇 박짜리 컷인가
    ox     가로 크롭 위치 0~1. 사람이 몰린 쪽을 잡는다
    z0,z1  컷 안에서 밀어 넣는 배율. **정지 크롭은 손 흔들림만 보인다**
    speed  1.0 이 원속. 0.6 이면 슬로우, 1.6 이면 빠르게

**속도를 바꾸는 게 이 판의 새 무기다.** 드롭 직전 한 컷을 슬로우로
끌었다가 드롭에서 원속으로 돌아오면 같은 소재가 다르게 보인다.

## 커버 셋

한 장의 넓은 그림(3240×1350)을 셋으로 잘라 각각 1080×1920 커버 안
`top=285` 에 앉힌다. **프로필 격자에서 세 칸이 한 장으로 이어진다.**
올리는 순서는 3 → 2 → 1 (격자는 최신이 왼쪽 위).

python reel3.py            세 편 다
python reel3.py 2          2편만
python reel3.py cover      커버만
"""
import os
import glob
import subprocess
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'reel3')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
NBEAT = 32                                # 곡 골격이 8마디 = 32박
TAIL = 5                                  # 끝 다섯 박은 마무리 판

# **편마다 곡이 다르다.** 셋을 연달아 보면 같은 곡이 세 번 나오는 게
# 그림보다 먼저 지겹다 — 컷을 아무리 다르게 짜도 귀가 먼저 알아챈다.
# BPM 이 다르면 한 박의 길이도 달라지고, 그래서 **컷 길이와 영상 길이가
# 곡을 따라간다.** 박 수(32)만 고정이다.
#   heavy 142  하프타임. 제일 센 판 — 가속 컷에 붙인다
#   deep  124  딥하우스. 제일 느리다 — 시간이 흐르는 판에
#   dark  130  다크테크노. 킥 럼블 — 길게 끌다 몰아치는 판에
def beat_of(style):
    import audio_motion
    return 60.0 / audio_motion.STYLES[style][0]

PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
INK = np.float32([0.03, 0.04, 0.05])

# **파일명이 아니라 순번으로 잡는다.** 카톡에서 받은 파일은 이름이 매번
# 바뀌는데, 예전 판은 이름을 박아 둬서 소재를 갈아 끼울 때마다 통째로 깨졌다.
CLIPS = sorted(glob.glob(os.path.join(SRC, '*.mp4')))

# 소재가 뭐가 찍혀 있는지. 컷을 짤 때 이걸 보고 고른다
#   0 물가에 앉은 사람들 (저녁)      5 해 질 녘 전경 — 하늘과 도시
#   1 밤 물속, 보라 네온              6 튜브 클로즈업, 바닥 네온
#   2 밤 물속, 붐빔                   7 노란 네온 계단 + 튜브
#   3 밤 물속 + 핑크 라이트바          8 위에서 본 밤 물속
#   4 물가 뒤통수, 붐빔


def _cut(clip, at, beats, ox=0.5, z0=1.0, z1=1.06, speed=1.0):
    return dict(clip=clip, at=at, beats=beats, ox=ox, z0=z0, z1=z1, speed=speed)


# ── 세 편 ────────────────────────────────────────────────
# (제목, 곡, 컷 목록, 자막)
# **자막은 편마다 완전히 다르다.** 셋을 연달아 본 사람이 같은 영상 세 번
# 본 것으로 느끼면 세 편을 만든 의미가 없다.
REELS = [
    dict(
        name='reel_1', style='heavy',
        # 가속 — 뒤로 갈수록 컷이 짧아진다
        # 5·5·4·3·2·2·1·1·1·1·3·4 = 32박
        cuts=[_cut(5, 0.5, 5, 0.50, 1.00, 1.10),
              _cut(7, 0.6, 5, 0.46, 1.04, 1.00, speed=0.72),   # 슬로우로 끌고
              _cut(6, 2.4, 4, 0.50, 1.00, 1.10),
              _cut(1, 1.2, 3, 0.44, 1.02, 1.10),
              _cut(2, 0.8, 2, 0.52, 1.00, 1.08),
              _cut(8, 1.0, 2, 0.50, 1.00, 1.08),
              _cut(3, 6.4, 1, 0.46), _cut(4, 1.2, 1, 0.54),
              _cut(1, 4.6, 1, 0.50), _cut(2, 3.2, 1, 0.44),
              _cut(6, 0.5, 3, 0.50, 1.00, 1.12),
              _cut(3, 6.6, 4, 0.50, 1.02, 1.12)],
        caps=[(0, 4, '여기 서울이에요'),
              (4, 8, '양재 루프탑'),
              (8, 12, '8월 29일 토요일'),
              (12, 16, '해 지기 전엔 물에서'),
              (16, 21, '9시 반부터 솔로파티'),
              (21, 27, '혼자 와도 됩니다')]),
    dict(
        name='reel_2', style='deep',
        # 시간 — 해 질 녘은 길게, 밤이 되면 짧게
        # 5·5·5·3·3·3·2·2·2·2 = 32박
        cuts=[_cut(5, 2.4, 5, 0.44, 1.00, 1.08),
              _cut(0, 0.8, 5, 0.50, 1.02, 1.10),
              _cut(7, 3.0, 5, 0.52, 1.00, 1.06),
              _cut(6, 3.8, 3, 0.48, 1.04, 1.00, speed=0.66),
              _cut(1, 5.6, 3, 0.50, 1.00, 1.08),
              _cut(3, 2.2, 3, 0.46, 1.02, 1.10),
              _cut(8, 4.2, 2, 0.50, 1.00, 1.08),
              _cut(2, 4.0, 2, 0.54, 1.00, 1.08),
              _cut(4, 3.2, 2, 0.46, 1.00, 1.10),
              _cut(1, 2.4, 2, 0.50, 1.02, 1.12)],
        caps=[(0, 5, '해가 지기 전엔'),
              (5, 10, '물에서 놉니다'),
              (10, 15, '어두워지면'),
              (15, 20, '판이 바뀝니다'),
              (20, 27, '9시 반부터 솔로파티')]),
    dict(
        name='reel_3', style='dark',
        # 대비 — 길게 보다가 확 몰아친다
        # 8·1·1·1·1·8·3·3·3·3 = 32박
        cuts=[_cut(3, 0.4, 8, 0.48, 1.00, 1.14),               # 롱테이크
              _cut(2, 1.6, 1, 0.50), _cut(8, 2.4, 1, 0.46),
              _cut(4, 0.6, 1, 0.54), _cut(1, 3.4, 1, 0.50),
              _cut(6, 1.2, 8, 0.50, 1.00, 1.12),               # 다시 길게
              _cut(7, 4.4, 3, 0.48, 1.00, 1.08),
              _cut(1, 6.4, 3, 0.50, 1.00, 1.08),
              _cut(2, 2.0, 3, 0.44, 1.00, 1.10),
              _cut(8, 4.6, 3, 0.52, 1.00, 1.10)],
        caps=[(0, 8, '친구 없어서 못 갔죠'),
              (8, 12, '여기선 상관없어요'),
              (12, 20, '다 혼자 온 사람들이니까'),
              (20, 27, '8/29 토요일 · 양재 루프탑')]),
]

# 커버 — 한 장을 셋으로 자른다. (클립, 초, 가로 위치)
# 3.0초는 왼쪽 칸이 나무와 하늘뿐이었다 — 셋으로 잘랐을 때 **세 칸에 다
# 사람이 있는 순간**을 골라야 한다. 4.6초는 물이 화면을 가로지른다.
COVER_SRC = (5, 4.6, 0.50)
COVER_Y = 0.55                            # 세로 크롭. 0.42는 하늘이 반이었다
# 16:9 원본을 3240 폭에 그냥 맞추면 가로가 꽉 차서 **좌우를 고를 수가 없다** —
# 왼쪽 나무·난간이 그대로 1번 칸이 됐다. 더 당겨서(zoom) 고를 폭을 만든다.
COVER_ZOOM = 1.30
COVER_OX = 0.72                           # 당긴 뒤 어디를 볼지. 오른쪽 = 파티 쪽
# **칸마다 완성된 한 줄을 준다.** 한 문장을 셋으로 쪼개면 격자에서는
# 멋있는데, 릴스 탭에서 낱장으로 뜨면 '되는' 한 단어라 아무 말도 안 한다.
# 사진은 셋을 관통하고 글은 각자 선다 — 둘 다 얻는 방법이다.
COVER_LINES = ['혼자 와도 되는 풀파티',
               '9시 반부터 솔로파티',
               '8.29 토요일 양재 루프탑']
_CAPS = {}


def cap(i):
    if i not in _CAPS:
        c = cv2.VideoCapture(CLIPS[i])
        if not c.isOpened():
            raise SystemExit(f'못 엶: {CLIPS[i]}')
        _CAPS[i] = c
    return _CAPS[i]


def crop916(fr, ox, z):
    """가로 16:9 를 세로 9:16 으로. 가운데를 무조건 쓰지 않는다 —
    컷마다 사람이 몰린 쪽이 다르다."""
    h, w = fr.shape[:2]
    tw, th = h * W / H / z, h / z
    cx = (w - h * W / H) * ox + h * W / H / 2
    x0 = int(np.clip(cx - tw / 2, 0, w - tw))
    y0 = int(np.clip(h / 2 - th / 2, 0, h - th))
    return cv2.resize(fr[y0:y0 + int(th), x0:x0 + int(tw)], (W, H),
                      interpolation=cv2.INTER_AREA)


def grade(a):
    """물·조명이 살아나게. 원본은 휴대폰 촬영이라 밋밋하다."""
    a = np.clip((a - 0.5) * 1.16 + 0.5, 0, 1)
    g = a @ np.float32([0.299, 0.587, 0.114])
    a = np.clip(g[..., None] + (a - g[..., None]) * 1.26, 0, 1)
    a *= np.float32([0.99, 1.005, 1.02])
    yy = np.linspace(-1, 1, H)[:, None, None]
    return np.clip(a * (1 - 0.18 * yy ** 2), 0, 1)


def band(img, cy, half, amt):
    """자막 자리는 배경을 눌러 만든다. 외곽선을 두르면 지저분해진다."""
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= 1 - amt * np.exp(-((yy - cy) / half) ** 2)


def plan(cuts, BEAT):
    """컷 목록 → 프레임별 (클립, 원본 프레임번호, ox, 배율).

    **속도(speed)가 여기서 들어간다.** 컷 안에서 원본을 얼마나 빨리
    훑을지만 정하면 되고, 컷 길이는 박이 정한다."""
    out = []
    for c in cuts:
        n = int(round(c['beats'] * BEAT * FPS))
        cp = cap(c['clip'])
        fps = cp.get(cv2.CAP_PROP_FPS) or 30.0
        total = cp.get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
        need = c['beats'] * BEAT * c['speed']
        at = c['at']
        # **컷이 클립 끝을 넘으면 검은 프레임이 나온다.** 안으로 민다
        if at + need > total - 0.05:
            at = max(0.0, total - need - 0.05)
        for i in range(n):
            u = i / max(n - 1, 1)
            src_t = at + (i / FPS) * c['speed']
            z = c['z0'] + (c['z1'] - c['z0']) * u
            out.append((c['clip'], int(src_t * fps), c['ox'], z))
    return out


_LAST = {}


def grab(clip, fno):
    c = cap(clip)
    if _LAST.get(clip) != fno - 1:
        c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
    ok, fr = c.read()
    if not ok:
        c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
    _LAST[clip] = fno
    if not ok:
        return np.zeros((1080, 1920, 3), np.uint8)
    return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)


def render(spec):
    cuts, caps = spec['cuts'], spec['caps']
    BEAT = beat_of(spec['style'])
    nb = sum(c['beats'] for c in cuts)
    assert nb == NBEAT, f"{spec['name']}: 컷이 {nb}박인데 곡은 {NBEAT}박이다 — 뒤가 잘린다"

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', f"bgm_{spec['style']}.wav")
    if not os.path.exists(wav):
        audio_motion.write(spec['style'])

    fr_plan = plan(cuts, BEAT)
    nf = int(round(NBEAT * BEAT * FPS))
    fr_plan = fr_plan[:nf] + [fr_plan[-1]] * max(0, nf - len(fr_plan))
    # 컷이 바뀌는 프레임 번호 — 여기서 한 번 번쩍인다
    edges, acc = set(), 0
    for c in cuts:
        acc += int(round(c['beats'] * BEAT * FPS))
        edges.add(acc)

    raw = os.path.join(OUT, f"raw_{spec['name']}.mp4")
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    lg = logo(42)
    for i, (clip, fno, ox, z) in enumerate(fr_plan):
        img = grade(crop916(grab(clip, fno), ox, z).astype(np.float32) / 255)
        b = (i / FPS) / BEAT

        # **화면 아래를 통째로 떨어뜨린다.** 자막 자리에만 띠를 두르면
        # 밝은 물 위에서 흰 글자가 그대로 묻힌다 — 실제로 '양재 루프탑' 이
        # 안 읽혔다. 아래를 다 눌러 두면 색보정으로 읽히고 자막도 산다
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        img *= 1 - 0.50 * np.clip((yy - H * 0.46) / (H * 0.22), 0, 1) ** 1.15

        # 서명 — 처음부터 끝까지. 릴스는 팔로워 밖으로 나간다
        paint(img, lg, W * 0.068, H * 0.056, color=PAPER, a=0.82)

        if b < NBEAT - TAIL:
            for b0, b1, txt in caps:
                if b0 <= b < b1 and txt:
                    k = float(np.clip((b - b0) / 0.18, 0, 1))
                    cy = H * 0.615
                    band(img, cy, H * 0.062, 0.52 * k)
                    fs = min(66, fit(txt, KRB, W * 0.86, 0.02))
                    paint(img, tmask(txt, KRB, fs, 0.02), W / 2, cy,
                          color=PAPER, a=k, anchor='c')
        else:
            k = float(np.clip((b - (NBEAT - TAIL)) / 0.45, 0, 1))
            img *= 1 - 0.88 * k
            cy = H * 0.36
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.84, 0.10), 0.10),
                  W / 2, cy, color=PAPER, a=k, anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 27, 0.36), W / 2, cy + H * 0.040,
                  color=AQUA, a=k, anchor='c')
            rule(img, cy + H * 0.070, W * 0.24, W * 0.76, PAPER, 0.26 * k, 2)
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 37, 0.02), W / 2,
                  cy + H * 0.100, color=PAPER, a=k * 0.96, anchor='c')
            paint(img, tmask(EV.PRICE_LINE, KR, 31, 0.02), W / 2, cy + H * 0.140,
                  color=PAPER, a=k * 0.76, anchor='c')
            k2 = float(np.clip((b - (NBEAT - TAIL) - 0.9) / 0.45, 0, 1))
            if k2 > 0.004:
                paint(img, tmask('프로필 링크에서 예약', KRB, 50, 0.02), W / 2,
                      cy + H * 0.204, color=CORAL, a=k2, anchor='c')
                paint(img, tmask(EV.HANDLE, BRAND, 21, 0.22), W / 2, cy + H * 0.246,
                      color=PAPER, a=k2 * 0.72, anchor='c')

        # **컷이 바뀐 걸 눈이 알아채게 두 프레임만 번쩍인다.**
        # 이게 없으면 비슷한 그림끼리 이어질 때 컷이 아니라 흔들림으로 읽힌다
        d = min((i - e for e in edges if 0 <= i - e < 2), default=None)
        if d is not None and i < nf - TAIL * BEAT * FPS:
            img = img * (1 - 0.26 * (1 - d / 2)) + PAPER * (0.26 * (1 - d / 2))

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f"{spec['name']}.mp4")
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f"{final}  {NBEAT * BEAT:.2f}s  {spec['style']} {60 / BEAT:.0f}BPM  "
          f"컷 {len(cuts)}개 ({'·'.join(str(c['beats']) for c in cuts)}박)")


def covers():
    """**한 장을 셋으로 자른다.** 격자에서 세 칸이 이어져 한 그림이 된다.

    타일은 1080×1350 이고 커버 안 `top=285` 에 앉는다 — 이 자리가
    어긋나면 줄이 깨진다."""
    TH, TOP = 1350, 285
    clip, at, ox = COVER_SRC
    c = cap(clip)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    if not ok:
        raise SystemExit('커버 프레임을 못 읽었습니다')
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)

    # 3240×1350 — 가로 셋을 이어 붙인 넓은 그림
    WW = 1080 * 3
    h, w = fr.shape[:2]
    s = max(WW / w, TH / h) * COVER_ZOOM
    big = cv2.resize(fr, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_AREA)
    x0 = int(np.clip((big.shape[1] - WW) * COVER_OX, 0, big.shape[1] - WW))
    y0 = int(np.clip(big.shape[0] * COVER_Y - TH / 2, 0, big.shape[0] - TH))
    big = big[y0:y0 + TH, x0:x0 + WW].astype(np.float32) / 255
    big = np.clip((big - 0.5) * 1.14 + 0.5, 0, 1)
    g = big @ np.float32([0.299, 0.587, 0.114])
    big = np.clip(g[..., None] + (big - g[..., None]) * 1.22, 0, 1)

    # 아래를 눌러 글자 자리를 만든다. 세 칸에 똑같이 걸려야 이어진다
    yy = np.arange(TH, dtype=np.float32)[:, None, None]
    big *= 1 - 0.70 * np.clip((yy - TH * 0.44) / (TH * 0.30), 0, 1) ** 1.1
    big *= 1 - 0.40 * np.clip((TH * 0.16 - yy) / (TH * 0.16), 0, 1)

    # **제목 자리를 눌러야 한다.** 뒤가 노을이라 흰 글자가 그대로 묻혔다
    big *= 1 - 0.46 * np.exp(-((yy - TH * 0.20) / (TH * 0.10)) ** 2)

    # 글자는 칸마다 선다. 같은 기준선이라 이어 봐도 한 줄로 읽힌다
    for i, line in enumerate(COVER_LINES):
        fs = min(78, fit(line, KRB, 1080 * 0.84, 0.02))
        paint(big, tmask(line, KRB, fs, 0.02), 1080 * i + 540, TH * 0.635,
              color=PAPER, anchor='c')
        # 칸마다 밑줄 한 개 — 낱장으로 봐도 글이 얹힌 게 아니라 판으로 읽힌다
        rule(big, TH * 0.695, 1080 * i + 540 - 1080 * 0.30,
             1080 * i + 540 + 1080 * 0.30, PAPER, 0.24, 2)

    # **행사 이름은 가운데 칸에만 크게.** 셋에 다 크게 박으면 이어 봤을 때
    # 같은 글자가 세 번 나와 한 장으로 안 읽힌다.
    paint(big, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, WW * 0.30, 0.14), 0.14),
          WW / 2, TH * 0.212, color=PAPER, anchor='c')
    # 대신 **마크 + BLACKOUT 글자를 칸마다** 둔다 — 마크만 있으면
    # 우리를 모르는 사람한테는 아무 표시도 아니다. 이름이 같이 있어야 한다
    lg = logo(52)
    wm = tmask('BLACKOUT  CREW', BRAND, 28, 0.30)
    gap = 26
    tw = lg.shape[1] + gap + wm.shape[1]
    for i in range(3):
        x0 = 1080 * i + 540 - tw / 2
        paint(big, lg, x0, TH * 0.130, color=PAPER, a=0.96)
        paint(big, wm, x0 + lg.shape[1] + gap, TH * 0.130, color=PAPER, a=0.92)
    # 아래 두 줄도 칸마다 따로. 가운데 한 번만 적으면 1·3번 칸이 허전하다
    for i in range(3):
        cx = 1080 * i + 540
        paint(big, tmask(EV.LEFT_LINE + '  ·  사전예약만', KR, 34, 0.02), cx,
              TH * 0.775, color=PAPER, a=0.88, anchor='c')
        paint(big, tmask(EV.HANDLE, BRAND, 22, 0.22), cx, TH * 0.845,
              color=PAPER, a=0.60, anchor='c')

    for i in range(3):
        tile = big[:, 1080 * i:1080 * (i + 1)]
        cv_ = np.zeros((H, W, 3), np.float32)
        cv_[TOP:TOP + TH] = tile
        # 잘리는 위아래는 타일 끝 줄을 흘려 채운다 — 재생 화면에서 안 뜬다
        for k in range(TOP):
            f = (1 - k / TOP) ** 1.5
            cv_[TOP - 1 - k] = tile[0] * f
            cv_[TOP + TH + k] = tile[-1] * f
        p = os.path.join(OUT, f'cover_{i + 1}.png')
        Image.fromarray((np.clip(cv_, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)
    print('격자에서 이어지려면 3 → 2 → 1 순서로 올립니다')


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if not CLIPS:
        raise SystemExit(f'{SRC} 에 mp4 가 없습니다')
    want = [a for a in args if a.isdigit()]
    if 'cover' in args or not args:
        covers()
    for i, spec in enumerate(REELS, 1):
        if args and 'cover' in args and not want:
            break
        if want and str(i) not in want:
            continue
        render(spec)
    for c in _CAPS.values():
        c.release()
