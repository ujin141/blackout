"""
AI안 — **DJ 얼굴 판.** 클럽 포스터의 가장 흔한 형식이고, 가장 잘 먹힙니다.

라인업을 글자로만 적으면 아는 이름만 읽힙니다. 얼굴을 붙이면 모르는
이름도 사람으로 남고, 무엇보다 **DJ 본인이 자기 얼굴이 걸린 판을 공유합니다** —
크루 일곱 명의 계정이 같이 움직이는 게 이 판의 진짜 목적입니다.

## 누끼 일곱 장이 서로 다르게 잘려 있다

TS·LYNN 은 전신, V 는 얼굴만, 나머지는 상반신입니다. 높이를 맞춰 나란히
놓으면 **얼굴 크기가 제각각**이라 줄로 안 보입니다.

그래서 **머리 크기를 기준으로 맞춥니다.** 사람마다 머리가 사진에서 차지하는
비율(`CUT` 의 둘째 값)을 적어 두고, 거기서 머리+어깨만큼을 잘라 칸에 채웁니다.
얼굴만 있는 V 도 전신인 TS 도 같은 크기의 얼굴로 섭니다.

값은 눈으로 맞춘 것입니다 — 알파 폭 곡선으로 목을 찾아 자동으로 잡아 보려
했는데 일곱 중 넷만 잡혔습니다(머리를 푼 사람과 얼굴 클로즈업에서 목이 안
잡힙니다). 일곱 장뿐이라 손으로 적는 쪽이 정확합니다.

## 얼굴은 칸 안에 둔다

누끼를 배경 없이 그냥 띄우면 어깨가 허공에서 잘립니다. 칸(얇은 테두리 +
아주 옅은 판)을 두면 그 자리가 사진의 가장자리로 읽혀서 잘린 게 안 보입니다.

python poster_crew.py  →  out/poster/crew_{feed,story}.png
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import (BRAND, IMG, SIZES, tmask, paint, rule, box, grain,
                        info_block, sign, save)
from fest_kit import justify, night, vignette, sky
from fonts import KR
import event as EV

INK    = np.float32([0.026, 0.027, 0.033])
PAPER  = np.float32([0.96, 0.96, 0.94])
DIM    = np.float32([0.56, 0.58, 0.62])
# **강조는 한 점뿐입니다.** 얼굴이 일곱 개나 있어서, 색까지 여러 개면
# 눈이 갈 데를 못 찾습니다. 솔로파티 한 줄에만 씁니다.
ACCENT = np.float32([1.00, 0.46, 0.30])

# (파일 이름, 머리 높이 / 사진 높이, 머리 가로 중심)
# **눈으로 맞춘 값입니다.** 고칠 일이 생기면 뽑아 놓고 보면서 고치세요 —
# 둘째 값을 키우면 그 사람 얼굴이 작아지고, 셋째 값은 좌우를 옮깁니다.
CUT = {
    'TS':    ('ts-cutout.png',    0.133, 0.47),
    'LYNN':  ('lynn-cutout.png',  0.178, 0.44),
    'V':     ('v-cutout.png',     0.780, 0.50),
    'CHIPS': ('chips-cutout.png', 0.250, 0.50),
    'HEIDY': ('heidy-cutout.png', 0.245, 0.50),
    'DEMIC': ('demic-cutout.png', 0.265, 0.49),
    'AROS':  ('aros-cutout.png',  0.390, 0.55),
}
# 머리 아래로 몇 배까지 담을지. 2.6 이면 머리 + 어깨입니다.
# 키우면 상반신이 들어오는데, 전신 사진(TS·LYNN)만 채워지고 V 는 빈 칸이 됩니다.
BODY = 2.6

ROWS = [4, 3]                      # 일곱을 넷·셋으로. 한 줄에 몰면 얼굴이 손톱만 해진다

# 라인업은 event.py 에서 온다 — 여기 다시 적으면 타임테이블과 어긋난다
ORDER = EV.LINEUP
SOLO = next((r for r in EV.TIMETABLE if r[2] in EV.PROGRAM), None)
SET_AT = {n: s for s, _, n in EV.TIMETABLE}


def crop_head(name, out_w, out_h):
    """누끼 한 장을 머리 기준으로 잘라 칸 크기에 맞춘 RGBA 를 돌려준다.

    **머리 위는 붙이고 아래는 흘린다.** 정수리를 칸 위쪽 같은 자리에 두면
    일곱 사람의 눈높이가 저절로 맞는다 — 아래는 잘려도 아무도 안 본다."""
    fn, head, hcx = CUT[name]
    im = Image.open(os.path.join(IMG, 'members', fn)).convert('RGBA')
    a = np.asarray(im, np.float32) / 255.0
    ys, xs = np.where(a[..., 3] > 0.03)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h0, w0 = a.shape[:2]

    keep = min(h0, int(round(h0 * head * BODY)))          # 머리+어깨 높이(원본 px)
    s = out_h / keep
    nw, nh = max(1, int(round(w0 * s))), max(1, int(round(h0 * s)))
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8))
                   .resize((nw, nh), Image.LANCZOS), np.float32) / 255.0

    # 칸 크기로 옮겨 담는다. 가로는 머리 중심을 칸 가운데에.
    dst = np.zeros((out_h, out_w, 4), np.float32)
    x0 = int(round(out_w / 2 - hcx * nw))
    sx0, sy0 = max(0, x0), 0
    sx1, sy1 = min(out_w, x0 + nw), min(out_h, nh)
    if sx1 > sx0 and sy1 > sy0:
        dst[sy0:sy1, sx0:sx1] = a[sy0:sy1, sx0 - x0:sx1 - x0]
    return dst


def rimlight(a_, V, thick=3.0, soft=3.4, top_fade=0.17):
    """누끼 테두리 빛 마스크.

    **두꺼우면 머리카락이 뭉개진다.** 7px 로 부풀렸더니 머리가 둥근 덩어리가
    되고 결이 통째로 사라졌다 — 빛은 실루엣을 떼어 놓는 정도면 충분하다.

    그리고 **위쪽은 죽인다.** 정수리에서 알파가 끊기는 자리를 빛이 강조하면
    거기에 가로줄이 그어진 것처럼 보인다. 머리 위에서 빛을 빼면 선이 사라지고,
    머리카락은 그대로 남는다 — 알파를 지우는 것(crown)보다 이쪽이 먼저다."""
    k = np.ones((max(3, int(thick * V)),) * 2, np.uint8)
    e = cv2.GaussianBlur(np.clip(cv2.dilate(a_, k) - a_, 0, 1), (0, 0),
                         max(1.0, soft * V))
    e = e / max(e.max(), 1e-6)
    n = e.shape[0]
    cd = max(6, int(n * top_fade))
    e[:cd] *= np.linspace(0.0, 1.0, cd, dtype=np.float32)[:, None] ** 0.9
    return e


def crown(al):
    """정수리를 위로 갈수록 흐리게. **누끼가 잘린 걸 감춘다.**

    누끼는 머리 꼭대기에서 알파가 일직선으로 끝난다. 거기에 테두리 빛까지
    얹히면 **가로줄이 그어진 것처럼** 보인다 — '머리 위가 잘린 느낌' 이 이거다.

    페이드 길이는 **원본이 얼마나 잘렸는지에 따라 정한다.** 맨 윗줄이
    채워져 있을수록(= 사진에서 정수리가 잘려 나갔을수록) 길게 녹인다.
    TS 는 첫 줄이 5.6% 차 있어서 짧게 주면 여전히 선이 보인다."""
    al = al.copy()
    n = al.shape[0]
    clipped = float((al[0] > 0.5).mean())
    # **길게 주면 머리카락이 지워진다.** 테두리 빛을 위에서 죽이는 게
    # 먼저고(rimlight), 이건 원본이 실제로 잘린 만큼만 거든다
    cd = max(3, int(n * (0.012 + clipped * 0.85)))
    cd = min(cd, n)
    al[:cd] *= np.linspace(0.0, 1.0, cd, dtype=np.float32)[:, None] ** 0.65
    return al


def cell(img, name, x0, y0, w, h, V):
    """칸 하나 — 옅은 판, 위에서 내리는 빛, 사람, 테두리, 이름, 시간."""
    x1, y1 = x0 + w, y0 + h
    box(img, x0, y0, x1, y1, np.float32([0.052, 0.054, 0.064]), 1.0)
    # 위에서 내리는 빛 한 겹. 검정 옷이 검정 판에 먹히는 걸 막는다
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img[y0:y1, x0:x1] += (1 - yy) ** 2 * np.float32([0.075, 0.078, 0.092])

    fig = crop_head(name, w, h)
    rgb, al = fig[..., :3], fig[..., 3:4]
    g = (rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114)[..., None]
    g = np.clip((g - 0.5) * 1.20 + 0.5, 0, 1)             # 흑백 + 대비
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + np.repeat(g, 3, 2) * al

    # 얇은 테두리. **이게 있어야 잘린 어깨가 사진의 가장자리로 읽힌다**
    t = max(1, int(1.4 * V))
    rule(img, y0, x0, x1, PAPER, 0.22, t)
    rule(img, y1 - t, x0, x1, PAPER, 0.22, t)
    box(img, x0, y0, x0 + t, y1, PAPER * 0.22 + img[y0:y1, x0:x0 + t].mean(axis=(0, 1)) * 0.78)
    box(img, x1 - t, y0, x1, y1, PAPER * 0.22 + img[y0:y1, x1 - t:x1].mean(axis=(0, 1)) * 0.78)

    cx = x0 + w / 2
    ns = min(int(26 * V), int(justify(name, w * 0.86, 0.14, cap=int(26 * V))))
    paint(img, tmask(name, BRAND, ns, 0.14), cx, y1 + 30 * V, color=PAPER, anchor='c')
    paint(img, tmask(SET_AT[name], BRAND, int(14 * V), 0.20), cx, y1 + 58 * V,
          color=DIM, a=0.85, anchor='c')


def build(W, H, story=False, safe=False):
    """`safe` 는 인스타 스토리용 — 위아래를 UI 가 먹는 만큼 비운다.

    **9:16 이라고 다 스토리가 아니다.** 그냥 뽑은 판을 스토리에 올리면
    프로필 줄이 눈썹을, 답장 막대가 계정 아이디를 먹는다 — 재 보니
    아래 10% 안에 서명이 들어가 있었다. 여기서는 판 전체를 10~86% 안으로
    몰아 넣는다."""
    V = W / 1080.0
    # 판이 실제로 쓰는 세로 구간. 아래 계산은 전부 이 두 값에서 나온다
    y0, y1 = (H * 0.100, H * 0.862) if safe else (0.0, float(H))
    BH = y1 - y0
    img = sky(W, H, [(0.0, (0.062, 0.064, 0.078)), (0.5, (0.030, 0.031, 0.039)),
                     (1.0, (0.018, 0.019, 0.025))])
    M = int(W * 0.072)
    CW = W - M * 2

    # ── 머리 ─────────────────────────────────────────────
    y = y0 + BH * (0.062 if story else 0.070)
    paint(img, tmask('BLACKOUT CREW PRESENTS', BRAND, int(19 * V), 0.42),
          W / 2, y, color=DIM, a=0.85, anchor='c')

    ny = y0 + BH * (0.130 if story else 0.148)
    ns = justify(EV.NAME, CW, 0.08, cap=int(146 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(21 * V), 0.32),
          W / 2, ny + ns * 0.80, color=PAPER, a=0.72, anchor='c')

    # ── 얼굴 판 ──────────────────────────────────────────
    # **아래에서부터 거꾸로 잡는다.** 처음엔 칸 자리를 비율로 박아 뒀는데,
    # 피드(1080×1350)에서 정보 블록이 협업 브랜드 줄 위로 올라타 글자가 겹쳤다 —
    # 세로가 350px 짧으면 같은 비율이 같은 자리가 아니다.
    # 발치·정보·솔로가 쓸 높이를 먼저 빼고, 남는 만큼만 얼굴에 준다.
    foot_h = 88 * V                                   # 협업 줄 + 서명
    step = (36 if story else 31) * V                  # 정보 줄 간격
    info_h = step * 6.28 + 40 * V                     # info_block 이 쓰는 높이
    # **솔로파티 줄과 정보 블록이 겹쳤다.** 날짜(2026.08.29. SAT.)는 베이스라인
    # 기준으로 찍혀서 위로 글자가 올라온다 — 그 높이까지 계산에 넣는다
    solo_h = 148 * V
    name_h = (74 if story else 62) * V                # 이름 + 시간
    gap = 15 * V
    top = y0 + BH * (0.235 if story else 0.222)
    gbot = y1 - foot_h - info_h - solo_h - (42 if story else 30) * V

    n = len(ROWS)
    ch = (gbot - top - gap * 1.5 * (n - 1) - name_h * n) / n
    # 피드는 세로가 짧다. 4:5 를 고집하면 칸이 좁아져 얼굴이 손톱만 해진다 —
    # 조금 정사각에 가깝게 눕혀서 폭을 번다
    ratio = 0.80 if story else 0.88
    cw = min(ch * ratio, (CW - gap * (max(ROWS) - 1)) / max(ROWS))
    ch = cw / ratio

    i = 0
    block = (ch + name_h) * n + gap * 1.5 * (n - 1)
    yy = top + max(0.0, (gbot - top - block) / 2)      # 남는 세로는 위아래로 나눈다
    for cols in ROWS:
        row_w = cw * cols + gap * (cols - 1)
        xx = (W - row_w) / 2
        for _ in range(cols):
            cell(img, ORDER[i], int(xx), int(yy), int(cw), int(ch), V)
            xx += cw + gap
            i += 1
        yy += ch + name_h + gap * 1.5

    # ── 솔로파티 ─────────────────────────────────────────
    # **DJ 가 아니라 프로그램이라 칸에 안 들어간다.** 그런데 이 행사가 파는 건
    # 라인업이 아니라 이 90분이라, 얼굴 판 바로 아래 한 줄로 세운다.
    if SOLO:
        rule(img, gbot + 20 * V, M, W - M, PAPER, 0.16, max(1, int(1 * V)))
        paint(img, tmask(SOLO[2], BRAND, int(34 * V), 0.16), W / 2, gbot + 58 * V,
              color=ACCENT, anchor='c')
        paint(img, tmask(f'{SOLO[0]} — {SOLO[1]}   {EV.TAGLINE}', KR, int(19 * V), 0.02),
              W / 2, gbot + 96 * V, color=PAPER, a=0.78, anchor='c')

    # ── 정보 ─────────────────────────────────────────────
    end = info_block(img, M, gbot + solo_h + 8 * V, CW, V, DIM, PAPER,
                     head_color=PAPER, head=32, key=14, val=19, step=step)

    # ── 발치 ─────────────────────────────────────────────
    # **비율로 박지 않는다.** 정보가 끝난 자리에서 이어야 판 크기가 달라져도
    # 협업 줄이 잔글씨 위로 올라타지 않는다
    fy = max(end + 44 * V, y1 - 58 * V)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.28), W / 2, fy - 32 * V,
          color=DIM, a=0.58, anchor='c')
    sign(img, W / 2, fy, size=int(15 * V), color=PAPER, a=0.86, anchor='c')

    vignette(img, 0.32, 2.4)
    grain(img, 0.006, 6)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'crew_{k}')
        save(im, f'crew_{k}')
    # 인스타 스토리에 그대로 올리는 판. 위아래를 UI 만큼 비웠다
    im = build(1080, 1920, True, safe=True)
    night(im, 'crew_story_ig')
    save(im, 'crew_story_ig')
