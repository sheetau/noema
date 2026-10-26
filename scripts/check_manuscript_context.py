"""Typed context audit and two reversible manuscript context templates."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json

from noema.meaning_catalog import load_catalog, _references
from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document, FunctionValue
from scripts.context_abstraction import abstract, instantiate
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_word_forms import Word, symbol
from scripts.visible_collection import compile_collection, decode_collection
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.visible_lexical_script import require
from scripts.shared_modality import call, renamed

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'examples/v016/manuscript-context-templates-v1.noema'
BASIS = 'data/manuscript-context-interfaces-v1.json'
OUT = ROOT / 'output/manuscript-context-v1'
LABEL = Word('proper', ('book', 'aki', 'inside'))
SPECS = {
    'kant-1784': dict(target='r2em', statement=12,
        forms={'r2em': ('book', 'above', 'inside', 'book')},
        roles={'ue': 'text_order', 'hzzq': 'first_sentence', 'hzzr': 'second_sentence', 'wh': 'presentation_context'}),
    'einstein-1905': dict(target='eiab', statement=42,
        forms={'eiaa': ('book', 'aki', 'give', 'book'), 'eiab': ('book', 'aki', 'give', 'inside')},
        roles={'rd': 'author', 'eird': 'designation', 'eire': 'presentation', 'eirf': 'document',
               'eirg': 'presentation_context', 'eira': 'presentation_holds',
               'eirb': 'designation_applies', 'eirc': 'author_display_role'})}


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def core():
    return SensesVocabulary()


@lru_cache(maxsize=1)
def catalogs():
    state = read('data/work-state.json'); index = read(state['review_index'])
    return {w: load_catalog(ROOT, s['meaning_basis'], document_path=s['document']) for w, s in index['works'].items()}


def slice_for(work):
    c = catalogs()[work]; spec = SPECS[work]; by_name = {d['name']: d for d in c.document['declarations']}
    selected = set()
    def visit(n):
        if n in selected:
            return
        selected.add(n)
        for dep in _references(by_name[n].get('body')):
            visit(dep)
    visit(spec['target'])
    statement = c.document['statements'][spec['statement']]
    require(statement == dict(kind='assert', body=call(spec['target'])), 'Source assertion selection changed')
    doc = dict(schema_version='0.16', lexicon_version='0.16',
               declarations=[deepcopy(d) for d in c.document['declarations'] if d['name'] in selected], statements=[])
    checked = normalize_document(doc)
    require(checked['declarations'] == doc['declarations'], 'Native header adaptation changes source payload')
    return checked


def names_for(work):
    names = {n: symbol(Word('compound', parts), core()) for n, parts in SPECS[work]['forms'].items()}
    require(not (set(names.values()) & set(core()._by_symbol)), 'Local spelling shadows a common word')
    return names


@lru_cache(maxsize=2)
def template(work):
    s = SPECS[work]
    return abstract(slice_for(work), s['target'], names_for(work), s['roles'])


@lru_cache(maxsize=1)
def document():
    return normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=[d for w in SPECS for d in template(w)[0]['declarations']], statements=[]))


def interfaces():
    result = {}
    for work, spec in SPECS.items():
        c = catalogs()[work]; doc, bindings = template(work)
        restored = instantiate(doc, bindings, slice_for(work), spec['target'], names_for(work))
        require(restored == slice_for(work), 'Context substitution does not recover the original slice')
        result[work] = dict(document=c.document_path, statement_index=spec['statement'], target=spec['target'],
            visible_names=names_for(work), required_context=[dict(**b, meaning=c.entries[b['source_symbol']]['meaning_ja'],
                meaning_basis=c.entries[b['source_symbol']]['meaning_basis']) for b in bindings],
            original_assertion=c.document['statements'][spec['statement']], original_declarations=slice_for(work)['declarations'],
            reconstituted_source_exact=True, context_resolved=False, source_assertion_migrated=False)
    return result


def inventory():
    result = {}
    for work, c in catalogs().items():
        zero = [d for d in c.document['declarations'] if d['kind'] == 'primitive' and not d['parameters']]
        quoted = set()
        def scan(node):
            if isinstance(node, dict):
                if node.get('kind') == 'quote':
                    quoted.update(_references(node))
                for value in node.values():
                    scan(value)
            elif isinstance(node, list):
                for value in node:
                    scan(value)
        scan(c.document)
        rows = [dict(symbol=d['name'], result=d['result'], quoted_directly=d['name'] in quoted,
                     meaning=c.entries[d['name']]['meaning_ja'], meaning_basis=c.entries[d['name']]['meaning_basis']) for d in zero]
        result[work] = dict(zero_argument_primitives=len(zero), result_kinds=dict(sorted(Counter(
            d['result'] if isinstance(d['result'], str) else d['result']['kind'] for d in zero).items())),
            quoted_directly=sum(r['quoted_directly'] for r in rows), entries=rows)
    return result


def original_value(work, values):
    doc = slice_for(work); handlers = {}
    for d in doc['declarations']:
        if d['kind'] == 'primitive':
            value = values[d['name']]
            handlers[d['name']] = value if d['parameters'] else lambda value=value: value
    doc['statements'] = [dict(kind='ask', body=call(SPECS[work]['target']))]
    return evaluate_document(doc, individuals=('x', 'y'), situations=('now', 'other'), primitives=handlers)[0]['value']


def template_value(work, values, doc=None):
    doc = deepcopy(doc if doc is not None else template(work)[0]); handlers = {}; args = []
    # Private diagnostic declarations supply values. These are not published
    # new words and do not purport to identify the actual manuscript referents.
    by_name = {d['name']: d for d in slice_for(work)['declarations']}
    for i, record in enumerate(template(work)[1]):
        name = 'diagnostic' + chr(97 + i); d = by_name[record['source_symbol']]; value = values[d['name']]
        if d['parameters']:
            value = FunctionValue(tuple(d['parameters']), d['result'], value)
        doc['declarations'].append(dict(kind='primitive', name=name, parameters=[], result=record['sort']))
        handlers[name] = lambda value=value: value; args.append(call(name))
    doc['statements'] = [dict(kind='ask', body=call(names_for(work)[SPECS[work]['target']], *args))]
    return evaluate_document(doc, individuals=('x', 'y'), situations=('now', 'other'), primitives=handlers)[0]['value']


def cases():
    rows = []
    # Every input position is distinguished using only two values per sort.
    for a, b, world, present in product(('x', 'y'), ('x', 'y'), ('now', 'other'), (False, True)):
        values = dict(hzzq=a, hzzr=b, wh=world, ue=lambda x, y, s, p=present: p and (x,y,s)==('x','y','now'))
        rows.append(('kant-1784', f'{a}/{b}/{world}/{present}', values, present and (a,b,world)==('x','y','now')))
    for same, mask in product((False, True), range(8)):
        values = dict(rd='y', eird='y' if same else 'x', eire='x', eirf='y', eirg='now',
            eira=lambda p,s,m=mask: bool(m&1), eirb=lambda p,n,a,s,m=mask: bool(m&2),
            eirc=lambda p,d,a,s,m=mask: bool(m&4))
        rows.append(('einstein-1905', f'name-person-same={same}/mask={mask}', values, not same and mask==7))
    base = dict(rd='y', eird='x', eire='x', eirf='y', eirg='now',
        eira=lambda p,s: (p,s)==('x','now'), eirb=lambda p,n,a,s: (p,n,a,s)==('x','x','y','now'),
        eirc=lambda p,d,a,s: (p,d,a,s)==('x','y','y','now'))
    rows.append(('einstein-1905', 'all-roles-match', base, True))
    for name in ('rd','eird','eire','eirf','eirg'):
        values = dict(base); values[name] = ('other' if name=='eirg' else ('y' if base[name]=='x' else 'x'))
        rows.append(('einstein-1905', 'changed-'+name, values, False))
    return rows


@lru_cache(maxsize=1)
def compiled():
    return compile_collection(document(), LABEL, core(), payload=768)


@lru_cache(maxsize=1)
def restored():
    result = decode_collection([from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))], core())
    require(result['document'] == document(), 'Visible contextual templates differ')
    return result


def diagnostics():
    rows = []
    for work, label, values, wanted in cases():
        old = original_value(work, values); new = template_value(work, values, restored()['document'])
        require(old == new == wanted, 'Context binding mismatch: ' + work + '/' + label)
        rows.append(dict(work=work, case=label, original=old, template=new, expected=wanted))
    return rows


def write_once(path, value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    path = ROOT / path; require(not path.exists() or path.read_text(encoding='utf-8') == text, 'Existing artifact differs')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding='utf-8', newline='\n')


def prepare():
    write_once(SOURCE, format_graph(document()) + '\n'); write_once(BASIS, interfaces())
    write_once('output/manuscript-context-v1/inventory.json', inventory())
    for i, page in enumerate(compiled()['pages']):
        write_once(OUT / ('page-' + str(i+1).zfill(5) + '.svg'), to_svg(page['shapes']))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_report():
    result = restored(); inv = inventory(); actual = diagnostics()
    require(parse((ROOT/SOURCE).read_text(encoding='utf-8')) == document(), 'Native template differs')
    require(read(BASIS) == interfaces(), 'Interface evidence differs')
    require(read('output/manuscript-context-v1/inventory.json') == inv, 'Context inventory differs')
    previous = 'reports/visible-specialist-library-v1.json'; prior = read(previous)
    pins = prior['source_sha256'] | prior['artifact_sha256']
    for path, stamp in pins.items():
        require(digest(path) == stamp, 'Prior evidence changed: '+path)
    paths = {*pins, previous, SOURCE, BASIS, 'scripts/context_abstraction.py', 'scripts/check_manuscript_context.py',
             'tests/test_context_abstraction.py', 'docs/manuscript-context-v1.md', 'data/work-state.json'}
    for c in catalogs().values():
        paths.update(c.source_sha256)
    return dict(schema='noema-manuscript-context-evidence-1',
        inventory={w:{k:v for k,v in row.items() if k!='entries'} for w,row in inv.items()},
        source_slices={w:dict(statement=SPECS[w]['statement'],declarations=len(slice_for(w)['declarations']),
            context_inputs=len(template(w)[1]),exact_reinstantiation=True) for w in SPECS},
        new_common_words=0, new_primitives=0, local_definitions=3, source_assertions_migrated=0,
        pages=result['pages'],volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
        binding_diagnostics=actual, independent_human_reading=False,
        source_sha256={p:digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT)) for p in sorted(OUT.iterdir()) if p.is_file()},
        limits=['These are conditional templates with unresolved contextual inputs, not migrations of the source assertions.',
                'Quoted contextual names are rejected; substitution must not collapse quotation identity.',
                'Higher-order zero-argument constants are not automatically individual names or finite scalar values.',
                'Small distinguishing models diagnose binding; they are not an exhaustive proof over all relational interpretations.'])
