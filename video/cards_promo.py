"""참여 이벤트 카드뉴스 — 표지 1장 + 내용 3장. 1080×1350.

    0 표지   병 한 장. 왜 넘겨야 하는지만
    1 조건    무엇을 해야 하나
    2 셈·행사  몇 팀 · 언제 · 어디서
    3 CTA     마지막 장은 시키는 말만 남긴다

**마지막 장은 정보를 안 담는다.** 캐러셀에서 마지막까지 넘긴 사람은 이미
살 마음이 있는 사람이다 — 거기서 정보를 또 주면 다시 재기 시작한다.
남길 건 무엇을 하면 끝나는지 한 줄뿐이다.

**한 장에 한 가지만 쓴다.** 캐러셀에서 두 가지를 한 장에 넣으면 둘 다
안 읽힌다 — 넘기는 손가락은 한 장에 1초를 안 준다.

표지에 조건을 안 적는다. 표지의 일은 넘기게 만드는 것 하나뿐이고, 조건을
먼저 보여 주면 "귀찮네" 하고 그냥 지나간다.

배경은 네 장이 **같은 한 장**을 쓴다. 넘기면서 읽는 판이라 배경이 매번
바뀌면 읽는 자리가 흔들린다 — 빛의 자리만 조금씩 옮긴다.

⚠ 배경은 손님 얼굴이 든 현장 영상에서 뽑은 프레임이다. 알아볼 수 없을
만큼 흐리고 어둡게 깔았지만, 원본(`숏폼/`)은 공개 저장소에 올리지 않는다.

python cards_promo.py  →  out/cards_promo/promo_card_{0..3}.png
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import (BRAND, STOCK, tmask, tmask_bl, fit, paint, paint_bl, rule, box,
                        logo, grain, status_block, status_tag, sign)
from fonts import KR, KRB
from poster_promo import INK, BLUE, GOLD, PAPER, DIM
import poster_promo as PP
import event as EV
import qr

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'cards_promo')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
M = 96                                    # 좌우 여백
FY = H - 92                               # 발치 한 줄


# 사람이 찬 판. 숏폼 원본에서 제일 붐비는 한 프레임을 뽑았다
CROWD = 'crowd.jpg'


def _base(W=W, H=H):
    """배경 한 장을 한 번만 만들어 네 장이 같이 쓴다.

    **사람이 보여야 뜻이 있다.** 판 전체를 어둡게 깔면 글자는 읽히지만
    "사람이 찼다" 는 게 안 보인다 — 그럴 거면 사진을 안 쓰는 게 낫다.
    그래서 사진은 살려 두고, 그늘은 `scrim()` 으로 **글자가 앉는 띠에만**
    건다. 글자 사이사이로 현장이 그대로 보인다.

    흐림은 얼굴이 뭉개질 만큼만(σ=4). 사람 수와 물, 튜브는 그대로 읽히고
    누가 누구인지는 안 보인다.

    사진이 없으면 검정 판으로 떨어진다(판이 안 깨진다)."""
    p = os.path.join(STOCK, CROWD)
    if not os.path.exists(p):
        return None
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255
    h, w = a.shape[:2]
    # **사람이 있는 띠를 글자 사이 빈 자리에 맞춰 넣는다.** 그냥 꽉 채우면
    # 아래쪽 튜브·물이 열린 자리에 오고 정작 사람은 글자 뒤로 숨는다.
    ZOOM, TOP = 1.06, 0.02
    sc = max(W / w, H / h) * ZOOM
    a = cv2.resize(a, (int(w * sc + 0.5), int(h * sc + 0.5)), interpolation=cv2.INTER_AREA)
    y0 = int((a.shape[0] - H) * TOP)
    x0 = (a.shape[1] - W) // 2
    a = a[y0:y0 + H, x0:x0 + W]
    a = cv2.GaussianBlur(a, (0, 0), 2.2)
    # 병 라벨의 파랑 쪽으로 당기되 **명암은 살린다** — 눌러 버리면 사람이 사라진다
    g = (a @ np.float32([0.299, 0.587, 0.114]))[..., None]
    a = a * 0.55 + (INK + (BLUE * 0.94 + PAPER * 0.40) * g ** 0.85) * 0.45
    a = np.clip((a - 0.5) * 1.14 + 0.5, 0, 1)        # 사람 윤곽이 서게 대비를 준다
    # **하늘이 너무 밝아 작은 글자를 잡아먹는다.** 밝은 쪽만 눌러서
    # 사람이 있는 중간 밝기는 안 건드린다 — 어둡게만 하면 사람도 같이 죽는다
    g2 = (a @ np.float32([0.299, 0.587, 0.114]))[..., None]
    a *= 1 - 0.46 * np.clip((g2 - 0.34) / 0.42, 0, 1)
    return np.clip(a * 0.94, 0, 1)


_BASE = {}


def field(i, W=W, H=H):
    """장마다 빛의 자리만 조금씩 옮긴다. 완전히 같으면 안 넘긴 줄 알고,
    완전히 다르면 다른 게시물로 보인다 — 그 사이를 잡는다."""
    if (W, H) not in _BASE:
        _BASE[(W, H)] = _base(W, H)
    b = _BASE[(W, H)]
    img = (b.copy() if b is not None
           else np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy())
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = W * (0.50 + 0.10 * (i - 1.5) / 1.5)
    img += np.exp(-(((xx - cx) / (W * 0.62)) ** 2
                    + ((yy - H * 0.46) / (H * 0.50)) ** 2))[..., None] * BLUE * 0.14
    return img


SHADOW = np.float32([0.004, 0.008, 0.016])
# **번지면 때가 낀 것처럼 보인다.** 넓게 깔면 글자 뒤에 얼룩이 생기고
# 그게 눈에 먼저 띈다 — 글자에 딱 붙는 테두리 두께로만 준다.
# 얇게 줘도 글자 가장자리를 갉아먹어서 오히려 안 읽힌다는 말을 들었다 —
# **0 으로 껐다.** 대신 글자가 앉는 띠의 그늘을 올려서 대비를 만든다.
SHADOW_R = 0

# **예약 폼 QR 은 꺼 둔다.** 이 판은 이벤트 응모를 받는 판이고, 예약 폼은
# 참가가 정해진 사람만 쓰는 것이다 — 아직 응모도 안 한 사람에게 예약을
# 들이밀면 무엇을 하라는 판인지 흐려진다.
# 참가 확정자용 판을 따로 만들 때 True 로 켜면 받침까지 그대로 나온다.
SHOW_QR = False


def _blur(m, r):
    """마스크를 부풀려 흐린다. **배열 크기는 그대로 유지된다** — tmask_bl 의
    베이스라인 값이 그 배열 기준이라 크기가 바뀌면 줄이 어긋난다."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r * 2 + 1, r * 2 + 1))
    return cv2.GaussianBlur(cv2.dilate(m, k), (0, 0), max(0.8, r * 0.55))


