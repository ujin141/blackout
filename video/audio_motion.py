"""
포스터 영상용 BGM — 어둡고 비어 있는 판.

`audio_poster.py` 곡들은 "뽕짝 같다"는 지적을 받았다. 볼륨 문제가 아니라 짜임 문제다.
촌스러움은 세 가지에서 나온다. 이 파일은 셋 다 반대로 짠다.

    1  베이스가 엇박에서 튄다        →  킥 밑에 **한 음으로 계속 깔린다**
       킥 쿵 / 베이스 짝 / 킥 쿵 / 베이스 짝 이 그대로 쿵짝이다.
       클럽 트랙은 서브가 마디 내내 지속되고, 킥이 올 때마다 사이드체인으로
       눌렸다 되돌아온다. 같은 저음인데 "쿵-짝"이 아니라 "쿵-스으"가 된다.

    2  선율이 있다                   →  **음이 오르내리지 않는다**
       마림바·아르페지오처럼 음정이 움직이면 그 순간 노래가 된다. 여기 곡들은
       코드를 한 번 치고 길게 끌 뿐, 어디로도 가지 않는다.

    3  칸을 다 채운다                →  **빈칸을 남긴다**
       16분을 셰이커로 다 메우면 행진곡이다. 그루브는 소리가 아니라
       소리가 없는 자리에서 나온다.

    스타일  BPM  골격
    deep    124  딥하우스. 킥 4 + 엇박 오픈햇. 코드는 두 마디에 한 번
    dark    130  다크테크노. 킥 럼블(킥을 잔향에 통과시켜 저역만 남긴 것) + 얇은 클랩
    dub     121  덥테크노. 제일 비어 있다. 스네어 없음. 엇박 코드 스탭과 잔향뿐
    party   128  페스티벌 하우스. 엇박 오픈햇 + 클랩 + 드롭 뒤 리프. 유일하게 신나는 판
    heavy   142  하프타임. 킥 1·3&, 스네어 3박. 뭉갠 베이스 한 음. 제일 센 판

BPM·조성 모두 릴스(128·145·132·155·105)·포스터(122·138·136·118·110·126)와 안 겹친다.

python audio_motion.py           전부
python audio_motion.py dark      하나만
"""
import os
import sys
import wave
import numpy as np
from audio import (SR, place, lp, hp, reverb, clap, hat, noise_riser,
                   kick as kick0, impact)
from audio_reel import sat, subf, snare, stab, pad, soft_kick, hard_kick

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

STYLES = {'deep': (124.0, 8), 'dark': (130.0, 8), 'dub': (121.0, 8),
          'heavy': (142.0, 8), 'party': (128.0, 8)}

# 전부 단조 계열 낮은 음. 밝은 조성은 그 자체로 촌스럽다
ROOT = {'deep': 55.00,     # A1
        'dark': 32.70,     # C1 — 제일 낮다. 럼블이 바닥을 채우는 판
        'dub':  36.71,     # D1
        'heavy': 61.74,    # B1
        'party': 43.65}    # F1 — 제일 신나는 판. 나머지 넷과 조성이 안 겹친다

# 코드는 **마이너 9** 하나로 고정한다. 진행을 넣으면 그 순간 노래가 된다
MIN9 = (1.0, 1.189, 1.498, 2.245)          # root · m3 · 5 · 9


