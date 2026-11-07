"""Presentation viewports and a locally declared proper name; core is read-only."""
import sys, os, json, hashlib
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(os.environ.get('NOEMA_SOURCE', ROOT.parent/'noema')).resolve()))
from scripts.concept2_writing import WritingReader
from scripts.concept2_document import full_name, full_parts
from scripts import concept2_composition as c, concept2_geometry_v5 as g
from scripts.two_work_batch import render_record
from noema.constructed import parse

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')

w = WritingReader()
hero = c.from_svg((ROOT/'public/glyphs/kant-paragraph-1.svg').read_text(encoding='utf-8'))
save(ROOT/'public/glyphs/hero.svg', c.svg(hero, pad=c.PEN/2)+'\n')
for name in c.ROOT_NAMES:
    # Every root retains its own radius and the same origin and physical scale.
    save(ROOT/f'public/glyphs/roots/{name}.svg', c.svg(c.move(w.forms[('root', name)]['shapes'],70,70),width=140,height=140)+'\n')

out = ROOT/'output/noema-name'
roots = ['round','book','inside']
symbol = full_name([c.old.root_symbol(n) for n in roots])
catalog = json.loads((ROOT/'public/data/dictionary.json').read_text(encoding='utf-8'))
assert symbol not in {e['symbol'] for e in catalog['entries']}
source = f'p:\nr {symbol}[] a.\n'
record = parse(source)['declarations'][0]
canonical = w.canonical_record(record)
raw, _ = render_record(w,w.encode_record(record),1400)
assert WritingReader().read_page(raw)['statements']==[canonical]
tokens = w._raw_word(full_parts(symbol))
shapes = g.layout(w.units(tokens),max_width=1400)[0]['shapes']
word = c.svg(shapes,pad=c.PEN/2)
decoded = w.read_svg(word,fragment=True)['tokens']
assert decoded==tokens
save(out/'noema.svg',word+'\n')
save(out/'declaration.svg',c.svg(c.from_svg(raw),pad=c.PEN/2)+'\n')
save(out/'noema.noema',source)
save(out/'README.txt',f'Noema is assigned the local proper name {symbol}.\nRoots: {" · ".join(roots)}. Result type: individual; no arguments.\nThis is a new local declaration, not an existing official catalogue spelling or a phonetic transcription.\nBoth the declaration and visible spelling were decoded from SVG and checked. Not used by the website.\n')
save(out/'evidence.json',json.dumps({'symbol':symbol,'roots':roots,'local_declaration':True,'word_svg_decoded':True,'declaration_svg_decoded':True,'sha256':hashlib.sha256(word.encode()).hexdigest()},indent=2)+'\n')
print('Generated cropped hero, 30 aligned roots, and output/noema-name/noema.svg')
