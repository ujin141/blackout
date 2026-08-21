"""
**현장 영상 릴스.** 지난 풀파티에서 찍은 원본을 잘라 붙인다.

    python reel_pool.py            → out/reel/pool.mp4  (1080×1920 · 30fps)
    python reel_pool.py 3          → 3번 컷만 확인용으로 뽑는다

원본은 `숏폼/` 에 있는 4K 60fps 가로 아홉 개다. **저장소에 안 올린다** —
손님 얼굴이 들어 있고 gitignore 에 걸려 있다. 여기서는 경로만 읽는다.

## 컷을 고르는 기준

**사람이 보여야 한다.** 처음엔 풍경과 소품 위주로 갔는데 우진이 바로
잡았다 — "사람이 아무도 안 보인다". 맞는 말이다. 사람이 없으면 파티가
아니라 장소 소개고, 장소 소개를 보고 들어오는 사람은 없다.

    앞      풀에 사람이 가득한 컷. **붐비는 게 첫 1초에 보여야 한다**
    가운데  튜브 · 물놀이 · DJ. 노는 사람이 계속 나온다
    끝      풀과 네온. **전망은 안 쓴다** — 주변 경치는 우리가 파는 게 아니다

## 컷 길이

**한 컷 2~3초.** 처음엔 1초 안팎으로 잘게 썰었는데 "너무 짧다" 는 지적이
왔다. 맞다 — 짧게 썰면 리듬은 생겨도 **무슨 장면인지 못 읽는다.**
사람이 노는 걸 보여주는 게 목적인데 보이기 전에 넘어가면 소용이 없다.

저장소 규칙은 **정면 얼굴이 가운데 오는 클로즈업**을 막는 것이지 사람이
나오는 걸 막는 게 아니다. 그걸 넓게 읽어서 사람을 다 뺐던 게 1차 실수다.
여럿이 노는 와이드 컷은 쓴다.

## 세로로 자르는 법

원본이 3840×2160 이라 9:16 으로 자르면 가로의 32% 만 남는다. **가운데를
그냥 자르면 피사체가 밖으로 나간다** — 컷마다 `cx`(가로 중심, 0~1)를
따로 준다.

## 박

120BPM = 0.5초. 컷 길이를 **비트의 정수배**로 잡으면 나중에 어떤 곡을
얹어도 대충 맞는다. 인스타 음원을 얹을 걸 전제로 한다 —
릴스는 자체 음원을 쓰는 쪽이 도달이 낫다.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
OUT = os.path.join(HERE, 'out', 'reel')
TMP = os.path.join(HERE, 'out', '_reelcuts')
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BEAT = 0.5                                   # 120BPM

# (파일, 시작초, 비트 수, 가로중심 0~1, 줌, 설명)
# 줌은 1.0 이 꽉 참. 1.10 이면 10% 확대해서 천천히 밀어 넣는다.
CUTS = [
    ('P1023235',  1.4, 6, 0.50, 1.05, '풀 가득 · 튜브 (훅)'),
    ('P1023237',  1.8, 5, 0.48, 1.06, '풀 안 물놀이'),
    ('P1023239',  8.8, 5, 0.50, 1.05, 'DJ — 믹서 위의 손'),
    ('P1023231',  9.0, 4, 0.50, 1.06, '풀에 사람 가득'),
    # 여기 237@5.6 을 뒀다가 뺐다. 뒤태가 화면 가운데로 크게 잡혀서
    # 인스타 노출 정책에도, 우리 톤에도 안 맞았다
    ('P1023233',  4.0, 5, 0.50, 1.05, '풀 사람들'),
    ('P1023235',  4.6, 5, 0.50, 1.05, '풀 + 튜브'),
    ('P1023236', 18.6, 5, 0.50, 1.06, '계단 · 사람들'),
    # 25.4 로 뒀더니 컷 끝이 흐렸다 — 팬이 시작되는 자리라 앞으로 당겼다
    ('P1023234', 24.8, 5, 0.52, 1.06, '핑크 LED + 풀 — 정보가 얹힐 자리'),
]









# **트랜지션을 안 쓴다.** 흰 플래시와 검정 디졸브를 넣었더니 우진이
# "너무 세다" 고 했다 — 15초에 효과가 세 번이면 그게 주인공이 된다.
# 리듬은 효과가 아니라 **컷 길이**로 만든다. 하드컷만 쓴다.
FLASH = set()
DISSOLVE = set()


def run(args):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(' '.join(args[:6]) + ' …\n' + r.stderr[-1500:])
    return r


def cut_path(i):
    return os.path.join(TMP, f'cut_{i:02d}.mp4')


def make_cut(i, c):
    """컷 하나를 1080×1920 으로. **크롭 → 줌 → 스케일 순서다** —
    스케일을 먼저 하면 4K 해상도를 버리고 확대하게 된다."""
    name, t0, beats, cx, zoom, _ = c
    dur = beats * BEAT
    src = os.path.join(SRC, f'{name}.MOV')
    # 9:16 로 자를 때 쓸 수 있는 가로 폭
    cw = 2160 * W / H                        # 1215
    # 줌은 크롭을 더 좁게 잡는 것으로 낸다
    zw, zh = cw / zoom, 2160 / zoom
    x = f'(iw-{zw:.0f})*{cx:.3f}'
    y = f'(ih-{zh:.0f})/2'
    vf = (f'crop={zw:.0f}:{zh:.0f}:{x}:{y},'
          f'scale={W}:{H}:flags=lanczos,fps={FPS},'
          f'eq=contrast=1.22:saturation=1.34:gamma=0.94:brightness=0.02,'
          f'unsharp=5:5:0.5')
    if i in FLASH:
        vf += ',fade=t=in:st=0:d=0.09:color=white'
    elif i in DISSOLVE:
        vf += ',fade=t=in:st=0:d=0.16:color=black'
    run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-i', src, '-t', str(dur),
         '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '17', '-pix_fmt', 'yuv420p', '-y', cut_path(i)])
    return dur


def blur_score(path):
    """컷이 흔들렸는지 잰다. **눈으로 넘기면 꼭 한둘이 흐리다** —
    라플라시안 분산이 낮으면 초점이 안 맞았거나 팬이 너무 빨랐다는 뜻이다."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(path)
    vals = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY)
        vals.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))
    cap.release()
    return (float(np.mean(vals)), float(np.mean([v > 60 for v in vals]) * 100)
            ) if vals else (0.0, 0.0)


