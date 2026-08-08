"""
포스터 다섯 시안을 영상으로 — 1080×1920 · 30fps · BGM 포함.

포스터를 **매 프레임 다시 그리지 않습니다.** build() 한 번에 1~2초가 걸려서
450프레임을 다시 그리면 시안 하나에 10분이 넘습니다.
정지 이미지를 한 장 만들어 두고 그 위에 시간에 따른 처리를 얹습니다.
시안마다 움직임을 다르게 준 건 디자인 언어가 다르기 때문입니다.

    A split   물결        위쪽을 사인파로 흔든다. 수면이 흔들리는 판이니까
    B club    스트로브     박마다 흰 섬광 + 스캔라인이 굴러간다. 테크노 플라이어니까
    C ticket  빛 스침      종이가 빛을 받는 각도로 미세하게 기운다. 인쇄물이니까
    D neon    점멸        켜질 때 깜빡이다 자리 잡고, 킥마다 후광이 부푼다. 간판이니까
    E grid    칸 등장      칸이 하나씩 밀려 들어온다. 칸으로 짠 판이니까

BGM 은 `audio_reel.py` 의 다섯 곡을 그대로 씁니다. 시안마다 다른 곡을 물려서
나란히 틀어도 같은 영상으로 안 들립니다. wav 가 없으면 자동으로 만듭니다.

    A festival 128 · B techno 145 · C citypop 105 · D hard 155 · E bounce 132

킥 위치를 BPM 에서 계산해 화면이 같이 뜁니다 — 소리와 안 맞으면 그냥 배경음악입니다.

python poster_motion.py            다섯 개 전부
python poster_motion.py neon grid  골라서
"""
import os
import sys
import subprocess
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'poster')
REEL = os.path.join(HERE, 'out', 'reel')
os.makedirs(OUT, exist_ok=True)

W, H, FPS = 1080, 1920, 30

# 시안 → (포스터 모듈, BGM 스타일, 움직임)
SPECS = {
    'split':  ('poster_split',  'festival', 'water'),
    'club':   ('poster_club',   'techno',   'strobe'),
    'ticket': ('poster_ticket', 'citypop',  'card'),
    'neon':   ('poster_neon',   'hard',     'flicker'),
    'grid':   ('poster_grid',   'bounce',   'tiles'),
}


def bgm(style):
    """wav 가 없으면 만든다. 길이(초)를 돌려준다."""
    import audio_reel
    p = os.path.join(REEL, f'bgm_{style}.wav')
    if not os.path.exists(p):
        audio_reel.write(style)
    bpmv, bars = audio_reel.STYLES[style]
    return p, bpmv, (60.0 / bpmv) * 4 * bars


def kick_env(t, bpmv, sharp=9.0):
    """킥 봉투. 박 머리에서 1, 지수로 떨어진다."""
    b = t / (60.0 / bpmv)
    return float(np.exp(-(b % 1.0) * sharp))


