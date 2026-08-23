"""
**릴스 세트 커버 3장.** `push` · `day` · `dusk` 용.

    python cover_set.py   →  out/cover_set/ 세 장 + 나란히 붙인 확인용

## 왜 검정 타이포 판이 아닌가

`cover_reels` 는 검정 바탕에 은색 글자다. 브랜드 톤엔 맞지만 **탐색 탭에서
그냥 넘어간다** — 어두운 사각형은 스크롤을 못 멈춘다.

여기 목적은 바이럴이다. 우리를 이미 아는 사람이 아니라 **처음 보는 사람이
손가락을 멈추는 것**이 목표라, 규칙을 하나 바꿨다.

    배경   현장 사진. **사람이 가득 찬 프레임**을 릴스와 같은 색으로 뽑는다
    글자   화면 폭을 거의 채우는 한 덩어리. 멀리서도 읽힌다
    나머지 로고와 날짜만. 정보는 캡션이 한다

## 세 장이 각각 강해야 한다

이어지는 그림은 **이미 프로필에 온 사람**에게만 보인다. 탐색 탭에서는
한 장씩 따로 뜬다 — 그래서 이어 붙이는 대신 **같은 문법**으로 묶었다.
글자 자리·띠·로고 위치가 같아서 나란히 놓으면 시리즈로 읽힌다.

훅은 셋이 각각 다른 것을 판다.

    push   **10자리** — 희소. 숫자 하나가 제일 세다
    day    **혼자 와도 됨** — 문턱. 이 행사가 실제로 파는 것
    dusk   **9시 반부터 다른 파티** — 궁금증. 하루가 두 번이라는 말

## 잘리는 자리

    올리는 판    1080 × 1920
    격자에 보임  가운데 정사각 (y 420 ~ 1500)

**훅은 그 정사각 안에 둔다.** 격자에서 반만 보이면 없는 것과 같다.
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

import event as EV
from fonts import KR, KRB, KRD
from poster_kit import BRAND
from reel_set import GRADE

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'cover_set')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
SQ_T, SQ_B = 420, 1500               # 격자가 정사각으로 자르는 구간

# (릴스, 올리는 차례, 원본, 초, 훅 윗줄, 훅 아랫줄, 받침)
# 배경은 그 릴스에 실제로 쓰인 장면에서 뽑는다 — 커버와 영상이 이어진다
SHOTS = [
    ('push', 3, 'P1023234', 17.5, None, None, None),
    ('day',  2, 'P1023235',  4.2, '혼자 와도', '됩니다', '9시 반부터 솔로파티 90분'),
    ('dusk', 1, 'P1023231',  9.5, '9시 반부터', '다른 파티', '물에서 놀다 그대로 올라옵니다'),
]


def frame(src, t, tag):
    """원본 한 장을 릴스와 같은 색으로. **다른 색을 쓰면 커버만 남의 것이 된다.**"""
    p = os.path.join(OUT, f'_bg_{tag}.png')
    r = subprocess.run(
        ['ffmpeg', '-v', 'error', '-ss', str(t),
         '-i', os.path.join(SRC, f'{src}.MOV'), '-frames:v', '1',
         '-vf', f'{GRADE[tag]},scale={W}:{H}:flags=lanczos', '-y', p],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    return Image.open(p).convert('RGB')


def shade(im):
    """위아래를 떨군다. **글자 뒤에 띠를 두르지 않는다** — 화면이 어두워진
    것으로 읽혀야 얹은 판으로 안 보인다."""
    d = ImageDraw.Draw(im, 'RGBA')
    for y in range(0, 620):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / 620) ** 1.4)))
    for y in range(H - 560, H):
        t = (y - (H - 560)) / 560
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(185 * t ** 0.95)))
    return im


def mid(d, y, text, font, fill, track=0):
    if track:
        ws = [d.textlength(c, font=font) for c in text]
        x = (W - (sum(ws) + track * (len(text) - 1))) / 2
        for c, w in zip(text, ws):
            d.text((x, y), c, font=font, fill=fill)
            x += w + track
        return
    d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)


def fit(d, text, path, start, maxw):
    size = start
    while size > 20 and d.textlength(text, font=ImageFont.truetype(path, size)) > maxw:
        size -= 2
    return ImageFont.truetype(path, size)


def build():
    made = []
    for tag, order, src, t, l1, l2, sub in SHOTS:
        im = shade(frame(src, t, tag))
        d = ImageDraw.Draw(im, 'RGBA')
        for y in range(620, 1240):
            t = (y - 620) / 620
            d.line([(0, y), (W, y)],
                   fill=(0, 0, 0, int(96 * (1 - abs(t * 2 - 1)) ** 0.8)))

        # ── 머리 ─────────────────────────────────────────
        mid(d, 118, 'BLACKOUT CREW', ImageFont.truetype(BRAND, 30),
            (255, 255, 255, 235), track=10)
        mid(d, 175, EV.DATE_EN, ImageFont.truetype(BRAND, 24),
            (226, 230, 240, 210), track=8)

        # ── 훅 ───────────────────────────────────────────
        if tag == 'push':
            # **숫자 하나.** 읽는 게 아니라 보이는 크기여야 한다
            d.text((W / 2, 760), str(EV.OPEN_LEFT),
                   font=ImageFont.truetype(KRD, 460),
                   fill=(255, 255, 255, 255), anchor='mm')
            mid(d, 1010, '자리 남았습니다', ImageFont.truetype(KRD, 86),
                (255, 255, 255, 250))
            mid(d, 1130, f'{EV.OPEN_WAVE[0]} 예약 · {EV.DUE_STR} 마감',
                ImageFont.truetype(KRB, 44), (232, 236, 244, 232))
        else:
            f1 = fit(d, l1, KRD, 128, W * 0.86)
            f2 = fit(d, l2, KRD, 128, W * 0.86)
            mid(d, 700, l1, f1, (255, 255, 255, 252))
            mid(d, 850, l2, f2, (255, 255, 255, 252))
            mid(d, 1035, sub, ImageFont.truetype(KRB, 44), (232, 236, 244, 234))

        # ── 발 ───────────────────────────────────────────
        d.line([(W * 0.14, 1340), (W * 0.86, 1340)], fill=(255, 255, 255, 92), width=2)
        mid(d, 1385, EV.NAME, ImageFont.truetype(BRAND, 52),
            (255, 255, 255, 248), track=6)
        mid(d, 1462, f'{EV.DATE} · {EV.VENUE}', ImageFont.truetype(KR, 33),
            (230, 234, 242, 224))

        p = os.path.join(OUT, f'{order}_{tag}.png')
        im.save(p, optimize=True)
        os.remove(os.path.join(OUT, f'_bg_{tag}.png'))
        made.append((order, tag, p))
        print(f'{p}   {order}번째로 올림')

    # 나란히 붙여 한 줄로 보이는지 확인 — 격자는 정사각으로 자른다
    row = Image.new('RGB', (360 * 3, 360), (0, 0, 0))
    for i, (order, tag, p) in enumerate(sorted(made, reverse=True)):
        row.paste(Image.open(p).crop((0, SQ_T, W, SQ_B)).resize((360, 360)),
                  (360 * i, 0))
    row.save(os.path.join(OUT, 'row.png'))

    print()
    print('올리는 순서 — **거꾸로다.** 격자는 최신이 왼쪽 위다')
    for order, tag, p in sorted(made, key=lambda m: m[0]):
        print(f'  {order}) {tag}.mp4  →  {os.path.basename(p)}')
    return OUT


if __name__ == '__main__':
    build()
