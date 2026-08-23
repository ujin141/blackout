# BLACKOUT CREW

서울 기반 DJ 크루 BLACKOUT의 브랜드 자산 저장소. 랜딩페이지 · 숏폼 영상 · 인스타 콘텐츠 · 협업 제안서를 한 곳에서 만듭니다.
사용자는 **우진**(크루 운영). 한국어로 대화합니다.

빌드 도구 없습니다. HTML/CSS/JS는 그대로 서빙하고, 영상·이미지·PDF는 파이썬 스크립트로 생성합니다.

**작업 히스토리와 결정 배경은 [CONTEXT.md](CONTEXT.md)에 있습니다. 새 작업을 시작하기 전에 읽으세요.**
환경 설정·이전은 [HANDOFF.md](HANDOFF.md), 사용법은 [README.md](README.md).

---

## 지켜야 할 것

**말투 — AI 티가 나면 실패입니다.**
인스타 캡션·제안서·사이트 문구 모두 사람이 쓴 것처럼. "~하실 수 있습니다", "함께 만들어가요", "여러분의", 이모지 남발, 세 개씩 늘어놓는 병렬 구조 금지. 짧고 건조하게, 클럽 씬 사람이 쓰는 어투로.

**검증 안 된 사실을 단정하지 않습니다.**
특히 제안서에서 상대 회사 정보(취급 브랜드, 커리큘럼, 유동인구, 지점 성격)는 확인된 것만 씁니다. 추정은 "제안"·"가정"으로 명시. 과거에 이걸로 두 번 수정이 있었습니다(CONTEXT.md 참고).

**행사 정보는 `video/event.py` 한 곳에서만 고칩니다.** 날짜·시간·타임테이블·가격이 전부 거기 있고 포스터 다섯 시안이 가져다 씁니다. 시안 파일 안에 값을 다시 적지 마세요 — 예전에 그렇게 해서 날짜 하나 바꿀 때마다 다섯 군데를 고쳐야 했습니다.

**멤버를 추가·수정하면 네 곳을 같이 고칩니다.**
`assets/js/members.js`(화면) → `index.html`의 JSON-LD → `index.html`의 `<noscript>` 목록 → `llms.txt`.
화면은 JS로 그려서 크롤러가 못 보기 때문에 나머지 세 곳이 필요합니다.

**멤버 사진 크기는 전원 동일합니다.**
`styles.css`의 `.member__photo img.member__cut { height: 82% }` 한 곳으로만 관리. 멤버별 크기 값(`fit`)은 폐지됐습니다.

**내비게이션은 한국어 모드에서도 영문을 유지합니다** (브랜드 톤). `i18n.js`의 ko 블록에 영어가 들어 있는 건 의도된 것입니다.

**흑백 규칙에 예외가 하나 있습니다** — `video/poster_loud.py`(행사 모객용 컬러 포스터). 사용자가 직접 요청한 것이고, 나머지 자산은 전부 흑백을 지킵니다.

**영상 소재는 실제 출력 해상도를 먼저 재세요.** `ffprobe` 의 width/height 는
저장된 방향이지 화면에 나오는 방향이 아닙니다. 숏폼 원본 아홉 개가 전부
회전 90도라 실제로는 2160×3840(세로)인데, 3840×2160(가로)인 줄 알고 크롭을
걸어 **세로 프레임 한가운데 조각만 쓰고 있었습니다.** 얼굴이 잘리고 사람이
적어 보이던 게 전부 여기서 왔습니다.

**로고를 SVG로 다시 그리지 마세요.** 원본 PNG를 잘라 쓴 것이고, 재현하면 폰트가 달라집니다.

**사이트는 열려 있습니다.** `vercel.json`은 지웠습니다. 다시 막으려면 그 파일을 만들어 모든 요청을 `maintenance.html`(파일은 그대로 있음)로 보내면 됩니다.

**푸시하면 바로 공개됩니다.** Vercel이 `main`을 보고 있어 1~2분 내 https://www.blackoutsound.com 에 반영됩니다.

---

## 명령어 (`.claude/skills/`)

이 저장소 전용입니다. 우리 규칙과 숫자가 박혀 있어서 범용 도구보다 낫습니다.

