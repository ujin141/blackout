"""
릴스 커버 — 숏폼을 피드에 올려도 그리드가 안 깨지게.

**문제.** 계정은 세 칸 그리드를 맞춰 왔는데(멤버 한 칸 + 브랜드 두 칸), 릴스를
피드에 같이 올리면 그 커버가 그리드에 한 칸으로 들어온다. 컬러 실사 프레임이
흑백 브랜드 타일 사이에 끼면 줄이 통째로 어긋나 보인다.

**푸는 방법은 둘이다.**

    1  피드 공유를 끈다   올릴 때 '피드에도 공유' 를 끄면 릴스 탭에만 남고
                          그리드는 그대로다. 대신 프로필 들어온 사람은 못 본다
    2  그리드에 맞는 커버  커버를 브랜드 타일처럼 만들면 피드에 올려도 한 칸이
                          제자리에 앉는다. 이 파일이 그걸 만든다

**커버는 9:16 인데 그리드는 그 가운데를 4:5 로 잘라 보여준다.** 1080×1350 짜리를
그대로 커버로 주면 그리드에서 다시 잘려 글자 위치가 밀린다 —
1080×1920 을 만들고 타일을 정확히 가운데(위 285px)에 앉힌다. feed_row 와 같은 규칙.

색은 **흑백으로 되돌린다.** 포스터는 컬러 예외지만 피드 그리드는 흑백이 규칙이고,
커버는 포스터가 아니라 그리드의 한 칸이다.

python short_cover.py            party 판에서 뽑는다
python short_cover.py heavy      다른 판에서
"""
import os
import sys
import numpy as np
import cv2
from poster_kit import BRAND, tmask, fit, paint, rule, logo, grain
from fonts import KR
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, TH, CH = 1080, 1350, 1920          # 타일 1080×1350 · 커버 1080×1920
TOP = (CH - TH) // 2                  # 285 — 그리드가 잘라 보여주는 자리
PAPER = np.float32([0.97, 0.97, 0.96])
DIM = np.float32([0.55, 0.56, 0.58])


def pick(clip='crowd', at=3.6, ox=0.50):
    """커버로 쓸 프레임. **완성본이 아니라 원본 클립에서 가져온다** —
    완성본에서 뜨면 릴스 자막이 그대로 박힌다(실제로 '여기 서울이에요' 가 찍혔다).
    사람이 제일 많은 컷에서 고른다. 커버는 그리드에서 정지 사진으로 보인다."""
    import short
    c = short.load(clip)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    c.release()
    if not ok:
        raise SystemExit('프레임을 못 읽었습니다')
    fr = short.crop916(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), ox)
    return fr.astype(np.float32) / 255


def build(style):
    fr = pick()
    # **흑백으로 되돌린다.** 그리드는 흑백이 규칙이고 커버는 그리드의 한 칸이다
    g = fr @ np.float32([0.299, 0.587, 0.114])
    img = np.repeat(np.clip((g[..., None] - 0.5) * 1.10 + 0.5, 0, 1), 3, axis=2)
    img = cv2.resize(img, (W, CH), interpolation=cv2.INTER_AREA)

    # 사진은 뒤로 물린다. 커버에서 읽혀야 하는 건 사진이 아니라 행사 이름이다
    img *= 0.30
    yy = np.arange(CH, dtype=np.float32)[:, None, None]
    img *= 1 - 0.45 * np.exp(-((yy - (TOP + TH * 0.42)) / (TH * 0.30)) ** 2)

    # ── 타일은 정확히 가운데(285~1635) 안에서만 그린다 ────
    cy = TOP + TH * 0.30
    lg = logo(int(96))
    paint(img, lg, W / 2, cy - TH * 0.10, color=PAPER, a=0.96, anchor='c')

    ns = fit(EV.NAME, BRAND, W * 0.84, 0.10)
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, cy + TH * 0.055,
          color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 26, 0.36), W / 2, cy + TH * 0.105,
          color=DIM, a=0.95, anchor='c')

    rule(img, cy + TH * 0.165, W * 0.22, W * 0.78, PAPER, 0.24, 2)
    paint(img, tmask('2026.08.29. SAT.', BRAND, 34, 0.20), W / 2, cy + TH * 0.225,
          color=PAPER, a=0.96, anchor='c')
    paint(img, tmask('어나더 루프탑 라운지  ·  양재', KR, 26, 0.02), W / 2, cy + TH * 0.275,
          color=DIM, a=0.92, anchor='c')

    # 발치는 타일 아래쪽 안전선(1215) 안에. 넘기면 그리드에서 잘린다
    paint(img, tmask('@BLACKOUTCREW_OFFICIAL', BRAND, 21, 0.24), W / 2, TOP + 1150,
          color=DIM, a=0.80, anchor='c')

    grain(img, 0.006, 11)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    from PIL import Image
    for st in (sys.argv[1:] or ['party']):
        a = build(st)
        p = os.path.join(OUT, f'cover_{st}.png')
        Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
        print(f'{p}  {W}x{CH}  (그리드는 가운데 {W}x{TH} 만 보여준다)')