def sustain(f, dur, gain=1.0, drift=0.6):
    """마디 내내 이어지는 서브. **감쇠가 거의 없다** — 짧게 끊으면 그게 '짝'이 된다.
    아주 느린 디튠 두 겹으로 살짝 흔들어 둬야 죽은 사인파로 안 들린다."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) +
         0.55 * np.sin(2 * np.pi * f * 1.004 * t + 0.7) +
         0.30 * np.sin(2 * np.pi * f * 0.5 * t))          # 옥타브 아래 한 겹
    x *= 1 - drift * 0.12 * np.sin(2 * np.pi * 0.13 * t)   # 아주 느린 흔들림
    env = np.minimum(1.0, t / 0.05) * np.minimum(1.0, (dur - t) / 0.08)
    return np.tanh(x * 0.9) * env * gain


def rumble(kickbus, tail=2.2):
    """킥을 긴 잔향에 통과시키고 저역만 남긴 것. 요즘 테크노의 바닥이 이것이다.
    킥을 크게 키우면 시끄럽기만 하고, 럼블을 깔면 판이 깊어진다."""
    return lp(reverb(kickbus, tail, 1.0), 150, 2)


def build(style):
    bpm, bars = STYLES[style]
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * bars
    N = int(dur * SR)
    T = lambda b, x=0.0: (b - 1) * bar + x * beat
    R = ROOT[style]
    CH = [R * 4 * m for m in MIN9]

    kickbus = np.zeros(N); perc = np.zeros(N)
    bass = np.zeros(N); lead = np.zeros(N); fx = np.zeros(N)
    kicks = []
    DROP = bars // 2 + 1

    # ── DEEP — 딥하우스. 엇박 오픈햇이 굴리고 서브가 깔린다 ──
    if style == 'deep':
        for b in range(1, bars + 1):
            g = 0.86 if b < DROP else 1.0
            for x in range(4):
                place(kickbus, soft_kick(0.46, g), T(b, x)); kicks.append(T(b, x))
                place(perc, hat(0.19, 0.16 * g, open_=True), T(b, x + 0.5))
            # 닫힌 햇은 **네 칸 중 두 칸만**. 다 채우면 행진곡이 된다
            for at in (0.75, 2.75):
                place(perc, hat(0.05, 0.10 * g), T(b, at))
            if b % 2 == 1:
                place(perc, clap(0.30 * g), T(b, 2))
            place(bass, sustain(R, bar * 0.99, 0.62), T(b))     # 마디 내내
            if b % 2 == 1:                                      # 코드는 두 마디에 한 번
                place(lead, pad(CH, bar * 1.9, 0.15, 1500), T(b))

    # ── DARK — 럼블이 바닥. 위는 얇게. 선율 하나도 없다 ────
    elif style == 'dark':
        for b in range(1, bars + 1):
            g = 0.84 if b < DROP else 1.0
            for x in range(4):
                place(kickbus, hard_kick(0.38, g), T(b, x)); kicks.append(T(b, x))
            for i in range(8):                                  # 16분이 아니라 8분. 아주 작게
                if i % 4 != 1:                                  # 한 칸씩 비운다
                    place(perc, hat(0.04, 0.075 * g), T(b, i * 0.5))
            place(perc, clap(0.26 * g, ), T(b, 2))
            place(bass, sustain(R, bar * 0.99, 0.58), T(b))
            if b >= DROP and b % 2 == 0:                        # 드론 한 겹. 음정은 안 움직인다
                place(lead, pad([R * 4, R * 4.756], bar * 1.9, 0.09, 900), T(b))
        place(fx, noise_riser(bar * 1.5, 200, 7000, 0.22), T(DROP - 1))

    # ── DUB — 제일 비어 있다. 엇박 코드와 잔향만 ──────────
    elif style == 'dub':
        for b in range(1, bars + 1):
            g = 0.80 if b < DROP else 0.98
            for x in range(4):
                place(kickbus, soft_kick(0.50, g), T(b, x)); kicks.append(T(b, x))
            place(perc, hat(0.05, 0.07 * g), T(b, 1.5))         # 마디에 한 번뿐
            place(bass, sustain(R, bar * 0.99, 0.66), T(b))
            for at in (0.5, 2.5):                               # 엇박 스탭 — 덥테크노의 전부
                place(lead, stab(CH[:3], beat * 0.42, 0.20, 1300, 0.24), T(b, at))

    # ── PARTY — 페스티벌 하우스. 이 파일에서 유일하게 '신나는' 판 ──
    # 나머지 넷은 어둡고 비어 있게 짰다. 여기만 반대로 간다 — 다만 촌스러워지는
    # 선은 그대로 지킨다. **엇박은 하이햇이 치지 베이스가 안 친다**, 리프는
    # 코드 안에서만 돌고 음계를 오르내리지 않는다.
    elif style == 'party':
        RIFF = [1.0, 1.498, 2.0, 1.498, 1.783, 1.498]      # 근음·5도·옥타브만. 3음을 안 쓴다
        for b in range(1, bars + 1):
            g = 0.84 if b < DROP else 1.0
            for x in range(4):
                place(kickbus, kick0(0.44, g), T(b, x)); kicks.append(T(b, x))
                place(perc, hat(0.20, 0.22 * g, open_=True), T(b, x + 0.5))   # 엇박 오픈햇 — 이게 굴린다
            place(perc, clap(0.42 * g), T(b, 1)); place(perc, clap(0.42 * g), T(b, 3))
            for i in range(8):                                # 셰이커. 두 칸은 비운다
                if i % 4 != 2:
                    place(perc, hat(0.04, 0.09 * g), T(b, i * 0.5 + 0.25))
            place(bass, sustain(R, bar * 0.99, 0.60), T(b))
            if b >= DROP:                                     # 드롭 뒤에만 리프가 돈다
                for i, m in enumerate(RIFF):
                    place(lead, stab([R * 8 * m], beat * 0.34, 0.26 * g, 5200, 0.22),
                          T(b, i * 0.66))
            else:
                place(lead, pad([R * 4, R * 5.99], bar * 0.98, 0.10, 1800), T(b))
        place(fx, noise_riser(bar * 1.6, 300, 9000, 0.34), T(DROP - 1))
        place(fx, impact(2.2, 0.7), T(DROP))

    # ── HEAVY — 하프타임. 킥이 네 박을 안 친다 ────────────
    else:
        for b in range(1, bars + 1):
            g = 0.86 if b < DROP else 1.0
            for at in (0.0, 2.5):
                place(kickbus, hard_kick(0.40, g), T(b, at)); kicks.append(T(b, at))
            place(perc, snare(0.30, 0.80 * g, 1.0), T(b, 2))    # 3박 하나. 그게 하프타임이다
            for at in (1.5, 3.5):
                place(perc, hat(0.05, 0.11 * g), T(b, at))
            # 베이스도 한 음. 뭉개서 두껍게 만들 뿐 음정은 안 움직인다
            place(bass, sat(sustain(R, bar * 0.99, 0.70), 2.6), T(b))
            if b >= DROP and b % 4 == 1:
                place(lead, pad(CH[:3], bar * 3.8, 0.11, 1100), T(b))
        place(fx, noise_riser(bar * 1.2, 240, 8000, 0.26), T(DROP - 1))

    # ── 사이드체인 ────────────────────────────────────────
    # **여기가 뽕짝과 클럽을 가른다.** 얕게 누르면 베이스가 킥과 따로 들려서
    # 결국 쿵짝이 되고, 깊게 누르면 둘이 한 덩어리로 숨을 쉰다.
    depth = {'deep': 0.62, 'dark': 0.66, 'dub': 0.70, 'heavy': 0.58, 'party': 0.60}[style]
    hold = {'deep': 0.34, 'dark': 0.30, 'dub': 0.42, 'heavy': 0.36, 'party': 0.28}[style]
    duck = np.ones(N)
    tt = np.arange(N) / SR
    for at in kicks:
        i = int(at * SR); j = min(N, i + int(hold * SR))
        if j <= i:
            continue
        seg = np.clip((tt[i:j] - at) / hold, 0, 1)
        duck[i:j] = np.minimum(duck[i:j], (1 - depth) + depth * seg ** 0.55)
    rm = rumble(kickbus, 2.4 if style == 'dark' else 1.7)
    bass = bass * duck
    lead = lead * duck ** 0.7
    rm = rm * duck ** 0.5

    mix = (kickbus + perc * 0.9 + bass +
           rm * {'deep': 0.30, 'dark': 0.55, 'dub': 0.42, 'heavy': 0.34, 'party': 0.26}[style] +
           reverb(lead, 2.6 if style == 'dub' else 1.8, 0.42) * 0.9 +
           reverb(fx, 2.0, 0.34) * 0.7)
    mix = hp(mix, 26, 2)
    mix = sat(mix * 0.9, 1.25)
    mix /= (np.abs(mix).max() + 1e-9)
    mix *= 0.95
    f = int(0.35 * SR)
    mix[-f:] *= np.linspace(1, 0, f) ** 1.2
    mix[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

    d = int(0.009 * SR)
    right = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([mix * 0.94 + right * 0.06, right * 0.18 + mix * 0.82], axis=1)
    st /= (np.abs(st).max() + 1e-9)
    return st * 0.95, dur


def write(style):
    np.random.seed(abs(hash(style)) % 2 ** 31)
    st, d = build(style)
    p = os.path.join(OUT, f'bgm_{style}.wav')
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'{p}  {d:.2f}s  {STYLES[style][0]:.0f}BPM')
    return d


if __name__ == '__main__':
    for k in (sys.argv[1:] or list(STYLES)):
        write(k)
