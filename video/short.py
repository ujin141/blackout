"""
실사 숏폼 — 지난 풀파티 영상을 릴스/틱톡/쇼츠용 세로판으로 자른다. 1080×1920 · 30fps.

원본은 `숏폼/` 의 1920×1080 클립 다섯 개(총 38초). 그대로 올리면 세로 화면에서
위아래가 검게 비고, 소리는 현장 잡음이고, 박도 안 맞는다.

**숏폼은 짜임이 전부다.** 좋은 그림을 이어 붙인다고 되는 게 아니라 다음 다섯을
지켜야 끝까지 본다.

**1. 첫 1초에 제일 센 그림을 둔다**
   릴스는 첫 프레임에서 넘길지 말지가 갈린다. 시간 순서대로 붙이면 하늘·빈 수영장이
   먼저 나오고 거기서 다 넘긴다. **사람이 제일 많은 컷을 맨 앞에** 둔다.

**2. 박 위에서만 자른다**
   BGM 은 `audio_motion.py` 의 deep(124BPM). 한 박 0.4839초라 컷을 전부 박의
   배수로 놓는다. 아무 데서나 자르면 편집한 티가 나고, 박에 맞으면 안 난다.

**3. 소리 없이도 읽혀야 한다**
   피드에서 릴스는 대부분 음소거로 시작한다. **자막이 정보를 다 져야 한다** —
   음악에만 기대면 소리를 켠 사람만 무슨 행사인지 안다.

**4. 인스타 UI 가 화면의 40%를 가린다**
   위 14%는 계정·설명, 아래 25%는 캡션·버튼, 오른쪽 15%는 좋아요·공유.
   자막은 그 안쪽(세로 20~70%)에만 둔다. 가운데 두면 안전한 게 아니라
   **아래가 위험하다.**

**5. 끝과 시작을 붙여 둔다**
   릴스는 자동으로 되감아 다시 튼다. 마지막 프레임이 첫 프레임과 비슷하면
   이어 보이고, 그만큼 재생 시간이 늘어난다. 끝 카드를 넣되 마지막 0.3초는
   첫 컷으로 되돌린다.

⚠ **실제 손님 얼굴이 나온다.** 우리가 찍은 우리 행사 영상이지만 초상권은 별개다.
   정면으로 카메라를 보는 구간은 피해서 잡았지만, 넓은 그림에도 알아볼 만한
   얼굴이 남는다. 올리기 전에 아는 얼굴이 있으면 한 번 물어보는 게 안전하다.
   컷을 바꾸려면 SETS 의 시작초만 고치면 된다.

python short.py            기본 — deep 124BPM · 15.5초 · 네 박씩
python short.py fast       빠른 판 — heavy 142BPM · 13.5초 · 두 박씩
"""
import os
import subprocess
import sys
import numpy as np
import cv2
from poster_kit import BRAND, tmask, fit, paint
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, '숏폼')
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
INK = np.float32([0.03, 0.04, 0.05])

C = {
    'sky':   'KakaoTalk_20260811_235616682.mp4',   # 10.6s — 하늘 → 수영장 전경
    'side':  'KakaoTalk_20260811_235626504.mp4',   # 5.7s  — 물가에 사람들
    'walk':  'KakaoTalk_20260811_235641308.mp4',   # 6.2s  — 사람이 오간다
    'crowd': 'KakaoTalk_20260811_235704665.mp4',   # 7.8s  — 물 안이 꽉 찼다. 제일 센 그림
    'floor': 'KakaoTalk_20260811_235724410.mp4',   # 7.9s  — 튜브·조명. 색이 제일 좋다
}

# (클립, 시작초, 박 수, 가로 크롭 위치 0~1) — **박 수로 길이를 준다**
# **박 수는 곡이 정한다.** 컷을 곡보다 길게 짜면 ffmpeg 의 -shortest 가 뒤를
# 잘라내고, 끝 카드가 통째로 사라진다 — 실제로 그렇게 잘렸다.
# audio_motion 의 곡은 전부 8마디 = 32박이다.
STYLES = {'deep': 124.0, 'heavy': 142.0}
NBEAT = 32
SETS = {
    # 느린 판 — 네 박씩. 그림을 보여 주는 쪽
    'deep':  [('crowd', 2.2, 4, 0.50), ('floor', 3.2, 4, 0.46), ('side', 1.2, 4, 0.52),
              ('walk', 4.0, 4, 0.42), ('crowd', 5.0, 4, 0.44), ('floor', 5.6, 2, 0.55),
              ('floor', 1.4, 2, 0.42), ('crowd', 0.6, 8, 0.50)],
    # 빠른 판 — 두 박씩. 컷이 두 배로 잦아 스크롤을 잡는 쪽
    'heavy': [('crowd', 2.2, 2, 0.50), ('floor', 3.2, 2, 0.46), ('crowd', 4.4, 2, 0.44),
              ('floor', 5.6, 2, 0.55), ('side', 1.2, 2, 0.52), ('walk', 4.0, 2, 0.42),
              ('floor', 1.4, 2, 0.42), ('crowd', 6.2, 2, 0.50), ('side', 3.4, 2, 0.46),
              ('walk', 0.4, 2, 0.52), ('floor', 0.6, 2, 0.50), ('crowd', 3.4, 2, 0.46),
              ('crowd', 0.6, 8, 0.50)],
}