def P(img, m, x, y, r=None, sa=0.96, **kw):
    """그림자 + 글자. **판을 누르는 대신 글자를 세운다** — 그늘을 넓게 깔면
    사진이 죽고, 글자 뒤에만 그림자를 붙이면 사진을 살린 채로 읽힌다.
    이 판의 글자는 전부 이걸로 그린다."""
    r = SHADOW_R if r is None else r
    pos = {k: v for k, v in kw.items() if k in ('anchor', 'valign')}
    if r:
        paint(img, _blur(m, r), x, y, color=SHADOW, a=sa, **pos)
    paint(img, m, x, y, **kw)


def PB(img, pair, x, y, r=None, sa=0.94, **kw):
    r = SHADOW_R if r is None else r
    m, base = pair
    pos = {k: v for k, v in kw.items() if k == 'anchor'}
    if r:
        paint_bl(img, (_blur(m, r), base), x, y, color=SHADOW, a=sa, **pos)
    paint_bl(img, pair, x, y, **kw)


def scrim(img, y0, y1, a=0.74, soft=64):
    """글자가 앉는 띠에만 그늘. **판 전체를 누르지 않는다** — 띠 밖으로는
    사진이 그대로 보여야 사람이 찼다는 게 전달된다.

    가장자리를 부드럽게 풀어야 띠의 경계가 안 보인다. 딱 자르면 사진 위에
    검은 사각형을 올린 것처럼 읽힌다."""
    yy = np.arange(img.shape[0], dtype=np.float32)[:, None, None]
    m = (np.clip((yy - (y0 - soft)) / soft, 0, 1)
         * np.clip(((y1 + soft) - yy) / soft, 0, 1))
    img *= 1 - a * m


