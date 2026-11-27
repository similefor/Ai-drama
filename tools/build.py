"""로판ai영화 통합 자료집 빌더 (구조 v3.0)

사용법:  python3 tools/build.py
결과:    site/index.html (레포) 또는 tools/out/hub.html  → 아티팩트 한 개로 발행 (모든 작품 · 공통 자료 · 편집기 · 시장조사)

- 골격: hub.html (햄버거 메뉴 3단계: 분류 › 작품/페이지 › 세부 문서)
- 편집기: editor.html 의 본문·스크립트를 #editor 섹션으로 넣고, CSS는 #editor 안으로 한정한다.
- 새 작품: WORKS 에 한 줄 추가 + docs/작품/<코드>/ + presets/<코드>.json
- 큰 틀(문서 구조·HTML 골격)이 바뀌면 VERSION 메이저 숫자를 올린다.
"""
import markdown, re, html, json, pathlib, datetime

VERSION = "v3.0"
EDITOR_VERSION = "편집기 v2.0"
PROJECT = "로판ai영화"
ROOT = pathlib.Path(__file__).parent
# 깃허브 레포: <레포>/docs, 결과는 <레포>/site/index.html
# 프로젝트(claude/tools) 작업 폴더: tools/docs, 결과는 tools/out/hub.html
REPO = (ROOT.parent / "docs").exists()
DOCS = ROOT.parent / "docs" if REPO else ROOT / "docs"
E = html.escape

# 작품 목록 (메뉴 '작품' 아래 2단계로 나타남)
WORKS = {
    "01_그믐과_서리": {
        "title": "그믐과 서리",
        "tagline": "한국풍 퓨전 로맨스 판타지 · GL을 표방한 워맨스",
        "color": "#0e4d4a",
        "docs": [  # 3단계 메뉴 (분위기·톤은 presets mood 에서 자동 생성되어 맨 앞에 붙음)
            ("story",  "작품 설정",   "01_설정.md"),
            ("design", "작품 디자인", "02_디자인.md"),
        ],
    },
}

# 메뉴 1단계 분류 → 2단계 페이지 (id, 메뉴 이름, 원본 파일)
GROUPS = [
    ("도구", [("editor", "시나리오 작성 편집기", None)]),
    ("시장·제작 자료", [
        ("market", "시장조사", "공통/07_시장조사.md"),
        ("refs",   "제작 참고 (오픈소스)", "공통/06_제작_참고자료_오픈소스.md"),
        ("dcom",   "디자인·의상 공통자료", "공통/04_디자인_의상_공통자료.md"),
    ]),
    ("공통 규칙", [
        ("rules",  "기본 규칙", "공통/01_기본_규칙.md"),
        ("drama6", "드라마·웹툰 핵심 6", "공통/02_드라마웹툰_핵심6.md"),
        ("ai6",    "AI 캐릭터 핵심 6", "공통/03_AI캐릭터_핵심6.md"),
    ]),
    ("관리", [
        ("needs",  "요구사항 목록", "공통/05_요구사항_목록.md"),
        ("about",  "구조 안내·버전", "00_구조_안내.md"),
    ]),
]

MOOD_FIELDS = [
    ("ref_tone", "참조 톤 (색·빛)"), ("ref_camera", "참조 연출·카메라"), ("ref_works", "톤 참고 작품"),
    ("ref_costume", "참조 의상 컨셉"), ("ref_space", "참조 공간·배경"), ("ref_sound", "참조 음악·소리"),
]


def render(md_text, prefix):
    h = markdown.markdown(md_text, extensions=["tables", "sane_lists", "fenced_code"])
    h = h.replace("<table>", '<div class="scroll"><table>').replace("</table>", "</table></div>")
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    heads = []
    def h2(m):
        hid = f"{prefix}-{len(heads)}"
        heads.append((hid, re.sub("<[^>]+>", "", m.group(1))))
        return f'<h2 id="{hid}">{m.group(1)}</h2>'
    h = re.sub(r"<h2>(.*?)</h2>", h2, h)
    nav = "".join(f'<a href="#{i}">{E(t)}</a>' for i, t in heads)
    toc = f'<nav class="toc scroll">{nav}</nav>' if nav else ""
    return re.sub(r"<h1>(.*?)</h1>", lambda m: f'<h1 class="doc-title">{m.group(1)}</h1>{toc}', h, count=1)


LINKS = {}  # 문서 경로·별칭 → 섹션 id (build() 에서 채움)

def autolink(h):
    """본문 속 문서 경로·별칭을 통합 자료집 안의 메뉴 링크로 바꾼다 (기존 링크 안은 건드리지 않음)"""
    if not LINKS:
        return h
    keys = sorted(LINKS, key=len, reverse=True)
    pat = re.compile("|".join(re.escape(k) for k in keys))
    out, in_a = [], 0
    for part in re.split(r"(<[^>]+>)", h):
        if part.startswith("<"):
            if re.match(r"<a[\s>]", part): in_a += 1
            elif part.startswith("</a"): in_a = max(0, in_a - 1)
            out.append(part)
        elif in_a or not part.strip():
            out.append(part)
        else:
            out.append(pat.sub(lambda m: f'<a class="xref" href="#{LINKS[m.group(0)]}">{m.group(0)}</a>', part))
    return "".join(out)


