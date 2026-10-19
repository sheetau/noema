"""Bind a whole-sentence human reading to the unchanged active manuscript.

Mechanical checks preserve the reviewed object and test its interfaces; they
do not infer equivalence to German from passing finite models.
"""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import _references, load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.check_modal_prevention import catalog, presentation, ROOT, FULL, CORE, BASIS, SELECTION, INVENTORY
from scripts.compose_grounded_step import closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.fetch_guarded_walking_reading_evidence import PATH as EVIDENCE, validate

INDEX='data/semantic-review-index-v79.json'
REGISTRATION='data/semantic-review-index-v80.json'
AUDIT='data/guarded-walking-reading-v1.json'
REPORT='reports/guarded-walking-reading-v1.json'
DOC='docs/guarded-walking-reading-v1.md'
PRIOR='data/modal-prevention-reading-v1.json'
PRECEDING=('first-cause','convenience','delegation','payment','guardian')
COMPONENTS={
    'modal-prevention':['r2am','r2an','r2aj'],
    'prior-confinement':['r2af'],
    'quiet-depiction':['rqz7'],
    'insistent-framing':['r2ab'],
    'walking-warning':['rqy3','rqy4','rqy5'],
    'quantified-step-goals':['rqzu'],
    'grounded-step':['rqzd','rqze','rqzf'],
    'step-depiction':['rqzx'],
}
INTERPRETATIONS={
    'prior_stages':'理解不足を生じさせる行為と許容を妨げる行為を、後の危険提示より前に置く。zuerstとnachherを先行段階と後続段階の対比と読み、先行二行為同士の厳密な順序は補わない。',
    'livestock':'同じ後見人群の監督対象を、その群に属し継続的な管理と生活上の利用目的を持つ動物として描く。牛や羊などの種、遺伝的な家畜化、各飼い手の個別所有を指定しない。',
    'caused_deficiency':'同じ人について、その行為に必要な理解の十分さがない状態を先行行為が生じさせる。単なる勇気不足や生得的能力の固定には読み替えない。',
    'careful_prevention':'同じ行為が本人への許容欠如を生じさせ、その目標へ参加者の目的と関連事項への注意が向く。別の目標への注意や、たまたま許容がないだけでは足りない。',
    'quiet_creatures':'dieseの指示先を同じ家畜像へ戻し、同じ先行局面の外的な身体動作に目立つ落ち着かなさがないと描く。内心の平静や恒久的従順さ、神による創造を追加しない。',
    'emphasis':'同じ主張の身体側の一歩の不許容について、後見人の視点に帰属する緩めない姿勢を表す。著者の賛同、現実の命令発話、追加の禁止規範にはしない。',
    'minimal_step':'同じ本人が同じ装置の外へ通常の接地した一歩を踏み出す目標を置く。足と動作を指定する場合・未指定の場合を含む四形の試みについて許容がない。実際に外へ出たことは要求しない。',
    'confinement':'同じ本人・装置・先行局面へ、制限が成立してその局面まで続く閉じ込めを対応させる。後の危険提示まで閉じ込めが続いたとは追加しない。',
    'daring_permission':'勇気を伴う取り組みへの積極的な許容の欠如という読みを採る。実行機会、能力、実際の非試行とは区別する。',
    'later_presentation':'先行する二行為の後、同じ後見人群が同じ対象者へ、その本人についての条件付き危険を示す。著者の主張と後見人の提示内容を分ける。',
    'conditional_danger':'試みる場合の可能な不利益を提示内容に置く。実際の試み・転倒・負傷、危険の高さや提示内容の真理を著者の主張へ足さない。',
    'walking_attempt':'歩行器の補助から離れる文脈で、同じ身体が足で支持し位置を変える活動への試みとして読む。同行者の不在や特定の歩容は指定しない。知的側と身体側の仮定事例を対応させ、両者の真偽は独立に保つ。',
}
LIMITS=[
    'この原文・本文・意味規約に固定したアシスタントの読解判断であり、自動的な意味一致証明や独立査読ではない。',
    '許容、外的な落ち着き、後見人の強調、補助なしの足移動という採用読解を明記する。他の可能な読みを全て同時に表したという判断ではない。',
    '家畜像に伴う支配や軽視の含みは同じ監督対象を利用される動物として描くことから読む。個々の読者の感情的効果、全ての語感や綴りの復元は保証しない。',
    '動物分類・認知・制度・因果・身体運動などの基本関係の構成的説明はなお拡充が必要。全文の完成や任意の内容の表現率を意味しない。',
]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


def input_paths():
    return set(catalog().source_sha256)|{INDEX,FULL,CORE,BASIS,PRIOR,INVENTORY,EVIDENCE,
        'artifacts/first-cause-reading-v1/page-482.jpg'}|{
        'reports/'+name+'-v1.json' for name in COMPONENTS}|{
        'data/'+name+'-reading-v1.json' for name in PRECEDING}


