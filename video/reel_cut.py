"""
**현장 컷 릴스 두 편.** `sunset` 과 같은 문법 — 자막 없이 곡에 맞춰 자른다.

    python reel_cut.py             둘 다
    python reel_cut.py water       골라서
    python reel_cut.py neon 3      3번 컷만 확인용으로

## 각 — 셋이 서로 뭘 다르게 말하는가

    sunset   낮에서 밤으로     시간이 흐른다
    water    **물만.** 낮 · 튜브 · 물장구       놀이
    neon     **밤만.** 조명 · 사람 · 부스        밀도

`sunset` 이 이미 '낮→밤' 을 했으니 새 둘은 **한쪽에만 머문다.** 그래야
세 편이 각자 다른 인상을 남긴다.

## 컷이 겹치면 안 된다

`pool` · `sunset` · `close` 가 이미 열몇 구간을 쓰고 있다. 같은 초를
다시 쓰면 세 편을 이어 본 사람에게 소재가 없어 보인다.

아래 `USED` 에 **이미 쓴 (파일, 초)** 를 다 적어 두고 `assert` 로 막는다.
눈으로는 절대 안 잡힌다 — 실제로 `pool` 이 같은 구간을 두 번 쓴 걸
한참 뒤에야 발견했다.

## 길이는 곡이 정한다

`audio_cut.PRESET` 의 마디 수 × 4비트가 영상 길이다. 컷 표의 비트 합이
그와 다르면 `-shortest` 가 뒤를 잘라 **마지막 컷이 통째로 사라진다.**
빌드할 때 맞는지 재고 안 맞으면 멈춘다.

## 인스타

    릴스     1080×1920 · 30fps. 올리면 피드에도 같이 걸린다
    격자     프로필에서 **1:1 로 잘린다** — 가운데가 비면 안 된다
    UI       재생 중 위 14% · 아래 25% 를 덮는다. 여기는 자막이 없어서
             문제가 안 되지만, **얼굴이 그 자리에만 있으면 가려진다**
"""
import os
import subprocess
import sys

