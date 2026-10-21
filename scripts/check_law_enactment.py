"""Check complete legal content and same-actor self-imposition, including renewal."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_law_enactment import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure,NAMES,FAMILY
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_scoped_counts import arithmetic

REPORT='reports/law-enactment-v1.json'
DOC='docs/law-enactment-v1.md'
READING='data/law-enactment-reading-v1.json'
PRIORS=('reports/posterity-rights-v1.json','reports/spiritual-guardians-v2.json','reports/self-legislation-v1.json')
DOMAIN=('people','community','law','actor','activity','firstclause','secondclause','thirdclause','p','q','other')
SCENES=('reference','candidate','before','point','outside')
ARGS='k zpeople[] k zcommunity[] k zlaw[]'
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zchoose[a d '+FAMILY+' '+FAMILY+' '+FAMILY+'] '+FAMILY+'.r zperform[j[a] d] c.r zpower[a a a d] c.'
EXTRA+='d ztask[bindings j[a]] e[b point[k zperform[v bindings v point]]].'
EXACT='e[v bindings][l[a][k zlaw[] k zpeople[] k zcommunity[]]]'
for n,relation,person in (('zrequired','h7k','p'),('zallowed','h7l','q')):
    EXTRA+='d '+n+'[bindings j[a]] e[b point[w['+EXACT+'][k '+relation+'[k zlaw[] k z'+person+'[] k zcommunity[] r[p ztask] l[a][k z'+person+'[]] e[v point][v point] v point]]]].'
EXTRA+='d zpowerclause[bindings j[a]] e[b point[w['+EXACT+'][k zpower[k zlaw[] k zpeople[] k zcommunity[] v point]]]].'
PROVIDER='d h26cc[clause a reference d] '+FAMILY+'[k zchoose[v clause v reference r[p zrequired] r[p zallowed] r[p zpowerclause]]].'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    prefix=deepcopy(parent().document);prefix.update(declarations=closure(prefix,['h7k','h7l']),statements=[])
    provided=parse(format_graph(prefix,'compact')+EXTRA+PROVIDER)
    ns={d['name'] for d in provided['declarations']}
    doc['declarations']=provided['declarations']+[d for d in doc['declarations'] if d['name'] not in ns]
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def model(doc,variant='baseline',states=(True,True,True),actor='people'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(arithmetic());v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)});v['h26b7']=lambda:'reference'
    population={'empty_people':(),'duplicate_people':('p','p','q'),'missing_person':('p',),'extra_person':('p','q','other')}.get(variant,('p','q'))
    v['mp']=lambda g:SequenceValue(population if g=='people' else (),'"individual"')
    v['aa']=lambda p:p in ('p','q') and not(variant=='nonhuman' and p=='q')
    v['h237c']=lambda p,c,r:p in ('p','q') and(c,r)==('community','reference')
    v['h26ca']=lambda l,c,r:variant!='not_public_law' and(l,c,r)==('law','community','reference')
    clauses=('firstclause','secondclause','thirdclause')
    v['h26cb']=lambda l,c,r:variant!='empty_law' and(l,r)==('law','reference') and c in clauses
    def choose(clause,reference,first,second,third):
        assert reference in SCENES
        return dict(zip(clauses,(first,second,third))).get(clause,first)
    v['zchoose']=choose
    at='outside' if variant=='outside_history' else 'point'
    def operative(index,t):
        return states[index] and (t==at or(variant=='reconfirmation' and t=='before')) and not(variant=='split_times' and index==0 and t==at)
    def norm(i,s,p,r,c,b,sign,t):
        return operative(i,t) and(s,p,r,symbol(c),c.rank,tuple(b.items),sign)==('law',('p','q')[i],'community','ztask',0,(('p','q')[i],),True)
    v['h7k']=lambda *a:norm(0,*a);v['h7l']=lambda *a:norm(1,*a)
    v['zpower']=lambda l,p,c,t:operative(2,t) and(l,p,c)==('law','people','community')
    v['dg']=lambda a,t:variant!='no_activity' and(a,t)==('activity',at)
    def adoption(a,s,p,c,l,r,h,t):
        expected=['activity',actor,'people','community','law','reference','candidate',at]
        for i,k in enumerate(('activity','actor','people','community','law','reference','candidate','point')):
            if variant=='other_'+k:expected[i]='other' if i<5 else 'outside'
        return (a,s,p,c,l,r,h,t)==tuple(expected)
    v['h26cd']=adoption
    v['h26ce']=lambda a,p,c,l,r,h,t:variant!='no_effect' and(a,p,c,l,r,h,t)==(
        'other' if variant=='split_effect_activity' else 'activity','people','community','law','reference','candidate',at)
    v['h257z']=lambda r,h,t:(r,h)==('reference','candidate') and t in ('before','point')
    v['ic']=lambda a,b,h:h=='candidate' and ((a,b)==('before','point') or(variant=='cycle' and(a,b)==('point','before')))
    return v
def unknown_check(doc,names):
    for name in names:
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return list(names)

@lru_cache(None)
def scope_checks():
    doc=fixture(('r5ei',),'q[k r5ei['+ARGS+' k zreference[]]].');rows={}
    for variant in ('baseline','empty_people','duplicate_people','missing_person','extra_person','nonhuman','not_public_law','empty_law'):
        v=model(doc,variant);v['h7k']=unknown;v['h7l']=unknown;v['zpower']=unknown
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(complete_nonempty_people_and_law=rows,clause_states_not_evaluated=True,
        unknown_rejected=unknown_check(doc,('mp','aa','h237c','h26ca','h26cb')))

@lru_cache(None)
def provision_checks():
    doc=fixture(('r5ej',),'q[k r5ej['+ARGS+' k zreference[] k zpoint[]]].');rows={}
    for bits in product((False,True),repeat=3):
        v=model(doc,states=bits);actual=run(doc,v);assert actual==[all(bits)];rows[str(bits)]=actual[0]
        assert v['zperform'] is unknown
    contrasts={}
    for variant in ('empty_law','split_times','reconfirmation'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='reconfirmation'];contrasts[variant]=actual[0]
    # Exercise all three positions of the exact inner law/people/community list.
    for i in range(3):
        names=['law','people','community'];names[i]='other'
        extra='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
        q=''.join('q[t[k '+n+'['+extra+']][k zpoint[]]].' for n in ('zrequired','zallowed','zpowerclause'))
        d=fixture((),q);assert run(d,model(d))==[False]*3
    return dict(all_three_distinct_normative_clauses=rows,same_point_and_nonempty_scope=contrasts,
        target_actions_not_executed=True,inner_three_positions_checked=True,
        unknown_rejected=unknown_check(doc,('zchoose','h7k','h7l','zpower')))

@lru_cache(None)
def enactment_checks():
    query='q[k r5ek[k zpeople[] '+ARGS+' k zactivity[] k zreference[] k zcandidate[] k zpoint[]]].'
    doc=fixture(('r5ek',),query);rows={}
    for variant in ('baseline','reconfirmation','no_activity','no_effect','split_effect_activity','split_times',
                    *('other_'+k for k in ('activity','actor','people','community','law','reference','candidate','point'))):
        v=model(doc,variant);actual=run(doc,v);assert actual==[variant in ('baseline','reconfirmation')],(variant,actual);rows[variant]=actual[0]
    return dict(native_same_act_actor_people_and_legal_effect=rows,
        unknown_rejected=unknown_check(doc,('dg','h26cd','h26ce')),
        no_required_prior_absence=True)

@lru_cache(None)
def self_checks():
    doc=fixture(('r5el','r5em'),'q[k r5el[k zactor[] '+ARGS+' k zreference[] k zcandidate[]]].q[k r5em['+ARGS+' k zreference[] k zcandidate[]]].');rows={}
    for actor in ('people','actor'):
        actual=run(doc,model(doc,actor=actor));assert actual==([False,True] if actor=='people' else [True,False]);rows[actor]=actual
    d=fixture(('r5em',),'q[k r5em['+ARGS+' k zreference[] k zcandidate[]]].')
    for variant in ('baseline','reconfirmation','outside_history','cycle','missing_person','no_effect'):
        actual=run(d,model(d,variant));assert actual==[variant in ('baseline','reconfirmation')];rows[variant]=actual
    return dict(native_self_imposition_and_complete_history=rows,
        unknown_rejected=unknown_check(d,('h257z','ic','h26ce')),no_definition_boundaries=True,
        actual_vote_unanimity_and_moral_permission_not_added=True)

@lru_cache(None)
def binding_checks():
    matrices={};small=('alpha','beta')
    for root in ('r5en','r5eo'):
        def case(i,j,length=0):
            names=list(NAMES)
            if length<0:names.pop()
            if length>0:names.append('law')
            seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
            query='q[t[k '+root+'['+seq+(' k zreference[]' if root=='r5en' else '')+']][k zcandidate[]]].'
            doc=fixture((root,),query,('r5em',));v=model(doc)
            v.update({'z'+n:lambda k=k:'beta' if k==i else 'alpha' for k,n in enumerate(NAMES)})
            expected=tuple('beta' if k==j else 'alpha' for k in range(3))
            v['r5em']=lambda *a:a==(*expected,'reference','candidate')
            return run(doc,v,small)[0]
        matrix=[]
        for i,j in product(range(3),repeat=2):
            actual=case(i,j);assert actual==(i==j);matrix.append(actual)
        assert not case(0,0,-1) and not case(0,0,1);matrices[root]=matrix
    return dict(exact_outer_three_positions=matrices,wrong_lengths_rejected=True,boundary='r5em only; native self-imposition checked separately')

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    page='artifacts/law-enactment-v1/page-489.jpg'
    return dict(status='law_enactment_and_self_imposition_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1265,1436],text=u['text'][1265:1436]),
        primary_pages=[read('data/covenant-question-reading-v1.json')['original_page'],dict(path=page,
            url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00529/full/full/0/default.jpg',
            sha256=digest((ROOT/page).read_bytes()),visually_inspected=True)],
        corroboration=dict(url='https://korpora.org/kant/aa08/039.html',lines='13–15',
            observation='原刊489頁と固定原文は問いを疑問符で終える。AA版の同箇所は句点だが、ob以下の間接疑問である点は同じ。固定原文を変更しない。'),
        adopted_readings=LIMITS,remaining=['立法の資格と合理的な自己賦課の候補範囲','kann/könnteとwohl',
            '試金石の判断基準・全対象・問いと著者帰属','全文の通読'],new_verified_characters=0,whole_sentence_semantically_verified=False)
@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p in read(READING)['primary_pages']:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==101
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=101)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in [('scope',scope_checks),('provisions',provision_checks),('enactment',enactment_checks),('self',self_checks),('bindings',binding_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],
        *(p['path'] for p in read(READING)['primary_pages']),'scripts/compose_law_enactment.py','scripts/check_law_enactment.py',
        'tests/test_law_enactment.py','scripts/compose_self_legislation.py','scripts/compose_normative_powers.py',
        'scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='law_enactment_and_self_imposition_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
