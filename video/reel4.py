"""**릴스 세 편 — 마감 압박판.** 1080×1920 · 30fps.

    out/reel4/reel_1.mp4 ~ reel_3.mp4
    out/reel4/cover_1.png ~ cover_3.png

## reel3 과 뭐가 다른가

reel3 은 "이 파티가 뭔지" 를 알리는 판이었다. 지금은 D-10 에 21자리다 —
**같은 말을 또 하면 이미 본 사람은 그냥 넘긴다.** 이번 판이 파는 건
정보가 아니라 **남은 자리**다.

    보이는 것    reel3                    reel4
    화면         전면 영상                위아래 검은 띠(레터박스)
    자막         가운데 정렬               왼쪽 정렬 + 세로 막대
    항상 뜨는 것  없음                     D-day 배지 · 21/80 · 진행 막대
    컷 전환      흰 섬광                  검은 프레임 두 장(하드컷)
    끝           글자 CTA                 버튼 모양 박스 + 화살표

**HUD 를 계속 띄우는 게 이 판의 핵심이다.** 릴스는 어느 초에 멈춰도
"몇 자리 남았고 며칠 남았는지" 가 보여야 한다 — 마감이 안 보이면
"나중에 봐야지" 로 끝난다.

## 곡

**기존 곡을 안 쓴다.** `audio_motion` 5개와 `audio_poster` 6개는 뼈대가
다 같아서 — 킥 넷에 엇박 햇, 그 위에 패드나 스탭 — BPM 만 바꾼 걸로
들린다. 실제로 "너무 겹친다" 는 말이 나왔다.

`audio_reel4.py` 에서 **주인공 악기를 바꿔서** 새로 만든다.

    pluck  117  플럭 아르페지오가 주선율. 킥은 뒤로       — 숫자 훅에
    perc   108  선율이 아예 없다. 톰·콩가·림만            — 질문 던지는 판에
    bass   133  굵은 베이스 리프. 위쪽은 비운다            — 마감 압박에

셋 다 32박이다. 박 수는 곡에서 읽어 오니 곡을 바꾸면 컷도 같이 맞춰야 한다.

python reel4.py          세 편 + 커버
python reel4.py 2        2편만
python reel4.py cover    커버만
"""
import os
import glob
import datetime
import subprocess
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, logo, rule, box
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'reel4')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
TAIL = 6                                  # 끝 여섯 박은 CTA 판

PAPER = np.float32([0.99, 1.00, 1.00])
CORAL = np.float32([1.00, 0.42, 0.36])
AQUA = np.float32([0.34, 0.94, 1.00])
INK = np.float32([0.02, 0.02, 0.03])

# 레터박스 — 위아래를 검게 덮는다. **이게 reel3 과 첫눈에 갈리는 지점이다**
TOP_BAR = 0.150                           # 인스타 UI 가 덮는 위쪽
BOT_BAR = 0.255                           # 자막과 CTA 가 앉는 아래쪽

CLIPS = sorted(glob.glob(os.path.join(SRC, '*.mp4')))
DDAY = (datetime.date(2026, 8, 29) - datetime.date.today()).days


def bars_of(style):
    import audio_reel4
    bpm, bars = audio_reel4.STYLES[style]
    return 60.0 / bpm, bars * 4


def _cut(clip, at, beats, ox=0.5, z0=1.0, z1=1.06, speed=1.0):
    return dict(clip=clip, at=at, beats=beats, ox=ox, z0=z0, z1=z1, speed=speed)


