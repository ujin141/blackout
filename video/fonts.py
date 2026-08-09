"""
한글 폰트 경로.

**시스템 기본 폰트(맑은 고딕)는 쓰지 않습니다.** 어디에나 깔려 있어서 안전하지만,
바로 그래서 "기본값" 으로 보입니다 — 워드 문서와 같은 글씨로 포스터를 만들면
디자인한 판이 아니라 출력한 판이 됩니다.

우선순위는 **Pretendard → SUIT → 나눔바른고딕 → 맑은 고딕** 입니다.
앞의 둘은 한국 디자인 현장의 사실상 표준이고, 획 굵기가 고르고 자간이 정돈돼 있어
Michroma(영문 브랜드 폰트) 와 나란히 놨을 때 따로 놀지 않습니다.
맑은 고딕은 **하나도 못 찾았을 때의 마지막 수단**입니다.

세 가지를 내보냅니다.

    KR   본문 · 정보줄       (Pretendard Medium)
    KRB  강조                (Pretendard Bold)
    KRD  큰 제목             (Pretendard ExtraBold)

**본문에 Regular 가 아니라 Medium 을 씁니다.** 포스터는 대부분 어두운 바탕이고,
어두운 바탕의 흰 글자는 실제보다 가늘어 보입니다(광증). 한 단 굵은 게 제자리입니다.
"""
import os
import sys

_HOME = os.path.expanduser('~')
_WIN_USER = os.path.join(_HOME, 'AppData', 'Local', 'Microsoft', 'Windows', 'Fonts')
_DIRS = ['C:/Windows/Fonts', _WIN_USER,
         os.path.join(_HOME, 'Library', 'Fonts'), '/Library/Fonts',
         '/System/Library/Fonts', '/System/Library/Fonts/Supplemental',
         os.path.join(_HOME, '.fonts'), os.path.join(_HOME, '.local/share/fonts'),
         '/usr/share/fonts/truetype/nanum', '/usr/share/fonts/opentype/pretendard',
         os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')]

# (본문, 강조, 제목) — 앞에서부터 세 개가 다 있는 조합을 쓴다.
# 한 가족 안에서 굵기를 고르는 게 중요하다: 가족이 섞이면 같은 판에서
# 글자 폭과 획 대비가 달라져 두 가지 글씨로 읽힌다.
_FAMILIES = [
    ('Pretendard-Medium.ttf', 'Pretendard-Bold.ttf', 'Pretendard-ExtraBold.ttf'),
    ('Pretendard-Regular.otf', 'Pretendard-Bold.otf', 'Pretendard-ExtraBold.otf'),
    ('SUIT-Medium.ttf', 'SUIT-Bold.ttf', 'SUIT-Heavy.ttf'),
    ('NanumBarunGothic.ttf', 'NanumBarunGothicBold.ttf', 'NanumBarunGothicBold.ttf'),
    ('NanumGothic.ttf', 'NanumGothicBold.ttf', 'NanumGothicExtraBold.ttf'),
    ('AppleSDGothicNeo.ttc', 'AppleSDGothicNeo.ttc', 'AppleSDGothicNeo.ttc'),
    ('malgun.ttf', 'malgunbd.ttf', 'malgunbd.ttf'),
]


def _find(name):
    for d in _DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def _pick():
    for fam in _FAMILIES:
        paths = [_find(n) for n in fam]
        if all(paths):
            return paths
    raise FileNotFoundError(
        '한글 폰트를 찾지 못했습니다.\n'
        'Pretendard 를 설치하세요 — https://github.com/orioncactus/pretendard/releases\n'
        '(윈도우: 받은 ttf 를 우클릭 → 설치 / 맥: ~/Library/Fonts 에 넣기)\n'
        '또는 video/assets/ 에 폰트 파일을 넣으면 그것도 찾습니다.')


KR, KRB, KRD = _pick()

if os.path.basename(KR) == 'malgun.ttf':
    print('[fonts] 맑은 고딕으로 떨어졌습니다 — 포스터가 기본 폰트로 보입니다.\n'
          '        Pretendard 를 설치하면 원래 디자인이 나옵니다.')
