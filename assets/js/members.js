/* ============================================================
   BLACKOUT — 크루 멤버
   여기만 고치면 멤버 섹션이 바뀝니다.

   {
     name:      'AROS',                            // 활동명
     role:      { ko: 'DJ', en: 'DJ' },
     genres:    { ko: ['하우스', '테크노'], en: ['House', 'Techno'] },  // 이름 아래 한 줄
     bio:       { ko: '한 줄 소개', en: 'one line' },
     career:    { ko: ['클럽 A', '클럽 B'], en: [...] },   // 없으면 생략
     instagram: 'handle',                          // @ 없이 (없으면 '')
     soundcloud:'handle',                          // soundcloud.com/handle (없으면 '')
     cutout:    'assets/img/members/x.webp',       // 누끼(배경 투명) — 조명 위에 인물만
     photo:     ''                                 // 일반 사진(카드 꽉 채움). cutout 쓰면 비워둠
   }
   ============================================================ */

const MEMBERS = [
  {
    name: 'LYNN',
    role: { ko: 'DJ', en: 'DJ' },
    genres: {
      ko: ['EDM', '테크하우스', '하우스', '미니멀', '미니멀 바운스', '힙합'],
      en: ['EDM', 'Tech House', 'House', 'Minimal', 'Minimal Bounce', 'Hip-hop']
    },
    bio: {
      ko: '장르를 넘나들며 그날 플로어에 맞춰 갑니다.',
      en: 'Moves between genres and plays to whatever the room needs that night.'
    },
    instagram: '_1.ynn___',
    soundcloud: 'jfjmq6ahybym',
    cutout: 'assets/img/members/lynn-cutout.webp',
    photo: ''
  },
  {
    name: 'AROS',
    role: { ko: 'DJ', en: 'DJ' },
    genres: {
      ko: ['EDM', '바운스', '하우스', '하드'],
      en: ['EDM', 'Bounce', 'House', 'Hard']
    },
    bio: {
      ko: '중학교 때 Alan Walker로 전자음악에 빠졌고, 지금은 무대 위에서 그 에너지를 그대로 돌려줍니다.',
      en: 'Fell for electronic music through Alan Walker as a kid, now gives that energy back on stage.'
    },
    career: {
      ko: ['상하이 클럽 MAX', '클럽 234', '성남 국빈관 나이트클럽'],
      en: ['Club MAX, Shanghai', 'Club 234, Korea', 'Kukbinkwan, Seongnam']
    },
    instagram: 'arosjin__2000_12_23',
    soundcloud: 'jin-aros',
    cutout: 'assets/img/members/aros-cutout.webp',
    photo: ''
  },
  {
    name: 'TS',
    role: { ko: 'DJ', en: 'DJ' },
    genres: {
      ko: ['EDM', '딥 하우스', '개러지 하우스', 'K-POP', '시티팝'],
      en: ['EDM', 'Deep House', 'Garage House', 'K-Pop', 'City Pop']
    },
    bio: {
      ko: '업장 오픈덱에서 시작해 학원 파티와 워크샵, 빠지까지. 생일 파티 초청 DJ로도 섭니다.',
      en: 'Came up through open decks. Plays school parties, workshops, pool villas and private events.'
    },
    career: {
      ko: ['업장 오픈덱', 'DJ 학원 수강생 파티', '학원 워크샵', '가평 빠지'],
      en: ['Open decks', 'DJ school parties', 'Academy workshops', 'Gapyeong pool villa']
    },
    instagram: '_kim_jung_hoon_',
    soundcloud: '',
    cutout: 'assets/img/members/ts-cutout.webp',
    photo: ''
  },
  {
    name: 'DEMIC',
    role: { ko: 'DJ', en: 'DJ' },
    bio: {
      ko: '고등학생 때 TV로 본 Deadmau5 무대를 보고 시작했습니다. 대학 축제부터 클럽, 호텔 풀파티까지 무대를 가리지 않습니다.',
      en: 'Started after seeing a Deadmau5 set on TV. Plays anything — university festivals, clubs, hotel pool parties.'
    },
    career: {
      ko: ['포포인츠 바이 쉐라톤 수원 풀파티', '강남 THE FATE LOUNGE', '홍대 TASK FORCE', '압구정 VASSMENT ONE', '신촌 ESCAPE 파티 디렉터', '청담 MOHENIC HOUSE DJ 토너먼트 2위'],
      en: ['Four Points by Sheraton Suwon (pool party)', 'The Fate Lounge, Gangnam', 'Task Force, Hongdae', 'Vassment One, Apgujeong', 'Escape, Sinchon (party director)', '2nd — Mohenic House DJ Tournament']
    },
    instagram: 'demic.10.16',
    soundcloud: '',
    cutout: 'assets/img/members/demic-cutout.webp',
    photo: ''
  },
  {
    name: 'XANTHIC',
    role: { ko: 'DJ', en: 'DJ' },
    genres: {
      ko: ['EDM', '테크하우스', '힙합'],
      en: ['EDM', 'Tech House', 'Hip-hop']
    },
    bio: {
      ko: '다중다색의 사운드, 경계 없는 플레이. 매 순간 다른 플로어를 만듭니다.',
      en: 'Many colours, no borders. Builds a different floor every time.'
    },
    instagram: 'dj_xanthic',
    soundcloud: '',
    cutout: 'assets/img/members/xanthic-cutout.webp',
    photo: ''
  },
  {
    name: '1UCKY',
    role: { ko: 'DJ', en: 'DJ' },
    genres: {
      ko: ['덥스텝', '베이스하우스', '테크하우스'],
      en: ['Dubstep', 'Bass House', 'Tech House']
    },
    bio: {
      ko: '베이스 위주로 갑니다. 덥스텝부터 테크하우스까지.',
      en: 'Bass first. Dubstep through tech house.'
    },
    career: {
      ko: ['강남 ZSPOT EDM 파티', '이태원 UNION 안과밖',
           '성수동 XIMXIM Challengers Quartet', '강남 ZSPOT 오픈덱 파티',
           '서울 커뮤니티라디오 촬영'],
      en: ['Zspot, Gangnam (EDM party)', 'UNION, Itaewon — Inside Out',
           'Ximxim, Seongsu — Challengers Quartet', 'Zspot, Gangnam (open deck)',
           'Seoul Community Radio (shoot)']
    },
    // **원본이 571px 이라 다른 누끼보다 작다.** 카드가 레티나에서 728px 를
    // 쓰므로 살짝 올려 쓰는 셈이다 — 더 큰 원본이 생기면 다시 뽑을 것.
    instagram: '1uckym1n4_',
    soundcloud: '',
    cutout: 'assets/img/members/1ucky-cutout.webp',
    photo: ''
  },
];

/* 멤버 수가 이 숫자보다 적으면 남는 칸은 "모집 중"으로 표시됩니다. 0이면 표시 안 함. */
const MEMBER_SLOTS = 6;
