# BLACKOUT CREW — 랜딩페이지

서울 기반 DJ 크루 BLACKOUT의 원페이지 사이트. 한국어 기본, 우측 상단에서 EN 전환.

## 실행

```bash
python -m http.server 5180
```

브라우저에서 `http://localhost:5180` 열기. 빌드 과정 없음 — HTML/CSS/JS 파일만 있으면 어디든 올라갑니다.

## 배포

**https://www.blackoutsound.com** — Vercel이 GitHub `main` 브랜치를 보고 있어서, 푸시하면 1~2분 안에 자동으로 반영됩니다.

도메인(가비아)은 이미 Vercel을 가리키고 있습니다. DNS를 건드릴 일은 없습니다.

### 링크 미리보기(카카오톡 등)가 안 나올 때

- 카카오톡은 미리보기를 한 번 읽으면 캐시합니다. 예전에 공유한 적이 있으면 [카카오 디버거](https://developers.kakao.com/tool/debugger/sharing)에서 캐시를 초기화하거나, 주소 뒤에 `?v=2`를 붙여 새 주소로 공유하세요.
- 미리보기에 쓰는 이미지는 `assets/img/og-image.png`이고, `video/make_og.py`로 다시 만들 수 있습니다.

## 자주 바꿀 것들

| 무엇 | 어디 |
|---|---|
| 인스타 계정 / 이메일 | `assets/js/main.js` 맨 위 `CONFIG` |
| **멤버 소개** | `assets/js/members.js` |
| 모든 문구 (한/영) | `assets/js/i18n.js` |
| 색·간격·크기 | `assets/css/styles.css` 맨 위 `:root` |

## 멤버 추가하기

`assets/js/members.js`의 `MEMBERS` 배열에 한 명씩 넣으면 됩니다.

```js
const MEMBERS = [
  {
    name: 'RIN',
    role: { ko: 'DJ / 레지던트', en: 'DJ / Resident' },
    bio:  { ko: '테크노, 새벽 4시 이후를 담당.', en: 'Techno. Everything after 4am.' },
    career: { ko: ['클럽 A', '클럽 B'], en: ['Club A', 'Club B'] },   // 태그로 표시
    instagram: 'rin_blackout',                    // @ 빼고
    soundcloud: 'rin-blackout',                   // 없으면 ''
    cutout: 'assets/img/members/rin.webp',        // 누끼 — 무대 조명 위에 인물만
    photo: ''                                     // 일반 사진(카드 꽉 채움)
  },
];
```

- `cutout`(배경 투명 PNG/WebP)을 쓰면 뒤에 무대 조명이 자동 생성되고 그 위에 인물만 서 있게 됩니다. AROS가 이 방식입니다.
- 누끼 만들기: `python -c "from rembg import remove; from PIL import Image; Image.open('원본.jpg').save('x.png')"` 대신, 사진 주시면 제가 따드리는 게 빠릅니다.
- `photo`는 카드를 꽉 채우는 일반 사진입니다. 둘 다 비우면 조명 실루엣이 자동으로 들어갑니다(멤버마다 다르게).
- `MEMBER_SLOTS` 숫자만큼 자리를 만들고, 등록된 멤버보다 남는 칸은 "모집 중"으로 표시되며 누르면 지원서가 열립니다. 모집 칸을 없애려면 `MEMBER_SLOTS = 0`.

지원서 폼은 작성 내용을 메일 앱으로 넘깁니다(`CONFIG.email`로 수신). 폼을 서버로 받고 싶으면 `main.js`의 `apply()` 안 `window.location.href = href` 부분만 교체하면 됩니다.

## 갤러리에 진짜 사진·영상 넣기

지금 갤러리 8칸은 공연 사진이 없어서 조명·크라우드 실루엣을 코드로 그려 넣은 것입니다. 실제 사진이 생기면 `index.html`의 해당 `<figure class="tile">` 안에 이미지나 영상을 넣기만 하면 그림 대신 그게 표시됩니다.

```html
<figure class="tile tile--hero" data-reveal data-art="beams">
  <img src="assets/img/night-01.jpg" alt="" />
  <figcaption><b data-i18n="gal.1t">메인 플로어</b><span data-i18n="gal.1s">서울</span></figcaption>
</figure>
```

영상은 `<video src="..." autoplay muted loop playsinline></video>` 로 넣으면 됩니다. 흑백 처리·확대 효과는 자동 적용됩니다.

## 히어로 로고 (3D)

가운데 로고는 이미지 한 장이 아니라 **엠블럼 / 글자 / 광원**을 층으로 쌓아 3D 공간에 세운 것입니다. 마우스를 올리면 커서 쪽으로 기울고, 엠블럼이 글자보다 앞으로 튀어나오며(시차), 커서 위치에 금속 반사광이 생기고, 뒤쪽 블룸과 바닥 조명이 함께 밝아집니다. 마우스를 올리는 순간 전원이 튀듯 한 번 깜빡입니다.

세기 조절은 `assets/css/styles.css`의 `.logo3d` 블록과 `assets/js/main.js`의 `logo3d()` 안 `MAX`(기울기 각도) 값으로 합니다. 층 위치(`16.97%`, `87.32%` 등)는 원본 로고에서 계산한 값이라 건드리지 마세요.

## 로고 파일

| 파일 | 용도 |
|---|---|
| `assets/img/logo-original.png` | 원본 (검은 배경 포함) |
| `assets/img/logo-lockup.png` | 엠블럼 + BLACKOUT + CREW, 배경 투명 — 히어로/푸터 |
| `assets/img/logo-mark.png` | 엠블럼만 |
| `assets/img/logo-blackout.png` | 글자만 |
| `assets/img/favicon.png` / `favicon-32.png` | 브라우저 탭 아이콘 (검정 타일 + 흰 엠블럼) |
| `assets/img/apple-touch-icon.png` | 폰 홈화면 아이콘 |

원본에서 잘라 배경을 투명하게 뺀 것이라 어떤 배경에도 올릴 수 있습니다.
