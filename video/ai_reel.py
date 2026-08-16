"""**상황극 릴스를 붙인다** — 1080×1920 · 15초 · 128BPM.

    out/short/ai_reel.mp4

대본은 `mail/릴스_상황극_대본.md` 에 있습니다. 여기는 **붙이는 쪽**입니다.

    video/ai/1.mp4 ~ 5.mp4    핑계 넷 + 주인공. AI 로 뽑든 직접 찍든 상관없음
    video/ai/0.mp4            (선택) 첫 컷. 폰 단톡방 화면 같은 것
    숏폼/*.mp4                 마지막 두 컷 — **진짜 현장 영상**

**클립이 없어도 돕니다.** 없는 자리는 검은 판에 자막만 올려서 채웁니다 —
하나도 안 뽑은 상태에서 먼저 돌려 보고 타이밍부터 확인하라고 그렇게 뒀습니다.

**마지막 두 컷은 AI 로 만들지 않습니다.** 앞이 다 만든 그림이었다가 마지막에
진짜가 나와야 "실제로 있는 행사" 로 읽힙니다. 끝까지 가짜면 밈으로 끝나고
예약으로 안 갑니다.

**자막은 화면 아래쪽 0.615H 에 둡니다.** 릴스 기준입니다 — 스토리로 올릴
거면 `story.py` 를 쓰세요. 거기는 답장 막대 때문에 자막이 더 위에 있습니다.

python ai_reel.py
"""
import os
import subprocess
import numpy as np
import cv2
import short as S
from short import crop916, grade, band, load
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
AI = os.path.join(HERE, 'ai')
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)
os.makedirs(AI, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM
SEG = 4                                   # 한 컷 = 네 박 = 1.875초
TAIL = 4                                  # 끝 네 박은 마무리 판

PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])
INK = np.float32([0.030, 0.032, 0.038])

# (소스, 자막)
#   'ai:N'   → video/ai/N.mp4
#   'live:키,시작초,가로위치' → 진짜 현장 영상 (short.py 의 클립)
#
# **핑계는 넷까지다.** 다섯째부터는 같은 농담이 반복되는 걸로 읽혀서 넘긴다.
# **마지막 두 컷이 파는 자리다.** 앞의 웃음은 여기까지 데려오는 게 일이다.
CUTS = [('ai:0',              '토요일에 풀파티 가자고 했더니'),
        ('ai:1',              '나 그날 본가 가'),
        ('ai:2',              '돈이 없어…'),
        ('ai:3',              '남자들끼리 가면 못 놀아'),
        ('ai:4',              '혼자 가면 뻘쭘하잖아'),
        ('ai:5',              '그래서 혼자 갔습니다'),
        ('live:crowd,3.3,0.50', '9시 반부터 솔로파티'),
        ('live:crowd,5.4,0.44', '다 혼자 온 사람들이었어요')]


def ai_frames(n, need):
    """video/ai/N.mp4 에서 need 초를 뽑는다. 없으면 None."""
    p = os.path.join(AI, f'{n}.mp4')
    if not os.path.exists(p):
        return None
    c = cv2.VideoCapture(p)
    if not c.isOpened():
        return None
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    total = c.get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
    # **AI 클립은 대개 4~5초다.** 컷보다 짧으면 처음부터 다시 돈다 —
    # 검은 프레임을 내보내는 것보다 한 번 더 도는 게 낫다
    out = []
    for i in range(int(round(need * FPS))):
        t = (i / FPS) % max(total - 0.05, 0.1)
        c.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, fr = c.read()
        out.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok
                   else np.zeros((1080, 1920, 3), np.uint8))
    c.release()
    return out


def live_frames(key, at, need):
    c = load(key)
    fps = c.get(cv2.CAP_PROP_FPS) or 30.0
    total = c.get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
    if at + need > total - 0.05:
        at = max(0.0, total - need - 0.05)
    out = []
    for i in range(int(round(need * FPS))):
        c.set(cv2.CAP_PROP_POS_FRAMES, int((at + i / FPS) * fps))
        ok, fr = c.read()
        out.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok
                   else np.zeros((1080, 1920, 3), np.uint8))
    c.release()
    return out


