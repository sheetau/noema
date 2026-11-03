"""Apply a scoped type contraction only to the changed saved declaration."""
from functools import lru_cache
from unittest.mock import patch
import hashlib,json,time
from scripts import kant_public_fragment as writing,kant_type_grammar as expanded
from scripts import check_kant_saved_declarations as saved
from scripts.check_kant_declarations import reader_without_target
from scripts.check_kant_type_references import pins as prior_pins
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-type-reference-declaration'
RUN=ROOT/'.noema-project/runs/kant-type-reference-declaration-v1'
BASELINE='reports/kant-saved-declarations-v1.json'


@lru_cache(maxsize=1)
def records():
    published,ds=saved.inputs();prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'));rows=[]
    for key,source in zip(saved.ORIGINALS,ds):
        old=next(r for r in prior['diagnostics'] if r['key']==key)
        if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved native declaration changed')
        path='output/kant-saved-declarations/'+key+'.svg'
        raw=(ROOT/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=prior['source_sha256'][path]:raise ValueError('Saved declaration ink changed')
        with use_context(LexicalContext.from_published(published)):
            current=writing.events(source,multiple=True)
            with patch.object(writing,'type_tokens',expanded.type_tokens),patch.object(writing,'type_list_tokens',expanded.type_list_tokens):
                previous=writing.events(source,multiple=True)
        rows.append(dict(key=key,source=source,published=published,changed=current!=previous,old=old,path=path,
            previous_events=writing.event_count(previous),current_events=writing.event_count(current)))
    return rows


def cases():return [(r['key'],'保存宣言 '+r['key']+'：型の反復を短縮する',r['source']) for r in records() if r['changed']]


@lru_cache(maxsize=5)
def checked(index):
    row=[r for r in records() if r['changed']][index];source=row['source'];published=row['published'];key,label,_=cases()[index]
    start=time.perf_counter()
    drawing=writing.compile_declaration(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    if writing.decode_declaration(list(reversed(from_svg(svg))),lexicon=reader_without_target(published,source['name']))!=source:
        raise ValueError('Contracted declaration changed native syntax')
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],seconds=time.perf_counter()-start,
        syntax_sha256=syntax_hash(source),target_body_and_signature_absent=True,previous_svg=row['path'],
        previous_width=row['old']['width'],previous_circles=row['old']['circles'],previous_branches=row['old']['branches'],
        previous_events=row['previous_events'],current_events=row['current_events'],
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (BASELINE,'reports/kant-type-references-v2.json',
                 'scripts/check_kant_type_reference_declaration.py','tests/test_kant_type_reference_declaration.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-type-reference-declaration-1',version=writing.VERSION,title='実宣言の反復型を短く書く',
        intro='変更のある宣言だけ再描画し、同じ名前・型・本体を回収します。',
        limits=['Changed declarations among five saved examples only',
                'Unchanged streams retained; no broad performance claim or visual freeze'])


def build_report():
    return dict(report(OUT,pins),unchanged_event_streams=[r['key'] for r in records() if not r['changed']])