def section(sid, crumb, path_label, body, wide=False):
    cls = "doc wide" if wide else "doc"
    if not wide:
        body = autolink(body)
    return (f'<section class="{cls}" id="{sid}" data-crumb="{E(crumb)}" hidden>'
            f'<p class="path">{E(path_label)}</p>{body}</section>')


def load_preset(code):
    f = ROOT / "presets" / f"{code}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def palette(m):
    out = []
    for part in (m.get("palette") or "").split(","):
        mm = re.match(r"\s*(.*?)\s*(#[0-9a-fA-F]{6})\s*$", part)
        if mm:
            out.append((mm.group(1), mm.group(2)))
    return out


def mood_body(m, code):
    sw = "".join(f'<div class="sw"><i style="background:{c}"></i><b>{E(n)}</b><span>{c}</span></div>' for n, c in palette(m))
    kw = "".join(f'<span class="kw">{E(k.strip())}</span>' for k in (m.get("mood_keywords") or "").split(",") if k.strip())
    cards = "".join(f'<div class="mcard"><h3>{l}</h3><p>{E(m[k])}</p></div>' for k, l in MOOD_FIELDS if m.get(k))
    links = []
    for ln in (m.get("ref_links") or "").splitlines():
        if "|" in ln:
            lab, url = [x.strip() for x in ln.split("|", 1)]
            if url.startswith("https://"):
                links.append(f'<a class="rl" href="{E(url)}" target="_blank" rel="noopener">{E(lab)}</a>')
    return (f'<h1 class="doc-title">분위기·톤 보드</h1><p class="lead">{E(m.get("mood", ""))}</p><div class="kws">{kw}</div>'
            + (f'<h2>팔레트</h2><div class="sws">{sw}</div>' if sw else "")
            + f'<h2>참조</h2><div class="mcards">{cards}</div>'
            + (f'<h2>레퍼런스 링크</h2><div class="rls">{"".join(links)}</div>' if links else "")
            + f'<p class="note">시나리오와 별개인 비주얼·톤 기준. 원본: claude/tools/presets/{E(code)}.json 의 mood</p>')


def scope_css(css, scope="#editor"):
    """editor.html 의 CSS 를 #editor 안으로 한정 (:root/body/헤더 규칙은 버림)"""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i = [], 0
    while i < len(css):
        j = css.find("{", i)
        if j < 0:
            break
        sel = css[i:j].strip()
        if sel.startswith("@media") or sel.startswith("@keyframes"):
            depth, k = 1, j + 1
            while depth and k < len(css):
                depth += {"{": 1, "}": -1}.get(css[k], 0); k += 1
            inner = css[j + 1:k - 1]
            out.append(sel + "{" + (inner if sel.startswith("@keyframes") else scope_css(inner, scope)) + "}")
            i = k; continue
        k = css.find("}", j)
        body = css[j + 1:k]
        i = k + 1
        parts = [s.strip() for s in sel.split(",")]
        if any(s.startswith(":root") or s == "body" or s.startswith(".head") or s == ".band" or s == "*" for s in parts):
            continue
        out.append(",".join(f"{scope} {s}" for s in parts) + "{" + body + "}")
    return "\n".join(out)


def editor_parts():
    src = (ROOT / "editor.html").read_text(encoding="utf-8")
    css = scope_css(src[src.index("<style>") + 7:src.index("</style>")])
    body = src[src.index("<!--EDITOR-START-->") + 19:src.index("<!--EDITOR-END-->")]
    scripts = src[src.index("<!--SCRIPT-START-->") + 19:src.index("<!--SCRIPT-END-->")]
    rules_md = (DOCS / "공통/01_기본_규칙.md").read_text(encoding="utf-8")
    rules = rules_md[rules_md.find("## 1."):rules_md.find("## 7.")].strip()
    presets = {c: load_preset(c) for c in WORKS if load_preset(c)}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("<", "\\u003c")
    scripts = scripts.replace("{{RULES_JSON}}", js(rules)).replace("{{PRESETS_JSON}}", js(presets))
    intro = ('<h1 class="doc-title">시나리오 작성 편집기</h1>'
             '<p class="note" style="margin-top:0">입력칸을 채우면 기본 규칙이 들어간 작성 프롬프트가 만들어지고, 그 프롬프트로 시나리오를 씁니다. '
             '메뉴는 <b>시나리오 입력</b>과 <b>분위기·톤</b>으로 나뉩니다.</p>')
    return css, '<div id="editor">' + intro + body + "</div>", scripts


