"""Check nonexemption, joint fulfillment and complete typed duty coverage."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_preserved_public_duties import ROOT,LIBRARY,BASIS,CODE,RULE,MEANINGS,LIMITS,BASE,PROVIDERS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/preserved-public-duties-v1.md';READING='data/preserved-public-duties-reading-v1.json'
INDEX='data/semantic-review-index-v197.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/confessional-divergence-v1.json','reports/scholarly-mission-v1.json','reports/prince-sentence-v1.json')
DOMAIN=('person','office','issuer','positive','negative','other','activity','scholar','audience','church','creed','subject','source')
SCENES=('anchor','good','bad')
def z(n):return 'k z'+n+'[]'
def ns(names):return ' '.join(z(n) for n in names)
def codeid(c):return c.rank,json.loads(c.syntax)
PROVIDED='p zitems p zissuers p ztargets p zbindings p zreferences p zsigns'
B=ns(('person','office','anchor'))+' '+PROVIDED+' p zrequired'
CASE=B+' k ztrigger[] p zcases'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def restrict_coverage(row):
    """Diagnostic only: preserve all other quantifiers and replace two domains."""
    true=parse('p:q[e[n p a b][n p a b]].')['statements'][0]['body']
    templates=parse('p:r zperson[] a.r zother[] a.r zpositive[j[a] d] e.r znegative[j[a] d] e.'+
        'q[e[l['+CODE+'][r b[p zpositive] r b[p znegative]]][l['+CODE+'][]]].q[e[l[j[a]][l[a][k zperson[]] l[a][k zother[]]]][l[j[a]][]]].')
    codes,bindings=[s['body']['arguments'][0] for s in templates['statements']]
    count=0
    def walk(x):
        nonlocal count
        if isinstance(x,list):return [walk(y) for y in x]
        if not isinstance(x,dict):return x
        if x.get('kind')=='forall' and isinstance(x['sort'],dict) and x['sort']['kind'] in ('description','sequence'):
            count+=1;body=walk(x['body']);ok='coverageacc'+str(count)
            return dict(kind='fold',sequence=deepcopy(codes if x['sort']['kind']=='description' else bindings),initial=deepcopy(true),
                step=dict(kind='lambda',parameters=[dict(name=ok,sort='truth'),dict(name=x['variable'],sort=x['sort'])],
                    body=dict(kind='and',arguments=[dict(kind='variable',name=ok),body])))
        return {k:walk(v) for k,v in x.items()}
    row['body']=walk(row['body']);assert count==2

@lru_cache(None)
def fixture(roots,query,coverage='native',source=False):
    d=deepcopy(catalog().document)
    if coverage=='finite':restrict_coverage(next(x for x in d['declarations'] if x['name']=='r54c'))
    if source:
        row=next(x for x in d['declarations'] if x['name']=='r54f');row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES) if n not in ('positive','negative'))
    extra+='r zdutypos[] a.r zdutyneg[] a.r zvalue[a j[a] d d] c.'
    for name,tag in (('zpositive','zdutypos'),('znegative','zdutyneg')):
        extra+='d '+name+'[bindings j[a] reference d] e[b point[k zvalue[k '+tag+'[] v bindings v reference v point]]].'
    extra+='r ztargetpick[a '+CODE+' '+CODE+'] '+CODE+'.d ztargets[item a] '+CODE+'[k ztargetpick[v item r b[p zpositive] r b[p znegative]]].'
    extra+='r zitems[a] c.r zissuers[a] a.d zbindings[item a] j[a][l[a]['+z('person')+']].r zreferences[a] d.r zsigns[a] c.r zrequired[a a a '+CODE+' j[a] d c d] c.'
    extra+='r ztriggers[d] c.d ztrigger[] e[b point[k ztriggers[v point]]].r zcases[d] c.'
    extra+='r zcompare[a d] c.r zsavetarget['+CODE+'] c.r zpublic[j[a] d d] c.'
    if source:
        extra+='d r535[judgments j[a] insights j[a] comparisons h[a d] c bindings j[a] reference d] e[b point[k zpublic[v bindings v reference v point]]].'
    provider=parse('p:'+extra);replaced={x['name'] for x in provider['declarations']}
    d['declarations']=provider['declarations']+[x for x in d['declarations'] if x['name'] not in replaced]
    helpers=[x['name'] for x in provider['declarations']]
    d.update(declarations=closure(d,(*roots,*helpers)),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def model(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES) if n not in ('positive','negative')})
    v.update(zdutypos=lambda:'positive',zdutyneg=lambda:'negative')
    v['zitems']=lambda i:i in ('positive','negative')
    v['zissuers']=lambda i:'issuer';v['zreferences']=lambda i:'anchor';v['zsigns']=lambda i:i=='positive'
    v['ztargetpick']=lambda i,p,n:p if i=='positive' else n
    def required(issuer,p,office,code,binding,ref,sign,point):
        tag=codeid(code)[1].get('symbol')
        return (issuer,p,office,tuple(binding.items),ref)==('issuer','person','office',('person',),'anchor') and (tag,sign) in (('zpositive',True),('znegative',False))
    v['zrequired']=required
    v['zvalue']=lambda tag,b,r,t:tuple(b.items)==('person',) and r=='anchor' and ((tag=='positive' and t=='good') or(tag=='negative' and t=='bad'))
    v['ztriggers']=lambda t:t=='good';v['zcases']=lambda t:t in ('good','bad')
    v['zsavetarget']=lambda c:saved.update(target=codeid(c)) is None
    return v,saved

@lru_cache(None)
def preservation_checks():
    q='q[k r537['+B+']].q[k r54a['+B+' '+z('good')+']].q[k r54b['+B+' '+z('good')+']].'
    d=fixture(('r537','r54a','r54b'),q);rows={}
    for case in ('baseline','not_required','exempted','changed_sign','changed_issuer','unfulfilled','contradictory'):
        v,_=model(d)
        if case=='not_required':v['zrequired']=lambda *a:False
        if case in ('exempted','changed_sign','changed_issuer'):
            old=v['zrequired']
            def revised(issuer,p,o,c,b,r,sign,t,old=old,case=case):
                if t=='anchor':return old(issuer,p,o,c,b,r,sign,t)
                if case=='exempted':return False
                return old('other' if case=='changed_issuer' else issuer,p,o,c,b,r,not sign if case=='changed_sign' else sign,t)
            v['zrequired']=revised
        if case=='unfulfilled':v['zvalue']=lambda *a:True
        if case=='contradictory':
            v['ztargetpick']=lambda i,p,n:p
            old=v['zrequired'];v['zrequired']=lambda issuer,p,o,c,b,r,s,t:(issuer,p,o,tuple(b.items),r)==('issuer','person','office',('person',),'anchor') and codeid(c)[1].get('symbol')=='zpositive'
        expected=[case!='not_required',case not in ('not_required','exempted','changed_sign','changed_issuer'),case=='baseline']
        got=run(d,v);assert got==expected,(case,got);rows[case]=got
    pure=fixture(('r54a',),'q[k r54a['+B+' '+z('good')+']].');v,_=model(pure);v['zvalue']=unknown;assert run(pure,v)==[True]
    for n in ('zrequired','zvalue','ztargetpick'):
        v,_=model(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return dict(cases=rows,requirements_not_their_fulfillment=True,positive_and_negative_duties_preserved=True,unknown_rejected=True)

@lru_cache(None)
def coverage_checks():
    q='q[k r54d['+B+']].';full=fixture(('r54d',),q);v,_=model(full)
    try:run(full,v)
    except ValueError as e:assert 'Cannot finitely quantify the description domain' in str(e)
    else:raise AssertionError('Full description domain enumerated')
    limited=fixture(('r54d',),q,'finite');rows={}
    for case in ('baseline','omitted_negative','extra_issuer','extra_binding','extra_reference','extra_sign','empty_with_requirements','empty_without_requirements'):
        v,_=model(limited)
        if case=='omitted_negative':v['zitems']=lambda i:i=='positive'
        if case.startswith('empty'):v['zitems']=lambda i:False
        if case=='empty_without_requirements':v['zrequired']=lambda *a:False
        if case.startswith('extra'):
            old=v['zrequired']
            def extra(issuer,p,o,c,b,r,s,t,old=old,case=case):
                changed=(issuer=='other' if case=='extra_issuer' else tuple(b.items)==('other',) if case=='extra_binding' else r=='bad' if case=='extra_reference' else s is False)
                return old(issuer,p,o,c,b,r,s,t) or (changed and p=='person' and o=='office' and codeid(c)[1].get('symbol')=='zpositive')
            v['zrequired']=extra
        got=run(limited,v);expected=case in ('baseline','empty_without_requirements');assert got==[expected],(case,got);rows[case]=got[0]
    return dict(full_domain_rejected=True,limited_diagnostic=rows,
        limits='Only the two universal code/list domains are replaced by two explicit values each. All other quantifiers and the exact matching body remain native. This is not evidence of full semantic-domain completeness.')

@lru_cache(None)
def compatibility_checks():
    q=''.join('q[k '+n+'['+CASE+']].' for n in ('r54e','r54f','r54g'))
    d=fixture(('r54e','r54f','r54g'),q,'finite');rows={}
    for case in ('baseline','some_harmful_instance','only_harmful_instance','no_instance','empty_cases','exempted','split_fulfillment'):
        v,_=model(d)
        if case=='some_harmful_instance':v['ztriggers']=lambda t:t in ('good','bad')
        if case=='only_harmful_instance':v['ztriggers']=lambda t:t=='bad'
        if case=='no_instance':v['ztriggers']=lambda t:False
        if case=='empty_cases':v['zcases']=lambda t:False
        if case=='exempted':old=v['zrequired'];v['zrequired']=lambda *a:old(*a) and a[-1]=='anchor'
        if case=='split_fulfillment':
            v['ztriggers']=lambda t:t in ('good','bad')
            v['zvalue']=lambda tag,b,r,t:tuple(b.items)==('person',) and r=='anchor' and t=='good'
        expected={'baseline':[True,True,True],'some_harmful_instance':[True,True,False],
            'only_harmful_instance':[True,False,False],'no_instance':[True,False,False],
            'empty_cases':[False,False,False],'exempted':[False,False,False],'split_fulfillment':[True,False,False]}[case]
        got=run(d,v);assert got==expected,(case,got);rows[case]=got
    return dict(cases=rows,same_candidate_required=True,nonexemption_vs_joint_compatibility_vs_no_restriction_distinct=True,
        boundary='Same explicitly bounded coverage diagnostic as coverage_checks; preservation, target dequotation, signed fulfillment and candidate quantifiers execute natively.')

@lru_cache(None)
def source_checks():
    target='k r536[r[l[a][]] r[l[a][]] r[p zcompare]]';binding='l[a]['+ns(NAMES)+']'
    source=ns(NAMES)+' '+ns(('source','office','anchor','anchor'))+' r[l[a][]] r[l[a][]] r[p zcompare] '+PROVIDED+' p zcases'
    q='q[k zsavetarget['+target+']].q[k r54h['+source+']].';d=fixture(('r54h',),q,source=True)
    def setup():
        v,saved=model(d)
        v['zpublic']=lambda b,r,t:tuple(b.items)==NAMES and r=='anchor' and t=='good'
        v['h245c']=lambda source,p,role,code,b,r,sign,t:(source,p,role,tuple(b.items),r,sign,t)==('source','person','scholar',NAMES,'anchor',True,'anchor') and codeid(code)==saved['target']
        v['h237z']=lambda source,p,role,code,b,r,sign,t:role=='office'
        def compatible(p,o,a,items,issuers,targets,bindings,refs,signs,required,trigger,cases):
            return (p,o,a)==('person','office','anchor') and tuple(i for i in DOMAIN if items(i))==('positive','negative') and issuers('positive')=='issuer' and tuple(bindings('positive').items)==('person',) and refs('positive')=='anchor' and signs('positive') is True and signs('negative') is False and codeid(targets('positive'))[1].get('symbol')=='zpositive' and required('issuer','person','office',targets('positive'),bindings('positive'),'anchor',True,'anchor') is True and trigger.values==(False,True,False) and cases('good') is True
        v['r54f']=compatible
        return v
    rows={}
    for case in ('baseline','no_permission','opposite_required','no_compatibility','wrong_public_binding','wrong_duty_issuer','empty_duties'):
        v=setup()
        if case=='no_permission':v['h245c']=lambda *a:False
        if case=='opposite_required':v['h237z']=lambda *a:True
        if case=='no_compatibility':v['r54f']=lambda *a:False
        if case=='wrong_public_binding':v['zpublic']=lambda *a:False
        if case=='wrong_duty_issuer':v['zissuers']=lambda i:'other'
        if case=='empty_duties':v['zitems']=lambda i:False
        got=run(d,v);assert got==[True,case=='baseline'],(case,got);rows[case]=got[-1]
    return dict(cases=rows,same_constructed_target_for_permission_and_comparison=True,current_actual_publication_not_required=True,
        source_and_duty_issuer_distinct=True,
        boundary='r535 is an exact seven-binding public-content boundary and r54f checks the same complete signature and trigger. r536 and r37c execute natively; the full public action and duty constraints retain their separate prior/current native evidence.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='preserved_office_duties_and_public_freedom_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[574,889],text=u['text'][574:889]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ職務の完全な義務項目と比較候補の本文供給','君主への照応と聖職者の敬意評価','全発表候補への量化・無制約の他者・noch mehr','全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for source in parents():
        for n,e in c.entries.items():
            if n in source.entries:assert e['declaration']==source.entries[n]['declaration'] and e['meaning_ja']==source.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==113
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    try:parse(t+'q[e[r b[p r54h]][r b[p r54h]]].')
    except ValueError as e:assert 'Quoted evaluation' in str(e)
    else:raise AssertionError('Low-rank quote accepted')
    parse(t+'q[e[r c[p r54h]][r c[p r54h]]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=0,main_statements_preserved=113,new_verified_characters=0,
        inherited_meanings_preserved=True,rank_two_combined_condition=True,roundtrips=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('preservation',preservation_checks),('coverage',coverage_checks),('compatibility',compatibility_checks),('source',source_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_preserved_public_duties.py','scripts/check_preserved_public_duties.py','tests/test_preserved_public_duties.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_confessional_divergence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='complete_signed_duties_and_public_freedom_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
