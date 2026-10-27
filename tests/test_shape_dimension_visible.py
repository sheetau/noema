"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Native individual quantifiers remain in the distinguishing two-value models. Numerical cut examples and reference binding checks are diagnostics, not proofs over all real inputs.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json,re
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_shape_dimension_visible as check
from scripts import shape_dimension_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from itertools import product
from scripts import check_material_shape_dimensions as material
from scripts import check_directional_contraction_claim as directional
from scripts import check_planar_shape_limit as planar
from scripts import check_speed_boundary_forecast as forecast
from scripts import check_reciprocal_shape_results as reciprocal
from scripts import check_final_transform_claim as final
from scripts import check_transverse_segment as segment
from scripts.check_translated_light_trial import expose
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (four-coordinate-visible fixture)')

def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    if isinstance(x,SequenceValue):return tuple(value(v) for v in x.items)
    return x

def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            test(model|{name:forbidden})

def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows)
    return count

class Cuts:
    def __init__(self):self.table={}
    def make(self,n):
        n=Q(n);f=FunctionValue(('number',),'truth',lambda q:q<n)
        self.table[f.implementation]=n;return f
    def read(self,f):
        while isinstance(f,FunctionValue):
            impl=f.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):f=impl;continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            f=free.get('raw')
        raise ValueError('Unregistered finite cut')

def numbers():
    cuts=Cuts();c=cuts.make;r=cuts.read
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),
        bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),
        bg=lambda a,b:r(a)<r(b),shv=lambda a,b:c(r(a)*r(b)),sah=lambda a,b:c(r(a)*r(b)),
        sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b),zzbg=lambda a,b:r(a)<r(b))

MODULES=dict(material=material,directional=directional,planar=planar,forecast=forecast,reciprocal=reciprocal)
CHECKS=dict(material=('occupation_checks','history_checks','transform_checks'),
    directional=('dimension_checks','speed_checks','scope_checks','presentation_checks'),
    planar=('projection_checks','image_checks','neighborhood_checks','connection_checks','presentation_checks'),
    forecast=('caveat_checks','endpoint_checks','permission_checks','role_checks','presentation_checks'),
    reciprocal=('motion_checks','correspondence_checks','setting_checks','shape_width_checks','limit_checks','scope_checks','presentation_checks'))
EXPOSE=dict(material={'ejgh':3,'ejgi':1,'ejgm':1},
    directional={'ejgp':3,'ejgq':3,'ejgy':3,'ejgt':1,'ejgu':1,'ejgv':1,'ejgw':1},
    planar={'ejg5':1,'ejha':1,'ejhb':3,'ejhc':4,'ejhd':4,'ejhe':1,'ejhf':1},
    forecast={'ejhm':2,'ejhn':5,'ejhp':1,'ejhr':1},
    reciprocal={'ejhx':2,'ejhz':3,'ejh2':1,'ejh3':3,'ejh6':1,'ejh7':3,'ejia':4,'ejib':4,'ejic':1,'ejid':1})
SHAPE_ROOTS={'ejgt','ejgu','ejgv','ejgw','ejhf','ejhr','ejid'}


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    blueprint,slots=MODULES[group].fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        # Missing historical helpers cannot be passed off as decoded definitions.
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            sort=material.SS if name in SHAPE_ROOTS else RS
            quantifiers={'forall'} if group=='material' else {'forall','exists'}
            assert len(expose(actual,quantifiers,only_sort=sort))==EXPOSE[group][name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,args,model,mode='boundary',domain=None):
    source=MODULES[group];doc,slots=fixture(group,name,mode)
    assert len(args)==len(slots),(group,name,len(args),len(slots))
    point={'material':'jmsdpoint','directional':'jdccpoint','planar':'jpslpoint','forecast':'jsbfpoint','reciprocal':'jrsrpoint'}[group]
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{point:lambda:'context' if group=='material' else 'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN if domain is None else domain,
        situations=getattr(source,'POINTS',('context','other')),
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,arithmetic=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,value=value)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    numeric=clone(four,('model',))
    final_model=clone(final,('final_model',),dict(numeric_model=numeric['model']))['final_model']
    body_model=clone(segment,('model',))['model']
    result={}
    for group,module in MODULES.items():
        extra=dict(body_model=body_model,final_model=final_model,
            run=lambda *args,group=group,**kwargs:run(group,*args,**kwargs))
        if group=='material':functions=('setup',*CHECKS[group])
        elif group=='directional':
            functions=CHECKS[group];extra['setup']=result['material']['setup']
        elif group=='reciprocal':functions=('model','physical_model',*CHECKS[group])
        else:functions=('model',*CHECKS[group])
        result[group]=clone(module,functions,extra)
    return result


