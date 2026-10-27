"""Binding diagnostics for the decoded summary, application goal and second part.

Closed-description quantifiers remain in the delivered Native document. The
historical two-description substitution is applied only after matching the
actual recovered definitions, and is a finite diagnostic, not a general proof.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_kinematic_transition_visible as check
from scripts import kinematic_transition_visible_profile as profile
from scripts import check_kinematic_transition_claim as transition
from scripts import check_electrodynamic_part_heading as heading


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


def forbidden(*xs):raise ValueError('Unknown clock-site-time input (kinematic-transition-visible fixture)')


def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x


def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            test(model|{name:forbidden})


def perturb(test,model,rows):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:relation(rs-{row})});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:relation((rs-{row})|{bad})});count+=1
    unknowns(test,model,rows)
    return count


@lru_cache(None)
def native_blueprint(serialized):
    old=json.loads(serialized);doc=normalize_document(renamed(old,mapping()))
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    for i,(original,d) in enumerate(zip(old['declarations'],doc['declarations'],strict=True)):
        if d['kind']!='definition':continue
        assert d['name'] in recovered,original['name']
        actual=deepcopy(recovered[d['name']])
        assert actual==d,('Source/Native definition differs before finite substitution',original['name'])
        doc['declarations'][i]=actual
    return normalize_document(doc)


@lru_cache(None)
def fixture(group,name,mode):
    source=transition if group=='transition' else heading
    # Always retrieve the unmodified description quantifier first.
    old,slots=source.fixture(name,'native') if group=='transition' else source.fixture(name)
    native=native_blueprint(json.dumps(old,sort_keys=True))
    if group=='transition' and mode!='native':native=normalize_document(transition.finite_descriptions(native))
    return native,slots


def run(group,name,args,model,mode='finite',point='now'):
    source=transition if group=='transition' else heading
    doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{'jktpoint':lambda:point}|model|{n:lambda x=x:x for n,x in zip(slots,args,strict=True)}
    handlers={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,
        situations=transition.POINTS if group=='transition' else ('now','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


CHECKS={'transition':('summary_checks','application_checks','presentation_checks'),
        'heading':('heading_checks','topic_checks')}


@lru_cache(None)
def models():
    result={}
    for group,source in (('transition',transition),('heading',heading)):
        ns=dict(vars(source))|dict(relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,
            run=lambda *a,g=group,**kw:run(g,*a,**kw))
        for name in CHECKS[group]:
            fn=getattr(source,name);fn=getattr(fn,'__wrapped__',fn)
            ns[name]=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
        result[group]=ns
    return result


@pytest.mark.parametrize('group,name',[(g,n) for g in CHECKS for n in CHECKS[g]])
def test_decoded_summary_application_and_heading_models(group,name):assert models()[group][name]()


def test_whole_source_parent_and_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[19,20,192]
    assert list(b['source_units'])==['einstein-1905:u0150','einstein-1905:u0151']
    parent=check.previous.document();assert len(doc['statements'])==190 and doc['statements'][:187]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(ds)==2864 and len(check.vocabulary()._words)==865 and len(check.NEW_DEFINITIONS)==18
    assert check.REUSED_DEFINITIONS==['senz']
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(4,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(3,157,33)
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS+check.REUSED_DEFINITIONS)
    previous=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field].get(n)==d for n,d in previous[field].items())
    for source,public in profile.SOURCE_RELATIONS.items():
        assert ds[mapping()[source]]==renamed(old[source],mapping())
        contract=profile.CONTRACTS[public];assert contract['parameters']==old[source]['parameters']
    assert not b['annotations']['entries'] and not check.FORMS


def test_description_quantifiers_are_retained_before_diagnostic_substitution():
    for name in ('ejr4','ejr5'):
        raw,_=fixture('transition',name,'native');finite,_=fixture('transition',name,'finite')
        original=next(d for d in raw['declarations'] if d['name']==mapping()[name])
        modified=next(d for d in finite['declarations'] if d['name']==mapping()[name])
        assert original['body']['kind']=='exists'
        assert original['body']['sort']==dict(kind='description',result='content')
        assert modified['body']['kind']=='or' and len(modified['body']['arguments'])==2
        assert original!=modified


def test_reference_positions_types_and_unknown_arguments():
    b=dict(check.BASE);h=check.context_handlers(b);cases=[]
    for old,ordinal in check.HEADINGS.items():cases.append(('headingreference',[b['ri'],Q(ordinal)],b[old]))
    for old,pos in check.SENTENCES.items():cases.append(('sentencereference',[b['ri'],*map(Q,pos)],b[old]))
    for old,(node,start,end) in check.SPANS.items():cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append(('describedreference',args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    boundaries=check.text_boundaries()
    assert len(boundaries['sentences']['transitionstatement']['tokens'])==26
    assert boundaries['spans']=={'zni':['transitionstatement',1,15],'znj':['transitionstatement',16,26]}
    assert boundaries['headings']['eispc']['footnotes_follow_reference_positions']


def test_native_reference_lookup_does_not_evaluate_role_or_goal():
    b=dict(check.BASE)
    for old in (*check.HEADINGS,*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='transitioncapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('transitioncapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['transitioncapture']=lambda x:x==b[old]
        declared={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={n:handlers[n] for n in declared})[0]['value']


@lru_cache(None)
def body_fixture(symbol):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    body=deepcopy(ds[symbol]);decls=[]
    for name in sorted(_references(body['body'])):
        d=ds[name];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=name,parameters=parameters,result=d['result']))
    slots=[]
    for i,p in enumerate(body['parameters']):
        name='transitionarg'+chr(97+i);slots.append(name)
        decls.append(dict(kind='primitive',name=name,parameters=[],result=p['sort']))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[body],
        statements=[dict(kind='ask',body=call(symbol,*(call(n) for n in slots)))])),slots


def run_body(symbol,args,model,domain=('a','b','task','other','first','second','paper','author','theory','inquiry','heading')):
    doc,slots=body_fixture(symbol);handlers={mapping().get(n,n):fn for n,fn in model.items()}
    handlers.update({n:lambda x=x:x for n,x in zip(slots,args,strict=True)})
    return evaluate_document(doc,individuals=domain,situations=('reference','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def role(old,candidate,model,context='reference'):
    return run_body(check.reference_roles()[old],[candidate,context],model)


def test_task_role_binds_nonempty_requirement_agent_candidate_and_stage():
    rows={'zna':{('author','task','a','reference')}}
    model={'rd':lambda:'author','zna':relation(rows['zna'])}
    assert perturb(lambda m:role('zm7','task',m),model,rows)
    for item in ('a','b'):
        assert role('zm7','task',model|{'zna':relation({('author','task',item,'reference')})})
    assert not role('zm7','other',model)
    assert not role('zm7','task',model,context='other')


def test_first_part_role_binds_scope_heading_parent_depth_and_ordinal():
    rows={'eisdv':{('heading','first','paper','paper',Q(1),Q(1),'reference')}}
    model={'firstpartheading':lambda:'heading','eirf':lambda:'paper','eisdx':lambda:'first','eisdv':relation(rows['eisdv'])}
    assert perturb(lambda m:role('znb','first',m),model,rows)
    assert not role('znb','second',model|{'eisdv':lambda *xs:True})
    assert not role('znb','first',model,context='other')


def test_theory_role_binds_inquiry_both_principles_and_same_first_part():
    rows={'ejrz':{('theory','reference')},'zt':{('theory',p,'first','reference') for p in ('eion','eiot')}}
    model={n:relation(rs) for n,rs in rows.items()}|{'znb':lambda:'first'}
    assert perturb(lambda m:role('znc','theory',m),model,rows)
    assert not role('znc','other',model)
    assert not role('znc','theory',model,context='other')
    assert not role('znc','theory',model|{'znb':lambda:'second'})


def test_second_part_role_binds_depth_ordinal_parent_and_distinct_first_part():
    rows={'eisdv':{('heading','second','paper','paper',Q(1),Q(2),'reference')}}
    model={'eispc':lambda:'heading','eirf':lambda:'paper','eisdx':lambda:'first','eisdv':relation(rows['eisdv'])}
    assert perturb(lambda m:role('eispb','second',m),model,rows)
    assert not role('eispb','first',model|{'eisdv':lambda *xs:True})
    assert not role('eispb','second',model,context='other')


def test_kinematic_inquiry_quotes_the_current_closed_body_schema_without_execution():
    rows={'eisdh':{('inquiry','eigy','reference')}};model={'eisdh':relation(rows['eisdh'])}
    assert perturb(lambda m:run_body(mapping()['eihn'],['inquiry','reference'],m),model,rows)
    assert not run_body(mapping()['eihn'],['inquiry','other'],model)
    doc,_=body_fixture(mapping()['eihn']);decls={d['name']:d for d in doc['declarations']}
    schema=decls[mapping()['eigy']];contract=profile.CONTRACTS['kinematicinquirydomain']
    assert contract['parameters'][1]['result']==dict(kind='function',parameters=schema['parameters'],result=schema['result'])
