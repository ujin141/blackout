"""
**파티모아 릴스 3편.** 디자인·곡 전부 다르게. 커버는 피드 격자 위에 붙는다.

    python audio_partymoa.py    먼저. 곡 셋
    python reel_partymoa.py     →  out/partymoa/RA_혼자.mp4  RB_1분.mp4  RC_9900.mp4
                                   out/partymoa/RCA.jpg RCB.jpg RCC.jpg  (커버 1080×1920)
                                   out/partymoa/_릴스커버격자.jpg

## 세 편이 다른 이유

같은 판 세 개면 두 번째부터 안 본다. 편마다 판·곡·리듬을 바꾼다.

    A  혼자 가도 되나요   보라 바탕, 폰 스크롤       vowel 116  모음 신스
    B  예매 1분           어두운 바탕, 초시계·탭      acid 135   303
    C  9,900원            흰 바탕, 보라 큰 숫자       boom 100   808

## 훅 → 증거 → CTA

셋 다 같은 순서다. 첫 1초에 질문이나 숫자, 가운데에 앱 화면이나 사진,
마지막 3초에 노란 판 "예매 → 프로필 링크" 와 App Store.

## 커버

프로필 격자에서 릴스 커버는 가운데 4:5 만 보인다. 그 띠를 피드 P·U
와 같은 보라·같은 밑줄로 그려서 격자 맨 윗줄에 붙는다. 노란 선 하나가
셋을 지난다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from feed_partymoa import ACC, ACCENT, BRAND, DEEP, DOTS, WHITE, font
from fonts import KR, KRB
from qr import build as qr_build
from render import out_cubic, out_expo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'partymoa')
SHOTS = os.path.join(HERE, 'assets', 'shots_moon')
CROWD = os.path.join(os.path.dirname(HERE), '..', 'partymoa', 'public', 'covers',
                     'after-moon-crowd-raw.jpg')
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'

W, H, FPS = 1080, 1920, 30
DUR = 12.0
NF = int(DUR * FPS)
M = 84
SAFE_TOP, SAFE_BOT = 250, 1620
U = 12
BPM = {'A': 116.0, 'B': 135.0, 'C': 100.0}
BGM = {'A': 'bgm_vowel.wav', 'B': 'bgm_acid.wav', 'C': 'bgm_boom.wav'}

PURPLE = np.float32(BRAND) / 255
DEEPC = np.float32(DEEP) / 255
YEL = np.float32(ACCENT) / 255
INK = (255, 255, 255, 255)
INK_D = (20, 12, 60, 255)
SUB = (255, 255, 255, 200)


# ── 도구 ────────────────────────────────────────────────

def put(img, rgba, x, y, a=1.0):
    h, w = rgba.shape[:2]
    x, y = int(x), int(y)
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(W, x + w), min(H, y + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = rgba[sy0 - y:sy1 - y, sx0 - x:sx1 - x]
    al = sub[..., 3:4] * a
    img[sy0:sy1, sx0:sx1] = img[sy0:sy1, sx0:sx1] * (1 - al) + sub[..., :3] * al


def text(t, path, size, fill=INK):
    f = font(path, size)
    asc, desc = f.getmetrics()
    w = int(f.getlength(t)) + 8
    im = Image.new('RGBA', (w, asc + desc), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 0), t, font=f, fill=fill)
    return np.asarray(im, np.float32) / 255.0


def fit_text(t, path, room, cap, fill=INK):
    for sz in range(cap, 40, -4):
        if font(path, sz).getlength(t) <= room:
            return text(t, path, sz, fill)
    return text(t, path, 40, fill)


def scaled(rgba, s):
    if abs(s - 1) < 0.003:
        return rgba
    h, w = rgba.shape[:2]
    return cv2.resize(rgba, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_LINEAR)


def fade(t, t0, d=0.4):
    return out_cubic((t - t0) / d) if t >= t0 else 0.0


def pop(img, rgba, cx, cy, t, t0, d=0.35, a=1.0):
    """글자가 커진 상태에서 줄어들며 들어온다. 첫 박에 맞는 움직임."""
    k = fade(t, t0, d)
    if k <= 0:
        return
    s = 1.18 - 0.18 * out_expo(k)
    r = scaled(rgba, s)
    put(img, r, cx - r.shape[1] / 2, cy - r.shape[0] / 2, a * k)


def plate(img, t_, cx, cy, a=1.0, bg=ACCENT, fg=INK_D):
    """노란 CTA 판."""
    f = font(KRB, 40)
    tw = int(f.getlength(t_))
    pw, ph = tw + 96, 112
    im = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], 28, fill=bg + (255,))
    d.text((48, (ph - 40) / 2 - 6), t_, font=f, fill=fg)
    put(img, np.asarray(im, np.float32) / 255.0, cx - pw / 2, cy - ph / 2, a)


def logo_rgba(size=34, color=WHITE):
    """심볼 + 파티모아 워드마크 한 줄."""
    f = font(KRB, size)
    S = size / 80
    w = int(48 * S * 2 + f.getlength('파티모아')) + 20
    h = int(size * 1.9)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 4, h / 2 - 50 * S
    for x, y in DOTS:
        cx, cy = ox + x * S, oy + y * S
        d.ellipse([cx - 2.2 * S * 1.6, cy - 2.2 * S * 1.6, cx + 2.2 * S * 1.6, cy + 2.2 * S * 1.6],
                  fill=color + (255,))
    cx, cy = ox + ACC[0] * S, oy + ACC[1] * S
    d.ellipse([cx - 2.6 * S * 1.6, cy - 2.6 * S * 1.6, cx + 2.6 * S * 1.6, cy + 2.6 * S * 1.6],
              fill=ACCENT + (255,))
    d.text((ox + 100 * S + 10, h / 2 - size * 0.62), '파티모아', font=f, fill=color + (255,))
    return np.asarray(im, np.float32) / 255.0


def symbol_bg(img, alpha=0.06, cy=0.5, scale=1.0, color=(1, 1, 1)):
    """큰 심볼을 옅게 깐다."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    S = W / 63.0 * scale
    ox = (W - (ACC[0] - 26.6) * S) / 2 - 26.6 * S
    oy = H * cy - 50 * S
    r = 2.8 * S
    c = tuple(int(v * 255) for v in color)
    for x, y in DOTS:
        cx, cy_ = ox + x * S, oy + y * S
        d.ellipse([cx - r, cy_ - r, cx + r, cy_ + r], fill=c + (int(255 * alpha),))
    cx, cy_ = ox + ACC[0] * S, oy + ACC[1] * S
    d.ellipse([cx - r, cy_ - r, cx + r, cy_ + r], fill=ACCENT + (int(255 * alpha * 4),))
    put(img, np.asarray(lay, np.float32) / 255.0, 0, 0)


