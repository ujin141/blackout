"""
**릴스 세트 3편.** 마감(`push`) · 낮(`day`) · 밤(`dusk`). 각 15초 · 1080×1920.

    python reel_set.py            셋 다
    python reel_set.py push       골라서
    python reel_set.py day 2      2번 컷만 확인용으로

## 컷을 감으로 고르지 않는다

원본 아홉 개를 0.5초마다 훑어 **피부색 덩어리 개수**를 셌다(`out/_scan`).
사람이 여럿이면 얼굴·팔·다리가 여러 조각으로 흩어지고, 하늘·건물·집기는
0에 가깝다. 그 값이 **2초 내내 높게 유지되는** 구간만 골랐다.

앞서 만든 릴스들이 계속 '시작은 사람 가득, 끝은 빈 하늘' 이었던 게
시작 프레임만 보고 골랐기 때문이다. 아래 표의 컷은 전부 끝까지 사람이 있다.

**`P1023236` 은 통째로 뺐다.** 예거마이스터 병과 광고판이 화면을 채우는데
주황 라벨이 피부색 범위에 그대로 들어가 점수가 제일 높게 나왔다 —
숫자만 믿으면 협찬 영상이 될 뻔했다.

## 색

우진 지시 — 사람이 예뻐 보여야 한다. **채도를 올리면 반대가 된다.**
피부가 먼저 타서 주황색이 된다.

    curves     필름 S커브. 검정을 살짝 띄우고 하이라이트를 눌러 얼굴 톤을 남긴다
    vibrance   **채도가 낮은 곳만** 올린다. 이미 짙은 피부·입술은 안 건드린다
    colorbalance  미드톤을 따뜻하게, 하이라이트를 살짝 차갑게 — 얼굴이 살고
                  물이 시원해 보이는 조합이다

편마다 세기를 달리한다. 같은 색이면 세 편이 한 편처럼 보인다.

## 자막

`push` 는 정보가 주인공이라 컷마다 자막이 붙는다. `day` · `dusk` 는
분위기 편이라 **마지막 판에서만** 날짜·장소·예약을 말한다 — 셋 다
정보를 외치면 급한 게 아니라 시끄러운 게 된다.

숫자는 `event.py` 에서 온다. 판에 적으면 다음 차수에 거짓말이 된다.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

import audio_set
import event as EV
from fonts import KR, KRB, KRD
from poster_kit import BRAND

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'set')
TMP = os.path.join(HERE, 'out', '_setcuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30

# (파일, 시작초, 비트, 시작줌, 끝줌, 자막, 설명)
# 비트 합 = audio_set.PRESET 의 마디 × 4. 안 맞으면 build 가 멈춘다.
CUTS = {
    'push': [
        ('P1023237',  5.0, 5, 1.12, 1.00, 'hook',   '계단·풀 가득 (훅)'),
        ('P1023233',  1.0, 5, 1.00, 1.07, 'filled', '풀 안 물놀이'),
        ('P1023239',  4.5, 5, 1.00, 1.06, 'close',  'DJ'),
        ('P1023234', 16.0, 6, 1.08, 1.00, 'crew',   '풀 가득'),
        ('P1023234',  9.5, 5, 1.00, 1.08, 'nosale', '풀 가득 — 끝까지 사람'),
        ('P1023234', 41.0, 10, 1.06, 1.00, 'cta',   '하트 네온 + 풀 — 끝 판'),
    ],
    'day': [
        ('P1023235',  3.0, 6, 1.10, 1.00, None,   '풀 · 튜브 (훅)'),
        ('P1023233', 20.0, 5, 1.00, 1.07, None,   '루프탑 + 풀'),
        ('P1023234',  5.5, 5, 1.08, 1.00, None,   '풀 넓게'),
        ('P1023235', 11.4, 6, 1.00, 1.06, None,   '사람들'),
        ('P1023237', 14.4, 6, 1.06, 1.00, 'info', '튜브 · 팔 뻗기 — 정보'),
    ],
    'dusk': [
        ('P1023231',  8.5, 5, 1.12, 1.00, None,   '풀 가득 (훅)'),
        ('P1023234', 24.5, 5, 1.00, 1.07, None,   '풀 + 카바나'),
        ('P1023239', 12.0, 5, 1.00, 1.06, None,   'DJ — 믹서 위의 손'),
        ('P1023234', 13.5, 5, 1.08, 1.00, None,   '하트 네온 + 풀'),
        ('P1023235',  0.0, 5, 1.00, 1.07, None,   '풀 · 사람들'),
        ('P1023233', 32.0, 7, 1.06, 1.00, 'info', '핑크 LED + 사람 — 정보'),
    ],
}

# **채도를 올리면 피부가 먼저 탄다.** vibrance 로 옅은 데만 끌어올리고,
# 커브로 하이라이트를 눌러 얼굴 톤을 남긴다
GRADE = {
    'push': ("curves=master='0/0.018 0.25/0.22 0.5/0.52 0.75/0.80 1/0.98',"
             "vibrance=intensity=0.30,"
             "colorbalance=rm=0.02:gm=0.004:bm=-0.014:rh=0.01:bh=0.02,"
             "eq=contrast=1.10:saturation=1.06:gamma=1.00"),
    'day':  ("curves=master='0/0.022 0.25/0.24 0.5/0.54 0.75/0.81 1/0.985',"
             "vibrance=intensity=0.34,"
             "colorbalance=rm=0.035:gm=0.010:bm=-0.020:rh=0.03:bh=-0.02,"
             "eq=contrast=1.04:saturation=1.05:gamma=1.03:brightness=0.020"),
    'dusk': ("curves=master='0/0.014 0.25/0.21 0.5/0.51 0.75/0.79 1/0.98',"
             "vibrance=intensity=0.28,"
             "colorbalance=rm=0.020:gm=0.000:bm=0.010:rh=-0.02:bh=0.045,"
             "eq=contrast=1.14:saturation=1.08:gamma=0.98"),
}

SAFE_T, SAFE_B = 0.16, 0.72          # 릴스 UI 가 위 14% · 아래 25% 를 덮는다


def _f(path, size):
    """**BRAND(Michroma)는 영문·숫자 전용.** 한글을 넘기면 두부가 찍힌다."""
    return ImageFont.truetype(path, size)


def _fit(d, text, path, size, track, maxw):
    while size > 10:
        f = _f(path, size)
        w = sum(d.textlength(c, font=f) for c in text) + track * (len(text) - 1)
        if w <= maxw:
            return f
        size -= 1
    return _f(path, 10)


def _mid(d, y, text, font, fill, track=0):
    if track:
        ws = [d.textlength(c, font=font) for c in text]
        x = (W - (sum(ws) + track * (len(text) - 1))) / 2
        for c, w in zip(text, ws):
            d.text((x, y), c, font=font, fill=fill)
            x += w + track
        return
    d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font, fill=fill)


def _plate(d, y0, y1, a=170):
    """자막 뒤. **띠를 두르지 않는다** — 위아래로 풀어야 화면이 어두워진
    것으로 읽히지 얹은 판으로 안 읽힌다."""
    n = int(y1 - y0)
    for i in range(n):
        t = i / max(1, n - 1)
        d.line([(0, y0 + i), (W, y0 + i)],
               fill=(0, 0, 0, int(a * (1 - abs(t * 2 - 1)) ** 0.7)))


def overlay(kind, tag, i):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    left = str(EV.OPEN_LEFT)
    wave = EV.OPEN_WAVE

    if kind == 'hook':
        _plate(d, H * 0.20, H * 0.70, 178)
        d.text((W / 2, H * 0.395), left, font=_f(KRD, 540),
               fill=(255, 255, 255, 255), anchor='mm')
        _mid(d, H * 0.545, f'{wave[0]} 예약 {left}자리 남았습니다',
             _f(KRB, 56), (255, 255, 255, 242))

    elif kind == 'filled':
        _plate(d, H * 0.26, H * 0.62, 168)
        _mid(d, H * 0.335, f'{wave[0]} {wave[1]}명 중 {wave[2]}명이 찼습니다',
             _f(KRB, 62), (255, 255, 255, 246))
        bx0, bx1, by = W * 0.16, W * 0.84, H * 0.455
        d.rounded_rectangle([bx0, by, bx1, by + 22], 11, fill=(255, 255, 255, 62))
        d.rounded_rectangle([bx0, by, bx0 + (bx1 - bx0) * wave[2] / wave[1],
                             by + 22], 11, fill=(255, 255, 255, 240))
        _mid(d, by + 48, f'{wave[2]} / {wave[1]}', _f(BRAND, 34),
             (255, 255, 255, 205), track=6)

    elif kind == 'close':
        _plate(d, H * 0.23, H * 0.60, 180)
        _mid(d, H * 0.295, f'{wave[0]} 예약', _f(KRB, 42), (208, 214, 226, 224))
        _mid(d, H * 0.355, f'오늘 {wave[3]} 자정에 닫습니다', _f(KRD, 80),
             (255, 255, 255, 252))

    elif kind == 'crew':
        _plate(d, H * 0.24, H * 0.58, 165)
        _mid(d, H * 0.300, f'DJ {len(EV.LINEUP)}명  ·  솔로파티 90분',
             _f(KRB, 60), (255, 255, 255, 246))
        _mid(d, H * 0.378, EV.LINEUP_STR,
             _fit(d, EV.LINEUP_STR, BRAND, 27, 4, W * 0.86),
             (210, 214, 224, 222), track=4)

    elif kind == 'nosale':
        _plate(d, H * 0.17, H * 0.58, 205)
        _mid(d, H * 0.255, EV.PRICE_PUSH, _f(KRD, 90), (255, 255, 255, 252))
        _mid(d, H * 0.355, '문 앞에서 살 수 없습니다', _f(KR, 46),
             (216, 220, 230, 230))

    elif kind == 'cta':
        _plate(d, H * 0.20, H * 0.68, 190)
        _mid(d, H * 0.260, EV.STATUS_LINES[0], _f(KRB, 38), (208, 214, 226, 224))
        _mid(d, H * 0.320, f'{left}자리', _f(KRD, 130), (255, 255, 255, 252))
        _mid(d, H * 0.432, '프로필 링크에서 예약', _f(KRB, 56), (255, 255, 255, 246))
        _mid(d, H * 0.500, EV.HANDLE, _f(BRAND, 28), (210, 214, 224, 218), track=6)

    elif kind == 'info':
        # 분위기 편의 끝 판. **여기서만 정보를 말한다**
        _plate(d, H * 0.20, H * 0.68, 190)
        _mid(d, H * 0.250, EV.NAME, _f(BRAND, 64), (255, 255, 255, 250), track=8)
        _mid(d, H * 0.330, f'{EV.DATE} · {EV.VENUE}', _f(KRB, 46),
             (255, 255, 255, 240))
        _mid(d, H * 0.392, EV.ADDR, _f(KR, 34), (210, 214, 224, 220))
        _mid(d, H * 0.470, f'{wave[0]} {left}자리 · 오늘 마감', _f(KRD, 58),
             (255, 255, 255, 250))
        _mid(d, H * 0.548, '프로필 링크에서 예약', _f(KRB, 44),
             (255, 255, 255, 242))

    p = os.path.join(TMP, f'ov_{tag}_{i:02d}.png')
    im.save(p)
    return p


def run(args):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(' '.join(args[:6]) + ' …\n' + r.stderr[-1500:])
    return r


def cut_path(tag, i):
    return os.path.join(TMP, f'{tag}_{i:02d}.mp4')


def make_cut(tag, i, c):
    """컷 하나. **원본이 이미 9:16 이라 크롭하지 않는다**(회전 메타데이터)."""
    src, t0, beats, z0, z1, kind, _ = c
    beat = 60.0 / audio_set.PRESET[tag]['bpm']
    dur = beats * beat
    nf = max(1, int(round(dur * FPS)))
    zp = (f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS}")
    base = f'fps={FPS},{zp},{GRADE[tag]},unsharp=5:5:0.40'
    args = ['ffmpeg', '-v', 'error', '-ss', str(t0),
            '-i', os.path.join(SRC, f'{src}.MOV')]
    if kind:
        args += ['-i', overlay(kind, tag, i)]
        vf = (f'[0:v]{base}[v];[v][1:v]overlay=0:0,'
              f'scale=out_range=tv,format=yuv420p[o]')
        args += ['-t', f'{dur:.4f}', '-filter_complex', vf, '-map', '[o]']
    else:
        args += ['-t', f'{dur:.4f}', '-vf',
                 f'{base},scale=out_range=tv,format=yuv420p']
    args += ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
             '-pix_fmt', 'yuv420p', '-y', cut_path(tag, i)]
    run(args)
    return dur


def clip_len(src):
    return float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', os.path.join(SRC, f'{src}.MOV')],
        capture_output=True, text=True).stdout.strip())


def check(tag):
    want = audio_set.PRESET[tag]['bars'] * 4
    got = sum(c[2] for c in CUTS[tag])
    assert got == want, f'{tag}: 비트 합 {got} ≠ 곡 {want} 비트'
    # **컷이 클립 끝을 넘으면 조용히 짧아진다.** day 가 곡보다 1.4초 짧게
    # 나왔던 게 이것 때문이었다 — 에러도 안 나고 그냥 잘린다
    beat = 60.0 / audio_set.PRESET[tag]['bpm']
    for c in CUTS[tag]:
        end = c[1] + c[2] * beat
        n = clip_len(c[0])
        assert end <= n - 0.05, (f'{tag}: {c[0]}@{c[1]} 이 {end:.2f}초까지 가는데 '
                                 f'클립은 {n:.2f}초다')
    seen = set()
    for c in CUTS[tag]:
        k = (c[0], c[1])
        assert k not in seen, f'{tag}: {k} 가 두 번'
        seen.add(k)
    for other in CUTS:
        if other == tag:
            continue
        dup = seen & {(c[0], c[1]) for c in CUTS[other]}
        assert not dup, f'{tag} 와 {other} 가 겹친다: {dup}'


def build(tag):
    check(tag)
    bgm = audio_set.build(tag)
    durs = [make_cut(tag, i, c) for i, c in enumerate(CUTS[tag])]
    lst = os.path.join(TMP, f'{tag}.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS[tag])):
            fh.write("file '" + cut_path(tag, i).replace(os.sep, '/') + "'\n")
    silent = os.path.join(TMP, f'{tag}_silent.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-y', silent])
    # 컷마다 프레임이 반올림되면서 영상이 곡보다 짧아진다 — 재서 맞춘다
    vlen = float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', silent], capture_output=True, text=True).stdout.strip())
    out = os.path.join(OUT, f'{tag}.mp4')
    run(['ffmpeg', '-v', 'error', '-i', silent, '-i', bgm,
         '-af', f'atrim=0:{vlen:.3f},asetpts=N/SR/TB,'
                f'afade=t=out:st={max(0.0, vlen - 0.5):.3f}:d=0.5',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', '-y', out])
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'format=duration,size,bit_rate',
                        '-of', 'csv=p=0', out],
                       capture_output=True, text=True).stdout.strip().split(',')
    print(f'{out}  {W}×{H} · {FPS}fps · {float(q[0]):.2f}초 · '
          f'{int(q[1])/1e6:.1f}MB · 컷 {len(CUTS[tag])}개')
    for i, c in enumerate(CUTS[tag]):
        print(f'  {i:2d} {c[0]} @{c[1]:5.1f}s  {durs[i]:.2f}s  '
              f'{(c[5] or "—"):7s} {c[6]}')
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    # `reel_set.py day dusk` 를 'day 의 dusk 번 컷' 으로 읽던 버그 — 숫자일 때만
    if a and a[0] in CUTS and len(a) > 1 and a[1].isdigit():
        make_cut(a[0], int(a[1]), CUTS[a[0]][int(a[1])])
        print(cut_path(a[0], int(a[1])))
    else:
        for k in (a or list(CUTS)):
            if k not in CUTS:
                raise SystemExit(f'{k} 은 없습니다 — {", ".join(CUTS)}')
            build(k)
