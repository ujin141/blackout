"""
포스터 영상을 **사진 세 장 전부**로 뽑는다.

`motion.py` 는 한 번에 사진 한 장만 씁니다(`BLACKOUT_HERO`). 그냥 돌리면 전부
1번 사진으로만 나와서, 판이 열한 개인데 영상에서는 같은 사람만 계속 나옵니다.

**사진은 프로세스가 뜰 때 정해집니다.** `poster_kit` 이 import 되는 순간
환경변수를 읽어 `HERO` 를 고정하기 때문에, 한 프로세스 안에서 사진을 바꿔
끼울 수 없습니다 — 사진마다 따로 띄웁니다.

`card` 는 디제이 부스 사진이라 인물 사진을 안 씁니다. 세 번 돌릴 이유가 없어
1번에서만 뽑습니다.

python motion_all.py              전부 (사진 3 × 판 11 → 31편)
python motion_all.py 2 3          사진 2·3번만
python motion_all.py 1 -- story   사이즈까지 골라서
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ['tag', 'venn', 'float', 'ripple', 'night', 'deck', 'dive', 'real', 'ko', 'time', 'card']
NO_HERO = {'card'}                       # 인물 사진을 안 쓰는 판

args = sys.argv[1:]
cut = 'story'
if '--' in args:
    i = args.index('--')
    cut = args[i + 1] if len(args) > i + 1 else 'story'
    args = args[:i]
heroes = [int(a) for a in args] or [1, 2, 3]

total = sum(len([k for k in KEYS if h == 1 or k not in NO_HERO]) for h in heroes)
done = 0
for h in heroes:
    env = dict(os.environ, BLACKOUT_HERO=str(h), PYTHONIOENCODING='utf-8')
    for k in KEYS:
        if h != 1 and k in NO_HERO:
            continue
        done += 1
        print(f'[{done}/{total}] 사진 {h}번 · {k} · {cut}', flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'motion.py'), k, cut],
                           cwd=HERE, env=env, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        line = (r.stdout or '').strip().splitlines()
        print('   ' + (line[-1] if line else (r.stderr or '').strip()[-200:]), flush=True)
print('끝', flush=True)