def purple_bg():
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a = PURPLE * (1 - yy ** 1.4) + DEEPC * (yy ** 1.4)
    a = np.repeat(a, W, axis=1)
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    a += 0.06 * np.exp(-(((xx - 0.18) / 0.45) ** 2) - ((yy - 0.1) / 0.5) ** 2)
    return a


def dark_bg():
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.float32([0.11, 0.06, 0.30])
    low = np.float32([0.05, 0.03, 0.14])
    a = top * (1 - yy) + low * yy
    a = np.repeat(a, W, axis=1)
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    a += 0.10 * np.exp(-(((xx - 0.5) / 0.45) ** 2) - ((yy - 0.55) / 0.35) ** 2) * PURPLE
    return a


def white_bg():
    return np.ones((H, W, 3), np.float32)


def phone_window(shot, width, offset, win_h):
    """폰 테두리 안에 스크린샷의 offset 부터 win_h 만큼."""
    sw = width - 44
    s = sw / shot.width
    win = shot.crop((0, int(offset / s), shot.width, int((offset + win_h * 1) / s + shot.height * 0)))
    win = shot.crop((0, int(offset / s), shot.width, min(shot.height, int(offset / s + win_h / s))))
    win = win.resize((sw, int(win.height * s)), Image.LANCZOS)
    ph = win_h + 44
    body = Image.new('RGBA', (width, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, width - 1, ph - 1], 74, fill=(11, 10, 20, 255))
    d.rounded_rectangle([3, 3, width - 4, ph - 4], 72, outline=(60, 56, 84, 255), width=2)
    mask = Image.new('L', (sw, win_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, win_h - 1], 56, fill=255)
    scr = Image.new('RGB', (sw, win_h), (255, 255, 255))
    scr.paste(win, (0, 0))
    body.paste(scr, (22, 22), mask)
    d.rounded_rectangle([width / 2 - 78, 30, width / 2 + 78, 60], 15, fill=(11, 10, 20, 255))
    return np.asarray(body, np.float32) / 255.0