def reading():
    previous=read(PRIOR);clauses=deepcopy(previous['clauses'])
    for row in clauses:
        row['interpretation_ja']=INTERPRETATIONS[row['id']]
        row['status']='reviewed_under_stated_reading'
    return dict(status='guarded_walking_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence',document=FULL,meaning_basis=BASIS,
        source=previous['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),
        source_review=previous['source_review'],
        lexical_evidence=dict(path=EVIDENCE,
            gehen='Adelungは足による場所の変更という広い用法と、走行に対する狭い歩行を区別する。今回は前者を採る。',
            vieh='人が利用のために飼う動物という用法は犬・猫・蜂も含む。特定の大型家畜だけには絞らない。',
            zahm='蜂や池の魚を人が世話する用法もある。遺伝的な家畜化やあらゆる状況での服従は要求しない。',
            geschoepf='人を戯れや軽視を伴って呼ぶ用法がある。同じ対象への描写として読み、神による創造という命題は加えない。',
            limit='辞書の語義は採用読解を支持する資料であり、この文の唯一の解釈を証明しない。'),
        findings=[
            '原刊482頁の複文全体を十二範囲に分け、七つの現行本文文とその依存定義へ照合した。',
            '家畜と歩行の語義範囲を固定した一次資料で確認し、既存の定義を変更せず文脈上の読みを確定した。',
            '原因・許容・注意・目的、同じ対象者と先行時点、身体側の描写、後の警告の区別を通して確認した。',
            '公開した基本関係と採用読解の範囲では一文全体が対応すると判断する。'],
        interpretation_limits=LIMITS,remaining=['第二段落末尾の転倒・学習・萎縮と段落全体','二作品全文','基本関係の構成的説明の拡充'],
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        new_verified_sentence_characters=244,new_whole_unit_reviews=0,
        preceding_sentence_review_paths=['data/'+name+'-reading-v1.json' for name in PRECEDING],
        semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(input_paths())})


@lru_cache(None)
def interface_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'))
    people=('guards','clause','author','livestock','previous','other')
    contexts=('context','elsewhere');rows={}
    expected={'baseline':[], 'missing_livestock':[0], 'missing_warning':[3],
        'reversed_figures':[0,3], 'missing_claim':[1,6], 'missing_order':[1],
        'wrong_author':list(range(7)), 'wrong_context':list(range(7)),
        'wrong_clause':[1,2,3,4,5,6], 'wrong_livestock_node':[0],
        'missing_confinement':[2], 'missing_step':[4,6], 'missing_quiet':[5],
        'missing_insistence':[6], 'wrong_viewpoint':[6],
        'old_claim':[1,2,4,5,6], 'old_target':[2,4,5,6]}
    for name,missing in expected.items():
        v=presentation(d,name)
        if name in ('missing_livestock','missing_warning'):
            original=v['qa'];target='qj' if name=='missing_livestock' else 'eu'
            v['qa']=lambda n,a,t,b,s:original(n,a,t,b,s) and symbol(t)!=target
        elif name=='reversed_figures':
            original=v['qa'];v['qa']=lambda n,a,t,b,s:original(n,a,b,t,s)
        elif name=='missing_claim':v['uc']=lambda *args:False
        elif name=='missing_order':v['ue']=lambda *args:False
        elif name=='wrong_author':v['wa']=lambda:'other'
        elif name=='wrong_context':v['wh']=lambda:'elsewhere'
        elif name=='wrong_clause':v['hzsq']=lambda:'other'
        elif name=='wrong_livestock_node':v['qp']=lambda:'other'
        actual=evaluate(d,v,people,contexts)
        assert actual==[i not in missing for i in range(7)],(name,actual,missing)
        rows[name]=actual
    for name in ('qa','uc','ue','hzyb','hzye'):
        v=presentation(d);v[name]=unknown
        try:evaluate(d,v,people,contexts)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,current_seven_statements_executed=True,
        world_contents_unknown=True,unknown_inputs_refused=5,ordinary_evaluation=True)


@lru_cache(None)
def reused_checks():
    current=catalog();rows={};lineage={r['document'] for r in current.lineage}
    for name,roots in COMPONENTS.items():
        path='reports/'+name+'-v1.json';report=read(path)
        validate_hashes(ROOT,report['source_sha256'])
        assert report['document'] in lineage
        old=parse((ROOT/report['document']).read_text(encoding='utf-8'))
        assert closure(old,roots)==closure(current.document,roots)
        dependencies={d['name'] for d in closure(current.document,roots)}
        for symbol_name in dependencies:
            entry=current.entries[symbol_name]
            assert entry['meaning_basis'] in report['source_sha256'],(name,symbol_name)
        rows[path]=dict(roots=roots,dependency_count=len(dependencies),
            sha256=digest((ROOT/path).read_bytes()),declarations_and_meanings_unchanged=True)
    # The reports include source-model checks, not just formatting checks.
    assert read('reports/modal-prevention-v1.json')['scope']['unpermitted_but_attempted_countermodel']
    for name in ('prior-confinement','quiet-depiction','walking-warning'):
        assert read('reports/'+name+'-v1.json')['source']
    return dict(reports=rows,finite_evidence_reused_without_claiming_new_execution=True,
        old_whole_sentence_judgments_not_inferred_from_component_tests=True)


