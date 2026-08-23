"""
**2차 마감 릴스.** 현장 영상 위에 자막을 얹는다. 15초 · 1080×1920.

    python reel_close.py           → out/reel/close.mp4
    python reel_close.py 0         → 0번 컷만 확인용으로

## 각 — 이미 있는 것과 뭐가 다른가

`pool` 은 현장, `sunset` 은 낮에서 밤으로, `lineup` 은 라인업이다. **셋 다
"이 파티가 어떤 파티인가" 를 말한다.** 이 판은 **"지금 안 하면 못 한다"**
하나만 말한다 — 각이 겹치지 않는다.

## 훅

첫 1초가 전부다. 릴스는 그 안에 안 잡히면 넘어간다.

    쓰지 않는 것   "풀파티 합니다" · "라인업 공개" — 정보라서 안 멈춘다
    쓰는 것        **숫자 하나.** `10` 을 화면 절반 크기로 놓는다

숫자는 읽는 게 아니라 보인다. 무슨 뜻인지 모르는 채로 1초가 지나가고,
그 1초 동안 뒤에서 사람들이 놀고 있다 — 그다음 자막이 뜻을 알려 준다.

## 정직하게 센다

**"마지막 기회" 라고 쓰지 않는다.** 3차가 남아 있다. 거짓말을 하면 3차를
열 때 그 말이 그대로 돌아온다.

여기서 파는 건 **2차 잔여 10자리와 오늘이라는 기한**이다. 그것만으로
충분히 급하다 — 숫자가 진짜라서.

값이 오른다는 말도 안 쓴다(`SHOW_PRICE = False`). 그 자리는 **현장 판매를
안 한다**는 사실이 채운다. 오늘 못 잡으면 3차를 기다려야 하고, 3차가
닫히면 그날 문 앞에서 살 방법이 없다.

## 숫자는 event.py 에서 온다

`10` 도 `20` 도 여기 안 적혀 있다. 차수가 차면 `WAVES` 만 고치면 자막이
따라온다 — 판에 숫자를 박으면 다음 차수에 거짓말이 된다.

## 자막 자리

    위 14%    프로필·팔로우 버튼이 덮는다
    아래 25%  캡션·좋아요·공유가 덮는다

그래서 글자는 **0.16H ~ 0.72H** 안에만 둔다. 훅의 큰 숫자만 가운데다.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fonts import KR, KRB, KRD
from poster_kit import BRAND
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'reel')
TMP = os.path.join(HERE, 'out', '_closecuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BEAT = 0.5                                   # 120BPM

SAFE_T, SAFE_B = 0.16, 0.72                  # 글자를 두는 세로 범위

# **문구를 여기 모아 둔다.** 판 안에 흩어 놓으면 한 줄 바꾸려고 코드를 뒤진다.
BIG    = str(EV.OPEN_LEFT)                        # 10
SUB    = f'{EV.OPEN_WAVE[0]} 남은 자리'           # 2차 남은 자리
FILLED = (f'{EV.OPEN_WAVE[0]} {EV.OPEN_WAVE[1]}명 중 '
          f'{EV.OPEN_WAVE[2]}명이 찼습니다')
CLOSE  = f'오늘 {EV.OPEN_WAVE[3]} 자정에 닫습니다'
NOSALE = EV.PRICE_PUSH                            # 현장 판매 없습니다
CREW   = f'DJ {len(EV.LINEUP)}명  ·  솔로파티 90분'
WHERE  = f'{EV.DATE} · {EV.VENUE}'
CTA    = '프로필 링크에서 예약'

# (파일, 시작초, 비트, 시작줌, 끝줌, 자막 종류, 설명)
CUTS = [
    ('P1023234', 24.0, 3, 1.14, 1.00, 'hook',  '풀에 사람 가득 (훅)'),
    ('P1023233', 20.0, 4, 1.00, 1.09, 'filled', '루프탑 전경 + 풀'),
    ('P1023239', 14.0, 4, 1.00, 1.07, 'close',  'DJ — 믹서 위의 손'),
    ('P1023232',  3.0, 4, 1.08, 1.00, 'nosale', 'ADULT ONLY 네온'),
    ('P1023235',  1.4, 5, 1.10, 1.00, 'crew',   '풀 가득 · 튜브'),
    ('P1023231',  9.0, 5, 1.00, 1.08, 'where',  '풀에 사람 가득'),
    ('P1023237', 10.2, 5, 1.00, 1.07, 'cta',    '튜브·계단 — 끝까지 사람이 있다'),
]


def _font(path, size):
    """**BRAND(Michroma)는 영문·숫자 전용이다.** 한글을 넘기면 두부(□)가 찍힌다 —
    실제로 '2차 예약' 과 '1차 사전예약 SOLD OUT' 이 그렇게 나갔다."""
    return ImageFont.truetype(path, size)


def _fit(d, text, path, size, track, maxw):
    """폭을 넘으면 크기를 줄인다. 라인업이 여덟 명이 되면서 한 줄이 화면
    밖으로 흘렀다 — 사람 수가 늘어도 안 넘치게 재서 줄인다."""
    while size > 10:
        f = _font(path, size)
        w = sum(d.textlength(c, font=f) for c in text) + track * (len(text) - 1)
        if w <= maxw:
            return f
        size -= 1
    return _font(path, 10)


def _center(d, y, text, font, fill, track=0):
    """가운데 정렬 한 줄. `track` 은 자간(px)."""
    if track:
        ws = [d.textlength(c, font=font) for c in text]
        total = sum(ws) + track * (len(text) - 1)
        x = (W - total) / 2
        for c, w in zip(text, ws):
            d.text((x, y), c, font=font, fill=fill)
            x += w + track
        return total
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)
    return w


def _plate(d, y0, y1, a=150):
    """자막 뒤 판. **띠를 두르지 않는다** — 위아래로 풀리는 그라데이션이라
    얹은 물건이 아니라 화면이 어두워진 것으로 읽힌다."""
    n = int(y1 - y0)
    for i in range(n):
        t = i / max(1, n - 1)
        k = (1 - abs(t * 2 - 1)) ** 0.7
        d.line([(0, y0 + i), (W, y0 + i)], fill=(0, 0, 0, int(a * k)))


def overlay(kind, i):
    """자막 한 장을 RGBA PNG 로. 컷마다 하나씩."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    if kind == 'hook':
        # **숫자가 주인공이다.** 뜻은 그 아래 한 줄이 알려 준다
        _plate(d, H * 0.20, H * 0.70, 175)
        # **앵커로 가운데를 잡는다.** textbbox 로 맞췄더니 왼쪽으로 치우쳤다
        d.text((W / 2, H * 0.40), BIG, font=_font(KRD, 540),
               fill=(255, 255, 255, 255), anchor='mm')
        _center(d, H * 0.545, f'{EV.OPEN_WAVE[0]} 예약 {BIG}자리 남았습니다',
                _font(KRB, 56), (255, 255, 255, 240))

    elif kind == 'filled':
        _plate(d, H * 0.26, H * 0.62, 165)
        _center(d, H * 0.34, FILLED, _font(KRB, 66), (255, 255, 255, 245))
        # 막대 — 20/30 이 얼마나 찬 건지 숫자보다 빠르게 읽힌다
        bx0, bx1, by = W * 0.16, W * 0.84, H * 0.46
        d.rounded_rectangle([bx0, by, bx1, by + 22], 11, fill=(255, 255, 255, 60))
        p = EV.OPEN_WAVE[2] / EV.OPEN_WAVE[1]
        d.rounded_rectangle([bx0, by, bx0 + (bx1 - bx0) * p, by + 22], 11,
                            fill=(255, 255, 255, 240))
        _center(d, by + 48, f'{EV.OPEN_WAVE[2]} / {EV.OPEN_WAVE[1]}',
                _font(BRAND, 34), (255, 255, 255, 200), track=6)

    elif kind == 'close':
        _plate(d, H * 0.24, H * 0.60, 175)
        _center(d, H * 0.30, f'{EV.OPEN_WAVE[0]} 예약', _font(KRB, 42),
                (206, 212, 224, 220))
        _center(d, H * 0.36, CLOSE, _font(KRD, 84), (255, 255, 255, 250))

    elif kind == 'nosale':
        _plate(d, H * 0.17, H * 0.58, 205)
        _center(d, H * 0.26, NOSALE, _font(KRD, 92), (255, 255, 255, 252))
        _center(d, H * 0.36, '문 앞에서 살 수 없습니다', _font(KR, 46),
                (214, 218, 228, 230))

    elif kind == 'crew':
        _plate(d, H * 0.24, H * 0.58, 160)
        _center(d, H * 0.30, CREW, _font(KRB, 62), (255, 255, 255, 245))
        _center(d, H * 0.38, EV.LINEUP_STR,
                _fit(d, EV.LINEUP_STR, BRAND, 27, 4, W * 0.86),
                (208, 212, 222, 220), track=4)

    elif kind == 'where':
        _plate(d, H * 0.24, H * 0.62, 165)
        _center(d, H * 0.29, EV.NAME, _font(BRAND, 66), (255, 255, 255, 250),
                track=8)
        _center(d, H * 0.375, WHERE, _font(KRB, 46), (255, 255, 255, 235))
        _center(d, H * 0.435, EV.ADDR, _font(KR, 34), (208, 212, 222, 215))

    elif kind == 'cta':
        _plate(d, H * 0.22, H * 0.66, 185)
        _center(d, H * 0.28, EV.STATUS_LINES[0], _font(KRB, 38),
                (206, 212, 224, 220))
        _center(d, H * 0.345, f'{BIG}자리', _font(KRD, 130),
                (255, 255, 255, 252))
        _center(d, H * 0.455, CTA, _font(KRB, 56), (255, 255, 255, 245))
        _center(d, H * 0.525, EV.HANDLE, _font(BRAND, 28),
                (208, 212, 222, 215), track=6)

    p = os.path.join(TMP, f'ov_{i:02d}.png')
    im.save(p)
    return p


