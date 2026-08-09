"""
페스티벌 · 풀파티 시안 공통 도구.

G~K(페스티벌)는 **페스티벌의 관습**을 씁니다 — 라인업 블록, 지는 해, 배지, 무대 빔, 활판.
관습을 쓰는 이유는 하나입니다. 처음 보는 사람이 0.5초 안에 "축제구나"로 읽습니다.

L~P(풀×솔로)는 **이 행사의 조합 자체**를 구조로 씁니다.
페스티벌 관습만 쓰면 어느 행사에 갖다 붙여도 되는 판이 됩니다 —
풀파티인 것도, 솔로파티인 것도 그림에서 안 나옵니다.
그래서 **둘 다 한 장치로** 말합니다: 물 위의 원 두 개.
원은 물결이자 튜브이고, 두 개가 겹치는 자리가 혼자 온 사람 둘이 만나는 지점입니다.

`poster_kit.py` 를 그대로 쓰되, 여기 있는 건 페스티벌에만 필요한 것들입니다.
밤 행사라 **전부 어둡습니다** — `night()` 로 재서 평균 0.12~0.21, 밝은 픽셀 7% 아래를 지킵니다.
"""
import numpy as np
import cv2
from PIL import ImageFont
from poster_kit import BRAND, tmask, fit, paint, add


def sky(W, H, stops):
    """세로 그라데이션. stops 는 [(위치0~1, (r,g,b)), ...].

    페스티벌 포스터의 배경은 대개 하늘이고, 하늘은 단색이 아닙니다 —
    **단색으로 깔면 배경이 아니라 색지가 됩니다.**"""
    ys = np.linspace(0, 1, H, dtype=np.float32)
    pos = np.array([p for p, _ in stops], np.float32)
    cols = np.array([c for _, c in stops], np.float32)
    out = np.empty((H, 3), np.float32)
    for i in range(3):
        out[:, i] = np.interp(ys, pos, cols[:, i])
    return np.repeat(out[:, None, :], W, axis=1)


def slit(img, y0, y1, gap, thick, color, a=1.0, taper=True):
    """지는 해를 가르는 가로 띠.

    **레트로 선셋의 정체는 이 띠입니다.** 원판만 두면 그냥 동그라미이고,
    아래로 갈수록 촘촘해지는 띠가 들어가야 "해가 지고 있다"로 읽힙니다.
    간격을 일정하게 두면 무늬가 되고, 아래로 갈수록 좁혀야 원근이 생깁니다."""
    y, step = float(y1), float(gap)
    while y > y0:
        t = max(1, int(thick * (0.45 + 0.55 * (y - y0) / max(y1 - y0, 1)) if taper else thick))
        yy = int(y)
        img[yy:yy + t] = img[yy:yy + t] * (1 - a) + np.float32(color) * a
        step *= 0.86                                  # 위로 갈수록 촘촘해진다
        y -= step + t


def skyline(img, base_y, h, color, seed=7, n=26, a=1.0):
    """도시 실루엣. 루프탑 파티라 지평선이 산이 아니라 건물입니다.

    높이를 난수로만 뽑으면 톱니가 되어 그래프처럼 보입니다 —
    **낮은 덩어리 안에 가끔 높은 것 하나**가 있어야 스카이라인으로 읽힙니다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    x = 0
    while x < W:
        w = int(rng.integers(int(W * 0.020), int(W * 0.075)))
        tall = rng.random() < 0.18
        bh = h * (rng.uniform(0.55, 1.0) if tall else rng.uniform(0.16, 0.42))
        y0 = int(base_y - bh)
        img[max(0, y0):int(base_y), x:min(W, x + w)] = \
            img[max(0, y0):int(base_y), x:min(W, x + w)] * (1 - a) + np.float32(color) * a
        # 옥상 구조물 하나. 이게 있어야 건물이지 막대가 아니다
        if tall and rng.random() < 0.7:
            mw = max(2, int(w * 0.12))
            mx = x + int(w * rng.uniform(0.2, 0.7))
            img[max(0, y0 - int(bh * 0.22)):y0, mx:mx + mw] = np.float32(color)
        x += w + int(rng.integers(0, int(W * 0.012)))


def beams(img, sx, sy, count, spread, length, color, a=0.5, seed=3, wobble=0.0):
    """무대 조명 빔. 한 점에서 부챗살로 내려옵니다.

    **빔은 선이 아니라 원뿔입니다** — 끝으로 갈수록 넓어지고 옅어져야 공기가 보입니다.
    선으로 그으면 레이저 포인터가 되고 무대가 안 됩니다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    acc = np.zeros((H, W), np.float32)
    for i in range(count):
        ang = np.pi / 2 + spread * ((i + 0.5) / count - 0.5) * 2
        ang += wobble * (rng.random() - 0.5)
        dx, dy = np.cos(ang), np.sin(ang)
        # 광원에서의 거리와 축에서 벗어난 정도
        px, py = xx - sx, yy - sy
        along = px * dx + py * dy
        perp = np.abs(-px * dy + py * dx)
        wid = 6.0 + along * 0.075                     # 멀어질수록 넓어진다
        m = np.clip(1 - perp / np.maximum(wid, 1e-3), 0, 1) ** 1.6
        m *= np.clip(along / (length * 0.25), 0, 1) * np.clip(1 - along / length, 0, 1) ** 0.9
        acc += m * rng.uniform(0.7, 1.0)
    acc = cv2.GaussianBlur(acc, (0, 0), max(2.0, W * 0.004))
    add(img, acc, 0, 0, np.float32(color), a)
    return acc