def build():
    secs, nav = [], []
    LINKS.clear()
    for g, items in GROUPS:
        for sid, label, fn in items:
            if fn:
                LINKS["claude/" + fn] = sid; LINKS[fn] = sid
    for code, w in WORKS.items():
        LINKS[f"claude/tools/presets/{code}.json"] = f"{code}-mood"
        for key, label, fn in w["docs"]:
            LINKS[f"claude/작품/{code}/{fn}"] = f"{code}-{key}"; LINKS[f"작품/{code}/{fn}"] = f"{code}-{key}"
    first = next(iter(WORKS))
    LINKS.update({"공통 기본규칙": "rules", "공통 드라마6": "drama6", "공통 AI캐릭터6": "ai6", "공통 디자인": "dcom",
                  "작품1 설정": f"{first}-story", "작품1 디자인": f"{first}-design",
                  "시나리오 작성 편집기": "editor", "통합 자료집 › 시장·제작 자료 › 시장조사": "market"})
    # 홈
    cards_w = ""
    for code, w in WORKS.items():
        m = load_preset(code).get("mood", {})
        pal = "".join(f'<i style="background:{c}"></i>' for _, c in palette(m))
        cards_w += f'<a class="hcard" href="#{code}-mood"><b>{E(w["title"])}</b><span>{E(w["tagline"])}</span><div class="pal">{pal}</div></a>'
    cards_t = "".join(f'<a class="hcard" href="#{sid}"><b>{E(lab)}</b><span>{E(g)}</span></a>'
                      for g, items in GROUPS for sid, lab, _ in items if g in ("도구", "시장·제작 자료"))
    home = (f'<div class="hero"><div class="in"><h1>{PROJECT}</h1><p>로맨스 판타지 AI 드라마·웹툰 제작 자료집 · 왼쪽 ☰ 메뉴에서 작품과 자료를 찾아보세요.</p></div>'
            '<svg class="dan" viewBox="0 0 400 26" preserveAspectRatio="none" aria-hidden="true"><defs><pattern id="dp" width="32" height="26" patternUnits="userSpaceOnUse">'
            '<rect width="32" height="26" fill="#0b3d3b"/><rect width="32" height="4" fill="#b8362a"/><rect y="22" width="32" height="4" fill="#d9a53a"/>'
            '<path d="M16 6l8 7l-8 7l-8-7z" fill="#5fb3a9"/><path d="M16 9.5l4 3.5l-4 3.5l-4-3.5z" fill="#f3efe4"/></pattern></defs>'
            '<rect width="400" height="26" fill="url(#dp)"/></svg></div>'
            f'<p class="hsec">작품</p><div class="hgrid">{cards_w}</div>'
            f'<p class="hsec">도구 · 자료</p><div class="hgrid">{cards_t}</div>')
    secs.append(section("home", "홈", "", home))
    nav.append('<a class="it home" href="#home" data-go="home">⌂ 홈</a><div class="sep"></div>')

    # 작품 (1단계) › 작품명 (2단계) › 문서 (3단계)
    wnav = []
    for code, w in WORKS.items():
        items = []
        m = load_preset(code).get("mood")
        if m:
            sid = f"{code}-mood"
            secs.append(section(sid, f"작품 › {w['title']} › 분위기·톤", "비주얼·톤", mood_body(m, code)))
            items.append(f'<a class="it" href="#{sid}" data-go="{sid}">분위기·톤 <span class="ext">비주얼</span></a>')
        for key, label, fn in w["docs"]:
            sid = f"{code}-{key}"
            secs.append(section(sid, f"작품 › {w['title']} › {label}", f"claude/작품/{code}/{fn}",
                                render((DOCS / "작품" / code / fn).read_text(encoding="utf-8"), sid)))
            items.append(f'<a class="it" href="#{sid}" data-go="{sid}">{label}</a>')
        wnav.append(f'<details class="l2" open><summary><i class="dot" style="background:{w["color"]}"></i>{E(w["title"])}</summary>'
                    f'<div class="box l3">{"".join(items)}</div></details>')
    nav.append(f'<details class="l1" open><summary>작품</summary><div class="box">{"".join(wnav)}</div></details>')

    ed_css, ed_body, ed_js = editor_parts()
    for g, items in GROUPS:
        its = []
        for sid, label, fn in items:
            if sid == "editor":
                secs.append(section(sid, f"{g} › {label}", "", ed_body, wide=True))
            else:
                secs.append(section(sid, f"{g} › {label}", f"claude/{fn}", render((DOCS / fn).read_text(encoding="utf-8"), sid)))
            its.append(f'<a class="it" href="#{sid}" data-go="{sid}">{label}</a>')
        nav.append(f'<details class="l1" open><summary>{g}</summary><div class="box">{"".join(its)}</div></details>')

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    out = (ROOT / "hub.html").read_text(encoding="utf-8")
    for k, v in {"{{EDITOR_CSS}}": ed_css, "{{EDITOR_SCRIPTS}}": ed_js, "{{NAV}}": "".join(nav),
                 "{{SECTIONS}}": "\n".join(secs), "{{PROJECT}}": PROJECT, "{{VERSION}}": VERSION,
                 "{{EDITOR_VERSION}}": EDITOR_VERSION, "{{UPDATED}}": now}.items():
        out = out.replace(k, v)
    dst = (ROOT.parent / "site" / "index.html") if REPO else (ROOT / "out" / "hub.html")
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(out, encoding="utf-8")
    print(f"built {dst} ({len(out)} bytes, {VERSION}, {EDITOR_VERSION})")


if __name__ == "__main__":
    build()
