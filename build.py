"""Generate static language pages, validate links, and package the hosting directory."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json
import re
import shutil

root = Path(__file__).resolve().parent
languages = ('ko', 'en', 'ja')

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.anchors, self.files, self.switches = [], [], [], []
        self.sections = self.people = 0
        self.lang = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'section': self.sections += 1
        if a.get('class') == 'person': self.people += 1
        if tag == 'a' and 'hreflang' in a: self.switches.append(a)
        for key in ('src', 'href'):
            v = a.get(key, '')
            if v.startswith('#'): self.anchors.append(v[1:])
            elif v and not urlparse(v).scheme: self.files.append(unquote(urlparse(v).path))

def generate():
    source = (root / 'index.html').read_text()
    catalogs = {lang: json.loads((root / 'locales' / f'{lang}.json').read_text()) for lang in languages[1:]}
    assert catalogs['en'].keys() == catalogs['ja'].keys(), 'Translation keys differ'
    for lang, catalog in catalogs.items():
        assert all(key in source for key in catalog), 'Stale translation key'
        pattern = re.compile('|'.join(re.escape(key) for key in sorted(catalog, key=len, reverse=True)))
        untranslated = pattern.sub('', source)
        assert not re.search(r'[가-힣]', untranslated), f'{lang}: untranslated Korean source text'
        page = pattern.sub(lambda match: catalog[match[0]], source)
        page = page.replace('<html lang="ko">', f'<html lang="{lang}">')
        page = page.replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
        page = page.replace('href="style.css"', 'href="../style.css"')
        page = page.replace('href="index.html"', 'href="../index.html"')
        page = page.replace('href="en/index.html"', 'href="../en/index.html"').replace('href="ja/index.html"', 'href="../ja/index.html"')
        page = page.replace(' aria-current="page"', '').replace(f'lang="{lang}" hreflang="{lang}"', f'lang="{lang}" hreflang="{lang}" aria-current="page"')
        (root / lang).mkdir(exist_ok=True)
        (root / lang / 'index.html').write_text(page)
    return [root / 'index.html', *(root / lang / 'index.html' for lang in languages[1:])]

def build():
    pages = generate()
    for lang, path in zip(languages, pages):
        p = Page(); p.feed(path.read_text())
        assert p.lang == lang, f'{lang}: wrong document language'
        assert len(p.ids) == len(set(p.ids)), f'{lang}: duplicate IDs'
        assert p.sections == 3 and p.people == 5, f'{lang}: unexpected page structure'
        assert all(x in p.ids for x in p.anchors), f'{lang}: broken section link'
        assert all((path.parent / x).is_file() for x in p.files), f'{lang}: missing asset or page'
        assert {a['hreflang'] for a in p.switches} == set(languages), f'{lang}: missing language switch'
        assert [a['hreflang'] for a in p.switches if a.get('aria-current') == 'page'] == [lang], f'{lang}: incorrect active language'
    css = (root / 'style.css').read_text()
    assert css.count('{') == css.count('}'), 'CSS braces'
    out = root / 'dist'; out.mkdir(exist_ok=True)
    for name in ('index.html', 'style.css'): shutil.copy2(root / name, out / name)
    for name in ('en', 'ja', 'assets'): shutil.copytree(root / name, out / name, dirs_exist_ok=True)
    print('Static build passed: 3 languages, each with 3 sections and 5 producers; assets, section links, and language links verified.')

if __name__ == '__main__':
    build()
