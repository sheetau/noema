"""Check one performance witness and preserve its criteria through ability."""
import argparse
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_topical_standing as prior
from scripts.compose_qualified_judgment import ROOT,FULL,CORE,LIBRARY,BASIS,MEANINGS,LIMITS,build,parent,closure

REPORT='reports/qualified-judgment-v1.json'
READING='data/qualified-judgment-reading-v1.json'
INDEX=prior.INDEX
INVENTORY=prior.INVENTORY
DOMAIN=(*prior.NATIVE_DOMAIN,'weakreason')
SCENES=prior.SCENES
QUALITY='r zsecure[a a a d d] c.r zadequate[a a a d d] c.'
REFERENCES='r zqualitycontext[] d.r zpoint[] d.r zother[a a a d d] c.'
QARGS=prior.TOPIC+' r[k zqualitycontext[]] r[p zsecure] r[p zadequate]'
CODE='k hzvq[r[k zone[]] r[k zqualitycontext[]] r[p zsecure] r[p zadequate]]'
CONCRETE='''
d zsecure[p a m a j a c d s d] c[k rqwr[v j v s p fc p fd]].
d zadequate[p a m a j a c d s d] c[k fb[v j v m v s]].
'''


def unknown(*args):raise ValueError('Unknown qualified judgment input')


@lru_cache(None)
def prefix(roots,concrete=False):
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));d['declarations']=closure(d,list(roots)+['hzvg']+(['rqwr'] if concrete else []));d['statements']=[]
    return format_graph(d,'compact')+prior.EXTRA+REFERENCES+(CONCRETE if concrete else QUALITY)


def evaluate(doc,m,domain=DOMAIN,max_steps=60000000):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=SCENES,
        primitives={d['name']:m[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=max_steps,memoize_definitions=True,memoize_expressions=True)]


def qualified_task(code,alternate=False):
    node=json.loads(code.syntax)
    if node.get('function')!={'kind':'function_ref','symbol':'hzvp'} or node.get('kind')!='apply':return None
    args=node.get('arguments',[])
    if len(args)!=4 or args[1:]!=[{'kind':'call','symbol':'zqualitycontext','arguments':[]},
        {'kind':'function_ref','symbol':'zsecure'},{'kind':'function_ref','symbol':'zother' if alternate else 'zadequate'}]:return None
    return {'zone':'one','ztwo':'two'}.get(args[0].get('symbol')) if args[0].get('kind')=='call' else None


def model(variant='baseline',secure=True,adequate=True):
    inherited=variant if variant in ('wrong_reference','unassessed_after','fixed_scope','split_results') else 'baseline'
    m=prior.model((True,True),(True,False) if variant=='fixed_scope' else (True,True),inherited,True)
    def matching(p,g):return p=='person' and qualified_task(g,variant=='alternate_profile') in ('one','two') and variant!='unqualified_profile'
    def scope(p,g,method,anchor,scene):
        matter=qualified_task(g,variant=='alternate_profile')
        return matching(p,g) and method==('methodone' if matter=='one' else 'methodtwo') and not(
            variant=='split_results' and (anchor,matter) in (('after','two'),('bad','one')))
    def quality(p,matter,judgment,context,scene):
        return (p,context,scene)==('person','now','good') and (matter,judgment) in (('one','actone'),('two','acttwo'))
    m.update(zqualitycontext=lambda:'after' if variant=='wrong_standard_context' else 'now',zpoint=lambda:'good',
        zsecure=lambda *args:secure and quality(*args),zadequate=lambda *args:adequate and quality(*args),zother=lambda *args:adequate and quality(*args),
        hzuq=lambda p,g,a,s:matching(p,g) and ((a,s) in (('now','pretrial'),('after','posttrial')) or variant=='split_results' and (a,s)==('bad','posttrial')),
        hzur=lambda p,g,a,s:matching(p,g),hzus=lambda p,g,s:matching(p,g) and s in ('pretrial','posttrial'),hzut=lambda *args:False,
        hzuu=scope,hzuv=lambda p,g,method,a,s:matching(p,g))
    if variant=='extra_unsupported_reason':
        old=m['fc'];m['fc']=lambda a,r,s:old(a,r,s) or a in ('actone','acttwo') and r=='weakreason' and s=='good'
    return m


@lru_cache(None)
def generic():
    args='k zperson[] k zone[] k zqualitycontext[] k zpoint[] p ab p ac p fa p fb p fc p fd p ad p zsecure p zadequate'
    return parse(prefix(('rqwq',))+'q[k rqwq['+args+']].')


