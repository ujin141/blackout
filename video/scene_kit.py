"""
**장면.** 도형이 아니라 그림입니다.

두 가지 방법이 있고, **지금 쓰는 건 사진 쪽**입니다.

    photoscene()  사진 두 장(클럽 · 수영장)을 물가에서 잇는다  ← 포스터가 쓰는 것
    poolscene()   전부 그린다. 도표처럼 보여서 물러났다

벤 다이어그램·물결·튜브는 컨셉을 **상징**으로 옮긴 것이라, 보는 사람이
한 번 해석해야 뜻이 옵니다. 그게 "추상적"의 정체입니다.

이 파일은 해석할 게 없는 그림을 그립니다 — **밤 루프탑 수영장에 사람이 있고
디제이가 틀고 있는 장면.** 물, 사람, 부스, 조명, 도시. 보면 그냥 압니다.

사진은 못 씁니다(크루에 공연 사진이 없고, 스톡의 빈 수영장은 파티가 아닙니다).
그래서 전부 그립니다 — 사이트의 캔버스 아트와 같은 방식입니다.

장면이 장면으로 읽히려면 **겹의 순서**가 전부입니다.

    하늘 → 도시 → 전구줄 → 디제이 부스 · 빔 → 데크 · 사람 →
    수면 → 물에 비친 상 → 물에 있는 사람 → 튜브 → 물빛 → 공기

순서를 바꾸면 사람이 물 위에 뜨거나 빛이 사람 앞으로 나옵니다.
"""
import numpy as np
import cv2

SKY_TOP = (0.020, 0.024, 0.050)
SKY_LOW = (0.115, 0.055, 0.075)
WATER_D = (0.020, 0.070, 0.105)
WATER_L = (0.080, 0.230, 0.290)
INK     = np.float32([0.010, 0.010, 0.016])
BULB    = np.float32([1.00, 0.80, 0.42])
AQUA    = np.float32([0.35, 0.92, 1.00])
ROSE    = np.float32([1.00, 0.28, 0.62])
VIOLET  = np.float32([0.62, 0.34, 1.00])


def _grad(W, H, top, low, p=1.0):
    # (H,1,1) 에 (3,) 를 곱하면 (H,1,3) 이 나온다 — **폭이 1인 그림**이다.
    # 가로로 펴 줘야 한다. 이걸 빼먹고 배경을 만들면 뒤에서 엉뚱하게 터진다.
    t = (np.linspace(0, 1, H, dtype=np.float32) ** p)[:, None, None]
    col = np.float32(top) * (1 - t) + np.float32(low) * t
    return np.ascontiguousarray(np.repeat(col, W, axis=1))


def _add(img, m, color, a):
    img += m[..., None] * np.float32(color) * a


