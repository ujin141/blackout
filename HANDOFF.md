# 다른 컴퓨터로 옮기기

이 저장소만 클론하면 **사이트·제안서·영상 스크립트는 전부 따라옵니다.**
아래는 클론으로 따라오지 **않는 것**과, 환경을 맞추는 방법입니다.

---

## 1. 클론

```bash
git clone https://github.com/ujin141/blackout.git
cd blackout
python -m http.server 5180
```

`http://localhost:5180` 을 열면 사이트가 그대로 뜹니다. 빌드 과정 없습니다.

---

## 2. 저장소에 **없는** 것

`.gitignore`로 빠져 있습니다. 없어도 사이트는 정상 동작합니다.

| 빠진 것 | 왜 | 어떻게 |
|---|---|---|
| `AROS/` `Lynn/` `TS/` `V/` — 멤버 원본 사진 (약 2MB) | 개인정보(프로필 카드에 전화번호)가 있어 공개 저장소에 올리지 않음 | **USB·드라이브로 직접 옮기세요.** 누끼 결과물(`assets/img/members/*.webp`)은 저장소에 있으므로, 사진을 다시 따야 할 때만 필요합니다 |
| `video/out/` — 렌더된 영상·음원·카드뉴스 (약 110MB) | 용량이 크고 스크립트로 다시 만들 수 있음 | 아래 명령으로 재생성 (아래 4번) |
| `proposal/*.pdf` `proposal2/*.pdf` | HTML에서 다시 뽑을 수 있음 | 아래 5번 |

> 완성본(영상·PDF)을 바로 쓰고 싶으면 재생성이 제일 확실합니다. 렌더 결과는 매번 동일합니다.

---

## 3. 필요한 프로그램

```bash
pip install numpy scipy opencv-python pillow rembg onnxruntime
```

| 도구 | 용도 | 없으면 |
|---|---|---|
| **Python 3.10+** | 전부 | 필수 |
| **ffmpeg** (PATH에 등록) | 영상 인코딩 | 영상만 못 만듦 |
| **Google Chrome** | 제안서 PDF 출력 | PDF만 못 뽑음 |
| `rembg` | 새 멤버 사진 누끼 | 기존 멤버는 이미 따둠 |

### 맥·리눅스 한글 폰트

`video/fonts.py`가 OS를 보고 알아서 찾습니다. 다만 **맥은 Pretendard를 설치하는 편이 좋습니다** — 없으면 Apple SD Gothic으로 대체되는데 볼드가 없어 제목이 얇게 나옵니다.

[Pretendard 내려받기](https://github.com/orioncactus/pretendard/releases) → `Pretendard-Regular.otf`와 `Pretendard-Bold.otf`를 `~/Library/Fonts`에 넣으면 끝입니다.

영문 폰트(Michroma)는 `video/assets/`에 들어 있어 어디서나 동일합니다.

### 윈도우에서 한글 깨질 때

```bash
set PYTHONIOENCODING=utf-8
```

---

## 4. 영상 다시 만들기

```bash
cd video
python audio.py       && python make.py        # 티저 28초
python audio_open.py  && python opening.py     # 오프닝 1 (30초)
python audio_open2.py && python opening2.py    # 오프닝 2 (29초, 140BPM 하드테크노)
python cards.py aros lynn v ts                 # 인스타 카드뉴스
python feed.py                                 # 피드 3분할 세트
python make_og.py                              # 링크 미리보기 카드
```

전부 `video/out/`에 저장됩니다. 한 편에 몇 분 걸립니다.
`python make.py 15.0 16.2` 처럼 시간 두 개를 주면 그 구간만 PNG로 뽑아 빠르게 확인합니다.

음악·효과음까지 코드로 합성해서 저작권 이슈가 없습니다.

---

## 5. 제안서 PDF 다시 뽑기

`proposal/` = 웨이비 스튜디오(18p), `proposal2/` = 디제이코리아(15p).
스타일시트는 `proposal/style.css` 하나를 공유합니다.

```bash
chrome --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=25000 --print-to-pdf="BLACKOUT_제안서.pdf" "file:///절대경로/proposal/index.html"
```

윈도우면 `"C:\Program Files\Google\Chrome\Application\chrome.exe"`를 직접 지정하세요.
**뽑은 뒤 페이지 넘침을 반드시 확인합니다** — 브라우저 콘솔에서:

```js
[...document.querySelectorAll('.page')].map((p,i)=>({p:i+1, over:p.scrollHeight-p.clientHeight})).filter(x=>x.over>2)
```

빈 배열이면 정상입니다.

---

## 6. 배포

**https://www.blackoutsound.com** — Vercel이 GitHub `main`을 보고 있어서 **푸시하면 1~2분 안에 자동 반영**됩니다.
GitHub Pages는 쓰지 않습니다. 도메인(가비아)은 이미 Vercel을 가리키고 있으니 DNS는 건드릴 일이 없습니다.

---

## 7. 작업 규칙

이 프로젝트에서 굳어진 것들입니다.

- **AI 말투 금지.** 인스타 캡션·제안서 문구는 사람이 쓴 것처럼. "~하실 수 있습니다", "함께 만들어가요" 같은 상투구 배제.
- **검증 안 된 사실을 단정하지 않는다.** 특히 제안서에서 상대 회사 정보(취급 브랜드, 커리큘럼, 유동인구)는 확인된 것만 씁니다. 숫자는 전부 `제안`·`가정`으로 표기.
- **멤버를 추가하면 네 곳을 같이 고친다** — `assets/js/members.js`(화면), `index.html`의 JSON-LD와 `<noscript>` 목록(크롤러), `llms.txt`. 화면은 JS로 그려서 크롤러가 못 봅니다.
- **멤버 사진 크기는 전원 동일.** `styles.css`의 `.member__photo img.member__cut { height: 82% }` 한 곳으로 관리합니다. 멤버별 `fit` 값은 폐지됐습니다(README의 `fit` 설명은 옛날 내용).
- **내비게이션은 한국어 모드에서도 영문 유지** (브랜드 톤).
- **로고는 원본 PNG를 자른 것.** SVG로 다시 그리지 마세요 — 폰트가 달라집니다.

---

## 8. 현재 상태 (2026-08-01)

**완료** — 랜딩페이지(한/영, 3D 로고), 멤버 4명(V·LYNN·AROS·TS), SEO/AEO, Vercel 배포, 영상 3편, 카드뉴스 4명분 + 피드 3분할, 제안서 2건.

**열려 있는 것**

- TS 사운드클라우드 주소 없음
- 디제이코리아 제안서 중 2개 문장이 미검증 추정 — 용산 쇼룸 유동인구, CAMPUS 커리큘럼 범위. 미팅에서 확인 후 조정 권장