@pytest.mark.parametrize('group,name',[(g,n) for g,ns in CHECKS.items() for n in ns])
def test_decoded_shape_distinguishing_models(group,name):assert models()[group][name]()


def test_decoded_equation_correspondence_and_both_prior_considerations():
    # The historical helper locally imports the legacy Content class; use the
    # identical model with constructed Content without changing that validator.
    cuts,m,norm=models()['forecast']['model']();c=cuts.make
    one=FunctionValue((RS,),RS,lambda t:c(Q(1)))
    for event,first,second in product(('a','b'),repeat=3):
        rows={'eiyx':{(event,first,'a','context'),(event,second,'b','context')},
            'sre':{norm([first,second,c(Q(5)),c(Q(3)),one])}}
        mm=segment.relations(m|{'ra':lambda:'a','zbm':lambda:'b'},rows,norm)
        test=lambda mm:run('forecast','ejhk',[c(Q(3))],mm,domain=('a','b'))
        assert perturb(test,mm,rows,norm)
        other='b' if event=='a' else 'a'
        assert not test(mm|{'eiyx':relation({(event,first,'a','context'),(other,second,'b','context')})})
    for a,b in product((False,True),repeat=2):
        mm={'ejgt':lambda a=a:Content(forecast.POINTS,(a,)*len(forecast.POINTS)),
            'ejhf':lambda b=b:Content(forecast.POINTS,(b,)*len(forecast.POINTS))}
        assert run('forecast','ejhl',[],mm)==(a and b)


def test_decoded_actual_shape_width_binds_body_frame_time_and_axis():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=models()['material']['setup']();c=cuts.make
    rows={'suk':{norm([shape,'x',c(Q(5))])}};mm=segment.relations(m,rows,norm)
    args=['body','k','context',c(Q(1)),'x',c(Q(5))]
    assert perturb(lambda mm:run('material','ejgl',args,mm),mm,rows,norm)
    for time in (-1,3):
        bad=args[:];bad[3]=c(Q(time));assert not run('material','ejgl',bad,mm)
    unknowns(lambda mm:run('material','ejgl',args,mm),mm,('eislu','eirh','eisls','eislt'))
    # The superseded ejgn/ejgo helpers are outside this source selection.
    # Current width existence, axis ratios and generic scope are tested above
    # through ejgp/ejgq/ejgt, which are actually present in the visible document.
    assert not {'ejgn','ejgo'}&set(check.mapping())


def test_source_backprojection_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[168,169,170,171,172]
    assert list(b['source_units'])==['einstein-1905:u0116','einstein-1905:u0117']
    assert len(doc['declarations'])==2270 and len(doc['statements'])==148
    parent=check.previous.document();assert doc['statements'][:143]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        meaning=catalog.entries[name]['meaning_ja']
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',meaning)
    assert len(check.vocabulary()._words)==833 and len(check.NEW_DEFINITIONS)==114
    assert b['new_public_relations']==31 and b['new_core_words']==b['new_reference_primitives']==0
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(4,116,32)


def test_native_real_quantifiers_and_shape_scope_are_preserved():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for group,roots in EXPOSE.items():
        for name in roots:
            native={d['name']:d for d in fixture(group,name)[0]['declarations']}
            assert native[mapping()[name]]==ds[mapping()[name]]
    # This is a syntax check of the uninstantiated bodies, distinct from the
    # finite binding diagnostics. It does not prove a theorem over all reals.
    def refs(old):return set(_references(ds[mapping()[old]]['body']))
    assert {mapping()[n] for n in ('ejgp','ejgm','ejgr','ejgs')}<=refs('ejgt')
    assert {mapping()[n] for n in ('ejgm','ejhc','ejhd')}<=refs('ejhe')
    assert {mapping()[n] for n in ('eiscv','ejhq','ejgp','ejhp')}<=refs('ejhr')
    assert {mapping()[n] for n in ('ejid','ejgy')}<=refs('ejie')
    assert {mapping()[n] for n in ('ejhz','ejic')}<=refs('ejid')
    seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(mapping()['ejhf'])
    assert not {check.names()[n] for n in ('zhw','zhx','zh2')}&seen


