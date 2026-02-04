import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

ARXIV_API = "http://export.arxiv.org/api/query"

def arxiv_search(query: str, k: int = 8) -> List[Dict]:
    # arXiv API uses its own query syntax; this is a simple default
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max(1, min(k, 20)),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    r = requests.get(ARXIV_API, params=params, timeout=20)
    r.raise_for_status()

    # Parse Atom feed
    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
        link = ""
        for l in entry.findall("a:link", ns):
            if l.attrib.get("rel") == "alternate":
                link = l.attrib.get("href", "")
                break
        published = (entry.findtext("a:published", default="", namespaces=ns) or "").strip()
        year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else 0
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        out.append({
            "title": title,
            "year": year,
            "url": link,
            "abstract": summary,
        })
    return out
