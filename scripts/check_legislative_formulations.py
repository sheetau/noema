"""Check complete content representation and the same law's earlier enactment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_legislative_formulations import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,CLAUSE,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

DOC='docs/legislative-formulations-v1.md';READING='data/legislative-formulations-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/law-enactment-v1.json','reports/single-ruler-v1.json','reports/religious-emphasis-sentence-v1.json')
DOMAIN=('ruler','other','people','community','othercommunity','office','otheroffice','law','revision','form','newform','one','two','extra','parta','partb','partc')
SCENES=('reference','candidate','before','now','outside')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r ztruth[j[a] d] c.d zrulea[bindings j[a]] e[b point[k ztruth[v bindings v point]]].d zruleb[bindings j[a]] e[b point[u[k ztruth[v bindings v point]]]].'
    extra+='r zchoose[a d '+CLAUSE+' '+CLAUSE+'] '+CLAUSE+'.d h26cc[clause a reference d] '+CLAUSE+'[k zchoose[v clause v reference r[p zrulea] r[p zruleb]]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns));return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(r2uj=lambda r,c,p:(r,c,p)==('ruler','community','reference'),
        r2ui=lambda r,o,c,p:(r,o,c,p)==('ruler','office','community','reference'),
        h234f=lambda o,c,p:(o,c,p)==('office','community','reference'),
        h26tb=lambda o,c,l,r:(o,c,r)==('office','community','reference') and l in ('law','revision'),
        r5ei=lambda p,c,l,r:(p,c,r)==('people','community','reference') and l in ('law','revision'),
        h26cb=lambda l,c,r:l in ('law','revision') and c in ('one','two') and r=='reference',
        h26tc=lambda f,p,r:f in ('form','newform') and p in ('parta','partb') and r=='reference',
        h26te=lambda f,r:f in ('form','newform') and r=='reference',
        zchoose=lambda c,r,a,b:a if c=='one' else b,
        h26td=lambda p,c,r:(p,symbol(c)) in (('parta','zrulea'),('partb','zruleb')) and c.rank==0 and r=='reference',
        h26tf=lambda a,b,c,r:(a,b,c,r)==('law','revision','community','reference'))
    return v

@lru_cache(None)
def office_checks():
    q='q[k r6ck['+args(('ruler','community','law','reference'))+']].';d=fixture(('r6ck',),q,('r2uj','r2ui'));v=model(d);assert run(d,v)==[True];rows={}
    for case in ('not_monarch','wrong_holder','wrong_office','wrong_community','wrong_law','wrong_reference'):
        w=dict(v)
        if case=='not_monarch':w['r2uj']=lambda *a:False
        if case=='wrong_holder':w['r2ui']=lambda r,o,c,p:r=='other' and (o,c,p)==('office','community','reference')
        if case=='wrong_office':w['h26tb']=lambda o,c,l,r:o=='otheroffice'
        if case=='wrong_community':w['h26tb']=lambda o,c,l,r:c=='othercommunity'
        if case=='wrong_law':w['h26tb']=lambda o,c,l,r:l=='revision'
        if case=='wrong_reference':w['h26tb']=lambda o,c,l,r:r=='outside'
        got=run(d,w);assert got==[False],case;rows[case]=False
    for n in ('r2uj','r2ui','h234f','h26tb'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Reuse the existing native role model to avoid treating office words as labels.
    from scripts import check_single_ruler as prior
    e=prior.fixture('role');ns={r['name'] for r in e['declarations']}
    e['declarations'] += [deepcopy(r) for r in closure(catalog().document,('r6ck',)) if r['name'] not in ns]
    e['statements']=[];e=parse(format_graph(e,'compact')+'r zlaw[] a.q[k r6ck[k zp[] k zcommunity[] k zlaw[] k zt[]]].')
    domain=('ruler','other','state','otherstate','top','middle','lower','law')
    native={}
    for case in ('baseline','second_holder','private_owner','not_appointed','holds_another_role'):
        w=prior.role_model(e,case);w.update(zlaw=lambda:'law',h26tb=lambda o,c,l,r:(o,c,l,r)==('top','state','law','now'))
        got=run(e,w,domain,prior.SCENES);assert got==[case=='baseline'],(case,got);native[case]=got[0]
    return dict(cases=rows,native_institutional_role=native,unknown_rejected=True,boundary='Broad reference mutations use r2uj/r2ui boundaries; five native role cases execute their original bodies.')

@lru_cache(None)
def representation_checks():
    d=fixture(('r6cl',),'q[k r6cl['+args(('form','law','reference'))+']].');v=model(d);assert run(d,v)==[True];rows=[]
    for bits in product((False,True),repeat=4):
        w=dict(v);w['h26td']=lambda p,c,r,bits=bits:p in ('parta','partb') and symbol(c) in ('zrulea','zruleb') and bits[('parta','partb').index(p)*2+('zrulea','zruleb').index(symbol(c))]
        want=(bits[0] or bits[1]) and (bits[2] or bits[3]) and (bits[0] or bits[2]) and (bits[1] or bits[3])
        assert run(d,w)==[want],bits;rows.append(dict(links=list(bits),complete=want))
    cases={}
    for case in ('empty_law','empty_form','not_formulation','missing_clause','extra_normative_part','duplicate_expression','wrong_reference','all_rules_unknown'):
        w=dict(v);want=case in ('duplicate_expression','all_rules_unknown')
        if case=='empty_law':w['h26cb']=lambda *a:False
        if case=='empty_form':w['h26tc']=lambda *a:False
        if case=='not_formulation':w['h26te']=lambda *a:False
        if case=='missing_clause':w['h26td']=lambda p,c,r:symbol(c)=='zrulea'
        if case in ('extra_normative_part','duplicate_expression'):
            w['h26tc']=lambda f,p,r:(f,r)==('form','reference') and p in ('parta','partb','partc')
            if case=='duplicate_expression':w['h26td']=lambda p,c,r:v['h26td'](p,c,r) or (p,symbol(c),r)==('partc','zrulea','reference')
        if case=='wrong_reference':w['h26td']=lambda p,c,r:r=='outside'
        got=run(d,w);assert got==[want],(case,got);cases[case]=want
    for n in ('h26cb','h26tc','h26td','h26te','zchoose'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    assert v['ztruth'] is unknown
    return dict(all_four_link_combinations=rows,cases=cases,all_clauses_and_all_normative_parts=True,duplicates_allowed=True,represented_rule_truth_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def revision_checks():
    q='q[k r6cp['+args(('ruler','people','community','law','revision','form','newform','reference'))+']].'
    d=fixture(('r6cp',),q,('r2uj','r2ui','r5ei'));v=model(d);assert run(d,v)==[True];rows={}
    for case in ('same_form','wrong_direction','wrong_community','different_people','revision_outside_office','new_form_incomplete','same_content_new_wording','altered_clause_content'):
        w=dict(v);want=case in ('same_content_new_wording','altered_clause_content')
        if case=='same_form':w['znewform']=lambda:'form'
        if case=='wrong_direction':w['h26tf']=lambda a,b,c,r:(a,b)==('revision','law')
        if case=='wrong_community':w['h26tf']=lambda a,b,c,r:c=='othercommunity'
        if case=='different_people':w['r5ei']=lambda p,c,l,r:p==('people' if l=='law' else 'other')
        if case=='revision_outside_office':w['h26tb']=lambda o,c,l,r:l=='law'
        if case=='new_form_incomplete':w['h26tc']=lambda f,p,r:v['h26tc'](f,p,r) and (f!='newform' or p=='parta')
        if case=='same_content_new_wording':w['zrevision']=lambda:'law';w['h26tf']=lambda a,b,c,r:(a,b,c,r)==('law','law','community','reference')
        if case=='altered_clause_content':
            w['h26cb']=lambda l,c,r:r=='reference' and ((l=='law' and c in ('one','two')) or (l=='revision' and c=='two'))
            w['h26tc']=lambda f,p,r:r=='reference' and ((f=='form' and p in ('parta','partb')) or (f=='newform' and p=='partb'))
        got=run(d,w);assert got==[want],(case,got);rows[case]=want
    for n in ('h26tf','r5ei'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_public_regulatory_question=True,no_adoption_or_improvement_inferred=True,unknown_rejected=True,
        boundary='r5ei full-population frame and monarch identification are boundaries here; native checks and the pinned law-enactment report cover those bodies.')

@lru_cache(None)
def enactment_checks():
    from scripts import check_law_enactment as prior
    d=prior.fixture(('r5ek',),'');ns={r['name'] for r in d['declarations']}
    d['declarations'] += [deepcopy(r) for r in closure(catalog().document,('r6cn',)) if r['name'] not in ns]
    extra='r zform[] a.r zparta[] a.r zpartb[] a.r zpartc[] a.'
    q='q[k r6cn[k zpeople[] '+prior.ARGS+' k zform[] k zreference[] k zcandidate[] k zpoint[]]].'
    d=parse(format_graph(d,'compact')+extra+q);domain=(*prior.DOMAIN,'form','parta','partb','partc')
    def values(case='baseline'):
        w=prior.model(d,case,actor='people')
        w.update(zform=lambda:'form',zparta=lambda:'parta',zpartb=lambda:'partb',zpartc=lambda:'partc')
        w.update(h26te=lambda f,r:(f,r)==('form','reference'),
          h26tc=lambda f,p,r:(f,r)==('form','reference') and p in ('parta','partb','partc'),
          h26td=lambda p,c,r:(p,symbol(c)) in (('parta','zrequired'),('partb','zallowed'),('partc','zpowerclause')) and r=='reference')
        if case!='only_current_adoption':
            for n in ('dg','h26cd','h26ce','h7k','h7l','zpower'):
                original=w[n]
                w[n]=lambda *a,original=original:original(*a[:-1],'point' if a[-1]=='before' else 'outside')
        return w
    assert run(d,values(),domain,prior.SCENES)==[True];rows={}
    for case in ('only_current_adoption','no_activity','no_effect','split_effect_activity','other_law','other_people','other_actor','cycle','missing_person'):
        got=run(d,values(case),domain,prior.SCENES);assert got==[False],(case,got);rows[case]=False
    w=values();w['h7l']=lambda *a:False;assert run(d,w,domain,prior.SCENES)==[False]
    for n in ('h26cd','h26ce','h7k','h7l','zpower','h257z','ic'):
        w=values();w[n]=unknown;rejects(d,w,domain,prior.SCENES)
    # The current ruler need not be the earlier adopting person or collective.
    e=fixture(('r6co',),'q[k r6co['+args(('ruler','people','community','law','form','reference','candidate','now'))+']].',('r6cm','r6cn'))
    w=model(e);w['r6cm']=lambda *a:a==('ruler','people','community','law','form','reference')
    for actor in ('ruler','other','people'):
        w['r6cn']=lambda *a,actor=actor:a==(actor,'people','community','law','form','reference','candidate','now')
        assert run(e,w)==[True]
    w['r6cn']=lambda *a:False;assert run(e,w)==[False]
    return dict(cases=rows,native_full_law_enactment=True,all_distinct_normative_clauses_at_same_prior_point=True,
        earlier_adopter_not_restricted_to_current_ruler=True,unknown_rejected=True,
        boundary='r6cn runs the original r5ei/r5ek/r5ej bodies with requirement, permission and normative power clauses. Only the final current-ruler/adopter separation uses r6cm/r6cn boundaries.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016')
    spans=((519,538),(679,706),(744,763))
    return dict(status='legislative_formulations_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],interpretation=LIMITS,
      alignment=dict(segments=[dict(unit=u['id'],range=[a,b],text=u['text'][a:b],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for a,b in spans]),
      unresolved=['よりよい定式についての本人の判断','同じ全臣民の公的理性使用・世界への思想と率直な批判の提示・全候補への許可','危険・洞察・思考態度と啓蒙への照応・拡張','輝かしい実例・同じ尊敬する君主と先行者不在・全文提示と通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==118
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:int(n in ('r6cn','r6co')) for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('office',office_checks),('representation',representation_checks),('revision',revision_checks),('enactment',enactment_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_legislative_formulations.py','scripts/check_legislative_formulations.py','tests/test_legislative_formulations.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_single_ruler.py','scripts/check_law_enactment.py','scripts/check_scoped_counts.py'}
    return dict(status='legislative_formulations_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