def finish(img):
    out = np.clip(img, 0, 1)
    rng = np.random.default_rng(7)
    out += rng.normal(0, 0.006, out.shape).astype(np.float32)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def encode(name, frames, bgm):
    dst = os.path.join(OUT, f'{name}.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', '0', '-t', f'{DUR:.2f}', '-i', os.path.join(OUT, bgm),
           '-map', '0:v', '-map', '1:a', '-af', f'afade=t=out:st={DUR - 0.8:.2f}:d=0.8',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
           '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', dst]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print('완료:', dst)


def end_card(img, t, t0, dark=False):
    """마지막 판. 로고 · 노란 판 · App Store."""
    k = fade(t, t0, 0.5)
    if k <= 0:
        return
    lg = logo_rgba(56, WHITE if not dark else (91, 43, 232))
    put(img, lg, (W - lg.shape[1]) / 2, H * 0.36 - lg.shape[0] / 2, k)
    pop(img, text('예매는 앱에서', KRB, 84, INK if not dark else (91, 43, 232, 255)),
        W / 2, H * 0.45, t, t0 + 0.1, 0.4, k)
    plate(img, '예매 → 프로필 링크', W / 2, H * 0.55, k)
    s = text('App Store · 파티모아', KR, 34, SUB if not dark else (91, 43, 232, 200))
    put(img, s, (W - s.shape[1]) / 2, H * 0.55 + 90, k)


# ══════════════════════════════════════════════════════════
#  A. 혼자 가도 되나요 — 보라, 폰 스크롤, 모음 신스 116
# ══════════════════════════════════════════════════════════

def reel_a():
    beat = 60 / BPM['A']
    B = lambda n: n * beat
    bg = purple_bg()
    symbol_bg(bg, 0.07, 0.42, 1.0)
    home = Image.open(os.path.join(SHOTS, 'home.png')).convert('RGB')
    party = Image.open(os.path.join(SHOTS, 'party.png')).convert('RGB')
    hook1 = fit_text('혼자 가도', KRB, W - M * 2, 170)
    hook2 = fit_text('되나요', KRB, W - M * 2, 170)
    yes = text('네', KRB, 340, ACCENT + (255,))
    proof = text('지난 파티 45명 중 45명이 혼자 왔어요', KR, 38, SUB)
    cap1 = text('라인업까지 다 보여요', KRB, 52)
    cap2 = text('누가 트는지, 몇 자리 남았는지', KRB, 52)
    cap3 = text('자리는 크루가 붙여줘요', KRB, 72)
    cap4 = text('예매할 때 인스타 아이디만 적으면', KR, 38, SUB)
    lg = logo_rgba(36)
    t_end = B(20)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            put(img, lg, M, SAFE_TOP + U * 4)
            if t < B(5):
                hold = 1 - fade(t, B(2), 0.25)
                pop(img, hook1, W / 2, H * 0.40, t, 0.0, 0.35, hold)
                pop(img, hook2, W / 2, H * 0.40 + 190, t, B(0.5), 0.35, hold)
                if t >= B(2):
                    pop(img, yes, W / 2, H * 0.44, t, B(2), 0.3)
                    put(img, proof, (W - proof.shape[1]) / 2, H * 0.44 + 210, fade(t, B(2.5)))
            elif t < B(17):
                k = fade(t, B(5), 0.6)
                which = home if t < B(11) else party
                seg = (t - B(5)) / B(6) if t < B(11) else (t - B(11)) / B(6)
                seg = max(0.0, min(1.0, seg))
                total_off = 480 if which is home else 460
                off = out_cubic(seg) * total_off
                win = phone_window(which, 720, off, 1120)
                py = H - (H - 600) * out_expo(k)
                put(img, win, (W - 720) / 2, py, 1.0)
                cap = cap1 if t < B(11) else cap2
                put(img, cap, (W - cap.shape[1]) / 2, SAFE_TOP + U * 12, fade(t, B(5.5) if t < B(11) else B(11)))
            elif t < t_end:
                pop(img, cap3, W / 2, H * 0.44, t, B(17), 0.35)
                put(img, cap4, (W - cap4.shape[1]) / 2, H * 0.44 + 70, fade(t, B(17.5)))
            end_card(img, t, t_end)
            yield finish(img)

    encode('RA_혼자', frames(), BGM['A'])


