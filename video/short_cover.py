"""릴스 커버(썸네일) — 1080×1920.

    python short_cover.py          →  out/short/cover_ad.png
    python short_cover.py scene    →  out/short/cover_scene.png
    python short_cover.py promo    →  out/short/cover_promo.png
    python short_cover.py sale     →  out/short/cover_sale.png

**커버는 두 군데에서 다르게 보인다.**

    릴스 재생 화면   1080×1920 전체
    프로필 격자      가운데 1080×1350 만 (위 285px · 아래 285px 는 잘림)

그래서 **중요한 건 전부 285 ~ 1635 안에** 둔다. 이 줄(`TOP`·`TH`)을 넘긴
글자는 프로필에서 잘려 나가고, 계정을 보러 온 사람은 잘린 판을 본다.

**첫 줄이 커버의 전부다.** 격자에서는 소리도 움직임도 없고 글자 한 줄만
남는다 — 영상 안의 훅과 같은 문장을 쓴다. 다른 말을 쓰면 눌렀을 때
다른 영상이 나온 것처럼 읽힌다.

얼굴이 정면으로 잡히는 순간은 안 쓴다(`short_card.AD_SHOTS` 와 같은 이유).

**격자에서 두 칸이 같은 말을 하면 한 칸을 버리는 것이다.** 그래서 판마다
주인공을 다르게 둔다.

    ad     한글 훅이 제일 크다. 파는 판
    scene  행사 이름이 제일 크다. 브랜드 판 — 영상 자체가 분위기라 훅이 없다
    promo  받는 물건(샴페인)이 제일 크다. **상품을 말로만 하면 안 믿는다**
    sale   이미 간 사람 수가 제일 크다. 남은 걸 먼저 말하면 안 팔린 것으로 읽힌다
"""
import os
import numpy as np
import cv2
from PIL import Image
import short as S
from short import crop916, grade, load
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from poster_kit import status_tag as _tag
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1920
TH = 1350                                 # 격자에 보이는 높이
TOP = (H - TH) // 2                       # 285

