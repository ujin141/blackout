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

python short_card.py           행사 소개판
python short_card.py sale      판매 상태판 (1차 마감 · 테이블만 · 2차 일정)
python short_card.py promo     참여 이벤트판 (팔로우·댓글·공유 → 무료 입장)
"""
import os
import re
import subprocess
import numpy as np
import cv2
from PIL import Image
import poster_kit
from poster_kit import status_tag as _tag
from poster_kit import BRAND, tmask, fit, paint
from fonts import KR, KRB
import event as EV
import short
from poster_kit import HEROES, duotone

# 현장 클립이 없을 때 대신 쓸 사진. **클립은 손님 얼굴이 있어 저장소에 없다** —
# 폴더가 비어 있으면 판이 통째로 안 나오는 대신, 사진으로 채우고 밀어 넣는다.
PHOTO_CROP = [dict(focus=0.52, zoom=1.10), dict(focus=0.50, zoom=1.10),
              dict(focus=0.50, zoom=1.00, offx=0.50)]
DUO = (np.float32([0.016, 0.034, 0.054]), np.float32([0.340, 0.520, 0.610]))

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
#
# **두 벌을 둔다.** 행사 소개는 안 바뀌지만 판매 상태는 며칠마다 바뀐다 —
# 한 벌로 두면 "1차 마감" 을 넣는 순간 소개용으로 못 쓴다.
#   기본   행사가 뭔지. 처음 보는 사람용
#   sale   지금 무엇을 파는지. event.py 에서 자동으로 나온다
# **정보를 나열하면 안 움직인다.** 사람을 움직이는 건 막힌 지점이다 —
# 이 행사의 상품은 "혼자 가도 되는 것" 이고, 그게 못 가던 이유이기도 하다.
# 그래서 순서가 막힌 지점 → 답 → 어떻게 → 언제·어디다.
# **첫 장이 전부다.** 스크롤을 멈추는 건 정보가 아니라 대답하게 만드는 질문이다 —
# 머릿속으로 "아니" 든 "맞아" 든 답하는 순간 이미 멈춘 것이다.
# 바꿔 가며 시험할 것 (같은 판에 첫 장만 갈아 끼운다)
#   혼자 가면 이상한가요?      질문. 제일 세다
#   친구 없어서 못 갔죠        아픈 지점 직격
#   아는 사람 없이 오세요       명령형
INTRO = [(DEEP,  '혼자 가면 이상한가요?'),
         (INK,   '아니라고 만들었습니다'),
         (AQUA,  '9시 반부터 한 시간 반'),
         (CORAL, '혼자 온 사람들끼리'),
         (DEEP,  '양재 루프탑 풀파티'),
         (AQUA,  '8월 29일 토요일'),
         (INK,   '밤은 신사 ACE에서')]


_BOTTLE = None


def bottle_on(img, cy, h):
    """참여 이벤트판 첫 칸에만 병을 얹는다. **상품을 말로만 하면 안 믿는다** —
    글자 일곱 칸 중 한 칸은 물건을 보여 주는 데 쓴다.

    원본이 작은 JPG 라 확대하면 압축 블록이 뜬다. 가장자리를 살리는 필터로
    한 번 편 뒤 캐시한다(칸마다 다시 열면 15초짜리가 느려진다)."""
    global _BOTTLE
    if _BOTTLE is None:
        p = os.path.join(poster_kit.STOCK, EV.PROMO_BOTTLE)
        if not os.path.exists(p):
            return
        raw = np.asarray(Image.open(p).convert('RGBA'))
        rgb = cv2.bilateralFilter(raw[..., :3], 11, 46, 46)
        _BOTTLE = np.dstack([rgb, raw[..., 3]]).astype(np.float32) / 255
    b = _BOTTLE
    w = int(h * b.shape[1] / b.shape[0])
    b = cv2.resize(b, (w, int(h)), interpolation=cv2.INTER_AREA)
    H, W = img.shape[:2]
    x0, y0 = (W - w) // 2, int(cy - h / 2)
    x1, y1 = min(W, x0 + w), min(H, y0 + int(h))
    sx, sy = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    sub = b[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
    a = sub[..., 3:4]
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a


def promo_cards():
    """참여 이벤트 판. **판매판과 섞으면 둘 다 죽는다** — 무료로 갈 수 있다는
    말과 테이블만 남았다는 말이 한 판에 있으면 어느 쪽도 안 믿긴다.

    조건 넷을 한 장에 다 적지 않는다. 한 장에 하나씩 넘겨야 읽힌다."""
    # **상품 둘을 한 칸에 붙이면 글자가 68px 로 줄어든다.** 훅 칸에서 제일
    # 하면 안 되는 짓이다 — 두 칸으로 쪼개면 둘 다 132px 로 꽉 찬다.
    c = [(CORAL, EV.PROMO_GET_A),
         (INK,   f'{EV.PROMO_GET_B}도')]
    for d in EV.PROMO_DO:
        c.append((AQUA if len(c) % 2 else DEEP, d))
    c.append((AQUA, f'추첨 {EV.PROMO_TEAMS}팀'))
    c.append((CORAL, EV.PROMO_CTA))
    c.append((INK, f'{EV.PROMO_DUE} 마감'))
    while len(c) < 7:                    # 칸 수는 판이 정한다
        c.insert(-1, (DEEP, EV.PROMO_PUSH))
    return c[:7]


def sale_cards():
    """판매용 카드. **event.py 만 고치면 문구가 따라온다** —
    영상에 숫자를 손으로 박아 두면 다음 차수에 통째로 다시 만들어야 한다.

    자극은 없는 말을 지어내는 게 아니라 **아는 사실을 센 순서로 놓는 것**이다.
    먼저 찼다(사회적 증거) → 남은 게 이것뿐(희소) → 언제까지(마감).
    성비·마지막 기회·가격은 안 쓴다. 확인이 안 됐거나 사실이 아니다."""
    # 판매판의 첫 장은 **사회적 증거**다. 남은 걸 먼저 말하면 안 팔린 것으로 읽히고,
    # 이미 간 사람을 먼저 말하면 안 가면 손해로 읽힌다.
    c = [(DEEP, f'{EV.DONE}명은 이미 갔습니다')]
    if EV.LAST_FULL:
        c.append((INK, f'{EV.LAST_FULL[0]} {EV.LAST_FULL[1]}명 마감'))
    if EV.SALE == 'table':
        c.append((CORAL, '남은 건 테이블뿐'))
    else:
        c.append((CORAL, f'{EV.OPEN_LEFT}자리 남았습니다'))
    if EV.NEXT_OPEN:
        # **마감일이 아니라 여는 날이다.** 지금 못 사는 사람한테 필요한 건
        # 언제 살 수 있느냐이지 언제 닫느냐가 아니다
        m = re.search(r'(\d+/\d+)', EV.NEXT_OPEN)
        c.append((AQUA, f'{EV.OPEN_WAVE[0]}는 {m.group(1)}부터' if m and EV.OPEN_WAVE
                        else EV.NEXT_OPEN))
    c.append((DEEP, '혼자 온 사람들끼리'))
    c.append((AQUA, '8월 29일 토요일'))
    c.append((INK, '양재 루프탑'))
    return c


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


_PHOTO = {}


def photo_shot(idx, j, n):
    """사진 한 장을 9:16 으로. **컷 안에서 밀어 넣는다** — 정지 사진을 그냥
    두면 영상 사이에서 멈춘 것으로 보인다. 6% 안쪽이라 화질은 안 깨진다."""
    k = idx % len(HEROES)
    if k not in _PHOTO:
        _PHOTO[k] = duotone(HEROES[k][0], W, H, *DUO, contrast=1.16, keep=0.30,
                            **PHOTO_CROP[k])
    # **두 번째 바퀴는 더 당긴다.** 사진이 셋인데 칸이 여섯이라 두 번씩 도는데,
    # 같은 배율로 두면 같은 그림이 또 나온 것으로 읽힌다.
    base = 1.0 + 0.14 * (idx // len(HEROES))
    z = base + 0.06 * (j / max(n - 1, 1))
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
    return cv2.warpAffine(_PHOTO[k], M, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def crop916(fr, ox=0.5):
    h, w = fr.shape[:2]
    tw = int(h * W / H)
    x0 = int(np.clip((w - tw) * ox, 0, w - tw))
    return cv2.resize(fr[:, x0:x0 + tw], (W, H), interpolation=cv2.INTER_AREA)


def render(mode='intro'):
    CARDS = {'sale': sale_cards, 'promo': promo_cards}.get(mode, lambda: INTRO)()
    nseg = (NBEAT - TAIL) // SEG                  # 13 칸
    # 글자 판과 현장 컷을 번갈아. 칸 0·2·4… 는 글자, 1·3·5… 는 현장
    order = []
    si_map = {}
    ci = si = 0
    for k in range(nseg):
        if k % 2 == 0:
            order.append(('card', CARDS[ci % len(CARDS)])); ci += 1
        else:
            order.append(('shot', SHOTS[si % len(SHOTS)])); si_map[k] = si; si += 1
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
    raw = os.path.join(OUT, f'raw_card_{mode}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    last = {}

    def grab(key, at, i):
        if key not in caps:
            try:
                caps[key] = short.load(key)
            except SystemExit:
                caps[key] = None
        if caps[key] is None:
            return None
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
            # 참여 이벤트판의 첫 칸에만 병이 들어간다 — 글자를 위로 올려 자리를 낸다
            shot = (mode == 'promo' and k == 2)   # 병은 '샴페인 한 병도' 칸에
            ty = H * (0.255 if shot else 0.47)
            paint(img, tmask(txt, KRB, fs, 0.02), W / 2, ty, color=ink, anchor='c')
            paint(img, tmask(EV.DATE_EN, BRAND, 24, 0.30), W / 2, ty + fs * 0.95,
                  color=ink, a=0.62, anchor='c')
            if shot:
                bottle_on(img, H * 0.655, H * 0.44)
        else:
            key, at = v
            fr = grab(key, at, j)
            if fr is None:                      # 클립이 없으면 사진으로
                img = photo_shot(si_map[k], j, seglen)
            else:
                img = grade(crop916(fr).astype(np.float32) / 255)

        # **상태 띠는 처음부터 끝까지 붙어 있다.** 스크롤로 지나가는 영상이라
        # 어느 초에 멈춰도 "1차 끝났고 2차 열렸다" 가 보여야 한다.
        # 인스타 UI 가 아래 25% 를 덮으니 그 위에 둔다.
        if b < NBEAT - TAIL:
            # 왼쪽 여백선에 붙인다. 가운데에 홀로 뜨면 나중에 얹은 것으로 읽힌다
            _tag(img, W * 0.085, H * 0.688, 40, color=PAPER, accent=CORAL,
                 width=W * 0.80, bar=0.58)

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
            _tag(img, W / 2, H * 0.40 + 172, 36, color=PAPER, accent=CORAL,
                 a=float(kk), width=W * 0.80, anchor='c')
            k2 = np.clip((b - (NBEAT - TAIL) - 1.2) / 0.5, 0, 1)
            if k2 > 0.004:
                cta = (EV.PROMO_CTA if mode == 'promo'
                       else EV.RESERVE_NOW if mode == 'sale' else '프로필 링크에서 예약')
                paint(img, tmask(cta, KRB, 52, 0.02), W / 2, H * 0.40 + 240,
                      color=CORAL, a=float(k2), anchor='c')
                paint(img, tmask(EV.PARTNERS_STR, BRAND,
                                 min(20, fit(EV.PARTNERS_STR, BRAND, W * 0.88, 0.16)), 0.16),
                      W / 2, H * 0.40 + 324, color=PAPER, a=float(k2) * 0.66, anchor='c')

        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    for c in caps.values():
        if c is not None:
            c.release()

    final = os.path.join(OUT, {'sale': 'short_sale.mp4',
                              'promo': 'short_promo.mp4'}.get(mode, 'short_card.mp4'))
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav, '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {W}x{H}  {dur:.2f}s  글자 판 {ci}칸 · 현장 컷 {si}칸')


if __name__ == '__main__':
    import sys
    for m in (sys.argv[1:] or ['intro']):
        render(m)
