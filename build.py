from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import shutil
root=Path(__file__).resolve().parent
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.anchors=[];self.files=[];self.sections=0;self.people=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='section':self.sections+=1
        if a.get('class')=='person':self.people+=1
        for key in ('src','href'):
            v=a.get(key,'')
            if v.startswith('#'):self.anchors.append(v[1:])
            elif v and not urlparse(v).scheme:self.files.append(v)
p=Page();p.feed((root/'index.html').read_text())
assert len(p.ids)==len(set(p.ids)), 'Duplicate IDs'
assert p.sections==3 and p.people==5, 'Unexpected page structure'
assert all(x in p.ids for x in p.anchors), 'Broken section link'
assert all((root/x).is_file() for x in p.files), 'Missing asset'
assert (root/'style.css').read_text().count('{')==(root/'style.css').read_text().count('}'), 'CSS braces'
out=root/'dist';out.mkdir(exist_ok=True)
for name in ('index.html','style.css'):shutil.copy2(root/name,out/name)
shutil.copytree(root/'assets',out/'assets',dirs_exist_ok=True)
print('Static build passed: 3 sections, 5 producers, all local assets and section links present.')
