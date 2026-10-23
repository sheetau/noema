"""Check exact author-reference binding without inferring a physical presenter."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse, format_graph
from noema.constructed import parse as parse_constructed
from noema.finite_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import digest, validate_hashes
from scripts.compose_einstein_author_credit import (
    ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS, LIBRARY,
    LIBRARY_BASIS, INDEX, PRIMITIVES, MEANINGS, build, read)

SOURCE = 'data/einstein-opening-source-reading-v1.json'
INVENTORY = 'artifacts/written-units-v1/einstein-1905.json'
DOC = 'docs/einstein-opening-v1.md'
REPORT = 'reports/einstein-author-credit-v1.json'


def record(path):
    return json.loads(read(path))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def source_record():
    units = record(INVENTORY)['units'][:3]
    retrieval = record('artifacts/einstein-opening-v1/retrieval.json')
    pins = {r['path']:r['sha256'] for r in retrieval['sources']}
    pins.update({p:digest((ROOT/p).read_bytes()) for p in (
        INVENTORY, 'artifacts/einstein-opening-v1/retrieval.json',
        'artifacts/written-sources-v1/einstein-1905.html', DOC)})
    text = units[2]['text']
    starts = [text.index(s) for s in ('Daß die', 'Man denke', 'Das beobachtbare',
        'Bewegt sich nämlich', 'Ruht aber')]
    ends = [p-1 for p in starts[1:]]+[len(text)]
    return dict(version='einstein-opening-source-reading-v1', reviewer='assistant_visual_and_text_review',
        page='891', image='artifacts/einstein-opening-v1/page-891.jpg',
        source_units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],
            range=[0,len(u['text'])], facsimile_text_collated=True) for u in units],
        body_sentence_ranges=[dict(range=[a,b],text=text[a:b]) for a,b in zip(starts,ends)],
        observations=[
            '原刊画像の表題・著者表示・第一段落を視認し、固定転記の全体と照合した。',
            '原刊の表題前の3.は誌面内の配列番号で、固定単位u0001に含まれない。番号の存在を記録し、表題の主題内容に加えない。',
            'u0002はvon A. Einstein.であり、A.の展開、表示の真正性、自筆性、実際の提示者を補わない。',
            'u0003は原刊の一段落。行末分綴と改行を除き、五文の語句・否定・留保・挿入部・括弧条件が転記に保持される。',
            'u0004の途中は同じ頁の下部にあるが、今回はu0004全体の原刊照合を完了扱いしない。'],
        semantic_completion={'einstein-1905:u0001':False,'einstein-1905:u0002':'separate_review',
            'einstein-1905:u0003':False}, source_sha256=pins)


def forbidden(*args):
    raise ValueError('Unspecified author-credit input')


def evaluate(doc, values):
    return [r['value'] for r in evaluate_document(doc, individuals=('act','name','author','paper','other'),
        situations=('front','other'), primitives=values, max_steps=10000,
        memoize_definitions=False, memoize_expressions=False)]


def model(doc, bits=(True,True,True), mutate=None, unknown=None, same_name=False):
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(rd=lambda:'author', eird=lambda:'author' if same_name else 'name',
        eire=lambda:'act', eirf=lambda:'paper', eirg=lambda:'front')
    expected={'eira':('act','front'), 'eirb':('act','author' if same_name else 'name','author','front'),
        'eirc':('act','paper','author','front')}
    for i,(name,row) in enumerate(expected.items()):
        if mutate and mutate[0]==name:
            row=tuple('other' if j==mutate[1] else x for j,x in enumerate(row))
        def callback(*args, name=name, row=row, bit=bits[i]):
            if name==unknown:raise ValueError('Unknown '+name)
            return bit and args==row
        values[name]=callback
    return values


@lru_cache(None)
def finite_checks():
    cases=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        for bits in product((False,True),repeat=3):
            assert evaluate(doc,model(doc,bits))==[all(bits)];cases+=1
        for name,arity in (('eira',2),('eirb',4),('eirc',4)):
            for slot in range(arity):
                assert evaluate(doc,model(doc,mutate=(name,slot)))==[False];cases+=1
            try:evaluate(doc,model(doc,unknown=name))
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError('Unknown input accepted: '+name)
        assert evaluate(doc,model(doc,same_name=True))==[False];cases+=1
    return dict(cases=cases, unknown_inputs_rejected=6, full_and_core_native_bodies=True,
        original_206_assertions_not_evaluated=True, presenter_or_authenticity_not_requested=True,
        limitations='有限入力で新しい合成本体と全引数の接続を検査する。表示の歴史的真実性や原文との意味同値を計算しない。')


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    c=catalog();old=load_catalog(ROOT,PARENT_BASIS)
    assert c.document['statements'][:-1]==old.document['statements']
    assert c.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    for n,e in old.entries.items():
        assert c.entries[n]['meaning_ja']==e['meaning_ja']
    source=parse_constructed(read(LIBRARY))['declarations'][0]
    target=deepcopy(c.entries['eiaa']['declaration']);target['name']='rqqx'
    assert target==source
    assert MEANINGS['eiaa']==record(LIBRARY_BASIS)['definitions']['rqqx']
    annotation=load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert annotation.find('A. Einstein')['matches'][0]['symbol']=='eird'
    core=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(core,style)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==core
    reading=record(SOURCE);assert reading==source_record();validate_hashes(ROOT,reading['source_sha256'])
    return dict(previous_statements_preserved=INDEX, previous_declarations_and_meanings_preserved=True,
        new_definitions=2,new_primitives=7,generic_body_and_meaning_preserved=True,
        core_roundtrips=['compact','full','v2'],annotation_on_name_not_person=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,encoded(source_record()))


def build_report():
    finite=finite_checks();structure=structure_checks()
    unit=record(INVENTORY)['units'][1]
    paths=set(build())|set(catalog().source_sha256)|set(record(SOURCE)['source_sha256'])|{
        SOURCE,LIBRARY,LIBRARY_BASIS,PARENT,PARENT_BASIS,DOC,INVENTORY,
        'scripts/compose_einstein_author_credit.py','scripts/check_einstein_author_credit.py',
        'tests/test_einstein_author_credit.py'}
    return dict(status='einstein_author_credit_checked',document=FULL,finite=finite,structure=structure,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            range=[0,len(unit['text'])],source=unit['text'],definitions=list(MEANINGS),
            status='author_credit_composed_whole_unit_judgment_separate')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