# 소재 메모는 reel3 과 같다
#   0 물가에 앉은 사람들(저녁)  1 밤 물속 보라  2 밤 물속 붐빔  3 밤 물속+핑크바
#   4 물가 뒤통수  5 해 질 녘 전경  6 튜브 클로즈업  7 노란 계단  8 위에서 본 밤 물속
REELS = [
    dict(
        name='reel_1', style='pluck',
        # 숫자로 친다. 컷은 짧게 균일 — 숫자가 주인공이라 그림이 튀면 안 된다
        # 4×8 = 32박
        cuts=[_cut(2, 0.8, 4, 0.50, 1.00, 1.10), _cut(8, 1.2, 4, 0.46, 1.02, 1.10),
              _cut(1, 2.0, 4, 0.52, 1.00, 1.08), _cut(6, 2.0, 4, 0.50, 1.00, 1.12),
              _cut(3, 1.6, 4, 0.46, 1.02, 1.10), _cut(4, 2.4, 4, 0.54, 1.00, 1.08),
              _cut(7, 3.6, 4, 0.48, 1.00, 1.10), _cut(5, 3.0, 4, 0.50, 1.02, 1.12)],
        big='21',                          # 화면 가운데 크게 박히는 숫자
        bigsub='자리 남았습니다',
        bigat=(0, 8),
        caps=[(8, 14, '정원 80명입니다'),
              (14, 20, '8월 29일 토요일 · 양재 루프탑'),
              (20, 26, '사전예약만 받습니다')]),
    dict(
        name='reel_2', style='perc',
        # 질문 — 느린 곡이라 컷도 길게. 5·5·5·5·4·4·4 = 32박
        cuts=[_cut(0, 1.0, 5, 0.50, 1.00, 1.08), _cut(4, 1.0, 5, 0.46, 1.02, 1.10),
              _cut(7, 1.2, 5, 0.50, 1.00, 1.08), _cut(1, 4.0, 5, 0.48, 1.02, 1.10),
              _cut(3, 4.0, 4, 0.50, 1.00, 1.10), _cut(2, 2.6, 4, 0.52, 1.00, 1.08),
              _cut(8, 3.0, 4, 0.48, 1.00, 1.12)],
        caps=[(0, 6, '혼자 가면 뻘쭘하죠?'),
              (6, 12, '그래서 시간을 따로 뺐습니다'),
              (12, 18, '9시 반부터 90분'),
              (18, 26, '그 시간엔 다 혼자 온 사람들입니다')]),
    dict(
        name='reel_3', style='bass',
        # 마감 — 뒤로 갈수록 짧아진다. 6·5·5·4·4·3·3·2 = 32박
        cuts=[_cut(5, 1.2, 6, 0.44, 1.00, 1.10), _cut(6, 0.6, 5, 0.50, 1.00, 1.12),
              _cut(1, 0.6, 5, 0.50, 1.02, 1.10), _cut(2, 1.4, 4, 0.46, 1.00, 1.10),
              _cut(8, 2.0, 4, 0.52, 1.00, 1.08), _cut(3, 3.0, 3, 0.48, 1.02, 1.12),
              _cut(4, 0.8, 3, 0.50, 1.00, 1.10), _cut(7, 2.2, 2, 0.46, 1.00, 1.12)],
        caps=[(0, 6, '2차는 8월 24일에 닫습니다'),
              (6, 12, '남은 건 21자리'),
              (12, 19, '현장에서는 못 삽니다'),
              (19, 26, '사전예약 안 하면 못 들어옵니다')]),
]

# 1.4초는 커튼과 소파뿐이라 파티로 안 읽혔다. **커버는 물이 보여야 한다** —
# 7번(노란 네온 계단 + 튜브)이 세 칸에 걸쳐 물을 가로지른다
COVER_SRC = (7, 2.0, 0.50)
COVER_LINES = ['21자리 남았습니다', '2차 마감 8월 24일', '사전예약만 받습니다']
_CAPS, _LAST = {}, {}


def cap(i):
    if i not in _CAPS:
        c = cv2.VideoCapture(CLIPS[i])
        if not c.isOpened():
            raise SystemExit(f'못 엶: {CLIPS[i]}')
        _CAPS[i] = c
    return _CAPS[i]


def crop916(fr, ox, z):
    h, w = fr.shape[:2]
    tw, th = h * W / H / z, h / z
    cx = (w - h * W / H) * ox + h * W / H / 2
    x0 = int(np.clip(cx - tw / 2, 0, w - tw))
    y0 = int(np.clip(h / 2 - th / 2, 0, h - th))
    return cv2.resize(fr[y0:y0 + int(th), x0:x0 + int(tw)], (W, H),
                      interpolation=cv2.INTER_AREA)


