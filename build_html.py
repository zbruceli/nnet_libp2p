#!/usr/bin/env python3
"""Render nnet-vs-libp2p-deep-dive.md into a standalone, browser-friendly index.html.

usage: python3 build_html.py        (writes index.html next to this script)
Images are referenced relatively (images/...), so keep index.html at the repository root.
"""
import html, os, re
import markdown
from pygments.formatters import HtmlFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "nnet-vs-libp2p-deep-dive.md")
OUT = os.path.join(HERE, "index.html")
REPO = "https://github.com/zbruceli/nnet_libp2p"
SITE = "https://zbruceli.github.io/nnet_libp2p/"

md_text = open(SRC, encoding="utf-8").read()

# ---- pull title, hero and subtitle out of the markdown; the page header renders them
m = re.match(r"# (.+?)\n\n!\[([^\]]*)\]\(([^)]+)\)\n\n\*(.+?)\*\n", md_text, re.S)
title, hero_alt, hero_src, subtitle = m.group(1), m.group(2), m.group(3), m.group(4)
# the page already shows the title as a heading, so the header uses the text-free hero;
# link previews (og:image) keep the titled version
page_hero = hero_src.replace("00-hero.png", "00-hero-notext.png")
if not os.path.exists(os.path.join(HERE, page_hero)):
    page_hero = hero_src
body_md = md_text[m.end():]

md = markdown.Markdown(extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists", "attr_list"],
                       extension_configs={"codehilite": {"guess_lang": False, "css_class": "hl"},
                                          "toc": {"toc_depth": "2-3", "permalink": "#", "permalink_title": "Link to this section"}})
body = md.convert(body_md)
toc_tokens = md.toc_tokens

# ---- figures: <p><img></p> followed by <p><em>Figure …</em></p>  ->  <figure>
body = re.sub(r'<p>(<img [^>]+>)\s*(?:</p>\s*<p>)?<em>(Figure \d+\..*?)</em></p>',
              lambda m: f'<figure>{m.group(1)}<figcaption>{m.group(2)}</figcaption></figure>', body, flags=re.S)
body = re.sub(r'<p>(<img [^>]+>)</p>', r'<figure>\1</figure>', body)
def png_size(path):
    import struct
    with open(os.path.join(HERE, path), "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])
def add_dims(m):
    tag = m.group(0)
    src = re.search(r'src="([^"]+)"', tag).group(1)
    w, h = png_size(src)
    return tag.replace("<img ", f'<img width="{w}" height="{h}" loading="lazy" decoding="async" ', 1)
body = re.sub(r"<img [^>]+>", add_dims, body)  # reserve space so lazy images don't shift the page
# ---- tables scroll horizontally on small screens
body = re.sub(r"<table>", '<div class="table-wrap"><table>', body).replace("</table>", "</table></div>")
# ---- links to repository files open on GitHub (works when the page is hosted elsewhere too)
def fix_link(m):
    href = m.group(1)
    if href.startswith(("http", "#", "mailto:", "images/")):
        return m.group(0)
    kind = "tree" if href.endswith("/") else "blob"
    return f'href="{REPO}/{kind}/main/{href}"'
body = re.sub(r'href="([^"]+)"', fix_link, body)
body = body.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')

# ---- table of contents (sections + subsections)
def toc_html(tokens, depth=0):
    out = ['<ol>' if depth == 0 else '<ol class="sub">']
    for t in tokens:
        out.append(f'<li><a href="#{t["id"]}">{t["name"]}</a>')
        if t.get("children") and depth == 0:
            out.append(toc_html(t["children"], depth + 1))
        out.append("</li>")
    out.append("</ol>")
    return "".join(out)
toc = toc_html(toc_tokens)

words = len(re.sub(r"<[^>]+>", " ", body).split())
minutes = round(words / 230)

pyg_light = HtmlFormatter(style="friendly").get_style_defs(".hl")
pyg_dark = HtmlFormatter(style="github-dark").get_style_defs(":root[data-theme=dark] .hl")
pyg_dark_media = HtmlFormatter(style="github-dark").get_style_defs(":root:not([data-theme=light]) .hl")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(subtitle)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(subtitle)}">
<meta property="og:type" content="article">
<meta property="og:image" content="{SITE}{hero_src}">
<meta property="og:url" content="{SITE}">
<link rel="canonical" href="{SITE}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>
:root {{
  color-scheme: light;
  --bg: #fcfcfb; --surface: #f3f2ee; --surface-2: #ebe9e3; --border: #dedcd5;
  --text: #1b1b19; --text-2: #52514e; --text-3: #7a7974;
  --accent: #2a78d6; --accent-2: #eb6834; --link: #1c5cab; --mark: #fff3c4;
  --code-bg: #f5f4f0; --shadow: 0 1px 2px rgba(0,0,0,.04), 0 4px 16px rgba(0,0,0,.04);
  --serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --bg: #0f1218; --surface: #171b23; --surface-2: #1f2430; --border: #2b3140;
    --text: #e9e8e4; --text-2: #b4b7bf; --text-3: #868a94;
    --accent: #5598e7; --accent-2: #f08a5d; --link: #86b6ef; --mark: #3a3420;
    --code-bg: #151922; --shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 16px rgba(0,0,0,.25);
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --bg: #0f1218; --surface: #171b23; --surface-2: #1f2430; --border: #2b3140;
  --text: #e9e8e4; --text-2: #b4b7bf; --text-3: #868a94;
  --accent: #5598e7; --accent-2: #f08a5d; --link: #86b6ef; --mark: #3a3420;
  --code-bg: #151922; --shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 16px rgba(0,0,0,.25);
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; scroll-padding-top: 72px; -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; background: var(--bg); color: var(--text); font: 18px/1.7 var(--serif); }}
a {{ color: var(--link); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
a:hover {{ text-decoration-thickness: 2px; }}

/* progress bar */
#progress {{ position: fixed; inset: 0 0 auto 0; height: 3px; z-index: 50; background: linear-gradient(90deg, var(--accent), var(--accent-2));
  transform-origin: 0 50%; transform: scaleX(0); }}

