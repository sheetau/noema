"""Publish aliases in geometry, then decode later declarations and statements."""
from copy import deepcopy
from functools import lru_cache
import hashlib,json
from scripts import kant_public_fragment as writing,kant_incremental_dictionary as document
from scripts import check_kant_incremental_dictionary as prior
from scripts import check_kant_item_rows as prior_pages
from scripts.kant_item_rows import pack_rows,decode_page
from scripts.kant_lexical_context import LexicalContext
from scripts.visible_word_forms import read_symbol
from scripts.kant_page_public_context import ROOT,BRIDGE,semantic_spellings
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-spelling-records'
RUN=ROOT/'.noema-project/runs/kant-spelling-records-v1'
SEMANTIC='data/kant-reference-spellings-v1.json'


def spelling(name,parts):return dict(kind='spelling',name=name,parts=list(parts))


@lru_cache(maxsize=1)
def saved_inputs():
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for path in (DICTIONARY,BRIDGE,SEMANTIC):
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=baseline['source_sha256'][path]:
            raise ValueError('Published spelling input changed: '+path)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))
    specification=json.loads((ROOT/SEMANTIC).read_text(encoding='utf-8'))
    specification['entries']={'wa':specification['entries']['wa']}
    meanings,paths=semantic_spellings(specification,SEMANTIC,bridge,
        lambda path:json.loads((ROOT/path).read_text(encoding='utf-8')))
    wa=bridge['mapping']['wa'];declared=published['declared_spellings'][wa]
    if meanings[wa]!=declared:raise ValueError('Published semantic spelling differs from its meaning basis')
    lexicon=LexicalContext.from_published(published)
    dependencies=lexicon.declarations_for((wa,))
    target=deepcopy(lexicon.declarations[wa])
    seed=dict(document.empty_document(),declarations=[d for d in dependencies if d['name']!=wa])
    if wa in document.Reader(seed).context.words:raise ValueError('Target leaked into shared dependency seed')
    return published,bridge,target,seed,declared,paths


@lru_cache(maxsize=1)
def fixtures():
    p=prior.name('book','town','book','town');q=prior.name('book','town','book','town','book')
    v=prior.variable;book=prior.call('book')
    assertion=lambda body:dict(kind='assert',body=body)
    relation=prior.primitive(p,['individual'],'truth')
    alias=prior.definition(q,[('x','individual')],'truth',prior.invoke(p,v('x')))
    sources=[
        ('short-statement','完全名を公開してから短い綴りで読む',prior.canonical([relation],[assertion(prior.invoke(p,book))]),[(0,spelling(p,['round','town']))]),
        ('later-definition','短い綴りを後続の定義本体でも使う',prior.canonical([relation,alias],[assertion(prior.invoke(q,book))]),
            [(0,spelling(p,['round','town'])),(1,spelling(q,['round','home']))]),
        ('two-spellings','以前の綴りも保持して第二の綴りを読む',prior.canonical([relation],[assertion(prior.invoke(p,book))]),
            [(0,spelling(p,['round','town'])),(0,spelling(p,['round','home']))]),
        ('alias-prefix','短い綴り同士が接頭部を共有する',prior.canonical([prior.primitive(p,[],'individual'),prior.primitive(q,[],'individual')],
            [assertion(prior.logic('equal',prior.invoke(p),prior.invoke(q)))]),
            [(0,spelling(p,['round','town'])),(1,spelling(q,['round','town','book']))]),
    ]
    result=[]
    for key,label,native,aliases in sources:
        records=[]
        for i,decl in enumerate(native['declarations']):records += [decl,*[r for at,r in aliases if at==i]]
        records+=native['statements']
        result.append(dict(key=key,label=label,native=native,records=records,seed=None,spellings=[r for _,r in aliases]))
    published,bridge,target,seed,declared,_=saved_inputs()
    record=spelling(target['name'],declared['parts'])
    native=dict(document.empty_document(),declarations=[target],statements=[assertion(prior.logic('equal',prior.invoke(target['name']),book))])
    result.append(dict(key='saved-semantic',label='既存の著者参照 wa の意味に基づく綴り',native=native,
        records=[target,record,*native['statements']],seed=seed,spellings=[record]))
    native=prior.cases()[-1][2];dg=native['declarations'][0]['name']
    selected=published['selected_spellings'][dg]
    record=spelling(dg,[read_symbol(t,writing.vocabulary()).parts[0] for t in selected])
    result.append(dict(key='saved-subsequence',label='既存の決定的省略綴り dg を公開する',native=native,
        records=[native['declarations'][0],record,native['declarations'][1],*native['statements']],seed=None,spellings=[record]))
    return result


def cases():return [(r['key'],r['label'],dict(native=r['native'],spellings=r['spellings'])) for r in fixtures()]


@lru_cache(maxsize=8)
def checked(index):
    row=fixtures()[index];source=cases()[index][2]
    drawings=document.compile_records(row['records'],seed=row['seed'],multiple=True)
    items=[to_svg(d['shapes']) for d in drawings];svg=to_svg(pack_rows([from_svg(s) for s in items]))
    recovered=decode_page(list(reversed(from_svg(svg))),seed=row['seed'],include_spellings=True)
    if recovered!=source:raise ValueError('Published spelling changed document or mapping')
    return dict(key=row['key'],label=row['label'],source=source,svg=svg,width=max(d['width'] for d in drawings),
        syntax_sha256=syntax_hash(source),item_svgs=items,items=len(items),spellings=len(row['spellings']),
        shared_seed_declarations=0 if row['seed'] is None else len(row['seed']['declarations']),
        item_circles=[measure(s)['circles'] for s in items],circles=sum(measure(s)['circles'] for s in items),
        branches=sum(measure(s)['branches'] for s in items),branch_limits=[d.get('branch_limits',[]) for d in drawings],
        unbranched_paths=[d.get('unbranched_paths',[]) for d in drawings])


def preserved_count():return len(prior.previous.preserved_rows())+len(prior_pages.cases())


def preserved(index):
    count=len(prior.previous.preserved_rows())
    if index<count:return prior.previous.preserved(index)
    row=prior_pages.checked(index-count)
    return dict(svg=row['original_svg'],syntax_sha256=row['syntax_sha256'])


def pins():
    result=prior_pages.pins()
    names={'scripts/check_kant_spelling_records.py','tests/test_kant_spelling_records.py','docs/kant-spelling-records.md',SEMANTIC,
           'reports/kant-item-rows-v1.json',*saved_inputs()[-1]}
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,preserved_count=preserved_count(),
        schema='kant-spelling-records-1',version=writing.VERSION,title='省略綴りの対応を図形から読む',
        intro='綴り記録を読んでから後続の文に使います。元の名前・型・本体は維持します。',
        limits=['Public seed dependencies are explicit; target spelling records are not supplied to the reader',
                'One item per row; multiple-item rows, wrapping and final visual approval remain',
                'Saved wa definition is pinned as published; pure source-name substitution is not claimed'])


def build_report():return report(OUT,pins)
