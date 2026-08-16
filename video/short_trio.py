"""숏폼 D안 — **세 편이 한 줄이 되는 연작.** 1080×1920 · 30fps · 128BPM.

    trio_1.mp4 · trio_2.mp4 · trio_3.mp4     릴스 세 편
    trio_1_cover.png · … · trio_3_cover.png  각 편의 커버
    trio_row.png                             셋을 붙여 본 그림(확인용)

앞선 셋(A 전면 · B 두 판 · C 색 판)과 다른 점은 **낱개가 아니라 연작**이라는
것이다. 세 편을 다 올리면 프로필 그리드에서 **커버 세 장이 한 장면으로
이어진다** — 하나만 봐도 말이 되고, 셋을 같이 보면 다른 그림이 된다.

    [01 물]      [02 사람]     [03 새벽]
      낮 → 밤으로 넘어가는 빛이 세 칸을 가로지른다

**이어지게 만드는 건 사진이 아니라 빛과 선이다.** 한 사진을 3.2:1 로 늘리면
가운데 칸에만 사람이 남는다 — 대신 가로로 흐르는 빛 한 줄기와 세 칸을
관통하는 가로선 하나로 잇는다. 칸마다 사진은 달라도 한 장면으로 읽힌다.

**커버는 릴스의 첫 프레임과 같다.** 인스타가 자동으로 고른 프레임을 쓰면
그리드에서 줄이 깨지므로, 각 편이 자기 커버로 시작하게 짰다 —
커버를 따로 지정해도 되고 안 해도 줄이 안 어긋난다.

⚠ 실제 손님 얼굴이 나온다. 초상권은 저작권과 별개다.

python short_trio.py            → 세 편 다
python short_trio.py 2          → 2편만
"""
import os
import subprocess
import sys
import numpy as np
import cv2
from PIL import Image
from poster_kit import BRAND, tmask, fit, paint, rule, logo, sign, status_tag
from fonts import KR, KRB
import event as EV
import short

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'trio')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
TH = 1350                              # 그리드 한 칸의 높이(4:5)
TOP = (H - TH) // 2                    # 285. 커버 안에서 타일이 앉는 자리
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM

INK = np.float32([0.020, 0.028, 0.042])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA = np.float32([0.36, 0.92, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
DIM = np.float32([0.55, 0.62, 0.72])

# (번호, 영문, 한글 한 줄, 시간, 컷들[(클립, 시작초, 박)])
PARTS = [
    ('01', 'WATER', '해 지기 전엔 물에서',   'PM 19:00',
     [('sky', 2.6, 8, 0.50), ('side', 0.2, 6, 0.45),
      ('walk', 0.1, 6, 0.50), ('crowd', 0.2, 6, 0.55)]),
    ('02', 'PEOPLE', '9시 반부터 솔로파티',  'PM 21:30',
     [('crowd', 4.0, 8, 0.50), ('floor', 0.3, 6, 0.45),
      ('side', 3.0, 6, 0.55), ('walk', 3.4, 6, 0.45)]),
    ('03', 'AFTER', '끝나면 강남에서 2차',   'AM 12:00',
     [('floor', 4.2, 8, 0.55), ('crowd', 6.6, 6, 0.45),
      ('sky', 6.8, 6, 0.50), ('walk', 1.6, 6, 0.55)]),
]
TAIL = 6                               # 끝 여섯 박은 마무리 판


def field(w, h, i):
    """세 칸이 이어져 보이게 하는 바탕.

    **낮에서 밤으로 넘어가는 빛이 세 칸을 가로지른다.** 칸을 따로 그려도
    `i` 만큼 빛의 자리를 옮기면 붙였을 때 한 줄기가 된다."""
    img = np.repeat(np.repeat(INK[None, None, :], h, 0), w, 1).copy()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # 세 칸을 하나의 가로축(0~3)으로 보고 그 위에서 빛을 계산한다
    u = (i + xx / w) / 3.0
    glow = np.exp(-((u - 0.42) / 0.30) ** 2) * np.exp(-((yy / h - 0.44) / 0.55) ** 2)
    img += glow[..., None] * (AQUA * 0.62 + PAPER * 0.10) * 0.34
    img *= (1 - 0.30 * np.clip((yy / h - 0.72) / 0.28, 0, 1))[..., None]
    return img


def tile(i):
    """그리드 한 칸(1080×1350). 커버의 가운데에 그대로 앉는다."""
    num, en, ko, tm, _ = PARTS[i]
    img = field(W, TH, i)
    cx = W / 2

    # 세 칸을 관통하는 가로선 — 붙이면 한 줄로 이어진다
    rule(img, TH * 0.615, 0, W, PAPER, 0.16, 2)

    paint(img, tmask(num, BRAND, 210, 0.0), cx, TH * 0.30, color=PAPER, a=0.16,
          anchor='c')
    paint(img, tmask(en, BRAND, min(72, fit(en, BRAND, W * 0.80, 0.14)), 0.14),
          cx, TH * 0.30, color=PAPER, anchor='c')
    paint(img, tmask(tm, BRAND, 22, 0.34), cx, TH * 0.30 + 62, color=AQUA, a=0.92,
          anchor='c')
    paint(img, tmask(ko, KRB, min(46, fit(ko, KRB, W * 0.84, 0.02)), 0.02),
          cx, TH * 0.72, color=PAPER, anchor='c')

    if i == 1:                                    # 가운데 칸에만 행사 이름
        paint(img, tmask(EV.NAME, BRAND, min(40, fit(EV.NAME, BRAND, W * 0.80, 0.16)),
                         0.16), cx, TH * 0.845, color=PAPER, a=0.88, anchor='c')
    elif i == 2:
        paint(img, tmask(EV.DATE_EN, BRAND, 30, 0.20), cx, TH * 0.845,
              color=PAPER, a=0.88, anchor='c')
    else:
        sign(img, cx, TH * 0.845, 22, color=PAPER, a=0.80, anchor='c')
    return np.clip(img, 0, 1)


def cover(t):
    """1080×1920 커버. **타일을 정확히 top=285 에 앉힌다** — 그리드가
    커버의 가운데를 4:5 로 잘라 보여주기 때문에 여기가 어긋나면 줄이 깨진다."""
    c = np.zeros((H, W, 3), np.float32)
    c[TOP:TOP + TH] = t
    for k in range(TOP):
        f = (1 - k / TOP) ** 1.5
        c[TOP - 1 - k] = t[0] * f
        c[TOP + TH + k] = t[-1] * f
    return np.clip(c, 0, 1)


def render(i):
    num, en, ko, tm, shots = PARTS[i]
    nb = sum(s[2] for s in shots)
    assert nb + TAIL == NBEAT, f'{num}: 컷 {nb}박 + 끝 {TAIL}박 ≠ {NBEAT}박 — 뒤가 잘린다'

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    cov = cover(tile(i))
    caps = {s[0]: short.load(s[0]) for s in shots}
    plan = []
    for key, at, nbeat, ox in shots:
        fps = caps[key].get(cv2.CAP_PROP_FPS) or 30.0
        n = int(round(nbeat * BEAT * FPS))
        for f in range(n):
            # 아주 느린 푸시인. 정지 크롭이면 손 흔들림만 보인다
            plan.append((key, int((at + f / FPS) * fps), ox, 1.0 + 0.05 * f / n))
    nf = int(round(NBEAT * BEAT * FPS))

    raw = os.path.join(OUT, f'raw_{num}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}

    def grab(key, fno):
        c = caps[key]
        if last.get(key) != fno - 1:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
        if not ok:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
            ok, fr = c.read()
        last[key] = fno
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((1080, 1920, 3), np.uint8)

    HOLD = int(0.7 * FPS)                          # 커버를 잠깐 들고 시작한다
    for f in range(nf):
        b = (f / FPS) / BEAT
        if f < HOLD:
            img = cov.copy()
        elif b < NBEAT - TAIL:
            key, fno, ox, z = plan[min(f - HOLD, len(plan) - 1)]
            img = short.grade(short.crop916(grab(key, fno), ox, z).astype(np.float32) / 255)
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            img *= 1 - 0.54 * np.clip((yy - H * 0.50) / (H * 0.20), 0, 1) ** 1.15
            # 편 번호와 한 줄은 내내 붙어 있다 — 어느 초에 멈춰도 몇 편인지 안다
            paint(img, tmask(num, BRAND, 44, 0.10), W * 0.085, H * 0.615,
                  color=PAPER, a=0.85)
            paint(img, tmask(ko, KRB, min(56, fit(ko, KRB, W * 0.82, 0.02)), 0.02),
                  W * 0.085, H * 0.672, color=PAPER)
            status_tag(img, W * 0.085, H * 0.722, 34, color=PAPER, accent=CORAL,
                       width=W * 0.80)
        else:
            k = np.clip((b - (NBEAT - TAIL)) / 0.5, 0, 1)
            img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
            lg = logo(58)
            paint(img, lg, W / 2 - lg.shape[1] / 2, H * 0.40 - 116, color=PAPER,
                  a=float(k) * 0.94)
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.86, 0.10), 0.10),
                  W / 2, H * 0.40, color=PAPER, a=float(k), anchor='c')
            paint(img, tmask(f'{EV.DATE_EN}  ·  {EV.VENUE}', KR, 32, 0.02),
                  W / 2, H * 0.40 + 74, color=PAPER, a=float(k) * 0.94, anchor='c')
            yb = status_tag(img, W / 2, H * 0.40 + 150, 34, color=PAPER, accent=CORAL,
                            a=float(k), width=W * 0.80, anchor='c')
            k2 = np.clip((b - (NBEAT - TAIL) - 1.2) / 0.5, 0, 1)
            if k2 > 0.004:
                paint(img, tmask('프로필 링크에서 예약', KRB, 50, 0.02), W / 2, yb + 84,
                      color=CORAL, a=float(k2), anchor='c')
                sign(img, W / 2, yb + 160, 28, color=PAPER, a=float(k2) * 0.92,
                     anchor='c')
        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        c.release()

    final = os.path.join(OUT, f'trio_{num.lstrip("0")}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    Image.fromarray((cov * 255).astype(np.uint8)).save(
        os.path.join(OUT, f'trio_{num.lstrip("0")}_cover.png'), optimize=True)
    print(f'{final}  {W}x{H}  {NBEAT * BEAT:.2f}s  · 커버 같이 나옴')


if __name__ == '__main__':
    want = [int(a) - 1 for a in sys.argv[1:]] or [0, 1, 2]
    for i in want:
        render(i)
    # 셋을 붙여 확인 — 커버의 4:5 구간이 그리드에서 보이는 그림이다
    row = np.concatenate([tile(i) for i in range(3)], axis=1)
    Image.fromarray((row * 255).astype(np.uint8)).save(
        os.path.join(OUT, 'trio_row.png'), optimize=True)
    print(f'\n{os.path.join(OUT, "trio_row.png")}  ← 셋을 붙인 그림(확인용)')
    print('올리는 순서: 3편 → 2편 → 1편. 커버는 각 편의 trio_N_cover.png 를 지정하세요.')