# ══════════════════════════════════════════════════════════
#  B. 예매 1분 — 어두운 판, 초시계, 탭, 303 135
# ══════════════════════════════════════════════════════════

# 예매 시트 스크린샷(1075×2330)에서 칸 위치. (y0, y1, 이름)
FIELDS = [(455, 690, '차수'), (800, 920, '이름'), (1035, 1155, '연락처'),
          (1355, 1475, '인스타 (선택)'), (1625, 1760, '성별'), (1930, 2045, '인원'),
          (2195, 2295, '신청')]


def ring(img, cx, cy, r, k, color, th=10):
    lay = np.zeros((H, W), np.float32)
    cv2.ellipse(lay, (int(cx), int(cy)), (int(r), int(r)), -90, 0, int(360 * k), 1.0, th, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.0)
    img[...] = img * (1 - lay[..., None]) + np.float32(color) * lay[..., None]


def reel_b():
    beat = 60 / BPM['B']
    B = lambda n: n * beat
    bg = dark_bg()
    symbol_bg(bg, 0.05, 0.5, 1.1)
    party = Image.open(os.path.join(SHOTS, 'party.png')).convert('RGB')
    book = Image.open(os.path.join(SHOTS, 'book.png')).convert('RGB')
    h1 = text('예매', KRB, 200)
    h2 = text('1분', KRB, 300, ACCENT + (255,))
    lg = logo_rgba(36)
    end1 = text('입금 24시간', KRB, 120)
    end2 = text('안 하면 자리 자동으로 풀려요', KR, 40, SUB)
    t_end = B(23)
    pw, win_h = 700, 1180
    px, py = (W - pw) // 2, 470
    s = (pw - 44) / book.width

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            put(img, lg, M, SAFE_TOP + U * 4)
            if t < B(3):
                pop(img, h1, W / 2, H * 0.36, t, 0.0, 0.3)
                pop(img, h2, W / 2, H * 0.36 + 260, t, B(1), 0.3)
                ring(img, W / 2, H * 0.36 + 120, 330, fade(t, B(1), 0.9), YEL, 8)
            elif t < B(20):
                if t < B(7):
                    win = phone_window(party, pw, 240, win_h)
                    put(img, win, px, py)
                    # 커서가 예매하기 버튼으로 간다. 버튼은 창 아래 오른쪽
                    k = fade(t, B(4), 0.8)
                    cx = px + pw * 0.50 + (pw * 0.32) * out_cubic(k)
                    cy = py + 22 + win_h * 0.90 - (1 - out_cubic(k)) * 260
                    cv2.circle(img, (int(cx), int(cy)), 22, (1.0, 0.89, 0.30), -1, cv2.LINE_AA)
                    if t >= B(6):
                        r = int(30 + 60 * fade(t, B(6), 0.4))
                        cv2.circle(img, (int(cx), int(cy)), r, (1.0, 0.89, 0.30), 3, cv2.LINE_AA)
                else:
                    j = min(len(FIELDS) - 1, int((t - B(7)) / B(1.85)))
                    y0, y1, name = FIELDS[j]
                    # 강조 칸이 창 40% 높이에 오게 스크롤
                    off = max(0, y0 * s - win_h * 0.40)
                    win = phone_window(book, pw, off, win_h)
                    put(img, win, px, py)
                    fy0 = py + 22 + y0 * s - off
                    fy1 = py + 22 + y1 * s - off
                    kk = fade(t, B(7) + j * B(1.85), 0.25)
                    x0, x1 = px + 22 + 14, px + pw - 22 - 14
                    cv2.rectangle(img, (int(x0), int(fy0)), (int(x1), int(fy1)),
                                  (1.0, 0.89, 0.30), max(2, int(6 * kk)), cv2.LINE_AA)
                    tag = text(name, KRB, 40, INK_D)
                    plate(img, name, W / 2, py - 70, kk)
                # 초시계
                sec = int((t - B(3)) * 4.6)
                tm = text(f'00:{sec:02d}', KRB, 56, ACCENT + (255,))
                put(img, tm, W - M - tm.shape[1], SAFE_TOP + U * 4)
            elif t < t_end:
                pop(img, end1, W / 2, H * 0.42, t, B(20), 0.3)
                put(img, end2, (W - end2.shape[1]) / 2, H * 0.42 + 90, fade(t, B(20.5)))
            end_card(img, t, t_end)
            yield finish(img)

    encode('RB_1분', frames(), BGM['B'])