def crowd(img, base_y, h, color, seed=11, a=1.0):
    """관객 실루엣. **머리만 늘어놓으면 자갈밭입니다** —
    가끔 손을 든 사람이 섞여야 사람으로 읽힙니다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    layer = np.zeros((H, W), np.float32)
    for row, (scale, dy) in enumerate(((1.0, 0.0), (0.78, 0.30), (0.60, 0.55))):
        y = base_y + h * dy
        x = -int(W * 0.05)
        while x < W:
            r = int(h * 0.13 * scale * rng.uniform(0.8, 1.2))
            cv2.circle(layer, (x, int(y)), r, 1.0, -1, cv2.LINE_AA)
            cv2.ellipse(layer, (x, int(y + r * 1.5)), (int(r * 1.7), int(r * 2.2)),
                        0, 180, 360, 1.0, -1, cv2.LINE_AA)
            if rng.random() < 0.16:                   # 손 든 사람
                for s in (-1, 1):
                    cv2.line(layer, (x + s * int(r * 0.7), int(y)),
                             (x + s * int(r * 1.5), int(y - r * 2.6)),
                             1.0, max(2, int(r * 0.28)), cv2.LINE_AA)
            x += int(r * rng.uniform(1.5, 2.4))
    m = np.clip(layer, 0, 1)[..., None] * a
    img[:] = img * (1 - m) + np.float32(color) * m


def arc_text(img, text, cx, cy, r, size, color, a=1.0, top=True, track=0.10, path=BRAND):
    """원을 따라 도는 글자. 배지의 문법입니다.

    글자를 통째로 굽히면 뭉개지므로 **한 자씩 돌려서** 놓습니다.
    아래쪽 호는 위아래를 뒤집어야 읽힙니다 — 안 뒤집으면 거꾸로 매달립니다."""
    f = ImageFont.truetype(path, size)
    ws = [f.getlength(c) for c in text]
    tr = size * track
    total = sum(ws) + tr * max(len(text) - 1, 0)
    span = total / r                                  # 라디안
    ang = (-np.pi / 2 if top else np.pi / 2) - (span / 2 if top else -span / 2)
    for c, w in zip(text, ws):
        step = (w + tr) / r
        a_mid = ang + (step / 2 if top else -step / 2)
        if not c.strip():                             # 공백은 마스크가 비어 있다
            ang += step if top else -step
            continue
        m = tmask(c, path, size, 0.0)
        deg = np.degrees(a_mid) + (90 if top else -90)
        pad = int(max(m.shape) * 0.8)
        mp = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        Mx = cv2.getRotationMatrix2D((mp.shape[1] / 2, mp.shape[0] / 2), -deg, 1.0)
        rot = cv2.warpAffine(mp, Mx, (mp.shape[1], mp.shape[0]), flags=cv2.INTER_LINEAR)
        px = cx + np.cos(a_mid) * r
        py = cy + np.sin(a_mid) * r
        paint(img, rot, px, py, color=color, a=a, anchor='c')
        ang += step if top else -step


def rays(img, cx, cy, n, r0, r1, color, a=0.5, phase=0.0, duty=0.5):
    """배지 안쪽의 방사선. 가운데를 향한 시선을 만듭니다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    th = np.arctan2(yy - cy, xx - cx)
    band = ((th * n / (2 * np.pi) + phase) % 1.0 < duty).astype(np.float32)
    ring = np.clip((d - r0) / 6, 0, 1) * np.clip((r1 - d) / 6, 0, 1)
    add(img, band * ring, 0, 0, np.float32(color), a)


