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

## 화면이 움직여야 한다

컷을 고정으로 두면 **사진 여덟 장을 넘기는 것**과 같다. 컷마다 천천히
밀거나(push in) 빠지게(pull out) 한다 — 2~3초 컷에서 8~20% 면 눈에
'움직인다' 로만 남고 어지럽지 않다.

방향을 섞는다. 훅은 크게 시작해 빠지면서 "여기가 어디" 가 드러나고,
**중요한 컷(DJ)은 세게 밀어 넣어** 얼굴이 커진다. 전부 같은 방향이면
그게 또 기계가 된다.

## 컷 길이

**한 컷 2~3초.** 처음엔 1초 안팎으로 잘게 썰었는데 "너무 짧다" 는 지적이
왔다. 맞다 — 짧게 썰면 리듬은 생겨도 **무슨 장면인지 못 읽는다.**
사람이 노는 걸 보여주는 게 목적인데 보이기 전에 넘어가면 소용이 없다.

저장소 규칙은 **정면 얼굴이 가운데 오는 클로즈업**을 막는 것이지 사람이
나오는 걸 막는 게 아니다. 그걸 넓게 읽어서 사람을 다 뺐던 게 1차 실수다.
여럿이 노는 와이드 컷은 쓴다.

## 원본은 이미 세로다

**`ffprobe` 가 3840×2160 이라고 말하지만 그건 저장된 방향이다.**
회전 메타데이터가 90도라 실제로 디코딩되는 건 **2160×3840** — 정확히
9:16 이다. 세로로 찍은 영상이다.

이걸 모르고 가로인 줄 알고 `crop=1215:2160` 을 걸고 있었다. 세로 프레임
한가운데 손바닥만 한 조각만 쓰고 있었던 것이다 — DJ 얼굴이 자꾸 잘리고,
사람이 적어 보이고, 장면이 답답했던 게 전부 여기서 왔다.

**크롭이 필요 없다.** 원본을 그대로 1080×1920 으로 줄이면 된다.
`cx`·`cy` 는 줌을 걸었을 때 그 안에서 어디를 볼지 정하는 값으로만 남는다.

원본 방향을 의심하는 데 오래 걸렸다. 앞으로 새 소재가 들어오면
**저장 해상도가 아니라 실제 출력 해상도를 먼저 재라.**

## 인스타에 올릴 때

    크기      1080×1920 · 30fps · h264 + aac. 릴스 권장 그대로다
    비트레이트 **너무 높으면 손해다.** crf 17 로 뽑았더니 24Mbps · 60MB 가
              나왔는데, 인스타는 어차피 자기 기준으로 다시 인코딩한다 —
              용량만 크고 화질은 그대로 깎인다. crf 21 이면 10Mbps 안쪽이다
    색 범위    소스가 full-range 라 그냥 두면 `yuvj420p` 로 나간다. 플레이어에
              따라 검정이 뜨거나 색이 튄다 — `out_range=tv` 로 못 박는다

화면은 9:16 이라 릴스 피드에서 **잘리지 않는다.** 다만 프로필 격자와
탐색 탭은 커버를 1:1 로 자르고, 재생 중에는 UI 가 위아래를 덮는다 —
위 14% · 아래 25% 에는 글자를 두지 않는다.

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

# (파일, 시작초, 비트 수, 가로중심, 세로중심, 시작줌, 끝줌, 설명)
# 줌 1.0 이 꽉 참. 시작줌 < 끝줌 이면 밀어 넣고(push in), 크면 빠진다.
# 세로중심은 줌이 1.0 일 때는 아무 효과가 없다 — 자를 여백이 없기 때문이다.
CUTS = [
    ('P1023235',  1.4, 5, 0.50, 0.50, 1.12, 1.00, '풀 가득 · 튜브 (훅)'),
    ('P1023237',  1.8, 4, 0.50, 0.50, 1.00, 1.10, '풀 안 물놀이'),
    # DJ 컷은 얼굴이 다 보여야 한다. **줌을 걸면 잘린다** — 원본이 이미
    # 세로 한 장이라 그대로 두는 게 제일 잘 보인다
    ('P1023239',  2.6, 8, 0.50, 0.50, 1.00, 1.06, 'DJ — 얼굴 (4초)'),
    ('P1023231',  9.0, 4, 0.50, 0.50, 1.10, 1.00, '풀에 사람 가득'),
    ('P1023233', 30.4, 4, 0.50, 0.50, 1.00, 1.09, '풀 전경'),
    ('P1023235',  6.6, 4, 0.50, 0.50, 1.09, 1.00, '풀 · 사람들'),
    ('P1023239',  9.4, 6, 0.50, 0.50, 1.00, 1.08, 'DJ — 믹서 위의 손 (3초)'),
    ('P1023234',  5.0, 5, 0.50, 0.50, 1.00, 1.09, '위에서 본 풀 — 정보가 얹힐 자리'),
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
    name, t0, beats, cx, cy, z0, z1, _ = c
    dur = beats * BEAT
    src = os.path.join(SRC, f'{name}.MOV')
    nf = max(1, int(round(dur * FPS)))
    # **크롭하지 않는다.** 원본이 이미 9:16 이다(위 참고).
    # 줌은 zoompan 이 확대와 스케일을 한 번에 한다
    vf = (f'fps={FPS},'
          f"zoompan=z='{z0:.4f}+({z1 - z0:.4f})*on/{nf}':d=1:"
          f"x='(iw-iw/zoom)*{cx:.3f}':y='(ih-ih/zoom)*{cy:.3f}':"
          f's={W}x{H}:fps={FPS},'
          f'eq=contrast=1.22:saturation=1.34:gamma=0.94:brightness=0.02,'
          f'unsharp=5:5:0.5,'
          f'scale=out_range=tv,format=yuv420p')
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
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
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
    q = subprocess.run(['ffprobe', '-v', 'error',
                        '-show_entries', 'stream=codec_name,width,height,pix_fmt',
                        '-show_entries', 'format=size,bit_rate',
                        '-of', 'csv=p=0', out], capture_output=True, text=True)
    info = [l for l in q.stdout.splitlines() if l.strip()]
    print('  규격:', ' | '.join(info[:2]))
    if len(info) > 2:
        sz, br = info[-1].split(',')[:2]
        print(f'  용량: {int(sz)/1e6:.1f}MB · {int(br)/1e6:.1f}Mbps')
    print(f'{out}  {W}×{H} · {FPS}fps · {sum(durs):.1f}초 · 컷 {len(CUTS)}개')
    for i, c in enumerate(CUTS):
        mark = ' ⚡' if i in FLASH else (' ◐' if i in DISSOLVE else '  ')
        sharp, ok = blur_score(cut_path(i))
        warn = '  ← 흐리다' if sharp < 55 else ''
        print(f'  {i:2d}{mark} {c[0]} @{c[1]:5.1f}s  {c[2] * BEAT:.1f}s  '
              f'선명도 {sharp:5.0f}  {c[7]}{warn}')
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1:
        i = int(sys.argv[1])
        make_cut(i, CUTS[i])
        print(cut_path(i), CUTS[i][7])
    else:
        build()
