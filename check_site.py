"""Check static release structure, not truth, security, or search indexing."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'docs'
BASE = 'https://unnamedmistress.github.io/practical-ai-safety/'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.metas, self.canonicals = [], set(), {}, []
        self.h1 = 0
        self.schema = ''
        self.in_schema = False
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            assert a['id'] not in self.ids, f"Duplicate id {a['id']}"
            self.ids.add(a['id'])
        if tag == 'h1': self.h1 += 1
        if tag == 'title': self.in_title = True
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag == 'script' and a.get('src'): self.links.append(a['src'])
        if tag == 'img':
            assert a.get('alt') and a.get('width') and a.get('height'), 'Image needs alt and dimensions'
            self.links.append(a['src'])
        if tag == 'link' and a.get('rel') == 'canonical': self.canonicals.append(a['href'])
        if tag == 'meta': self.metas[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'script' and a.get('type') == 'application/ld+json': self.in_schema = True

    def handle_endtag(self, tag):
        if tag == 'script': self.in_schema = False
        if tag == 'title': self.in_title = False

    def handle_data(self, data):
        if self.in_schema: self.schema += data
        if self.in_title: self.title += data

def main():
    pages = {}
    for f in ROOT.glob('*.html'):
        p = Page(); p.feed(f.read_text(encoding='utf-8')); pages[f.resolve()] = p
    assert len(pages) == 6, 'Expected six pages'
    titles, descriptions, canonicals = set(), set(), set()
    for f,p in pages.items():
        assert p.h1 == 1, f'{f.name}: exactly one H1 required'
        assert p.title and p.title not in titles, f'{f.name}: title missing or duplicated'
        titles.add(p.title)
        desc = p.metas.get('description')
        assert desc and desc not in descriptions, f'{f.name}: description missing or duplicated'
        descriptions.add(desc)
        expected = BASE + ('' if f.name == 'index.html' else f.name)
        assert p.canonicals == [expected], f'{f.name}: wrong canonical'
        assert p.metas.get('og:url') == expected, f'{f.name}: wrong social URL'
        assert p.metas.get('robots') == 'index,follow', f'{f.name}: index directive'
        assert p.metas.get('viewport'), f'{f.name}: viewport missing'
        schema = json.loads(p.schema)
        assert schema['url'] == expected and schema['author']['name'] == 'Chrysti Reichert'
        canonicals.add(expected)
        for link in p.links:
            u = urlsplit(link)
            if u.scheme or u.netloc: continue
            target = (f.parent / unquote(u.path)).resolve() if u.path else f
            assert target.is_relative_to(ROOT), f'{f.name}: link escapes published docs'
            assert target.exists(), f'{f.name}: missing {link}'
            if u.fragment and target in pages:
                assert u.fragment in pages[target].ids, f'{f.name}: missing anchor {link}'
        if f.name != 'sources.html':
            coaching = [x for x in p.links if '/ai-assistant-coaching?' in x]
            assert len(coaching) == 1 and 'utm_campaign=practical_ai_safety' in coaching[0]
    sm = ET.parse(ROOT/'sitemap.xml')
    locations = [e.text for e in sm.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    assert len(locations) == len(set(locations)) and set(locations) == canonicals
    assert len(list((ROOT/'worksheets').glob('*.md'))) == 3
    print('PASS: six pages, unique metadata, canonicals, schema, local links, anchors, coaching tags, three worksheets, sitemap')

if __name__ == '__main__': main()