def skyline(img, base, h, seed=5, a=1.0):
    """도시 실루엣 + 창문 불빛. **창문이 없으면 검은 산이지 도시가 아니다.**"""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    x = 0
    while x < W:
        w = int(rng.integers(int(W * 0.030), int(W * 0.090)))
        tall = rng.random() < 0.22
        bh = h * (rng.uniform(0.55, 1.00) if tall else rng.uniform(0.18, 0.45))
        y0 = int(base - bh)
        img[max(0, y0):int(base), x:min(W, x + w)] = INK
        # 창문 — 몇 개만 켜져 있어야 사람이 사는 건물로 보인다
        gx = max(3, int(w * 0.16))
        gy = max(4, int(bh * 0.10))
        for wy in range(y0 + gy, int(base) - gy, gy * 2):
            for wx in range(x + gx, x + w - gx, gx * 2):
                if rng.random() < 0.22 and 0 <= wy < H and 0 <= wx < W:
                    img[wy:wy + max(1, gy // 2), wx:wx + max(1, gx // 2)] = \
                        np.float32([0.55, 0.44, 0.26]) * rng.uniform(0.5, 1.0)
        x += w + int(rng.integers(0, int(W * 0.010)))


def strings(img, y, sag, rows, V, seed=3):
    """전구줄. 루프탑 파티의 표식이고, **늘어져야** 줄이지 막대가 아니다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    lay = np.zeros((H, W), np.float32)
    for r in range(rows):
        y0 = y + r * sag * 0.55
        xs = np.linspace(-W * 0.05, W * 1.05, 260)
        ys = y0 + np.sin(np.linspace(0, np.pi * (2 + r), len(xs))) * sag * 0.5
        pts = np.stack([xs, ys], 1).astype(np.int32)
        cv2.polylines(img, [pts], False, (0.06, 0.06, 0.08), max(1, int(2 * V)), cv2.LINE_AA)
        for i in range(0, len(xs), 9):
            cv2.circle(lay, (int(xs[i]), int(ys[i])), max(2, int(4 * V)),
                       float(rng.uniform(0.7, 1.0)), -1, cv2.LINE_AA)
    _add(img, lay, BULB, 0.95)
    _add(img, cv2.GaussianBlur(lay, (0, 0), 14 * V), BULB, 0.85)


def person(layer, cx, base, h, arms=0, lean=0.0):
    """사람 하나. **자세히 그리면 삽화가 되고, 덩어리로 그려야 실루엣이다.**"""
    hh = h * 0.17
    cv2.circle(layer, (int(cx + lean * h * 0.08), int(base - h * 0.90)), int(hh * 0.5),
               1.0, -1, cv2.LINE_AA)
    pts = np.array([[cx - h * 0.115, base - h * 0.76], [cx + h * 0.115, base - h * 0.76],
                    [cx + h * 0.095, base - h * 0.34], [cx + h * 0.075, base],
                    [cx + h * 0.014, base], [cx + h * 0.022, base - h * 0.34],
                    [cx - h * 0.022, base - h * 0.34], [cx - h * 0.014, base],
                    [cx - h * 0.075, base], [cx - h * 0.095, base - h * 0.34]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0, cv2.LINE_AA)
    if arms:                                          # 손 든 사람 — 파티의 신호
        for s in (-1, 1):
            cv2.line(layer, (int(cx + s * h * 0.10), int(base - h * 0.72)),
                     (int(cx + s * h * 0.26), int(base - h * (1.02 + 0.06 * arms))),
                     1.0, max(2, int(h * 0.045)), cv2.LINE_AA)


def booth(img, cx, base, w, V, seed=7):
    """디제이 부스. **틀고 있는 사람이 보여야 디제잉이다** —
    장비만 두면 창고이고, 사람이 뒤에 서야 공연이 된다."""
    H, W = img.shape[:2]
    h = w * 0.42
    cv2.rectangle(img, (int(cx - w / 2), int(base - h)), (int(cx + w / 2), int(base)),
                  (0.030, 0.030, 0.040), -1)
    cv2.rectangle(img, (int(cx - w / 2), int(base - h)), (int(cx + w / 2), int(base - h * 0.86)),
                  tuple(float(v) for v in AQUA * 0.55), -1)
    lay = np.zeros((H, W), np.float32)
    for i in range(9):                                # 장비 표시등
        cv2.circle(lay, (int(cx - w * 0.36 + w * 0.09 * i), int(base - h * 0.62)),
                   max(1, int(3 * V)), 1.0, -1, cv2.LINE_AA)
    _add(img, cv2.GaussianBlur(lay, (0, 0), 6 * V), AQUA, 0.9)
    # 부스 뒤에 선 사람
    p = np.zeros((H, W), np.float32)
    person(p, cx, base - h * 0.98, w * 0.60, arms=1)
    img[:] = img * (1 - np.clip(p, 0, 1)[..., None]) + INK * np.clip(p, 0, 1)[..., None]
    _add(img, cv2.GaussianBlur(p, (0, 0), 18 * V), VIOLET, 0.30)


def beams(img, sx, sy, n, spread, length, color, a, seed=3):
    """부스에서 뻗는 빔. 원뿔이어야 공기가 보인다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    acc = np.zeros((H, W), np.float32)
    for i in range(n):
        ang = -np.pi / 2 + spread * ((i + 0.5) / n - 0.5) * 2 + rng.uniform(-0.05, 0.05)
        dx, dy = np.cos(ang), np.sin(ang)
        px, py = xx - sx, yy - sy
        along = px * dx + py * dy
        perp = np.abs(-px * dy + py * dx)
        wid = 5.0 + along * 0.10
        m = np.clip(1 - perp / np.maximum(wid, 1e-3), 0, 1) ** 1.5
        m *= np.clip(along / (length * 0.2), 0, 1) * np.clip(1 - along / length, 0, 1) ** 0.8
        acc += m
    _add(img, cv2.GaussianBlur(acc, (0, 0), max(2.0, W * 0.005)), color, a)


def water(img, wy, V, seed=9):
    """수면. 위를 뒤집어 아래에 깔고 흔든다 — **비치지 않으면 물이 아니다.**"""
    H, W = img.shape[:2]
    wy = int(wy)
    depth = H - wy
    if depth < 8:
        return
    src = img[max(0, wy - depth):wy][::-1].copy()
    d = min(depth, src.shape[0])
    rows = np.arange(d, dtype=np.float32)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), rows)
    wob = (np.sin(rows * 0.10 + 0.5) * (9.0 * V) * (0.25 + rows / d))[:, None]
    src = cv2.remap(src[:d], (gx + wob).astype(np.float32), gy.astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    src = cv2.GaussianBlur(src, (0, 0), 2.2)
    base = _grad(W, depth, WATER_D, WATER_L, 0.7)
    k = (0.62 * (1 - rows / d) ** 0.9)[:, None, None]
    img[wy:wy + d] = base[:d] * (1 - k) + src * k
    # 잔물결
    for i in range(0, d, max(3, int(H * 0.008))):
        aa = 0.09 * (1 - i / d) + 0.03
        img[wy + i:wy + i + max(1, int(2 * V))] = \
            img[wy + i:wy + i + max(1, int(2 * V))] * (1 - aa) + np.float32([0.5, 0.85, 1.0]) * aa
    # 물가 선
    img[wy:wy + max(2, int(3 * V))] = np.float32([0.55, 0.92, 1.00]) * 0.55


def swimmers(img, wy, V, W, seed=11, n=7):
    """물에 있는 사람 — **수면 위로 머리와 어깨만.** 몸 전체를 그리면
    물 위에 서 있는 그림이 되고, 잘라야 물에 들어가 있는 것으로 보인다."""
    H, Wd = img.shape[:2]
    rng = np.random.default_rng(seed)
    lay = np.zeros((H, Wd), np.float32)
    for _ in range(n):
        cx = rng.uniform(0.05, 0.95) * Wd
        cy = wy + rng.uniform(0.06, 0.55) * (H - wy)
        r = (H - wy) * rng.uniform(0.032, 0.058)
        cv2.circle(lay, (int(cx), int(cy - r * 1.1)), int(r * 0.62), 1.0, -1, cv2.LINE_AA)
        cv2.ellipse(lay, (int(cx), int(cy)), (int(r * 1.35), int(r * 0.85)),
                    0, 180, 360, 1.0, -1, cv2.LINE_AA)
        if rng.random() < 0.45:                       # 팔 든 사람
            s = 1 if rng.random() < 0.5 else -1
            cv2.line(lay, (int(cx + s * r * 0.7), int(cy - r)),
                     (int(cx + s * r * 1.6), int(cy - r * 2.9)),
                     1.0, max(2, int(r * 0.30)), cv2.LINE_AA)
    m = np.clip(lay, 0, 1)[..., None]
    img[:] = img * (1 - m) + INK * m
    _add(img, cv2.GaussianBlur(np.clip(lay, 0, 1), (0, 0), 10 * V), AQUA, 0.22)


def floats(img, wy, V, W, seed=13, n=4):
    """물에 뜬 튜브. **물건이 있어야 파티다.**"""
    H, Wd = img.shape[:2]
    rng = np.random.default_rng(seed)
    for i in range(n):
        cx = rng.uniform(0.08, 0.92) * Wd
        cy = wy + rng.uniform(0.18, 0.85) * (H - wy)
        r = (H - wy) * rng.uniform(0.075, 0.135)
        col = (AQUA, ROSE, np.float32([0.90, 1.00, 0.35]), BULB)[i % 4]
        yy, xx = np.mgrid[0:H, 0:Wd].astype(np.float32)
        d = np.sqrt(((xx - cx) / r) ** 2 + ((yy - cy) / (r * 0.34)) ** 2)
        body = (d < 1.0).astype(np.float32)
        img[:] = img * (1 - (body * 0.50)[..., None])
        ring = np.clip(1 - np.abs(d - 1.0) / 0.30, 0, 1) ** 0.8
        _add(img, ring, col, 0.55)
        _add(img, cv2.GaussianBlur(ring, (0, 0), r * 0.30), col, 0.45)


def caustics(img, wy, W, H, amp=0.24):
    """물빛 그물. 마지막에 얹어야 물 위의 빛으로 보인다."""
    yq, xq = np.mgrid[0:H // 2, 0:W // 2].astype(np.float32)
    x, y = xq * 0.052, yq * 0.052
    f = (np.sin(x * 1.7 + 1.8 * np.sin(y * 0.55)) + np.sin(y * 1.35 + 1.5 * np.sin(x * 0.48))
         + 0.9 * np.sin((x + y) * 1.05))
    k = np.clip(1 - np.abs(np.sin(f * 2.1)) * 8.0, 0, 1) ** 1.1
    k = cv2.resize(cv2.GaussianBlur(k, (0, 0), 0.9), (W, H), interpolation=cv2.INTER_LINEAR)
    mask = np.clip((np.arange(H, dtype=np.float32)[:, None] - wy) / max(H - wy, 1), 0, 1) ** 0.5
    _add(img, k * mask, np.float32([0.60, 0.95, 1.00]), amp)


def poolscene(W, H, story=False, wy=0.52, dj=0.74):
    """**밤 루프탑 풀파티 한 장면 — 그려서 만든 판.**

    **지금 포스터는 이걸 안 씁니다.** 선으로 그린 실루엣이 도표로 읽혀
    "자연스럽지 않다" 는 지적을 받았고, 사진을 합친 `photoscene()` 으로 갔습니다.
    남겨 둔 이유는 겹의 순서와 각 겹의 규칙(파일 첫머리)이 여전히 유효해서고,
    영상처럼 사진을 못 쓰는 자리에서 다시 필요할 수 있어서입니다."""
    V = W / 1080.0
    img = _grad(W, H, SKY_TOP, SKY_LOW, 1.6)
    WY = H * wy
    DECK = WY - H * 0.008

    # **도시는 사람보다 위에, 사람보다 작게.** 같은 검정에 같은 크기로 두니
    # 건물과 사람이 엉켜 무슨 덩어리인지 안 보였다. 도시를 데크 위로 올린다.
    skyline(img, DECK - H * 0.075, H * 0.090, seed=5)
    # 데크 — 사람이 설 바닥. 아주 옅게 밝혀야 실루엣이 배경에서 떨어진다
    img[int(DECK - H * 0.075):int(DECK)] += np.float32([0.030, 0.026, 0.040])
    strings(img, H * 0.135, H * 0.045, 2, V)

    # 디제이 부스 — 오른쪽. 빔은 부스에서 나온다
    bx, bw = W * dj, W * 0.30
    beams(img, bx, DECK - bw * 0.42, 6, 0.55, H * 0.42, VIOLET, 0.28)
    beams(img, bx, DECK - bw * 0.42, 5, 0.42, H * 0.36, ROSE, 0.20)
    booth(img, bx, DECK, bw, V)

    # 데크에 선 사람들 — 왼쪽에 모인다
    lay = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(21)
    x = -W * 0.02
    while x < W * 0.66:
        h = H * rng.uniform(0.125, 0.165)
        person(lay, x, DECK, h, arms=1 if rng.random() < 0.30 else 0,
               lean=rng.uniform(-0.4, 0.4))
        x += h * rng.uniform(0.42, 0.72)
    m = np.clip(lay, 0, 1)[..., None]
    img[:] = img * (1 - m) + INK * m

    water(img, WY, V)
    swimmers(img, WY, V, W)
    floats(img, WY, V, W)
    caustics(img, WY, W, H, amp=0.16)
    return np.clip(img, 0, 1)


# ── 사진으로 만드는 장면 ───────────────────────────────────
def photoscene(W, H, story=False, wy=0.46, warm=1.0, seed=5):
    """**사진 두 장으로 만든 장면.**

    그린 사람은 아무리 다듬어도 자연스럽지 않습니다 — 선으로 그린 실루엣은
    도표로 읽히고, 그 위에 네온을 얹으면 둘이 따로 놉니다.
    자연스러움은 **실제 사진의 결**에서 옵니다. 헤이즈의 얼룩, 물결의 불규칙,
    조명의 번짐은 코드로 흉내 낼수록 가짜 티가 납니다.

        위  클럽 사진의 위 34% — 헤이즈 · 조명 · 디스코볼. 얼굴은 안 들어간다
        아래 수영장 사진 — 진짜 물결과 반사

    경계에 물가 선을 두고, **위를 아래에 비춥니다.** 비치지 않으면 두 장을
    붙여 놓은 것이지 한 장면이 아닙니다.

    두 사진 다 CC0 이고, 클럽 사진은 아래쪽에 얼굴이 다 나와서 `CLUB_SAFE`
    크롭(위 34%)만 씁니다 — 이 값은 올리기만 할 것."""
    from poster_kit import duotone, CLUB, CLUB_SAFE, POOL
    V = W / 1080.0
    WY = int(H * wy)

    # **사진을 그대로 쓰면 낮이 된다.** 밝은 쪽을 반 이하로 내려야 밤이다 —
    # 처음 값(클럽 0.86 · 물 0.74)으로는 평균 밝기가 0.387 이었다(기준 0.24).
    top = duotone(CLUB, W, WY, np.float32([0.020, 0.010, 0.028]),
                  np.float32([0.40 * warm, 0.14, 0.30]), contrast=1.34, keep=0.10,
                  **CLUB_SAFE)
    bot = duotone(POOL, W, H - WY, np.float32([0.008, 0.024, 0.040]),
                  np.float32([0.15, 0.30, 0.37]), contrast=1.28, keep=0.09,
                  focus=0.62, zoom=1.30)
    img = np.empty((H, W, 3), np.float32)
    img[:WY] = top
    img[WY:] = bot

    # 위를 아래에 비춘다 — **이게 없으면 두 장을 붙인 것이지 한 장면이 아니다**
    d = min(WY, H - WY)
    src = top[WY - d:][::-1].copy()
    rows = np.arange(d, dtype=np.float32)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), rows)
    wob = (np.sin(rows * 0.09 + 0.4) * (10.0 * V) * (0.25 + rows / d))[:, None]
    src = cv2.remap(src, (gx + wob).astype(np.float32), gy.astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    src = cv2.GaussianBlur(src, (0, 0), 3.0)
    k = (0.46 * (1 - rows / d) ** 1.1)[:, None, None]
    img[WY:WY + d] = img[WY:WY + d] * (1 - k) + src * k

    # 물가 선 · 잔물결
    for i in range(0, H - WY, max(3, int(H * 0.010))):
        aa = 0.055 * (1 - i / (H - WY)) + 0.02
        img[WY + i:WY + i + max(1, int(2 * V))] =             img[WY + i:WY + i + max(1, int(2 * V))] * (1 - aa) + np.float32([0.5, 0.85, 1.0]) * aa
    img[WY:WY + max(2, int(3 * V))] = np.float32([0.60, 0.92, 1.00]) * 0.60

    # 물에 뜬 튜브 — 물건이 있어야 파티다. 가장자리에만
    rng = np.random.default_rng(seed)
    for cx, cy, r, col in ((0.11, 0.66, 0.105, AQUA), (0.90, 0.80, 0.080, ROSE),
                           (0.62, 0.58, 0.062, BULB)):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        py = WY + (H - WY) * cy
        d2 = np.sqrt(((xx - W * cx) / (W * r)) ** 2 + ((yy - py) / (W * r * 0.34)) ** 2)
        img *= (1 - ((d2 < 1.0).astype(np.float32) * 0.45)[..., None])
        ring = np.clip(1 - np.abs(d2 - 1.0) / 0.30, 0, 1) ** 0.8
        _add(img, ring, col, 0.50)
        _add(img, cv2.GaussianBlur(ring, (0, 0), W * r * 0.28), col, 0.40)

    caustics(img, WY, W, H, amp=0.10)

    # 위아래를 눌러 글자 자리를 만든다. 사진 판은 여기서 밤 톤이 정해진다
    yv = np.arange(H, dtype=np.float32)[:, None, None] / H
    img *= (1 - 0.55 * np.clip((0.30 - yv) / 0.30, 0, 1))
    img *= (1 - 0.45 * np.clip((yv - 0.72) / 0.28, 0, 1))
    return np.clip(img, 0, 1)
