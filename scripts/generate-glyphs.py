"""Bounded LP export with v7; resumable, no writes to the core checkout."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
NOEMA = Path(os.environ.get('NOEMA_SOURCE', ROOT.parent / 'noema')).resolve()
sys.path.insert(0, str(NOEMA))
from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from scripts.concept2_writing import WritingReader
from scripts.two_work_repair import RepairWritingReader
from scripts.two_work_assemble import renamed
from scripts.two_work_batch import render_record
from scripts.concept2_document import full_name
from scripts import concept2_composition as c

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    temp.replace(path)

def write_text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')

freeze = json.loads((NOEMA / 'data/writing-freeze-v2.json').read_text(encoding='utf-8'))
pins = {**freeze['source_sha256'], **freeze['output_sha256']}
retired_evidence = {name: value for name, value in pins.items() if not (NOEMA / name).exists()}
assert all(name.startswith('output/') for name in retired_evidence), 'A required source is missing'
pins = {name: value for name, value in pins.items() if name not in retired_evidence}
for name, expected in pins.items():
    assert sha(NOEMA / name) == expected, f'Frozen source changed: {name}'
for name in ['scripts/two_work_repair.py', 'scripts/two_work_batch.py', 'scripts/two_work_assemble.py']:
    pins[name] = sha(NOEMA / name)
samples = json.loads((ROOT / 'src/samples.json').read_text(encoding='utf-8'))
catalog = json.loads((NOEMA / 'data/general-language-catalog-v2.json').read_text(encoding='utf-8'))
occupied = {item['symbol'] for item in catalog['entries'].values()}
labels = sorted({d['name'] for sample in samples for d in parse(sample['source'])['declarations']})
# Local root spellings are explicitly declared, not catalogue entries or row IDs.
mapping = {}; spellings = {}
for label, root in zip(labels, c.ROOT_NAMES, strict=True):
    parts = ['book', 'book', root]
    name = full_name([c.old.root_symbol(p) for p in parts])
    assert name not in occupied
    mapping[label] = name; spellings[label] = parts
manifest = dict(renderer=freeze['adopted_alphabet'], edition='1.0', source_hashes=pins, retired_evidence=retired_evidence, samples={},
    limits='Authored readings with locally declared vocabulary. Exact SVG-to-syntax recovery is not a proof of natural-language equivalence.')
cache = ROOT / 'output/glyph-cache'
cache.mkdir(parents=True, exist_ok=True)
identity = dict(pins=pins, generator=sha(__file__), mapping=mapping, width=1400)
for index, sample in enumerate(samples, 1):
    key = digest(dict(sample=sample, implementation=identity))
    checkpoint = cache / f'{sample["id"]}.json'
    prior = json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {}
    if prior.get('key') == key and all((ROOT / p).exists() and sha(ROOT / p) == h for p, h in prior['files'].items()):
        manifest['samples'][sample['id']] = prior['result']
        print(f'[{index}/{len(samples)}] {sample["id"]}: verified cache', flush=True)
        continue
    original = parse(sample['source'])
    visible = normalize_document(renamed(original, mapping))
    writer = RepairWritingReader(); reader = WritingReader(); files = {}; declarations = []
    records = visible['declarations'] + visible['statements']
    for number, record in enumerate(records):
        print(f'[{index}/{len(samples)}] {sample["id"]}: SVG decode {number + 1}/{len(records)}', flush=True)
        canonical = writer.canonical_record(record)
        tokens = writer.encode_record(canonical)
        svg, rows = render_record(writer, tokens, 1400)
        # Tight viewport, retaining relative geometry and physical line spacing.
        svg = c.svg(c.from_svg(svg), pad=24)
        restored = reader.read_page(svg)['statements']
        assert restored == [canonical], (sample['id'], number, 'SVG geometry mismatch')
        writer.register(canonical)
        is_declaration = number < len(visible['declarations'])
        name = f'examples/{sample["id"]}/declaration-{number + 1}.svg' if is_declaration else f'glyphs/{sample["id"]}.svg'
        target = ROOT / 'public' / name
        write_text(target, svg + '\n')
        files[target.relative_to(ROOT).as_posix()] = sha(target)
        if is_declaration:
            label = original['declarations'][number]['name']
            declarations.append(dict(label=label, symbol=mapping[label], roots=spellings[label], svg=name, svg_sha256=sha(target)))
    assert reader.result()['native'] == visible, sample['id']
    native = format_graph(visible, 'compact') + '\n'
    for suffix, source in [('', sample['source']), ('-visible', native)]:
        target = ROOT / 'public/examples' / f'{sample["id"]}{suffix}.noema'
        write_text(target, source)
        files[target.relative_to(ROOT).as_posix()] = sha(target)
    result = dict(svg_sha256=sha(ROOT / 'public/glyphs' / f'{sample["id"]}.svg'),
        source_sha256=hashlib.sha256(sample['source'].encode()).hexdigest(),
        visible_source_sha256=hashlib.sha256(native.encode()).hexdigest(),
        declarations=declarations, visible_decode=True, records=len(records))
    manifest['samples'][sample['id']] = result
    write_json(checkpoint, dict(key=key, result=result, files=files))
report = json.loads((NOEMA / 'output/noema-writing-v2/report.json').read_text(encoding='utf-8'))
manifest['specimens'] = []
for paragraph in report['paragraphs']:
    source = NOEMA / 'output/noema-writing-v2' / paragraph['svg']
    assert sha(source) == paragraph['sha256']
    target = ROOT / 'public/glyphs' / ('kant-' + paragraph['svg'])
    target.write_bytes(source.read_bytes())
    manifest['specimens'].append(dict(file=target.name, sha256=sha(target)))
writer = WritingReader()
alphabet = []
for name in c.ROOT_NAMES:
    path = ROOT / 'public/glyphs/alphabet' / f'{name}.svg'
    write_text(path, c.svg(writer.forms[('root', name)]['shapes']) + '\n')
    alphabet.append(dict(name=name, svg=f'glyphs/alphabet/{name}.svg', sha256=sha(path)))
manifest['alphabet'] = alphabet
for name, expected in pins.items():
    assert sha(NOEMA / name) == expected, f'Frozen source changed during generation: {name}'
write_json(ROOT / 'public/glyphs/provenance.json', manifest)
print('Done: all 15 examples visibly decoded. Core files unchanged.', flush=True)
