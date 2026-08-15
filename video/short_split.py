"""
숏폼 B안 — **위아래 두 판, 가운데 글자.** 1080×1920 · 30fps · 128BPM.

A안(`short.py`)은 16:9 원본을 9:16 으로 잘라 꽉 채운다. 그러면 **가로의 66%를
버린다** — 물가에 선 사람도, 옆에서 벌어지는 일도 다 프레임 밖으로 나간다.

B안은 거의 안 자른다. 1920×1080 을 1080×608 로 그대로 줄여 **위아래 두 판**에 놓고,
가운데 빈 자리를 글자에 준다.

    y  120– 728   위 판 (16:9 그대로)
    y  728–1192   글자 자리
    y 1192–1800   아래 판 (16:9 그대로)

이렇게 하면 얻는 게 셋이다.
    · 원본이 안 잘린다. 넓은 그림이 넓게 남는다
    · **두 장면이 동시에 보인다.** 한 판에 한 장면씩 보여 주는 것보다 밀도가 높다
    · 글자가 사진 위에 안 얹힌다 — 누를 필요가 없어서 판이 깨끗하다

**클립이 모자란 게 이 짜임의 한계다.** 판이 둘이면 15초짜리에 30초 분량이
필요하다(원본 총 38초). 판이 셋이면 45초가 필요해서 같은 그림을 또 써야 한다 —
그래서 셋이 아니라 둘이다.

**같은 순간이 두 판에 동시에 뜨지 않게** 짰다. 위아래가 같은 그림이면 두 판으로
나눈 뜻이 없다. 아래 SPLIT 의 구간은 겹치지 않게 잡은 값이라 바꿀 때 확인해야
한다(assert 가 잡는다).

⚠ 실제 손님 얼굴이 나온다. 초상권은 저작권과 별개다.

python short_split.py
"""
import os
import subprocess
import numpy as np
import cv2
from poster_kit import BRAND, tmask, fit, paint, status_chips
from fonts import KR, KRB
import event as EV
import short

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM
BH = 608                                  # 1920×1080 을 폭 1080 으로 줄인 높이
YA, YB = 120, 1192                        # 위 판 · 아래 판의 y
MID = (YA + BH + YB) // 2                 # 글자 자리 가운데

PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])

# 8박(3.75초)씩 넷. (위 판, 아래 판) — 같은 클립이 동시에 오지 않게 짰다
# **sky 클립은 앞 2.5초가 하늘·건물이라 판이 빈다.** 그 뒤부터 수영장이 나온다 —
# 넓은 그림이라고 다 쓸 수 있는 게 아니라 사람이 있는 구간만 쓴다.
SPLIT = [(('crowd', 0.2), ('floor', 0.2)),
         (('floor', 4.1), ('sky',   2.6)),
         (('sky',   6.6), ('crowd', 4.0)),
         (('walk',  0.1), ('side',  0.1))]
CUT = 8                                   # 한 컷 = 8박

CAPS = [(0, 4, '여기 서울이에요'),
        (4, 8, '양재 루프탑 풀파티'),
        (8, 12, '8월 29일 토요일'),
        (12, 16, '디제이 일곱 명'),
        (16, 20, '9시 반부터는 솔로파티'),
        (20, 24, '혼자 온 사람들끼리 섞여요')]


def band(fr):
    """1080×608 판에 앉힌다. 가로 영상은 그대로 들어가고, **세로 영상은 잘라 넣는다.**

    `floor` 클립 하나만 회전 메타데이터(-90°)가 붙은 세로 영상이다. ffprobe 는
    저장된 대로 1920×1080 이라고 보고하는데 **디코더는 회전을 적용해 1080×1920 을
    내놓는다** — 그걸 그냥 resize 하면 세로가 3.16 배로 눌려 찌그러진다.
    비율을 재서 넘치는 쪽을 자른다. 원본 비율을 안 건드리는 게 먼저다."""
    h, w = fr.shape[:2]
    ar = W / BH
    if w / h > ar:                       # 가로가 더 넓다 → 좌우를 자른다
        tw = int(h * ar)
        x0 = (w - tw) // 2
        fr = fr[:, x0:x0 + tw]
    else:                                # 세로가 더 길다 → 위아래를 자른다
        th = int(w / ar)
        y0 = int((h - th) * 0.45)        # 가운데보다 조금 위 — 사람이 위쪽에 있다
        fr = fr[y0:y0 + th]
    return cv2.resize(fr, (W, BH), interpolation=cv2.INTER_AREA)


def grade(a):
    a = np.clip((a - 0.5) * 1.14 + 0.5, 0, 1)
    g = a @ np.float32([0.299, 0.587, 0.114])
    a = np.clip(g[..., None] + (a - g[..., None]) * 1.22, 0, 1)
    return np.clip(a * np.float32([0.99, 1.005, 1.02]), 0, 1)


