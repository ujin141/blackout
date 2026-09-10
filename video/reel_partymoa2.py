"""
**파티모아 릴스 두 번째 세트.** 지난 파티 실사 사진으로. 앱이 파는 게 이거다.

    python audio_partymoa2.py     먼저. 곡 셋
    python reel_partymoa2.py      →  out/partymoa/RD_45명.mp4  RE_어디서.mp4  RF_9900.mp4
                                     out/partymoa/RDA.jpg REA.jpg RFA.jpg  (커버 1080×1920)
                                     out/partymoa/_릴스2커버격자.jpg

## 앞 세트와 다른 점

앞 세트(RA·RB·RC)는 앱 화면이었다. 이건 **사진**이다. 지난 루프탑 파티
실사 — 풀, 디제이 부스, 테이블, 샴페인. 앱이 파는 게 화면이 아니라 이
밤이라는 걸 보여 준다. 사진은 out/partymoa/_photos (깃 밖).

    D  혼자 온 45명       사진 여덟 장이 박자에 맞춰 끊긴다      organ 124
    E  이런 파티 어디서    사진 위로 폰이 올라온다. 앱에 다 있다  epiano 128
    F  9,900원이면        큰 글자 셋이 사진을 갈아치운다          dub 140

## 사실만

45명 중 45명 혼자 — 앱 홈의 '지금까지' 숫자. 사진은 지난 파티고, 9,900원·
9.26·압구정은 다음 파티(AFTER MOON)다. 둘을 섞어 말하지 않는다 —
"지난 파티" / "다음 파티" 를 자막에 그대로 적는다.

## 커버

셋이 한 장의 사진을 나눠 갖는다. 풀 와이드컷(029)을 3240 폭으로 잘라
보라 톤을 덮고, 노란 선 하나가 셋을 지난다. 앞 세트 커버와 같은 규칙.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

from feed_partymoa import ACCENT, BRAND, DEEP, WHITE, font
from fonts import KR, KRB
from render import out_cubic, out_expo
from reel_partymoa import (DUR, FPS, H, INK, INK_D, M, NF, OUT, SAFE_BOT, SAFE_TOP,
                           SUB, U, W, YEL, encode, end_card, fade, finish, fit_text,
                           logo_rgba, phone_window, plate, pop, put, text)
from reel_partymoa import SHOTS

PH = os.path.join(OUT, '_photos')
BPM = {'D': 124.0, 'E': 128.0, 'F': 140.0}
BGM = {'D': 'bgm_organ.wav', 'E': 'bgm_epiano.wav', 'F': 'bgm_dub.wav'}
PURPLE = np.float32(BRAND) / 255
DEEPC = np.float32(DEEP) / 255

# 사진마다 (파일, 초점 x 0~1, 초점 y 0~1). 세로로 자를 때 어디를 남길지
FOCUS = {
    '029': (0.50, 0.55), '030': (0.50, 0.55), '031': (0.50, 0.55), '041': (0.45, 0.5),
    '044': (0.5, 0.45), '045': (0.5, 0.45), '065': (0.55, 0.5), '083': (0.45, 0.45),
    '084': (0.5, 0.45), '085': (0.5, 0.45), '089': (0.5, 0.5), '097': (0.5, 0.5),
    '099': (0.5, 0.5), '100': (0.5, 0.45), '117': (0.5, 0.5), '132': (0.5, 0.5),
    '133': (0.5, 0.45), '136': (0.45, 0.45), '142': (0.4, 0.5), '173': (0.5, 0.5),
    '184': (0.5, 0.5), '186': (0.5, 0.5), '191': (0.5, 0.5), '194': (0.5, 0.5),
    '205': (0.55, 0.45), '209': (0.5, 0.5), '211': (0.5, 0.5), '218': (0.5, 0.5),
    '221': (0.5, 0.5), '222': (0.5, 0.5), '227': (0.5, 0.45), '236': (0.45, 0.45),
    '239': (0.45, 0.5), '241': (0.5, 0.45), '244': (0.5, 0.45), '262': (0.5, 0.45),
    '268': (0.5, 0.5), '277': (0.5, 0.5), '278': (0.5, 0.5), '297': (0.4, 0.45),
    '027': (0.5, 0.5), '020': (0.5, 0.5), '022': (0.5, 0.5), '035': (0.5, 0.5),
    '036': (0.5, 0.5), '037': (0.5, 0.5), '001': (0.5, 0.5), '014': (0.5, 0.5),
}

_cache = {}


def photo(name):
    """세로 1080×1920 보다 넉넉하게(1.25배) 잘라 둔다. 켄번즈 여유."""
    if name in _cache:
        return _cache[name]
    im = cv2.imread(os.path.join(PH, f'{name}.jpg'))[..., ::-1]
    h, w = im.shape[:2]
    fx, fy = FOCUS.get(name, (0.5, 0.5))
    # 세로 비율 9:16 에 맞춘 창. 높이는 사진 전체, 폭은 h*9/16
    cw = int(h * 9 / 16 * 1.0)
    cw = min(cw, w)
    x0 = int(np.clip(fx * w - cw / 2, 0, w - cw))
    crop = im[:, x0:x0 + cw]
    tgt_h = int(H * 1.25)
    tgt_w = int(crop.shape[1] * tgt_h / crop.shape[0])
    crop = cv2.resize(crop, (tgt_w, tgt_h), interpolation=cv2.INTER_AREA)
    arr = np.asarray(crop, np.float32) / 255.0
    _cache[name] = arr
    return arr


def kb(name, k, zoom=(1.0, 1.12), pan=(0.0, 0.0), dim=0.0):
    """켄번즈 한 프레임. k 0→1. 화면을 채운다."""
    src = photo(name)
    sh, sw = src.shape[:2]
    z = zoom[0] + (zoom[1] - zoom[0]) * k
    win_h = int(H / z * (sh / H) / 1.25 * 1.25)
    win_h = int(min(sh, H * 1.25 / z))
    win_w = int(win_h * W / H)
    cx = sw / 2 + pan[0] * (sw - win_w) / 2 * k
    cy = sh / 2 + pan[1] * (sh - win_h) / 2 * k
    x0 = int(np.clip(cx - win_w / 2, 0, sw - win_w))
    y0 = int(np.clip(cy - win_h / 2, 0, sh - win_h))
    fr = src[y0:y0 + win_h, x0:x0 + win_w]
    fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LINEAR)
    if dim:
        fr = fr * (1 - dim)
    return fr


def vignette(img, amt=0.35):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    img *= (1 - amt * np.clip(r, 0, 1)[..., None])


def band(img, y0, y1, a=0.55):
    """글자 뒤 어두운 띠. 사진 위 글자가 읽히게."""
    img[y0:y1] *= (1 - a)


def grade(img, k=1.0):
    """보라 쪽으로 살짝. 앱 색과 사진이 한 판으로 붙는다."""
    img[...] = img * (1 - 0.10 * k) + PURPLE * 0.10 * k * img.mean(axis=2, keepdims=True) * 2.2


def stack(img, lines, y, t, t0, gap=U * 1.5, size=64, step=0.18, color=INK):
    """쌓이는 자막. 한 줄씩 박자에 맞춰."""
    yy = y
    for i, ln in enumerate(lines):
        m = text(ln, KRB, size, color)
        put(img, m, M, yy, fade(t, t0 + i * step, 0.25))
        yy += m.shape[0] + gap
    return yy


# ══════════════════════════════════════════════════════════
#  D. 혼자 온 45명 — 사진 여덟 장, 오르간 124
# ══════════════════════════════════════════════════════════

def reel_d():
    beat = 60 / BPM['D']
    B = lambda n: n * beat
    lg = logo_rgba(36)
    hook1 = fit_text('혼자 온 사람', KRB, W - M * 2, 150)
    hook2 = text('45명 중', KRB, 150)
    hook3 = text('45명', KRB, 260, ACCENT + (255,))
    src = text('지난 파티 · 파티모아 집계', KR, 36, SUB)
    # (사진, 자막, 줌, 팬)
    cuts = [('209', '처음 보는 사람들이', (1.0, 1.10), (0.0, 0.0)),
            ('065', '테이블에서 만나고', (1.08, 1.0), (0.3, 0.0)),
            ('184', '풀에 발 담그고', (1.0, 1.12), (0.0, 0.3)),
            ('083', '디제이 앞에서', (1.1, 1.0), (-0.3, 0.0)),
            ('218', '바에서', (1.0, 1.1), (0.2, 0.0)),
            ('262', '샴페인 터지고', (1.05, 1.15), (0.0, -0.2)),
            ('221', '풀에 들어가고', (1.0, 1.1), (0.0, 0.0)),
            ('244', '새벽까지', (1.12, 1.0), (0.0, 0.0))]
    t_cut0 = B(4)
    per = B(1.5)
    t_next = t_cut0 + per * len(cuts)
    nxt1 = text('다음 파티', KR, 44, SUB)
    nxt2 = fit_text('AFTER MOON', KRB, W - M * 2, 150)
    nxt3 = text('9.26 토 · 압구정 딥하우즈 · 9,900원', KR, 40, SUB)
    t_end = t_next + B(3)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_cut0:
                img = kb('044', t / t_cut0, (1.0, 1.08), (0, 0), dim=0.55)
                grade(img)
                vignette(img, 0.4)
                pop(img, hook1, W / 2, H * 0.36, t, 0.0, 0.35)
                pop(img, hook2, W / 2, H * 0.36 + 170, t, B(1), 0.3)
                pop(img, hook3, W / 2, H * 0.36 + 420, t, B(2), 0.3)
                put(img, src, (W - src.shape[1]) / 2, H * 0.36 + 600, fade(t, B(2.5)))
            elif t < t_next:
                j = min(len(cuts) - 1, int((t - t_cut0) / per))
                name, cap, zm, pn = cuts[j]
                k = (t - t_cut0 - j * per) / per
                img = kb(name, k, zm, pn)
                grade(img, 0.7)
                vignette(img, 0.3)
                band(img, int(H * 0.70) - 30, int(H * 0.70) + 120, 0.45)
                c = text(cap, KRB, 72)
                put(img, c, M, int(H * 0.70), fade(t, t_cut0 + j * per, 0.2))
                n = text(f'{j + 1:02d} / {len(cuts):02d}', KR, 30, SUB)
                put(img, n, W - M - n.shape[1], SAFE_TOP + U * 4 + 8)
            else:
                img = kb('029', (t - t_next) / B(3), (1.0, 1.06), (0, 0), dim=0.5)
                grade(img)
                vignette(img, 0.4)
                if t < t_end:
                    put(img, nxt1, (W - nxt1.shape[1]) / 2, H * 0.33, fade(t, t_next))
                    pop(img, nxt2, W / 2, H * 0.33 + 150, t, t_next + 0.1, 0.35)
                    put(img, nxt3, (W - nxt3.shape[1]) / 2, H * 0.33 + 270, fade(t, t_next + 0.3))
            put(img, lg, M, SAFE_TOP + U * 4)
            end_card(img, t, t_end)
            yield finish(img)

    encode('RD_45명', frames(), BGM['D'])


# ══════════════════════════════════════════════════════════
#  E. 이런 파티 어디서 찾아요 — 사진 위로 폰, 이피 128
# ══════════════════════════════════════════════════════════

def reel_e():
    beat = 60 / BPM['E']
    B = lambda n: n * beat
    lg = logo_rgba(36)
    home = Image.open(os.path.join(SHOTS, 'home.png')).convert('RGB')
    party = Image.open(os.path.join(SHOTS, 'party.png')).convert('RGB')
    q1 = fit_text('이런 파티', KRB, W - M * 2, 160)
    q2 = fit_text('어디서 찾아요?', KRB, W - M * 2, 160)
    a1 = text('파티모아에', KRB, 120)
    a2 = text('다 올라와요', KRB, 120, ACCENT + (255,))
    chips = ['라인업', '잔여석', '남녀 자리', '9,900원']
    shots = [('133', (1.0, 1.1), (0, 0)), ('236', (1.1, 1.0), (0.2, 0)),
             ('173', (1.0, 1.08), (0, 0)), ('277', (1.08, 1.0), (-0.2, 0))]
    per = B(1.5)
    t_q = B(4)
    t_phone = t_q + per * len(shots)
    t_end = t_phone + B(8)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_q:
                img = kb('083', t / t_q, (1.0, 1.15), (0, 0), dim=0.45)
                grade(img)
                vignette(img, 0.4)
                pop(img, q1, W / 2, H * 0.40, t, 0.0, 0.35)
                pop(img, q2, W / 2, H * 0.40 + 180, t, B(1), 0.35)
            elif t < t_phone:
                j = min(len(shots) - 1, int((t - t_q) / per))
                name, zm, pn = shots[j]
                k = (t - t_q - j * per) / per
                img = kb(name, k, zm, pn)
                grade(img, 0.7)
                vignette(img, 0.3)
                band(img, int(H * 0.30) - 40, int(H * 0.30) + 300, 0.5)
                pop(img, a1, W / 2, H * 0.30 + 60, t, t_q, 0.3)
                pop(img, a2, W / 2, H * 0.30 + 200, t, t_q + 0.2, 0.3)
            else:
                img = kb('097', (t - t_phone) / B(8), (1.0, 1.06), (0, 0), dim=0.6)
                grade(img)
                vignette(img, 0.4)
                k = fade(t, t_phone, 0.6)
                which = home if t < t_phone + B(4) else party
                seg = (t - t_phone) / B(4) if which is home else (t - t_phone - B(4)) / B(4)
                seg = max(0.0, min(1.0, seg))
                off = out_cubic(seg) * (480 if which is home else 460)
                win = phone_window(which, 640, off, 1000)
                py = H * 0.34 + (1 - out_expo(k)) * 300
                put(img, win, (W - 640) / 2, py, k)
                # 칩. 폰 옆에 하나씩
                for c_i, chip in enumerate(chips):
                    kk = fade(t, t_phone + B(1) + c_i * B(0.75), 0.25)
                    if kk <= 0:
                        continue
                    cm = text(chip, KRB, 34, INK_D)
                    pw, ph = cm.shape[1] + 44, 64
                    cy = H * 0.34 + 120 + c_i * 90
                    cx = W - M - pw / 2 + (1 - out_expo(kk)) * 120
                    plate_small(img, chip, cx, cy, kk)
            put(img, lg, M, SAFE_TOP + U * 4)
            end_card(img, t, t_end)
            yield finish(img)

    encode('RE_어디서', frames(), BGM['E'])


def plate_small(img, t_, cx, cy, a=1.0):
    f = font(KRB, 34)
    tw = int(f.getlength(t_))
    pw, ph = tw + 44, 64
    im = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], 18, fill=ACCENT + (255,))
    d.text((22, (ph - 34) / 2 - 5), t_, font=f, fill=INK_D)
    put(img, np.asarray(im, np.float32) / 255.0, cx - pw / 2, cy - ph / 2, a)


# ══════════════════════════════════════════════════════════
#  F. 9,900원이면 — 큰 글자 셋, 더브 140
# ══════════════════════════════════════════════════════════

def reel_f():
    beat = 60 / BPM['F']
    B = lambda n: n * beat
    lg = logo_rgba(36)
    price = fit_text('9,900원이면', KRB, W - M * 2, 170)
    items = [('117', '웰컴샷 한 잔', (1.0, 1.12), (0, 0)),
             ('027', 'DJ 다섯 명', (1.1, 1.0), (0.3, 0)),
             ('244', '새벽 2시까지', (1.0, 1.1), (0, -0.2)),
             ('211', '남녀 15 : 15', (1.06, 1.0), (0, 0))]
    per = B(2.5)
    t_items = B(3)
    t_ev = t_items + per * len(items)
    ev1 = fit_text('AFTER MOON', KRB, W - M * 2, 150)
    ev2 = text('9.26 토 · 압구정 딥하우즈', KR, 42, SUB)
    ev3 = text('1차 30명 · 차면 2차', KR, 42, SUB)
    t_end = t_ev + B(4)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_items:
                img = kb('186', t / t_items, (1.0, 1.1), (0, 0), dim=0.5)
                grade(img)
                vignette(img, 0.4)
                pop(img, price, W / 2, H * 0.42, t, 0.0, 0.35)
                s = text('다음 파티 값이에요', KR, 40, SUB)
                put(img, s, (W - s.shape[1]) / 2, H * 0.42 + 130, fade(t, B(1)))
            elif t < t_ev:
                j = min(len(items) - 1, int((t - t_items) / per))
                name, cap, zm, pn = items[j]
                k = (t - t_items - j * per) / per
                img = kb(name, k, zm, pn)
                grade(img, 0.7)
                vignette(img, 0.35)
                band(img, int(H * 0.40) - 40, int(H * 0.40) + 220, 0.5)
                c = fit_text(cap, KRB, W - M * 2, 130)
                pop(img, c, W / 2, H * 0.40 + 90, t, t_items + j * per, 0.3)
                n = text(f'{j + 1} / {len(items)}', KR, 30, SUB)
                put(img, n, W - M - n.shape[1], SAFE_TOP + U * 4 + 8)
            else:
                img = kb('030', (t - t_ev) / B(4), (1.0, 1.06), (0, 0), dim=0.5)
                grade(img)
                vignette(img, 0.4)
                if t < t_end:
                    pop(img, ev1, W / 2, H * 0.36, t, t_ev, 0.35)
                    put(img, ev2, (W - ev2.shape[1]) / 2, H * 0.36 + 110, fade(t, t_ev + 0.2))
                    put(img, ev3, (W - ev3.shape[1]) / 2, H * 0.36 + 170, fade(t, t_ev + 0.4))
            put(img, lg, M, SAFE_TOP + U * 4)
            end_card(img, t, t_end)
            yield finish(img)

    encode('RF_9900', frames(), BGM['F'])


# ══════════════════════════════════════════════════════════
#  커버 셋 — 사진 한 장이 세 칸을 지난다
# ══════════════════════════════════════════════════════════

BAND = 1350
BAND_Y = (H - BAND) // 2
COVERS = [('RDA', ['혼자 온', '45명'], '릴스 · 12초', '예매 → 프로필 링크'),
          ('REA', ['이런 파티', '어디서?'], '릴스 · 12초', '예매 → 프로필 링크'),
          ('RFA', ['9,900원'], '릴스 · 12초', 'App Store · 파티모아')]


def covers():
    im = cv2.imread(os.path.join(PH, '029.jpg'))[..., ::-1]
    h, w = im.shape[:2]
    # 3240×1350 비율(2.4)로 가운데 띠를 자른다
    bh = int(w / 2.4)
    y0 = int(np.clip(h * 0.52 - bh / 2, 0, h - bh))
    strip = cv2.resize(im[y0:y0 + bh], (W * 3, BAND), interpolation=cv2.INTER_AREA)
    a = np.asarray(strip, np.float32) / 255.0
    # 보라 덮기. 위는 진하게, 아래는 사진이 보이게
    yy = np.linspace(0, 1, BAND, dtype=np.float32)[:, None, None]
    tint = PURPLE * (1 - yy) + DEEPC * yy
    a = a * 0.55 * (0.6 + 0.4 * yy) + tint * (0.55 - 0.25 * yy)
    a = np.clip(a, 0, 1)
    sheet = Image.fromarray((a * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(sheet)
    d.line([(M, int(BAND * 0.86)), (W * 3 - M, int(BAND * 0.86))], fill=WHITE + (110,), width=2)
    ly = int(BAND * 0.60)
    d.line([(0, ly), (W * 3, ly)], fill=ACCENT + (255,), width=6)

    tiles = []
    longest = max((l for _, ls, _, _ in COVERS for l in ls), key=len)
    for sz in range(180, 60, -4):
        if font(KRB, sz).getlength(longest) <= W - M * 2:
            break
    for i, (name, lines, sub, cta) in enumerate(COVERS):
        b = sheet.crop((i * W, 0, (i + 1) * W, BAND)).convert('RGBA')
        d = ImageDraw.Draw(b)
        lg = logo_rgba(34)
        b.alpha_composite(Image.fromarray((np.clip(lg, 0, 1) * 255).astype(np.uint8), 'RGBA'), (M, 96))
        f = font(KRB, sz)
        y = ly - 30 - len(lines) * (sz + 10)
        for line in lines:
            d.text((M + 3, y + 3), line, font=f, fill=(0, 0, 0, 120))
            d.text((M, y), line, font=f, fill=WHITE)
            y += sz + 10
        d.polygon([(M, ly + 40), (M, ly + 92), (M + 44, ly + 66)], fill=ACCENT)
        d.text((M + 64, ly + 44), sub, font=font(KR, 34), fill=WHITE + (220,))
        fc = font(KRB, 34)
        pw, ph = int(fc.getlength(cta) + 72), 92
        cy0 = int(BAND * 0.86) - 92 - 48
        d.rounded_rectangle([M, cy0, M + pw, cy0 + ph], 22, fill=ACCENT)
        d.text((M + 36, cy0 + (ph - 34) / 2 - 4), cta, font=fc, fill=(20, 12, 60))
        fb = font(KR, 22)
        d.text((M, int(BAND * 0.86) + 22), 'partymoa.com', font=fb, fill=WHITE + (200,))
        r = 'App Store'
        d.text((W - M - d.textlength(r, font=fb), int(BAND * 0.86) + 22), r, font=fb, fill=WHITE + (200,))
        full = Image.new('RGB', (W, H), DEEP)
        full.paste(b.convert('RGB'), (0, BAND_Y))
        full.save(os.path.join(OUT, f'{name}.jpg'), quality=94)
        tiles.append(b.convert('RGB'))

    g = Image.new('RGB', (W * 3 + 16, BAND * 2 + 8), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    for i, name in enumerate(('V3', 'V2', 'V1')):
        p = os.path.join(OUT, f'{name}.jpg')
        if os.path.exists(p):
            g.paste(Image.open(p), (i * (W + 8), BAND + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_릴스2커버격자.jpg'), quality=92)
    print('커버 완료')


def main(argv):
    want = set(argv) or {'d', 'e', 'f', 'cover'}
    if 'd' in want:
        reel_d()
    if 'e' in want:
        reel_e()
    if 'f' in want:
        reel_f()
    if 'cover' in want:
        covers()


if __name__ == '__main__':
    main(sys.argv[1:])
