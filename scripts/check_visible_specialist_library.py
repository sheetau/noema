"""Publish mathematics as optional definitions readable with edition twelve."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_library_linker import link
from scripts.visible_collection import compile_collection, decode_collection
from scripts.visible_word_forms import Word, symbol
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.visible_lexical_script import require
from scripts.shared_modality import call, op, renamed
from scripts.shared_reference import definition
from scripts.shared_focus import quote

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = 'examples/v016/visible-mathematics-library-v1.noema'
SOURCE = 'examples/v016/visible-specialist-document-v1.noema'
OUT = ROOT / 'output/visible-specialist-library-v1'
LABEL = Word('proper', ('round', 'book', 'inside'))


@lru_cache(maxsize=1)
def core():
    return SensesVocabulary()


@lru_cache(maxsize=1)
def authoring_vocabulary():
    return VectorsVocabulary()


def specialist_names():
    return set(authoring_vocabulary()._words) - set(core()._words)


@lru_cache(maxsize=1)
def library():
    # Published spellings and original typed bodies; no new vocabulary edition.
    return normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=authoring_vocabulary().imports(specialist_names()), statements=[]))


def aliases():
    return [symbol(Word('compound', ('round', 'inside', 'book', x)), core()) for x in ('home', 'town')]


@lru_cache(maxsize=1)
def authored():
    original = parse((ROOT / 'examples/v016/visible-vectors-v1.noema').read_text(encoding='utf-8'))
    statements = renamed(original['statements'], authoring_vocabulary()._symbols)
    a, b = aliases()
    require(all(x not in authoring_vocabulary()._by_symbol for x in (a, b)), 'Example spelling collision')
    declarations = [definition(name, [], 'truth', deepcopy(statements[1]['body'])) for name in (a, b)]
    bodies = [op('equal', call(a), call(b)), op('equal', quote(call(a)), quote(call(b))),
              op('equal', quote(quote(call(a)), 1), quote(quote(call(b)), 1)),
              call(core()._symbols['rationalbelow'], dict(kind='number', numerator=0, denominator=1),
                   dict(kind='number', numerator=1, denominator=1))]
    return dict(schema_version='0.16', lexicon_version='0.16', declarations=declarations,
                statements=statements + [dict(kind='ask', body=b) for b in bodies])


@lru_cache(maxsize=1)
def source():
    return link(authored(), [library()], roots=[authoring_vocabulary()._symbols[n] for n in specialist_names()], vocabulary=core())


@lru_cache(maxsize=1)
def compiled():
    return compile_collection(source(), LABEL, core(), payload=768)


def saved_pages():
    return [from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))]


@lru_cache(maxsize=1)
def restored():
    result = decode_collection(saved_pages(), core())
    require(result['document'] == source(), 'Geometry lost an inline library definition')
    return result


def answers(document):
    handlers = dict(rationalbelow=lambda x, y: x < y, rationaladd=lambda x, y: x + y,
                    rationalnegate=lambda x: -x, rationalmultiply=lambda x, y: x * y)
    declared = {d['name'] for d in document['declarations'] if d['kind'] == 'primitive'}
    primitives = {core()._symbols[n]: f for n, f in handlers.items() if core()._symbols[n] in declared}
    result = []
    for domain in [('x',), ('x', 'y')]:
        values = [r['value'] for r in evaluate_document(document, individuals=domain,
                    situations=('now',), primitives=primitives)]
        require(values == [False, True, False, True, True, False, False, True], 'Questions or quoted identities changed')
        result.append(dict(individuals=list(domain), answers=values))
    return result


def write_once(path, body):
    require(not path.exists() or path.read_text(encoding='utf-8') == body, 'Published artifact differs: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(body, encoding='utf-8', newline='\n')


def prepare():
    write_once(ROOT / LIBRARY, format_graph(library()) + '\n')
    write_once(ROOT / SOURCE, format_graph(source()) + '\n')
    for i, page in enumerate(compiled()['pages']):
        write_once(OUT / ('page-' + str(i + 1).zfill(5) + '.svg'), to_svg(page['shapes']))


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_report():
    result = restored(); doc = result['document']
    require(parse((ROOT / SOURCE).read_text(encoding='utf-8')) == doc, 'Saved document differs')
    require(parse((ROOT / LIBRARY).read_text(encoding='utf-8')) == library(), 'Saved library differs')
    previous_path = 'reports/shared-vectors-v1.json'
    previous = json.loads((ROOT / previous_path).read_text(encoding='utf-8'))
    pins = previous['source_sha256'] | previous['artifact_sha256']
    for path, stamp in pins.items():
        require(digest(path) == stamp, 'Original evidence changed: ' + path)
    paths = {*pins, previous_path, LIBRARY, SOURCE, 'scripts/visible_library_linker.py',
             'scripts/check_visible_specialist_library.py', 'tests/test_visible_library_linker.py',
             'scripts/visible_collection.py', 'docs/visible-specialist-library-v1.md'}
    imports = [d['name'] for d in doc['declarations'] if d['name'] in core()._by_symbol]
    return dict(schema='noema-visible-specialist-library-evidence-1', core_edition=12,
        core_words=375, specialist_definitions=49, authored_definitions=2, new_primitives=0,
        actual_core_imports=len(imports), declarations=len(doc['declarations']), statements=len(doc['statements']),
        pages=result['pages'], volumes=result['volumes'], rows=result['rows'], body_glyphs=result['body_glyphs'],
        finite_question_checks=answers(doc), decoder_requires_specialist_dictionary=False,
        decoder_requires_document_name_table=False, full_manuscript_visible_decoding=False,
        independent_human_reading=False,
        source_sha256={p: digest(p) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix(): digest(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.svg'))},
        limits=['The 375-word core is an existing usable profile, not a proven minimal vocabulary.',
                'Specialist definitions keep their previous spelling, body and contracts; no new semantic review is claimed.',
                'Finite question checks concern sequence length, binding, quoted name identity and rational order, not general real analysis.',
                'Unmapped manuscript primitives still need explicit reusable or contextual meaning contracts before visible publication.'])
