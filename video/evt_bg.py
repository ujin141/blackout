"""홈페이지 팝업 배경 — `assets/img/event/bg.webp`.

**이 판이 하는 일은 하나다: "사람이 많다" 를 0.5초 안에 보여주는 것.**
그래서 흐리면 안 된다. 처음 판은 σ=6 으로 뭉개 놔서 사람이 아니라
색 덩어리로 보였다 — 글자를 읽히게 하려다 사진을 죽인 것이다.

글자는 사진이 아니라 **CSS 그늘(.evt__art::after)** 이 책임진다.
여기서는 사진을 살리고, 읽히게 하는 건 저쪽에 맡긴다.

**얼굴은 남의 얼굴이다.** 지난 행사 손님들이라 또렷하게 만들 이유가 없다 —
크게 키우지 않고 약한 blur 를 남겨서 장면은 읽히되 개인은 안 잡히게 둔다.
SOFT 를 0 으로 내리지 마세요.

python evt_bg.py  →  assets/img/event/bg.webp
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'assets', 'img', 'stock', 'crowd.jpg')
DST = os.path.join(HERE, '..', 'assets', 'img', 'event', 'bg.webp')

# 원본 1080×1920 중 사람이 들어찬 띠. 위는 하늘, 아래는 빈 바닥이라 버린다
CROP = (0, 430, 1080, 1150)
OUT = (1600, 1067)
SOFT = 1.1      # **0 으로 내리지 마세요** — 손님 얼굴이 또렷해집니다
LIFT = 0.055    # 어두운 데를 살짝 들어 준다. 그늘이 덮여도 형체가 남게


def build():
    im = Image.open(SRC).convert('RGB').crop(CROP).resize(OUT, Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(SOFT))
    # **채도를 조금 올린다.** 그늘이 덮이면 색이 먼저 죽는다 —
    # 미리 올려 둬야 덮인 뒤에도 물빛과 잔디 초록이 남는다
    im = ImageEnhance.Color(im).enhance(1.14)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    a = np.asarray(im, np.float32) / 255
    a = a + (1 - a) * LIFT
    return Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))


if __name__ == '__main__':
    img = build()
    img.save(DST, 'WEBP', quality=84, method=6)
    print(f'{DST}  {img.size[0]}×{img.size[1]}  {os.path.getsize(DST)/1024:.0f}KB')
