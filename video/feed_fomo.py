"""
**예약 전환 피드 3연작.** 차수 진행을 격자 한 줄로 펼친다.

    python feed_fomo.py   →  out/feed_fomo/ 세 장 + 나란히 붙인 확인용

## 왜 세 칸으로 펼치나

`poster_fomo` 는 한 장 안에 세 줄을 쌓았다. 그건 판 하나로 끝나는 대신
**각 줄이 작아진다.** 격자로 펼치면 한 칸이 통째로 한 차수라 숫자가
화면을 채운다 — 프로필에 들어온 사람은 세 칸을 한 번에 본다.

    올리는 차례   1차 → 2차 → 3차
    격자에 보임   왼쪽 3차 · 가운데 2차 · 오른쪽 1차

**격자는 최신이 왼쪽 위**라 마지막에 올린 3차가 왼쪽에 걸린다. 눈이
왼쪽부터 가므로 **지금 살 수 있는 것을 먼저 보고, 그 옆에 증거(SOLD OUT
둘)가 따라온다** — 시간 순서로 늘어놓는 것보다 이쪽이 낫다.

타임라인에서도 마지막에 올린 3차 OPEN 이 먼저 뜬다. 팔로워가 보는 것도
지금 파는 것이어야 한다.

## 릴스를 끼워 올릴 때

세 칸 중 **열린 차수 칸(3차)** 은 릴스로 올릴 수 있다. 그 칸의 커버를
`_cover.png` 로 같이 뽑는다 — 릴스는 9:16 이라 4:5 판의 가장자리를 복제해
늘린 것이고, 격자는 어차피 정사각으로 자르므로 늘린 부분은 안 보인다.

    1) 오른쪽   1차 SOLD OUT    피드 게시물
    2) 가운데   2차 SOLD OUT    피드 게시물
    3) 왼쪽     3차 OPEN        **릴스** — 커버로 `_cover.png` 를 지정한다

## 칸마다 완결된다

배경은 세 칸이 다른 프레임이지만 **색·띠·글자 자리가 같아** 한 줄로 읽힌다.
날짜와 장소는 세 칸에 다 넣는다 — 하나만 열어 본 사람에게도 말이 돼야 한다.

값과 예약 버튼은 **3차 칸에만** 넣는다. 닫힌 차수에 값을 적으면 지금 살 수
있는 것으로 오해한다.

## 잘리는 자리

    올리는 판    1080 × 1350
    격자에 보임  가운데 정사각 (y 135 ~ 1215)

차수 숫자와 SOLD OUT 은 그 정사각 안에 둔다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

import event as EV
from fest_kit import justify, specks, vignette
from fonts import KR, KRB, KRD
from poster_dj3 import chrome
from poster_dj4 import fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM
from poster_kit import (BRAND, tmask, paint, rule, box, glow, outline, grain,
                        logo)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'feed_fomo')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
SAFE_T, SAFE_B = 135, 1215        # 격자가 정사각으로 자르는 구간
CH_ = 1920                        # 릴스 커버 높이
PAD = (CH_ - TH) // 2             # 위아래로 늘리는 양 (285)

# 사진은 셋 다 다른 프레임. **같은 그림을 세 번 쓰면 한 장을 세 조각 낸 것으로
# 보인다** — 0.5초마다 피부 덩어리를 세어 고른 구간에서 셋을 뽑았다
SHOTS = {'1차': ('P1023237', 16.0),
         '2차': ('P1023231',  9.0),
         '3차': ('P1023234', 16.5)}

GRADE = ("curves=master='0/0.016 0.25/0.22 0.5/0.52 0.75/0.80 1/0.98',"
         'vibrance=intensity=0.26,'
         'colorbalance=rm=0.02:gm=0.004:bm=0.006:rh=-0.01:bh=0.03,'
         'eq=contrast=1.12:saturation=1.04:gamma=0.98')


def photo(clip, at):
    """현장 프레임 하나를 칸 크기로. 원본은 2160×3840 세로다."""
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
    y0 = int((h - need_h) * 0.62)          # 사람이 아래쪽 풀에 몰려 있다
    im = im[max(0, y0):max(0, y0) + need_h]
    return cv2.resize(im, (TW, TH), interpolation=cv2.INTER_AREA)


def cell(name, cap, got, closed):
    """칸 하나. 닫힌 차수와 열린 차수가 **한눈에 갈려야** 한다."""
    img = photo(*SHOTS[name])
    y = np.arange(TH, dtype=np.float32)[:, None, None]
    # 위는 차수 숫자, 아래는 정보 자리 — 가운데만 사진으로 남긴다
    img *= (1 - 0.94 * np.clip(1 - y / (TH * 0.42), 0, 1) ** 0.85)
    img *= (1 - 0.90 * np.clip((y - TH * 0.60) / (TH * 0.28), 0, 1) ** 0.85)

    M = int(TW * 0.088)
    paint(img, tmask('BLACKOUT CREW', BRAND, 15, 0.34), M, SAFE_T - 40,
          color=SILVER, a=0.86, anchor='l')
    paint(img, tmask(EV.DATE_EN, BRAND, 15, 0.22), TW - M, SAFE_T - 40,
          color=SILVER, a=0.86, anchor='r')

    # ── 차수 — 칸을 채운다 ───────────────────────────────
    ns = justify(name, TW * 0.52, 0.01, cap=230)
    nm = tmask(name, KRD, ns, 0.01)
    if closed:
        paint(img, nm, TW / 2, SAFE_T + 150, color=PAPER, a=0.60, anchor='c')
        t = tmask('SOLD OUT', BRAND, 62, 0.16)
        paint(img, t, TW / 2, SAFE_T + 320, color=PAPER, a=0.80, anchor='c')
        # 취소선. **끝났다는 걸 글자 스스로 말한다**
        rule(img, SAFE_T + 320, TW / 2 - t.shape[1] / 2 - 8,
             TW / 2 + t.shape[1] / 2 + 8, PAPER, 0.85, 5)
    else:
        glow(img, nm, TW / 2, SAFE_T + 150, SILVER, 0.26, 30, anchor='c')
        chrome(img, nm, TW / 2, SAFE_T + 150, PAPER, STEEL)
        paint(img, outline(nm, 3), TW / 2, SAFE_T + 150, color=PAPER, a=0.94,
              anchor='c')
        bh = 82
        box(img, M, SAFE_T + 280, TW - M, SAFE_T + 280 + bh, PAPER, 0.97)
        paint(img, tmask('예약 OPEN', KRD, 40, 0.01), TW / 2,
              SAFE_T + 280 + bh * 0.5, color=np.float32([0.02, 0.02, 0.03]),
              anchor='c')
        paint(img, tmask(f'{cap - got}자리 남았습니다', KRD, 34, 0.01), TW / 2,
              SAFE_T + 416, color=PAPER, anchor='c')

    # ── 발 — 세 칸이 같은 자리에 같은 것을 둔다 ──────────
    fy = SAFE_B - 210
    rule(img, fy, M, TW - M, SILVER, 0.30, 2)
    paint(img, tmask(EV.NAME, BRAND, 46, 0.10), TW / 2, fy + 52,
          color=PAPER, a=0.96, anchor='c')
    paint(img, tmask(f'{EV.DATE}  ·  {EV.VENUE}', KRB, 26, 0.01), TW / 2,
          fy + 106, color=SILVER, a=0.94, anchor='c')

    # 값과 예약은 **열린 차수 칸에만**. 닫힌 칸에 적으면 지금 살 수 있는
    # 것으로 오해한다
    if not closed:
        pr = EV.PRICE.get(name)
        if pr:
            paint(img, tmask(f"여 {pr['여']:,}   ·   남 {pr['남']:,}", KRD, 30,
                             0.01), TW / 2, fy + 158, color=PAPER, anchor='c')
        paint(img, tmask(f'{EV.CAP}명 한정  ·  {EV.PERKS} 포함', KR, 21, 0.01),
              TW / 2, fy + 202, color=SILVER, a=0.90, anchor='c')
    else:
        paint(img, tmask(f'{EV.CAP}명 한정  ·  {EV.PERKS} 포함', KR, 21, 0.01),
              TW / 2, fy + 158, color=SILVER, a=0.88, anchor='c')

    specks(img, 60, 0, int(TH * 0.34), PAPER, 0.10, seed=len(name) * 17,
           rmax=2.0)
    fringe(img, 0.0010)
    vignette(img, 0.32, 2.4)
    grain(img, 0.005, len(name) * 7 + 3)
    return np.clip(img, 0, 1)


def build():
    waves = [(n, cap, got) for n, cap, got, _ in EV.WAVES]
    if len(waves) != 3:
        raise SystemExit(f'차수가 셋이어야 합니다 — 지금 {len(waves)}개')

    made = []
    # 격자는 최신이 왼쪽 위. **오른쪽 칸을 먼저 올린다**
    for i, (name, cap, got) in enumerate(waves):
        closed = got >= cap
        img = cell(name, cap, got, closed)
        order = len(waves) - i          # 1차가 3번째… 가 아니라 1번째로 올라간다
        tag = 'ABC'[i]
        p = os.path.join(OUT, f'{i + 1}_{tag}_{name}.png')
        p8 = (img * 255).astype(np.uint8)
        Image.fromarray(p8).save(p, optimize=True)
        where = ('오른쪽', '가운데', '왼쪽')[i]
        made.append((i + 1, name, where, p))
        print(f'{p}   {where} 칸 · {i + 1}번째로 올림')
        if not closed:
            # **열린 차수 칸은 릴스로 올릴 수 있다.** 릴스 커버는 9:16 이라
            # 4:5 판의 가장자리를 복제해 늘린다 — 격자는 어차피 정사각으로
            # 자르므로 늘린 부분은 안 보이고 이음매도 안 생긴다
            cov = cv2.copyMakeBorder(p8, PAD, CH_ - TH - PAD, 0, 0,
                                     cv2.BORDER_REPLICATE)
            q = os.path.join(OUT, f'{i + 1}_{tag}_{name}_cover.png')
            Image.fromarray(cov).save(q, optimize=True)
            print(f'{q}   ← 이 칸을 릴스로 올릴 때 커버 (1080×1920)')

    row = Image.new('RGB', (360 * 3, 360), (0, 0, 0))
    for k, (order, name, where, p) in enumerate(reversed(made)):
        row.paste(Image.open(p).crop((0, SAFE_T, TW, SAFE_B)).resize((360, 360)),
                  (360 * k, 0))
    row.save(os.path.join(OUT, 'row.png'))

    print()
    print('올리는 순서 — **1차부터.** 격자는 최신이 왼쪽 위라 마지막에 올린')
    print('3차 OPEN 이 왼쪽에 걸린다. 눈이 왼쪽부터 가므로 지금 살 수 있는')
    print('것을 먼저 보고 그 옆에 SOLD OUT 둘이 증거로 따라온다')
    for order, name, where, p in made:
        print(f'  {order}) {name}  →  {os.path.basename(p)}   {where} 칸')
    return OUT


if __name__ == '__main__':
    build()
