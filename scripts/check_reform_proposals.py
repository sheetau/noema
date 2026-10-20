"""Check strict comparison, proposed adoption and nonfactive public delivery."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_reform_proposals import ROOT,LIBRARY,BASIS,NAMES,BIND_NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/reform-proposals-v1.json'
DOC='docs/reform-proposals-v1.md'
PRIOR='reports/clerical-obligation-v1.json'
DOMAIN=(*NAMES,'reader','second','other')
SCENES=('now','future')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
EXTRA+='d zalias[bindings j[a] reference d] e[k r362[v bindings v reference]].'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind='public',bindings=BIND_NAMES):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if kind=='public':
        doc['declarations']=closure(doc,['r366','r367','r362'])
        for d in doc['declarations']:
            if d['name']=='r2zi':
                d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
        args=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]'
        query='q[k r366['+args+']].q[t[k r367['+args+']][k zpoint[]]].'
    elif kind=='comparison':
        doc['declarations']=closure(doc,['r362'])
        args=' '.join('k z'+n+'[]' for n in BIND_NAMES)+' k zref[]'
        query='q[t[k r36z['+args+']][k zpoint[]]].'
    else:
        doc['declarations']=closure(doc,['r362'])
        if kind=='binding':
            for d in doc['declarations']:
                if d['name']=='r36z':
                    d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
        seq='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+']'
        query='q[t[k r362['+seq+' k zref[]]][k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(doc,variant='baseline',bits=(True,True,True,False)):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'now',zpoint=lambda:'future')
    def matches(actual,expected,prefix,fields):
        return actual==tuple('other' if variant==prefix+'_'+f else e for e,f in zip(expected,fields))
    def arrangement(config,field,ref):
        return variant!='not_arrangement' and config in ('older','newer') and matches((field,ref),('field','now'),
            'arrangement',('field','reference'))
    def applied(config,field,point):
        return field=='field' and ((config,point)==('older','now') and variant!='no_baseline' or
            (config,point)==('newer','future') and variant!='unimplemented')
    def comparison(standard,field,left,right,ref,point):
        if not matches((standard,field,ref,point),('standard','field','now','future'),'comparison',('standard','field','reference','point')):return False
        return dict(zip((('older','older'),('newer','newer'),('newer','older'),('older','newer')),bits)).get((left,right),False)
    def target(code,bindings,ref,prefix):
        names=tuple('other' if variant==prefix+'_binding_'+n else n for n in BIND_NAMES)
        if variant==prefix+'_short':names=names[:-1]
        if variant==prefix+'_long':names+=('other',)
        if variant==prefix+'_reordered':names=names[1:]+names[:1]
        return (symbol(code),code.rank,tuple(bindings.items),ref)==('zalias' if variant==prefix+'_description' else 'r362',0,names,
            'future' if variant==prefix+'_reference' else 'now')
    def proposed(person,proposal,code,bindings,ref,point):
        return variant!='not_proposal' and matches((person,proposal,point),('person','proposal','now'),'proposal',('person','item','point')) and target(code,bindings,ref,'proposal')
    def delivered(activity,recipient,proposal,code,bindings,ref,point):
        readers=('reader',) if variant=='missed_reader' else ('reader','second')
        return recipient in readers and matches((activity,proposal,point),('activity','proposal','future'),'delivery',('activity','item','point')) and target(code,bindings,ref,'delivery')
    v.update(aa=lambda p:p=='person',h246w=arrangement,h246x=applied,h246y=comparison,h246z=proposed,h247a=delivered,
        h246d=lambda church,ref:variant!='no_community' and (church,ref)==('church','now'),
        h245z=lambda subject,ref:variant!='secular_subject' and (subject,ref)==('subject','now'),
        h246h=lambda church,code,ref:matches((church,symbol(code),ref),('church','hzxi','now'),'practice',('church','content','reference')),
        h246v=lambda field,church,subject,ref:matches((field,church,subject,ref),('field','church','subject','now'),
            'domain',('field','church','subject','reference')),
        r2zi=lambda person,activity,scholar,ref:variant!='not_scholar' and (person,activity,scholar,ref)==('person','activity','scholar','now'),
        cc=lambda act,audience,ref:matches((act,audience,ref),('activity','audience','now'),'audience',('activity','audience','reference')),
        ce=lambda audience,ref:variant!='limited_public' and (audience,ref)==('audience','now'),
        h6t=lambda audience,person,ref:variant!='empty_audience' and (audience,ref)==('audience','now') and person in ('reader','second'),
        dg=lambda act,point:variant!='not_executed' and (act,point)==('activity','future'),
        f3=lambda person,act,point:matches((person,act,point),('person','activity','future'),'presenter',('person','activity','point')))
    return v


@lru_cache(None)
def comparison_checks():
    doc=fixture('comparison');rows=[]
    for bits in product((False,True),repeat=4):
        actual=evaluate(doc,model(doc,bits=bits),BIND_NAMES,SCENES,True)
        assert actual==[bits==(True,True,True,False)],(bits,actual)
        rows.append(dict(inputs=bits,result=actual[0]))
    for variant in ('not_arrangement','arrangement_field','arrangement_reference','comparison_standard','comparison_field','comparison_reference','comparison_point'):
        assert evaluate(doc,model(doc,variant),BIND_NAMES,SCENES,True)==[False],variant
    goal=fixture('goal')
    for variant,result in [('baseline',True),('unimplemented',False),('not_arrangement',False)]:
        assert evaluate(goal,model(goal,variant),BIND_NAMES,SCENES,True)==[result]
    v=model(doc);v['znewer']=lambda:'older'
    assert evaluate(doc,v,BIND_NAMES,SCENES,True)==[False]
    return dict(comparison_table=rows,equality_not_strict_improvement=True,
        real_improvement_target_requires_realization=True,fixed_standard_field_and_points=True)


@lru_cache(None)
def binding_checks():
    for pos in range(4):
        names=tuple('person' if i==pos else 'other' for i in range(4))
        expected=tuple('x' if i==pos else 'y' for i in range(4))
        doc=fixture('binding',names);v=model(doc);v.update(zperson=lambda:'x',zother=lambda:'y')
        v['r36z']=lambda *args:Content(SCENES,tuple(args==(*expected,'now') for _ in SCENES))
        v['h246x']=lambda config,field,point:(config,field)==(expected[1],expected[2])
        assert evaluate(doc,v,('x','y'),SCENES,True)==[True],pos
    for count in (0,3,5):
        doc=fixture('binding',('person',)*count);v=model(doc);v['zperson']=lambda:'x'
        v['r36z']=lambda *args:Content(SCENES,(True,True));v['h246x']=lambda *args:True
        assert evaluate(doc,v,('x','y'),SCENES,True)==[False],count
    return dict(independent_binding_positions=4,wrong_lengths_rejected=[0,3,5],
        boundary='r36z is typed only in this positional test; comparison_checks evaluates its native body.')


@lru_cache(None)
def public_checks():
    doc=fixture();rows={}
    candidate=['not_proposal','no_community','secular_subject','not_arrangement','no_baseline','not_scholar','limited_public']
    for prefix,fields in [('proposal',('person','item','point')),('practice',('church','content','reference')),
        ('domain',('field','church','subject','reference')),('audience',('activity','audience','reference')),
        ('arrangement',('field','reference'))]:candidate.extend(prefix+'_'+f for f in fields)
    delivery=['missed_reader','empty_audience','not_executed']
    for prefix,fields in [('delivery',('activity','item','point')),('presenter',('person','activity','point'))]:
        delivery.extend(prefix+'_'+f for f in fields)
    for prefix,items in [('proposal',candidate),('delivery',delivery)]:
        items.extend(prefix+'_'+f for f in ('description','reference','short','long','reordered',*('binding_'+n for n in BIND_NAMES)))
    for variant in ['baseline','unimplemented']+candidate+delivery:
        v=model(doc,variant);v['h246y']=unknown
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        expected=[True,True] if variant in ('baseline','unimplemented') else [False,False] if variant in candidate else [True,False]
        assert actual==expected,(variant,actual);rows[variant]=actual
    for bits in ((False,False,False,False),(True,True,True,False),(True,True,True,True)):
        assert evaluate(doc,model(doc,bits=bits),DOMAIN,SCENES,True)==[True,True]
    return dict(contrasts=rows,proposal_does_not_execute_improvement_or_candidate_realization=True,
        exact_same_description_bindings_reference_attribution_and_delivery=True,
        boundary='r2zi is a typed boundary; existing scholarly classification is unchanged.',all_fixed_recipients=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,names in [('comparison',('h246w','h246y')),('goal',('h246x',)),('public',('h246d','h245z','h246h','h246v','h246w','h246x','h246z','h247a','r2zi','cc','ce','h6t','dg','f3'))]:
        doc=fixture(kind)
        for n in names:
            v=model(doc);v[n]=unknown
            try:evaluate(doc,v,BIND_NAMES if kind!='public' else DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error),str(error)
            else:raise AssertionError((kind,n))
            rows.append([kind,n])
    return dict(unknown_inputs_rejected=rows)


@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    validate_hashes(ROOT,read(PRIOR)['source_sha256']);validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    doc=deepcopy(new.document);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[e[r[p r367]][r[p r367]]].')
    assert evaluate(doc,{d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'},DOMAIN,SCENES,True)==[True]
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        roundtrips=True,whole_communication_can_be_quoted_without_execution=True,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('comparison',comparison_checks),('bindings',binding_checks),('public',public_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{DOC,PRIOR,'scripts/compose_reform_proposals.py','scripts/check_reform_proposals.py',
        'tests/test_reform_proposals.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='proposed_better_religious_ecclesiastical_arrangements',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