def witness_checks():
    rows=0
    for bits in product((False,True),repeat=6):
        supported,secure,adequate=bits[:2],bits[2:4],bits[4:]
        m=model();m.update(fb=lambda j,m,s:j in ('actone','acttwo') and m=='one' and s=='good',
            fd=lambda r,j,s:r=='reason' and j in ('actone','acttwo') and s=='good' and supported[j=='acttwo'],
            zsecure=lambda p,m,j,c,s:(p,m,c,s)==('person','one','now','good') and j in ('actone','acttwo') and secure[j=='acttwo'],
            zadequate=lambda p,m,j,c,s:(p,m,c,s)==('person','one','now','good') and j in ('actone','acttwo') and adequate[j=='acttwo'])
        result=evaluate(generic(),m);want=any(all(x) for x in zip(supported,secure,adequate,strict=True))
        assert result==[want],(bits,result);rows+=1
    cases={}
    for slot,foreign in [(0,'other'),(1,'two'),(2,'acttwo'),(3,'after'),(4,'bad')]:
        m=model();target=['person','one','actone','now','good'];target[slot]=foreign
        m['zadequate']=lambda *args:args==tuple(target)
        result=evaluate(generic(),m);assert result==[False],(slot,result);cases[str(slot)]=result
    for name in ('zsecure','zadequate','fd','fb'):
        m=model();m[name]=unknown
        try:evaluate(generic(),m)
        except ValueError as e:assert 'Unknown qualified' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=rows,foreign_bindings=cases,unknown_inputs_refused=4,
        independent_existential_witnesses_rejected=True)


def reason_checks():
    text=prefix(('rqwr',))+'r zjudgment[] a.q[k rqwr[k zjudgment[] k zpoint[] p fc p fd]].'
    doc=parse(text);count=0
    for usedone,usedtwo,validone,validtwo in product((False,True),repeat=4):
        m=model();m.update(zjudgment=lambda:'actone',
            fc=lambda j,r,s:(j,s)==('actone','good') and (r=='reason' and usedone or r=='weakreason' and usedtwo),
            fd=lambda r,j,s:(j,s)==('actone','good') and (r=='reason' and validone or r=='weakreason' and validtwo))
        want=(usedone or usedtwo) and (not usedone or validone) and (not usedtwo or validtwo)
        assert evaluate(doc,m)==[want];count+=1
    return dict(combinations=count,nonempty_and_all_used_reasons_supported=True,
        not_a_definition_of_infallibility_or_all_judgment_quality=True)


def construction_checks():
    text=prefix(('hzvq',))+'r zinspect[i[h[a] e]] c.q[k zinspect['+CODE+']].'
    doc=parse(text);m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    m['zinspect']=lambda code:code.rank==0 and qualified_task(code)=='one'
    assert evaluate(doc,m)==[True]
    d={**doc,'statements':[]};doc=parse(format_graph(d,'compact')+'q[t[c[s['+CODE+']][k zperson[]]][k zpoint[]]].')
    m=model();m.update(zsecure=unknown,zinspect=unknown)
    try:evaluate(doc,m)
    except ValueError as e:assert 'Unknown qualified' in str(e)
    else:raise AssertionError('Unknown criterion was silently executed')
    return dict(all_four_references_preserved=True,construction_nonfactive=True,explicit_execution_requires_criteria=True)


@lru_cache(None)
def native(mode='ability',alternate=False,concrete=False):
    roots={'ability':('hzvr','hzvs'),'support':('hzvt','hzvu'),'collective':('hzvv','hzvw')}[mode]
    text=prefix(roots,concrete);args=QARGS.replace('r[p zadequate]','r[p zother]') if alternate else QARGS
    if mode=='support':args+=' p zagents p zenabling p zeffects'
    if mode=='collective':
        text+='r zepoch[] a.r zhistory[d] c.r zbefore[d d] c.r zperiods[a d] c.r zpeople[a] c.r zpresent[a d] c.r zstandard[h[a] c h[a] c d] c.r zprogress[] e.'
        args='k zepoch[] p zhistory p zbefore p zperiods p zpeople p zpresent p zstandard '+args
        text+='q[t[k hzvv['+args+']][k zcontext[]]].q[t[k hzvw['+args+' k zprogress[]]][k zcontext[]]].'
    else:
        text+=''.join('q[t[c[k '+n+'['+args+']][k zperson[]]][k zcontext[]]].' for n in roots)
    return parse(text)


def source_checks():
    rows={}
    for variant,secure,adequate,want in [('baseline',True,True,[True,True]),('secure_failure',False,True,[True,False]),
        ('adequate_failure',True,False,[True,False]),('wrong_standard_context',True,True,[False,False]),
        ('wrong_reference',True,True,[False,False]),('unqualified_profile',True,True,[False,False])]:
        result=evaluate(native(),model(variant,secure,adequate));assert result==want,(variant,result);rows[variant]=result
    for variant,want in [('baseline',[False,False]),('alternate_profile',[True,True])]:
        result=evaluate(native(alternate=True),model(variant));assert result==want,(variant,result);rows['alternate_'+variant]=result
    for variant,want in [('baseline',[True,True]),('extra_unsupported_reason',[True,False])]:
        result=evaluate(native(concrete=True),model(variant));assert result==want,(variant,result);rows['composed_criterion_'+variant]=result
    # The old unqualified goal still has a supporting reason in the mixed case.
    doc=parse(prefix(('hzvg',))+'q[t[c[k hzvg[k zone[]]][k zperson[]]][k zpoint[]]].')
    assert evaluate(doc,model('extra_unsupported_reason'))==[True]
    return dict(cases=rows,native_judgment_and_ability_executed=True,
        same_truth_criteria_need_explicit_profile=True,concrete_noema_reason_criterion_executed=True,
        existential_support_not_sufficient_for_stronger_criterion=True)


