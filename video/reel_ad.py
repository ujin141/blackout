"""
**광고 릴스.** 파티를 보다가 SOLD OUT 을 발견하게 만든다. 22초 · 1080×1920.

    python reel_ad.py       만든다
    python reel_ad.py 3     3번 컷만 확인용으로

## `reel_set` 의 push 와 뭐가 다른가

push 는 **첫 프레임부터 숫자**다. 이미 우리를 아는 사람에게 "지금 몇 자리
남았다" 를 알리는 판이라 그게 맞다.

이건 광고다. **우리를 모르는 사람이 대상**이라 첫 2초에 정보를 던지면
광고로 인식되고 넘어간다. 순서를 뒤집는다.

    0~2초    가장 강렬한 장면 + 질문 한 줄. 정보 없음
    2~11초   자막 없이 컷만. 빠르게 — 파티가 어떤 파티인지 그림으로
    11~15초  **브레이크.** 음악이 얇아지고 1차·2차 SOLD OUT 이 뜬다
    15~18초  3차 OPEN
    18~22초  날짜 · 장소 · 값 · 예약

ENTERTAIN → CURIOSITY → SOCIAL PROOF → FOMO → RESERVATION.

## 컷을 왜 이렇게 짧게 자르나

분위기 릴스는 컷이 2.4~2.7초다. 장면을 읽을 시간을 주는 게 목적이라 그게
맞다. 광고는 **완주율이 KPI**라 다르다 — 한 컷이 길면 그 컷에서 나간다.

여기는 **0.9~1.4초**로 자른다. 131BPM 에서 2~3비트다. 마디 경계가 곧
킥이라 컷이 박에 맞고, 소리와 그림이 같이 움직이면 그것만으로 완주가 는다.

**마지막 세 컷만 길다.** 정보를 읽어야 하는 자리라 2초 이상 준다.

## 자막이 앉는 자리

브레이크(마디 8~9)에 SOLD OUT 을 얹는다. **드롭 위에 글자를 얹으면
아무도 안 읽는다** — 소리가 얇아지는 순간 눈이 글자로 간다.

릴스 UI 가 위 14% · 아래 25% 를 덮으므로 글자는 0.18H ~ 0.70H 안에 둔다.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

import audio_ad
import event as EV
from fonts import KR, KRB, KRD
from poster_kit import BRAND

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'ad')
TMP = os.path.join(HERE, 'out', '_adcuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BEAT = 60.0 / audio_ad.BPM

# (파일, 시작초, 비트, 시작줌, 끝줌, 자막)
# 비트 합 = audio_ad.BARS * 4 = 48. 안 맞으면 build 가 멈춘다.
CUTS = [
    ('P1023237',  5.0, 4, 1.05, 1.00, 'hook'),      # 훅 — 사람 제일 많은 컷
    ('P1023234', 16.5, 3, 1.00, 1.04, None),
    ('P1023233',  1.0, 3, 1.04, 1.00, None),
    ('P1023235',  3.0, 3, 1.00, 1.04, None),
    ('P1023234', 24.5, 3, 1.04, 1.00, None),
    ('P1023231',  8.5, 3, 1.00, 1.04, None),
    ('P1023233', 20.0, 3, 1.03, 1.00, None),
    ('P1023234',  9.5, 3, 1.00, 1.04, None),
    ('P1023235',  0.0, 3, 1.03, 1.00, None),
    ('P1023234', 12.0, 4, 1.00, 1.04, None),
    ('P1023233', 29.0, 4, 1.03, 1.00, 'sold1'),     # 여기부터 브레이크
    ('P1023234',  5.5, 4, 1.00, 1.03, 'sold2'),
    ('P1023237', 15.5, 5, 1.02, 1.00, 'open'),      # 재드롭
    ('P1023233', 32.0, 6, 1.00, 1.03, 'info'),
    ('P1023234', 41.0, 5, 1.02, 1.00, 'cta'),
]

# 밤 · 네온 쪽으로. **얼굴이 뭉개지지 않게** 커브로 하이라이트만 누른다
GRADE = ("curves=master='0/0.016 0.25/0.21 0.5/0.51 0.75/0.79 1/0.98',"
         'vibrance=intensity=0.28,'
         'colorbalance=rm=0.020:gm=0.000:bm=0.012:rh=-0.02:bh=0.042,'
         'eq=contrast=1.14:saturation=1.06:gamma=0.97')


def _f(path, size):
    """**BRAND(Michroma)는 영문·숫자 전용.** 한글을 넘기면 두부가 찍힌다."""
    return ImageFont.truetype(path, size)


def _mid(d, y, text, font, fill, track=0):
    if track:
        ws = [d.textlength(c, font=font) for c in text]
        x = (W - (sum(ws) + track * (len(text) - 1))) / 2
        for c, w in zip(text, ws):
            d.text((x, y), c, font=font, fill=fill)
            x += w + track
        return
    d.text(((W - d.textlength(text, font=font)) / 2, y), text, font=font,
           fill=fill)


def _plate(d, y0, y1, a=175):
    """자막 뒤. 띠가 아니라 화면이 어두워진 것으로 읽혀야 한다."""
    n = int(y1 - y0)
    for i in range(n):
        t = i / max(1, n - 1)
        d.line([(0, y0 + i), (W, y0 + i)],
               fill=(0, 0, 0, int(a * (1 - abs(t * 2 - 1)) ** 0.7)))


def overlay(kind, i):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w3 = EV.OPEN_WAVE

    if kind == 'hook':
        # **정보를 안 준다.** 질문 하나로 '뭐지?' 만 만든다
        _plate(d, H * 0.30, H * 0.62, 165)
        _mid(d, H * 0.395, '이번 주말', _f(KRD, 108), (255, 255, 255, 252))
        _mid(d, H * 0.475, '어디 감?', _f(KRD, 108), (255, 255, 255, 252))

    elif kind in ('sold1', 'sold2'):
        # 브레이크. 음악이 얇아진 자리라 글자가 읽힌다
        name = EV.WAVES[0][0] if kind == 'sold1' else EV.WAVES[1][0]
        _plate(d, H * 0.26, H * 0.60, 190)
        _mid(d, H * 0.335, name, _f(KRD, 130), (255, 255, 255, 250))
        t = 'SOLD OUT'
        f = _f(BRAND, 72)
        ws = [d.textlength(c, font=f) for c in t]
        tw = sum(ws) + 10 * (len(t) - 1)
        _mid(d, H * 0.455, t, f, (255, 255, 255, 250), track=10)
        # 취소선 — 끝났다는 걸 글자 스스로 말한다
        d.line([((W - tw) / 2 - 10, H * 0.455 + 46),
                ((W + tw) / 2 + 10, H * 0.455 + 46)],
               fill=(255, 255, 255, 235), width=6)

    elif kind == 'open':
        _plate(d, H * 0.22, H * 0.64, 195)
        _mid(d, H * 0.290, w3[0], _f(KRD, 130), (255, 255, 255, 252))
        # 흰 판 반전 — 유일하게 열린 문
        d.rectangle([W * 0.10, H * 0.425, W * 0.90, H * 0.425 + 106],
                    fill=(255, 255, 255, 248))
        _mid(d, H * 0.425 + 22, '예약 OPEN', _f(KRD, 62), (6, 6, 8, 255))
        _mid(d, H * 0.545, f'{EV.OPEN_LEFT}자리 남았습니다', _f(KRB, 46),
             (255, 255, 255, 244))

    elif kind == 'info':
        _plate(d, H * 0.22, H * 0.66, 195)
        _mid(d, H * 0.270, EV.NAME, _f(BRAND, 62), (255, 255, 255, 250),
             track=8)
        _mid(d, H * 0.345, f'{EV.DATE}  ·  {EV.VENUE}', _f(KRB, 44),
             (255, 255, 255, 242))
        pr = EV.PRICE.get(w3[0])
        if pr:
            _mid(d, H * 0.425, f"여 {pr['여']:,}   ·   남 {pr['남']:,}",
                 _f(KRD, 52), (255, 255, 255, 250))
        _mid(d, H * 0.510, f'{EV.CAP}명 한정  ·  {EV.PERKS} 포함', _f(KR, 34),
             (222, 226, 234, 232))

    elif kind == 'cta':
        _plate(d, H * 0.24, H * 0.64, 200)
        d.rectangle([W * 0.10, H * 0.335, W * 0.90, H * 0.335 + 118],
                    fill=(255, 255, 255, 250))
        _mid(d, H * 0.335 + 26, '프로필 링크에서 예약', _f(KRD, 58),
             (6, 6, 8, 255))
        _mid(d, H * 0.505, EV.HANDLE, _f(BRAND, 30), (226, 230, 238, 226),
             track=6)

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


def clip_len(src):
    return float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', os.path.join(SRC, f'{src}.MOV')],
        capture_output=True, text=True).stdout.strip())


def make_cut(i, c):
    """컷 하나. **원본이 이미 9:16 이라 크롭하지 않는다**(회전 메타데이터)."""
    src, t0, beats, z0, z1, kind = c
    dur = beats * BEAT
    nf = max(1, int(round(dur * FPS)))
    zp = (f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS}")
    base = f'fps={FPS},{zp},{GRADE},unsharp=5:5:0.40'
    args = ['ffmpeg', '-v', 'error', '-ss', str(t0),
            '-i', os.path.join(SRC, f'{src}.MOV')]
    if kind:
        args += ['-i', overlay(kind, i)]
        args += ['-t', f'{dur:.4f}', '-filter_complex',
                 f'[0:v]{base}[v];[v][1:v]overlay=0:0,'
                 f'scale=out_range=tv,format=yuv420p[o]', '-map', '[o]']
    else:
        args += ['-t', f'{dur:.4f}', '-vf',
                 f'{base},scale=out_range=tv,format=yuv420p']
    args += ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
             '-pix_fmt', 'yuv420p', '-y', cut_path(i)]
    run(args)
    return dur


def check():
    want = audio_ad.BARS * 4
    got = sum(c[2] for c in CUTS)
    assert got == want, f'비트 합 {got} ≠ 곡 {want} 비트'
    for c in CUTS:
        end = c[1] + c[2] * BEAT
        n = clip_len(c[0])
        assert end <= n - 0.05, f'{c[0]}@{c[1]} 이 {end:.2f}초까지 — 클립은 {n:.2f}초'
    seen = set()
    for c in CUTS:
        for d in CUTS:
            if c is d or c[0] != d[0]:
                continue
            a0, a1 = c[1], c[1] + c[2] * BEAT
            b0, b1 = d[1], d[1] + d[2] * BEAT
            assert a1 <= b0 or b1 <= a0, f'{c[0]} 안에서 {c[1]} 과 {d[1]} 이 겹친다'
    # 브레이크에 SOLD OUT 이 앉는지 — 어긋나면 드롭 위에 글자가 얹힌다
    t = 0.0
    for c in CUTS:
        if c[5] == 'sold1':
            bar = t / (BEAT * 4)
            assert abs(bar - audio_ad.BREAK_IN) < 0.6, (
                f'SOLD OUT 이 {bar:.1f}마디에 있다 — 브레이크는 '
                f'{audio_ad.BREAK_IN}마디다')
        t += c[2] * BEAT


def build():
    check()
    bgm = audio_ad.build()
    durs = [make_cut(i, c) for i, c in enumerate(CUTS)]
    lst = os.path.join(TMP, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS)):
            fh.write("file '" + cut_path(i).replace(os.sep, '/') + "'\n")
    silent = os.path.join(TMP, 'silent.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-y', silent])
    vlen = float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', silent], capture_output=True, text=True).stdout.strip())
    out = os.path.join(OUT, 'ad.mp4')
    run(['ffmpeg', '-v', 'error', '-i', silent, '-i', bgm,
         '-af', f'atrim=0:{vlen:.3f},asetpts=N/SR/TB,'
                f'afade=t=out:st={max(0.0, vlen - 0.55):.3f}:d=0.55',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', '-y', out])
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'format=duration,size,bit_rate',
                        '-of', 'csv=p=0', out],
                       capture_output=True, text=True).stdout.strip().split(',')
    print(f'{out}  {W}×{H} · {FPS}fps · {float(q[0]):.2f}초 · '
          f'{int(q[1])/1e6:.1f}MB · 컷 {len(CUTS)}개')
    t = 0.0
    for i, c in enumerate(CUTS):
        print(f'  {i:2d} {t:5.2f}s  {c[0]} @{c[1]:5.1f}s  {durs[i]:.2f}s  '
              f'{c[5] or "—"}')
        t += durs[i]
    return out


if __name__ == '__main__':
    if sys.argv[1:]:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i))
    else:
        build()
