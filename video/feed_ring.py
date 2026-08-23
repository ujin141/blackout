"""
**피드 3연작 — 관통선.** 세 칸을 가로지르는 선과 원으로 진행을 그린다.

    python feed_ring.py   →  out/feed_ring/ 세 장 + 릴스 커버 + 확인용

## `feed_fomo` 와 뭐가 다른가

feed_fomo 는 **차수 숫자를 크게 놓고 사진을 깐** 구조다. 칸마다 독립적이고
이어지는 건 글자 자리뿐이었다.

여기는 **그래픽이 물리적으로 세 칸을 관통한다.** 가로선 하나가 3240px 를
지나가고 각 칸 한가운데에 원이 앉는다 — 격자에서 세 칸이 한 장치로 보인다.

    ●───────●───────○
    1차      2차      3차
    닫힘     닫힘     열림

원본이 세로 2160×3840 이라 **사진은 못 잇는다.** 가로 띠로 자르면 확대율이
커져 물이 안 보이고 앞사람 다리만 남는다(한 번 해 보고 접었다). 그래서
사진은 칸마다 세로로 꽉 채우고 **잇는 일은 그래픽에 맡긴다.**

## 채운 원과 빈 원

닫힌 차수는 **채운 원**, 열린 차수는 **빈 원에 흰 테두리**다. 색을 안 쓰고도
갈린다(브랜드가 흑백). 빈 원이 하나뿐이라 눈이 거기로 간다.

## 두 벌로 나온다

    `N_X_n차.png`        1080×1350   피드 게시물
    `N_X_n차_9x16.png`   1080×1920   릴스 커버 · 스토리

4:5 판의 가장자리를 복제해 9:16 을 만든다. 위아래가 이미 검정이라 늘려도
이음매가 안 생기고, **격자는 어차피 정사각으로 자르므로** 어느 쪽을 올려도
세 칸은 똑같이 이어진다.
"""
import os
import subprocess

import cv2
import numpy as np
from PIL import Image

import event as EV
from fest_kit import justify, specks, vignette
from fonts import KR, KRB, KRD
from poster_dj4 import fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM
from poster_kit import BRAND, tmask, paint, rule, box, grain, logo

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'feed_ring')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
SAFE_T, SAFE_B = 135, 1215        # 격자가 정사각으로 자르는 구간
CH_ = 1920
PAD = (CH_ - TH) // 2

LINE_Y = 560                      # 세 칸을 관통하는 선
RING_R = 168                      # 원 반지름

# 칸 순서는 왼쪽 → 오른쪽. **feed_fomo 와 다른 프레임을 쓴다** — 같은 사진이면
# 리뉴얼이 아니라 재배치로 보인다
SHOTS = {'3차': ('P1023234', 41.0),
         '2차': ('P1023234', 24.5),
         '1차': ('P1023235',  3.0)}

GRADE = ("curves=master='0/0.016 0.25/0.21 0.5/0.51 0.75/0.79 1/0.98',"
         'vibrance=intensity=0.26,'
         'colorbalance=rm=0.018:gm=0.000:bm=0.010:rh=-0.02:bh=0.040,'
         'eq=contrast=1.12:saturation=1.04:gamma=0.98')


