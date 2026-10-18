"""Check target timing, native confinement state and nonliteral attribution."""
import argparse
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_confinement_depiction import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,parent,build,closure
from scripts.check_prevented_attempt import DOMAIN,SCENES,source_model,unknown,ref

REPORT='reports/confinement-depiction-v1.json'
READING='data/confinement-depiction-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,model,domain=DOMAIN,scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]


def target_fixture():
    return fixture(['hzss','ej'],'r zp[] a.r za[] d.r zb[] d.'+
        'q[t[k hzss[k zp[]]][k za[]]].q[t[k qj[k zp[]]][k zb[]]].q[t[k ej[k zp[]]][k za[]]].')


def target_model(doc,variant='baseline'):
    inherited=variant if variant in ('late_blocking','blocking_now','actually_attempts','no_blocking_cause','different_earlier_target','split_blocking','empty_agents') else 'baseline'
    model=source_model(doc,inherited)
    attempt=model['ei'];model.update(zp=lambda:'person',za=lambda:'actual',zb=lambda:'prior',
        dc=lambda keeper,person,scene:variant!='no_supervision' and (keeper,person,scene)==(
            'other' if variant=='foreign_supervisor' else 'guardone','other' if variant=='different_supervised_target' else 'person','prior' if variant=='past_supervision_only' else 'actual'),
        ei=lambda person,goal,scene:True if scene=='actual' else attempt(person,goal,scene))
    if variant=='no_selected_target':model['u3']=lambda *args:False
    if variant=='no_presentation_time_membership':
        members=model['mp'];model['mp']=lambda group:SequenceValue(('other',),'"individual"') if group=='population' else members(group)
    return model


def target_checks():
    doc=target_fixture();rows={}
    variants=('baseline','late_blocking','blocking_now','actually_attempts','no_blocking_cause','different_earlier_target','split_blocking','empty_agents',
        'no_supervision','foreign_supervisor','different_supervised_target','past_supervision_only','no_selected_target','no_presentation_time_membership')
    for variant in variants:
        actual=evaluate(doc,target_model(doc,variant));assert actual==[variant=='baseline',False,True],(variant,actual);rows[variant]=actual
    return dict(cases=rows,past_danger_belief_not_required=True,current_nonattempt_not_required=True,
        all_defined_bodies_native=True,pure_memoization=True)


def unknown_checks():
    doc=target_fixture()
    for name in ('dc','ei','g3','dd'):
        model=target_model(doc);model[name]=unknown
        try:evaluate(doc,model)
        except ValueError as e:assert 'Unknown prevention' in str(e)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=4)


