/* ============================================================
   BLACKOUT — 크루 멤버
   여기만 고치면 멤버 섹션이 바뀝니다.

   {
     name:      'AROS',                            // 활동명
     role:      { ko: 'DJ', en: 'DJ' },
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
    bio: {
      ko: '중학교 때 Alan Walker로 전자음악에 빠졌고, 지금은 무대 위에서 그 에너지를 그대로 돌려줍니다. EDM · 바운스 · 하우스 · 하드.',
      en: 'Fell for electronic music through Alan Walker as a kid, now gives that energy back on stage. EDM · bounce · house · hard.'
    },
    career: {
      ko: ['상하이 클럽 MAX', '클럽 234', '성남 국빈관 나이트클럽'],
      en: ['Club MAX, Shanghai', 'Club 234, Korea', 'Kukbinkwan, Seongnam']
    },
    instagram: 'arosjin__2000_12_23',
    soundcloud: 'jin-aros',
    cutout: 'assets/img/members/aros-cutout.webp',
    photo: ''
  }
];

/* 멤버 수가 이 숫자보다 적으면 남는 칸은 "모집 중"으로 표시됩니다. 0이면 표시 안 함. */
const MEMBER_SLOTS = 3;