PAPER = np.float32([0.99, 1.00, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
AQUA = np.float32([0.34, 0.94, 1.00])

# **커버는 프로필에 계속 남는 판이다.** 영상은 지나가지만 이건 안 지나간다 —
# 손님 얼굴이 알아볼 만하게 잡힌 컷은 쓰지 않는다.
# ad 는 `crowd 1.4` 로 뒀다가 앞쪽 얼굴이 또렷해서 바꿨다. 지금 컷은 사람이
# 원경에 있고 앞은 튜브와 조명이라 **사람이 많다는 건 남고 얼굴은 안 남는다.**
#
#   src   ('live', 클립, 초, 가로위치)   현장 클립에서 한 장
#         ('scene', 프레임번호)          scene_motion 이 그리는 판을 **자막 없이**
#
# **mp4 에서 프레임을 뽑지 않는다.** 영상에는 자막이 이미 구워져 있어서
# 커버 글자와 겹친다 — 실제로 'AFTER SUNSET' 위에 '9시 반부터 솔로파티' 가
# 겹쳐 나왔다. 그림을 그리는 코드를 직접 불러 자막 얹기 전 상태를 받는다.
#   head  한글 훅. None 이면 행사 이름을 주인공으로 세운다
#   lines 훅 아래 두 줄. 판마다 무엇을 알려야 하는지가 다르다
#   bottle 병을 얹을지. 참여 이벤트 판에만 쓴다
#   press  아래쪽을 누르는 정도. 기본 0.66. **사람이 아래쪽에 몰린 사진은
#          덜 눌러야 한다** — 세게 누르면 "많다" 가 어둠 속으로 사라져서
#          정작 그 말을 하려고 고른 사진이 아무 말도 안 하게 된다
#   soft   사진을 흐리는 정도(σ). **사람이 많은 그림에는 이게 필요하다** —
#          어느 컷을 골라도 손님 얼굴이 나오는데, 커버는 프로필에 계속 남는다.
#          장면은 읽히되 개인은 안 잡히는 선까지만. `assets/img/event/bg.webp`
#          와 같은 판단이다. 0 으로 내리지 마세요
VARIANTS = {
    'ad':    dict(src=('live', 'floor', 2.8, 0.46), head='혼자 와도 되는 풀파티',
                  lines=('8.29 SAT  ·  양재 루프탑', EV.price_str())),
    # **받는 물건을 보여 준다.** '샴페인 준다' 는 글자보다 병 한 장이 세다 —
    # 배경은 사람이 없는 네온 컷이라 병이 앞으로 나온다
    'promo': dict(src=('live', 'floor', 3.6, 0.46), head=EV.PROMO_GET, bottle=True,
                  lines=('8.29 SAT  ·  양재 루프탑',
                         f'{EV.PROMO_NOTE}  ·  {EV.PROMO_DUE} 마감')),
    # scene_story 는 영상 자체가 분위기라 훅이 없다. 커버까지 한글 훅을 달면
    # ad 커버와 격자에서 같은 말을 두 번 하게 된다 — 여기는 이름을 크게 세운다
    # **먼저 찼다는 말이 먼저다.** '60자리 남았습니다' 를 크게 쓰면 안 팔린
    # 판으로 읽히고, '20자리는 이미 찼습니다' 는 안 가면 손해로 읽힌다.
    # **'갔습니다' 라고 쓰지 않는다** — 아직 안 열린 행사라 문장이 안 맞는다.
    # 남은 자리는 아랫줄에서 말한다 — 순서가 뜻을 바꾼다
    # **상태줄을 끈다(tag=False).** 훅이 '1차 사전예약 풀만석' 인데 아래
    # 상태줄도 '1차 사전예약 SOLD OUT' 이라, 한 판에서 같은 말을 두 번 하게 된다
    'sale':  dict(src=('live', 'crowd', 2.0, 0.50), soft=4.2, press=0.44, tag=False,
                  head=EV.SOLD_LINE,
                  lines=('8.29 SAT  ·  양재 루프탑',
                         f'{EV.LEFT_LINE}  ·  {EV.price_str()}')),
    'scene': dict(src=('scene', 180), head=None,
                  lines=('8.29 SAT  ·  양재 루프탑', EV.price_str())),
}


def frame(src):
    if src[0] == 'live':
        _, key, at, ox = src
        c = load(key)
        z = 1.02
    elif src[0] == 'scene':
        import scene_motion as SM
        return np.clip(cv2.resize(SM.push(SM.scene(src[1]), src[1] / SM.FPS),
                                  (W, H), interpolation=cv2.INTER_CUBIC), 0, 1)
    else:
        raise SystemExit(f'모르는 src: {src}')
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    c.set(cv2.CAP_PROP_POS_FRAMES, int(at * fps))
    ok, fr = c.read()
    c.release()
    if not ok:
        raise SystemExit(f'{src} 를 못 읽었습니다')
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    if fr.shape[1] / fr.shape[0] < W / H + 0.02:      # 이미 세로면 그대로 쓴다
        return np.clip(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
                       .astype(np.float32) / 255, 0, 1)
    return grade(crop916(fr, ox, z).astype(np.float32) / 255)


def build(name='ad'):
    v = VARIANTS[name]
    HEAD = v['head']
    img = frame(v['src'])
    if v.get('soft'):
        img = cv2.GaussianBlur(img, (0, 0), v['soft'])
    yy = np.arange(H, dtype=np.float32)[:, None, None]

    # **잘리는 위아래를 어둡게 눌러 둔다.** 격자에서 잘린 자리가 그대로 밝으면
    # 재생 화면에서 위아래가 붕 떠 보인다 — 눌러 두면 가운데가 판으로 읽힌다
    img *= 1 - 0.62 * np.clip((TOP + 40 - yy) / (TOP + 40), 0, 1) ** 0.9
    img *= 1 - 0.62 * np.clip((yy - (TOP + TH - 40)) / (TOP + 40), 0, 1) ** 0.9
    # 글자가 앉는 아래쪽을 통째로 떨어뜨린다. 띠를 두르지 않는다
    img *= 1 - v.get('press', 0.66) * np.clip((yy - H * 0.50) / (H * 0.22), 0, 1) ** 1.1
    # **제목 자리도 눌러야 한다.** 뒤에 형광 기둥이 서 있어서 흰 글자가
    # 거기서만 먹혔다 — 띠 대신 가우시안으로 부드럽게 떨어뜨린다
    img *= 1 - 0.42 * np.exp(-((yy - (TOP + 180)) / 130.0) ** 2)

    lg = logo(58)
    if HEAD:
        paint(img, lg, W / 2 - lg.shape[1] / 2, TOP + 96, color=PAPER, a=0.94)
        paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.62, 0.14), 0.14),
              W / 2, TOP + 176, color=PAPER, a=0.92, anchor='c')
        paint(img, tmask(EV.FORMAT, BRAND, 22, 0.34), W / 2, TOP + 222,
              color=AQUA, a=0.88, anchor='c')
        if v.get('bottle'):
            from short_card import bottle_on
            bottle_on(img, TOP + 520, 480)
        # ── 훅. 커버에서 제일 큰 것 ──────────────────────
        fs = min(104, fit(HEAD, KRB, W * 0.86, 0.02))
        paint(img, tmask(HEAD, KRB, fs, 0.02), W / 2, TOP + 830, color=PAPER, anchor='c')
    else:
        # 이름이 주인공. 위는 로고만 두고 아래를 이름에 내준다
        paint(img, lg, W / 2 - lg.shape[1] / 2, TOP + 110, color=PAPER, a=0.94)
        paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.88, 0.10), 0.10),
              W / 2, TOP + 782, color=PAPER, anchor='c')
        paint(img, tmask(EV.FORMAT, BRAND, 26, 0.36), W / 2, TOP + 848,
              color=AQUA, a=0.94, anchor='c')

    l1, l2 = v['lines']
    rule(img, TOP + 918, W * 0.14, W * 0.86, PAPER, 0.26, 2)
    paint(img, tmask(l1, KR, min(40, fit(l1, KR, W * 0.86, 0.02)), 0.02),
          W / 2, TOP + 976, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(l2, KR, min(34, fit(l2, KR, W * 0.86, 0.02)), 0.02),
          W / 2, TOP + 1030, color=PAPER, a=0.76, anchor='c')

    # 상태는 왼쪽 여백선에. 가운데에 홀로 뜨면 나중에 얹은 것으로 읽힌다
    if v.get('tag', True):
        _tag(img, W * 0.085, TOP + 1140, 38, color=PAPER, accent=CORAL, width=W * 0.80)
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.22), W / 2, TOP + 1276,
          color=PAPER, a=0.70, anchor='c')

    # **격자에서 잘리는지 눈으로 못 본다** — 자리를 재서 막는다
    assert TOP + 1276 < TOP + TH - 20, '아이디 줄이 격자 밖으로 나갑니다'
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    import sys
    for name in (sys.argv[1:] or ['ad']):
        p = os.path.join(OUT, f'cover_{name}.png')
        Image.fromarray((build(name) * 255).astype(np.uint8)).save(p, optimize=True)
        print(f'{p}  {W}x{H}   격자에 보이는 구간 {TOP}~{TOP + TH}px')