def test_arithmetic_forwarders_preserve_both_arguments_and_sign():
    ds={d['name']:d for d in check.restored()['document']['declarations']};voc=check.vocabulary()
    for old,target in check.FORWARD_MAPS.items():
        actual=ds[check.names()[old]];expected=next(d for d in check.forwarder_definitions() if d['name']==actual['name'])
        assert actual==expected
        argc=len(actual['parameters']);primitive=deepcopy(ds[voc._symbols[target]])
        for values in product((Q(-3,2),Q(0),Q(7,3)),repeat=argc):
            args=[dict(kind='number',numerator=x.numerator,denominator=x.denominator) for x in values]
            expected=-values[0] if argc==1 else values[0]+values[1] if target=='rationaladd' else values[0]*values[1]
            capture=dict(kind='primitive',name='arithmeticcapture',parameters=['number'],result='truth')
            statement=dict(kind='ask',body=call('arithmeticcapture',call(actual['name'],*args)))
            native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[primitive,actual,capture],statements=[statement]))
            fn=(lambda x:-x) if argc==1 else (lambda a,b:a+b) if target=='rationaladd' else (lambda a,b:a*b)
            assert evaluate_document(native,individuals=('a','b'),situations=('context',),primitives={primitive['name']:fn,'arithmeticcapture':lambda x:x==expected})[0]['value']


def test_sentence_spans_annotation_and_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():
        args=[b['ri'],*map(Q,pos)];assert h['sentencereference'](*args)==b[old]
        for slot in range(3):
            bad=args[:];bad[slot]='unknown' if slot==0 else Q(999)
            with pytest.raises(ValueError):h['sentencereference'](*bad)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['eisod'])),check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
    args=[b['eirf'],b['zh7'],role,b['ri']];assert h['describedreference'](*args)==b['eisod']
    for slot in range(4):
        bad=args[:];bad[slot]='unknown'
        with pytest.raises(ValueError):h['describedreference'](*bad)
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    assert [len(row['tokens']) for row in check.text_boundaries()['sentences'].values()]==[37,17,28,24]


def test_native_references_do_not_execute_quoted_claims():
    b=check.BASE
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='shapecapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('shapecapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['shapecapture']=lambda x:x==b[old]
        assert evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)[0]['value']


def test_native_annotation_role_binds_every_input_and_preserves_call_quotes():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=deepcopy(ds[check.reference_roles()['eisod']]);boundaries=('zfl','rd','ejgt','ejhf','eisn5');decls=[]
    for old in boundaries:
        d=ds[mapping()[old]];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=d['name'],parameters=parameters,result=d['result']))
    decls += [dict(kind='primitive',name='shapecandidate',parameters=[],result='individual'),dict(kind='primitive',name='shapecontext',parameters=[],result='situation'),role]
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls,statements=[dict(kind='ask',body=call(role['name'],call('shapecandidate'),call('shapecontext')))]))
    row=('annotation','author','ejgt','ejhf','section','discourse')
    base={'shapecandidate':lambda:'annotation','shapecontext':lambda:'discourse',mapping()['rd']:lambda:'author',mapping()['eisn5']:lambda:'section',mapping()['ejgt']:forbidden,mapping()['ejhf']:forbidden}
    def test(rows):
        return evaluate_document(doc,individuals=('annotation','author','section','other'),situations=('discourse','other'),primitives=base|{mapping()['zfl']:relation(rows)})[0]['value']
    assert test({row})
    for slot in range(6):assert not test({tuple('wrong' if i==slot else x for i,x in enumerate(row))})
    with pytest.raises(ValueError):evaluate_document(doc,individuals=('annotation','author','section','other'),situations=('discourse','other'),primitives=base|{mapping()['zfl']:forbidden})
