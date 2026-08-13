"""
행사 정보 — **여기 한 곳만 고치면 포스터 다섯 시안이 전부 따라옵니다.**

전에는 시안마다 파일 맨 위에 같은 정보를 복사해 뒀습니다. 시안이 다섯으로 늘면서
날짜 하나 바뀔 때마다 다섯 군데를 고쳐야 했고, 한 곳만 빠뜨려도 티가 안 납니다.

포스터를 다시 뽑는 명령
    cd video
    python poster_split.py && python poster_club.py && python poster_ticket.py \
        && python poster_neon.py && python poster_grid.py
    python poster_motion.py          # 영상까지
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PARTNER_DIR = os.path.join(os.path.dirname(HERE), 'assets', 'img', 'partners')

# ── 행사 정보 ─────────────────────────────────────────────
# 행사 이름과 형식은 다르다. 이름이 브랜드고, 형식은 무슨 파티인지 설명이다.
# 포스터는 이름을 크게, 형식을 그 밑에 작게 — 순서가 바뀌면 이름이 안 남는다.
NAME    = 'AFTER SUNSET'
NAME_KR = '애프터 선셋'
FORMAT  = 'POOL PARTY  ×  SOLO PARTY'

DATE  = '8월 29일 토요일'         # 2026-08-29 (토)
TIME  = '오후 7시 — 자정'         # 19:00 ~ 24:00
VENUE = '어나더 루프탑 라운지'    # 장소명과 주소는 줄을 나눈다 —
ADDR  = '서울특별시 서초구 양재동 122-6'   # 한 줄에 몰면 글자가 너무 작아진다
# 사전 예약제라 가격은 포스터에 넣지 않는다 (사용자 지시).
# 다시 넣을 일이 생기면 PRICE 에 값을 채우면 ENTRY 가 알아서 붙는다.
PRICE = ''
PERKS = '웰컴드링크 1잔'
# **"사전예매제" 가 아니라 "사전예매".** 사용자가 정한 표기다.
ENTRY = (f'{PRICE} · ' if PRICE else '') + f'사전예매 · {PERKS}'

# 입장 조건. **포스터에 반드시 들어간다** — 문 앞에서 실랑이가 나는 자리다.
AGE   = '미성년자 입장 불가 · 신분증 지참'
FINE  = f'{PERKS} 포함 · {AGE}'

# ── 인스타 표기 ───────────────────────────────────────────
# **사용자가 정한 형식이다. 순서와 표기를 바꾸지 말 것.**
# 날짜는 한글(8월 29일 토요일)과 영문 점 표기(2026.08.29. SAT.) 두 벌을 둔다 —
# 한글 헤드라인 판에는 한글을, 정보 블록에는 영문 점 표기를 쓴다.
# 시간 구간은 **물결표(~)** 를 쓴다. 다른 자산의 en dash 규칙보다 이 지시가 우선한다.
DATE_EN  = '2026.08.29. SAT.'
# 사용자가 정한 표기 그대로. 19시는 이미 오후라 PM 이 겹치지만 지시를 따른다.
TIME_EN  = 'PM 19:00 ~ CLOSE AM 12:00'
VENUE_IG = '@another.lounge._'          # 장소 인스타 계정
ENTRY_EN = '사전예매 + Welcome Drink'

# 포스터 정보 블록. 라벨이 빈 줄은 헤드(날짜)라 크게 찍는다.
# 장소는 **인스타 계정이 아니라 주소**로 (사용자 지시). 계정은 아래 VENUE_IG 에
# 남겨 뒀지만 포스터에는 안 쓴다 — 처음 오는 사람은 계정이 아니라 주소로 찾아온다.
# ── 모집 차수 ─────────────────────────────────────────────
# 사전예약제라 한 번에 다 열지 않고 나눠 받는다. **여기 숫자만 고치면**
# 현황 판(poster_wave.py)과 캡션이 같이 따라온다 — 두 곳에 적으면 어긋난다.
#   (이름, 정원, 마감 여부)
WAVES = [('1차', 18, True),
         ('2차', 20, False),
         ('3차', 20, False)]
CAP = sum(n for _, n, _ in WAVES)                    # 58
DONE = sum(n for _, n, d in WAVES if d)              # 마감된 인원
OPEN_WAVE = next((w for w in WAVES if not w[2]), None)   # 지금 받는 차수

# 성비. **밖으로 내보낼지는 따로 정한다** — 예전에 성비 문구를 한 번 뺐다.
# 운영용 숫자로만 두고, 판·캡션에 넣을 때는 SHOW_RATIO 를 켠다.
RATIO = '남녀 반반'
SHOW_RATIO = False


# 애프터파티 — 본 행사가 끝나고 이어지는 자리. 협업 브랜드인 에이스에서 한다
AFTER = 'ACE 힙합존  ·  8/29(토)'

# 장내 규칙. **라벨을 안 붙이고 잔글씨 한 줄로 둔다** — 표의 한 줄로 넣으면
# 날짜·장소와 같은 무게가 되는데, 이건 읽어야 하는 정보가 아니라 걸어 두는 단서다.
# 줄이 늘어도 여기 이어 붙인다. 규칙마다 한 줄씩 주면 발치가 안내문이 된다.
RULES = '실내 흡연 금지  ·  클럽에 맞지 않는 복장이나 내부 상황에 따라 입장이 불가할 수 있습니다'

INFO = [('',       DATE_EN),
        ('OPEN',   TIME_EN),
        ('VENUE',  f'{VENUE}   {ADDR}'),
        ('ENTRY',  ENTRY_EN),
        ('AFTER',  AFTER),
        ('NOTICE', AGE)]

# 포스터에 들어가는 유일한 카피. **한 줄이면 카피고 네 줄이면 광고 문구다.**
# 사용자가 준 소개글에서 사실만 남겼다 — 칵테일은 아직 확정이 아니라 뺐다.
TAGLINE = '혼자 와도 어색하지 않은 밤'

HANDLE = '@BLACKOUTCREW_OFFICIAL'
NOTE   = '예약 · 문의는 DM'
# **사전예매라고만 적으면 어디서 하는지가 없다.** 상세 안내와 신청은 캡션·구글폼으로
# 가므로, 포스터에는 **거기로 가는 길** 한 줄만 있으면 된다.
RESERVE = '예약 · 프로필 링크'
SITE   = 'BLACKOUTSOUND.COM'

# ── 타임테이블 (시작, 끝, 이름) ────────────────────────────
# 솔로파티는 디제잉이 아니라 프로그램이라 SOLO 로 표시가 갈린다.
TIMETABLE = [
    ('19:00', '19:30', 'TS'),
    ('19:30', '20:00', 'LYNN'),
    ('20:00', '20:30', 'V'),
    ('20:30', '21:00', 'CHIPS'),
    ('21:00', '21:30', 'HEIDY'),
    ('21:30', '23:00', 'SOLO PARTY'),
    ('23:00', '23:30', 'DEMIC'),
    ('23:30', '24:00', 'AROS'),
]

# 라인업 — 타임테이블에서 뽑는다. 따로 적으면 둘이 어긋난다.
PROGRAM = {'SOLO PARTY'}          # DJ 가 아니라 프로그램. 타임테이블에서 색을 가른다
LINEUP = [n for _, _, n in TIMETABLE if n not in PROGRAM]
LINEUP_STR = ' · '.join(LINEUP)

# ── 협업 브랜드 ───────────────────────────────────────────
# assets/img/partners/ 에 파일을 넣으면 자동으로 들어간다. 없으면 그냥 건너뛴다.
# 파일명은 아래와 정확히 같아야 한다.
# 지금은 로고를 안 쓴다. 이름만 한 줄로 넣는다(아래 PARTNER_NAMES).
# 다시 로고로 갈 일이 생기면 파일명을 여기 채우면 된다 — 그리는 코드는 살아 있다.
PARTNERS = []

# 협업 브랜드 이름. 로고를 섞으면 글자 붙은 것과 심볼만 있는 것이 따로 놀아서
# 전부 이름으로 통일했다.
PARTNER_NAMES = ['CLUB ACE SEOUL', 'Z SPOT LOUNGE', 'SPACE SEOUL', 'ANOTHER LOUNGE']
PARTNERS_STR  = ' · '.join(PARTNER_NAMES)


def partner_paths():
    """실제로 있는 로고만 돌려준다."""
    return [p for p in (os.path.join(PARTNER_DIR, f) for f in PARTNERS)
            if os.path.exists(p)]