def run(args):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(' '.join(args[:6]) + ' …\n' + r.stderr[-1500:])
    return r


def cut_path(i):
    return os.path.join(TMP, f'cut_{i:02d}.mp4')


def make_cut(i, c):
    """컷 하나 + 자막. **원본은 이미 9:16 이다** — 크롭하지 않는다."""
    name, t0, beats, z0, z1, kind, _ = c
    dur = beats * BEAT
    nf = max(1, int(round(dur * FPS)))
    ov = overlay(kind, i)
    vf = (f'[0:v]fps={FPS},'
          f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)*0.5':y='(ih-ih/zoom)*0.5':s={W}x{H}:fps={FPS},"
          f'eq=contrast=1.22:saturation=1.30:gamma=0.94:brightness=0.02,'
          f'unsharp=5:5:0.5[v];'
          f'[v][1:v]overlay=0:0,scale=out_range=tv,format=yuv420p[o]')
    af = (f'afade=t=in:st=0:d=0.03,'
          f'afade=t=out:st={max(0.0, dur - 0.03):.3f}:d=0.03,aresample=48000')
    run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-i',
         os.path.join(SRC, f'{name}.MOV'), '-i', ov, '-t', str(dur),
         '-filter_complex', vf, '-map', '[o]', '-map', '0:a',
         '-af', af,
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
         '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-y', cut_path(i)])
    return dur


