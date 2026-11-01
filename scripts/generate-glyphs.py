"""Render a bounded LP sample set using the frozen Noema renderer, read-only.

Usage: node scripts/export-samples.mjs; python -X utf8 scripts/generate-glyphs.py
No corpus jobs, ledger writes, or generation inside the language checkout.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NOEMA = Path(os.environ.get('NOEMA_SOURCE', str(ROOT.parent / 'noema'))).resolve()
sys.path.insert(0, str(NOEMA))
from noema.constructed import parse, format_graph
from scripts.contextual_opening_script import compile_expression, pack_lines, STROKE

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

freeze = json.loads((NOEMA / 'data/writing-freeze-v1.json').read_text(encoding='utf-8'))
pinned = {**freeze['source_sha256'], **freeze['output_sha256']}
for name, expected in pinned.items():
    assert sha(NOEMA / name) == expected, f'Frozen source changed: {name}'

samples = json.loads((ROOT / 'src/samples.json').read_text(encoding='utf-8'))
manifest = {'renderer': freeze['version'], 'source_hashes': pinned, 'samples': {},
            'limits': 'Authored readings; syntax, geometry and AST restoration checked. Not independent optical decoding or automatic semantic equivalence.'}

def svg(compiled, title):
    rows = pack_lines(compiled, 1000, .8)
    width = min(1000, max((r['end']-r['start'])*.8 for r in rows)) + 40
    height = len(rows)*126 + 20
    elements = []
    for index, row in enumerate(rows):
        dx, dy, scale = 20, 40 + index*126, .8
        for s in row['shapes']:
            if s['kind'] == 'circle':
                elements.append(f'<circle cx="{dx+s["x"]*scale:.4f}" cy="{dy+s["y"]*scale:.4f}" r="{s["r"]*scale:.4f}"/>')
            else:
                elements.append(f'<path d="M{dx+s["x1"]*scale:.4f} {dy+s["y1"]*scale:.4f}L{dx+s["x2"]*scale:.4f} {dy+s["y2"]*scale:.4f}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.4f} {height}" width="{width:.4f}" height="{height}">'
            f'<title>{title}</title><g fill="none" stroke="#e8e8e8" stroke-width="{STROKE*.8}">'
            + ''.join(elements) + '</g></svg>\n')

for i, sample in enumerate(samples, 1):
    print(f'[{i}/{len(samples)}] {sample["id"]}: parse, type, geometry, AST restoration', flush=True)
    doc = parse(sample['source'])
    assert parse(format_graph(doc, 'compact')) == doc
    compiled = compile_expression(doc['statements'][0], reference_order={d['name']:i for i,d in enumerate(doc['declarations'])})
    target = ROOT / 'public/glyphs' / f'{sample["id"]}.svg'
    target.write_text(svg(compiled, f'Noema — {sample["id"]}'), encoding='utf-8', newline='\n')
    (ROOT / 'public/examples' / f'{sample["id"]}.noema').write_text(sample['source'], encoding='utf-8', newline='\n')
    manifest['samples'][sample['id']] = {'svg_sha256': sha(target), 'source_sha256': hashlib.sha256(sample['source'].encode()).hexdigest(),
        'opening': compiled['opening']['family'], 'groups':len(compiled['groups']), 'syntax_roundtrip':True, 'geometry':True}

# Reuse the exact frozen page geometry. Only ink/background colors change.
page = (NOEMA / 'output/kant-page-script-v3/kant-page.svg').read_text(encoding='utf-8')
page = page.replace('#203438', '#e8e8e8').replace('#fffffe', '#000000')
(ROOT / 'public/glyphs/kant-page.svg').write_text(page, encoding='utf-8', newline='\n')
tree = ET.fromstring(page)
tree.set('viewBox', '80 75 1440 340')
tree.set('width', '1440')
tree.set('height', '340')
ET.register_namespace('', 'http://www.w3.org/2000/svg')
(ROOT / 'public/glyphs/kant-opening.svg').write_text(ET.tostring(tree, encoding='unicode')+'\n', encoding='utf-8', newline='\n')
for name, expected in pinned.items():
    assert sha(NOEMA / name) == expected, f'Frozen source changed during generation: {name}'
(ROOT / 'public/glyphs/provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
print('Done. All frozen source/output hashes unchanged.', flush=True)