def build():
    durs = [make_cut(i, c) for i, c in enumerate(CUTS)]
    # **concat demuxer 로 붙인다.** 컷이 전부 같은 규격(1080×1920·30fps·h264)
    # 이라 다시 인코딩할 필요가 없다 — filter_complex 로 이으면 열한 번
    # 재인코딩하면서 화질만 깎인다
    lst = os.path.join(TMP, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for i in range(len(CUTS)):
            fh.write("file '" + cut_path(i).replace(os.sep, '/') + "'\n")
    out = os.path.join(OUT, 'pool.mp4')
    run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-movflags', '+faststart', '-y', out])
    print(f'{out}  {W}×{H} · {FPS}fps · {sum(durs):.1f}초 · 컷 {len(CUTS)}개')
    for i, c in enumerate(CUTS):
        mark = ' ⚡' if i in FLASH else (' ◐' if i in DISSOLVE else '  ')
        sharp, ok = blur_score(cut_path(i))
        warn = '  ← 흐리다' if sharp < 55 else ''
        print(f'  {i:2d}{mark} {c[0]} @{c[1]:5.1f}s  {c[2] * BEAT:.1f}s  '
              f'선명도 {sharp:5.0f}  {c[5]}{warn}')
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i), CUTS[i][5])
    else:
        build()
