"""**스토리 전용 영상** — 현장 영상이 계속 돌고 자막만 얹힌다. 15초 · 128BPM.

    out/short/story_ad.mp4     1080×1920

`short.py`(릴스 A안)와 엔진은 같고 **셋이 다르다.** 스토리는 릴스가 아니다.

    자막 높이   릴스는 0.615H 에 둔다. 스토리는 아래에서 답장 막대가 올라와서
                0.545H 로 올린다 — 릴스 자리에 두면 막대에 반쯤 먹힌다
    링크 자리   아래 STICKER 구간을 비워 둔다. **거기에 링크 스티커를 올린다**
    문구        릴스는 "여기 서울이에요" 로 궁금하게 만든다. 스토리는 이미
                우리를 아는 사람이 보므로 바로 판다 — 날짜 · 값 · 예약

**스토리에서는 '프로필 링크에서 예약' 이라고 쓰지 않는다.** 스토리에는
링크 스티커를 바로 붙일 수 있어서, 프로필까지 가라고 하면 한 번 더 걷게 하는
것이다. 마지막 판이 "여기 눌러서 예약" 인 이유고, 그 '여기' 가 스티커 자리다.

python story.py
"""
import os
import subprocess
import numpy as np
import cv2
import short as S
from short import crop916, grade, band, load, SETS, C
from poster_kit import BRAND, tmask, fit, paint, logo, rule
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'short')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30
BPM, NBEAT = 128.0, 32
BEAT = 60.0 / BPM
TAIL = 6                                  # 끝 여섯 박은 예약 판

PAPER = np.float32([0.99, 1.00, 1.00])
AQUA = np.float32([0.34, 0.94, 1.00])
CORAL = np.float32([1.00, 0.44, 0.40])

CAP_Y = 0.545                             # 자막 — 답장 막대 위
STICKER = (0.640, 0.780)                  # **비워 둔다.** 링크 스티커 자리

# (시작 박, 끝 박, 글자). **스토리는 궁금하게 만들 필요가 없다** — 스토리를
# 보는 사람은 이미 팔로워다. 바로 판다.
# 값을 넣는 이유는 광고판과 같다 — 못 낼 사람이 스티커를 누르기 전에 걸러진다.
CAPS = [(0,  4,  '혼자 와도 되는 풀파티'),
        (4,  8,  '8월 29일 토요일'),
        (8,  12, '양재 루프탑'),
        (12, 17, '9시 반부터 솔로파티'),
        (17, 21, EV.LEFT_LINE),
        (21, 26, EV.PRICE_PUSH)]     # 값을 숨기면 여기가 '현장 판매 없습니다'


def plan_frames(shots, beat):
    """컷마다 필요한 프레임을 미리 뽑아 둔다 — 프레임마다 seek 하면 몇 배가 든다."""
    caps, plan = {}, []
    for key, at, nbeat, ox in shots:
        if key not in caps:
            caps[key] = load(key)
        fps = caps[key].get(cv2.CAP_PROP_FPS) or 30.0
        total = caps[key].get(cv2.CAP_PROP_FRAME_COUNT) / max(fps, 1e-6)
        need = nbeat * beat
        # 컷이 클립 끝을 넘으면 검은 프레임이 나온다 — 시작점을 안으로 민다
        if at + need > total - 0.05:
            at = max(0.0, total - need - 0.05)
        n = int(round(need * FPS))
        for i in range(n):
            plan.append((key, int((at + i / FPS) * fps), ox,
                         1.0 + 0.06 * (i / max(n - 1, 1))))
    return caps, plan