def foot(img, page=None):
    """발치 한 줄 — **로고와 아이디는 네 장 다 같은 자리에 있다.**
    어떤 장은 로고만, 어떤 장은 아이디만 있으면 같은 크루가 만든 걸로
    안 보인다. 캐러셀은 넘기면서 보는 물건이라 이 어긋남이 특히 잘 보인다."""
    rule(img, FY - 44, M, W - M, PAPER, 0.14, 1)
    sign(img, M, FY + 8, 21, color=PAPER, a=0.90)
    PB(img, tmask_bl(f'{EV.DATE_EN}   {EV.VENUE}', KR, 17, 0.01), W - M, FY,
       color=PAPER, a=0.78, anchor='r')
    if page is not None:
        PB(img, tmask_bl(f'{page} / 3', BRAND, 17, 0.20), W - M, FY + 30,
           color=GOLD, a=0.80, anchor='r')


def cover():
    img = field(0)
    scrim(img, 190, 570, 0.72)
    scrim(img, 1130, H, 0.82)
    lg = logo(56)
    paint(img, lg, W / 2 - lg.shape[1] / 2, 128, color=PAPER, a=0.92)
    P(img, tmask('FREE ENTRY  +  BOTTLE', BRAND, 19, 0.48), W / 2, 236,
          color=GOLD, a=0.92, anchor='c')
    # **표지는 상품만 말한다.** 조건을 여기 적으면 넘기기 전에 계산부터 한다.
    # 상품이 둘이라 쌓는다 — 한 줄로 붙이면 둘 다 작아 보인다
    for i, t in enumerate((EV.PROMO_GET_A, EV.PROMO_GET_B)):
        P(img, tmask(t, KRB, min(118, fit(t, KRB, W - M * 2, 0.0)), 0.0),
              W / 2, 322 + i * 104, color=PAPER, anchor='c')
    P(img, tmask('둘 다 드립니다', KRB, 46, 0.0), W / 2, 522, color=GOLD, anchor='c')
    PP.bottle(img, 856, 458, cx=W / 2, halo=0.32)
    # **표지에 상태를 안 넣으면 아무도 급하지 않다.** 왼쪽 여백선에 붙여서
    # 발치 줄과 같은 격자에 앉힌다
    status_tag(img, M, FY - 196, 34, color=PAPER, accent=GOLD, width=W - M * 2)
    P(img, tmask('넘기세요  →', KRB, 32, 0.02), W - M, FY - 96,
      color=GOLD, anchor='r')
    foot(img)
    return img


def page_do():
    img = field(1)
    scrim(img, 160, 330, 0.72)
    scrim(img, 430, 950, 0.60)
    scrim(img, 1110, H, 0.82)
    P(img, tmask(f'조건은 {EV.PROMO_N_KO}입니다', KRB, 64, 0.02), W / 2, 214,
          color=PAPER, anchor='c')
    P(img, tmask(f'{EV.PROMO_N_KO} 다 해야 인정됩니다', KRB, 27, 0.02), W / 2, 288,
          color=PAPER, a=0.94, anchor='c')
    y, step = (430, 178) if len(EV.PROMO_DO) > 2 else (470, 238)
    for i, d in enumerate(EV.PROMO_DO):
        box(img, M, y - 6, M + 8, y + 96, GOLD, 0.85)
        PB(img, tmask_bl(f'{i + 1}', BRAND, 32, 0.02), M + 38, y + 44,
                 color=GOLD, a=0.95)
        PB(img, tmask_bl(d, KRB, 58, 0.02), M + 96, y + 48, color=PAPER)
        rule(img, y + 122, M, W - M, PAPER, 0.11, 1)
        y += step
    # 조건을 다 보여 준 자리에서 바로 첫 동작을 시킨다. 셋 다 하라고 하면
    # 크게 느껴지지만 "댓글부터" 는 3초짜리다 — 하나만 하면 나머지도 한다
    P(img, tmask('지금 댓글부터 다세요', KRB, 40, 0.02), W / 2, FY - 100,
          color=GOLD, anchor='c')
    foot(img, 1)
    return img


