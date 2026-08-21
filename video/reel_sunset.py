"""
**해 지는 릴스.** 숏폼 원본으로 만든 두 번째 판. 19.2초 · 1080×1920.

    python reel_sunset.py            → out/sunset/sunset.mp4
    python reel_sunset.py 4          → 4번 컷만 확인용으로

`reel_pool.py` 와 **같은 원본, 다른 판**이다. 겹치는 컷이 하나도 없다.

    pool     현장 소리 그대로. 컷 2~3초. 풀만 보여 준다
    sunset   새 곡(`audio_sunset`)에 맞춘 비트컷. 1.4~1.9초.
             **낮에서 밤으로 간다** — 밝은 물에서 시작해 네온으로 끝난다

## 왜 두 판이 필요한가

한 소재로 한 판만 만들면 그 소재가 죽는다. 같은 날 찍은 영상인데 각이
다르면 두 번 올릴 수 있고, 두 번 올려야 도달이 붙는다. 대신 **컷이
겹치면 안 된다** — 겹치는 순간 재탕으로 보인다.

## 원본은 세로다

`ffprobe` 가 3840×2160 이라고 말하지만 회전 90도라 실제는 2160×3840.
크롭하지 않는다(`reel_pool` 참고). 이걸 모르고 한 번 크게 헤맸다.

## 흐름

곡이 125BPM, 한 비트 0.48초다. 컷을 비트 배수로 잡아 킥 위에 놓는다.

    앞 (0~9초)    낮. 물빛이 밝고 사람이 가득하다
    뒤 (9~19초)   밤. 핑크 LED · 보라 조명 · DJ

**해가 지는 건 하늘로 말하지 않는다.** 하늘 컷을 넣었다가 뺐다 —
사람이 없고 밋밋했다. 앞은 물빛, 뒤는 네온이면 색온도만으로 읽힌다.
"""
import os
import subprocess
import sys

import audio_sunset

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'sunset')
TMP = os.path.join(HERE, 'out', '_sunsetcuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BEAT = 60.0 / 125.0                      # 0.48초

# (파일, 시작초, 비트 수, 시작줌, 끝줌, 설명)
# **pool.mp4 와 한 컷도 겹치지 않는다.** 겹치면 재탕으로 보인다
CUTS = [
    ('P1023233',  5.4, 4, 1.10, 1.00, '풀 가득 — 낮'),
    # 7.4 는 뒤태가 화면 가운데로 왔다. pool 에서도 같은 이유로 뺐던 자리다
    ('P1023237', 12.4, 3, 1.00, 1.09, '풀 · 튜브'),
    ('P1023231', 12.0, 3, 1.09, 1.00, '풀 + 사람'),
    ('P1023235',  4.2, 3, 1.00, 1.09, '풀 · 튜브'),
    ('P1023234',  6.4, 3, 1.08, 1.00, '풀 넓게'),
    # 하늘만 나오는 컷을 넣었다가 뺐다. **해가 지는 건 하늘이 아니라
    # 색온도로 말한다** — 앞은 물빛, 뒤는 네온이면 그것만으로 읽힌다
    ('P1023233', 11.0, 3, 1.00, 1.10, '풀 + 사람'),
    ('P1023234', 13.0, 3, 1.10, 1.00, '핑크 LED + 풀 — 밤'),
    ('P1023236', 16.2, 3, 1.00, 1.09, '보라 조명 · 사람들'),
    ('P1023239',  5.2, 4, 1.00, 1.07, 'DJ'),
    ('P1023233', 33.2, 3, 1.09, 1.00, '핑크 LED · 사람들'),
    ('P1023235', 12.8, 3, 1.00, 1.09, '사람들'),
    ('P1023234', 26.2, 5, 1.08, 1.00, '풀 + 사람 — 정보가 얹힐 자리'),
]


def run(args):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(' '.join(args[:6]) + ' …\n' + r.stderr[-1500:])
    return r


def cut_path(i):
    return os.path.join(TMP, f'cut_{i:02d}.mp4')


def make_cut(i, c):
    name, t0, beats, z0, z1, _ = c
    dur = beats * BEAT
    nf = max(1, int(round(dur * FPS)))
    vf = (f'fps={FPS},'
          f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS},"
          f'eq=contrast=1.20:saturation=1.30:gamma=0.95:brightness=0.015,'
          f'unsharp=5:5:0.5,scale=out_range=tv,format=yuv420p')
    run(['ffmpeg', '-v', 'error', '-ss', str(t0),
         '-i', os.path.join(SRC, f'{name}.MOV'), '-t', f'{dur:.4f}',
         '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '21', '-pix_fmt', 'yuv420p', '-y', cut_path(i)])
    return dur


def build():
    bgm = audio_sunset.build()
    durs = [make_cut(i, c) for i, c in enumerate(CUTS)]
    lst = os.path.join(TMP, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS)):
            fh.write("file '" + cut_path(i).replace(os.sep, '/') + "'\n")
    silent = os.path.join(TMP, 'silent.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-y', silent])
    out = os.path.join(OUT, 'sunset.mp4')
    run(['ffmpeg', '-v', 'error', '-i', silent, '-i', bgm,
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', '-y', out])
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'format=duration,size,bit_rate',
                        '-of', 'csv=p=0', out],
                       capture_output=True, text=True).stdout.strip().split(',')
    print(f'{out}  {W}×{H} · {FPS}fps · {float(q[0]):.2f}초 · '
          f'{int(q[1])/1e6:.1f}MB · {int(q[2])/1e6:.1f}Mbps')
    for i, c in enumerate(CUTS):
        print(f'  {i:2d} {c[0]} @{c[1]:5.1f}s  {c[2] * BEAT:.2f}s  {c[5]}')
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i), CUTS[i][5])
    else:
        build()