```
/caption        캡션 — 판마다 길이와 첫 줄이 다르다. 이미 쓴 것과 안 겹치게
/ad-check       광고 점검 — 손익분기·CAC 를 event.py 값으로 다시 계산
/creative       새 소재의 각을 정한다. 만들 필요가 있는지부터 본다
/distribute     0원 채널이 먼저다. 뭐가 나갔는지 묻는다

/board-review   그림 판(포스터·커버·카드) — **이미지를 열어서** 본다
/video-review   영상 — 프레임을 뽑아서 본다. 박·컷·자막·안전영역
/web-review     사이트 — **눈으로 보지 말고 브라우저에서 재라**
```

**부르라고 하지 않아도 알아서 씁니다.** 아래에 걸리면 먼저 그 명령어를
읽고 시작하세요 — 우진이 `/caption` 이라고 안 쳐도 마찬가지입니다.

| 이런 말이 오면 | 먼저 읽을 것 |
|---|---|
| 캡션 · 글 · 문구 · 멘트 · "올릴 글" · 스레드 · 오픈챗 · X | `/caption` |
| 광고 · 메타 · 예산 · 타겟 · 세팅 · CAC · 손익분기 | `/ad-check` |
| 새 릴스 · 스토리 · 포스터 · 커버 · 소재 · 썸네일 | `/creative` → 만든 뒤 점검 |
| 올린다 · 배포 · 어디에 · 홍보 · 제안 · DM | `/distribute` |
| 포스터·커버·카드를 만들었거나 고쳤을 때 | `/board-review` |
| 영상을 만들었거나 고쳤을 때 | `/video-review` |
| 사이트·팝업·CSS 를 고쳤을 때 | `/web-review` |

**만들고 나서 점검을 건너뛰지 않습니다.** 이 저장소에서 난 실수는 대부분
"코드는 맞는데 눈으로 보면 틀린" 것이었고, 점검 문서에 그게 순서대로
적혀 있습니다.

점검 세 개에는 **이 저장소에서 실제로 났던 실수가 순서대로** 적혀 있습니다.
일반론이 아니라 우리가 틀렸던 것들입니다.

## 구조

```
index.html              랜딩페이지 (한/영, 섹션 전부 여기)
assets/js/members.js    멤버 데이터 — 사실상 유일한 데이터 소스
assets/js/i18n.js       모든 문구 (ko/en)
assets/js/main.js       CONFIG(인스타·이메일), 캔버스 아트, 3D 로고, 지원 폼
assets/css/styles.css   :root 에 디자인 토큰
video/                  영상·카드뉴스·OG 생성 스크립트
video/event.py          행사 정보 원본 — 날짜·시간·타임테이블·협업 브랜드. 시안 다섯이 여기서 가져감
video/poster_kit.py     포스터 공통 도구 (C·D·E안이 씀. A·B안은 각자 복사본)
video/fest_kit.py       페스티벌 시안 전용 도구 (G~K안)
video/members.py        멤버 데이터를 assets/js/members.js 에서 읽는다. 파이썬에 다시 적지 않는다
video/scene_kit.py      풀파티 '장면' 을 그리는 도구 (AF~AH안)
assets/img/partners/    협업 브랜드 로고 4종 — 포스터에 자동으로 들어감 (README 참고)
assets/img/stock/       배경 사진. `pool-model.jpg` 를 넣으면 장면 배경이 그걸로 바뀜
proposal/               웨이비 스튜디오 제안서 (18p)
proposal2/              디제이코리아 제안서 (15p) — style.css 는 proposal/ 것을 공유
llms.txt robots.txt sitemap.xml   AI·검색 노출
```

## 자주 쓰는 명령