def grade(a):
    """reel3 보다 **한 단 더 차갑고 세게** 간다. 마감 압박판이라 톤도 조인다."""
    a = np.clip((a - 0.5) * 1.22 + 0.5, 0, 1)
    g = a @ np.float32([0.299, 0.587, 0.114])
    a = np.clip(g[..., None] + (a - g[..., None]) * 1.18, 0, 1)
    a *= np.float32([0.97, 1.00, 1.05])
    return np.clip(a, 0, 1)


def letterbox(img):
    """위아래를 검게. **자막을 영상 위에 얹지 않는다** — 띠 안에 앉히면
    글자가 언제나 같은 밝기 위에 있어서 어떤 컷에서도 읽힌다."""
    t, b = int(H * TOP_BAR), int(H * (1 - BOT_BAR))
    img[:t] = INK
    img[b:] = INK
    # 띠 안쪽 가장자리에 실선 한 줄 — 덮은 게 아니라 판으로 읽힌다
    img[t:t + 2] = PAPER * 0.22
    img[b - 2:b] = PAPER * 0.22
    return t, b


def hud(img, t):
    """**어느 초에 멈춰도 마감이 보여야 한다.** D-day 와 남은 자리를
    위 띠 안에 계속 띄운다 — 이게 이 판의 CTA 절반이다."""
    y = t * 0.56
    d = f'D-{DDAY}' if DDAY > 0 else 'TODAY'
    paint(img, tmask(d, BRAND, 30, 0.16), W * 0.075, y, color=CORAL)
    left = f'{EV.OPEN_LEFT} / {EV.CAP}'
    paint(img, tmask(left, BRAND, 30, 0.16), W * 0.925, y, color=PAPER, anchor='r')
    # 진행 막대 — 숫자만 적으면 안 와닿는다
    x0, x1, by = W * 0.075, W * 0.925, y + 26
    rule(img, by, x0, x1, PAPER, 0.20, 3)
    rule(img, by, x0, x0 + (x1 - x0) * (EV.DONE / EV.CAP), CORAL, 0.95, 3)


def caption(img, b, txt, b0, bot):
    """왼쪽 정렬 + 세로 막대. **가운데 정렬은 reel3 이 썼다** —
    같은 자리에 같은 모양이면 새 판으로 안 읽힌다."""
    k = float(np.clip((b - b0) / 0.22, 0, 1))
    x = W * 0.085
    cy = bot + (H - bot) * 0.36
    fs = min(62, fit(txt, KRB, W * 0.80, 0.02))
    m = tmask(txt, KRB, fs, 0.02)
    box(img, x - 26, cy - m.shape[0] * 0.72, x - 18, cy + m.shape[0] * 0.72, CORAL, k)
    paint(img, m, x, cy, color=PAPER, a=k)


