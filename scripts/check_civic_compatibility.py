"""Check fallible improvement beliefs, exact names and joint civil conditions."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_compatibility import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import SCENES,DOMAIN,EXTRA

REPORT='reports/civic-compatibility-v1.json'
READING='data/civic-compatibility-reading-v1.json'
DOC='docs/civic-compatibility-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/monarchical-sentence-v1.json','reports/reform-proposals-v1.json','reports/perceived-doctrinal-conflict-v1.json')
A='k zalpha[]';B='k zbeta[]';R='k zreference[]';P='k zcandidate[]'
PROVIDERS='''
r zthird[] a.r znamepick[a i[a] i[a] i[a]] i[a].r zrefpick[d i[d] i[d]] i[d].
r zcontentpick[a d i[e] i[e] i[e]] i[e].r ztruth[a d] c.r zsave[i[e]] c.
d zfirstbody[] e[b point[k ztruth[k zalpha[] v point]]].
d zsecondbody[] e[b point[k ztruth[k zbeta[] v point]]].
d zthirdbody[] e[b point[k ztruth[k zthird[] v point]]].
d h223g[item a] i[a][k znamepick[v item r[k zalpha[]] r[k zbeta[]] r[k zthird[]]]].
d h223h[point d] i[d][k zrefpick[v point r[k zreference[]] r[k zassessment[]]]].
d h246e[form a reference d] i[e][k zcontentpick[v form v reference r[k zfirstbody[]] r[k zsecondbody[]] r[k zthirdbody[]]]].
'''

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    prefix=parse('p:'+EXTRA+PROVIDERS)
    providers={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in providers]+[providers.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(s in points for s in SCENES))
def base(d,bindings=('alpha',)*4):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES,'third')})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),aa=lambda p:p in DOMAIN,
        znamepick=lambda obj,a,b,c:{'alpha':a,'beta':b,'third':c}[obj],
        zrefpick=lambda p,r,a:r if p=='reference' else a,
        zcontentpick=lambda obj,r,a,b,c:{'alpha':a,'beta':b,'third':c}[obj] if r=='reference' else c)
    return v

@lru_cache(None)
def comparison_checks():
    d=fixture('q[t[k r5mx['+' '.join((A,B,A,A,R))+']][k zcandidate[]]].');rows={}
    for reflexive_old,reflexive_new,forward,reverse in product((False,True),repeat=4):
        v=base(d);pairs={('alpha','alpha'):reflexive_old,('beta','beta'):reflexive_new,('beta','alpha'):forward,('alpha','beta'):reverse}
        v['h26ha']=lambda s,f,l,r,ref,p:(s,f,ref,p)==('alpha','alpha','reference','candidate') and pairs[l,r]
        actual=run(d,v);assert actual==[reflexive_old and reflexive_new and forward and not reverse]
        rows[str((reflexive_old,reflexive_new,forward,reverse))]=actual[0]
    d=fixture('q[t[k r5my[k zbindings[] '+R+']][k zcandidate[]]].',('r5mx',));positions=[]
    for i in range(4):
        b=tuple('beta' if j==i else 'alpha' for j in range(4));v=base(d,b)
        v['r5mx']=lambda *a:content({'candidate'}) if a==(*b,'reference') else content(set())
        assert run(d,v)==[True];v['zbindings']=lambda:SequenceValue(('alpha',)*4,'"individual"');assert run(d,v)==[False];positions.append(i)
    for length in (3,5):v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
    return dict(strict_not_equal_incomparable_or_nonreflexive=rows,all_four_adapter_positions=positions,boundary_only_for_adapter='r5mx')

@lru_cache(None)
def scope_checks():
    positions=[]
    for i in range(6):
        b=tuple('beta' if j==i else 'alpha' for j in range(6))
        args=' '.join('k z'+x+'[]' for x in b)
        d=fixture('q[k r5mw['+args+' '+R+']].');v=base(d)
        v['h26g6']=lambda *a:a==(*b,'reference')
        v['h26g7']=lambda f,c,r:(f,c,r)==(b[1],b[2],'reference')
        assert run(d,v)==[True]
        v['zbeta']=lambda:'alpha';assert run(d,v)==[False];positions.append(i)
    for relation in ('h26g6','h26g7'):
        v=base(d);v['h26g6']=lambda *a:True;v['h26g7']=lambda *a:True;v[relation]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(relation)
    return dict(all_six_transition_bindings=positions,unknown_rejected=True,qualification_not_used_to_select_candidates=True)

@lru_cache(None)
def belief_checks():
    # The saved literal specialization is independent of the provider path.
    literal='k r5mz[r[k zalpha[]] r[k zbeta[]] r[k zalpha[]] r[k zalpha[]] r[k zreference[]]]'
    query='q[k zsave['+literal+']].q[k r5m3['+' '.join((A,A,B,A,A,R,P))+']].'
    rows={}
    for variant in ('baseline','false_belief','no_belief','other_person','other_point','wrong_name','wrong_reference_name','wrong_order','unknown'):
        selected=query
        if variant=='wrong_order':
            reversed_literal='k r5mz[r[k zbeta[]] r[k zalpha[]] r[k zalpha[]] r[k zalpha[]] r[k zreference[]]]'
            selected=query.replace('q[k zsave['+literal+']].','q[k zsave['+reversed_literal+']].')
        d=fixture(selected)
        v=base(d);saved=[];v['zsave']=lambda code:saved.append(code) is None
        v['h26ha']=unknown;v['ztruth']=unknown
        def belief(p,code,at):
            return variant!='no_belief' and (p,at)==('beta' if variant=='other_person' else 'alpha','end' if variant=='other_point' else 'candidate') and code.rank==0 and code.syntax==saved[0].syntax
        v['h233c']=belief
        if variant=='wrong_name':v['znamepick']=lambda obj,a,b,c:a
        if variant=='wrong_reference_name':v['zrefpick']=lambda p,r,a:a
        if variant=='unknown':
            v['h233c']=unknown
            try:run(d,v)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown belief accepted')
            continue
        actual=run(d,v)
        expected=variant in ('baseline','false_belief')
        assert actual==[True,expected],(variant,actual);rows[variant]=actual[1]
    positions=[]
    for i in range(4):
        b=['alpha']*4;b[i]='beta'
        args=' '.join('k z'+x+'[]' for x in b)
        literal='k r5mz['+' '.join('r[k z'+x+'[]]' for x in b)+' r[k zreference[]]]'
        d=fixture('q[k zsave['+literal+']].q[k r5m3['+A+' '+args+' '+R+' '+P+']].')
        v=base(d);saved=[];v['zsave']=lambda code:saved.append(code) is None
        v['h233c']=lambda p,code,at:code.syntax==saved[0].syntax and (p,at)==('alpha','candidate')
        assert run(d,v)==[True,True];v['znamepick']=lambda obj,a,b,c:a;assert run(d,v)==[True,False];positions.append(i)
    return dict(fallible_belief_with_unevaluated_comparison=rows,all_four_name_positions=positions,unknown_rejected=True,actual_comparison_and_realization_not_executed=True)

@lru_cache(None)
def selection_checks():
    args=' '.join((A,A,A,A,B,A,R,P));d=fixture('q[k r5m4['+args+']].',('r5mx','r5m3'));rows={}
    for true,believed in product((False,True),repeat=2):
        v=base(d);v['h26g7']=lambda *a:a==('alpha','alpha','reference')
        v['h26g6']=lambda *a:a==('alpha','alpha','alpha','alpha','beta','alpha','reference')
        v['r5mx']=lambda *a:content({'candidate'}) if true and a==('alpha','beta','alpha','alpha','reference') else content(set())
        v['r5m3']=lambda p,*a:believed and p=='beta' and a==('alpha','beta','alpha','alpha','reference','candidate')
        actual=run(d,v);assert actual==[true or believed];rows[str((true,believed))]=actual[0]
    for name in ('h26g7','h26g6'):
        saved=v[name];v[name]=lambda *a:False;assert run(d,v)==[False];v[name]=saved
    return dict(inclusive_genuine_or_believed=rows,belief_not_limited_to_ruler=True,boundaries=['r5mx','r5m3'])

@lru_cache(None)
def compatibility_checks():
    # Two distinct civil conditions plus a third realization content.
    args=' '.join((A,A,A,A,'k zthird[]',A,A,R))
    d=fixture('q[k r5m7['+args+']].');rows={}
    for variant in ('baseline','only_possible_not_actual','split_conditions','split_change_and_order','no_change','no_order_condition','empty_order','empty_candidates','not_civil','wrong_change','wrong_order','wrong_reference','unknown_condition'):
        v=base(d)
        v['h26g7']=lambda *a:a==('alpha','alpha','reference')
        v['h26g6']=lambda *a:a==('alpha','alpha','alpha','alpha','third','alpha','reference')
        v['h26hb']=lambda *a:a==('alpha','alpha','reference') and variant!='not_civil'
        v['h26hc']=lambda o,c,r:(o,r)==('alpha','reference') and c in DOMAIN and variant!='empty_order'
        def selected(change,order,ref,at):
            return (change,order,ref)==('beta' if variant=='wrong_change' else 'alpha','beta' if variant=='wrong_order' else 'alpha','assessment' if variant=='wrong_reference' else 'reference') and at in ('start','end') and variant!='empty_candidates'
        v['h26hd']=selected
        truth={('alpha','end'),('beta','end'),('third','end')}
        if variant=='split_conditions':truth={('alpha','start'),('beta','end'),('third','start'),('third','end')}
        if variant=='split_change_and_order':truth={('alpha','end'),('beta','end'),('third','start')}
        if variant=='no_change':truth={('alpha','end'),('beta','end')}
        if variant=='no_order_condition':truth={('alpha','end'),('third','end')}
        v['ztruth']=lambda obj,p:(obj,p) in truth
        if variant=='unknown_condition':
            v['ztruth']=unknown
            try:run(d,v,(*DOMAIN,'third'))
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Unknown condition accepted')
            continue
        actual=run(d,v,(*DOMAIN,'third'));assert actual==[variant in ('baseline','only_possible_not_actual')],(variant,actual);rows[variant]=actual[0]
        assert v['h26ha'] is unknown and v['h233c'] is unknown
    queries=''.join('q[k r5m7['+' '.join(('k z'+ch+'[]',A,A,'k zthird[]','k z'+ch+'[]',A,A,R))+']].' for ch in DOMAIN)
    queries+='q[g point d[w[t[k zfirstbody[]][v point]][t[k zsecondbody[]][v point]]]].'
    d=fixture(queries);v=base(d)
    v['h26g7']=lambda *a:a==('alpha','alpha','reference')
    v['h26g6']=lambda ch,f,c,o,n,s,r:(f,c,o,s,r)==('alpha','alpha','third','alpha','reference') and ch==n and ch in DOMAIN
    v['h26hb']=lambda *a:a==('alpha','alpha','reference')
    v['h26hc']=lambda *a:a==('alpha','third','reference')
    v['h26hd']=lambda ch,o,r,p:(o,r)==('alpha','reference') and p==('start' if ch=='alpha' else 'end')
    v['ztruth']=lambda obj,p:(obj,p) in {('alpha','start'),('beta','end'),('third','start'),('third','end')}
    alternatives=run(d,v,(*DOMAIN,'third'));assert alternatives==[True,True,False]
    return dict(same_possible_situation_for_change_and_every_order_condition=rows,each_alternative_can_coexist_without_joint_adoption=alternatives,
        compatibility_does_not_require_objective_improvement=True,unknown_rejected=True,boundaries=[])

@lru_cache(None)
def universal_checks():
    d=fixture('q[t[k r5nb['+A+' '+B+' '+R+']][k zcandidate[]]].',('r5mw','r5m4','r5m7','r5m5','r5m2'));rows={}
    for variant in ('baseline','missing_second_change','neither_true_nor_believed','empty_change_scope','invalid_name','wrong_community','wrong_order','wrong_reference','wrong_assessment'):
        v=base(d);v['r5m5']=lambda *a:a==('beta','alpha','reference')
        v['r5mw']=lambda ch,f,c,o,n,s,r:(f,c,o,n,s,r)==('alpha','alpha','alpha','beta','alpha','reference') and variant!='empty_change_scope'
        v['r5m2']=lambda *a:variant!='invalid_name'
        def qualifies(ch,f,c,o,n,s,r,p):
            return variant!='neither_true_nor_believed' and (f,c,o,n,s,r,p)==('alpha','alpha','alpha','beta','alpha','reference','end' if variant=='wrong_assessment' else 'candidate')
        v['r5m4']=qualifies
        def compatible(ch,f,c,o,n,s,order,r):
            wanted=('alpha','beta' if variant=='wrong_community' else 'alpha','alpha','beta','alpha','alpha' if variant=='wrong_order' else 'beta','assessment' if variant=='wrong_reference' else 'reference')
            return (f,c,o,n,s,order,r)==wanted and not(variant=='missing_second_change' and ch=='beta')
        v['r5m7']=compatible
        actual=run(d,v)
        # A different assessment can legitimately change which items qualify.
        want=variant in ('baseline','neither_true_nor_believed','empty_change_scope','wrong_assessment')
        assert actual==[want],(variant,actual);rows[variant]=actual[0]
    return dict(all_changes_fixed_context_and_nonvacuous_name_validation=rows,boundaries=['r5mw','r5m4','r5m7','r5m5','r5m2'],no_joint_adoption_of_all_alternatives_required=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    pages=[p for p in read('data/personal-enlightenment-choice-reading-v1.json')['primary_pages'] if 'page-490' in p['path']]
    return dict(status='partial_genuine_or_believed_improvement_and_civil_compatibility',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3256,3341],text=u['text'][3256:3341]),
        interpretation=LIMITS,new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,primary_pages=pages,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',lines='3–10',observation='原刊490頁を再表示し第十一文を通読。真又は見かけの改善、秩序との両立、臣民の自己判断と妨害防止の後続を区別。')],
        unresolved=['君主が両立を確保する監督とWenn/nurの限定','同じ臣民の救済目的と必要性の自己判断','委ねる範囲と君主の職責','暴力的妨害の防止と全能力での営み','全ての照応・談話提示・全文判断'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old.entries[n]['declaration'] and c.entries[n]['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    assert read(READING)==reading_record() and len(old.document['statements'])==106
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,preserved_main_statements=106,semantic_review_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('comparison',comparison_checks),('scope',scope_checks),('belief',belief_checks),('selection',selection_checks),('compatibility',compatibility_checks),('universal',universal_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,*(x['path'] for x in read(READING)['primary_pages']),
        'scripts/compose_civic_compatibility.py','scripts/check_civic_compatibility.py','tests/test_civic_compatibility.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_persistent_compact_progress.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='genuine_or_believed_improvement_jointly_compatible_with_civil_order',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