/* top bar */
.topbar {{ position: sticky; top: 0; z-index: 40; display: flex; align-items: center; gap: 12px; padding: 10px 20px;
  background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: saturate(1.4) blur(10px);
  border-bottom: 1px solid var(--border); font: 500 14px/1.2 var(--sans); }}
.topbar .brand {{ color: var(--text); text-decoration: none; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.topbar .spacer {{ flex: 1; }}
.topbar button, .topbar a.btn {{ font: inherit; color: var(--text-2); background: transparent; border: 1px solid var(--border);
  border-radius: 8px; padding: 6px 10px; cursor: pointer; text-decoration: none; white-space: nowrap; }}
.topbar button:hover, .topbar a.btn:hover {{ color: var(--text); background: var(--surface); }}
#toc-toggle {{ display: none; }}

/* hero */
.hero {{ background: #0b1220; }}
.hero img {{ display: block; width: 100%; max-width: 1600px; margin: 0 auto; height: auto; aspect-ratio: 1600 / 840; }}
header.intro {{ max-width: 760px; margin: 48px auto 8px; padding: 0 20px; }}
header.intro h1 {{ font: 800 clamp(30px, 5vw, 46px)/1.12 var(--sans); letter-spacing: -0.02em; margin: 0 0 16px; }}
header.intro .dek {{ font: 400 21px/1.5 var(--serif); color: var(--text-2); margin: 0 0 20px; font-style: italic; }}
header.intro .meta {{ font: 500 14px/1.4 var(--sans); color: var(--text-3); display: flex; flex-wrap: wrap; gap: 6px 16px; }}

/* layout */
.layout {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 760px) minmax(0, 1fr); gap: 0 48px; padding: 0 20px; }}
main {{ grid-column: 2; min-width: 0; }}
nav.toc {{ grid-column: 1; justify-self: end; width: 100%; max-width: 280px; }}
nav.toc .inner {{ position: sticky; top: 72px; max-height: calc(100vh - 96px); overflow: auto; padding: 8px 4px 24px 0; font: 14px/1.45 var(--sans); }}
nav.toc .label {{ font: 700 12px/1 var(--sans); letter-spacing: .08em; text-transform: uppercase; color: var(--text-3); margin: 8px 0 12px 12px; }}
nav.toc ol {{ list-style: none; margin: 0; padding: 0; }}
nav.toc ol.sub {{ display: none; margin: 2px 0 6px 12px; border-left: 1px solid var(--border); }}
nav.toc li.open > ol.sub {{ display: block; }}
nav.toc a {{ display: block; padding: 5px 12px; color: var(--text-2); text-decoration: none; border-radius: 6px; }}
nav.toc ol.sub a {{ font-size: 13px; padding: 3px 12px; color: var(--text-3); }}
nav.toc a:hover {{ color: var(--text); background: var(--surface); }}
nav.toc a.active {{ color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); font-weight: 600; }}

/* content */
main > *:first-child {{ margin-top: 24px; }}
main h2, main h3, main h4 {{ font-family: var(--sans); letter-spacing: -0.01em; line-height: 1.25; position: relative; }}
main h2 {{ font-size: 30px; font-weight: 800; margin: 72px 0 16px; padding-top: 8px; }}
main h3 {{ font-size: 22px; font-weight: 700; margin: 44px 0 12px; }}
main h4 {{ font-size: 18px; font-weight: 700; margin: 32px 0 8px; }}
main .headerlink {{ position: absolute; left: -1.1em; padding-right: .3em; color: var(--text-3); text-decoration: none; opacity: 0; font-weight: 400; }}
main h2:hover .headerlink, main h3:hover .headerlink, main h4:hover .headerlink {{ opacity: 1; }}
main p, main li {{ hyphens: auto; }}
main ul, main ol {{ padding-left: 1.4em; }}
main li {{ margin: .35em 0; }}
main strong {{ font-weight: 600; }}
main hr {{ border: 0; height: 1px; background: var(--border); margin: 56px 0; }}
main blockquote {{ margin: 24px 0; padding: 4px 20px; border-left: 3px solid var(--accent); color: var(--text-2); }}
code {{ font: 0.84em/1.5 var(--mono); background: var(--code-bg); border: 1px solid var(--border); border-radius: 5px; padding: .1em .35em; }}
.hl {{ margin: 24px 0; border: 1px solid var(--border); border-radius: 10px; background: var(--code-bg) !important; }}
.hl pre {{ margin: 0; padding: 16px 18px; overflow: auto; font: 14px/1.6 var(--mono); }}
.hl code {{ background: none; border: 0; padding: 0; font-size: inherit; }}
pre {{ font: 14px/1.6 var(--mono); overflow: auto; }}

/* figures */
figure {{ margin: 36px 0; }}
figure img {{ display: block; width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--border); box-shadow: var(--shadow); background: #fcfcfb; }}
figcaption {{ margin-top: 10px; font: 14px/1.5 var(--sans); color: var(--text-2); }}
@media (min-width: 1440px) {{ figure {{ margin-left: -48px; margin-right: -48px; }} }}

/* tables */
.table-wrap {{ overflow-x: auto; margin: 28px 0; border: 1px solid var(--border); border-radius: 10px; }}
table {{ border-collapse: collapse; width: max-content; min-width: 100%; max-width: 1100px; font: 14.5px/1.45 var(--sans); }}
td:first-child {{ min-width: 170px; }}
td {{ max-width: 340px; }}
th, td {{ padding: 10px 14px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--border); }}
thead th {{ background: var(--surface); font-weight: 600; white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }}
tbody tr:hover td {{ background: color-mix(in srgb, var(--surface) 60%, transparent); }}
td code, th code {{ font-size: .85em; }}

/* TL;DR emphasis */
#tldr + * , #tldr ~ ul:first-of-type {{ }}
.callout {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 4px 24px; margin: 24px 0; }}