```bash
python -m http.server 5180          # 사이트 미리보기

cd video
python audio.py       && python make.py       # 티저 28초
python audio_open.py  && python opening.py    # 오프닝 1
python audio_open2.py && python opening2.py   # 오프닝 2 (140BPM)
python audio_open3.py && python opening3.py   # 오프닝 3 (174BPM, wav를 읽어 그림)
python cards.py aros lynn v ts                # 인스타 카드뉴스
python feed.py                                # 피드 3분할 (1~3번)
python feed2.py                               # 이어지는 4·5번
python feed_row.py                            # 멤버 한 줄(3칸) 이어지는 세트
python audio_reel.py && python reel_word.py   # 멤버별 키워드 릴스 5편 (15초)
python make_og.py                             # 링크 미리보기 카드
python kakao_bg.py                            # 카톡 단톡방 배경
python poster_pool.py                         # 파티 포스터 (스토리용)
python poster_event.py                        # 행사 포스터 (범용)
python poster_solo.py                         # 풀파티 × 솔로파티 티저 포스터
python poster_ad.py                           # 같은 행사 판매용 포스터 (정보형)
python poster_loud.py                         # 직설 버전 — 컬러 일러스트
python poster_photo.py                        # F안 실사 물 사진 — 밤 버전 (CC0)
python band.py                                # 입장 밴드 앞면 4종 → BAND_1_GUEST_FRONT.png …
python band.py back                           # 밴드 뒷면 (로고 + BLACKOUT). 크기는 BAND_MM 에서
python coupon.py                              # 웰컴드링크 쿠폰 앞뒤 + A4 시트
#                                               칼선 90×50 · 편집 150×70 · 안전 2mm (CUT_MM/ART_MM)
python print_pack.py                          # **인쇄소에 넘길 폴더 한 방에** → out/print (PDF+TIFF+사양서)
python story_print.py                         # 쿠폰·밴드를 보여주는 인스타 스토리 판 1080×1920
python to_cmyk.py out/band                    # CMYK TIFF 만 — 잉크량 250%, 리치블랙 직접 지정
python to_pdf.py out/band_cmyk                # CMYK PDF 만 — 무손실, ICC 심음
python poster_ally.py                         # 협업 혜택 판 — ONE BAND / FOUR DOORS
python qr.py                                  # 예약·게스트 폼 QR (읽히는지 재고 뽑음)
python guest.py                               # 게스트 등록 판 — 폰 · A4 · 명함
python audio_intro.py && python intro.py      # 행사 인트로 23초 · 120BPM. 가로(행사장)·세로(인스타)
                                              #   한 방 17.0초 · 21~22.5초 시보음 카운트인 · **23.0초가 노래 첫 박**
python audio_intro2.py && python intro2.py    # 인트로 B안 — 밝은 풀파티(물속→수면). 격자는 A안과 같음
python poster_split.py                        # A안 물×클럽, 기울인 축 · 시안×마젠타
python poster_club.py                         # B안 클럽, 직각 격자 + 쌓은 타이포 · 검정×레드
python poster_ticket.py                       # C안 입장권, 유일한 밝은 판 · 파랑
python poster_neon.py                         # D안 네온 사인, 밤 느낌 최대 · 형광 초록
python poster_grid.py                         # E안 모듈 그리드, 정보 밀도 최대 · 오렌지
python poster_bill.py                         # G안 라인업 블록(톰스톤) · 순수 타이포 · 청록
python poster_sun.py                          # H안 지는 해 + 레트로 띠 · 주황
python poster_crest.py                        # I안 원형 배지 · 금색
python poster_stage.py                        # J안 무대 빔 + 관객 · 보라×자홍
python poster_stack.py                        # K안 활판 밴드 · 라임 한 줄
python poster_ripple.py                       # L안 두 물결이 만난다 · 시안×주황
python poster_float.py                        # M안 겹친 튜브 두 개 · 아쿠아×핑크
python poster_mirror.py                       # N안 혼자 왔는데 비친 건 둘 · 호박
python poster_lane.py                         # O안 수영 레인 = 타임테이블 · 라임
python poster_tag.py                          # P안 번호표 두 장 · 코랄×아쿠아
python poster_siren.py                        # Q안 경고문 · 위험 노랑×적색
python poster_heat.py                         # R안 열화상 · 자홍→주황
python poster_shred.py                        # S안 찢겨 어긋난 판 · 독성 마젠타
python poster_splash.py                       # T안 물튀김 정지 · 전기 시안
python poster_scream.py                       # U안 판을 넘치는 글자 · 형광 오렌지
python poster_venn.py                         # V안 삼중 벤 — 풀×솔로×일렉
python poster_prism.py                        # W안 세 빛이 한 점으로
python poster_misreg.py                       # X안 삼색 판 어긋남(인쇄)
python poster_mixer.py                        # Y안 믹서 3채널 다 열림
python poster_orbit.py                        # Z안 세 궤도가 한 점에서 교차
python poster_real.py                         # AA안 실사 한 장 + 한글 정보 네 줄
python poster_half.py                         # AB안 위=물 / 아래=클럽, 사진 두 장
python poster_card.py                         # AC안 사진 + 정보판 (제일 정보형)
python poster_time.py                         # AD안 타임테이블이 주인공
python poster_board.py                        # 타임테이블 판 — **브랜드 톤(흑백·은색)**
python poster_board.py story                  #   피드·스토리·정사각. 색 있는 판은 시안 비교용
python poster_ko.py                           # AE안 한글 헤드라인이 제일 큼
python poster_night.py                        # AF안 장면 + 한글 헤드라인 (그린 그림)
python poster_deck.py                         # AG안 장면 위 / 정보판 아래
python poster_dive.py                         # AH안 장면 전면 + 행사명 한 줄
python poster_crew.py                         # AI안 DJ 얼굴 판 — 누끼 일곱을 칸에 넣는다
python poster_dj.py                           # DJ 한 명짜리 판 일곱 장 (사람마다 색이 다르다)
python poster_dj.py lynn heidy                # 골라서
python poster_dj2.py                          # 같은 개인 판 B안 — 색분해·대각 띠·세로 이름
python poster_dj3.py                          # C안 — 크롬 이름·무대 빔 (강남 클럽 게스트 판)
python poster_dj4.py                          # D안 — 우진 레퍼런스(월디페) 문법. 정사각 + 흰 정보 띠
python poster_dj5.py                          # E안 — 액자를 뚫고 나온다. 해 + 잔상 + 바닥 반사
python poster_dj6.py                          # F안 — 네온 간판. 콘크리트 벽 + 젖은 바닥
python poster_dj7.py                          # G안 — 판은 흑백·은색, 사람만 컬러 (브랜드 판)
python poster_dj8.py xanthic                  # 라인업 밖 크루도 뽑힌다 — 행사 대신 크루가 들어감
python poster_dj8.py                          # H안 — 같은 사람을 크기 달리해 세 번 세운다 (우진 채택)
python poster_b2b.py                          # 백투백 판 — 둘이 같이 선다 (HEIDY × CHIPS · DEMIC × AROS)
python poster_b2b.py "HEIDY x CHIPS"          # 골라서. 세트는 event.py 의 B2B_SETS 에서 온다
#                                               피드 4:5 · 정사각 · 스토리 세 벌이 나온다
python audio_poster.py                        # 포스터 전용 BGM 다섯 곡 (릴스 곡과 안 겹침)
python poster_motion.py                       # 다섯 시안 영상 × 스토리·피드 두 사이즈 (BGM 포함, 15초)
python poster_motion.py neon grid             # 시안만 골라서
python poster_motion.py split story           # 사이즈까지 골라서
python intro_sig.py                           # 크루 시그니처 인트로 5.85초 (세로·가로)
#                                               소리를 재서 만든 판 — 4.71초가 클라이맥스
python audio_lineup.py                        # 라인업 릴스 곡 — 필터 도는 코드 + 사이드체인
python reel_lineup.py                         # 라인업 공개 릴스 20초 (곡까지 같이 만든다)
python cover_reels.py                         # 릴스 셋을 피드에서 잇는 커버 3장 (올리는 순서는 거꾸로)
python audio_sunset.py                        # 해 지는 릴스 곡 — 애시드 베이스 125BPM
python reel_sunset.py                         # 같은 원본 다른 판 — 낮에서 밤으로 (19.2초)
python reel_pool.py                           # 현장 영상 릴스 — 숏폼/ 원본을 잘라 붙인다 (14.5초)
python reel_close.py                          # 2차 마감 릴스 15초 — 현장 영상 + 자막. 숫자는 event.py 에서
python audio_cut.py && python reel_cut.py     # 현장 컷 릴스 두 편 — water(낮·물) · neon(밤·조명)
python reel_cut.py water                      #   골라서. 컷은 USED 에 없는 구간만 (assert 로 막힘)
python audio_check.py                         # **곡이 기존 곡과 겹치는지 잰다** — 음색·리듬·음정
python reel_pool.py 3                         # 3번 컷만 확인용으로
```

영상 스크립트에 시간 두 개를 주면 그 구간만 PNG로 뽑습니다 — `python make.py 15.0 16.2`.
제안서 PDF는 Chrome headless로 뽑고, **뽑은 뒤 페이지 넘침을 반드시 확인합니다**(HANDOFF.md 5번).

## 지금 열려 있는 것

- TS 사운드클라우드 주소 없음
- DEMIC 장르 미확인 — 프레스킷에 장르 표기가 없음
- 디제이코리아 제안서에 미검증 추정 2건 — 용산 쇼룸 유동인구, CAMPUS 커리큘럼 범위
- 풀파티 가격 미정 — **사전 예약제라 포스터에 안 적기로 함**. 넣을 일이 생기면 `video/event.py` 의 `PRICE` 만 채우면 됨
