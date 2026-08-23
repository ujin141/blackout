"""
**곡이 이미 있는 곡과 겹치는지 잰다.**

    python audio_check.py                       out/ 안의 모든 wav 를 서로 비교
    python audio_check.py out/cut/bgm_neon.wav  한 곡을 나머지 전부와 비교

## 왜 필요한가

곡이 스무 개가 넘었다. **"BPM 만 다르면 다른 곡" 이라고 생각하기 쉬운데
아니다** — 같은 신스로 같은 코드를 치면 빠르기만 다른 같은 곡으로 들린다.
반대로 BPM 이 같아도 악기가 다르면 다른 곡이다.

귀로 스무 곡을 비교할 수는 없다. 세 가지를 재서 숫자로 본다.

    음색   로그 주파수 24밴드의 평균 세기. **어떤 악기를 썼는가**
    리듬   온셋 강도의 자기상관. **템포와 그 안의 결**
    음정   크로마 12 — 도레미 분포. **조성과 코드**

셋 다 0~1 유사도로 내고, **음색 0.97 이상 + 리듬 0.90 이상**이면 같은
곡으로 본다. 하나만 높은 건 괜찮다 — 같은 신스로 다른 리듬을 치거나,
같은 템포로 다른 악기를 쓰는 건 다른 곡이다.

## 임계값을 왜 저렇게 잡았는가

전부 우리 손으로 만든 곡이라 **바탕이 비슷하다**(같은 킥·하이햇 함수를
쓴다). 그래서 절대값이 원래 높게 나온다 — 무작정 0.8 로 자르면 전부
걸린다. 이미 서로 다르다고 확인된 곡들끼리의 값을 보고 그 위로 잡았다.
"""
import glob
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

SR_A = 22050                      # 비교용으로 낮춰 잡는다. 음색 비교엔 충분하다
TONE_HI, RHY_HI = 0.97, 0.90      # 둘 다 넘으면 같은 곡


def load(path):
    """wav 를 모노 float 로. 길이가 다르면 앞 20초만 본다."""
    w = wave.open(path, 'rb')
    n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
    raw = w.readframes(n)
    w.close()
    if sw != 2:
        return None, 0
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    step = max(1, int(round(sr / SR_A)))
    x = x[::step]
    return x[:SR_A * 20], sr


def spec(x, nfft=2048, hop=512):
    win = np.hanning(nfft).astype(np.float32)
    m = 1 + (len(x) - nfft) // hop
    if m < 4:
        return None
    S = np.empty((m, nfft // 2 + 1), np.float32)
    for i in range(m):
        S[i] = np.abs(np.fft.rfft(x[i * hop:i * hop + nfft] * win))
    return S


def tone(S):
    """음색 지문. 로그 주파수 40밴드에 **DCT 를 걸고 첫 계수를 버린다.**

    처음엔 밴드 평균을 그대로 비교했는데 서른한 곡이 전부 0.999 로 나왔다 —
    우리 곡은 다 광대역이라 **총 에너지 분포만 보면 다 같아 보인다.**
    DCT 계수(=MFCC)는 스펙트럼의 '모양' 만 남기고, 첫 계수(전체 밝기)를
    버리면 악기 차이가 드러난다."""
    f = np.fft.rfftfreq(2048, 1.0 / SR_A)
    edges = np.geomspace(40, SR_A / 2, 41)
    v = np.array([S[:, (f >= a) & (f < b)].mean() if ((f >= a) & (f < b)).any() else 0.0
                  for a, b in zip(edges[:-1], edges[1:])], np.float32)
    v = np.log(v + 1e-6)
    n = len(v)
    k = np.arange(n)[:, None]
    c = (np.cos(np.pi * k * (2 * np.arange(n) + 1) / (2 * n)) @ v)[1:14]
    return c / (np.linalg.norm(c) + 1e-9)


def rhythm(S):
    """온셋 강도의 자기상관. **템포와 그 안의 결.**"""
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    flux -= flux.mean()
    if not np.any(flux):
        return np.zeros(200, np.float32)
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    ac = ac[:200] / (ac[0] + 1e-9)
    return ac.astype(np.float32)


def chroma(S):
    """도레미 12분포. **조성과 코드.**"""
    f = np.fft.rfftfreq(2048, 1.0 / SR_A)
    ok = f > 55
    pc = np.zeros(12, np.float32)
    midi = 69 + 12 * np.log2(np.maximum(f[ok], 1e-6) / 440.0)
    idx = np.mod(np.round(midi).astype(int), 12)
    e = S[:, ok].mean(0)
    for k in range(12):
        pc[k] = e[idx == k].sum()
    return pc / (np.linalg.norm(pc) + 1e-9)


def cos(a, b):
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9))


def fingerprint(path):
    x, _ = load(path)
    if x is None or len(x) < 4096:
        return None
    S = spec(x)
    if S is None:
        return None
    return tone(S), rhythm(S), chroma(S)


def main(targets):
    paths = sorted(glob.glob(os.path.join(OUT, '**', '*.wav'), recursive=True))
    fps = {}
    for p in paths:
        fp = fingerprint(p)
        if fp:
            fps[p] = fp
    if not fps:
        raise SystemExit('out/ 에 wav 가 없습니다 — audio_*.py 를 먼저 돌리세요')

    if targets:
        pairs = [(t, p) for t in targets for p in fps if os.path.abspath(p)
                 != os.path.abspath(t)]
        for t in targets:
            if t not in fps:
                fp = fingerprint(t)
                if not fp:
                    raise SystemExit(f'못 읽었습니다: {t}')
                fps[t] = fp
    else:
        ks = list(fps)
        pairs = [(a, b) for i, a in enumerate(ks) for b in ks[i + 1:]]

    rows = []
    for a, b in pairs:
        ta, ra, ca = fps[a]
        tb, rb, cb = fps[b]
        rows.append((cos(ta, tb), cos(ra, rb), cos(ca, cb), a, b))
    # **음색과 리듬을 같이 보고 정렬한다.** 음색만으로 줄 세우면 리듬까지
    # 닮은 쌍이 목록 아래로 밀려 안 보인다
    rows.sort(key=lambda r: r[0] * 0.6 + r[1] * 0.4, reverse=True)

    bad = [r for r in rows if r[0] >= TONE_HI and r[1] >= RHY_HI]
    print(f'곡 {len(fps)}개 · 비교 {len(rows)}쌍\n')
    print(f'{"음색":>6} {"리듬":>6} {"음정":>6}   쌍')
    for t, r, c, a, b in rows[:12]:
        mark = '  ← 같은 곡으로 들린다' if (t >= TONE_HI and r >= RHY_HI) else ''
        print(f'{t:6.3f} {r:6.3f} {c:6.3f}   '
              f'{os.path.basename(a)[:-4]} ↔ {os.path.basename(b)[:-4]}{mark}')
    print()
    if bad:
        print(f'★ 겹치는 쌍 {len(bad)}개 — 주인공 악기를 갈아야 합니다')
        for t, r, c, a, b in bad:
            print(f'    {os.path.basename(a)[:-4]} ↔ {os.path.basename(b)[:-4]}'
                  f'   음색 {t:.3f} · 리듬 {r:.3f}')
        return 1
    print('겹치는 곡 없습니다')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