def page_count():
    img = field(2)
    scrim(img, 150, 680, 0.70)
    scrim(img, 720, 1010, 0.78)
    scrim(img, 1110, H, 0.82)
    P(img, tmask('몇 팀 드리나요', KRB, 52, 0.02), W / 2, 196, color=PAPER, anchor='c')
    P(img, tmask(f'{EV.PROMO_TEAMS}팀', KRB, 210, 0.0), W / 2, 384,
          color=GOLD, anchor='c')
    P(img, tmask(f'추첨  ·  팀당 {EV.PROMO_PER}명 입장 무료  ·  샴페인 1병', KR, 24, 0.02),
          W / 2, 512, color=PAPER, a=0.94, anchor='c')
    # 추첨이니 '지금' 할 이유는 마감일뿐이다 — 제일 크게 보이는 자리에 둔다
    P(img, tmask(f'{EV.PROMO_DUE} 마감', KRB, 40, 0.02), W / 2, 578,
          color=PAPER, anchor='c')
    P(img, tmask(f'당첨자는 {EV.PROMO_ANNOUNCE} DM 으로 알려드립니다', KR, 22, 0.02),
          W / 2, 630, color=PAPER, a=0.88, anchor='c')
    rule(img, 688, M, W - M, PAPER, 0.14, 1)
    y = 762
    for k, v in (('DATE', EV.DATE_EN), ('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE),
                 ('AFTER', EV.AFTER)):
        PB(img, tmask_bl(k, BRAND, 16, 0.24), M, y, color=GOLD, a=0.92)
        PB(img, tmask_bl(v, BRAND if v.isascii() else KR, 22,
                               0.14 if v.isascii() else 0.01), M + 140, y,
                 color=PAPER, a=0.98)
        y += 50
    PB(img, tmask_bl(EV.ADDR, KR, 17, 0.01), M + 140, y - 12, color=DIM, a=0.85)
    # 마감일은 판마다 되풀이한다. 한 장만 본 사람도 날짜는 봐야 한다
    status_tag(img, M, FY - 200, 32, color=PAPER, accent=GOLD, width=W * 0.52)
    P(img, tmask(EV.PROMO_PUSH, KRB,
                 min(24, fit(EV.PROMO_PUSH, KRB, W * 0.40, 0.02)), 0.02),
      W - M, FY - 150, color=GOLD, anchor='r')
    P(img, tmask('추첨으로 뽑습니다', KR, 20, 0.02), W - M, FY - 112,
      color=PAPER, a=0.86, anchor='r')
    foot(img, 2)
    return img


_QR = None


def qr_patch(px):
    """QR 조각. **색을 뒤집지 않는다** — 검정 판에 맞춰 흰 코드로 뽑으면
    인식기가 못 읽는다(`qr.py` 참고). 밝은 받침을 깔고 보통 QR 을 얹는다."""
    global _QR
    if not EV.FORM_URL:
        return None
    if _QR is None:
        _QR = qr.build(EV.FORM_URL, 900, [0.02, 0.02, 0.03], [0.97, 0.98, 0.99])
    a = np.asarray(_QR.convert('RGB').resize((px, px), Image.NEAREST))
    return a.astype(np.float32) / 255


def _round(w, h, r):
    """모서리 둥근 사각 마스크."""
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(m, (cx, cy), r, 255, -1)
    return m


def plate(img, q, cx, cy, pad=30, rad=26, ring=3):
    """QR 받침. **흰 사각형을 그냥 얹으면 사진 위에 뜬다** — 모서리를 둥글리고
    금색 실선을 둘러야 판의 일부로 앉는다.

    받침 폭은 QR 여백(quiet zone) 몫이기도 하다. 여백을 먹으면 안 읽힌다."""
    qh, qw = q.shape[:2]
    ph, pw = qh + pad * 2, qw + pad * 2
    m = _round(pw, ph, rad).astype(np.float32) / 255
    inner = _round(pw - ring * 2 - 10, ph - ring * 2 - 10, max(2, rad - 8))
    edge = m.copy()
    edge[5 + ring:5 + ring + inner.shape[0], 5 + ring:5 + ring + inner.shape[1]] -=         inner.astype(np.float32) / 255
    edge = np.clip(edge, 0, 1)

    y0, x0 = int(cy - ph / 2), int(cx - pw / 2)
    sub = img[y0:y0 + ph, x0:x0 + pw]
    # 받침 뒤로 옅은 그늘 — 종이 한 장이 얹힌 것처럼 보인다
    sh = cv2.GaussianBlur(m, (0, 0), 14)[..., None]
    sub *= 1 - 0.45 * sh
    sub *= 1 - m[..., None]
    sub += m[..., None] * PAPER
    sub *= 1 - edge[..., None]
    sub += edge[..., None] * GOLD
    img[y0 + pad:y0 + pad + qh, x0 + pad:x0 + pad + qw] = q


def page_cta():
    """마지막 장 — **시키는 말만 남긴다.** 여기까지 넘긴 사람에게 정보를 더 주면
    다시 재기 시작한다.

    **이 판이 받는 건 응모 하나다.** 예약 폼까지 같이 놓아 봤는데, 아직
    응모도 안 한 사람에게 예약을 들이밀면 무엇을 하라는 판인지 흐려진다 —
    예약 폼은 참가가 정해진 사람만 쓰는 것이라 판을 따로 가는 게 맞다."""
    img = field(3)
    scrim(img, 250, 660, 0.74)
    scrim(img, 700, H, 0.80)
    lg = logo(46)
    paint(img, lg, W / 2 - lg.shape[1] / 2, 150, color=PAPER, a=0.88)
    P(img, tmask('조건 다 하셨으면', KR, 28, 0.02), W / 2, 306,
      color=PAPER, a=0.92, anchor='c')
    cta = EV.PROMO_CTA
    P(img, tmask(cta, KRB, min(104, fit(cta, KRB, W - M * 2, 0.0)), 0.0),
      W / 2, 396, color=GOLD, anchor='c')
    P(img, tmask(EV.PROMO_CTA_SUB, KRB, 38, 0.02), W / 2, 478,
      color=PAPER, anchor='c')
    P(img, tmask(EV.HANDLE, BRAND, min(36, fit(EV.HANDLE, BRAND, W - M * 2, 0.16)), 0.16),
      W / 2, 542, color=PAPER, a=0.94, anchor='c')

    P(img, tmask('프로필 → 메시지', KRB, 26, 0.02), W / 2, 616,
      color=PAPER, a=0.92, anchor='c')

    q = qr_patch(244) if SHOW_QR else None
    if q is not None:
        plate(img, q, W / 2, 800)
        P(img, tmask('자리 예약은 여기서', KRB, 34, 0.02), W / 2, 1000,
          color=PAPER, anchor='c')
    else:
        P(img, tmask(EV.PROMO_PUSH, KRB,
                     min(40, fit(EV.PROMO_PUSH, KRB, W - M * 2, 0.02)), 0.02),
          W / 2, 760, color=GOLD, anchor='c')
        P(img, tmask(f'{EV.PROMO_NOTE}  ·  {EV.PROMO_GET}', KR, 24, 0.02),
          W / 2, 812, color=PAPER, a=0.90, anchor='c')
        P(img, tmask(f'{EV.NAME}   {EV.DATE_EN}', BRAND,
                     min(28, fit(f'{EV.NAME}   {EV.DATE_EN}', BRAND, W - M * 2, 0.14)),
                     0.14), W / 2, 916, color=PAPER, a=0.90, anchor='c')
        P(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, 20, 0.01), W / 2, 950,
          color=PAPER, a=0.82, anchor='c')
        status_tag(img, W / 2, 1006, 34, color=PAPER, accent=GOLD,
                   width=W - M * 2, anchor='c')
    P(img, tmask(EV.RULES, KR, 13, 0.01), W / 2, FY - 66, color=DIM, a=0.72,
      anchor='c')
    foot(img, 3)
    return img


if __name__ == '__main__':
    for i, fn in enumerate((cover, page_do, page_count, page_cta)):
        a = np.clip(fn(), 0, 1)
        grain(a, 0.008, 17 + i)
        p = os.path.join(OUT, f'promo_card_{i}.png')
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)
    print('\n캐러셀 순서: 0 → 1 → 2 → 3')