def render(spec):
    BEAT, NBEAT = bars_of(spec['style'])
    nb = sum(c['beats'] for c in spec['cuts'])
    assert nb == NBEAT, f"{spec['name']}: 컷 {nb}박인데 곡은 {NBEAT}박이다 — 뒤가 잘린다"

    import audio_reel4
    wav = os.path.join(OUT, f"bgm_{spec['style']}.wav")
    if not os.path.exists(wav):
        audio_reel4.write(spec['style'])

    plan, edges, acc = [], set(), 0
    for c in spec['cuts']:
        n = int(round(c['beats'] * BEAT * FPS))
        cp = cap(c['clip'])
        fps = cp.get(cv2.CAP_PROP_FPS) or 30.0
        total = cp.get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
        need = c['beats'] * BEAT * c['speed']
        at = min(c['at'], max(0.0, total - need - 0.05))
        for i in range(n):
            u = i / max(n - 1, 1)
            plan.append((c['clip'], int((at + i / FPS * c['speed']) * fps), c['ox'],
                         c['z0'] + (c['z1'] - c['z0']) * u))
        acc += n
        edges.add(acc)

    nf = int(round(NBEAT * BEAT * FPS))
    plan = plan[:nf] + [plan[-1]] * max(0, nf - len(plan))

    raw = os.path.join(OUT, f"raw_{spec['name']}.mp4")
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    lg = logo(34)
    for i, (clip, fno, ox, z) in enumerate(plan):
        c = cap(clip)
        if _LAST.get(clip) != fno - 1:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
        if not ok:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno)); ok, fr = c.read()
        _LAST[clip] = fno
        fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((1080, 1920, 3), np.uint8)
        img = grade(crop916(fr, ox, z).astype(np.float32) / 255)
        b = (i / FPS) / BEAT
        t, bot = letterbox(img)
        hud(img, t)
        paint(img, lg, W * 0.075, bot + (H - bot) * 0.80, color=PAPER, a=0.60)
        paint(img, tmask(EV.HANDLE, BRAND, 17, 0.20), W * 0.075 + lg.shape[1] + 14,
              bot + (H - bot) * 0.80, color=PAPER, a=0.52)

        if b < NBEAT - TAIL:
            big = spec.get('big')
            if big and spec['bigat'][0] <= b < spec['bigat'][1]:
                # **숫자를 화면 가운데 크게.** 글자로 적으면 안 박힌다
                k = float(np.clip((b - spec['bigat'][0]) / 0.3, 0, 1))
                m = tmask(big, BRAND, 300, 0.02)
                cy = H * 0.40
                # **숫자 뒤를 눌러 준다.** 흰 숫자를 밝은 물 위에 그냥 얹으니
                # 반이 묻혔다 — 띠가 아니라 부드러운 그늘로 떨어뜨린다
                yy = np.arange(H, dtype=np.float32)[:, None, None]
                img *= 1 - 0.55 * k * np.exp(-((yy - cy) / (m.shape[0] * 0.95)) ** 2)
                paint(img, m, W / 2, cy, color=PAPER, a=k, anchor='c')
                # 아래 줄은 숫자 높이를 재서 내린다. 상수로 두면 겹친다
                paint(img, tmask(spec['bigsub'], KRB, 62, 0.02), W / 2,
                      cy + m.shape[0] * 0.5 + 66, color=PAPER, a=k, anchor='c')
            for b0, b1, txt in spec['caps']:
                if b0 <= b < b1:
                    caption(img, b, txt, b0, bot)
        else:
            # ── CTA 판 — 버튼처럼 생긴 박스 ──────────────────
            k = float(np.clip((b - (NBEAT - TAIL)) / 0.4, 0, 1))
            img *= 1 - 0.90 * k
            cy = H * 0.34
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.82, 0.10), 0.10),
                  W / 2, cy, color=PAPER, a=k, anchor='c')
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 36, 0.02), W / 2,
                  cy + H * 0.048, color=PAPER, a=k * 0.9, anchor='c')
            paint(img, tmask(f'{EV.OPEN_LEFT}자리 남았습니다', KRB, 54, 0.02), W / 2,
                  cy + H * 0.115, color=CORAL, a=k, anchor='c')
            k2 = float(np.clip((b - (NBEAT - TAIL) - 0.9) / 0.4, 0, 1))
            if k2 > 0.004:
                by = cy + H * 0.215
                box(img, W * 0.135, by - 52, W * 0.865, by + 52, PAPER, 0.10 * k2)
                for xx in (W * 0.135, W * 0.865):
                    rule(img, by - 52, xx, xx + 2, PAPER, 0.6 * k2, 104)
                rule(img, by - 52, W * 0.135, W * 0.865, PAPER, 0.55 * k2, 2)
                rule(img, by + 52, W * 0.135, W * 0.865, PAPER, 0.55 * k2, 2)
                paint(img, tmask('프로필 링크에서 예약', KRB, 48, 0.02), W / 2, by,
                      color=PAPER, a=k2, anchor='c')
                # **화살표를 글자로 찍지 않는다.** BRAND 는 영문 전용이라
                # ↓ 가 두부로 나온다 — 삼각형을 직접 그린다
                ax, ay = int(W / 2), int(by + 96)
                tri = np.array([[ax - 17, ay - 10], [ax + 17, ay - 10], [ax, ay + 14]], np.int32)
                lay = np.zeros((H, W), np.float32)
                cv2.fillPoly(lay, [tri], 1.0, cv2.LINE_AA)
                img[:] = img * (1 - (lay * k2)[..., None]) + CORAL * (lay * k2)[..., None]

        # 컷 경계에 검은 두 프레임 — 흰 섬광(reel3)과 반대로 간다
        d = min((i - e for e in edges if 0 <= i - e < 2), default=None)
        if d is not None and b < NBEAT - TAIL:
            img *= 0.12 + 0.44 * d

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f"{spec['name']}.mp4")
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f"{final}  {NBEAT * BEAT:.2f}s  {spec['style']} {60 / BEAT:.0f}BPM  {NBEAT}박")