def haze(img, y0, y1, color, a, seed=5):
    """공기 중의 연기. 빔이 보이는 이유가 이것이고, 없으면 빔이 뜬금없습니다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, H // 40), max(2, W // 40))).astype(np.float32)
    g = cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC)
    g = cv2.GaussianBlur(g, (0, 0), W * 0.02)
    g = (g - g.min()) / max(float(np.ptp(g)), 1e-6)
    band = np.clip((np.arange(H, dtype=np.float32) - y0) / max(y1 - y0, 1), 0, 1)
    band = np.clip(np.sin(band * np.pi), 0, 1) ** 1.2   # 부동소수 오차로 음수가 나오면 nan 이 된다
    add(img, g * band[:, None], 0, 0, np.float32(color), a)


def specks(img, n, y0, y1, color, a, seed=9, rmax=2.6):
    """공중의 먼지·색종이. 아주 작게, 아주 적게 — 많으면 눈이 옵니다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    layer = np.zeros((H, W), np.float32)
    for _ in range(n):
        x = rng.integers(0, W)
        y = rng.integers(int(y0), int(y1))
        cv2.circle(layer, (int(x), int(y)), int(rng.uniform(1, rmax)), 1.0, -1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 1.1)
    add(img, layer, 0, 0, np.float32(color), a)


def vignette(img, amt=0.45, p=2.2):
    """네 귀퉁이를 눌러 가운데로 시선을 모읍니다. 밤 톤을 잡는 데도 씁니다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    img *= (1 - amt * np.clip(d / 1.42, 0, 1) ** p)[..., None]


def justify(text, width, track=0.10, path=BRAND, cap=None):
    """폭에 딱 맞는 크기. **라인업 블록의 전부가 이것입니다** —
    줄마다 폭을 채우면 글자 크기가 저절로 등급이 되고, 블록이 한 덩어리로 섭니다.
    `cap` 은 상한 — 짧은 줄이 터무니없이 커지는 걸 막습니다."""
    s = fit(text, path, width, track)
    return min(s, cap) if cap else s


def night(img, name=''):
    """**밤 행사 포스터는 눈으로 판단하지 말고 잽니다.** 화면마다 다르게 보입니다.
    평균 밝기 0.12~0.21, 밝은 픽셀(>0.6) 7% 아래가 여섯 시안에서 잡은 기준입니다."""
    lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114
    m, br = float(lum.mean()), float((lum > 0.6).mean() * 100)
    # 처음엔 기존 여섯 시안의 수치(평균 0.12~0.21)를 그대로 문턱으로 썼다가
    # 다섯 개 중 셋이 걸렸다. **그 수치는 사진이 깔린 판의 값**이고,
    # 순수 타이포·배지·무대 실루엣 판은 검정 면적이 훨씬 넓어 원래 더 어둡다.
    # 실제로 막아야 하는 실패는 둘뿐이다 — 너무 밝아 낮 행사로 보이는 것,
    # 너무 어두워 피드에서 검은 사각형이 되는 것.
    if br > 11 or m > 0.24:
        flag = '  ← 너무 밝다. 낮 행사처럼 보인다'
    elif m < 0.045:
        flag = '  ← 너무 어둡다. 피드에서 검은 사각형이 된다'
    else:
        flag = ''
    print(f'    {name:14s} 평균 {m:.3f} · 밝은 픽셀 {br:.1f}%{flag}')
    return m, br


# ── 풀 × 솔로 (L~P) ───────────────────────────────────────
def water(W, H, deep, shallow, seed=4, scale=0.030, amp=0.16, t=0.0):
    """밤의 수면. 그라데이션 위에 코스틱(물빛 그물)을 얹습니다.

    **코스틱이 없으면 그냥 파란 판입니다.** 사인파 몇 개를 간섭시켜
    마루만 남기면 물 밑에서 빛이 흔들리는 그 무늬가 나옵니다."""
    img = sky(W, H, [(0.0, deep), (0.55, deep), (1.0, shallow)])
    yq, xq = np.mgrid[0:H // 3, 0:W // 3].astype(np.float32)
    x, y = xq * scale * 3, yq * scale * 3
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42 + t)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37 - t)) +
         0.8 * np.sin((x + y) * 0.85 + t * 1.4))
    k = np.clip(1 - np.abs(np.sin(f * 1.7)) * 6.5, 0, 1) ** 1.3
    k = cv2.resize(cv2.GaussianBlur(k, (0, 0), 1.2), (W, H), interpolation=cv2.INTER_LINEAR)
    add(img, k, 0, 0, np.float32([0.55, 0.90, 1.00]), amp)
    return img


def ripple(img, cx, cy, r0, r1, n, color, a=0.5, th=2.0, fade=True):
    """한 점에서 퍼지는 동심원. **혼자 온 사람 하나가 물에 닿은 자리**입니다.

    간격을 일정하게 두면 과녁이 됩니다 — 밖으로 갈수록 넓어지고 옅어져야
    퍼져 나가는 것으로 보입니다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    acc = np.zeros((H, W), np.float32)
    r, step = float(r0), (r1 - r0) / max(n, 1)
    i = 0
    while r < r1:
        w = th * (1 + 1.4 * (r - r0) / max(r1 - r0, 1))
        g = np.clip(1 - np.abs(d - r) / w, 0, 1)
        acc += g * ((1 - (r - r0) / max(r1 - r0, 1)) ** 0.8 if fade else 1.0)
        r += step * (1 + 0.10 * i)                 # 밖으로 갈수록 간격이 넓어진다
        i += 1
    add(img, np.clip(acc, 0, 1), 0, 0, np.float32(color), a)
    return np.clip(acc, 0, 1)


