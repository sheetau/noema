"""Finite contrasts for permission, demands, grounds and counterfactual choice."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_norms import *
from scripts.shared_reference import content
from scripts.shared_modality import composed as modality

EXAMPLE='examples/v016/norms-counterfactual-v1.noema'
NORMS=tuple(NAMES.values())+('normrequired','normpermitted','normforbidden','normfulfilled','normoptional')
CONDITIONS=('conditionalvalid','conditionalall','conditionalmight','contraryconditional')


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(n):return dict(kind='quote',body=ref(n))
def key(value):return json.loads(value.syntax)['symbol'] if hasattr(value,'syntax') else value
def unknown(*args):raise ValueError('Unknown interpretation')


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    signatures={n:([],I) for n in ('source','person','role','activity','norm','reason','viewpoint','other')}
    signatures.update(context=([],S),elsewhere=([],S),polarity=([],T),required=(RULE['parameters'],T),allowed=(RULE['parameters'],T),
        recognized=(RECOGNIZED['parameters'],T),applicable=(APPLICABLE['parameters'],T),supports=(SUPPORTS['parameters'],T),
        eligible=(SELECT['parameters'],T),closer=(CLOSER['parameters'],T),selects=(SELECT['parameters'],T),
        justifies=(JUSTIFIES['parameters'],T),lend=([I,I,S],T),start=([I,I,S],T),
        offered=([S],T),switched=([S],T),received=([S],T),running=([S],T),
        available=([I,I,S],T),outcomes=([I,I,S,S],T))
    d['declarations'].extend(dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items())
    for name,relation in (('lendingaction','lend'),('startingaction','start'),('otheraction','lend')):
        d['declarations'].append(definition(name,[('person',I),('activity',I)],C,
            content(call(relation,v('person'),v('activity'),v('world')))))
    d['declarations'].append(next(x for x in modality()['declarations'] if x['name']=='methodpossible'))
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)


def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda value=value:value) for n,value in dict(source='a',person='b',role='a',activity='b',norm='a',
        reason='b',viewpoint='a',other='a',context='now',elsewhere='left',polarity=True).items()})
    m.update(overrides)
    return m


def values(document,interpretation=None,*,situations=('now','left','right')):
    return [r['value'] for r in evaluate_document(document,individuals=('a','b'),situations=situations,
        primitives=model() if interpretation is None else interpretation)]


def norm_args(topic='lendingaction',sign=None,grounded=False):
    target=[call('source'),call('person'),call('role'),call('activity'),quote(topic),call('polarity') if sign is None else truth(sign),call('context')]
    required=call('groundedrule',ref('recognized'),ref('applicable'),ref('supports')) if grounded else ref('required')
    return target+[required,ref('allowed')]


def condition_args(topic='lending',selector=None):
    a,c=('offered','received') if topic=='lending' else ('switched','running')
    return [call('context'),ref(a),ref(c),ref('selects') if selector is None else selector]


@lru_cache(maxsize=1)
def normative_checks():
    count=0
    for topic in ('lendingaction','startingaction'):
        d=doc([call(n,*norm_args(topic)) for n in NORMS])
        for rp,rn,ap,an,actual,sign in product((False,True),repeat=6):
            required={True:rp,False:rn};allowed={True:ap,False:an}
            m=model(required=lambda *a:required[a[-2]],allowed=lambda *a:allowed[a[-2]],polarity=lambda:sign,
                    lend=lambda *a:actual,start=lambda *a:actual)
            expected=[allowed[sign] and not required[not sign],rp and rn,allowed[sign] and required[not sign],
                      not required[not sign],required[sign] and actual!=sign,required[sign],allowed[sign],
                      required[not sign],required[sign] and actual==sign,ap and an and not rp and not rn]
            if values(d,m)!=expected:raise ValueError('Permission, demand or performance collapsed')
            count+=1
    return dict(models=count,topics=['本の貸出','装置の起動'],states_per_topic=64)


@lru_cache(maxsize=1)
def counterfactual_checks():
    d=doc([call(n,*condition_args()) for n in CONDITIONS]);worlds=('now','left','right');count=0
    for amask,cmask,smask in product(range(8),range(8),range(4)):
        ant={w for i,w in enumerate(worlds) if amask&(1<<i)}
        con={w for i,w in enumerate(worlds) if cmask&(1<<i)}
        selected={w for i,w in enumerate(worlds[1:]) if smask&(1<<i)}
        valid=bool(selected) and selected<=ant
        expected=[valid,valid and selected<=con,valid and bool(selected&con),valid and 'now' not in ant and selected<=con]
        m=model(offered=lambda w:w in ant,received=lambda w:w in con,selects=lambda a,w:a=='now' and w in selected)
        if values(d,m)!=expected:raise ValueError('Counterfactual scope or actuality changed')
        count+=1
    return dict(models=count,comparison_situations=2,actual_situations=1)


@lru_cache(maxsize=1)
def comparison_checks():
    selection=call('comparisonbest',ref('offered'),ref('eligible'),ref('closer'))
    d=doc([apply_expr(selection,call('context'),call(n)) for n in ('context','elsewhere')]+
          [call('comparisonordered',call('context'),ref('offered'),ref('eligible'),ref('closer'))])
    worlds=('now','left');pairs=list(product(worlds,repeat=2));count=0
    for amask,emask,pmask in product(range(4),range(4),range(16)):
        ant={w for i,w in enumerate(worlds) if amask&(1<<i)}
        eligible={w for i,w in enumerate(worlds) if emask&(1<<i)}
        closer={p for i,p in enumerate(pairs) if pmask&(1<<i)};pool=ant&eligible
        best={w for w in pool if not any((x,w) in closer for x in pool)}
        ordered=not any((x,x) in closer for x in pool) and all(
            (x,z) in closer for x,y,z in product(pool,repeat=3) if (x,y) in closer and (y,z) in closer)
        m=model(offered=lambda w:w in ant,eligible=lambda a,w:a=='now' and w in eligible,
                closer=lambda a,x,y:a=='now' and (x,y) in closer)
        if values(d,m,situations=worlds)!=[w in best for w in worlds]+[ordered]:raise ValueError('Best comparisons or strict order differs')
        count+=1
    return dict(models=count,domain_size=2)


def witness_args():
    return [call('norm'),call('reason')]+norm_args()[:7]+[ref('recognized'),ref('applicable'),ref('supports')]


def supported_args():
    return [call('viewpoint'),quote('offered'),call('reason'),call('context'),ref('received'),ref('selects'),ref('justifies')]


@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    fixtures=[('normwitness',witness_args(),'supports',('a','b','a','b','a','b','lendingaction',True,'now'),
               ('b','a','b','a','b','a','otheraction',False,'left'),
               dict(recognized=lambda *a:True,applicable=lambda *a:True)),
              ('counterfactualsupported',supported_args(),'justifies',('a','offered','b','now','left'),
               ('b','switched','a','left','right'),
               dict(offered=lambda w:w=='left',received=lambda w:w=='left',selects=lambda a,w:(a,w)==('now','left')))]
    for name,args_,relation,wanted,other,context in fixtures:
        d=doc([call(name,*args_)])
        for slot in range(-1,len(wanted)):
            target=list(wanted)
            if slot>=0:target[slot]=other[slot]
            bound=lambda *a,expected=tuple(target):tuple(key(x) for x in a)==expected
            value=values(d,model(**context,**{relation:bound}))[0]
            if value!=(slot==-1):raise ValueError('Norm or comparison evidence binding differs')
            rows.append(dict(definition=name,changed_slot=None if slot<0 else slot,value=value))
    return rows


def example():
    bodies=[]
    for topic in ('lendingaction','startingaction'):
        bodies.extend(call(n,*norm_args(topic)) for n in ('permissionclear','normrequired','normviolated','normoptional'))
        relation='lend' if topic=='lendingaction' else 'start'
        goal=content(call(relation,call('person'),call('activity'),v('world')))
        bodies.append(call('methodpossible',call('person'),goal,call('context'),ref('available'),ref('outcomes')))
    for topic in ('lending','device'):
        a='offered' if topic=='lending' else 'switched'
        selection=call('comparisonbest',ref(a),ref('eligible'),ref('closer'))
        bodies.extend(call(n,*condition_args(topic,selection)) for n in CONDITIONS)
        bodies.extend(call(n,*condition_args(topic)[:3],ref('eligible'),ref('closer'))
                      for n in ('orderedconditional','orderedmight'))
    bodies.append(call('normrequired',*norm_args('startingaction',grounded=True)))
    bodies.append(call('counterfactualsupported',*supported_args()))
    return doc(bodies)


def example_model():
    # Fictional lending and device rules; actual performance never creates a permission.
    def bound(*a):return tuple(key(x) for x in a[:4])==('a','b','a','b') and a[-1]=='now'
    return model(required=lambda *a:bound(*a) and key(a[4])=='startingaction' and a[5],
        allowed=lambda *a:bound(*a) and key(a[4])=='lendingaction' and a[5],
        lend=lambda *a:False,start=lambda *a:False,available=lambda *a:False,outcomes=lambda *a:True,
        offered=lambda w:w!='now',received=lambda w:w=='left',switched=lambda w:w!='now',running=lambda w:w!='now',
        eligible=lambda a,w:a=='now' and w!='now',closer=lambda a,x,y:False,
        recognized=lambda n,s,w:(n,s,w)==('a','a','now'),applicable=lambda n,p,r,w:(n,p,r,w)==('a','b','a','now'),
        supports=lambda n,r,*a:n=='a' and r=='b' and bound(*a) and key(a[4])=='startingaction' and a[5],
        selects=lambda a,w:(a,w)==('now','left'),
        justifies=lambda p,d,r,a,w:(p,key(d),r,a,w)==('a','offered','b','now','left'))


EXAMPLE_VALUES=[True,False,False,False,False,False,True,True,False,False,
                True,False,True,False,False,True,True,True,True,True,True,True,True,True]


def prepare():
    from scripts.shared_norms import prepare as library_prepare
    library_prepare();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published basis differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-norms-evidence-1',definitions=21,new_primitives=0,
        normative=normative_checks(),counterfactual=counterfactual_checks(),comparison=comparison_checks(),
        bindings=binding_diagnostics(),example=values(example(),example_model()))
    if result['example']!=EXAMPLE_VALUES:raise ValueError('Integrated example differs')
    paths=[LIBRARY,BASIS,EXAMPLE,NORM_SOURCE,COUNTER_SOURCE,'data/described-norms-basis-v1.json',
           'data/counterfactual-withholding-basis-v1.json','docs/counterfactual-withholding-v1.md',
           'docs/shared-norms-v1.md','scripts/shared_norms.py','scripts/check_shared_norms.py','tests/test_shared_norms.py',
           'scripts/shared_modality.py','scripts/shared_time.py','scripts/shared_reference.py',
           'examples/v013/contextual-ability.noema','examples/v014/derivation-modalities.noema']
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
