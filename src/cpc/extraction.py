"""Structural extraction; changes only an in-memory derived DOM."""

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from .domain import Block

NORMALIZATION_VERSION = "structure-v1"
NOISE = (
    "script,style,noscript,nav,footer,aside,button,form,svg,template,"
    "[role=navigation],[role=banner],[role=complementary],.advertisement,.adsbygoogle,"
    ".mw-editsection,.vector-header,.vector-page-toolbar,.printfooter"
)
ATOMIC = {
    "p": "paragraph",
    "ul": "list",
    "ol": "list",
    "dl": "list",
    "table": "table",
    "blockquote": "quote",
    "pre": "code",
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
}
CONTAINERS = {"div", "section", "main", "article", "body", "header", "details", "figure"}


def text(tag):
    if tag.name == "table":
        return "\n".join(
            " | ".join(
                c.get_text(" ", strip=True) for c in row.find_all(["th", "td"], recursive=False)
            )
            for row in tag.find_all("tr")
        )
    if tag.name in {"ul", "ol", "dl"}:
        return "\n".join(
            "- " + item.get_text(" ", strip=True) for item in tag.find_all(["li", "dt", "dd"])
        )
    return re.sub(r"[ \t]+", " ", tag.get_text(" ", strip=True)).strip()


def positions(soup):
    for tag in soup.find_all(True):
        chain = []
        current = tag
        while isinstance(current, Tag) and current.name != "[document]":
            index = sum(isinstance(t, Tag) for t in current.previous_siblings)
            chain.append(f"{current.name}[{index}]")
            current = current.parent
        tag["_cpc_position"] = "/" + "/".join(reversed(chain))


class GenericExtractor:
    name = "generic"
    version = "1"

    def root(self, soup):
        main = soup.select_one("main, [role=main]")
        if main:
            return main
        articles = soup.find_all("article")
        if len(articles) == 1 and len(text(articles[0])) > 80:
            return articles[0]
        return soup.body or soup

    def extract_html(self, html, artifact="dom/main.html", prefix=""):
        if isinstance(html, bytes):
            html = html.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        positions(soup)
        for tag in soup.select(NOISE):
            tag.decompose()
        root = self.root(soup)
        blocks, section = [], []

        def emit(tag, kind, content=None):
            value = text(tag) if content is None else content.strip()
            if value:
                blocks.append(
                    Block(
                        kind,
                        value,
                        section.copy(),
                        prefix + tag.get("_cpc_position", "/"),
                        artifact,
                        {k: tag[k] for k in ("id", "datetime", "data-post-id") if k in tag},
                    )
                )

        def walk(tag):
            if not isinstance(tag, Tag):
                return
            if tag.name in ATOMIC:
                kind = ATOMIC[tag.name]
                if kind == "heading":
                    level = int(tag.name[1])
                    del section[level - 1 :]
                    section.append(text(tag))
                emit(tag, kind)
                return
            classes = set(tag.get("class", []))
            is_post = (
                tag.get("data-testid") == "tweet"
                or bool(classes & {"post", "res", "response"})
                or tag.has_attr("data-post-id")
            )
            if is_post:
                emit(tag, "post")
                if blocks:
                    blocks[-1].metadata["links"] = [
                        a.get("href") for a in tag.find_all("a") if a.get("href")
                    ]
                    blocks[-1].metadata["times"] = [t.get("datetime") for t in tag.find_all("time")]
                return
            inline = []

            def flush():
                if inline:
                    emit(tag, "paragraph", " ".join(inline))
                    inline.clear()

            for child in tag.children:
                if isinstance(child, NavigableString):
                    if str(child).strip():
                        inline.append(str(child).strip())
                elif isinstance(child, Tag):
                    if (
                        child.name in ATOMIC
                        or child.name in CONTAINERS
                        or child.find(list(ATOMIC.keys()) + list(CONTAINERS))
                    ):
                        flush()
                        walk(child)
                    else:
                        inline.append(text(child))
            flush()

        walk(root)
        return blocks

    def extract(self, bundle, include_auxiliary=False):
        blocks = self.extract_html(bundle.artifacts["dom/main.html"])
        if include_auxiliary:
            for frame in bundle.metadata["frames"]:
                if frame.get("capture_status") == "success":
                    blocks.extend(self.extract_html(bundle.artifacts[frame["file"]], frame["file"]))
            for i, shadow in enumerate(bundle.metadata["shadow-dom"]):
                blocks.extend(
                    self.extract_html(
                        shadow["html"],
                        "metadata/shadow-dom.json",
                        f"/{i}:{shadow['host_path']}/#shadow-root",
                    )
                )
        return blocks


class WikipediaExtractor(GenericExtractor):
    name = "wikipedia"

    def root(self, soup):
        return soup.select_one(
            "#mw-content-text .mw-parser-output, #mw-content-text"
        ) or super().root(soup)


class PixivExtractor(GenericExtractor):
    name = "pixiv-encyclopedia"

    def root(self, soup):
        return soup.select_one("article") or super().root(soup)


class ExtractorRegistry:
    def __init__(self):
        self.sites = {"ja.wikipedia.org": WikipediaExtractor(), "dic.pixiv.net": PixivExtractor()}
        self.generic = GenericExtractor()

    def select(self, site):
        return self.sites.get(site, self.generic)


def chunks(blocks, size=1000, overlap=100):
    if size < 100 or not 0 <= overlap < size:
        raise ValueError("Invalid chunk size/overlap")
    output, pending = [], []

    def flush():
        if pending:
            output.append(
                {
                    "content": "\n".join(b.content for b in pending),
                    "section": pending[0].section,
                    "positions": [b.position for b in pending],
                    "artifact": pending[0].artifact,
                    "kinds": [b.kind for b in pending],
                    "blocks_metadata": [b.metadata for b in pending],
                    "start": 0,
                }
            )
            pending.clear()

    for block in blocks:
        structural = block.kind in {"table", "post", "quote", "list"}
        if pending and (
            structural
            or block.section != pending[0].section
            or block.artifact != pending[0].artifact
            or sum(len(b.content) + 1 for b in pending) + len(block.content) > size
        ):
            flush()
        if len(block.content) > size:
            flush()
            for start in range(0, len(block.content), size - overlap):
                output.append(
                    {
                        "content": block.content[start : start + size],
                        "section": block.section,
                        "positions": [block.position],
                        "artifact": block.artifact,
                        "kinds": [block.kind],
                        "blocks_metadata": [block.metadata],
                        "start": start,
                    }
                )
                if start + size >= len(block.content):
                    break
        else:
            pending.append(block)
            if structural:
                flush()
    flush()
    return output