def ticks(total):
    """훅에 얹는 초읽기. **현장 소리를 지우지 않는다** — 위에 살짝 얹는다.
    시계 소리가 나면 '기한' 이라는 말을 안 해도 급해진다."""
    sr = 48000
    buf = np.zeros(int(total * sr), np.float32)
    for k in range(3):
        i = int(k * 0.5 * sr)
        n = int(sr * 0.045)
        t = np.arange(n, dtype=np.float32) / sr
        env = np.exp(-t * 130)
        s = (np.sin(2 * np.pi * 2400 * t) * 0.6
             + np.sin(2 * np.pi * 3700 * t) * 0.4) * env
        s += np.random.default_rng(k).standard_normal(n).astype(np.float32) * env * 0.25
        j = min(len(buf), i + n)
        if j > i:
            buf[i:j] += s[:j - i] * (0.34 if k < 2 else 0.44)
    buf = np.clip(buf, -1, 1)
    p = os.path.join(TMP, 'ticks.wav')
    w = wave.open(p, 'w')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes((buf * 32767).astype(np.int16).tobytes())
    w.close()
    return p


def build():
    durs = [make_cut(i, c) for i, c in enumerate(CUTS)]
    lst = os.path.join(TMP, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS)):
            fh.write("file '" + cut_path(i).replace(os.sep, '/') + "'\n")
    joined = os.path.join(TMP, 'joined.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-y', joined])

    out = os.path.join(OUT, 'close.mp4')
    tk = ticks(sum(durs))
    run(['ffmpeg', '-v', 'error', '-i', joined, '-i', tk,
         '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:'
                            'weights=1 0.9:normalize=0[a]',
         '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-y', out])

    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'stream=codec_name,width,height',
                        '-show_entries', 'format=size,bit_rate',
                        '-of', 'csv=p=0', out], capture_output=True, text=True)
    info = [l for l in q.stdout.splitlines() if l.strip()]
    if len(info) > 2:
        sz, br = info[-1].split(',')[:2]
        print(f'  용량: {int(sz)/1e6:.1f}MB · {int(br)/1e6:.1f}Mbps')
    print(f'{out}  {W}×{H} · {FPS}fps · {sum(durs):.1f}초 · 컷 {len(CUTS)}개')
    for i, c in enumerate(CUTS):
        print(f'  {i:2d}  {c[0]} @{c[1]:5.1f}s  {c[2] * BEAT:.1f}s  '
              f'{c[5]:7s} {c[6]}')
    return out


if __name__ == '__main__':
    if sys.argv[1:]:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i), CUTS[i][6])
    else:
        build()