# ══════════════════════════════════════════════════════════
#  C. 9,900원 — 흰 판, 보라 큰 숫자, 808 100
# ══════════════════════════════════════════════════════════

PUR = (91, 43, 232, 255)
PUR_SUB = (91, 43, 232, 180)


def reel_c():
    beat = 60 / BPM['C']
    B = lambda n: n * beat
    bg = white_bg()
    symbol_bg(bg, 0.05, 0.5, 1.2, color=(0.36, 0.17, 0.91))
    price = text('9,900원', KRB, 250, PUR)
    p_sub = text('웰컴샷 포함 · 남녀 같은 값', KR, 40, PUR_SUB)
    cap = text('1차 30명', KRB, 220, PUR)
    cap_sub = text('남녀 15 : 15 · 한쪽 차면 마감', KR, 40, PUR_SUB)
    nxt = text('차면 2차', KRB, 220, PUR)
    nxt_sub = text('먼저 잡는 쪽이 먼저', KR, 40, PUR_SUB)
    ev1 = text('AFTER MOON', KRB, 96, PUR)
    ev2 = text('9.26 토 · 압구정 딥하우즈', KR, 40, PUR_SUB)
    now = text('지금 예매', KRB, 150, PUR)
    lg = logo_rgba(36, (91, 43, 232))
    # 사진 카드
    crowd = Image.open(CROWD).convert('RGB')
    cw = W - M * 2
    ch = int(cw * 3 / 5)
    crowd = crowd.resize((cw, ch), Image.LANCZOS)
    card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    mask = Image.new('L', (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], 40, fill=255)
    card.paste(crowd, (0, 0), mask)
    card = np.asarray(card, np.float32) / 255.0
    q = qr_build(PARTY_URL, 320, [0.36, 0.17, 0.91], [1.0, 1.0, 1.0], badge=False, error='m')
    q = np.asarray(q.convert('RGBA').resize((360, 360), Image.NEAREST), np.float32) / 255.0
    t_end = B(16)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            put(img, lg, M, SAFE_TOP + U * 4)
            if t < B(2.5):
                pop(img, price, W / 2, H * 0.42, t, 0.0, 0.3)
                put(img, p_sub, (W - p_sub.shape[1]) / 2, H * 0.42 + 150, fade(t, B(0.5)))
            elif t < B(5):
                pop(img, cap, W / 2, H * 0.42, t, B(2.5), 0.3)
                put(img, cap_sub, (W - cap_sub.shape[1]) / 2, H * 0.42 + 140, fade(t, B(3)))
            elif t < B(7):
                pop(img, nxt, W / 2, H * 0.42, t, B(5), 0.3)
                put(img, nxt_sub, (W - nxt_sub.shape[1]) / 2, H * 0.42 + 140, fade(t, B(5.5)))
            elif t < B(12):
                k = fade(t, B(7), 0.5)
                cy = H * 0.50 - ch / 2 + (1 - out_expo(k)) * 200
                put(img, card, M, cy, k)
                put(img, ev1, (W - ev1.shape[1]) / 2, cy - 150, fade(t, B(7.5)))
                put(img, ev2, (W - ev2.shape[1]) / 2, cy + ch + 40, fade(t, B(8)))
            elif t < t_end:
                pop(img, now, W / 2, H * 0.30, t, B(12), 0.3)
                k = fade(t, B(12.3), 0.4)
                put(img, q, (W - 360) / 2, H * 0.40, k)
                s = text('카메라로 찍으면 예매 화면', KR, 38, PUR_SUB)
                put(img, s, (W - s.shape[1]) / 2, H * 0.40 + 380, k)
            end_card(img, t, t_end, dark=True)
            yield finish(img)

    encode('RC_9900', frames(), BGM['C'])


# ══════════════════════════════════════════════════════════
#  커버 셋 — 격자 맨 윗줄
# ══════════════════════════════════════════════════════════

