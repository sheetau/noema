"""Check one bodily fall reading and subject/event preserving metaphor bindings."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT,PARENT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure

REPORT='reports/falling-depiction-v1.json'
READING='data/falling-depiction-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','experience','otherexperience','extra')
SCENES=('start','end','otherpoint')


def unknown(*args):raise ValueError('Unknown falling input')


def ref(code,name):return json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d['declarations']=closure(d,roots);d['statements']=[]
    return parse(format_graph(d,'compact')+suffix)


def evaluate(doc,model,domain=DOMAIN,scenes=SCENES,memoize=False):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=10000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_model(bits=(True,True,True,True,True,False,True,True,False),variant='baseline'):
    order,occurs,change,affected,standing_before,standing_after,grounded,downward,controlled=bits
    def binding(p,e,a,b):return (p,e,a,b)==('other' if variant=='other_person' else 'person',
        'otherexperience' if variant=='other_process' else 'experience','otherpoint' if variant=='other_start' else 'start',
        'otherpoint' if variant=='other_end' else 'end')
    return dict(zperson=lambda:'person',zprocess=lambda:'experience',zstart=lambda:'start',zend=lambda:'end',
        zbefore=lambda a,b:order and (a,b)==('start','end'),zoccurs=lambda e,s:occurs and (e,s)==('experience','start'),
        zchanges=lambda e,a,b:change and (e,a,b)==('experience','start','end'),
        zaffected=lambda p,e,a,b:affected and (p,e,a,b)==('person','experience','start','end'),
        zstanding=lambda p,s:p=='person' and (standing_before if s=='start' else standing_after if s=='end' else False),
        zgrounded=lambda p,s:grounded and (p,s)==('person','otherpoint' if variant=='other_contact_time' else 'end'),
        zdownward=lambda p,e,a,b:downward and binding(p,e,a,b),
        zcontrolled=lambda p,e,a,b:controlled and (p,e,a,b)==('person','experience','start','end'))


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zprocess[] a.r zstart[] d.r zend[] d.r zbefore[d d] c.r zoccurs[a d] c.r zchanges[a d d] c.
r zaffected[a a d d] c.r zstanding[a d] c.r zgrounded[a d] c.r zdownward[a a d d] c.r zcontrolled[a a d d] c.
q[k rqvu[k zperson[] k zprocess[] k zstart[] k zend[] p zbefore p zoccurs p zchanges p zaffected p zstanding p zgrounded p zdownward p zcontrolled]].
''')
    count=0
    for bits in product((False,True),repeat=9):
        actual=evaluate(doc,generic_model(bits));expected=all(bits[i] for i in (0,1,2,3,4,6,7)) and not bits[5] and not bits[8]
        assert actual==[expected],(bits,actual);count+=1
    rows={}
    for variant in ('baseline','other_person','other_process','other_start','other_end','other_contact_time'):
        actual=evaluate(doc,generic_model(variant=variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    names=('zbefore','zoccurs','zchanges','zaffected','zstanding','zgrounded','zdownward','zcontrolled')
    for name in names:
        m=generic_model();m[name]=unknown
        try:evaluate(doc,m)
        except ValueError as e:assert 'Unknown falling' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=count,binding_contrasts=rows,unknown_inputs_refused=len(names),uncached=True)


def physical_model(doc,variant='baseline'):
    m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    p='other' if variant=='other_falling_person' else 'person'
    event='otherexperience' if variant=='other_falling_experience' else 'experience'
    m.update(zperson=lambda:'person',zexperience=lambda:'experience',zextra=lambda:'extra',zscene=lambda:'start',
        f5=lambda person,e,g,s:(person,e,s)==('person','experience','start') and ref(g,'bb' if variant=='wrong_task' else 'zal'),
        f6=lambda e,s:variant!='missing_result' and (e,s)==('otherexperience' if variant=='foreign_result' else 'experience','end'),
        dd=lambda a,b:(a,b)==(('end','start') if variant=='reversed_time' else ('start','end')),
        dg=lambda e,s:variant!='no_occurrence' and (e,s)==('experience','start'),
        ag=lambda e,a,b:variant!='no_transition' and (e,a,b)==('experience','start','end'),
        la=lambda person,e,a,b:(person,e,a,b)==('person','experience','start','end'),
        hzui=lambda person,s:person=='person' and (s=='start' or variant=='still_standing' and s=='end'),
        hzuj=lambda person,s:variant!='no_lower_contact' and (person,s)==('person','end'),
        hzuk=lambda person,e,a,b:variant!='no_descent' and (person,e,a,b)==(p,event,'start','end'),
        hzul=lambda person,e,a,b:variant=='controlled_lowering' and (person,e,a,b)==('person','experience','start','end'))
    return m


def physical_checks():
    doc=fixture(['hzum'],'r zperson[] a.r zexperience[] a.r zscene[] d.q[t[k hzum[k zperson[] k zexperience[]]][k zscene[]]].');rows={}
    for variant in ('baseline','wrong_task','missing_result','foreign_result','reversed_time','no_occurrence','no_transition',
        'still_standing','no_lower_contact','no_descent','controlled_lowering','other_falling_person','other_falling_experience'):
        actual=evaluate(doc,physical_model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    for name in ('f5','f6','hzul'):
        m=physical_model(doc);m[name]=unknown
        try:evaluate(doc,m)
        except ValueError as e:assert 'Unknown falling' in str(e)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=3,walking_goal_content_unknown=True,uncached=True)


def adapter_checks():
    suffix='r zperson[] a.r zexperience[] a.r zextra[] a.r zscene[] d.'
    bindings=['l[a][]','l[a][k zperson[]]','l[a][k zperson[] k zexperience[]]',
        'l[a][k zexperience[] k zperson[]]','l[a][k zperson[] k zexperience[] k zextra[]]']
    for symbol in ('hzun','hzuo'):
        for b in bindings:suffix+='q[t[k '+symbol+'['+b+']][k zscene[]]].'
    doc=fixture(['hzun','hzuo'],suffix);m=physical_model(doc)
    # Both candidate descriptions can be interpreted, but neither is a premise
    # of the nonliteral attribution. The next check makes ALL these facts unknown.
    m.update(f5=lambda p,e,g,s:(p,e,s)==('person','experience','start') and (ref(g,'bb') or ref(g,'zal')),
        ab=lambda *args:False,ac=lambda *args:False,ad=lambda *args:False)
    actual=evaluate(doc,m,memoize=True);assert actual==[False,False,True,False,False]*2,actual
    # A body fall need not imply the target-side intellectual failure.
    m['f5']=lambda p,e,g,s:(p,e,s)==('person','experience','start') and ref(g,'zal')
    separate=evaluate(doc,m,memoize=True);assert separate==[False]*5+[False,False,True,False,False],separate
    return dict(ordered_arity_cases=actual,body_without_target=separate,same_person_and_experience=True,
        native_definitions_with_pure_memoization=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_clause','other_context','reversed_descriptions','wrong_target','wrong_depiction'):
        m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        m.update(fv=lambda:'clause',wa=lambda:'author',wh=lambda:'context')
        def nonliteral(node,author,target,depiction,context):
            first,second=('hzuo','hzun') if variant=='reversed_descriptions' else (
                'hzuo' if variant=='wrong_target' else 'hzun','hzun' if variant=='wrong_depiction' else 'hzuo')
            return (node,author,context)==('other' if variant=='other_clause' else 'clause',
                'other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context') and ref(target,first) and ref(depiction,second)
        m['rbt']=nonliteral
        actual=evaluate(doc,m,('author','clause','other'),('context',));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    m['rbt']=unknown
    try:evaluate(doc,m,('author','clause','other'),('context',))
    except ValueError as e:assert 'Unknown falling' in str(e)
    else:raise AssertionError('Unknown depiction attribution guessed')
    return dict(cases=rows,all_physical_and_intellectual_facts_unknown=True,unknown_attribution_refused=True,uncached=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-9]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==39
    idx=json.loads((ROOT/'data/semantic-review-index-v32.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_definitions=5,new_primitive_relations=4,appended_statement_indices=[38],other_statements_preserved=38,
        nine_review_bindings_preserved=True,generic_library_has_no_source_primitives=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='einigemahl Fallen';start=unit['text'].index(phrase)
    return dict(status='explicit_postural_descent_depiction',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        references=['https://korpora.org/Kant/aa08/036.html','https://www.duden.de/rechtschreibung/fallen'],
        decision='歩行を試みる中で足支持の姿勢を失い、制御しない下降により地面側へ身体が接する転倒を、学習に寄与する不成功経験の描写として接続する。',
        reasoning='原文はFallenをgehen lernenと結ぶ。現代Dudenの身体的な語義も支持・均衡の喪失と身体が地面へ至ることを区別しており、今回はその一つの読みを構成する。現代辞書を1784年の唯一の語義の証明とはしない。',
        limits=LIMITS,whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[38]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('generic',generic_checks),('physical',physical_checks),('adapters',adapter_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    prior=json.loads((ROOT/'reports/caused-deterrence-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    old_range=json.loads((ROOT/'reports/experience-acquisition-v1.json').read_text(encoding='utf-8'))['alignment']
    assert old_range['start']<=s['range'][0]<s['range'][1]<=old_range['end']
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS),status='partial_postural_descent_depiction',full_semantic_equivalence=False)
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,
        'reports/caused-deterrence-v1.json','reports/experience-acquisition-v1.json','scripts/compose_falling_depiction.py',
        'scripts/check_falling_depiction.py','tests/test_falling_depiction.py','docs/falling-depiction-v1.md'}
    return dict(status='bodily_fall_depiction_bound_to_person_and_experience',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Bodily transition, experience bindings and nonliteral attribution checked',flush=True)


if __name__=='__main__':main()
