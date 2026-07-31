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
    name: 'AKILL',
    role: { ko: 'DJ / 레지던트', en: 'DJ / Resident' },
    bio: {
      ko: '대학 일일호프에서 시작해 클럽 타임 디제이로 현장을 쌓았습니다. 지금은 드래곤시티 풀파티 상주 디제이로 섭니다.',
      en: 'Started on college one-day bar nights and worked up through club time slots. Now resident DJ at the Dragon City pool party.'
    },
    career: {
      ko: ['드래곤시티 풀파티 상주', '이태원 더서울', '의정부 아레나2 클럽', '커튼클럽', '문 라운지', '파티팀'],
      en: ['Dragon City pool party (resident)', 'The Seoul, Itaewon', 'Arena2, Uijeongbu', 'Curtain Club', 'Moon Lounge', 'Party team']
    },
    instagram: 'dj_aki1l',
    soundcloud: '',
    cutout: 'assets/img/members/akill-cutout.webp',
    photo: ''
  }
];

/* 멤버 수가 이 숫자보다 적으면 남는 칸은 "모집 중"으로 표시됩니다. 0이면 표시 안 함. */
const MEMBER_SLOTS = 6;