BAND = 1350
BAND_Y = (H - BAND) // 2
COVERS = [('RCA', ['혼자 가도', '되나요'], '릴스 · 12초'),
          ('RCB', ['예매 1분'], '릴스 · 12초'),
          ('RCC', ['9,900원'], '릴스 · 12초')]


def covers():
    yy = np.linspace(0, 1, BAND, dtype=np.float32)[:, None, None]
    row = PURPLE * (1 - yy ** 1.4) + DEEPC * (yy ** 1.4)
    row = np.repeat(row, W * 3, axis=1)
    xx = np.linspace(0, 1, W * 3, dtype=np.float32)[None, :, None]
    row += 0.06 * np.exp(-(((xx - 0.18) / 0.45) ** 2) - ((yy - 0.1) / 0.5) ** 2)
    sheet = Image.fromarray((np.clip(row, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(sheet)
    d.line([(M, int(BAND * 0.86)), (W * 3 - M, int(BAND * 0.86))], fill=WHITE + (110,), width=2)
    # 노란 선 하나가 셋을 지난다. 릴스 줄이라는 표시
    ly = int(BAND * 0.60)
    d.line([(0, ly), (W * 3, ly)], fill=ACCENT + (255,), width=6)

    tiles = []
    for i, (name, lines, sub) in enumerate(COVERS):
        band = sheet.crop((i * W, 0, (i + 1) * W, BAND)).convert('RGBA')
        d = ImageDraw.Draw(band)
        # 로고
        lg = logo_rgba(34)
        lgp = Image.fromarray((np.clip(lg, 0, 1) * 255).astype(np.uint8), 'RGBA')
        band.alpha_composite(lgp, (M, 96))
        # 제목. 노란 선 위에 올라탄다
        longest = max((l for _, ls, _ in COVERS for l in ls), key=len)
        for sz in range(180, 60, -4):
            if font(KRB, sz).getlength(longest) <= W - M * 2:
                break
        f = font(KRB, sz)
        y = ly - 30 - len(lines) * (sz + 10)
        for line in lines:
            d.text((M, y), line, font=f, fill=WHITE)
            y += sz + 10
        # 재생 표시 + 부제
        d.polygon([(M, ly + 40), (M, ly + 92), (M + 44, ly + 66)], fill=ACCENT)
        d.text((M + 64, ly + 44), sub, font=font(KR, 34), fill=WHITE + (220,))
        # CTA 판. 아래 줄(U4~U6)과 같은 자리
        fc = font(KRB, 34)
        cta = ('예매 → 프로필 링크', '예매 → 프로필 링크', 'App Store · 파티모아')[i]
        pw, ph = int(fc.getlength(cta) + 72), 92
        cy0 = int(BAND * 0.86) - 92 - 48
        d.rounded_rectangle([M, cy0, M + pw, cy0 + ph], 22, fill=ACCENT)
        d.text((M + 36, cy0 + (ph - 34) / 2 - 4), cta, font=fc, fill=(20, 12, 60))
        fb = font(KR, 22)
        d.text((M, int(BAND * 0.86) + 22), 'partymoa.com', font=fb, fill=WHITE + (200,))
        r = 'App Store'
        d.text((W - M - d.textlength(r, font=fb), int(BAND * 0.86) + 22), r, font=fb, fill=WHITE + (200,))

        full = Image.new('RGB', (W, H), DEEP)
        full.paste(band.convert('RGB'), (0, BAND_Y))
        full.save(os.path.join(OUT, f'{name}.jpg'), quality=94)
        tiles.append(band.convert('RGB'))

    g = Image.new('RGB', (W * 3 + 16, BAND * 2 + 8), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    # 그 아래 줄은 U6 U5 U4 (맨 윗줄에 있던 것)
    for i, name in enumerate(('U6', 'U5', 'U4')):
        p = os.path.join(OUT, f'{name}.jpg')
        if os.path.exists(p):
            g.paste(Image.open(p), (i * (W + 8), BAND + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_릴스커버격자.jpg'), quality=92)
    print('커버 완료')


def main(argv):
    want = set(argv) or {'a', 'b', 'c', 'cover'}
    if 'a' in want:
        reel_a()
    if 'b' in want:
        reel_b()
    if 'c' in want:
        reel_c()
    if 'cover' in want:
        covers()


if __name__ == '__main__':
    main(sys.argv[1:])
