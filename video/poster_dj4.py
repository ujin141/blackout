"""
**DJ 한 명짜리 판 — D안.** 우진이 준 레퍼런스(월디페 ANYMA 판) 문법.

    python poster_dj4.py                 일곱 명 전부
    python poster_dj4.py lynn chips      골라서

레퍼런스 세 장(WDJF ANYMA · CLUB LIVEN × DUO · SUNDAY NIGHT)에서 공통으로
지키고 있는 것만 뽑았습니다. 우리 A·B·C안이 셋 다 안 하고 있던 것들입니다.

    정사각          1:1. 클럽·페스티벌 게스트 판은 세로가 아니라 정사각이다
    폭발 배경       인물 뒤가 비어 있지 않다. 성운 · 파편 · 방사형 빛으로 꽉 찬다
    이름은 가슴께   판 가운데가 아니라 인물 가슴 위에 얹는다. 얼굴을 안 가린다
    흰 정보 띠      아래를 흰 띠로 끊고 그 안에 행사·장소·날짜를 칸으로 나눈다
    잔글씨 줄       맨 아래 한 줄 — 연령 고지 · 계정. 이게 있어야 진짜 판으로 보인다

C안(`poster_dj3.py`)의 크롬 이름은 여기서 안 씁니다. 레퍼런스는 전부
**그냥 굵은 흰 글자**입니다 — 배경이 화려할수록 글자는 단순해야 읽힙니다.

## 배경을 코드로 만든다

성운은 노이즈 두 겹을 다른 크기로 흐려 겹치고, 가운데에서 멀어질수록
꺼뜨립니다. 파편은 다각형을 뿌리되 **가까운 것일수록 크고 흐리게** 합니다 —
크기만 다르고 초점이 같으면 벽지가 되고 공간이 안 됩니다.
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, fit, rule, box, glow, grain,
                        outline, save, sign, bloom)
from poster_crew import crop_head, crown, rimlight, rimlight
from fest_kit import justify, night, vignette, rays, specks, haze
from fonts import KR, KRB
from members import get
from poster_dj import HUE, LINE
from poster_dj2 import MATE
import event as EV

PAPER = np.float32([0.98, 0.98, 0.97])
INK   = np.float32([0.045, 0.045, 0.050])
DIM   = np.float32([0.62, 0.64, 0.68])

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}

SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}


def nebula(W, H, cx, cy, c1, c2, seed, spread=0.70):
    """인물 뒤 성운. **노이즈 한 겹으로는 구름이 안 된다** — 큰 덩어리와
    잔결을 따로 만들어 겹쳐야 깊이가 생긴다.

    색은 **세 단계로 간다.** 옅은 데는 짝색, 짙어지면 자기 색, 제일 밝은
    심지만 흰빛 — 한 색으로 밝기만 올리면 물감 뿌린 판이 되고 빛이 안 된다.
    구름 결도 두 겹이 아니라 세 겹이라야 가까운 결과 먼 결이 갈린다."""
    rng = np.random.default_rng(seed)
    def layer(s, sig):
        n = rng.standard_normal((max(2, int(H * s)), max(2, int(W * s)))).astype(np.float32)
        n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
        return cv2.GaussianBlur(n, (0, 0), sig)
    f = layer(0.035, W * 0.022) + layer(0.09, W * 0.008) * 0.55         + layer(0.20, W * 0.0032) * 0.26
    f = (f - f.min()) / (f.max() - f.min() + 1e-6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / (W * spread)) ** 2 + ((yy - cy) / (H * spread)) ** 2)
    m = np.clip(1 - r, 0, 1) ** 1.5
    # **문턱을 높게 잡아야 구름이 된다.** 낮으면 판 전체가 뿌옇게 뜨고
    # 인물이 안개 속에 선 꼴이 된다 — 검은 데가 넓어야 밝은 데가 산다
    # 0.70 이면 구름이 판을 다 덮어서 인물이 묻힌다. 문턱을 올릴수록
    # 검은 데가 넓어지고 남은 구름이 또렷해진다
    v = np.clip(f * 2.25 - 0.92, 0, 1) * m
    hot = np.float32([1.0, 1.0, 1.0])
    return (v[..., None] * c2 * 0.62
            + (v ** 1.9)[..., None] * c1 * 1.15
            + (v ** 4.5)[..., None] * hot * 0.85)


def debris(img, n, cx, cy, color, seed, rmin, rmax):
    """떠 있는 파편. **가까운 것일수록 크고 흐리다** — 크기만 다르고 초점이
    같으면 벽지가 되고 공간이 안 된다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ang = rng.uniform(0, 2 * np.pi)
        d = rng.uniform(0.16, 1.05)
        x = cx + np.cos(ang) * d * W * 0.62
        y = cy + np.sin(ang) * d * H * 0.58
        size = rng.uniform(rmin, rmax) * (0.35 + d * 1.5)
        k = rng.integers(5, 8)
        a = np.sort(rng.uniform(0, 2 * np.pi, k))
        pts = np.stack([x + np.cos(a) * size * rng.uniform(0.55, 1.0, k),
                        y + np.sin(a) * size * rng.uniform(0.55, 1.0, k)], 1).astype(np.int32)
        lay = np.zeros((H, W), np.float32)
        cv2.fillPoly(lay, [pts], 1.0)
        # **테두리에 빛을 물린다.** 면만 칠하면 종잇조각이고, 가장자리가
        # 밝아야 뒤에서 빛을 받는 돌조각으로 읽힌다
        lit = np.zeros((H, W), np.float32)
        cv2.polylines(lit, [pts], True, 1.0, max(1, int(size * 0.10)))
        blur = max(0.8, size * (0.05 + d * 0.22))
        lay = cv2.GaussianBlur(lay, (0, 0), blur)
        lit = cv2.GaussianBlur(lit, (0, 0), blur * 0.6)
        img += lay[..., None] * color * rng.uniform(0.10, 0.30)
        img += lit[..., None] * (color * 0.35 + 0.65) * rng.uniform(0.16, 0.42)


