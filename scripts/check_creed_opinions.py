"""Check topic identity and expression without making quoted defects factual."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_creed_opinions import ROOT, LIBRARY, BASIS, NAMES, MEANINGS, parents, build, closure
from scripts.compose_qualitative_influence import TRUE
from scripts.check_reviewed_thoughts import EXTRA, PROVIDER, model as review_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT='reports/creed-opinions-v1.json'
DOC='docs/creed-opinions-v1.md'
PRIOR=('reports/reviewed-thoughts-v1.json','reports/military-remarks-v1.json','reports/clerical-obligation-v1.json')
DOMAIN=(*NAMES,'subject','criterion','reader','second','other')
SCENES=('past','now','future')


def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture():
    doc=deepcopy(catalog().document); doc.update(declarations=closure(doc,['r36x','r36y']),statements=[])
    # The previously checked review qualification and scholarly classification
    # are typed boundaries; native topic and expression composition stays live.
    boundaries={'r36s','r2zi'}
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDER); existing={d['name'] for d in prefix['declarations']}
    added=''.join('r z'+n+'[] a.' for n in DOMAIN if 'z'+n not in existing)+'r zpoint[] d.'
    provider=next(d for d in prefix['declarations'] if d['name']=='h224y')
    doc['declarations']=[d for d in prefix['declarations'] if d['name']!='h224y']+[
        deepcopy(provider if d['name']=='h224y' else d) for d in doc['declarations']]
    args=' '.join('k z'+n+'[]' for n in NAMES)+' k znow[]'
    return parse(format_graph(doc,'compact')+added+'q[k r36x['+args+']].q[t[k r36y['+args+']][k zpoint[]]].')


def model(variant='baseline'):
    doc=fixture(); v=review_model(doc)
    for n in DOMAIN: v['z'+n]=lambda n=n:n
    v.update(znow=lambda:'now',zpoint=lambda:'future')
    def matches(actual,expected,prefix,fields):
        return actual==tuple('other' if variant==prefix+'_'+f else e for e,f in zip(expected,fields))
    def qualification(person,thought,judgment,beneficiary,ref):
        return variant!='unqualified' and matches((person,thought,judgment,beneficiary,ref),
            ('person','thought','judgment','beneficiary','now'),'qualified',('person','thought','judgment','beneficiary','reference'))
    def topic(remark,target,criterion,code,ref):
        return variant!='no_topic' and code.rank==0 and matches((remark,target,criterion,symbol(code),ref),
            ('thought','creed','criterion','r326','now'),'topic',('thought','creed','criterion','content','reference'))
    def presentation(act,recipient,subject,code,point):
        expected=dict(kind='apply',function=dict(kind='function_ref',symbol='rsa'),arguments=[
            dict(kind='function_ref',symbol='zalias' if variant=='message_content' else 'zcontent'),
            parse('p:q['+TRUE+'].')['statements'][0]['body']])
        recipients=('reader',) if variant=='missed_reader' else ('reader','second')
        return recipient in recipients and json.loads(code.syntax)==expected and code.rank==0 and matches(
            (act,subject,point),('activity','subject','future'),'message',('activity','subject','point'))
    v.update(r36s=qualification,r2zi=lambda person,act,scholar,ref: variant!='private_role' and matches(
        (person,act,scholar,ref),('person','activity','scholar','now'),'scholar',('person','activity','role','reference')),
        h243x=topic,cc=lambda act,audience,ref: matches((act,audience,ref),('activity','audience','now'),'audience',('activity','audience','reference')),
        ce=lambda audience,ref: variant!='limited_public' and (audience,ref)==('audience','now'),
        h6t=lambda audience,reader,ref: variant!='empty_audience' and (audience,ref)==('audience','now') and reader in ('reader','second'),
        dg=lambda act,point: variant!='not_executed' and (act,point)==('activity','future'),
        f3=lambda person,act,point: matches((person,act,point),('person','activity','future'),'presenter',('person','activity','point')),
        f2=presentation,h245r=lambda act,judgment,point: matches((act,judgment,point),('activity','judgment','future'),
            'expression',('activity','judgment','point')),
        fa=lambda person,judgment,point: variant!='not_own' and (person,judgment,point)==('person','judgment','future'),
        fb=lambda judgment,subject,point:(judgment,subject,point)==('judgment','subject','future'),
        hznn=lambda judgment,subject,code,sign,point: variant!='no_endorsement' and (judgment,subject,symbol(code),sign,point)==(
            'judgment','subject','zcontent',True,'future'))
    return v


@lru_cache(None)
def identity_checks():
    rows={}
    variants=['unqualified','no_topic','private_role','limited_public']
    for prefix,fields in [('qualified',('person','thought','judgment','beneficiary','reference')),
        ('topic',('thought','creed','criterion','content','reference')),
        ('scholar',('person','activity','role','reference')),('audience',('activity','audience','reference'))]:
        variants.extend(prefix+'_'+field for field in fields)
    for variant in ['baseline']+variants:
        actual=evaluate(fixture(),model(variant),DOMAIN,SCENES,True)
        assert actual==([True,True] if variant in ('baseline','topic_criterion') else [False,False]),(variant,actual)
        rows[variant]=actual
    return dict(contrasts=rows, criterion_witness_not_fixed_by_source=True,
        typed_boundaries=['r36s: reviewed-thoughts report','r2zi: inherited scholarly public-use classification'])


@lru_cache(None)
def expression_checks():
    rows={}
    variants=['not_executed','not_own','no_endorsement','missed_reader','empty_audience','message_content',
        'message_activity','message_subject','message_point','presenter_person','presenter_activity','presenter_point',
        'expression_activity','expression_judgment','expression_point']
    for variant in variants:
        actual=evaluate(fixture(),model(variant),DOMAIN,SCENES,True)
        assert actual==[True,False],(variant,actual); rows[variant]=actual
    for truth in (False,True):
        v=model(); v.update(zcontent=lambda subject:Content(SCENES,(truth,)*3),
            h243u=lambda *args:truth,h243v=lambda *args:truth)
        assert evaluate(fixture(),v,DOMAIN,SCENES,True)==[True,True]
    return dict(contrasts=rows, fixed_all_recipients=True, native_ownership_and_exact_message_evaluated=True,
        actual_delivery_distinct_from_candidate=True, defect_truth_and_thought_truth_not_executed=True,
        reference_and_delivery_points_distinct=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for n in ('r36s','r2zi','h243x','cc','ce','h6t','dg','f3','f2','h245r','fa','fb','hznn','h224z','zchoose'):
        v=model(); v[n]=unknown
        try:evaluate(fixture(),v,DOMAIN,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rows.append(n)
    return dict(unknown_relations_rejected=rows)


@lru_cache(None)
def structure_checks():
    new=catalog(); old={n:e for p in parents() for n,e in p.entries.items()}
    for n,e in new.entries.items():
        if n not in MEANINGS:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    # Quoting the complete expression does not execute either boundary or truth.
    doc=deepcopy(new.document);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[e[r[p r36y]][r[p r36y]]].')
    assert evaluate(doc,{d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'},DOMAIN,SCENES,True)==[True]
    return dict(new_primitives=0,new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        roundtrips=True,quoted_expression_not_executed=True,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('identity',identity_checks),('expression',expression_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(p.source_sha256) for p in parents()))|set(PRIOR)|{DOC,
        'scripts/compose_creed_opinions.py','scripts/check_creed_opinions.py','tests/test_creed_opinions.py',
        'scripts/check_reviewed_thoughts.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='qualified_creed_defect_opinions_and_public_expression',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
