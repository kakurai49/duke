"""Generated validation snapshot; edit the sandbox source and run export_duke_validator.py.
Source: kakurai49/sandbox@47419e615aada02963da17bd97f422da7ab216d8/projects/agent2/tools/learning_dashboard_release.py
Source SHA-256: 5e254c3d3ad76a89317a32fccd182d402d00212039dd13de2f08475f7c526fa9
"""

from __future__ import annotations
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote, urlsplit


def _module(name):
    if name != "learning_dashboard_history":
        raise ValueError("UNSUPPORTED_VALIDATOR_MODULE")
    path = Path(__file__).with_name("duke_history.py")
    spec = importlib.util.spec_from_file_location("duke_history_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE_REPOSITORY = "kakurai49/sandbox"


CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'none'; "
       "connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'")


SHA = re.compile(r"[0-9a-f]{40}\Z")


ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\Z")


MAX_FILE = 1_000_000


MAX_TOTAL = 5_000_000


README = "# duke\n理解度の測定結果です\n"


class ReleaseError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ReleaseError(code)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def load_json(raw):
    require(len(raw) <= MAX_TOTAL, "JSON_BYTE_BUDGET")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ReleaseError("NONFINITE_JSON")))


def _keys(value, expected, code):
    require(isinstance(value, dict) and set(value) == set(expected.split()), code)


def _string(value, limit=2000, nullable=False):
    if nullable and value is None:
        return
    require(isinstance(value, str) and len(value) <= limit, "PUBLIC_TEXT_INVALID")
    require(not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value), "PUBLIC_TEXT_CONTROL")
    require(not re.search(r"(?:/workspace/|/home/|projects/agent2/|oai-library://|BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20})", value), "PRIVATE_REFERENCE_IN_PUBLIC_TEXT")


def validate_snapshot(snapshot):
    """Independent public-field allowlist; private records never pass through."""
    _keys(snapshot, "schema source summary items", "PUBLIC_SNAPSHOT_FIELDS")
    require(snapshot["schema"] == "learning-dashboard/v1", "PUBLIC_SNAPSHOT_SCHEMA")
    source = snapshot["source"]
    _keys(source, "repository commit verification_scope", "PUBLIC_SOURCE_FIELDS")
    require(source["repository"] == SOURCE_REPOSITORY and isinstance(source["commit"], str)
            and SHA.fullmatch(source["commit"]), "PUBLIC_SOURCE_IDENTITY")
    require(source["verification_scope"] == "stored_record_integrity_only", "PUBLIC_SOURCE_SCOPE")
    _keys(snapshot["summary"], "total open closed review_pending", "PUBLIC_SUMMARY_FIELDS")
    items = snapshot["items"]
    require(isinstance(items, list) and 0 < len(items) <= 120, "PUBLIC_ITEM_BUDGET")
    seen = set()
    for item in items:
        fields = "preparation_id title status status_label group event_date registered_at goal next_action learning capabilities sections closure evidence question hold"
        if "history" in item:
            fields += " history"
            _module("learning_dashboard_history").validate_history(item["history"])
        _keys(item, fields, "PUBLIC_ITEM_FIELDS")
        key = item["preparation_id"]
        require(isinstance(key, str) and ID.fullmatch(key) and key.lower() not in seen
                and ".." not in key, "PUBLIC_ID_INVALID_OR_DUPLICATE")
        seen.add(key.lower())
        require(item["group"] in {"open", "review_pending", "closed"}, "PUBLIC_GROUP")
        for field in ("title", "status", "status_label", "goal", "next_action"):
            _string(item[field])
        for field in ("event_date", "registered_at"):
            _string(item[field], 100, nullable=True)
        for category, names in (("learning", "preparation attendance review"),
                                ("capabilities", "recall application automaticity")):
            _keys(item[category], names, "PUBLIC_ASSESSMENT_FIELDS")
            for assessment in item[category].values():
                _keys(assessment, "status label description evidence_count", "PUBLIC_ASSESSMENT_FIELDS")
                for field in ("status", "label", "description"):
                    _string(assessment[field])
                require(type(assessment["evidence_count"]) is int and 0 <= assessment["evidence_count"] <= 100000, "PUBLIC_EVIDENCE_COUNT")
        require(isinstance(item["sections"], list) and len(item["sections"]) <= 20, "PUBLIC_SECTION_BUDGET")
        for section in item["sections"]:
            _keys(section, "heading body", "PUBLIC_SECTION_FIELDS")
            _string(section["heading"])
            _string(section["body"], 12000)
        _keys(item["closure"], "status label reason", "PUBLIC_CLOSURE_FIELDS")
        for value in item["closure"].values():
            _string(value)
        require(isinstance(item["evidence"], list) and len(item["evidence"]) <= 30, "PUBLIC_EVIDENCE_BUDGET")
        for row in item["evidence"]:
            _keys(row, "label kind status", "PUBLIC_EVIDENCE_FIELDS")
            for value in row.values():
                _string(value)
        _keys(item["question"], "text author adopted", "PUBLIC_QUESTION_FIELDS")
        _string(item["question"]["text"], nullable=True)
        require(item["question"]["author"] == "assistant" and type(item["question"]["adopted"]) is bool, "PUBLIC_QUESTION_ATTRIBUTION")
        _keys(item["hold"], "active reason", "PUBLIC_HOLD_FIELDS")
        require(type(item["hold"]["active"]) is bool, "PUBLIC_HOLD_ACTIVE")
        _string(item["hold"]["reason"], nullable=True)
        require(not item["hold"]["active"] or item["group"] != "closed", "PUBLIC_HOLD_CLOSED_CONFLICT")
    expected = {"total": len(items), "closed": sum(i["group"] == "closed" for i in items),
                "open": sum(i["group"] != "closed" for i in items),
                "review_pending": sum(i["group"] == "review_pending" for i in items)}
    require(snapshot["summary"] == expected and all(type(n) is int for n in snapshot["summary"].values()), "PUBLIC_SUMMARY_MISMATCH")
    return snapshot


