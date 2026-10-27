"""Check recovered Native definitions, real-domain boundaries and nonexecuting references.

Preserved models supply distinguishing inputs. All tested definitions are replaced
by recovered Native bodies before explicit instantiation. Two-value record tests
diagnose argument binding; they do not prove all real times or physical histories.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_transverse_symmetry_claim_visible as check
from scripts import transverse_symmetry_claim_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_transverse_symmetry_claim as symmetry
from scripts import check_transverse_measured_length as measured
from scripts import check_transverse_comparison_scope as comparison
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

MODULES=dict(symmetry=symmetry,measured=measured,comparison=comparison)
CHECKS=[('symmetry',n) for n in ('scope_checks','numeric_checks','presentation_checks')]+[('measured',n) for n in ('length_checks','time_checks','vector_checks','transverse_checks','branch_checks')]+[('comparison',n) for n in ('shape_checks','eligibility_checks','range_checks','signed_checks')]

@lru_cache(None)
def fixture(group,name,mode='boundary'):
    blueprint,slots=MODULES[group].fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            kinds={'forall','exists'} if group=='comparison' else {'forall'}
            expected={'ejdc':4,'ejde':3}.get(name,2 if name=='ejc3' else 1)
            assert len(expose(actual,kinds,only_sort=RS))==expected
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(group,name,args,model,mode='boundary',domain=None):
    source=MODULES[group];doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jtscpoint',lambda:'discourse');mm.setdefault('jtcspoint',lambda:'context')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN if domain is None else domain,situations=source.POINTS if hasattr(source,'POINTS') else ('context','other'),
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,arithmetic=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models(group):
    names=tuple(n for g,n in CHECKS if g==group)
    numeric=clone(four,('model',))['model'];physical=clone(measured,('model',),dict(segment_model=clone(segment,('model',))['model']))['model']
    execute=lambda name,args,m,mode='boundary',domain=None:run(group,name,args,m,mode,domain)
    if group=='symmetry':return clone(symmetry,('truth',*names),dict(numeric_model=numeric,run=lambda name,m,mode='boundary':run(group,name,[],m,mode)))
    if group=='measured':return clone(measured,names,dict(model=physical,numeric_model=numeric,run=execute))
    return clone(comparison,('setup_shapes','speed_model',*names),dict(physical_model=physical,numeric_model=numeric,run=execute))

@pytest.mark.parametrize('group,name',CHECKS)
def test_decoded_native_distinguishing_models(group,name):assert models(group)[name]()

def test_source_backprojection_and_preserved_parent():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[154,155,156,157,158]
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(101,105)]
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(181,188)]
    assert len(doc['declarations'])==2014 and len(doc['statements'])==134
    parent=check.previous.document();assert doc['statements'][:129]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.NEW_DEFINITIONS)==41 and b['new_public_relations']==2 and b['new_reference_primitives']==1
    assert set(b['forwarded_reference_signatures'])=={'zha'}

def test_public_contracts_and_previous_profile_preserved():
    voc=check.vocabulary();assert len(voc._words)==801
    before=check.previous.vocabulary().document();after=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(after[field][n]==d for n,d in before[field].items())
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        original=next(d for d in check.source_excerpt()['declarations'] if d['name']==old)
        actual=ds[mapping()[old]];contract=profile.CONTRACTS[new]
        assert actual['kind']=='primitive' and actual['parameters']==original['parameters']==contract['parameters']
        assert actual['result']==original['result']=='truth'
    assert profile.FAMILY==dict(kind='function',parameters=['situation'],result=profile.CUT)

def test_sentence_and_display_span_coordinates_reject_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():assert h['sentencereference'](b['ri'],*map(Q,pos))==b[old]
    for args in ((b['ri'],Q(52),Q(5)),('unknown',Q(52),Q(1)),(b['ri'],Q(0),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args.copy();bad[slot]=Q(99) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
        bad=args.copy();bad[2]=Q(end);bad[4]=Q(start)
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    sentences=check.text_boundaries()['sentences']
    assert [len(s['tokens']) for s in sentences.values()]==[18,39,20,5]
    assert sentences['symmetrydisplays']['tokens']==['Hieraus','folgt:','[M0186]','oder','[M0187].']

def checked_values(function=None):
    cuts,_=numbers()
    if function is None:function=FunctionValue(('situation',),RS,forbidden)
    return cuts,check.BASE|dict(measuredlengthfamily=function,zgz=cuts.make(Q(2)))

def test_native_references_and_forwarding_do_not_execute_descriptions():
    cuts,b=checked_values();base=check.restored()['document']
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,'zha'):
        sort=profile.FAMILY if old=='measuredlengthfamily' else RS if old=='zha' else 'situation' if old=='zg2' else 'individual'
        doc=deepcopy(base);doc['declarations'].append(dict(kind='primitive',name='symmetrycapture',parameters=[sort],result='truth'))
        expression=call(check.names()[old])
        if old=='zha':
            doc['declarations'].append(dict(kind='primitive',name='symmetrysetting',parameters=[],result='situation'))
            expression=call(check.names()[old],call('symmetrysetting'))
            b=b|dict(measuredlengthfamily=FunctionValue(('situation',),RS,lambda s:cuts.make(Q(7)) if s=='other' else forbidden()))
        doc['statements']=[dict(kind='ask',body=call('symmetrycapture',expression))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
        handlers['symmetrycapture']=lambda x:cuts.read(x)==7 if old=='zha' else isinstance(x,FunctionValue) and x.parameters==('situation',) and x.result==RS if old=='measuredlengthfamily' else x==b[old]
        if old=='zha':handlers['symmetrysetting']=lambda:'other'
        result=evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
        assert [r['value'] for r in result]==[True]

def test_typed_reference_arguments_unknown_inputs_and_rank():
    cuts,b=checked_values();h=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        sort=profile.FAMILY if old=='measuredlengthfamily' else 'situation'
        kind='describedsituationcutfunctionreference' if old=='measuredlengthfamily' else 'describedsettingreference'
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        assert h[kind](*args)==b[old]
        for slot in range(4):
            bad=args.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h[kind](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    for bad in (FunctionValue(('individual',),RS,forbidden),FunctionValue(('situation',),profile.FAMILY,forbidden),FunctionValue(('situation',),RS,None),'function'):
        with pytest.raises(ValueError):profile.SituationCutFunctionReferences({('d','n','role','s'):bad})

def role_fixture(old,dependencies,instantiated=True):
    ds={d['name']:d for d in check.restored()['document']['declarations']};role=deepcopy(ds[check.reference_roles()[old]])
    if instantiated:assert len(expose(role,{'forall','exists'},only_sort=RS))==1
    boundaries=[]
    for name in dependencies:
        d=ds[mapping()[name]];sorts=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
        boundaries.append(dict(kind='primitive',name=d['name'],parameters=sorts,result=d['result']))
    args=[]
    for i,p in enumerate(role['parameters']):
        name='symmetryslot'+'abcd'[i];boundaries.append(dict(kind='primitive',name=name,parameters=[],result=p['sort']));args.append(call(name))
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=boundaries+[role],statements=[dict(kind='ask',body=call(role['name'],*args))]))
    def execute(values,handlers):
        mapped={mapping().get(n,n):f for n,f in handlers.items()}|{'symmetryslot'+'abcd'[i]:lambda x=x:x for i,x in enumerate(values)}
        return evaluate_document(doc,individuals=('body','low','high','K'),situations=('context','other'),primitives=mapped)[0]['value']
    return execute

def test_native_reverse_setting_role_binds_candidate_negative_speed_and_length():
    execute=role_fixture('zg2',('zb6','zb7','bb','bf','ejdg'));cuts,m=numbers();c=cuts.make;r=cuts.read
    base={'zb6':lambda:'context','zb7':lambda:c(Q(3)),'bb':m['bb'],'bf':m['bf']}
    args=['other','context',c(Q(2))];target=('other',Q(-3),Q(2))
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    assert execute(args,base|{'ejdg':lambda *xs:norm(xs)==target})
    for slot in range(3):
        wrong=tuple(('context' if i==0 else Q(99)) if i==slot else x for i,x in enumerate(target))
        assert not execute(args,base|{'ejdg':lambda *xs:norm(xs)==wrong})
    assert not execute(['context',*args[1:]],base|{'ejdg':lambda *xs:True})
    with pytest.raises(ValueError):execute(args,base|{'ejdg':forbidden})
    full=role_fixture('zg2',('zb6','zb7','bb','bf','ejdg'),False)
    with pytest.raises(ValueError,match='Cannot finitely quantify|Finite function domain'):full(args[:2],base|{'ejdg':lambda *xs:True})

def test_native_length_family_role_keeps_all_settings_and_unmeasured_values_free():
    execute=role_fixture('measuredlengthfamily',('zgu','zgv','zgw','ra','ejcz','sca'));cuts,m=numbers();c=cuts.make;r=cuts.read
    fixed={'zgu':lambda:'body','zgv':lambda:'low','zgw':lambda:'high','ra':lambda:'K','sca':m['sca']}
    lengths={'context':Q(1),'other':Q(2)}
    family=FunctionValue(('situation',),RS,lambda s:c(lengths[s]))
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    for setting,length in lengths.items():
        row=('body','low','high','K',setting,length)
        base=fixed|{'ejcz':lambda *xs:norm(xs)==row}
        assert execute([family,'context',c(length)],base)
        for wrong in (Q(-3),Q(7)):
            bad=FunctionValue(('situation',),RS,lambda s:c(wrong if s==setting else lengths[s]))
            assert not execute([bad,'context',c(length)],base)
        # Every fixed measurement argument must be carried into the role.
        for slot in range(4):
            wrong=tuple('wrong' if i==slot else x for i,x in enumerate(row))
            # The evaluator eagerly visits both sides of implication. The role
            # constrains no output when this measurement is absent, but the
            # candidate function remains defined on every situation.
            assert execute([FunctionValue(('situation',),RS,lambda s:c(Q(-7))),'context',c(length)],fixed|{'ejcz':lambda *xs:norm(xs)==wrong})
    for arbitrary in (Q(-7),Q(0),Q(11)):
        assert execute([FunctionValue(('situation',),RS,lambda s:c(arbitrary)),'context',c(Q(9))],fixed|{'ejcz':lambda *xs:False})
    with pytest.raises(ValueError):execute([family,'context',c(Q(1))],fixed|{'ejcz':forbidden})
    full=role_fixture('measuredlengthfamily',('zgu','zgv','zgw','ra','ejcz','sca'),False)
    with pytest.raises(ValueError,match='Cannot finitely quantify|Finite function domain'):full([family,'context'],fixed|{'ejcz':lambda *xs:False})
