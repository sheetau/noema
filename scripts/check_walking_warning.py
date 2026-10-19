"""Check conditional risk, independent metaphor contents and the remaining sentence gaps."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_walking_warning import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v67.json'
REPORT='reports/walking-warning-v1.json'
AUDIT='data/walking-warning-reading-v1.json'
DOC='docs/walking-warning-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','move')
SCENES=('actual','case','caseother','loss','otherloss')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jp[] a.r js[] d.r jcases[a d d] c.r jtries[a i[h[a] e] d] c.
r joutcome[a i[h[a] e] d d] c.r jadverse[a d] c.r jtruth[a d] c.
d jtrial[person a] e[b scene[k jtruth[v person v scene]]].
d jrisk[person a] e[b scene[k jtruth[v person v scene]]].
q[t[k rqy3[k jp[] r[p jtrial] r[p jrisk] p jcases p jtries p joutcome p jadverse]][k js[]]].
''')


def generic_values(nonempty=True,attempt=True,outcome=True,adverse=True,variant='baseline'):
    return dict(jp=lambda:'person',js=lambda:'actual',jtruth=unknown,
        jcases=lambda p,b,s:nonempty and (p,b,s)==('other' if variant=='other_scope_person' else 'person',
            'case' if variant=='other_base' else 'actual','case'),
        jtries=lambda p,g,s:attempt and (p,symbol(g),s)==('person',
            'jrisk' if variant=='other_trial_goal' else 'jtrial','case'),
        joutcome=lambda p,g,s,o:outcome and (p,symbol(g),s,o)==(
            'other' if variant=='other_risk_person' else 'person',
            'jtrial' if variant=='other_risk_goal' else 'jrisk',
            'caseother' if variant=='other_risk_case' else 'case','loss'),
        jadverse=lambda p,o:adverse and (p,o)==('other' if variant=='other_harmed_person' else 'person',
            'otherloss' if variant=='other_harm_outcome' else 'loss'))


def generic_checks():
    rows=[]
    for nonempty,attempt,outcome,adverse in product((False,True),repeat=4):
        v=generic_values(nonempty,attempt,outcome,adverse)
        for goal_truth in (False,True,None):
            v['jtruth']=unknown if goal_truth is None else lambda p,s:goal_truth
            actual=evaluate(generic(),v,DOMAIN,SCENES)
            assert actual==[nonempty and (not attempt or outcome and adverse)]
            rows.append(dict(nonempty=nonempty,attempt=attempt,outcome=outcome,adverse=adverse,
                goal_truth=goal_truth,values=actual))
    return dict(combinations=rows,goal_success_not_required=True,ordinary_evaluation=True)


def scope_checks():
    rows={}
    for name in ('other_scope_person','other_base','other_trial_goal','other_risk_person','other_risk_goal',
            'other_risk_case','other_harmed_person','other_harm_outcome'):
        actual=evaluate(generic(),generic_values(variant=name),DOMAIN,SCENES)
        # A goal-mismatched trial is absent, so implication is vacuously true;
        # this does not assert an attempt or applicability of the warning.
        assert actual==[name=='other_trial_goal'],(name,actual);rows[name]=actual
    v=generic_values();base=v['jcases'];v['jcases']=lambda p,b,s:base(p,b,s) or (p,b,s)==('person','actual','caseother')
    v['jtries']=lambda p,g,s:(p,symbol(g))==('person','jtrial') and s in ('case','caseother')
    assert evaluate(generic(),v,DOMAIN,SCENES)==[False]
    for name in ('jcases','jtries','joutcome','jadverse'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,DOMAIN,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,every_selected_case_required=True,unknown_inputs_refused=4,
        empty_scope_not_vacuous_success=True,ordinary_evaluation=True)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


def source_checks():
    d=fixture(['eu','rqy3','rqy4'],'''r jp[] a.r js[] d.
q[t[k eu[k jp[]]][k js[]]].
q[t[k rqy3[k jp[] r[p bb] r[p up] p f4 p ei p uq p ur]][k js[]]].
q[t[k rqy4[k jp[]]][k js[]]].''')
    rows=[]
    for abstract_trial,abstract_risk,body_trial,body_risk in product((False,True),repeat=4):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(jp=lambda:'person',js=lambda:'actual',
            f4=lambda p,b,s:(p,b,s)==('person','actual','case'),
            ei=lambda p,g,s:(p,s)==('person','case') and (
                abstract_trial if symbol(g)=='bb' else body_trial if symbol(g)=='zal' else False),
            uq=lambda p,g,s,o:(p,s,o)==('person','case','loss') and (
                abstract_risk if symbol(g)=='up' else body_risk if symbol(g)=='zal' else False),
            ur=lambda p,o:(p,o)==('person','loss'))
        actual=evaluate(d,v,DOMAIN,SCENES)
        expected=[not abstract_trial or abstract_risk]*2+[not body_trial or body_risk]
        assert actual==expected,(actual,expected)
        rows.append(dict(abstract_trial=abstract_trial,abstract_risk=abstract_risk,body_trial=body_trial,
            body_risk=body_risk,values=actual))
    # Execute the actual bodily goal separately, rather than replacing zal by a
    # supplied truth value. Trial and conditional risk above never execute it.
    goal=fixture(['zal'],'r jp[] a.r js[] d.q[t[k zal[k jp[]]][k js[]]].')
    goal_rows=[]
    for movement,support in product((False,True),repeat=2):
        v=dict(jp=lambda:'person',js=lambda:'actual',
            zai=lambda p,a,s:movement and (p,a,s)==('person','move','actual'),
            zaj=lambda p,a,s:support and (p,a,s)==('person','move','actual'))
        actual=evaluate(goal,v,DOMAIN,SCENES);assert actual==[movement and not support]
        goal_rows.append(dict(movement=movement,external_support=support,values=actual))
    return dict(conditional_combinations=rows,existing_abstract_condition_matches_generic=True,
        body_goal_combinations=goal_rows,physical_and_intellectual_truth_independent=True,
        actual_world_and_goal_success_unknown_in_conditionals=True,ordinary_evaluation=True)


def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    variants=('baseline','no_claim','no_order','no_livestock','no_confinement','no_warning_depiction',
        'wrong_author','wrong_context','wrong_node','reversed_warning','wrong_target','wrong_depiction')
    for name in variants:
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        def depicts(n,a,p,q,s):
            expected=[('livestock','qj','qk'),('relative','hztt','zbf'),('clause','eu','rqy4')]
            if name=='no_livestock':expected.pop(0)
            elif name=='no_confinement':expected.pop(1)
            elif name=='no_warning_depiction':expected.pop(2)
            elif name=='wrong_node':expected[2]=('relative','eu','rqy4')
            elif name=='reversed_warning':expected[2]=('clause','rqy4','eu')
            elif name=='wrong_target':expected[2]=('clause','et','rqy4')
            elif name=='wrong_depiction':expected[2]=('clause','eu','zal')
            return (a,s)==('other' if name=='wrong_author' else 'author',
                'other' if name=='wrong_context' else 'context') and (n,symbol(p),symbol(q)) in expected
        v.update(qp=lambda:'livestock',hzsq=lambda:'clause',hzst=lambda:'relative',wa=lambda:'author',wh=lambda:'context',dq=lambda:'previous',
            qa=depicts,uc=lambda n,a,p,s:name!='no_claim' and (n,a,symbol(p),s)==('clause','author','hztr','context'),
            ue=lambda a,b,s:name!='no_order' and (a,b,s)==('previous','clause','context'))
        actual=evaluate(d,v,('livestock','clause','relative','author','previous','other'),('context','other'))
        wrong=name in ('wrong_author','wrong_context')
        expected=[not wrong and name!='no_livestock',name not in ('no_claim','no_order'),
            not wrong and name!='no_confinement',not wrong and name not in ('no_warning_depiction','wrong_node',
                'reversed_warning','wrong_target','wrong_depiction')]
        assert actual==expected,(name,actual,expected);rows[name]=actual
    return dict(contrasts=rows,all_world_contents_unknown=True,current_four_statements_executed=True,
        bodily_truth_not_asserted=True,ordinary_evaluation=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    text=unit['text'];start=text.index('Nachdem sie ihr Hausvieh');end=text.index(' Nun ist diese Gefahr',start)
    parts=[
        ('prior_stages','Nachdem ',['hztp'],'二つの先行局面を後の危険提示へ結ぶ。先行二局面相互の厳密な順序は指定しない。','mapped'),
        ('livestock','sie ihr Hausvieh ',['qq','qj','qk'],'指示された同じ後見人群と対象者を、帰属と飼育を持つ動物として描写する。家畜と愛玩動物の境界は再確認が必要。','partial'),
        ('caused_deficiency','zuerst dumm gemacht haben, und ',['g4','hztp'],'同じ人の理解不足を先行する実際の行為が生じさせる読み。永久的不能や知能数値は補わない。','mapped'),
        ('careful_prevention','sorgfältig verhüteten, daß ',['hzto','hztn','rqvp'],'同じ原因行為に関連事項への注意と目標を結ぶ。','mapped'),
        ('quiet_creatures','diese ruhigen Geschöpfe ',['qj','qk'],'対象の再指示はあるが、ruhigenの穏やかさ・非抵抗の描写が明示されていない。単なる非試行から補わない。','unresolved'),
        ('emphasis','ja ',[],'否定された許容・試みへの強調の担い手と作用範囲を確定して接続する必要がある。前文schonの確言とは自動的に同一視しない。','unresolved'),
        ('minimal_step','keinen Schritt außer dem Gängelwagen, ',['hzsm','hztc','zam'],'知的活動の非試行と不許容、装置の構成はあるが、身体的な一歩の最小単位・装置外という目標範囲が未接続。','unresolved'),
        ('confinement','darin sie sie einsperreten, ',['hztu','hztt','zbf'],'同じ本人と装置の閉じ込め成立・継続を、先行する阻止へ非字義的に結ぶ。','mapped'),
        ('daring_permission','wagen durften; ',['hzs4','hztc'],'勇気を伴う取り組みを対象とした許容欠如を採る既存の読み。実行機会の読みとの選択は文全体の確認で再点検する。','partial'),
        ('later_presentation','so zeigen sie ihnen nachher ',['ew','hztp','hztr'],'同じ送り手群と対象者を同じ後続の提示行為へ結ぶ。提示された危険の真理は要求しない。','mapped'),
        ('conditional_danger','die Gefahr, die ihnen drohet, ',['et','eu','rqy3','rqy4'],'本人への可能な不利益を条件内容の後件として結ぶ。現実の発生や高い危険度を補わない。','partial'),
        ('walking_attempt','wenn sie es versuchen allein zu gehen.', ['ej','eu','zal','rqy4','rqy5'],
            '既存の知的側の警告を、補助なしの脚の移動を試みる場合の身体側の警告へ結ぶ。対応する仮定事例の索引を共有するが、両側の試み・危険の真理は独立。歩行の細部は残る。','partial'),
    ]
    pos=start;clauses=[]
    for name,phrase,names,meaning,status in parts:
        assert text[pos:pos+len(phrase)]==phrase,(name,pos)
        clauses.append(dict(id=name,range=[pos,pos+len(phrase)],text=phrase,definitions=names,
            interpretation_ja=meaning,status=status));pos+=len(phrase)
    assert pos==end
    paths=(INVENTORY,INDEX,PARENT,PARENT_BASIS,FULL,BASIS,'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='prevention_sentence_audited_bodily_warning_added_remaining_gaps_explicit',reviewer='assistant_review',
        decision='whole_sentence_not_yet_verified',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=text[start:end],
            nonblank_characters=sum(not c.isspace() for c in text[start:end])),clauses=clauses,
        selection=selection_binding(catalog(),[9,35,36,46]),interpretation_limits=LIMITS,
        source_review=dict(facsimile_page=482,image=paths[-1],visually_compared=True,
            url='https://www.digitale-sammlungen.de/de/view/bsb10926843?page=522'),
        remaining=['ruhigenの描写','jaの強調','一歩も・装置外・許容の結合','歩行と家畜の語義範囲を含む一文全体','第二段落末尾と段落全体','二作品全文'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['statements'][:46]==old.document['statements'] and len(new.document['statements'])==47
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    assert selection_binding(old,list(range(46)))==selection_binding(new,list(range(46)))
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in r['selection']['statements']]
        assert selection_binding(old,indices)==r['selection']==selection_binding(new,indices)
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==r
    validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert all(n in new.entries for c in r['clauses'] for n in c['definitions'])
    assert [c['id'] for c in r['clauses'] if c['status']=='unresolved']==['quiet_creatures','emphasis','minimal_step']
    return dict(preserved_statements=46,new_statements=[46],new_primitives=0,new_definitions=3,
        prior_declarations_and_meanings_unchanged=True,preserved_review_selections=11,
        current_selection_bound=True,clause_partition=12,roundtrips=True,whole_sentence_verified=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,fn in [('generic',generic_checks),('scope',scope_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[n]=fn();print(n+' checked',flush=True)
    r=reading();span=r['clauses'][-1]
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_walking_warning.py','scripts/check_walking_warning.py','scripts/register_walking_warning.py',
        'tests/test_walking_warning.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_bodily_conditional_warning_with_explicit_sentence_gaps',document=FULL,**results,
        alignment=dict(unit=r['source']['unit'],unit_sha256=r['source']['unit_sha256'],range=span['range'],
            text=span['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