def _local_target(page, value):
    require(isinstance(value, str) and not re.search(r"[\x00-\x20\\]", value), "URL_CONTROL_OR_BACKSLASH")
    parsed = urlsplit(value)
    require(not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.path.startswith("/"), "EXTERNAL_OR_ABSOLUTE_URL")
    decoded = unquote(parsed.path)
    require(decoded == parsed.path and "\\" not in decoded, "ENCODED_URL_DENIED")
    path = posixpath.normpath(posixpath.join(posixpath.dirname(page), decoded)) if decoded else page
    require(path not in {".", ".."} and not path.startswith("../"), "URL_PATH_ESCAPE")
    return path, unquote(parsed.fragment)


class PageFacts(HTMLParser):
    TAGS = set("html head meta title link body header main footer nav section article aside div span h1 h2 h3 h4 h5 h6 p a strong em small b i time dl dt dd label input textarea select option button details summary ul ol li script table caption thead tbody tfoot tr th td br hr noscript".split())
    ATTRS = set("lang charset name content http-equiv rel href src defer type class id role title datetime for value placeholder selected checked disabled readonly rows maxlength hidden open tabindex autocomplete inputmode spellcheck scope colspan rowspan aria-label aria-labelledby aria-describedby aria-live aria-current aria-controls aria-pressed aria-expanded aria-hidden aria-atomic data-filter data-search data-status data-preparation-id data-card data-count".split())

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.ids, self.links, self.assets = path, set(), [], []
        self.meta, self.script, self.script_count = {}, False, 0

    def handle_decl(self, decl):
        require(decl.lower() == "doctype html", "UNEXPECTED_DOCTYPE")

    def handle_starttag(self, tag, pairs):
        require(tag in self.TAGS, "ACTIVE_OR_UNKNOWN_HTML_TAG:" + tag)
        require(len({key for key, _ in pairs}) == len(pairs), "DUPLICATE_HTML_ATTRIBUTE")
        attrs = dict(pairs)
        for key, value in pairs:
            require(not key.startswith("on") and key != "style", "INLINE_HANDLER_OR_STYLE")
            require(key in self.ATTRS or re.fullmatch(r"(?:aria|data)-[a-z0-9-]+", key), "UNKNOWN_HTML_ATTRIBUTE:" + key)
            require(value is None or not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value), "HTML_ATTRIBUTE_CONTROL")
        if "id" in attrs:
            require(attrs["id"] and attrs["id"] not in self.ids, "DUPLICATE_HTML_ID")
            self.ids.add(attrs["id"])
        if tag == "meta":
            key = (attrs.get("http-equiv") or attrs.get("name") or ("charset" if "charset" in attrs else "")).lower()
            require(key in {"content-security-policy", "viewport", "referrer", "charset", "description", "color-scheme"}, "UNEXPECTED_META")
            require(key not in self.meta, "DUPLICATE_HTML_META")
            self.meta[key] = attrs.get("charset") if key == "charset" else attrs.get("content")
        if tag == "a":
            require(attrs.get("href"), "ANCHOR_HREF_REQUIRED")
            self.links.append(_local_target(self.path, attrs["href"]))
        elif "href" in attrs:
            require(tag == "link" and attrs.get("rel") == "stylesheet", "UNEXPECTED_HTML_HREF")
            target, fragment = _local_target(self.path, attrs["href"])
            require(target == "assets/style.css" and not fragment, "UNEXPECTED_STYLESHEET")
            self.assets.append(target)
        if tag == "script":
            require(not self.script and attrs.get("src") and attrs.get("type") in {None, "text/javascript"}, "INLINE_OR_NONSTANDARD_SCRIPT")
            target, fragment = _local_target(self.path, attrs["src"])
            require(target == "assets/app.js" and not fragment, "UNEXPECTED_SCRIPT")
            self.script = True
            self.script_count += 1
            self.assets.append(target)
        elif "src" in attrs:
            raise ReleaseError("UNEXPECTED_HTML_SOURCE")
        if tag == "input":
            require(attrs.get("type") in {"search", "text"}, "UNEXPECTED_INPUT_TYPE")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "script":
            raise ReleaseError("SELF_CLOSING_SCRIPT")

    def handle_endtag(self, tag):
        require(tag in self.TAGS, "UNKNOWN_HTML_END_TAG")
        if tag == "script":
            self.script = False

    def handle_data(self, data):
        require(not self.script or not data.strip(), "INLINE_SCRIPT_BODY")

    def validate(self):
        self.close()
        require(not self.script, "UNCLOSED_SCRIPT")
        require(self.meta.get("content-security-policy") == CSP, "CSP_MISMATCH")
        require(self.meta.get("referrer") == "no-referrer", "REFERRER_POLICY")
        require((self.meta.get("charset") or "").lower() == "utf-8", "CHARSET_REQUIRED")
        require("width=device-width" in (self.meta.get("viewport") or ""), "VIEWPORT_REQUIRED")
        require(self.assets.count("assets/style.css") == 1 and self.script_count <= 1, "HTML_ASSET_INVENTORY")
        if self.path == "index.html":
            require(self.script_count == 1, "INDEX_SEARCH_SCRIPT_REQUIRED")


