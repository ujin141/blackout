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
PARTNERS = ['club-ace.png', 'z-spot.png', 'space-seoul.png']

# 로고 대신 이름만 넣을 곳. 어나더 라운지는 심볼만 있는 로고라
# 다른 로고(글자가 붙은 것)들과 나란히 두면 무엇인지 안 읽힌다.
# 게다가 행사 장소라 VENUE 행에 이미 이름이 나온다 — 이름으로 통일한다.
PARTNER_NAMES = ['어나더 라운지']


def partner_paths():
    """실제로 있는 로고만 돌려준다."""
    return [p for p in (os.path.join(PARTNER_DIR, f) for f in PARTNERS)
            if os.path.exists(p)]
