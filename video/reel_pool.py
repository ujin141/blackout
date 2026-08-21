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

    전부    **물이 화면을 채워야 한다.** 우리가 파는 건 풀파티다 —
            계단 · 부스 · 전망은 다 뺐다. 여덟 컷 중 일곱이 풀이다
    DJ 두 컷 얼굴 하나(4초) · 손 하나(3초). 스무 초 중 일곱 초, 35% 다.
            처음엔 손만 1.5초 보여 줬는데 "DJ 여자도 보여 달라", 다음엔
            "더 보이게" 라는 지적이 이어졌다 — **크루가 튼다는 걸 말하는 게
            이 판의 목적**이고, 풀은 그 배경이다

## 같은 장면을 두 번 쓰지 않는다

원본이 아홉 개인데 235·237·239 를 두 번씩 쓰고 있었다. 게다가 237 은
1.8초와 3.2초 — 1.4초 차이라 **사실상 같은 장면**이었다. 스무 초짜리에서
같은 그림이 두 번 나오면 소재가 없어 보인다.

지금은 여덟 컷에 일곱 클립을 쓴다. 239(DJ)만 두 번인데 하나는 얼굴,
하나는 손이라 장면이 다르다 — DJ 원본이 그것 하나뿐이기도 하다.

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

세로는 사정이 다르다. 9:16 은 원본 높이를 전부 쓰기 때문에 **줌을 키우지
않으면 위아래로 옮길 여지가 없다.** DJ 얼굴이 프레임 위로 잘렸을 때
`cx` 만 만지다가 알았다 — 얼굴을 가운데로 가져오려면 줌을 1.35 까지
올려서 자리를 만들고 `cy` 로 끌어내려야 한다.

## 소리

**현장 소리를 살린다.** 처음엔 무음으로 뽑았는데(인스타 음원을 얹을
생각이었다) 우진이 소리를 빼지 말라고 했다 — 물소리·사람 소리가 있어야
현장이고, 인스타 음원은 그 위에 얹으면 된다.

컷 경계에서 소리가 툭 끊기면 거슬린다. **컷마다 앞뒤 30ms 페이드**를
넣으면 클릭 노이즈가 사라진다.

## 박

120BPM = 0.5초. 컷 길이를 **비트의 정수배**로 잡으면 나중에 어떤 곡을
얹어도 대충 맞는다.
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

# (파일, 시작초, 비트 수, 가로중심, 세로중심, 줌, 설명)
# 줌 1.0 이 꽉 참. 세로중심은 줌이 1.0 일 때는 아무 효과가 없다 —
# 자를 여백이 없기 때문이다.
CUTS = [
    ('P1023235',  1.4, 5, 0.50, 0.50, 1.05, '풀 가득 · 튜브 (훅)'),
    ('P1023237',  1.8, 4, 0.48, 0.50, 1.06, '풀 안 물놀이'),
    # **점점 또렷해지는 쪽으로 잡는다.** 이 구간 선명도가 2.2(100) →
    # 5.4(179) 로 오른다. 흐린 데서 시작해 또렷해지면 흐린 게 덜 보인다
    ('P1023239',  2.6, 8, 0.46, 0.42, 1.10, 'DJ — 얼굴 (4초)'),
    ('P1023231',  9.0, 4, 0.50, 0.50, 1.06, '풀에 사람 가득'),
    ('P1023233', 30.4, 4, 0.50, 0.50, 1.05, '풀 전경'),
    # 여기에 236(예거 부스)과 238(풀사이드)을 차례로 넣어 봤다. 236 은 물이
    # 안 보였고 238 은 발만 나왔다 — **같은 장면을 피하려다 풀파티가 아닌
    # 컷을 넣으면 앞뒤가 안 맞는다.** 235 를 쓰되 훅(1.4)에서 5초 떨어뜨렸다
    ('P1023235',  6.6, 4, 0.50, 0.50, 1.05, '풀 · 사람들'),
    ('P1023239',  9.4, 6, 0.50, 0.50, 1.05, 'DJ — 믹서 위의 손 (3초)'),
    ('P1023234',  5.0, 5, 0.50, 0.50, 1.05, '위에서 본 풀 — 정보가 얹힐 자리'),
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
    name, t0, beats, cx, cy, zoom, _ = c
    dur = beats * BEAT
    src = os.path.join(SRC, f'{name}.MOV')
    # 9:16 로 자를 때 쓸 수 있는 가로 폭
    cw = 2160 * W / H                        # 1215
    # 줌은 크롭을 더 좁게 잡는 것으로 낸다
    zw, zh = cw / zoom, 2160 / zoom
    x = f'(iw-{zw:.0f})*{cx:.3f}'
    y = f'(ih-{zh:.0f})*{cy:.3f}'
    vf = (f'crop={zw:.0f}:{zh:.0f}:{x}:{y},'
          f'scale={W}:{H}:flags=lanczos,fps={FPS},'
          f'eq=contrast=1.22:saturation=1.34:gamma=0.94:brightness=0.02,'
          f'unsharp=5:5:0.5')
    if i in FLASH:
        vf += ',fade=t=in:st=0:d=0.09:color=white'
    elif i in DISSOLVE:
        vf += ',fade=t=in:st=0:d=0.16:color=black'
    # 컷 경계의 클릭 노이즈를 없앤다 — 앞뒤 30ms 만 페이드
    af = (f'afade=t=in:st=0:d=0.03,'
          f'afade=t=out:st={max(0.0, dur - 0.03):.3f}:d=0.03,'
          f'aresample=48000')
    run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-i', src, '-t', str(dur),
         '-vf', vf, '-af', af,
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
         '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-y', cut_path(i)])
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
    a = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                        '-show_entries', 'stream=codec_name,channels',
                        '-of', 'csv=p=0', out], capture_output=True, text=True)
    print('  소리:', (a.stdout or '없음').strip())
    print(f'{out}  {W}×{H} · {FPS}fps · {sum(durs):.1f}초 · 컷 {len(CUTS)}개')
    for i, c in enumerate(CUTS):
        mark = ' ⚡' if i in FLASH else (' ◐' if i in DISSOLVE else '  ')
        sharp, ok = blur_score(cut_path(i))
        warn = '  ← 흐리다' if sharp < 55 else ''
        print(f'  {i:2d}{mark} {c[0]} @{c[1]:5.1f}s  {c[2] * BEAT:.1f}s  '
              f'선명도 {sharp:5.0f}  {c[6]}{warn}')
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i), CUTS[i][6])
    else:
        build()
