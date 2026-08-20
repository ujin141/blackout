"""**인쇄용 CMYK 변환.** RGB PNG → CMYK TIFF.

    python to_cmyk.py out/band            → out/band_cmyk/*.tif
    python to_cmyk.py out/coupon 260      → 잉크량 상한을 260% 로

## 왜 PNG 로 못 보내나

PNG 에는 CMYK 가 없습니다. 인쇄소가 CMYK 를 요구하면 TIFF 나 PDF 여야 하고,
**변환은 프로파일을 물려서 해야** 합니다 — 그냥 뒤집는 계산으로 바꾸면
색이 통째로 틀어집니다.

## 잉크량(TAC)이 진짜 문제다

프로파일만 물려서 변환하면 검정 바탕이 **C67 M68 Y82 K80 = 298%** 로 나옵니다.
네 색을 다 얹은 값인데, **코팅 안 된 종이에 300% 를 뿌리면 안 마릅니다.**
번지고, 뒷장에 묻고, 손목에 차는 밴드면 땀에 지워집니다.

    코팅지      300~320% 까지
    비코팅지    240~260%          ← 타이벡 밴드는 여기
    신문지      240% 이하

넘는 자리는 **CMY 만 비율대로 줄이고 K 는 그대로 둡니다.** K 를 같이 줄이면
검정이 흐려지는데, CMY 를 줄이면 색조는 거의 그대로면서 잉크만 빠집니다.

## 검정은 프로파일에 맡기지 않는다

비코팅 프로파일은 K 를 80% 까지만 씁니다. 그대로 두면 우리 검정 바탕이
**진회색으로 뜹니다** — 실제로 그렇게 나왔습니다.

그래서 원본이 거의 검정인 픽셀은 **리치블랙을 직접 박습니다.**

    C40 M30 Y30 K100 = 200%

K 100% 에 CMY 를 얹은 인쇄소 표준 배합입니다. K 만 100% 로 두면(단색 검정)
비코팅지에서 얇고 바래 보이고, CMY 를 더 얹으면 잉크량만 늘고 안 마릅니다.

## 프로파일

`JapanColor2001Uncoated` 를 씁니다 — 국내 인쇄소 기본값이고, 타이벡은
코팅지가 아닙니다. 업체가 다른 걸 쓰면 `PROFILE` 만 바꾸세요.
윈도우에 깔린 프로파일 목록은 `C:\\Windows\\System32\\spool\\drivers\\color`.
"""
import os
import sys
import glob
import numpy as np
from PIL import Image, ImageCms

COLOR = r'C:\Windows\System32\spool\drivers\color'
PROFILE = 'JapanColor2001Uncoated.icc'
TAC = 250                                  # 잉크량 상한 %. 비코팅지 기준
DPI = 300
# 인쇄소 표준 리치블랙. K 만 100 이면 비코팅지에서 바래 보이고,
# CMY 를 더 얹으면 잉크량만 는다
RICH_BLACK = np.float32([40, 30, 30, 100])
BLACK_AT = 0.10                            # 원본 RGB 가 이보다 어두우면 리치블랙으로


def transform():
    src = ImageCms.createProfile('sRGB')
    dst = ImageCms.getOpenProfile(os.path.join(COLOR, PROFILE))
    return dst, ImageCms.buildTransformFromOpenProfiles(
        src, dst, 'RGB', 'CMYK',
        renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC)


def limit_tac(a, tac):
    """잉크량 상한. **CMY 만 줄이고 K 는 건드리지 않는다.**

    K 를 같이 줄이면 검정이 회색으로 뜬다. CMY 를 비율대로 줄이면
    색조는 거의 유지되면서 잉크만 빠진다."""
    a = a.astype(np.float32)
    cmy, k = a[..., :3], a[..., 3:]
    over = cmy.sum(axis=2, keepdims=True) + k - tac
    hit = over > 0
    if not hit.any():
        return a, 0.0
    room = np.maximum(tac - k, 0)                       # CMY 가 쓸 수 있는 몫
    s = cmy.sum(axis=2, keepdims=True)
    scale = np.where((s > 0) & hit, np.minimum(1.0, room / np.maximum(s, 1e-6)), 1.0)
    return np.concatenate([cmy * scale, k], axis=2), float(hit.mean() * 100)


def convert(folder, tac=TAC):
    dst_profile, tf = transform()
    out = folder.rstrip('/\\') + '_cmyk'
    os.makedirs(out, exist_ok=True)
    icc = dst_profile.tobytes()
    files = sorted(glob.glob(os.path.join(folder, '*.png')))
    if not files:
        raise SystemExit(f'{folder} 에 png 가 없습니다')
    for p in files:
        im = Image.open(p).convert('RGB')
        c = ImageCms.applyTransform(im, tf)
        a = np.asarray(c, np.float32) / 255 * 100
        before = a.sum(axis=2).max()
        # **검정을 먼저 박고 나서 잉크량을 잡는다.** 순서가 반대면
        # 리치블랙(200%)이 상한에 안 걸리는데도 다시 손대게 된다
        rgb = np.asarray(im, np.float32) / 255
        blk = rgb.max(axis=2) < BLACK_AT
        a[blk] = RICH_BLACK
        a, pct = limit_tac(a, tac)
        after = a.sum(axis=2).max()
        c = Image.fromarray(np.clip(a / 100 * 255, 0, 255).astype(np.uint8), 'CMYK')
        name = os.path.splitext(os.path.basename(p))[0]
        q = os.path.join(out, name + '.tif')
        c.save(q, 'TIFF', compression='tiff_lzw', dpi=(DPI, DPI), icc_profile=icc)
        print(f'{name:26} {c.size[0]}×{c.size[1]}  잉크 {before:.0f}% → {after:.0f}%  '
              f'(잉크 줄인 픽셀 {pct:.0f}%, 리치블랙 {blk.mean()*100:.0f}%)  '
              f'{os.path.getsize(q)/1024:.0f}KB')
    print(f'\n{out}  ·  {PROFILE}  ·  상한 {tac}%')


if __name__ == '__main__':
    args = sys.argv[1:]
    folder = args[0] if args else 'out/band'
    convert(folder, int(args[1]) if len(args) > 1 else TAC)