def cam(base, z, dx=0.0, dy=0.0):
    """줌·이동. resize 후 자르는 것보다 warpAffine 이 훨씬 싸다."""
    Mx = np.float32([[z, 0, (1 - z) * W / 2 + dx], [0, z, (1 - z) * H / 2 + dy]])
    return cv2.warpAffine(base, Mx, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def chroma(img, off):
    """색분해 흔들림. 정지본에 이미 색분해가 있어도 이건 시간축이라 따로 논다."""
    if off < 0.5:
        return img
    o = int(off)
    out = img.copy()
    out[:, :, 0] = np.roll(img[:, :, 0], o, axis=1)
    out[:, :, 2] = np.roll(img[:, :, 2], -o, axis=1)
    return out


# ── 시안별 움직임 ─────────────────────────────────────────
def m_water(base, t, dur, bpmv, grids):
    """위쪽을 사인파로 밀어 물결을 만든다. 아래(클럽)로 갈수록 진폭을 죽인다."""
    gx, gy = grids
    amp = 5.0 + 2.5 * kick_env(t, bpmv, 6.0)
    fade = np.clip(1.0 - (gy / H - 0.30) / 0.22, 0, 1).astype(np.float32)
    dx = np.sin(gy * 0.022 + t * 2.4).astype(np.float32) * amp * fade
    dy = np.sin(gx * 0.013 + t * 1.7).astype(np.float32) * amp * 0.45 * fade
    img = cv2.remap(base, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    img = cam(img, 1.02 + 0.045 * (t / dur))
    return chroma(img, 3.5 * kick_env(t, bpmv, 14.0))


def m_strobe(base, t, dur, bpmv, grids):
    """박마다 섬광, 스캔라인이 굴러간다. 셋잇단 흔들림으로 정박을 깬다."""
    e = kick_env(t, bpmv, 11.0)
    img = cam(base, 1.05 - 0.035 * (t / dur), dx=np.sin(t * 31.0) * 3.0 * e)
    sc = (np.sin((np.arange(H, dtype=np.float32) * 0.55) - t * 26.0) * 0.5 + 0.5) ** 3
    img = img * (1.0 - sc[:, None, None] * 0.10)
    img = img + (e ** 4) * 0.30
    return chroma(img, 6.0 * e)


def m_card(base, t, dur, bpmv, grids):
    """종이가 기울며 빛을 받는다. 인쇄물이라 세게 흔들면 싸구려가 된다."""
    gx, gy = grids
    a = np.sin(t * 0.85) * 0.010
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    dst = np.float32([[W * a, 0], [W * (1 - a), H * 0.006],
                      [W * (1 + a), H], [-W * a, H * (1 - 0.006)]])
    img = cv2.warpPerspective(base, cv2.getPerspectiveTransform(src, dst), (W, H),
                              flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    band = ((gx / W) * 0.7 + (gy / H) * 0.3 - (t / dur * 1.9 - 0.45))
    img = img + np.clip(1.0 - np.abs(band) / 0.13, 0, 1)[..., None] ** 2 * 0.16
    return cam(img, 1.015 + 0.02 * (t / dur))


def m_flicker(base, t, dur, bpmv, grids, glow=None):
    """켜질 때 깜빡이다 자리 잡는다. 처음 1.1초가 이 시안의 전부다."""
    if t < 1.1:
        seq = [0.10, 0.85, 0.15, 0.95, 0.30, 1.0, 0.55, 1.0]
        k = seq[min(int(t / 1.1 * len(seq)), len(seq) - 1)]
    else:
        k = 0.94 + 0.06 * kick_env(t, bpmv, 7.0)
    img = cam(base, 1.02 + 0.035 * (t / dur), dx=np.sin(t * 47.0) * 1.2)
    img = img * (0.55 + 0.45 * k)
    if glow is not None:
        img = img + glow * (0.35 + 0.65 * kick_env(t, bpmv, 5.0)) * k
    return img


def m_tiles(base, t, dur, bpmv, grids, rects=None):
    """칸이 하나씩 밀려 들어온다. 1.7초 안에 다 들어오고 그 뒤엔 숨만 쉰다."""
    img = cam(base, 1.012 + 0.022 * (t / dur))
    if t < 1.7:
        canvas = np.zeros_like(img)
        canvas[:] = img[0, 0]
        for i, (y0, y1) in enumerate(rects):
            s = np.clip((t - i * 0.13) / 0.42, 0, 1)
            s = 1 - (1 - s) ** 3                       # 감속
            if s <= 0:
                continue
            off = int((1 - s) * W * (0.55 if i % 2 == 0 else -0.55))
            row = np.roll(img[y0:y1], off, axis=1)
            if off > 0:
                row[:, :off] = canvas[y0:y1, :off]
            elif off < 0:
                row[:, off:] = canvas[y0:y1, off:]
            canvas[y0:y1] = row * s + canvas[y0:y1] * (1 - s)
        img = canvas
    else:
        img = img * (0.97 + 0.03 * kick_env(t, bpmv, 8.0))
    return img


MOTION = {'water': m_water, 'strobe': m_strobe, 'card': m_card,
          'flicker': m_flicker, 'tiles': m_tiles}


def render(key):
    mod_name, style, motion = SPECS[key]
    mod = __import__(mod_name)
    print(f'[{key}] 정지본 렌더…')
    base = np.ascontiguousarray(mod.build(W, H, True).astype(np.float32))

    wav, bpmv, dur = bgm(style)
    nf = int(round(dur * FPS))
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)

    extra = {}
    if motion == 'flicker':
        lum = base @ np.float32([0.299, 0.587, 0.114])
        hi = np.clip(lum - 0.50, 0, 1) / 0.5
        extra['glow'] = cv2.GaussianBlur(hi, (0, 0), 26)[..., None] * \
            np.float32([0.42, 0.85, 0.20]) * 0.55
    if motion == 'tiles':
        import poster_grid
        _, _, _, ys = poster_grid.layout(W, H)
        extra['rects'] = [(int(a), int(b)) for a, b in ys.values()]

    fn = MOTION[motion]
    raw = os.path.join(OUT, f'raw_{key}.mp4')
    p = subprocess.Popen(
        ['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
         '-pix_fmt', 'yuv420p', raw],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rng = np.random.default_rng(11)
    for fi in range(nf):
        t = fi / FPS
        img = fn(base, t, dur, bpmv, (gx, gy), **extra)
        img = img + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.008
        if t < 0.45:                                   # 들어오고
            img *= t / 0.45
        tail = dur - t
        if tail < 0.5:                                 # 나간다
            img *= max(0.0, tail / 0.5)
        p.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

    final = os.path.join(OUT, f'motion_{key}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', raw, '-i', wav,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '22',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '224k',
                    '-shortest', '-movflags', '+faststart', final],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    os.remove(raw)
    print(f'{final}  {dur:.1f}s  {style} {bpmv:.0f}BPM')


if __name__ == '__main__':
    keys = [k.lower() for k in sys.argv[1:]] or list(SPECS)
    for k in keys:
        if k not in SPECS:
            print(f'모르는 시안: {k} — {", ".join(SPECS)}')
            continue
        render(k)
