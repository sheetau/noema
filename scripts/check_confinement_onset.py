"""Countermodels for onset, missing prior assessments and persistent enclosure."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_caused_conditions import source_unit
from scripts.check_confinement import DOMAIN, NODES, sequence
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_training_frame import paragraph_review as previous_review
from scripts.compose_confinement_onset import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/confinement-onset-v1.json'
SCENES = ('before', 'closed', 'middle', 'now')


def values(doc, model, people=DOMAIN, scenes=SCENES):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=15_000_000, memoize_definitions=True)]


def generic_checks():
    doc = parse(generic_composed()[0]+'''
r za[d] c.r zb[d d] c.r zc[] a.r zd[] a.r ze[] a.r zf[] a.r zg[] d.r zh[] d.
r zi[a a a d] c.r zj[a a a] e.r zk[a d d] c.r zl[a a d d] c.r zm[a a a a d] c.r zn[a d] c.
q[k raj[p za p zb k zc[] k zd[] k ze[] k zf[] k zg[] k zh[] p zi p zj p zk p zl p zm p zn]].
''')
    rows = []
    for prior, after, valid_before, valid_after, change, affected, occurs, applies in product((False, True), repeat=8):
        model = {'za': lambda point: True, 'zb': lambda a,b: (a,b)==('before','closed'),
            'zc': lambda:'closing','zd':lambda:'being','ze':lambda:'frame','zf':lambda:'lock',
            'zg':lambda:'before','zh':lambda:'closed',
            'zi':lambda person,carrier,restriction,point: (person,carrier,restriction)==('being','frame','lock') and
                (valid_before if point=='before' else valid_after),
            'zj':lambda person,carrier,restriction: Content(('before','closed'),(prior,after)),
            'zk':lambda process,a,b: change and (process,a,b)==('closing','before','closed'),
            'zl':lambda person,process,a,b: affected and (person,process,a,b)==('being','closing','before','closed'),
            'zm':lambda process,restriction,person,carrier,point: applies and
                (process,restriction,person,carrier,point)==('closing','lock','being','frame','closed'),
            'zn':lambda process,point: occurs and (process,point)==('closing','closed')}
        result = values(doc,model,('closing','being','frame','lock'),('before','closed'))[0]
        if result != (not prior and after and valid_before and valid_after and change and affected and occurs and applies):
            raise ValueError('Onset conflated state, assessment or applying process')
        rows.append({'prior':prior,'after':after,'assessed':[valid_before,valid_after],
            'change':change,'affected':affected,'occurs':occurs,'applies':applies,'onset':result})
    return rows


def source_model(doc, variant='baseline'):
    def forbidden(*args):
        raise ValueError('Onset evaluated unrelated content')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def location(being,point):
        return 'outside' if (variant=='outside_before' and point=='before' or
            variant=='outside_now' and point=='now') else 'other' if variant=='unknown_prior_location' and point=='before' else 'inside'
    def history(restriction,being,carrier,anchor,point):
        return (restriction,being,carrier,anchor)==('lock','being','frame','now') and point in SCENES and not (
            variant=='missing_prior_history' and point=='before' or variant=='missing_anchor' and point=='now')
    def barrier(restriction,being,carrier,a,b,point):
        active=point!='before' or variant=='already_confined'
        if variant=='released_middle' and point=='middle': active=False
        if variant=='released_now' and point=='now': active=False
        return active and (restriction,being,carrier,a,b)==('lock','being','frame','threshold','outside')
    def applies(process,restriction,being,carrier,point):
        return variant!='no_application' and (process,restriction,being,carrier,point)==(
            'other' if variant=='different_applying_process' else 'closing',
            'other' if variant=='different_restriction' else 'lock',
            'other' if variant=='different_applied_subject' else 'being',
            'other' if variant=='different_carrier' else 'frame','closed')
    model.update(za=lambda:'being',zb=lambda:'frame',zc=lambda:'before',zd=lambda:'closed',ze=lambda:'now',
        zf=lambda:'lock',zg=lambda:'closing',db=lambda:'guards',
        mp=lambda group:sequence(('guard',) if group=='guards' else ()),
        aa=lambda person: variant!='nonhuman_actor' and person=='guard',
        df=lambda person,process,point:(person,process,point)==(
            'other' if variant=='foreign_actor' else 'guard','closing','closed'),
        dg=lambda process,point:variant!='no_event' and (process,point)==('closing','closed'),
        ag=lambda process,a,b:variant!='no_change' and (process,a,b)==('closing','before','closed'),
        la=lambda person,process,a,b:(person,process,a,b)==(
            'other' if variant=='different_affected_subject' else 'being','closing','before','closed'),
        dd=lambda a,b:(SCENES.index(a)>SCENES.index(b) if variant=='reverse_time' else SCENES.index(a)<SCENES.index(b)),
        zba=history,qw=location,qz=applies,
        qt=lambda carrier,point:sequence(NODES if carrier=='frame' else ()),
        qu=lambda carrier,place,point:carrier=='frame' and (place=='inside' or
            variant=='overlapping_prior_regions' and point=='before' and place=='outside'),
        qv=lambda carrier,place,point:(carrier,place)==('frame','outside'),
        q7=lambda restriction,being,carrier,point:(restriction,being,carrier)==('lock','being','frame') and not (
            variant=='unassessed_before' and point=='before' or variant=='unassessed_middle' and point=='middle'),
        qx=lambda restriction,being,carrier,a,b,point:(restriction,being,carrier)==('lock','being','frame') and
            (a,b) in (('inside','threshold'),('threshold','outside')),
        qy=barrier)
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {name:callback for name,callback in model.items() if name in required}


PARAMS='r za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] a.r zg[] a.'


def source_checks():
    doc=candidate(source_composed()[0],PARAMS+'''
q[k zbd[k za[] k zb[] k zf[] k zg[] k zc[] k zd[] k ze[]]].
q[t[k zbb[k za[] k zb[] k zf[]]][k ze[]]].q[t[k q2[k za[] k zb[]]][k ze[]]].
''')
    rows={}
    for variant in ('baseline','outside_before','already_confined','unassessed_before','unknown_prior_location',
                    'overlapping_prior_regions','missing_prior_history','reverse_time','no_change',
                    'different_affected_subject','no_event','no_application','different_applying_process',
                    'different_restriction','different_applied_subject','different_carrier','foreign_actor','nonhuman_actor'):
        result=values(doc,source_model(doc,variant))
        if result!=[variant in ('baseline','outside_before'),True,False]:
            raise ValueError('Onset or persisting state after the act ended differs: '+variant+repr(result))
        rows[variant]=dict(zip(('onset','current_state','current_applying_act_condition'),result))
    return rows


def persistence_checks():
    doc=candidate(source_composed()[0],PARAMS+'''
q[k zbe[k za[] k zb[] k zf[] k ze[]]].q[t[k zbb[k za[] k zb[] k zf[]]][k ze[]]].
''')
    rows={}
    for variant in ('baseline','outside_before','released_middle','released_now','unassessed_middle','missing_anchor','outside_now'):
        result=values(doc,source_model(doc,variant))
        expected=[variant in ('baseline','outside_before'),variant not in ('released_now','outside_now')]
        if result!=expected:
            raise ValueError('Continuous post-onset state differs: '+variant+repr(result))
        rows[variant]=dict(zip(('onset_and_persistence','current_state'),result))
    return rows


def attribution_checks():
    doc=candidate(source_composed()[0],'q[k zbg[]].')
    rows={}
    for variant in ('baseline','old_static_depiction','reversed'):
        model=source_model(doc)
        model.update(zbh=lambda:'frame',wa=lambda:'guard',wh=lambda:'now',
            qa=lambda node,author,target,depiction,point:(node,author,symbol(target),symbol(depiction),point)==(
                'frame','guard','zbf' if variant=='reversed' else 'q3',
                'q3' if variant=='reversed' else 'zan' if variant=='old_static_depiction' else 'zbf','now'))
        actual=values(doc,model)[0]
        if actual!=(variant=='baseline'): raise ValueError('Onset depiction reference differs')
        rows[variant]={'framed':actual,'contents_evaluated':False}
    return rows


def alignment():
    unit=source_unit()
    phrase='darin sie sie einsperreten'
    start=unit['text'].index(phrase)
    return {'unit':unit['id'],'unit_sha256':unit['text_sha256'],'start':start,'end':start+len(phrase),
        'source':phrase,'definitions':['raj','zbb','zbc','zbd','zbe','zbf','zbg'],
        'status':'explicit_interpretive_annotation','full_semantic_equivalence':False,
        'remaining':['source tense and ordering','scope and causal grounding','bodily motion and metaphor','facsimile review']}


def paragraph_review():
    review=previous_review()
    row=next(item for item in review['current_obligations'] if item['id']=='walking_frame')
    row['progress_ja']+='閉じ込めの成立過程と、その後に行為が終わっても続く状態を分け、同じ対象・装置・制限を前後と継続期間へ保持した。'
    row['required_review_ja']='歴史的形状・身体支持・歩行の基礎、履歴と移動範囲の妥当性、過程の機構、原文の時間関係と比喩対応全体。'
    return review


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose()
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text: raise ValueError('Stored onset differs')
        doc=parse(text)
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc: raise ValueError('Onset roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    if parse(source_composed()[0])['statements']!=parse((ROOT/'examples/v014/kant-training-frame.noema').read_text(encoding='utf-8'))['statements']:
        raise ValueError('Inherited assertions changed')
    files=[*documents,'data/confinement-onset-basis-v1.json','data/kant-confinement-onset-basis-v1.json',
        'examples/v014/kant-training-frame.noema','data/kant-training-frame-basis-v1.json',
        'scripts/compose_confinement_onset.py','scripts/check_confinement_onset.py','noema/discourse.py','noema/finite_semantics.py']
    return {'status':'partial_confinement_onset_with_assessed_prior_and_persistent_result','documents':documents,
        'generic':generic_checks(),'source':source_checks(),'persistence':persistence_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'paragraph_review':paragraph_review(),'roundtrips':True,'inherited_statements_unchanged':True,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--verify-only',action='store_true')
    args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Onset report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2)
            stream.write('\n')
    print('256 onset combinations, 18 source bindings, 7 persistence and 3 attribution cases checked')


if __name__=='__main__': main()
