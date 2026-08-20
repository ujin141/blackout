"""**인쇄용 CMYK PDF.** TIFF → PDF (무손실).

    python to_pdf.py out/coupon_cmyk       → out/coupon_pdf/*.pdf
    python to_pdf.py out/band_cmyk

## 왜 PDF 인가

국내 인쇄소는 대부분 **AI 나 PDF** 를 받습니다. TIFF 도 받는 데가 있지만
"이미지 파일은 별도 문의" 인 곳이 많고, 온라인 인쇄소는 아예 안 받기도 합니다.

우리 판은 코드로 그린 래스터라 AI(벡터)로는 못 만듭니다. **PDF 가 현실적인
최선**이고, 300dpi 원본 크기라 확대할 일이 없어 인쇄 품질에 문제가 없습니다.

## PIL 의 PDF 저장을 안 쓰는 이유

`Image.save(..., 'PDF')` 는 CMYK 를 **JPEG(DCTDecode)로 압축**합니다.
1.5MB TIFF 가 185KB 가 되는데, 우리 판은 가는 선과 작은 글자뿐이라
손실 압축이 가장자리를 갉습니다. 여기서는 **Flate(무손실)** 로 직접 씁니다.

## 색공간

`/ICCBased` 로 프로파일을 통째로 심습니다. `/DeviceCMYK` 로만 두면
"어느 CMYK 냐" 가 파일에 안 남아서 인쇄소가 자기 프로파일로 다시 해석합니다.
"""
import os
import sys
import glob
import zlib
import numpy as np
from PIL import Image

DPI = 300


def build_pdf(a, icc, dpi=DPI):
    """CMYK 배열 → PDF 바이트. **한 장짜리, 이미지 하나.**

    페이지 크기는 포인트(1/72인치)다 — 픽셀을 dpi 로 나눠 인치를 구하고
    72를 곱한다. 이게 어긋나면 인쇄소에서 크기가 다르게 잡힌다."""
    h, w = a.shape[:2]
    pw, ph = w / dpi * 72.0, h / dpi * 72.0
    img = zlib.compress(a.tobytes(), 9)
    prof = zlib.compress(icc, 9)
    content = f'q {pw:.4f} 0 0 {ph:.4f} 0 0 cm /Im0 Do Q'.encode()
    cz = zlib.compress(content, 9)

    objs = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw:.4f} {ph:.4f}] '
        f'/Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>'.encode(),
        b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(cz) + cz + b'\nendstream',
        (f'<< /Type /XObject /Subtype /Image /Width {w} /Height {h} '
         f'/ColorSpace 6 0 R /BitsPerComponent 8 /Filter /FlateDecode '
         f'/Length {len(img)} >>\nstream\n').encode() + img + b'\nendstream',
        b'[/ICCBased 7 0 R]',
        b'<< /N 4 /Alternate /DeviceCMYK /Length %d /Filter /FlateDecode >>\nstream\n'
        % len(prof) + prof + b'\nendstream',
    ]
    out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode() + o + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode()
    for off in offsets:
        out += f'{off:010d} 00000 n \n'.encode()
    out += (f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n'
            f'startxref\n{xref}\n%%EOF\n').encode()
    return bytes(out)


def convert(folder):
    out = folder.rstrip('/\\').replace('_cmyk', '') + '_pdf'
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(folder, '*.tif')))
    if not files:
        raise SystemExit(f'{folder} 에 tif 가 없습니다')
    for p in files:
        im = Image.open(p)
        if im.mode != 'CMYK':
            raise SystemExit(f'{p} 가 CMYK 가 아닙니다 — to_cmyk.py 를 먼저 돌리세요')
        icc = im.info.get('icc_profile')
        if not icc:
            raise SystemExit(f'{p} 에 ICC 프로파일이 없습니다')
        pdf = build_pdf(np.asarray(im), icc)
        q = os.path.join(out, os.path.splitext(os.path.basename(p))[0] + '.pdf')
        open(q, 'wb').write(pdf)
        w, h = im.size
        print(f'{os.path.basename(q):30} {w/DPI*25.4:.0f}×{h/DPI*25.4:.0f}mm  '
              f'{len(pdf)/1024:.0f}KB')
    print(f'\n{out}  ·  CMYK · 무손실(Flate) · ICC 심음')


if __name__ == '__main__':
    convert(sys.argv[1] if len(sys.argv) > 1 else 'out/coupon_cmyk')