def render():
    beat = BEAT
    shots = SETS['party']
    nb = sum(s[2] for s in shots)
    assert nb == NBEAT, f'컷이 {nb}박인데 곡은 {NBEAT}박이다 — 뒤가 잘린다'

    import audio_motion
    wav = os.path.join(HERE, 'out', 'poster', 'bgm_party.wav')
    if not os.path.exists(wav):
        audio_motion.write('party')

    nf = int(round(NBEAT * beat * FPS))
    caps, plan = plan_frames(shots, beat)
    plan = plan[:nf] + [plan[-1]] * max(0, nf - len(plan))

    raw = os.path.join(OUT, 'raw_story.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}
    lg = logo(46)
    for i, (key, fno, ox, z) in enumerate(plan):
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
        img = grade(crop916(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), ox, z).astype(np.float32) / 255)

        b = (i / FPS) / beat

        # **서명은 처음부터 끝까지.** 스토리는 어느 초에 멈춰도 누구 판인지
        # 보여야 한다 — 스토리는 링크를 안 누르면 계정으로 갈 길이 없다
        paint(img, lg, W * 0.075, H * 0.108, color=PAPER, a=0.88)
        paint(img, tmask(EV.HANDLE, BRAND, 21, 0.22), W * 0.075 + lg.shape[1] + 18,
              H * 0.108 + lg.shape[0] * 0.5, color=PAPER, a=0.72)

        if b < NBEAT - TAIL:
            for b0, b1, txt in CAPS:
                if b0 <= b < b1 and txt:
                    k = float(np.clip((b - b0) / 0.16, 0, 1))
                    cy = H * CAP_Y
                    band(img, cy, H * 0.058, 0.64 * k)
                    fs = min(66, fit(txt, KRB, W * 0.84, 0.02))
                    paint(img, tmask(txt, KRB, fs, 0.02), W / 2, cy,
                          color=PAPER, a=k, anchor='c')

        # ── 끝 여섯 박 — 예약 판 ────────────────────────────
        else:
            k = float(np.clip((b - (NBEAT - TAIL)) / 0.5, 0, 1))
            img *= 1 - 0.86 * k
            cy = H * 0.320
            paint(img, tmask(EV.NAME, BRAND, fit(EV.NAME, BRAND, W * 0.84, 0.10), 0.10),
                  W / 2, cy, color=PAPER, a=k, anchor='c')
            paint(img, tmask(EV.FORMAT, BRAND, 28, 0.36), W / 2, cy + H * 0.042,
                  color=AQUA, a=k, anchor='c')
            rule(img, cy + H * 0.072, W * 0.24, W * 0.76, PAPER, 0.26 * k, 2)
            paint(img, tmask('8.29 SAT  ·  양재 루프탑', KR, 38, 0.02), W / 2,
                  cy + H * 0.104, color=PAPER, a=k * 0.96, anchor='c')
            paint(img, tmask(EV.price_str() or EV.PRICE_LINE, KR, 34, 0.02), W / 2,
                  cy + H * 0.146, color=PAPER, a=k * 0.80, anchor='c')
            # **'여기 눌러서' 의 '여기' 는 바로 아래 스티커 자리다.**
            # 프로필로 보내지 않는다 — 스토리는 링크를 바로 붙일 수 있다
            k2 = float(np.clip((b - (NBEAT - TAIL) - 1.2) / 0.5, 0, 1))
            if k2 > 0.004:
                yb = H * (STICKER[0] - 0.048)
                paint(img, tmask('아래 눌러서 예약', KRB, 54, 0.02), W / 2, yb,
                      color=CORAL, a=k2, anchor='c')
                # 스티커 자리를 가리키는 화살표 한 개. 글자를 더 넣지 않는다
                ax, ay = W / 2, H * (STICKER[0] - 0.012)
                for s in (-1, 1):
                    cv2.line(img, (int(ax + s * 26), int(ay - 13)), (int(ax), int(ay + 9)),
                             tuple(float(v) for v in CORAL * k2), 5, cv2.LINE_AA)

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        c.release()

    final = os.path.join(OUT, 'story_ad.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {NBEAT * beat:.2f}s')
    print(f'link sticker zone: y {int(H * STICKER[0])}~{int(H * STICKER[1])}px')


if __name__ == '__main__':
    render()
