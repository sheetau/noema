"""Check the adopted shared capacity definitions and unchanged reviewed units."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_subject_bound_departure import closure
from scripts.compose_exercise_capacity import ROOT,PARENT,PARENT_BASIS,PARENT_ANNOTATIONS,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,CONTEXT,build,catalogs

REPORT='reports/exercise-capacity-v1.json'
READING='data/exercise-capacity-reading-v1.json'
STATUS='data/opening-reading-status-v3.json'
DOMAIN=('person','method','backup','faculty','act','guide','other','process')
SCENES=('anchor','first','second','success','failure','emancipated','endcase')


def unknown(*args):raise ValueError('Unknown exercise capacity input')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=20000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def generic():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zanchor[] d.r zcases[a d d] c.r zpreserved[a d d] c.r zopportunity[a d] c.r zpreferred[a d d d] c.
r zscope[a a d d] c.r zchecked[a a d d] c.r zavailable[a a d] c.r zoutcomes[a a d d] c.r zselected[a a d d] c.r zsuccess[d] c.
d zgoal[] e[b scene[k zsuccess[v scene]]].
'''
    args='k zperson[] k zgoal[] k zanchor[] p zcases p zpreserved p zopportunity p zpreferred p zscope p zchecked p zavailable p zoutcomes p zselected'
    text+=''.join('q[k '+n+'['+args+']].' for n in ('rqvn','rqvo','rqvm'))
    text+='q[k xd[k zperson[] k zgoal[] k zanchor[] p zavailable p zoutcomes p zselected]].'
    return parse(text)


def model(doc,variant='baseline',**options):
    from scripts.check_standing_ability import model as previous
    inherited=variant if variant in ('empty_profile','changed_person_state','missing_external_opportunity','cyclic_order','missing_assessment') else 'baseline'
    values=previous(doc,variant=inherited,**options)
    values.update(zscope=lambda p,m,a,s:(p,a)==('person','anchor') and m=='method',
        zchecked=lambda p,m,a,s:(p,a)==('person','anchor'))
    if variant=='unclassified_success':values['zchecked']=lambda p,m,a,s:(p,a)==('person','anchor') and s!='second'
    if variant in ('training_only','unclassified_training','known_success_unknown_other'):
        base=values['zavailable'];base_selected=values['zselected']
        def available(p,m,s):return base(p,m,s) or p=='person' and m=='backup' and (s in ('first','second') or options.get('now',False) and s=='anchor')
        values.update(zavailable=available,zoutcomes=lambda p,m,s,t:available(p,m,s) and t in ('success','failure'),
            zselected=lambda p,m,s,t:available(p,m,s) and (t=='success' if m=='backup' else base_selected(p,m,s,t)))
        if variant!='training_only':values['zchecked']=lambda p,m,a,s:(p,a)==('person','anchor') and m!='backup'
    return values


def combinations():
    doc=generic();rows=[]
    for now,first,second,ordered in product((False,True),repeat=4):
        actual=evaluate(doc,model(doc,now=now,passes=(first,second),prefer_first=ordered))
        capable=first and (ordered or second)
        assert actual==[capable,not capable,True,now],(now,first,second,ordered,actual)
        rows.append(dict(current_opportunity=now,first_success=first,second_success=second,first_preferred=ordered,values=actual))
    return dict(count=len(rows),cases=rows,negative_is_not_failure_in_every_case=True,uncached_and_unlowered=True)


def contrasts():
    doc=generic();rows={}
    for name,options,expected in [
        ('unclassified_success',{},[False,False,False,False]),
        ('training_only',{'now':True,'passes':(False,False)},[False,True,True,True]),
        ('unclassified_training',{'passes':(False,False)},[False,False,False,False]),
        ('known_success_unknown_other',{},[True,False,True,False]),
        ('empty_profile',{},[False,False,False,False]),
        ('changed_person_state',{'prefer_first':True},[False,False,False,False]),
        ('missing_external_opportunity',{},[False,False,False,False]),
        ('cyclic_order',{},[False,False,False,False]),
        ('missing_assessment',{},[False,False,False,False]),
    ]:
        actual=evaluate(doc,model(doc,name,**options));assert actual==expected,(name,actual);rows[name]=actual
    for name in ('zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked','zselected'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown exercise' in str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=7,unclassified_methods_do_not_prove_inability=True)


@lru_cache(None)
def source_fixture(path,departure=False):
    doc=parse((ROOT/path).read_text(encoding='utf-8'));doc['statements']=[]
    roots=['bc','up','fo']+(['be'] if departure else [])
    doc['declarations']=closure(doc,roots)
    suffix='r zperson[] a.r zanchor[] d.'
    if departure:suffix+='r zprocess[] a.r zend[] d.q[k be[k zperson[] k zprocess[] k zanchor[] k zend[]]].'
    else:suffix+='q[k bc[k zperson[] k zanchor[]]].q[t[k up[k zperson[]]][k zanchor[]]].q[t[k fo[k zperson[]]][k zanchor[]]].'
    return parse(format_graph(doc,'compact')+suffix)


def source_values(doc,variant='baseline',**options):
    values=model(doc,variant,**options)
    values.update(aa=lambda p:p=='person',ab=lambda f,p,s:(f,p)==('faculty','person'),
        ac=lambda p,f,a,s:(p,f,a,s)==('person','faculty','act','success'),ad=lambda *args:False,
        ae=values['zavailable'],af=values['zoutcomes'],ap=values['zselected'])
    for target,name in zip(CONTEXT,('zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked')):values[target]=values[name]
    return values


def source_checks():
    old=source_fixture(PARENT);new=source_fixture(FULL);rows={}
    for name,options,before,after in [
        ('baseline',{},[True,False,True],[False,True,True]),
        ('training_only',{'now':True,'passes':(False,False)},[False,True,True],[True,False,True]),
        ('unclassified_success',{},[True,False,True],[False,False,False]),
        ('unclassified_training',{'passes':(False,False)},[True,False,True],[False,False,False]),
        ('known_success_unknown_other',{},[True,False,True],[False,True,True]),
    ]:
        a=evaluate(old,source_values(old,name,**options));b=evaluate(new,source_values(new,name,**options))
        assert (a,b)==(before,after),(name,a,b);rows[name]=dict(previous=a,current=b)
    return dict(cases=rows,native_shared_bc_up_fo_executed=True)


def departure_checks():
    old=source_fixture(PARENT,True);new=source_fixture(FULL,True);rows={}
    for variant in ('baseline','wrong_person','wrong_process','missing_final_profile'):
        values=source_values(new,passes=(False,False));values.update(zprocess=lambda:'process',zend=lambda:'emancipated')
        available=values['ae'];outcomes=values['af'];selected=values['ap']
        values.update(ae=lambda p,m,s:available(p,m,s) or (p,m,s)==('person','method','endcase'),
            af=lambda p,m,s,t:outcomes(p,m,s,t) or (p,m,s,t)==('person','method','endcase','success'),
            ap=lambda p,m,s,t:selected(p,m,s,t) or (p,m,s,t)==('person','method','endcase','success'),
            hzsc=lambda p,a,s:p=='person' and (a=='anchor' and s in ('first','second') or variant!='missing_final_profile' and (a,s)==('emancipated','endcase')),
            hzsd=lambda p,a,s:p=='person' and a in ('anchor','emancipated'),hzse=lambda p,s:p=='person' and s in ('first','second','endcase'),
            hzsg=lambda p,m,a,s:p=='person' and m=='method' and a in ('anchor','emancipated'),
            hzsh=lambda p,m,a,s:p=='person' and a in ('anchor','emancipated'),
            ag=lambda r,a,b:(r,a,b)==('process','anchor','emancipated'),
            la=lambda p,r,a,b:(p,r,a,b)==('other' if variant=='wrong_person' else 'person','other' if variant=='wrong_process' else 'process','anchor','emancipated'),
            hziq=lambda p,g,s:(p,s)==('person','anchor') and json.loads(g.syntax)==dict(kind='function_ref',symbol='bf'),
            hzid=lambda p,r,f,t,a,b:(p,r,a,b)==('person','process','anchor','emancipated') and json.loads(f.syntax)==dict(kind='function_ref',symbol='bp') and json.loads(t.syntax)==dict(kind='function_ref',symbol='up'))
        a=evaluate(old,values);b=evaluate(new,values)
        assert a==[False] and b==[variant=='baseline'],(variant,a,b);rows[variant]=dict(previous=a,current=b)
    return dict(cases=rows,departure_endpoint_uses_same_updated_capacity=True)


def presentation_checks():
    from scripts import check_courageous_undertaking as previous
    with patch.object(previous,'CORE',CORE):result=previous.attribution_checks()
    return dict(**result,current_manuscript=True,new_profile_parameters_not_executed_by_quotation=True)


def substantive(entry):return {k:v for k,v in entry.items() if k not in ('meaning_basis','declaration_document')}


@lru_cache(None)
def current():return load_catalog(ROOT,BASIS)


def structure():
    old=catalogs()[0];new=current();a={d['name']:d for d in old.document['declarations']};b=new.entries
    changed=[n for n in a if a[n]!=b[n]['declaration']];assert changed==['bc','up','be','fo'],changed
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==35
    for name in old.entries:
        if name not in changed:assert substantive(old.entries[name])==substantive(new.entries[name]),name
    affected=[]
    for i in range(35):
        if set(selection_binding(old,[i])['dependencies'])&set(changed):affected.append(i)
    index=json.loads((ROOT/'data/semantic-review-index-v24.json').read_text(encoding='utf-8'));checked=[]
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        before=selection_binding(old,indices);after=selection_binding(new,indices)
        assert before==review['selection'] and before['statements']==after['statements']
        assert set(before['dependencies'])==set(after['dependencies']) and not set(indices)&set(affected)
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in before['dependencies'])
        assert before!=after  # Flat re-registration changes provenance, not these meanings.
        checked.append(review['unit'])
    for path in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(changed_bodies=changed,unchanged_statement_syntax=35,changed_dependency_statement_indices=affected,
        preserved_review_units=checked,review_provenance_requires_new_bindings=True,new_context_relations=6,
        new_generic_definitions=5,new_generic_primitives=0,roundtrips=True)


def reading():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0008')
    return dict(status='adopted_capacity_reading_not_whole_paragraph_equivalence',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[86,181],text=unit['text'][86:181]),
        references=['https://korpora.org/Kant/aa08/035.html','https://korpora.org/Kant/aa08/036.html'],
        decision='現在の本人の判断基盤を保持し、外的な使用機会のある通常場面で、既有の基盤を行使する方法によって自立的に使える能力として読む。習得可能性と現在の行使能力を分ける。',
        rationale='冒頭は指導なしの使用の不能を定義し、後続では当面の不能と、試みを許されなかった履歴や自分の精神への働きかけを区別する。単なる外的機会の不在や、将来習得する計画の可能性だけを現在の能力の可否へ移さない。この文脈で採る読解判断であり、能力一般の唯一の理論の証明ではない。',
        adequacy_reading='理解・決意・勇気の十分さは、同じ本人が自立的に使用する目標に関する文脈基準として保持する。原文が与えていない数量・成功率・心理的測定法は加えない。具体的な判断値の推定を、著者の主張を記述するための追加条件にはしない。',
        negative_reading='評価済みの通常行使能力がないこと。全正常場面で個別に絶対不能という強い読みへ置換しない。通常場面の一部だけでできることと、基準全体を満たすことを区別する。',
        whole_unit_semantically_verified=False,binding=selection_binding(current(),[1]),
        unresolved=['ラテン語のsapereとaudeの採用語義','第一段落全体の意味・照応・追加条件・脱落の再確認','後続段落の改訂した共有能力への依存と全文確認'])


def build_report():
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text,path
    results={}
    for name,fn in [('combinations',combinations),('contrasts',contrasts),('source',source_checks),('departure',departure_checks),('presentation',presentation_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    record=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==record
    prior=json.loads((ROOT/'reports/preparation-course-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(prior['source_sha256'])|set(current().source_sha256)|{READING,STATUS,'reports/preparation-course-v1.json',
        'scripts/compose_exercise_capacity.py','scripts/check_exercise_capacity.py','tests/test_exercise_capacity.py','docs/exercise-capacity-v1.md'}
    for cat in catalogs():paths.update(cat.source_sha256)
    u=record['source'];alignment=dict(unit=u['unit'],unit_sha256=u['unit_sha256'],range=u['range'],source=u['text'],
        definitions=['bc','up','fo','be','rqvn','rqvo'],status='partial_adopted_exercise_capacity_reading',full_semantic_equivalence=False)
    from scripts.audit_written_progress_extended import collect_alignment
    units={x['id']:x for x in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']}
    assert len(collect_alignment(dict(alignment=alignment),units,set(current().entries),REPORT))==1
    return dict(status='shared_manuscript_capacity_reading_updated',document=FULL,**results,alignment=alignment,
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--reading-only',action='store_true');cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import encoded,write_exact
    record=reading();write_exact(ROOT/READING,encoded(record))
    prior=json.loads((ROOT/'data/opening-reading-status-v2.json').read_text(encoding='utf-8'))
    status=dict(status='capacity_reading_adopted_latin_and_whole_paragraph_pending',document=FULL,meaning_basis=BASIS,
        supersedes_worklist='data/opening-reading-status-v2.json',reading_record=READING,reading_record_sha256=digest((ROOT/READING).read_bytes()),
        inherited_scope_decisions=prior['decisions'],coordination_reading=prior['inherited_coordination_judgment'],
        revalidation='作用範囲の読みを保持する。本文の能力の意味と依存ハッシュは改訂したため、旧記録の本文結合をそのまま流用しない。',
        binding=selection_binding(current(),[1]),remaining_semantic_reviews=[
            dict(item='ラテン語の判断能力と取り組みの読み',symbols=['bk','yb','hzs6']),
            dict(item='第一段落全体と後続依存箇所の意味確認',symbols=['hzsb','bc','up','fo','be'])])
    write_exact(ROOT/STATUS,encoded(status))
    if args.reading_only:print('Capacity reading and remaining source reviews recorded',flush=True);return
    report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Adopted capacity, departure endpoint and review migration prerequisites checked',flush=True)


if __name__=='__main__':main()