def validate_site(files, snapshot):
    validate_snapshot(snapshot)
    expected = {"index.html", "assets/style.css", "assets/app.js", "data/dashboard.json", ".nojekyll", "README.md"}
    expected.update("records/" + row["preparation_id"].lower() + ".html" for row in snapshot["items"])
    require(set(files) == expected, "PUBLIC_FILE_ALLOWLIST_MISMATCH")
    require(files["data/dashboard.json"] == canonical(snapshot), "PUBLIC_SNAPSHOT_BYTES")
    require(files[".nojekyll"] == b"" and files["README.md"] == README.encode("utf-8"), "PUBLIC_BASELINE_FILES")
    css, js = files["assets/style.css"].decode("utf-8"), files["assets/app.js"].decode("utf-8")
    require(not re.search(r"@import\b|url\s*\(|expression\s*\(|-moz-binding|(?:^|[;{\s])behavior\s*:|<", css, re.I), "CSS_ACTIVE_OR_EXTERNAL_CONTENT")
    require(not re.search(r"\b(?:eval|Function|import|require|fetch|XMLHttpRequest|WebSocket|Worker|SharedWorker|importScripts|setTimeout|setInterval)\s*\(|\b(?:import|export)\s|\b(?:innerHTML|outerHTML|insertAdjacentHTML|sendBeacon|cookie|localStorage|sessionStorage|constructor)\b|document\s*\.\s*write|(?:window\s*\.\s*open|location\s*\.\s*(?:assign|replace))\s*\(|(?:https?|wss?|data|blob|javascript):", js), "JAVASCRIPT_UNREVIEWED_CAPABILITY")
    pages = {}
    for path, raw in files.items():
        require(len(raw) <= MAX_FILE, "FILE_BYTE_BUDGET")
        text = raw.decode("utf-8")
        require("\x00" not in text, "NUL_IN_PUBLIC_FILE")
        if path.endswith(".html"):
            page = PageFacts(path)
            page.feed(text)
            page.validate()
            pages[path] = page
    for page in pages.values():
        for target, fragment in page.links:
            require(target in pages, "HTML_LINK_TARGET_MISSING")
            require(not fragment or fragment in pages[target].ids, "HTML_FRAGMENT_MISSING")
    index_targets = {p for p, _ in pages["index.html"].links}
    require(expected.difference({"index.html", "assets/style.css", "assets/app.js", "data/dashboard.json", ".nojekyll", "README.md"}) <= index_targets, "DETAIL_NAVIGATION_MISSING")
    for name, page in pages.items():
        require(name == "index.html" or "index.html" in {p for p, _ in page.links}, "RETURN_NAVIGATION_MISSING")
    require(len(files) <= 128 and sum(map(len, files.values())) <= MAX_TOTAL, "RELEASE_BYTE_OR_FILE_BUDGET")
    return {"public_files": len(files), "html_pages": len(pages), "records": len(snapshot["items"]),
            "local_links_verified": True, "csp_verified": True, "third_party_dependencies": 0}
