"""
한글 폰트 경로를 OS별로 찾는다.
윈도우는 맑은 고딕, 맥은 Pretendard → Apple SD Gothic 순으로 본다.
영문(Michroma)은 video/assets/ 에 들어 있어 어디서나 동일하다.
"""
import os
import sys

_HOME = os.path.expanduser('~')

# (일반, 볼드) 후보 — 앞에서부터 실제로 있는 것을 쓴다
_CANDIDATES = {
    'win32': [
        ('C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/malgunbd.ttf'),
    ],
    'darwin': [
        (f'{_HOME}/Library/Fonts/Pretendard-Regular.otf',
         f'{_HOME}/Library/Fonts/Pretendard-Bold.otf'),
        ('/Library/Fonts/Pretendard-Regular.otf',
         '/Library/Fonts/Pretendard-Bold.otf'),
        ('/System/Library/Fonts/AppleSDGothicNeo.ttc',
         '/System/Library/Fonts/AppleSDGothicNeo.ttc'),
        ('/System/Library/Fonts/Supplemental/AppleGothic.ttf',
         '/System/Library/Fonts/Supplemental/AppleGothic.ttf'),
    ],
}
_LINUX = [
    (f'{_HOME}/.fonts/Pretendard-Regular.otf', f'{_HOME}/.fonts/Pretendard-Bold.otf'),
    ('/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
     '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'),
    ('/usr/share/fonts/opentype/pretendard/Pretendard-Regular.otf',
     '/usr/share/fonts/opentype/pretendard/Pretendard-Bold.otf'),
]


def _pick():
    for reg, bold in _CANDIDATES.get(sys.platform, _LINUX):
        if os.path.exists(reg):
            return reg, (bold if os.path.exists(bold) else reg)
    raise FileNotFoundError(
        '한글 폰트를 찾지 못했습니다.\n'
        '맥이면 Pretendard를 설치하세요 — https://github.com/orioncactus/pretendard/releases\n'
        '(내려받은 otf를 ~/Library/Fonts 에 넣으면 됩니다)\n'
        '또는 video/fonts.py 의 후보 목록에 쓰던 폰트 경로를 직접 추가하세요.')


KR, KRB = _pick()

if KR == KRB and 'AppleSDGothicNeo' in KR:
    print('[fonts] 볼드가 없어 같은 굵기로 대체합니다. '
          'Pretendard를 설치하면 원본 디자인과 같아집니다.')
