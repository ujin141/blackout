"""릴스 커버 — **줄판의 한 칸을 릴스 자리에 앉힌다.**

릴스를 그냥 올리면 그리드에서 그 칸만 다른 그림이 되어 줄이 끊긴다.
커버를 이걸로 주면 릴스가 줄의 한 칸으로 보인다.

    그리드는 커버(1080×1920)의 **가운데를 4:5 로 잘라** 보여준다.
    1350 짜리 타일을 그대로 커버로 주면 잘린 결과가 밀려서 줄이 안 맞는다 —
    타일을 정확히 top=285 에 앉혀야 다른 두 칸과 딱 떨어진다.

위아래 여백은 타일 끝 줄을 늘여 어둡게 채운다. 릴스를 전체 화면으로 봐도
검은 띠가 아니라 판이 이어진 것으로 보인다.

**세 칸 모두 뽑는다.** 릴스를 몇 번째 칸에 넣을지는 그때 정하게 되는데,
1칸 커버만 있으면 자리를 못 바꾼다.

    out/reel_cover/{줄}_{칸}_cover.png

`feed_plan.ROWS` 를 그대로 돈다 — 줄을 늘리면 커버도 따라 나온다.
뽑은 뒤 **4:5 로 잘라 원본 타일과 같은지 재고**, 다르면 멈춘다.

python reel_cover.py            → 전부
python reel_cover.py promo      → 그 줄만
"""
import os
import sys
import numpy as np
from PIL import Image
import feed_plan

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'out')
OUT = os.path.join(SRC, 'reel_cover')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
CH = 1920
TOP = (CH - TH) // 2                      # 285. 그리드의 4:5 크롭과 맞는 자리


def cover(tile):
    a = np.asarray(tile.convert('RGB')).astype(np.float32) / 255.0
    canvas = np.zeros((CH, TW, 3), np.float32)
    canvas[TOP:TOP + TH] = a
    for i in range(TOP):
        f = (1 - i / TOP) ** 1.6          # 끝 줄을 늘여 어둡게 — 검은 띠가 아니라 이어짐
        canvas[TOP - 1 - i] = a[0] * f
        canvas[TOP + TH + i] = a[-1] * f
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))


def check(cov, tile):
    """그리드가 보여줄 4:5 구간이 원본 타일과 같은지 잰다.

    **뽑았다고 맞는 게 아니다.** TOP 을 한 번 잘못 잡으면 줄 전체가 몇 픽셀씩
    밀리는데, 눈으로는 안 보이고 올린 뒤에야 드러난다."""
    a = np.asarray(cov.convert('RGB')).astype(np.int16)[TOP:TOP + TH]
    b = np.asarray(tile.convert('RGB')).astype(np.int16)
    return float(np.abs(a - b).mean())


if __name__ == '__main__':
    want = sys.argv[1:]
    rows = [r for r in feed_plan.ROWS if not want or r[1] in want]
    assert rows, f'그런 줄이 없습니다 — {", ".join(r[1] for r in feed_plan.ROWS)}'
    n = 0
    for folder, stem, name in rows:
        made = []
        for i in (1, 2, 3):
            p = os.path.join(SRC, folder, f'{stem}_{i}.png')
            if not os.path.exists(p):
                break
            t = Image.open(p)
            assert t.size == (TW, TH), f'{p} 가 {t.size} 입니다 — 타일은 {TW}×{TH}'
            c = cover(t)
            q = os.path.join(OUT, f'{stem}_{i}_cover.png')
            c.save(q, optimize=True)
            d = check(c, t)
            assert d < 0.001, f'{q} 의 4:5 구간이 타일과 다릅니다 (차 {d:.4f})'
            made.append((i, q))
        if made:
            print(f'── {name}')
            for i, q in made:
                print(f'   {i}칸  {q}')
            n += len(made)
    print(f'\n{n}장. 4:5 구간이 타일과 같은지 전부 확인했습니다.')
    print('릴스를 넣을 칸의 커버를 쓰고, 나머지 두 칸은 사진으로 올리면 줄이 이어집니다.')