def integration_checks():
    rows={}
    for variant,secure,want in [('baseline',True,[True,True]),('quality_failure',False,[True,False]),
        ('fixed_scope',True,[True,False]),('split_results',True,[True,False]),('unassessed_after',True,[False,False])]:
        result=evaluate(native('support'),model(variant,secure));assert result==want,(variant,result);rows['support_'+variant]=result
        print('qualified support '+variant+' checked',flush=True)
    domain=(*DOMAIN,'epoch')
    for secure,want in [(True,[True,False]),(False,[False,True])]:
        m=model(secure=secure);m.update(zepoch=lambda:'epoch',zhistory=lambda s:True,zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b),
            zperiods=lambda e,s:(e,s)==('epoch','now'),zpeople=lambda p:p=='person',zpresent=lambda p,s:(p,s)==('person','now'),
            zstandard=lambda people,success,s:s=='now' and all(people(p)==(p=='person') for p in domain) and success('person'),
            zprogress=lambda:Content(SCENES,(True,False,False,False,False,False)))
        result=evaluate(native('collective'),m,domain,max_steps=180000000);assert result==want,(secure,result);rows['collective_'+str(secure)]=result
        print('qualified collective '+str(secure)+' checked',flush=True)
    return dict(cases=rows,same_quality_through_enabling_and_collective_attainment=True,
        collective_step_budget=180000000,initial_60000000_budget_exhausted=True,
        domain_and_definitions_not_reduced=True)


def structure():
    old=parent();new=load_catalog(ROOT,BASIS)
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text,name
    n=len(old.document['declarations']);assert new.document['declarations'][:n]==old.document['declarations']
    assert len(new.document['declarations'])==n+10 and new.document['statements']==old.document['statements']
    assert len(new.document['statements'])==41
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'));validate_hashes(ROOT,index['source_sha256'])
    active=index['works']['kant-1784'];assert active['document']=='examples/v016/kant-explanatory-question.noema'
    cat=load_catalog(ROOT,active['meaning_basis']);assert len(active['reviews'])==10
    for name in active['reviews']:
        r=json.loads((ROOT/name).read_text(encoding='utf-8'));indices=[x['index'] for x in r['selection']['statements']]
        assert selection_binding(cat,indices)==r['selection']==selection_binding(new,indices)
    return dict(new_definitions=10,new_primitives=0,preserved_statements=41,preserved_review_selections=10,roundtrips=True,source_adoption=False)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0014')
    return dict(status='quality_criteria_bound_to_same_judgment_comparison',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[148,412],text=unit['text'][148:412]),
        references=[dict(url='https://korpora.org/Kant/aa08/040.html',lines=[19,22],use='能力の対象が自分の理解力の使用だけでなくsicher und gutの質を伴うことを確認。')],
        decision='判断の質を同じ本人・事柄・判断・時点に結び、同じ閉じた活動記述として現在能力・支援可能性・集団到達へ渡す。具体的な質の基準の原文適合は、この配線の検査とは別に残す。',
        limitations=LIMITS,whole_unit_semantically_verified=False)


def build_report():
    result={}
    for name,fn in [('witnesses',witness_checks),('reasons',reason_checks),('construction',construction_checks),('source',source_checks),('integration',integration_checks),('structure',structure)]:
        result[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note;s=note['source']
    previous='reports/topical-standing-v1.json';validate_hashes(ROOT,json.loads((ROOT/previous).read_text(encoding='utf-8'))['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|{READING,INVENTORY,INDEX,previous,'scripts/compose_qualified_judgment.py','scripts/check_qualified_judgment.py',
        'scripts/check_topical_standing.py','scripts/compose_topical_standing.py','scripts/compose_bodily_acquisition.py','scripts/compose_collective_attainment.py',
        'scripts/compose_falling_depiction.py','tests/test_qualified_judgment.py','docs/qualified-judgment-v1.md','noema/constructed.py',
        'noema/constructed_semantics.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_same_judgment_quality_criteria',document=FULL,**result,
        alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=148,end=412,source=s['text'],definitions=list(MEANINGS),
            status='explicit_interpretive_annotation',full_semantic_equivalence=False),new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Same judgment and qualified task bindings checked',flush=True)


if __name__=='__main__':main()
