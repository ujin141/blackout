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
DATE  = '8월 29일 토요일'         # 2026-08-29 (토)
TIME  = '오후 7시 — 자정'         # 19:00 ~ 24:00
VENUE = '루프탑 어나더 라운지'    # 장소명과 주소는 줄을 나눈다 —
ADDR  = '서울특별시 서초구 양재동 122-6'   # 한 줄에 몰면 글자가 너무 작아진다
# 사전 예약제라 가격은 포스터에 넣지 않는다 (사용자 지시).
# 다시 넣을 일이 생기면 PRICE 에 값을 채우면 ENTRY 가 알아서 붙는다.
PRICE = ''
PERKS = '성비 1:1 · 웰컴드링크 1잔'
ENTRY = (f'{PRICE} · ' if PRICE else '') + f'사전 예약제 · {PERKS}'
FINE  = f'{PERKS} 포함 · 사전 예약자 우선 입장'

HANDLE = '@BLACKOUTCREW_OFFICIAL'
NOTE   = '예약 · 문의는 DM'
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
LINEUP = [n for _, _, n in TIMETABLE if n != 'SOLO PARTY']
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
