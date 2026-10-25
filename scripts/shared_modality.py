"""Reusable candidate/ability definitions, preserving original declarations."""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

from noema.constructed import parse
from noema.constructed_discourse import normalize_document

ROOT=Path(__file__).resolve().parents[1]
ABILITY_SOURCE='examples/v013/contextual-ability.noema'
MODAL_SOURCE='examples/v014/derivation-modalities.noema'
LIBRARY='examples/v016/shared-modality-v1.noema'
ABILITY_NAMES=dict(zip(('xa','xb','xc','xd','xe','xf','xg'),(
    'assessmentvalid','methodpossible','methodguaranteed','assessedability',
    'methodsassessable','assessmentdecisive','assessedinability')))
MODAL_NAMES={'s5k':'candidatenecessary','s5l':'necessaryactual'}


def renamed(value,mapping):
    """Rename only declared symbols and their references, never binders."""
    if isinstance(value,list): return [renamed(v,mapping) for v in value]
    if not isinstance(value,dict): return value
    result={k:renamed(v,mapping) for k,v in value.items()}
    if value.get('kind') in ('primitive','definition'): result['name']=mapping.get(value['name'],value['name'])
    if value.get('kind') in ('call','function_ref'): result['symbol']=mapping.get(value['symbol'],value['symbol'])
    return result


def v(name): return dict(kind='variable',name=name)
def app(name,*args): return dict(kind='apply',function=v(name),arguments=list(args))
def call(name,*args): return dict(kind='call',symbol=name,arguments=list(args))
def op(kind,*args): return dict(kind=kind,arguments=list(args))
def quant(kind,name,body): return dict(kind=kind,variable=name,sort='situation',body=body)


@lru_cache(maxsize=1)
def composed():
    # No composer import chains; read the preserved small standalone modules.
    modal=parse((ROOT/MODAL_SOURCE).read_text(encoding='utf-8'))
    ability=parse((ROOT/ABILITY_SOURCE).read_text(encoding='utf-8'))
    declarations=[renamed(d,MODAL_NAMES) for d in modal['declarations'] if d['name'] in MODAL_NAMES]
    template=declarations[0]
    content,context,selector=[p['name'] for p in template['parameters']]
    world='world'
    selected=app(selector,v(content),v(context),v(world))
    truth=dict(kind='evaluate',content=v(content),situation=v(world))
    exists=quant('exists',world,selected)
    possible=quant('exists',world,op('and',selected,truth))
    rejected=quant('exists',world,op('and',selected,op('not',truth)))
    added={
        'candidateexists':exists,
        'candidateempty':op('not',exists),
        'candidatepossible':possible,
        'candidateexcluded':op('and',exists,quant('forall',world,op('implies',selected,op('not',truth)))),
        'candidatecontingent':op('and',possible,rejected),
    }
    for name,body in added.items():
        declarations.append(dict(kind='definition',name=name,parameters=deepcopy(template['parameters']),result='truth',body=body))
    declarations.extend(renamed(d,ABILITY_NAMES) for d in ability['declarations'])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))


@lru_cache(maxsize=1)
def active_catalogs():
    from noema.meaning_catalog import load_catalog
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))
    return {work:load_catalog(ROOT,row['meaning_basis'],document_path=row['document'])
            for work,row in index['works'].items()}


def inventory(catalogs):
    """Evidence rows only: same spelling or signature does not merge meanings."""
    a,b=catalogs.values()
    common=set(a.entries)&set(b.entries)
    result=[]
    for n in a.entries:
        if n not in common: continue
        x,y=a.entries[n],b.entries[n]
        if x['declaration']!=y['declaration']: continue
        meanings=[x['meaning_ja'],y['meaning_ja']]
        # This exact prefix in the source labels the current spelling. Keep
        # the original texts in evidence and record this metadata-only step.
        plain=[m.removeprefix('[current の記号名] ') for m in meanings]
        result.append(dict(symbol=n,kind=x['kind'],meanings=meanings,
            declaration_identical=True,meaning_text_equal_after_label=plain[0]==plain[1],
            decision='same_convention_candidate' if plain[0]==plain[1] else 'keep_distinct_meanings',
            origins=[dict(work=work,basis=c.entries[n]['meaning_basis'],document=c.entries[n]['declaration_document'])
                     for work,c in catalogs.items()]))
    return result
