"""**인쇄소에 그대로 넘기는 폴더를 만든다.** 한 번에.

    python print_pack.py

    out/print/
      BAND/          밴드 8장 (앞뒤 × 4등급)   PDF + TIFF
      COUPON/        쿠폰 4장 (앞뒤 + A4 시트)  PDF + TIFF
      사양서.txt      크기 · 색 · 잉크량 · 주의사항

## 왜 스크립트로 묶나

밴드 한 번, 쿠폰 한 번, CMYK 한 번, PDF 한 번 — 네 번을 손으로 돌리면
**하나를 빼먹는다.** 실제로 크기를 바꾸고 CMYK 만 다시 뽑아서, 인쇄소에
옛 크기 PDF 를 보낼 뻔했다. 원본부터 PDF 까지 한 줄로 다시 만든다.

## 넘길 때 PDF 를 쓴다

국내 인쇄소는 대부분 AI 나 PDF 를 받는다. TIFF 도 같이 넣어 두는 건
업체가 원본 이미지를 달라고 할 때가 있어서다 — **먼저 PDF 를 보내고,
달라고 하면 TIFF 를 준다.**
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'print')

JOBS = [
    # (이름, 만드는 명령들, 원본 폴더)
    ('BAND', [['band.py'], ['band.py', 'back']], 'out/band'),
    ('COUPON', [['coupon.py']], 'out/coupon'),
]


def run(args):
    r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(f'{" ".join(args)} 실패\n{r.stdout}\n{r.stderr}')
    return r.stdout


def spec():
    import band
    import coupon
    bw, bh = band.BAND_MM
    cw, ch = coupon.CUT_MM
    aw, ah = coupon.ART_MM
    return f"""BLACKOUT — 인쇄 사양서

■ 입장 밴드 (BAND/)
  크기        {bw:.0f} × {bh:.0f} mm   (재단 = 편집)
  해상도      {band.DPI}dpi  →  {band.W} × {band.H} px
  파일        BAND_1_GUEST_FRONT / BACK … BAND_4_STAFF_FRONT / BACK  (8장)
  재질        타이벡 (비코팅)
  도련        {'없음' if not band.BLEED else f'{band.BLEED_MM:.1f}mm'}
  접착 탭     오른쪽 끝 {band.TAB / band.DPI * 25.4:.1f}mm — 인쇄 없이 비워 뒀습니다
  안전 여백   위아래 {band.SAFE / band.DPI * 25.4:.1f}mm
  등급        GUEST 검정 / VIP 마르살라 / VVIP 샴페인 / STAFF 흰색
              막대 개수로도 갈립니다 (1·2·3·4개)

■ 웰컴드링크 쿠폰 (COUPON/)
  재단(칼선)  {cw:.0f} × {ch:.0f} mm      ← 주문 사이즈
  편집사이즈  {aw:.0f} × {ah:.0f} mm      ← 파일 크기. 칼선 밖은 배경만 이어집니다
  안전영역    칼선에서 {coupon.SAFE_MM:.0f}mm 안쪽. 글자는 전부 이 안에 있습니다
  해상도      {coupon.DPI}dpi  →  {coupon.AW} × {coupon.AH} px
  파일        COUPON_FRONT / BACK  (낱장)
              COUPON_SHEET_FRONT / BACK  (A4 모아찍기)
  양면        장변 제본(long-edge). 뒷면 시트는 좌우를 뒤집어 뒀습니다
  뜯는 선     왼쪽 스터브에 타공선이 그려져 있습니다

■ 공통
  색공간      CMYK
  프로파일    JapanColor2001Uncoated (파일에 심어 뒀습니다)
  잉크량      최대 250% (비코팅 기준)
  검정        리치블랙 C40 M30 Y30 K100 = 200%
  최소 획     0.25mm
  포맷        PDF (무손실). TIFF 도 함께 넣었습니다

■ 확인 부탁드립니다
  1. 도련이 필요하면 몇 mm 인지 알려주세요 — 바로 다시 드립니다
  2. 프로파일이 다르면 알려주세요 (코팅지면 잉크량도 300%까지 올립니다)
  3. 밴드 접착 탭이 왼쪽이면 좌우 반전해서 다시 드립니다

BLACKOUT  우진   ujin141@naver.com
"""


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    import to_cmyk
    import to_pdf
    for name, cmds, src in JOBS:
        print(f'── {name} ' + '─' * 40)
        for c in cmds:
            run(c)
        # **중간 폴더를 먼저 비운다.** 파일 이름이 바뀌거나 빠져도 옛것이
        # 남아 패키지에 딸려 간다 — 확인용 가이드가 인쇄 파일에 섞였던 게 이거다
        for sub in (src + '_cmyk', src + '_pdf'):
            if os.path.exists(sub):
                shutil.rmtree(sub)
        to_cmyk.convert(src)
        to_pdf.convert(src + '_cmyk')
        dst = os.path.join(OUT, name)
        os.makedirs(dst)
        for sub, ext in ((src + '_pdf', '.pdf'), (src + '_cmyk', '.tif')):
            for f in sorted(os.listdir(sub)):
                if f.endswith(ext):
                    shutil.copy2(os.path.join(sub, f), os.path.join(dst, f))
        print()
    with open(os.path.join(OUT, '사양서.txt'), 'w', encoding='utf-8') as f:
        f.write(spec())
    n = sum(len(os.listdir(os.path.join(OUT, d))) for d, _, _ in
            [(j[0], 0, 0) for j in JOBS])
    print(f'{OUT}  ·  파일 {n}개 + 사양서.txt')
    print('이 폴더를 통째로 보내면 됩니다.')


if __name__ == '__main__':
    main()