def covers():
    """레터박스 그대로. **릴스와 커버가 같은 옷을 입어야** 눌렀을 때
    다른 영상이 나온 것처럼 안 읽힌다."""
    TH, TOP = 1350, 285
    clip, at, ox = COVER_SRC
    c = cap(clip)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    if not ok:
        raise SystemExit('커버 프레임을 못 읽었습니다')
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    WW = 1080 * 3
    h, w = fr.shape[:2]
    s = max(WW / w, TH / h) * 1.15
    big = cv2.resize(fr, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_AREA)
    x0 = int(np.clip((big.shape[1] - WW) * 0.5, 0, big.shape[1] - WW))
    y0 = int(np.clip(big.shape[0] * 0.48 - TH / 2, 0, big.shape[0] - TH))
    big = grade(big[y0:y0 + TH, x0:x0 + WW].astype(np.float32) / 255)
    big *= 0.60                                    # 글자가 주인공이라 사진을 눌러 둔다

    for i, line in enumerate(COVER_LINES):
        cx = 1080 * i + 540
        if i == 0:
            # 첫 칸은 숫자가 주인공. 격자에서 제일 먼저 눈에 걸린다
            paint(big, tmask(str(EV.OPEN_LEFT), BRAND, 250, 0.02), cx, TH * 0.42,
                  color=PAPER, anchor='c')
            paint(big, tmask('자리 남았습니다', KRB, 62, 0.02), cx, TH * 0.66,
                  color=PAPER, anchor='c')
        else:
            paint(big, tmask(line, KRB, min(76, fit(line, KRB, 1080 * 0.82, 0.02)), 0.02),
                  cx, TH * 0.50, color=PAPER, anchor='c')
        paint(big, tmask(f'D-{DDAY}' if DDAY > 0 else 'TODAY', BRAND, 30, 0.16),
              cx, TH * 0.155, color=CORAL, anchor='c')
        paint(big, tmask('8.29 SAT  ·  양재 루프탑', KR, 34, 0.02), cx, TH * 0.80,
              color=PAPER, a=0.86, anchor='c')
        paint(big, tmask(EV.HANDLE, BRAND, 21, 0.20), cx, TH * 0.865,
              color=PAPER, a=0.58, anchor='c')

    for i in range(3):
        tile = big[:, 1080 * i:1080 * (i + 1)]
        cv_ = np.zeros((H, W, 3), np.float32)
        cv_[TOP:TOP + TH] = tile
        for k in range(TOP):
            f = (1 - k / TOP) ** 1.5
            cv_[TOP - 1 - k] = tile[0] * f
            cv_[TOP + TH + k] = tile[-1] * f
        p = os.path.join(OUT, f'cover_{i + 1}.png')
        Image.fromarray((np.clip(cv_, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)
    print('올리는 순서 3 → 2 → 1')


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if not CLIPS:
        raise SystemExit(f'{SRC} 에 mp4 가 없습니다')
    want = [a for a in args if a.isdigit()]
    if 'cover' in args or not args:
        covers()
    if not (args and 'cover' in args and not want):
        for i, spec in enumerate(REELS, 1):
            if want and str(i) not in want:
                continue
            render(spec)
    for c in _CAPS.values():
        c.release()