def photo(clip, at):
    p = os.path.join(OUT, '_bg.png')
    r = subprocess.run(
        ['ffmpeg', '-v', 'error', '-ss', str(at),
         '-i', os.path.join(SRC, f'{clip}.MOV'), '-frames:v', '1',
         '-vf', GRADE, '-y', p],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    im = cv2.cvtColor(cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR),
                      cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    os.remove(p)
    h, w = im.shape[:2]
    need_h = int(round(w * (TH / TW)))
    y0 = int((h - need_h) * 0.58)
    im = im[max(0, y0):max(0, y0) + need_h]
    return cv2.resize(im, (TW, TH), interpolation=cv2.INTER_AREA)


def ring(img, cx, cy, r, closed):
    """원. **꺼진 것과 켜진 것으로 읽혀야 한다.**

    처음엔 닫힌 차수를 밝은 회색으로 채웠는데 그게 오히려 '켜진' 것으로
    보였다 — 끝난 차수가 제일 밝으면 안 된다. 뒤집었다.

        닫힘   어둡게 채우고 테두리도 얇게. 꺼진 전구
        열림   테두리를 두껍게 흰색으로, 안쪽은 밝힌다. 켜진 전구
    """
    yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    m = np.clip((r - d) / 2.0, 0, 1)
    if closed:
        img *= (1 - m[..., None] * 0.80)
        img += m[..., None] * STEEL * 0.32
        e = np.clip(2.0 - np.abs(d - r), 0, 1)
        img += e[..., None] * SILVER * 0.42
    else:
        img *= (1 - m[..., None] * 0.62)
        img += m[..., None] * SILVER * 0.24
        # 바깥으로 번지는 빛 — 유일하게 켜진 원이다
        halo = np.exp(-((d - r) / 26.0) ** 2)
        img += halo[..., None] * PAPER * 0.22
        e = np.clip(7.0 - np.abs(d - r), 0, 1)
        img += e[..., None] * PAPER * 1.00


def cell(name, cap, got, closed):
    img = photo(*SHOTS[name])
    y = np.arange(TH, dtype=np.float32)[:, None, None]
    img *= (1 - 0.72 * np.clip(1 - y / (TH * 0.30), 0, 1) ** 0.9)
    img *= (1 - 0.88 * np.clip((y - TH * 0.62) / (TH * 0.26), 0, 1) ** 0.85)
    # 선과 원이 앉는 띠만 한 번 더 — 사진이 밝으면 선이 사라진다
    img *= (1 - 0.40 * np.exp(-((y - LINE_Y) / 210.0) ** 2))

    M = int(TW * 0.088)
    paint(img, tmask('BLACKOUT CREW', BRAND, 15, 0.34), M, SAFE_T - 42,
          color=SILVER, a=0.84, anchor='l')
    paint(img, tmask(EV.DATE_EN, BRAND, 15, 0.22), TW - M, SAFE_T - 42,
          color=SILVER, a=0.84, anchor='r')

    # ── 관통선 — 칸 끝에서 끝까지 ────────────────────────
    rule(img, LINE_Y, 0, TW, SILVER, 0.62, 5)
    ring(img, TW / 2, LINE_Y, RING_R, closed)

    # 원 안 — 차수
    paint(img, tmask(name, KRD, 96, 0.01), TW / 2, LINE_Y, color=PAPER,
          anchor='c')

    # 원 아래 — 상태
    if closed:
        t = tmask('SOLD OUT', BRAND, 46, 0.16)
        paint(img, t, TW / 2, LINE_Y + 262, color=PAPER, a=0.88, anchor='c')
        rule(img, LINE_Y + 262, TW / 2 - t.shape[1] / 2 - 8,
             TW / 2 + t.shape[1] / 2 + 8, PAPER, 0.85, 4)
    else:
        bh = 76
        box(img, M, LINE_Y + 222, TW - M, LINE_Y + 222 + bh, PAPER, 0.97)
        paint(img, tmask('예약 OPEN', KRD, 38, 0.01), TW / 2,
              LINE_Y + 222 + bh * 0.5, color=np.float32([0.02, 0.02, 0.03]),
              anchor='c')
        paint(img, tmask(f'{cap - got}자리 남았습니다', KRB, 32, 0.01), TW / 2,
              LINE_Y + 352, color=PAPER, a=0.96, anchor='c')

    # ── 발 ───────────────────────────────────────────────
    fy = SAFE_B - 168
    rule(img, fy, M, TW - M, SILVER, 0.28, 2)
    paint(img, tmask(EV.NAME, BRAND, 44, 0.10), TW / 2, fy + 50, color=PAPER,
          a=0.96, anchor='c')
    paint(img, tmask(f'{EV.DATE}  ·  {EV.VENUE}', KRB, 25, 0.01), TW / 2,
          fy + 100, color=SILVER, a=0.94, anchor='c')
    if not closed:
        pr = EV.PRICE.get(name)
        if pr:
            paint(img, tmask(f"여 {pr['여']:,}   ·   남 {pr['남']:,}  ·  "
                             f"{EV.CAP}명 한정", KR, 21, 0.01), TW / 2,
                  fy + 146, color=SILVER, a=0.90, anchor='c')
    else:
        paint(img, tmask(f'{EV.CAP}명 한정  ·  {EV.PERKS} 포함', KR, 21, 0.01),
              TW / 2, fy + 146, color=SILVER, a=0.88, anchor='c')

    specks(img, 60, 0, int(TH * 0.28), PAPER, 0.10, seed=len(name) * 23,
           rmax=2.0)
    fringe(img, 0.0010)
    vignette(img, 0.30, 2.4)
    grain(img, 0.005, len(name) * 11 + 5)
    return np.clip(img, 0, 1)


def build():
    waves = [(n, cap, got) for n, cap, got, _ in EV.WAVES]
    if len(waves) != 3:
        raise SystemExit(f'차수가 셋이어야 합니다 — 지금 {len(waves)}개')

    made = []
    for i, (name, cap, got) in enumerate(waves):
        closed = got >= cap
        img = cell(name, cap, got, closed)
        p8 = (img * 255).astype(np.uint8)
        tag = 'ABC'[i]
        p = os.path.join(OUT, f'{i + 1}_{tag}_{name}.png')
        Image.fromarray(p8).save(p, optimize=True)
        where = ('오른쪽', '가운데', '왼쪽')[i]
        print(f'{p}   {where} 칸 · {i + 1}번째로 올림')
        made.append((i + 1, name, where, p))
        # **세 장 다 9:16 로도 뽑는다.** 어느 칸을 릴스로 올릴지, 스토리로
        # 돌릴지는 그때 정하면 된다 — 격자는 어차피 정사각으로 자르므로
        # 늘린 위아래는 안 보이고 이음매도 안 생긴다
        cov = cv2.copyMakeBorder(p8, PAD, CH_ - TH - PAD, 0, 0,
                                 cv2.BORDER_REPLICATE)
        q = os.path.join(OUT, f'{i + 1}_{tag}_{name}_9x16.png')
        Image.fromarray(cov).save(q, optimize=True)
        print(f'{q}   {where} 칸 · 9:16 (1080×1920)')

    row = Image.new('RGB', (360 * 3, 360), (0, 0, 0))
    for k, (order, name, where, p) in enumerate(reversed(made)):
        row.paste(Image.open(p).crop((0, SAFE_T, TW, SAFE_B)).resize((360, 360)),
                  (360 * k, 0))
    row.save(os.path.join(OUT, 'row.png'))

    print()
    print('올리는 순서 — **1차부터.** 마지막에 올린 3차가 격자 왼쪽에 걸린다')
    for order, name, where, p in made:
        print(f'  {order}) {name}  →  {os.path.basename(p)}   {where} 칸')
    return OUT


if __name__ == '__main__':
    build()
