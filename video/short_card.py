"""
숏폼 C안 — **글자 판과 현장 컷을 박마다 번갈아 친다.** 1080×1920 · 30fps · 128BPM.

    A안 short.py        16:9 를 잘라 꽉 채운다. 화면 전체가 현장
    B안 short_split.py  위아래 두 판 + 가운데 글자
    C안 (이 파일)       색 판(글자) ↔ 현장 컷을 두 박마다 갈아 친다

**색 판 언어는 인트로(intro2.py)에서 가져왔다.** 같은 크루가 만든 것으로 보이려면
판마다 새 규칙을 만들 게 아니라 이미 쓰는 규칙을 옮겨야 한다 —
색은 넷뿐이고, 판은 박 위에서 잘리고, 글자는 판 밝기에서 자동으로 뒤집힌다.

**두 박(0.94초)마다 갈아 치는 게 이 판의 전부다.** 글자 판만 이으면 카드뉴스가
되고 현장만 이으면 A안이 된다. 번갈아 치면 **읽을 것과 볼 것이 교대로 오고**,
그 사이에 사람이 못 넘긴다.

    글자 판  판을 꽉 채우는 한 줄. 음소거로 봐도 정보가 다 진다
    현장 컷  0.94초씩. 짧아서 무슨 그림인지만 남고 지루할 틈이 없다

**글자 판에는 사진이 없다.** 사진 위에 글자를 얹으면 누르고 다듬어야 하는데,
빈 판에 놓으면 그냥 크게 쓰면 된다. 숏폼에서 글자는 클수록 이긴다.

⚠ 실제 손님 얼굴이 나온다. 초상권은 저작권과 별개다.

python short_card.py
"""
import os
import subprocess
import numpy as np
import cv2
from poster_kit import BRAND, tmask, fit, paint
from fonts import KR, KRB
import event as EV
import short

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM
SEG = 2                                   # 한 칸 = 두 박 = 0.94초
TAIL = 6                                  # 끝 여섯 박은 마무리 판

# 인트로와 같은 색. 다섯째가 들어오면 전단지가 된다
DEEP = np.float32([0.035, 0.150, 0.215])
AQUA = np.float32([0.290, 0.780, 0.845])
PAPER = np.float32([0.975, 0.985, 0.985])
INK = np.float32([0.030, 0.038, 0.045])
CORAL = np.float32([0.980, 0.360, 0.300])

# (색, 문구) — 글자 판. 사이사이에 현장 컷이 들어간다
CARDS = [(DEEP,  '여기 서울이에요'),
         (AQUA,  '양재 루프탑 풀파티'),
         (INK,   '8월 29일 토요일'),
         (CORAL, '디제이 일곱 명'),
         (DEEP,  '9시 반부터 솔로파티'),
         (AQUA,  '혼자 온 사람들끼리'),
         (INK,   '끝나면 신사 ACE로 2차')]
# 현장 컷 — 겹치지 않는 구간만. 0.94초씩이라 짧게 잘라도 남는다
SHOTS = [('crowd', 3.3), ('floor', 0.4), ('side', 1.2),
         ('walk', 2.2), ('floor', 5.6), ('crowd', 6.2)]


def ink_for(col):
    """판이 밝으면 글자는 검정, 짙으면 흰색. 인트로와 같은 규칙."""
    return INK if float(col @ np.float32([0.299, 0.587, 0.114])) > 0.62 else PAPER


def grade(a):
    a = np.clip((a - 0.5) * 1.14 + 0.5, 0, 1)
    g = a @ np.float32([0.299, 0.587, 0.114])
    return np.clip(g[..., None] + (a - g[..., None]) * 1.22, 0, 1)


def crop916(fr, ox=0.5):
    h, w = fr.shape[:2]
    tw = int(h * W / H)
    x0 = int(np.clip((w - tw) * ox, 0, w - tw))
    return cv2.resize(fr[:, x0:x0 + tw], (W, H), interpolation=cv2.INTER_AREA)


