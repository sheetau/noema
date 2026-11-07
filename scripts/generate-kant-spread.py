"""Reflow the adopted four-paragraph specimen, preserving its decoded statements."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOEMA = Path(os.environ.get('NOEMA_SOURCE', ROOT.parent / 'noema')).resolve()
sys.path.insert(0, str(NOEMA))
from scripts import concept2_composition as c, concept2_geometry_v5 as g
from scripts.concept2_writing import WritingReader

OUT = ROOT / 'public/specimens'
CHECK = ROOT / 'output/kant-spread'
OUT.mkdir(exist_ok=True)
CHECK.mkdir(parents=True, exist_ok=True)

def read(path):
    return json.loads((NOEMA / path).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def progress(message):
    print(message, flush=True)
    with (CHECK / 'progress.log').open('a', encoding='utf-8') as log:
        log.write(message + '\n')

report = read('output/noema-writing-v2/report.json')
english_path = NOEMA / 'data/kant-page-english-v2.json'
english = json.loads(english_path.read_text(encoding='utf-8'))
assert len(english['paragraphs']) == len(report['paragraphs']) == 4
for entry in report['paragraphs']:
    assert digest(NOEMA / 'output/noema-writing-v2' / entry['svg']) == entry['sha256']
progress('Loading the frozen dictionary and four-paragraph trace')
native = read('output/concept2-dictionary-v3/dictionary.json')['native']
codec = WritingReader(native)
for item in read('output/concept2-dictionary-v3/report.json')['items']:
    if item['kind'] == 'spelling':
        codec.register(item['recovered'])
trace = read('output/kant-concept2-v9/trace.json')['cases']
all_shapes, paragraphs, y = [], [], 80
for index, paragraph in enumerate(sorted({case['paragraph'] for case in trace})):
    cases = [case for case in trace if case['paragraph'] == paragraph]
    progress(f'Paragraph {index + 1}/4: layout and visible decoding')
    drawings = [g.layout(codec.units([tuple(t) for t in case['tokens']]))[0] for case in cases]
    rows = g.fold(drawings, 4300)
    shapes = []
    for i, row in enumerate(rows):
        shapes += g.move(row['shapes'], 80, 80 + 170 * i)
    svg = c.svg(shapes, width=4460, height=170 * len(rows) + 160)
    decoded = codec.read_page(svg)['statements']
    assert decoded == [case['public'] for case in cases]
    (CHECK / f'paragraph-{index + 1}.svg').write_text(svg, encoding='utf-8', newline='\n')
    all_shapes += g.move(shapes, 0, y - 80)
    paragraphs.append(dict(unit=english['paragraphs'][index]['unit'], rows=len(rows),
        statements=[case['statement'] for case in cases], visible_decode=True))
    y += 170 * len(rows) + 120
pen = c.PEN * 2
svg = c.svg(all_shapes, pad=pen / 2, pen=pen)
viewport = ET.fromstring(svg).attrib
assert codec.read_page(svg)['statements'] == [case['public'] for case in trace]
(OUT / 'kant-four-paragraphs.svg').write_text(svg, encoding='utf-8', newline='\n')
(OUT / 'kant-english.json').write_bytes(english_path.read_bytes())
evidence = dict(scope='Opening four paragraphs, not the entire essay',
    english_source='data/kant-page-english-v2.json', english_sha256=digest(OUT / 'kant-english.json'),
    adopted_source='output/noema-writing-v2/report.json',
    source_paragraphs=report['paragraphs'], paragraphs=paragraphs,
    statement_count=sum(len(p['statements']) for p in paragraphs),
    visible_decode=True, width=float(viewport['width']), height=float(viewport['height']),
    svg_sha256=digest(OUT / 'kant-four-paragraphs.svg'))
(OUT / 'provenance.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
progress(f"Complete: {len(all_shapes)} shapes, {sum(p['rows'] for p in paragraphs)} rows; decoded statements unchanged")