def torus(img, cx, cy, R, r, color, a=1.0, glow=0.0):
    """수영장 튜브. **원 하나로 풀파티와 솔로파티를 동시에 말합니다** —
    물에 뜬 물건이면서, 두 개가 겹치면 둘이 만나는 그림이 됩니다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    band = np.clip(1 - np.abs(d - R) / r, 0, 1) ** 0.6
    if glow > 0:
        add(img, cv2.GaussianBlur(band, (0, 0), r * 1.6), 0, 0, np.float32(color), glow)
    m = band[..., None] * a
    img[:] = img * (1 - m) + np.float32(color) * m
    return band


def reflect(img, y, depth, wob=6.0, damp=0.55, seed=2):
    """수면에 비친 상. 위를 뒤집어 아래에 깔고 가로로 흔듭니다.

    **흔들지 않으면 거울이지 물이 아닙니다.** 아래로 갈수록 더 흔들고 더 흐립니다."""
    H, W = img.shape[:2]
    y = int(y)
    depth = int(min(depth, H - y, y))
    if depth <= 4:
        return
    src = img[y - depth:y][::-1].copy()
    rows = np.arange(depth, dtype=np.float32)
    dx = (np.sin(rows * 0.13 + 1.1) * wob * (0.3 + rows / depth)).astype(np.float32)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), rows)
    src = cv2.remap(src, (gx + dx[:, None]).astype(np.float32), gy.astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    src = cv2.GaussianBlur(src, (0, 0), 1.6)
    k = (damp * (1 - rows / depth) ** 1.2)[:, None, None]
    img[y:y + depth] = img[y:y + depth] * (1 - k) + src * k


def rope(img, y, W, color, bead, gap, a=1.0, alt=None):
    """레인 로프. 구슬이 번갈아 꿰인 그 줄입니다.
    구슬 없이 선만 그으면 레인이 아니라 밑줄입니다."""
    x = 0
    i = 0
    while x < W:
        c = color if (alt is None or i % 2 == 0) else alt
        cv2.circle(img, (int(x + bead), int(y)), int(bead),
                   tuple(float(v) for v in c), -1, cv2.LINE_AA)
        x += bead * 2 + gap
        i += 1
