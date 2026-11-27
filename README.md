# 로판ai영화 (Ai-drama)

로맨스 판타지 **AI 드라마·웹툰 제작 자료집**.

> **이 레포가 원본이다.** claude.ai 프로젝트 문서와 통합 자료집은 이 레포의 사본이며, 다르면 레포가 맞다. 작업 순서는 [CLAUDE.md](CLAUDE.md).
 여러 작품을 함께 관리할 수 있도록 공통 규칙과 작품별 문서를 나눠 두었다.

- 통합 자료집 (claude.ai): https://claude.ai/artifact/KnEAL5qqyTcteDdstdFyxC
- 레포 안 열람 파일: [`site/index.html`](site/index.html) — 브라우저로 열면 같은 화면 (단, 'Claude로 시나리오 작성' 버튼은 claude.ai 안에서만 동작)
- 현재 구조 버전: **v3.0** · 시나리오 작성 편집기 **v2.0**

## 폴더 구조

```
docs/
├─ 00_구조_안내.md              구조, 메뉴, 새 작품 추가 방법, 버전 기록
├─ 공통/                        모든 작품에 쓰는 규칙·자료
│  ├─ 01_기본_규칙.md
│  ├─ 02_드라마웹툰_핵심6.md
│  ├─ 03_AI캐릭터_핵심6.md
│  ├─ 04_디자인_의상_공통자료.md
│  ├─ 05_요구사항_목록.md
│  ├─ 06_제작_참고자료_오픈소스.md
│  └─ 07_시장조사.md
├─ 작품/
│  ├─ _템플릿/                  새 작품 시작용 양식
│  └─ 01_그믐과_서리/           작품 1: 설정, 디자인
└─ 인수인계/                    작업 이어받기용 현황·기록
tools/
├─ build.py                     문서 → site/index.html 빌드
├─ hub.html                     통합 자료집 골격 (햄버거 메뉴 3단계)
├─ editor.html                  시나리오 작성 편집기 부품
└─ presets/<작품>.json           작품 입력값 + 분위기·톤(mood)
site/index.html                 빌드 결과 (통합 자료집)
save.sh                         전체 변경분 커밋·푸시
```

## 빌드

```bash
pip install markdown
python3 tools/build.py      # → site/index.html
```

## 새 작품 추가
1. `docs/작품/_템플릿/` 두 파일을 `docs/작품/NN_작품명/` 으로 복사해 채운다.
2. `tools/presets/NN_작품명.json` 을 만든다 (작품 입력값 + mood).
3. `tools/build.py` 의 `WORKS` 에 한 줄 추가.
4. 빌드 후 커밋.

## 커밋

```bash
./save.sh "커밋 메시지"     # 전체 변경분을 현재 브랜치에 커밋·푸시
```