def fit916(fr, ox=0.5, z=1.0):
    """세로 클립은 그대로, 가로 클립만 잘라 세운다. AI 도구가 9:16 을
    안 지키고 뱉을 때가 있어서 여기서 받아 준다."""
    h, w = fr.shape[:2]
    if w / h <= W / H + 0.02:
        s = max(W / w, H / h) * z
        r = cv2.resize(fr, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_AREA)
        x0 = max(0, (r.shape[1] - W) // 2)
        y0 = max(0, (r.shape[0] - H) // 2)
        return r[y0:y0 + H, x0:x0 + W]
    return crop916(fr, ox, z)


def build_plan():
    """컷마다 프레임 목록을 만든다. 없는 컷은 None 으로 두고 나중에 판으로 채운다."""
    need = SEG * BEAT
    plan = []
    for src, txt in CUTS:
        if src.startswith('ai:'):
            fr = ai_frames(int(src[3:]), need)
        else:
            key, at, ox = src[5:].split(',')
            fr = live_frames(key, float(at), need)
        plan.append((fr, txt, src))
    return plan


def missing_card(txt, j, n):
    """클립이 없는 자리. **검게 두고 자막만 올린다** — 여기 뭐가 들어가야
    하는지 보이고, 타이밍도 그대로 확인된다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    u = j / max(n - 1, 1)
    paint(img, tmask('클립 없음', BRAND, 22, 0.34), W / 2, H * 0.40,
          color=PAPER, a=0.30, anchor='c')
    rule(img, H * 0.44, W * (0.5 - 0.16 * u), W * (0.5 + 0.16 * u), PAPER, 0.18, 2)
    return img


def render():
    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    plan = build_plan()
    have = sum(1 for fr, _, _ in plan if fr is not None)
    print(f'클립 {have}/{len(plan)}')
    for fr, txt, src in plan:
        if fr is None:
            print(f'   없음 {src}  ({txt})')

    seglen = int(round(SEG * BEAT * FPS))
    nf = int(round(NBEAT * BEAT * FPS))
    raw = os.path.join(OUT, 'raw_ai.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    lg = logo(44)
    nseg = len(plan)
    for i in range(nf):
        b = (i / FPS) / BEAT
        k = min(int(b // SEG), nseg - 1)
        j = min(i - k * seglen, seglen - 1)
        frames, txt, src = plan[k]

        if frames is None:
            img = missing_card(txt, j, seglen)
        else:
            z = 1.0 + 0.05 * (j / max(seglen - 1, 1))
            ox = 0.5 if src.startswith('ai:') else float(src.split(',')[2])
            img = grade(fit916(frames[min(j, len(frames) - 1)], ox, z)
                        .astype(np.float32) / 255)

        # 서명 — 처음부터 끝까지. 릴스는 팔로워 밖으로 나간다
        paint(img, lg, W * 0.072, H * 0.062, color=PAPER, a=0.86)

        # 자막
        if b < NBEAT - TAIL and txt:
            kk = float(np.clip((b - k * SEG) / 0.20, 0, 1))
            cy = H * 0.615
            band(img, cy, H * 0.058, 0.62 * kk)
            fs = min(64, fit(txt, KRB, W * 0.86, 0.02))
            paint(img, tmask(txt, KRB, fs, 0.02), W / 2, cy, color=PAPER,
                  a=kk, anchor='c')

        # ── 끝 네 박 — 마무리 판 ────────────────────────────
        if b >= NBEAT - TAIL:
            kk = float(np.clip((b - (NBEAT - TAIL)) / 0.5, 0, 1))
            img *= 1 - 0.88 * kk
            cy = H * 0.38
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.84, 0.10), 0.10),
                  W / 2, cy, color=PAPER, a=kk, anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 28, 0.36), W / 2, cy + H * 0.042,
                  color=AQUA, a=kk, anchor='c')
            rule(img, cy + H * 0.072, W * 0.24, W * 0.76, PAPER, 0.26 * kk, 2)
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 38, 0.02), W / 2,
                  cy + H * 0.104, color=PAPER, a=kk * 0.96, anchor='c')
            paint(img, tmask(EV.price_str(), KR, 32, 0.02), W / 2, cy + H * 0.146,
                  color=PAPER, a=kk * 0.78, anchor='c')
            k2 = float(np.clip((b - (NBEAT - TAIL) - 1.0) / 0.5, 0, 1))
            if k2 > 0.004:
                paint(img, tmask('프로필 링크에서 예약', KRB, 52, 0.02), W / 2,
                      cy + H * 0.212, color=CORAL, a=k2, anchor='c')
                paint(img, tmask(EV.HANDLE, BRAND, 22, 0.22), W / 2, cy + H * 0.256,
                      color=PAPER, a=k2 * 0.75, anchor='c')

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, 'ai_reel.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {NBEAT * BEAT:.2f}s')
    if have < len(plan):
        print(f'video/ai/N.mp4 를 채우면 검은 판이 그 클립으로 바뀝니다.')


if __name__ == '__main__':
    render()