# (시작 박, 끝 박, 문구) — **정보를 자막이 다 진다.** 음소거로 봐도 알아야 한다
CAPS = [(0, 4, '8월 29일 토요일'), (4, 8, '양재 루프탑'),
        (8, 12, '풀파티 × 솔로파티'), (12, 16, '혼자 와도 되고'),
        (16, 20, '친구 데려와도 된다'), (20, 24, '끝나면 신사 ACE 로 2차')]


def crop916(fr, ox):
    """가로 16:9 를 세로 9:16 으로. **가운데를 무조건 쓰지 않는다** —
    클립마다 사람이 몰린 쪽이 달라서 컷마다 가로 위치를 준다."""
    h, w = fr.shape[:2]
    tw = int(h * W / H)
    x0 = int(np.clip((w - tw) * ox, 0, w - tw))
    return cv2.resize(fr[:, x0:x0 + tw], (W, H), interpolation=cv2.INTER_AREA)


def grade(a):
    """물·조명이 살아나게. 원본은 휴대폰 촬영이라 밋밋하다."""
    a = np.clip((a - 0.5) * 1.14 + 0.5, 0, 1)
    g = a @ np.float32([0.299, 0.587, 0.114])
    a = np.clip(g[..., None] + (a - g[..., None]) * 1.22, 0, 1)   # 채도만 올린다
    a *= np.float32([0.99, 1.005, 1.02])                          # 아주 살짝 시원한 쪽
    yy = np.linspace(-1, 1, H)[:, None, None]
    return np.clip(a * (1 - 0.16 * yy ** 2), 0, 1)                # 위아래만 살짝 눌러 가운데를 세운다


def band(img, cy, half, amt):
    """자막 자리는 배경을 눌러 만든다. 외곽선을 두르면 지저분해진다."""
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= 1 - amt * np.exp(-((yy - cy) / half) ** 2)


def load(key):
    p = os.path.join(SRC, C[key])
    c = cv2.VideoCapture(p)
    if not c.isOpened():
        raise SystemExit(f'못 엶: {p}')
    return c


def render(style='deep'):
    beat = 60.0 / STYLES[style]
    shots = SETS[style]
    nb = sum(s[2] for s in shots)
    assert nb == NBEAT, f'{style}: 컷이 {nb}박인데 곡은 {NBEAT}박이다 — 뒤가 잘린다'
    dur = nb * beat
    nf = int(round(dur * FPS))

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', f'bgm_{style}.wav')
    if not os.path.exists(wav):
        audio_motion.write(style)

    # 컷마다 필요한 프레임을 미리 뽑아 둔다 — 프레임마다 seek 하면 몇 배가 든다
    caps = {}
    plan = []                                   # 프레임별 (클립, 원본 프레임번호, ox)
    t = 0.0
    for key, at, nbeat, ox in shots:
        if key not in caps:
            caps[key] = load(key)
        fps = caps[key].get(cv2.CAP_PROP_FPS) or 30.0
        n = int(round(nbeat * beat * FPS))
        # **컷이 클립 끝을 넘으면 검은 프레임이 나온다.** 실제로 한 컷이
        # 0.5초 동안 통째로 검게 나왔다 — 시작점을 클립 안으로 밀어 넣는다.
        total = caps[key].get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
        need = nbeat * beat
        if at + need > total - 0.05:
            at2 = max(0.0, total - need - 0.05)
            print(f'   {key}: {at:.1f}s 는 클립({total:.1f}s)을 넘는다 → {at2:.1f}s 로 당김')
            at = at2
        for i in range(n):
            plan.append((key, int((at + i / FPS) * fps), ox))
        t += nbeat * beat
    plan = plan[:nf] + [plan[-1]] * max(0, nf - len(plan))

    raw = os.path.join(OUT, f'raw_{style}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}
    for i, (key, fno, ox) in enumerate(plan):
        c = caps[key]
        if last.get(key) != fno - 1:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
        ok, fr = c.read()
        if not ok:
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, fno))
            ok, fr = c.read()
        last[key] = fno
        if not ok:
            fr = np.zeros((1080, 1920, 3), np.uint8)
        img = grade(crop916(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), ox).astype(np.float32) / 255)

        tt = i / FPS
        b = tt / beat
        # ── 자막. **아래 25%·위 14% 는 인스타 UI 가 덮는다** ──
        for b0, b1, txt in CAPS:
            if b0 <= b < b1:
                k = np.clip((b - b0) / 0.35, 0, 1)
                cy = H * 0.615
                band(img, cy, H * 0.055, 0.62 * k)
                paint(img, tmask(txt, KRB, int(64), 0.02), W / 2, cy,
                      color=PAPER, a=float(k), anchor='c')

        # ── 끝 카드 — 마지막 여덟 박 ─────────────────────────
        tail = nb - 6
        if b >= tail:
            k = np.clip((b - tail) / 0.5, 0, 1)
            img *= 1 - 0.86 * k
            cy = H * 0.44
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.84, 0.10), 0.10),
                  W / 2, cy, color=PAPER, a=float(k), anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 30, 0.36), W / 2, cy + H * 0.052,
                  color=AQUA, a=float(k), anchor='c')
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 40, 0.02), W / 2, cy + H * 0.105,
                  color=PAPER, a=float(k) * 0.96, anchor='c')
            paint(img, tmask('사전예약 · 프로필 링크', KR, 34, 0.02), W / 2, cy + H * 0.152,
                  color=CORAL, a=float(k) * 0.96, anchor='c')
        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        c.release()

    final = os.path.join(OUT, f'short_{style}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {dur:.2f}s  {nb}박')


if __name__ == '__main__':
    for s in (sys.argv[1:] or ['deep']):
        render('heavy' if s in ('long', 'fast') else s)