def render():
    nseg = (NBEAT - TAIL) // SEG                  # 13 칸
    # 글자 판과 현장 컷을 번갈아. 칸 0·2·4… 는 글자, 1·3·5… 는 현장
    order = []
    ci = si = 0
    for k in range(nseg):
        if k % 2 == 0:
            order.append(('card', CARDS[ci % len(CARDS)])); ci += 1
        else:
            order.append(('shot', SHOTS[si % len(SHOTS)])); si += 1
    assert ci <= len(CARDS), f'글자 판이 모자란다 — {ci}칸 필요'
    assert si <= len(SHOTS), f'현장 컷이 모자란다 — {si}칸 필요'
    used = {}
    for kind, v in order:
        if kind == 'shot':
            k, at = v
            a, z = at, at + SEG * BEAT
            for a2, z2 in used.get(k, []):
                assert z <= a2 + 0.05 or a >= z2 - 0.05, f'{k} 구간이 겹친다'
            used.setdefault(k, []).append((a, z))

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    caps = {}
    dur = NBEAT * BEAT
    nf = int(round(dur * FPS))
    raw = os.path.join(OUT, 'raw_card.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}

    def grab(key, at, i):
        if key not in caps:
            caps[key] = short.load(key)
        c = caps[key]
        fps = c.get(cv2.CAP_PROP_FPS) or 30.0
        fno = int((at + i / FPS) * fps)
        if last.get(key) != fno - 1:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
        if not ok:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
            ok, fr = c.read()
        last[key] = fno
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((1080, 1920, 3), np.uint8)

    seglen = int(round(SEG * BEAT * FPS))
    for i in range(nf):
        b = (i / FPS) / BEAT
        k = min(int(b // SEG), nseg - 1)
        j = i - k * seglen
        kind, v = order[k]

        if kind == 'card':
            col, txt = v
            img = np.repeat(np.repeat(col[None, None, :], H, 0), W, 1).copy()
            ink = ink_for(col)
            # **글자를 판 폭에 맞춰 키운다.** 숏폼에서 글자는 클수록 이긴다
            # **96 은 작다.** 판이 비어 있는데 글자를 안 키울 이유가 없다 —
            # 폭이 허락하는 데까지 키우고, 긴 줄만 fit 이 알아서 줄인다
            fs = min(132, fit(txt, KRB, W * 0.86, 0.02))
            paint(img, tmask(txt, KRB, fs, 0.02), W / 2, H * 0.47, color=ink, anchor='c')
            paint(img, tmask(EV.DATE_EN, BRAND, 24, 0.30), W / 2, H * 0.47 + fs * 0.95,
                  color=ink, a=0.62, anchor='c')
        else:
            key, at = v
            img = grade(crop916(grab(key, at, j)).astype(np.float32) / 255)

        # 칸이 갈리는 첫 두 프레임에 흰 섬광 한 번 — 컷이 딱 끊긴 게 보인다
        if j < 2 and k > 0:
            g = 0.34 * (1 - j / 2)
            img = img * (1 - g) + PAPER * g

        # ── 끝 여섯 박 ───────────────────────────────────
        if b >= NBEAT - TAIL:
            kk = np.clip((b - (NBEAT - TAIL)) / 0.5, 0, 1)
            img = img * (1 - kk) + INK * kk
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.86, 0.10), 0.10),
                  W / 2, H * 0.40, color=PAPER, a=float(kk), anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 26, 0.36), W / 2, H * 0.40 + 62,
                  color=AQUA, a=float(kk), anchor='c')
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 34, 0.02), W / 2, H * 0.40 + 128,
                  color=PAPER, a=float(kk) * 0.96, anchor='c')
            k2 = np.clip((b - (NBEAT - TAIL) - 1.2) / 0.5, 0, 1)
            if k2 > 0.004:
                paint(img, tmask('프로필 링크에서 예약', KRB, 52, 0.02), W / 2, H * 0.40 + 240,
                      color=CORAL, a=float(k2), anchor='c')
                paint(img, tmask(EV.PARTNERS_STR, BRAND,
                                 min(20, fit(EV.PARTNERS_STR, BRAND, W * 0.88, 0.16)), 0.16),
                      W / 2, H * 0.40 + 324, color=PAPER, a=float(k2) * 0.66, anchor='c')

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        c.release()

    final = os.path.join(OUT, 'short_card.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {dur:.2f}s  글자 판 {ci}칸 · 현장 컷 {si}칸')


if __name__ == '__main__':
    render()