@lru_cache(None)
def preceding_checks():
    current=catalog();rows={};total=0
    for name in PRECEDING:
        path='data/'+name+'-reading-v1.json';review=read(path)
        assert review['decision']=='equivalent_under_stated_reading_for_this_sentence'
        validate_hashes(ROOT,review['source_sha256'])
        old=load_catalog(ROOT,review['meaning_basis'])
        indices=[s['index'] for s in review['selection']['statements']]
        before=selection_binding(old,indices);after=selection_binding(current,indices)
        assert before==review['selection']
        assert before['statements']==after['statements'] and before['dependencies']==after['dependencies']
        differences={}
        for name in before['dependencies']:
            a,b=old.entries[name],current.entries[name]
            changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
            assert set(changed)<={'meaning_basis','declaration_document'},(path,name,changed)
            if changed:differences[name]=changed
        total+=review['source']['nonblank_characters']
        rows[path]=dict(original_selection=before,current_selection=after,
            changed_provenance_fields=differences,statements_declarations_and_meanings_unchanged=True,
            nonblank_characters=review['source']['nonblank_characters'])
    assert total==777
    return dict(reviews=rows,reviewed_nonblank_characters=total,
        provenance_changes_checked_separately_from_meaning=True)


@lru_cache(None)
def structure_checks():
    c=catalog();r=reading();assert r==read(AUDIT);validate_hashes(ROOT,r['source_sha256'])
    validate(read(EVIDENCE))
    unit=next(u for u in read(INVENTORY)['units'] if u['id']==r['source']['unit'])
    start,end=r['source']['range'];assert [start,end]==[925,1212]
    assert unit['text_sha256']==digest(unit['text'].encode('utf-8'))==r['source']['unit_sha256']
    assert unit['text'][start:end]==r['source']['text']
    assert sum(not ch.isspace() for ch in r['source']['text'])==244
    cursor=start
    assert len(r['clauses'])==len(INTERPRETATIONS)==12
    for row in r['clauses']:
        assert row['range'][0]==cursor;cursor=row['range'][1]
        assert row['text']==unit['text'][row['range'][0]:cursor]
        assert set(row['definitions'])<=set(r['selection']['dependencies'])
        assert row['status']=='reviewed_under_stated_reading'
    assert cursor==end
    assert r['selection']==read(PRIOR)['selection']==selection_binding(c,SELECTION)
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    assert core['statements']==[c.document['statements'][i] for i in SELECTION]
    assert core['declarations']==closure(c.document,_references(core['statements']))
    for style in ('compact','full'):
        text=format_graph(core,style)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==core
    index=read(INDEX)
    assert index['works']['kant-1784']['document']==FULL
    for path in index['works']['kant-1784']['reviews']:
        review=read(path);validate_hashes(ROOT,review['source_sha256'])
        assert review['selection']==selection_binding(c,[s['index'] for s in review['selection']['statements']])
    assert len(index['works']['kant-1784']['reviews'])==11
    return dict(clause_partition=12,current_selection_bound=True,unchanged_statements=50,
        new_definitions=0,new_primitives=0,preserved_unit_reviews=11,reviewed_sentence_characters=244,
        whole_unit_verified=False,roundtrips=True,semantic_equivalence_automatically_proved=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('interfaces',interface_checks),('reused',reused_checks),('preceding',preceding_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading()
    paths=input_paths()|{AUDIT,DOC,'scripts/check_guarded_walking_reading.py',
        'scripts/fetch_guarded_walking_reading_evidence.py','tests/test_guarded_walking_reading.py',
        'scripts/check_modal_prevention.py','scripts/compose_grounded_step.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/fetch_pastoral_role_evidence.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/semantic_reviews.py',
        'noema/meaning_catalog.py','noema/script.py'}
    for name in COMPONENTS:paths.update(read('reports/'+name+'-v1.json')['source_sha256'])
    for name in PRECEDING:paths.update(read('data/'+name+'-reading-v1.json')['source_sha256'])
    return dict(status='whole_guarded_walking_sentence_reviewed_under_explicit_reading',document=FULL,**results,
        alignment=dict(**r['source'],definitions=['qq','r2ao','r2as','rqy5','r2ap','r2aq','r2ar'],
            status='explicit_interpretive_annotation'),
        review_decision=r['decision'],reviewer='assistant_review',whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=244,new_covered_characters=1,
        reviewed_opening_six_sentence_characters=1021,
        new_coverage_explanation='Only the previously uncovered semicolon at source offset 1114 joins the range; no new manuscript text.',
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def registration():
    index=deepcopy(read(INDEX));report=read(REPORT)
    validate_hashes(ROOT,report['source_sha256'])
    assert report['reviewed_opening_six_sentence_characters']==1021
    pins=dict(report['source_sha256'])
    pins.update({p:digest((ROOT/p).read_bytes()) for p in (INDEX,REPORT)})
    for path,value in pins.items():
        assert path not in index['source_sha256'] or index['source_sha256'][path]==value
    index['source_sha256'].update(pins)
    return index


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
    write_exact(ROOT/REGISTRATION,encoded(registration()))


if __name__=='__main__':main()