def plan():
    """프레임별 (위, 아래) 원본 프레임 번호."""
    caps, out = {}, []
    for (ka, aa), (kb, ab) in SPLIT:
        for k in (ka, kb):
            if k not in caps:
                caps[k] = short.load(k)
        n = int(round(CUT * BEAT * FPS))
        fa = caps[ka].get(cv2.CAP_PROP_FPS) or 30.0
        fb = caps[kb].get(cv2.CAP_PROP_FPS) or 30.0
        for i in range(n):
            out.append((ka, int((aa + i / FPS) * fa), kb, int((ab + i / FPS) * fb)))
    return caps, out


def render():
    # 같은 클립의 구간이 겹치면 같은 그림이 또 나온다
    used = {}
    for pair in SPLIT:
        for k, at in pair:
            a, z = at, at + CUT * BEAT
            for a2, z2 in used.get(k, []):
                assert z <= a2 + 0.05 or a >= z2 - 0.05, \
                    f'{k} 구간이 겹친다 — {a:.1f}~{z:.1f} 와 {a2:.1f}~{z2:.1f}'
            used.setdefault(k, []).append((a, z))
    for (ka, _), (kb, _) in SPLIT:
        assert ka != kb, f'위아래가 같은 클립이다 — {ka}'

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    caps, pl = plan()
    dur = NBEAT * BEAT
    nf = int(round(dur * FPS))
    pl = pl[:nf] + [pl[-1]] * max(0, nf - len(pl))

    raw = os.path.join(OUT, 'raw_split.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}

    def grab(key, fno):
        c = caps[key]
        if last.get(key) != fno - 1:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
        if not ok:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
            ok, fr = c.read()
        last[key] = fno
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else np.zeros((1080, 1920, 3), np.uint8)

    for i, (ka, fa, kb, fb) in enumerate(pl):
        img = np.zeros((H, W, 3), np.float32)
        img[YA:YA + BH] = grade(band(grab(ka, fa)).astype(np.float32) / 255)
        img[YB:YB + BH] = grade(band(grab(kb, fb)).astype(np.float32) / 255)

        b = (i / FPS) / BEAT
        # ── 가운데 글자. **사진 위가 아니라 빈 자리에 놓는다** ──
        for b0, b1, txt in CAPS:
            if b0 <= b < b1:
                k = np.clip((b - b0) / 0.16, 0, 1)
                paint(img, tmask(txt, KRB, 58, 0.02), W / 2, MID - 26,
                      color=PAPER, a=float(k), anchor='c')
                paint(img, tmask(EV.DATE_EN, BRAND, 22, 0.30), W / 2, MID + 46,
                      color=AQUA, a=float(k) * 0.80, anchor='c')

        # 상태 띠 — 어느 초에 멈춰도 보인다. 아래 판 위쪽 여백에 앉힌다
        if b < NBEAT - 6:
            status_chips(img, W / 2, YB - 34, 24, color=PAPER, accent=CORAL,
                         width=W * 0.90, bar=0.55)

        # ── 끝 여섯 박 — 판을 닫고 이름만 ─────────────────
        tail = NBEAT - 6
        if b >= tail:
            k = np.clip((b - tail) / 0.5, 0, 1)
            img *= 1 - 0.90 * k
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.84, 0.10), 0.10),
                  W / 2, H * 0.40, color=PAPER, a=float(k), anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 26, 0.36), W / 2, H * 0.40 + 62,
                  color=AQUA, a=float(k), anchor='c')
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 34, 0.02), W / 2, H * 0.40 + 128,
                  color=PAPER, a=float(k) * 0.96, anchor='c')
            status_chips(img, W / 2, H * 0.40 + 190, 26, color=PAPER, accent=CORAL,
                         a=float(k), width=W * 0.86)
            k2 = np.clip((b - tail - 1.2) / 0.5, 0, 1)
            if k2 > 0.004:
                paint(img, tmask('프로필 링크에서 예약', KRB, 50, 0.02), W / 2, H * 0.40 + 236,
                      color=CORAL, a=float(k2), anchor='c')
                paint(img, tmask(EV.PARTNERS_STR, BRAND,
                                 min(20, fit(EV.PARTNERS_STR, BRAND, W * 0.88, 0.16)), 0.16),
                      W / 2, H * 0.40 + 320, color=PAPER, a=float(k2) * 0.66, anchor='c')

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        c.release()

    final = os.path.join(OUT, 'short_split.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {dur:.2f}s  {NBEAT}박')


if __name__ == '__main__':
    render()