def fringe(img, amt):
    """색수차 — 빨강과 파랑을 아주 조금 다른 배율로 민다.

    **이게 있고 없고가 '렌즈로 찍은 것' 과 '컴퓨터로 그린 것' 을 가른다.**
    양은 눈에 안 보일 만큼만. 보이면 그냥 인쇄 사고다."""
    H, W = img.shape[:2]
    def scale(ch, k):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + k)
        return cv2.warpAffine(ch, M, (W, H), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
    img[..., 0] = scale(img[..., 0], amt)
    img[..., 2] = scale(img[..., 2], -amt)


def melt(a_, px, frac=0.36, seed=0, V=1.0):
    """발치를 **직선으로 자르지 않는다.**

    가로 그라데이션만 주면 자로 자른 것처럼 보인다 — 누끼가 딱 끊긴 느낌이
    나는 게 이거다. 셋을 같이 한다.

        경계를 흔든다   노이즈를 섞어 사라지는 선이 일직선이 아니게
        같이 어둡게     사라지는 구간을 어둡게 해야 '잘린' 게 아니라
                        '어둠 속으로 들어간' 것이 된다
        가장자리 깃털   알파를 아주 조금 흐려 하드 엣지를 없앤다
    """
    n, w = a_.shape
    a_ = crown(a_)          # 정수리를 녹인다 — poster_crew.crown 참고
    fd = max(8, int(n * frac))
    t = np.linspace(0, 1, fd, dtype=np.float32)[:, None]
    rng = np.random.default_rng(seed)
    nz = rng.random((max(2, fd // 12), max(2, w // 12))).astype(np.float32)
    nz = cv2.resize(cv2.GaussianBlur(nz, (0, 0), 1.6), (w, fd),
                    interpolation=cv2.INTER_CUBIC)
    nz = (nz - nz.min()) / (float(np.ptp(nz)) + 1e-6)
    a_[n - fd:] *= np.clip(1.0 - t ** 1.05 * 1.38 + (nz - 0.5) * 0.98 * t, 0, 1)
    px[n - fd:] *= (1 - t * 0.74)[..., None]
    a_ = cv2.GaussianBlur(a_, (0, 0), max(0.8, 1.3 * V))
    return a_, px


def sharpen(a, sigma, amt):
    """언샤프 마스크. 누끼를 키워 얹으면 흐려진다 — 얼굴이 또렷해야 산다."""
    return np.clip(a + (a - cv2.GaussianBlur(a, (0, 0), sigma)) * amt, 0, 1)


def chip(img, text, x, y, h, font, size, fg, bg, V, pad=None, track=0.10):
    """정보 띠 안의 칸 하나. 돌려주는 값은 오른쪽 끝 x."""
    m = tmask(text, font, size, track)
    pad = int(size * 0.85) if pad is None else pad
    w = m.shape[1] + pad * 2
    if bg is not None:
        box(img, x, y - h / 2, x + w, y + h / 2, bg)
    paint(img, m, x + pad, y, color=fg, anchor='l')
    return x + w


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    BH = y1 - y0
    M = int(W * 0.055)
    tall = H > W * 1.2                                 # 9:16 이면 인물을 더 키운다

    # 아래 두 띠는 판 크기와 상관없이 같은 두께다 — 잔글씨는 줄어들면 안 읽힌다
    fine_h = 40 * V
    bar_h = 92 * V
    bar_y = y1 - fine_h - bar_h / 2

    img = np.repeat(np.repeat(np.float32([0.014, 0.013, 0.020])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 배경 ─────────────────────────────────────────────
    # **스토리는 구름을 판 전체에 깐다.** 안전영역 안에만 두면 흰 띠
    # 아래가 까맣게 비어서, 인물을 아무리 키워도 여백으로 읽힌다
    cx = W * 0.50
    cy = (H * 0.44) if safe else (y0 + BH * 0.36)
    img += nebula(W, H, cx, cy, C2 * 0.55 + C * 0.45, C,
                  seed=len(name) * 13 + 4, spread=0.98 if safe else 0.70)
    rays(img, cx, cy, 26, int(40 * V), int((H if safe else BH) * 0.80),
         C * 0.6 + PAPER * 0.4, 0.055, phase=0.11, duty=0.34)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - cx) / (W * 0.30)) ** 2
                    + ((yy - cy) / (BH * 0.20)) ** 2))[..., None] * (C * 0.7 + PAPER * 0.3) * 0.13
    debris(img, 40 if safe else 34, cx, cy, PAPER * 0.40 + C * 0.60,
           len(name) * 7 + 1, 9 * V, 44 * V)
    # 무대 연기. 빔이 공기를 통과하는 게 보여야 무대가 된다
    haze(img, int(H * 0.30), int(H * 0.92), C * 0.75 + PAPER * 0.25, 0.085,
         seed=len(name) * 3 + 6)

    # ── 사람 ─────────────────────────────────────────────
    # **스토리는 판이 프레임을 꽉 채워야 한다.** 안전영역 안에서만 그렸더니
    # 위아래에 검은 띠가 남았다(우진 지적 두 번). 그림은 가장자리까지 가고,
    # UI 를 피하는 건 글자뿐이다 — 인물도 흰 띠 아래로 이어진다
    # **인물 자리는 판 세로(H) 기준으로 잡는다.** 안전영역(BH) 기준으로 잡으면
    # 정사각과 스토리에서 구도가 달라진다 — 같은 비율을 쓰면 두 판이 한 세트로
    # 보인다. 0.86 까지 키웠을 땐 정수리가 프레임에 붙고 배경이 다 가려졌다.
    # 레퍼런스도 인물은 판의 절반 남짓이고 위아래로 배경이 넉넉하다
    hero_h = int(H * 0.668)
    top = int(H * 0.108)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = al[:n].copy()
    # 누끼 가장자리의 반투명 잔털을 깎는다. 어두운 판에서 회색 테로 보인다
    a_ = np.clip((a_ - 0.07) / 0.93, 0, 1)


    # 인물 뒤 그림자 — 배경이 밝아서 이게 없으면 사람이 배경에 먹힌다
    back = cv2.GaussianBlur(a_, (0, 0), 26 * V)
    img[sl] *= (1 - back[..., None] * 0.84)

    # 테두리 빛. **좌우를 다른 색으로 나눈다** — 한 색이면 윤곽선이고,
    # 두 색이면 양쪽에서 조명 두 대가 때리는 것이 된다.
    # 0.85 로 또렷하게 줬더니 오려 붙인 스티커로 보였다 — 빛은 번져야 빛이다
    edge = rimlight(a_, V)          # 얇게, 위쪽은 죽인다 — poster_crew 참고
    lr = np.linspace(0, 1, W, dtype=np.float32)[None, :, None] ** 0.8
    two = C2[None, None, :] * (1 - lr) + C[None, None, :] * lr
    img[sl] += edge[..., None] * (two * 0.72 + PAPER * 0.28) * 0.55

    # **사진은 사진 그대로 둔다.** 흑백으로 바꾸고 색을 덮으면 판의 색과
    # 사람이 한 덩어리가 되어서, 누가 서 있는지가 아니라 무슨 색인지가
    # 먼저 읽힌다. 사람은 실사로 두고 **테두리만** 판의 색을 준다.
    # ── 이름 (인물 뒤) ───────────────────────────────────
    # **이름을 사람 뒤로 넘긴다.** 위에만 얹으면 스티커고, 뒤로 넘기면
    # 사람이 글자 앞으로 걸어 나온 것이 된다 — 이 한 겹이 제일 크게 먹는다.
    # 0.655 는 인물 가슴께다. 0.60 에 뒀더니 흰 띠까지 아래가 뻥 뚫렸다
    ny = H * 0.655
    ns = justify(name, W * 0.86, 0.01, cap=int(215 * V))
    nm = tmask(name, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.026)),) * 2))
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 12 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 9 * V,
          color=np.float32([0, 0, 0]), a=0.62, anchor='c')
    paint(img, nm, W / 2, ny, color=PAPER, anchor='c')

    # 손도 안 댄다 — 대비도 노출도 원본 그대로. 흐린 것만 되살린다
    px = sharpen(np.clip(fig[..., :3], 0, 1), 2.4 * V, 0.60)[:n].copy()
    a_, px = melt(a_, px, 0.36, len(name) * 31 + 2, V)
    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None]

    # 발치. 정사각은 흰 띠 바로 위에서 끊고, 스토리는 판 아래 끝에서 녹인다
    # 스토리는 흰 띠 안에서 인물이 끝난다 — 레퍼런스도 띠가 인물을 자른다
    cut = int(bar_y + bar_h * 0.2) if safe else int(bar_y - bar_h * 0.5 - 26 * V)
    fade = int((H * 0.14) if safe else (BH * 0.13))
    if cut - fade > 0:
        t = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.4
        img[cut - fade:cut] *= (1 - t * (0.80 if safe else 0.96))
    if not safe:
        img[cut:int(y1)] *= 0.42

    # ── 이름 ─────────────────────────────────────────────
    # **가슴께에 얹는다.** 판 가운데에 두면 얼굴을 가리고, 아래로 내리면
    # 흰 띠에 붙는다 — 레퍼런스는 전부 가슴 위다
    # 이름은 인물보다 **먼저** 그렸다(아래 참고). 여기서는 인물 위로
    # 아주 옅게 한 번 더 얹어, 글자가 사람을 투과하는 것처럼 보이게 한다
    # **사람에 가린 구간이 흐릿했다.** 알파만 올리면 뒤로 넘긴 느낌이
    # 죽는다 — 면은 반투명으로 두고 **윤곽선만 또렷하게** 한 겹 더 얹는다.
    # 글자는 속이 아니라 테두리로 읽힌다
    paint(img, nm, W / 2, ny, color=PAPER, a=0.58, anchor='c')
    paint(img, outline(nm, max(2, int(3.6 * V))), W / 2, ny, color=PAPER,
          a=0.94, anchor='c')

    # ── 머리 ─────────────────────────────────────────────
    s, e = SET_AT[name]
    sign(img, M, y0 + 44 * V, size=int(13 * V), color=PAPER, a=0.92, anchor='l')
    paint(img, tmask(f'{s} — {e}', BRAND, int(20 * V), 0.20), W - M, y0 + 44 * V,
          color=PAPER, a=0.92, anchor='r')

    # ── 흰 정보 띠 ───────────────────────────────────────
    box(img, 0, bar_y - bar_h / 2, W, bar_y + bar_h / 2, PAPER)
    x = M
    x = chip(img, EV.NAME, x, bar_y, bar_h, BRAND, int(31 * V), INK, None, V,
             pad=int(6 * V), track=0.13)
    x += 22 * V
    x = chip(img, '양재', x, bar_y, bar_h * 0.62, KRB, int(24 * V), PAPER, INK, V)
    x += 14 * V
    x = chip(img, EV.VENUE, x, bar_y, bar_h, KR, int(21 * V), INK * 3.2, None, V,
             pad=int(8 * V), track=0.02)
    # 날짜는 오른쪽 끝에 색 박스로. **판에서 두 번째로 큰 정보가 날짜다**
    dm = tmask('8/29 SAT', BRAND, int(28 * V), 0.10)
    dw = dm.shape[1] + 40 * V
    box(img, W - M - dw, bar_y - bar_h * 0.34, W - M, bar_y + bar_h * 0.34, C * 0.85)
    paint(img, dm, W - M - dw / 2, bar_y, color=PAPER, anchor='c')

    # ── 잔글씨 줄 ────────────────────────────────────────
    fy = y1 - fine_h / 2
    # 스토리에서는 반투명으로 깐다 — 아래로 그림이 비쳐야 띠가 판의
    # 끝이 아니라 판 위에 얹힌 줄로 읽힌다
    box(img, 0, y1 - fine_h, W, y1, INK * 0.5, 1.0 if not safe else 0.80)
    left = f'19+  {EV.AGE}'
    paint(img, tmask(left, KR, int(15 * V), 0.02), M, fy, color=DIM, a=0.92, anchor='l')
    paint(img, tmask(f'{EV.ENTRY}   ·   {EV.HANDLE}', KR, int(15 * V), 0.02),
          W - M, fy, color=DIM, a=0.92, anchor='r')

    # ── 곁들이 ───────────────────────────────────────────
    gs = get(name)['genres']['ko'][:3]
    ig = get(name)['instagram']
    # **이름 바로 밑에 붙인다.** 아래로 내리면 인물 발치가 어두워지는
    # 구간에 들어가서, 흰 글자인데도 회색으로 읽힌다
    sy = ny + ns * 0.55
    paint(img, tmask(LINE[name], KRB, int(29 * V), 0.01), W / 2, sy, color=PAPER,
          anchor='c')
    bits = [b for b in ('  /  '.join(gs), '@' + ig if ig else '') if b]
    if bits:
        paint(img, tmask('     ·     '.join(bits), KR, int(18 * V), 0.02), W / 2,
              sy + 36 * V, color=PAPER, a=0.84, anchor='c')

    if safe:
        # 흰 띠 아래로 흐르는 바닥 반사. 구름만으로는 발치가 심심하다
        gy = np.arange(H, dtype=np.float32)
        gx = np.arange(W, dtype=np.float32)
        spill = (np.exp(-((gy - H * 0.955) / (H * 0.085)) ** 2)[:, None]
                 * np.exp(-((gx - W * 0.5) / (W * 0.62)) ** 2)[None, :])
        img += spill[..., None] * C * 0.22
        # **아무것도 덮지 않는다.** 처음엔 0 으로 잘라냈고, 다음엔 단색으로
        # 채웠는데 둘 다 '검은 여백' 으로 보였다. 그림이 끝까지 가면
        # 여백이라는 게 아예 없다 — 글자만 UI 를 피해 앉아 있으면 된다.
        rule(img, int(y1), 0, W, C, 0.50, max(1, int(2 * V)))

    specks(img, 140, 0, int(y1), PAPER, 0.20, seed=len(name) * 5 + 9, rmax=2.6)
    bloom(img, 0.82, 16 * V, 0.22, PAPER)
    fringe(img, 0.0016)
    vignette(img, 0.46, 2.0)
    grain(img, 0.005, 13)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj4_{key}_{k}')
            save(im, f'dj4_{key}_{k}')
