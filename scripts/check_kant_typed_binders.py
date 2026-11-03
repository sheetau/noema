"""Exact native types and parameter lists recovered from visible geometry."""
from functools import lru_cache
import hashlib
import json

from scripts.check_kant_binding_scope import ROOT, preserved, pins as old_pins
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, logic, quant, variable, quote
from scripts.kant_public_fragment import compile_statement, decode, VERSION
from scripts.kant_type_grammar import BASE_TYPES
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.kant_structural_trial import prepare as prepare_trial, report

OUT=ROOT/'output/kant-typed-binders'
RUN=ROOT/'.noema-project/runs/kant-typed-binders-v1'


def lam(types,slot=0):
    names=('a','b','c','d','e','f')[:len(types)]
    return dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in zip(names,types)],
                body=variable(names[slot]) if names else call('book'))


@lru_cache(maxsize=1)
def cases():
    rows=[]
    types=list(BASE_TYPES)+[
        dict(kind='sequence',element='number'),
        dict(kind='description',result='truth'),
        dict(kind='description',result='individual',rank=2),
        dict(kind='question',parameters=[]),
        dict(kind='question',parameters=['individual','number']),
        dict(kind='function',parameters=[],result='truth'),
        dict(kind='function',parameters=['individual','number'],result='situation'),
        dict(kind='sequence',element=dict(kind='description',result=dict(kind='question',parameters=['number']),rank=1)),
        dict(kind='function',parameters=[dict(kind='sequence',element='number'),
            dict(kind='description',result='truth',rank=2)],result=dict(kind='question',parameters=['message'])),
    ]
    for i,t in enumerate(types):
        body=logic('equal',variable('x'),variable('x'))
        rows.append(('type-'+str(i),'型を保つ束縛 '+json.dumps(t,ensure_ascii=False),
            dict(kind='forall' if i%2==0 else 'exists',variable='x',sort=t,body=body)))
    rows.append(('lambda-empty','引数を持たないlambda',logic('equal',lam([]),lam([]))))
    rows.append(('lambda-single-number','number一引数lambda',logic('equal',lam(['number']),lam(['number']))))
    rows.append(('lambda-two-individual','individual二引数lambda',logic('equal',lam(['individual']*2,0),lam(['individual']*2,1))))
    for slot in range(3):
        f=lam(['individual','number','situation'],slot)
        rows.append(('lambda-slot-'+str(slot),'混合型lambdaの第'+str(slot+1)+'引数',logic('equal',f,f)))
    for i,ts in enumerate((['number','individual','situation'],['situation','number','individual'])):
        f=lam(ts,1)
        rows.append(('lambda-order-'+str(i),'混合型の宣言順 '+str(ts),logic('equal',f,f)))
    f=lam([types[-1],types[-2]],1)
    rows.append(('lambda-recursive','再帰型の複数引数lambda',logic('equal',f,f)))
    f=lam(['number','individual'],0)
    rows.append(('quote-lambda','引用ごとに型と束縛を復元',logic('equal',quote(f),quote(f))))
    f=lam(['number','individual']);f['body']=variable('x')
    rows.append(('lambda-outer','混合型lambdaから外側の量化変数を参照',quant('forall','x',logic('equal',f,f))))
    return [(key,label,canonical(body)) for key,label,body in rows]


@lru_cache(maxsize=40)
def checked(index):
    key,label,source=cases()[index]
    drawing=compile_statement(source)
    svg=to_svg(drawing['shapes'])
    if decode(list(reversed(from_svg(svg))))!=source:
        raise ValueError('Visible type or parameter order changed: '+key)
    return dict(key=key,label=label,source=source,svg=svg,
                circles=sum(s['kind']=='circle' for s in drawing['shapes']),width=drawing['width'],
                syntax_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest())


def pins():
    result=old_pins()
    names=['scripts/kant_type_grammar.py','scripts/kant_structural_trial.py',
           'scripts/check_kant_typed_binders.py','tests/test_kant_typed_binders.py']
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    prepare_trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,preserved_count=40,
        schema='kant-typed-binders-1',version=VERSION,title='型と複数引数の束縛',
        intro='型を基底型と再帰的な構成規則で表し、引数の型列には継続・終端を示します。既存のindividual省略形は保持します。以下は復号を区別するための検査例で、完成版の外観ではありません。',
        limits=['Native types and parameter lists; other expression constructors and document declarations remain',
                'Native nesting and drawing event limits apply; description rank limited to 128',
                'Exact structural recovery, no full semantic model suite or visual freeze'])


def build_report():
    return report(OUT,pins)