footer {{ max-width: 760px; margin: 80px auto 48px; padding: 24px 20px 0; border-top: 1px solid var(--border);
  font: 14px/1.6 var(--sans); color: var(--text-3); }}

/* responsive */
@media (max-width: 1100px) {{
  .layout {{ grid-template-columns: minmax(0, 760px); justify-content: center; }}
  main {{ grid-column: 1; }}
  #toc-toggle {{ display: inline-block; }}
  nav.toc {{ position: fixed; inset: 49px auto 0 0; z-index: 45; width: min(320px, 86vw); max-width: none; background: var(--bg);
    border-right: 1px solid var(--border); transform: translateX(-102%); transition: transform .2s ease; box-shadow: var(--shadow); }}
  nav.toc.open {{ transform: none; }}
  nav.toc .inner {{ position: static; max-height: 100%; height: 100%; padding: 16px 8px 40px; }}
  nav.toc ol.sub {{ display: block; }}
}}
@media (max-width: 640px) {{
  body {{ font-size: 17px; }}
  main h2 {{ font-size: 25px; margin-top: 56px; }}
  main h3 {{ font-size: 20px; }}
  header.intro {{ margin-top: 32px; }}
  header.intro .dek {{ font-size: 18px; }}
  .topbar .brand {{ display: none; }}
  .topbar .lbl {{ display: none; }}
  .topbar {{ padding: 8px 14px; }}
  main .headerlink {{ display: none; }}
}}
@media print {{
  .topbar, nav.toc, #progress {{ display: none; }}
  .layout {{ display: block; }}
  body {{ font-size: 11pt; background: #fff; color: #000; }}
  figure {{ break-inside: avoid; }}
}}
{pyg_light}
@media (prefers-color-scheme: dark) {{
{pyg_dark_media}
}}
{pyg_dark}
</style>
</head>
<body>
<div id="progress"></div>
<div class="topbar">
  <button id="toc-toggle" aria-label="Toggle contents" aria-expanded="false">☰<span class="lbl"> Contents</span></button>
  <a class="brand" href="#top">{html.escape(title.split(':')[0])}</a>
  <span class="spacer"></span>
  <button id="theme" aria-label="Toggle dark mode">◐<span class="lbl"> Theme</span></button>
  <a class="btn" href="{REPO}" target="_blank" rel="noopener">GitHub<span class="lbl"> ↗</span></a>
</div>
<div class="hero" id="top"><img src="{page_hero}" alt="{html.escape(hero_alt)}" width="1600" height="840"></div>
<header class="intro">
  <h1>{html.escape(title)}</h1>
  <p class="dek">{html.escape(subtitle)}</p>
  <div class="meta"><span>≈ {minutes} min read</span><span>{len(re.findall('<figure>', body))} figures</span>
    <span>Code, data &amp; benchmark: <a href="{REPO}" target="_blank" rel="noopener">github.com/zbruceli/nnet_libp2p</a></span></div>
</header>
<div class="layout">
  <nav class="toc" id="toc" aria-label="Contents"><div class="inner"><div class="label">Contents</div>{toc}</div></nav>
  <main id="content">
{body}
  </main>
</div>
<footer>
  Generated from <a href="{REPO}/blob/main/nnet-vs-libp2p-deep-dive.md">nnet-vs-libp2p-deep-dive.md</a>. Figures, simulator and benchmark harness:
  <a href="{REPO}">{REPO.replace('https://', '')}</a>.
</footer>
<script>
(() => {{
  // theme toggle (remembered per browser when storage is available)
  const root = document.documentElement;
  try {{ const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; }} catch (e) {{}}
  document.getElementById("theme").addEventListener("click", () => {{
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try {{ localStorage.setItem("theme", root.dataset.theme); }} catch (e) {{}}
  }});
  // reading progress
  const bar = document.getElementById("progress");
  const onScroll = () => {{
    const h = document.documentElement; const max = h.scrollHeight - h.clientHeight;
    bar.style.transform = `scaleX(${{max > 0 ? h.scrollTop / max : 0}})`;
  }};
  addEventListener("scroll", onScroll, {{ passive: true }}); onScroll();
  // mobile contents drawer
  const toc = document.getElementById("toc"), btn = document.getElementById("toc-toggle");
  btn.addEventListener("click", () => {{ const o = toc.classList.toggle("open"); btn.setAttribute("aria-expanded", o); }});
  toc.addEventListener("click", e => {{ if (e.target.tagName === "A") {{ toc.classList.remove("open"); btn.setAttribute("aria-expanded", false); }} }});
  // scroll-spy: highlight the current section, expand its subsections
  const links = [...toc.querySelectorAll("a")];
  const byId = new Map(links.map(a => [decodeURIComponent(a.hash.slice(1)), a]));
  const heads = [...document.querySelectorAll("main h2[id], main h3[id]")].filter(h => byId.has(h.id));
  let current = null;
  const spy = () => {{
    let best = heads[0];
    for (const h of heads) {{ if (h.getBoundingClientRect().top < 120) best = h; else break; }}
    if (!best || best === current) return;
    current = best;
    links.forEach(a => a.classList.remove("active"));
    toc.querySelectorAll("li.open").forEach(li => li.classList.remove("open"));
    const a = byId.get(best.id); a.classList.add("active");
    let li = a.closest("li"); while (li) {{ li.classList.add("open"); li = li.parentElement.closest("li"); }}
    const top = a.closest("ol:not(.sub) > li"); if (top) top.classList.add("open");
    if (getComputedStyle(toc).position !== "fixed") a.scrollIntoView({{ block: "nearest" }});
  }};
  addEventListener("scroll", spy, {{ passive: true }}); spy();
}})();
</script>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {OUT}: {len(page)//1024} KB, {words} words (~{minutes} min), {len(toc_tokens)} sections")