def confinement_checks():
    # Only the fixture's primitive values are adapted from the earlier checker.
    # Evaluate the current catalog bodies with the current constructed runtime.
    from scripts.check_confinement_onset import source_model as old_model,SCENES as times,PARAMS
    from scripts.check_confinement import DOMAIN as domain
    from noema.finite_semantics import SequenceValue as LegacySequence
    doc=fixture(['zbd','zbe','zbb'],PARAMS+
        'q[k zbd[k za[] k zb[] k zf[] k zg[] k zc[] k zd[] k ze[]]].'+
        'q[k zbe[k za[] k zb[] k zf[] k ze[]]].q[t[k zbb[k za[] k zb[] k zf[]]][k ze[]]].')
    def adapted(callback):
        def invoke(*args):
            value=callback(*args)
            return SequenceValue(value.items,value.element_type) if isinstance(value,LegacySequence) else value
        return invoke
    variants=('baseline','outside_before','already_confined','unassessed_before','unknown_prior_location','overlapping_prior_regions',
        'missing_prior_history','reverse_time','no_change','different_affected_subject','no_event','no_application',
        'different_applying_process','different_restriction','different_applied_subject','different_carrier','foreign_actor','nonhuman_actor',
        'released_middle','released_now','unassessed_middle','missing_anchor','outside_now')
    rows={}
    for variant in variants:
        model={n:adapted(fn) for n,fn in old_model(doc,variant).items()}
        model.update(ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)))
        actual=evaluate(doc,model,domain,times)
        onset=variant in ('baseline','outside_before','released_middle','released_now','unassessed_middle','missing_anchor','outside_now')
        expected=[onset,variant in ('baseline','outside_before'),variant not in ('released_now','outside_now')]
        assert actual==expected,(variant,actual,expected);rows[variant]=actual
    return dict(cases=rows,current_catalog_and_runtime=True,old_primitive_fixture_adapted=True,
        current_applying_act_not_required=True,full_depiction_not_independently_completed=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    variants=('baseline','old_model_target','old_static_depiction','reversed','other_node','other_author','other_context','missing_presentation')
    for variant in variants:
        model={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        def presentation(node,author,target,depiction,scene):
            return variant!='missing_presentation' and (node,author,scene)==(
                'other' if variant=='other_node' else 'clause','other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context') and \
                ref(target,'zbf' if variant=='reversed' else 'q3' if variant=='old_model_target' else 'hzss') and \
                ref(depiction,'hzss' if variant=='reversed' else 'zan' if variant=='old_static_depiction' else 'zbf')
        model.update(hzst=lambda:'clause',wa=lambda:'author',wh=lambda:'context',qa=presentation)
        actual=evaluate(doc,model,('clause','author','other'),('context',));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(cases=rows,target_and_depiction_inputs_unknown=True,contents_not_asserted_or_equated=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-3]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==37
    used={d['name'] for d in closure(new.document,['hzsu'])};assert not used&{'q3','er','ek','rx','eh','eg','ee','ef'}
    assert {'hzss','hzsn','qj','zbf','qk','zam','zbe','zbd','zbb','raj'}<=used
    idx=json.loads((ROOT/'data/semantic-review-index-v27.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for p in (FULL,CORE):
        d=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(new_definitions=2,new_local_references=1,new_semantic_primitives=0,previous_statements_preserved=36,
        new_statement_index=36,nine_review_bindings_preserved=True,no_causal_equation_model_dependency=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='darin sie sie einsperreten';start=unit['text'].index(phrase)
    prior=json.loads((ROOT/'data/prevented-attempt-reading-v1.json').read_text(encoding='utf-8'))
    assert prior['source']['range'][0]<=start<start+len(phrase)<=prior['source']['range'][1]
    return dict(status='partial_confinement_depiction_connected',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        reference='https://korpora.org/Kant/aa08/035.html',containing_clause='hzsq',
        decision='提示時点の監督対象である同じ本人への先行する試みの阻止を、家畜の描写・同じ歩行訓練装置・閉じ込めの成立と継続へ非字義的に対応させる。',
        limits=['本文は提示時点で人々を選び、先行する阻止を同じ人物へ結ぶ。過去の危険信念や現在の非試行を追加しない。',
            '描写側の継続は履歴内の状態を明示する既存の解釈候補を採る。原文から唯一の時間構造を証明しない。',
            '人間が動物であると断言せず、対象側と描写側の内容の同値性も保証しない。',
            '許可・機会・勇気、穏順さ・慎重さ・皮肉、身体的な語義と比喩全体、段落全体の確認は残る。'],
        whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[36]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('target',target_checks),('unknown',unknown_checks),('confinement',confinement_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading
    historical='reports/confinement-onset-v1.json';old=json.loads((ROOT/historical).read_text(encoding='utf-8'))['alignment'];s=reading['source']
    assert [old['start'],old['end']]==s['range'] and old['source']==s['text']
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS)+['zbf','zbe','zbd'],status='partial_connected_depiction',full_semantic_equivalence=False)
    prior=json.loads((ROOT/'reports/prevented-attempt-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,historical,
        'reports/prevented-attempt-v1.json','data/prevented-attempt-reading-v1.json','scripts/check_confinement_onset.py','scripts/check_confinement.py',
        'scripts/compose_confinement_depiction.py','scripts/check_confinement_depiction.py','tests/test_confinement_depiction.py','docs/confinement-depiction-v1.md'}
    return dict(status='partial_confinement_depiction_connected',document=FULL,**results,alignment=alignment,
        historical_report_usage='Source range only; current native confinement bodies are tested with adapted primitive fixtures, not a replay of the historical runtime.',
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Confinement depiction and its factual target checked',flush=True)


if __name__=='__main__':main()