import audio_cut

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'cut')
TMP = os.path.join(HERE, 'out', '_cutcuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30

# **이미 나간 릴스가 쓰는 구간.** 여기 있는 초는 다시 쓰지 않는다.
#   pool / sunset / close 세 편에서 긁어 온 값이다
USED = {
    ('P1023231', 9.0), ('P1023231', 12.0),
    ('P1023232', 3.0),
    ('P1023233', 5.4), ('P1023233', 11.0), ('P1023233', 20.0),
    ('P1023233', 30.4), ('P1023233', 33.2),
    ('P1023234', 5.0), ('P1023234', 6.4), ('P1023234', 13.0),
    ('P1023234', 24.0), ('P1023234', 26.2),
    ('P1023235', 1.4), ('P1023235', 4.2), ('P1023235', 6.6), ('P1023235', 12.8),
    ('P1023236', 16.2),
    ('P1023237', 1.8), ('P1023237', 10.2), ('P1023237', 12.4),
    ('P1023239', 2.6), ('P1023239', 5.2), ('P1023239', 9.4), ('P1023239', 14.0),
}

# (파일, 시작초, 비트, 시작줌, 끝줌, 설명)
CUTS = {
    # 낮 · 물. 비트 합 32 = 8마디
    'water': [
        ('P1023237',  5.0, 5, 1.10, 1.00, '계단·풀에 사람 가득 (훅)'),
        ('P1023233',  2.0, 4, 1.00, 1.08, '풀 안 물놀이'),
        ('P1023239',  8.0, 5, 1.00, 1.06, 'DJ — 믹서 위의 손'),
        ('P1023233',  8.5, 4, 1.09, 1.00, '풀 가득'),
        ('P1023237', 16.0, 4, 1.00, 1.08, '튜브 · 팔 뻗기'),
        ('P1023235', 11.0, 4, 1.00, 1.07, '뒷모습 · 헤드폰'),
        ('P1023234', 20.0, 6, 1.06, 1.00, '풀을 훑는다 — 끝 판'),
    ],
    # 밤 · 조명. 비트 합 36 = 9마디
    'neon': [
        ('P1023234', 10.0, 7, 1.12, 1.00, '하트 네온 + 풀 가득 (훅)'),
        ('P1023239',  1.0, 5, 1.00, 1.07, 'DJ — 부스'),
        ('P1023234', 17.0, 6, 1.08, 1.00, '풀 가득 · 튜브'),
        ('P1023239', 12.0, 5, 1.00, 1.06, 'DJ — 믹서 위의 손'),
        ('P1023239', 16.0, 5, 1.00, 1.07, 'DJ — 옆모습'),
        ('P1023234', 41.0, 8, 1.06, 1.00, '하트 네온 + 풀 — 끝 판'),
    ],
}

# 낮 편은 따뜻하게, 밤 편은 차갑고 세게. **같은 보정을 쓰면 두 편이
# 한 편처럼 보인다** — 컷을 갈라도 색이 같으면 소용이 없다
GRADE = {
    'water': 'eq=contrast=1.14:saturation=1.24:gamma=1.02:brightness=0.030,'
             'colorbalance=rs=0.04:gs=0.01:bs=-0.05',
    'neon':  'eq=contrast=1.30:saturation=1.36:gamma=0.90:brightness=-0.010,'
             'colorbalance=rs=-0.03:gs=-0.01:bs=0.07',
}


def run(args):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(' '.join(args[:6]) + ' …\n' + r.stderr[-1500:])
    return r


def cut_path(name, i):
    return os.path.join(TMP, f'{name}_{i:02d}.mp4')


def make_cut(name, i, c):
    """컷 하나. **원본이 이미 9:16 이라 크롭하지 않는다**(회전 메타데이터)."""
    src, t0, beats, z0, z1, _ = c
    beat = 60.0 / audio_cut.PRESET[name]['bpm']
    dur = beats * beat
    nf = max(1, int(round(dur * FPS)))
    vf = (f'fps={FPS},'
          f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS},"
          f'{GRADE[name]},unsharp=5:5:0.5,scale=out_range=tv,format=yuv420p')
    run(['ffmpeg', '-v', 'error', '-ss', str(t0),
         '-i', os.path.join(SRC, f'{src}.MOV'), '-t', f'{dur:.4f}',
         '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '21', '-pix_fmt', 'yuv420p', '-y', cut_path(name, i)])
    return dur


def check(name):
    """컷 표가 곡과 맞는지, 이미 쓴 구간을 다시 쓰지 않는지."""
    cfg = audio_cut.PRESET[name]
    want = cfg['bars'] * 4
    got = sum(c[2] for c in CUTS[name])
    assert got == want, f'{name}: 비트 합 {got} ≠ 곡 {want} 비트'
    seen = set()
    for src, t0, *_ in CUTS[name]:
        key = (src, t0)
        assert key not in USED, f'{name}: {src}@{t0} 는 이미 다른 릴스가 쓴다'
        assert key not in seen, f'{name}: {src}@{t0} 가 이 편에서 두 번'
        seen.add(key)
    # 두 편끼리도 안 겹쳐야 한다
    if name == 'neon':
        w = {(c[0], c[1]) for c in CUTS['water']}
        dup = seen & w
        assert not dup, f'water 와 겹친다: {dup}'


def build(name):
    check(name)
    bgm = audio_cut.build(name)
    durs = [make_cut(name, i, c) for i, c in enumerate(CUTS[name])]
    lst = os.path.join(TMP, f'{name}.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS[name])):
            fh.write("file '" + cut_path(name, i).replace(os.sep, '/') + "'\n")
    silent = os.path.join(TMP, f'{name}_silent.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-y', silent])
    # **곡을 영상 길이에 맞춘다.** 비트 합은 맞는데 컷마다 프레임이
    # 반올림되면서 neon 이 0.6초 짧아졌고, `-shortest` 가 곡 끝을 잘라
    # 페이드아웃이 통째로 사라졌다 — 재서 맞춘다
    vlen = float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', silent], capture_output=True, text=True).stdout.strip())
    out = os.path.join(OUT, f'{name}.mp4')
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
          f'{int(q[1])/1e6:.1f}MB · {int(q[2])/1e6:.1f}Mbps · '
          f'컷 {len(CUTS[name])}개')
    for i, c in enumerate(CUTS[name]):
        print(f'  {i:2d} {c[0]} @{c[1]:5.1f}s  {durs[i]:.2f}s  {c[5]}')
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] in CUTS and len(args) > 1:
        name, i = args[0], int(args[1])
        make_cut(name, i, CUTS[name][i])
        print(cut_path(name, i), CUTS[name][i][5])
    else:
        for k in (args or list(CUTS)):
            if k not in CUTS:
                raise SystemExit(f'{k} 은 없습니다 — {", ".join(CUTS)}')
            build(k)
