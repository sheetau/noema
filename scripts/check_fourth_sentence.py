"""Check adopted correspondence and record a separate contextual sentence judgment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_fourth_sentence import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MAPPINGS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap
from scripts.check_learned_familiarity import source_model

INDEX='data/semantic-review-index-v111.json'
REPORT='reports/fourth-sentence-v1.json'
AUDIT='data/fourth-sentence-reading-v1.json'
DOC='docs/fourth-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
IMAGE='artifacts/future-dissemination-reading-v1/page-483.jpg'
PRIOR=['reports/limited-consequence-v1.json','reports/minimum-challenge-v1.json','reports/unfamiliar-judgment-v1.json','reports/depicted-referents-v1.json','reports/fetters-sentence-v1.json']
COVERAGE=['reports/conditional-release-v1.json','reports/learned-familiarity-v1.json']
SENTENCES=[('data/nature-sentence-reading-v1.json',[51]),('data/confirmed-incapacity-reading-v1.json',[11,12]),('data/fetters-sentence-reading-v1.json',[10,52])]
PEOPLE=('person','shackle','release','limb','movement','small','jump','experience','other')
SCENES=('before','case','anchor')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def document():return parse((ROOT/FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,extra):
    doc=deepcopy(document());doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra)


def unknowns(doc):return {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}


def refuse(doc,values,names,people=PEOPLE,scenes=SCENES):
    for name in names:
        changed=dict(values);changed[name]=unknown
        try:evaluate(doc,changed,people,scenes,True)
        except ValueError as error:assert 'Unknown' in str(error),(name,str(error))
        else:raise AssertionError(name)


@lru_cache(None)
def reference_checks():
    doc=fixture(['r2io','r2ip'],'r zr[a d] c.r zv[a d] c.r zk[a d] c.r zitem[] a.r zpoint[] d.'+
        'q[k r2io[p zr p zv p zk]].q[k r2ip[k zitem[] k zpoint[] p zr p zv p zk]].')
    people=('first','second','candidate');scenes=('source','past')
    def model(bits):
        return dict(zitem=lambda:'candidate',zpoint=lambda:'past',
            zr=lambda a,s:a in people[:2] and s=='source' and bits[people.index(a)],
            zv=lambda a,s:a in people[:2] and s=='source' and bits[2+people.index(a)],
            zk=lambda a,s:a in people[:2] and s=='source' and bits[4+people.index(a)] or (a,s)==('candidate','past') and bits[6])
    for bits in product((False,True),repeat=7):
        valid=any(bits[:2]) and all(not bits[i] or bits[i+2] and bits[i+4] for i in range(2))
        assert evaluate(doc,model(bits),people,scenes,True)==[valid,valid and bits[6]],bits
    refuse(doc,model((True,True,True,True,True,True,True)),('zr','zv','zk'),people,scenes)
    return dict(combinations=128,all_references_validated=True,nonempty_reference_required=True,
        candidate_can_differ_in_activity_and_time=True,unknown_inputs_refused=3)


def bodily_values(doc,variant='baseline'):
    values=source_model(doc,variant)
    previous_block=values['h2h']
    values.update(
        h3u=lambda p,anchor,act,scene:variant!='no_reference' and (p,anchor,act,scene)==(
            'other' if variant=='foreign_reference' else 'person','anchor','jump','before' if variant=='outside_reference' else 'case'),
        h3h=lambda p,act,scene:p=='person' and (act,scene) in (('jump','case'),('other','before')),
        h2h=lambda obj,limb,p,act,scene:previous_block(obj,limb,p,act,scene) or variant=='blocked_reference' and (obj,limb,p,act,scene)==('shackle','limb','person','jump','case'),
        h3e=lambda p,event,d,scene:(p,event,symbol(d),scene)==('person','experience','r2ir','before'),
        h3g=lambda event,p,d,start,end:(event,p,symbol(d),start,end)==('experience','person','r2ir','before','case'),
        h3f=lambda p,d,scene:variant=='familiar' and (p,symbol(d),scene)==('person','r2ir','case'),
        hzie=lambda p,factor,q,effect,scene:variant!='no_cause' and (p,symbol(factor),q,symbol(effect),scene)==(
            'person','h4b' if variant=='wrong_cause_description' else 'r2is','person','r2iu','case'),
        ea=(lambda *args:True) if variant=='no_cause' else unknown)
    return values


@lru_cache(None)
def bodily_checks():
    doc=fixture(['r2iq','r2ir','r2is','r2iu','r2iw','r2ix'],'r za[] a.r zb[] d.r zc[] d.r zpast[] d.'+
        'q[k r2iq[k za[]]].q[t[k r2ir[k za[]]][k zpast[]]].'+
        ''.join('q[t[k '+name+'[k za[]]][k zb[]]].' for name in ('r2is','r2iu','r2iw'))+
        'q[t[k r2ix[k za[]]][k zc[]]].')
    cases={
        'baseline':[True]*6,
        'familiar':[True,True,False,True,False,False],
        'no_reference':[False,False,False,True,False,False],
        'foreign_reference':[False,False,False,True,False,False],
        'outside_reference':[False,False,False,True,False,False],
        'blocked_reference':[False]*6,
        'no_jump':[False]*6,
        'steady_jump':[False]*6,
        'no_cause':[True,True,True,True,False,False],
        'wrong_cause_description':[True,True,True,True,False,False],
        'still_bound':[True,True,True,True,True,False],
        'invalid_history':[True,True,False,True,False,False],
        'no_cases':[False,False,False,True,False,False],
    }
    for name,expected in cases.items():
        values=bodily_values(doc,name);values['zpast']=lambda:'before'
        actual=evaluate(doc,values,PEOPLE,SCENES,True);assert actual==expected,(name,actual,expected)
    values=bodily_values(doc);values['zpast']=lambda:'before'
    refuse(doc,values,('h3u','h3h','hzie','h2r','h3e'))
    return dict(cases=cases,native_release_jump_kind_familiarity_and_cause_executed=True,
        past_kind_has_another_movement_without_a_ditch_or_uncertainty=True,
        explanatory_adoption_does_not_replace_cause=True,unknown_inputs_refused=5)


def mapping_document():
    doc=fixture(['r2in','r2iy'],'q[k r2in[]].q[k r2iy[]].')
    replacement=parse('p:r zreference[] c.d r2gi[] c[k zreference[]].')['declarations']
    doc['declarations']=[replacement[0]]+[deepcopy(replacement[1]) if d['name']=='r2gi' else d for d in doc['declarations']]
    doc['declarations']=closure(doc,['r2in','r2iy'])
    return parse(format_graph(doc,'compact'))


@lru_cache(None)
def mapping_checks():
    doc=mapping_document();seen=[]
    expected={('clause' if n=='h3a' else 'reason',t,d) for n,t,d in MAPPINGS}
    fg=dict(kind='call',symbol='r2ik',arguments=[]);bg=dict(kind='call',symbol='r2il',arguments=[])
    def model(variant='baseline',missing=None):
        values=unknowns(doc)
        def link(node,author,target,depiction,scope):
            row=(node,symbol(target),symbol(depiction));seen.append(row)
            return (author,scope)==('author','anchor') and row in expected and row!=missing
        values.update(h3a=lambda:'clause',h3s=lambda:'reason',wa=lambda:'author',wh=lambda:'anchor',
            zreference=lambda:variant!='missing_reference',qa=link,
            ue=lambda a,b,s:variant!='wrong_order' and (a,b,s)==('clause','reason','anchor'),
            hznreport=lambda n,a,d,sc,s:variant!='missing_claim' and (n,a,sc,s)==('reason','author','reason','anchor') and unwrap(d)==fg,
            hzrbgreport=lambda n,a,f,b,fs,bs,s:variant!='missing_background' and (n,a,fs,bs,s)==('reason','author','reason','clause','anchor') and unwrap(f)==fg and unwrap(b)==bg)
        if variant=='wrong_author':values['wa']=lambda:'other'
        if variant=='wrong_context':values['wh']=lambda:'elsewhere'
        return values
    rows={}
    people=('clause','reason','author','other');scenes=('anchor','elsewhere')
    for variant,wanted in [('baseline',[True,True]),('missing_reference',[False,False]),('wrong_order',[False,True]),
        ('missing_claim',[False,True]),('missing_background',[False,True]),('wrong_author',[False,False]),('wrong_context',[False,False])]:
        seen.clear();actual=evaluate(doc,model(variant),people,scenes,True)
        assert actual==wanted,(variant,actual);assert set(seen)==expected;rows[variant]=actual
    for missing in expected:
        assert evaluate(doc,model(missing=missing),people,scenes,True)==[True,False],missing
    refuse(doc,model(),('qa','zreference','hznreport','hzrbgreport'),people,scenes)
    return dict(cases=rows,missing_links_refused=6,closed_correspondences=len(expected),reference_boundary_test=True,
        bodily_and_intellectual_contents_not_executed=True,foreground_and_both_backgrounds_preserved=True,
        unknown_inputs_refused=4,correspondence_is_not_an_equivalence_proof=True)


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0010')
    parts=[
        ('Wer ',['r2ef','hzzn','r2ii'],'先行文と同じ人物範囲についての条件。'),
        ('sie ',['r2gi','r2gh','r2fh'],'足枷として描かれた規定・定型表現を同じ人物について受ける両側の指示。'),
        ('auch abwürfe, ',['r2gt','h3n','r2iy','r2ii'],'除去と依存離脱を対応させた仮定。現実の離脱や、それだけによる能力獲得は断言しない。'),
        ('würde dennoch ',['r2ig','r2ij','ke'],'離脱を認める通常予想では不確かな判断にならないという比較に反する帰結。候補は非空で同じ前件を満たす。'),
        ('auch über den schmalesten Graben ',['r2iv','r2hr','r2hs','r2il'],'固定した最小幅の溝と最小の困難を対応させ、より難しい課題での同じ結果より見込まれにくいという尺度背景を付ける。'),
        ('einen nur unsicheren Sprung thun, ',['r2id','r2ie','r2it','r2iu'],'存在する同じ活動の確かな遂行を対照にした限定。不確かな自由な跳躍と独立判断を対応させ、別の活動を排除しない。'),
        ('weil er ',['r2hj','r2iw','hzie'],'同じ人物・仮定内で不慣れが帰結に寄与する原因。説明採用だけでは代用しない。'),
        ('zu dergleichen freier Bewegung ',['r2iq','r2ir','r2hf','r2he'],'先行する跳躍を参照し、自由な自己の活動を共有面にする。対象側は自分の理解力を他者の指導なしに使う判断。課題や不確かさを経験種類の必須条件にしない。'),
        ('nicht gewöhnt ist.',['r2is','r2hh','rci'],'同じ有効な履歴と活動記述について、経験に由来する慣れがない。過去の経験があっても許し、未知や不正な参照から不慣れを導かない。'),
    ]
    clauses=[];position=474
    for text,roots,meaning in parts:
        assert unit['text'][position:position+len(text)]==text
        clauses.append(dict(range=[position,position+len(text)],text=text,definitions=roots,reading=meaning));position+=len(text)
    assert position==634
    paths={INDEX,INVENTORY,IMAGE,FULL,BASIS,PARENT,PARENT_BASIS,*PRIOR,*COVERAGE,*(p for p,_ in SENTENCES)}
    return dict(status='fourth_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[474,634],text=unit['text'][474:634]),
        clauses=clauses,selection=selection_binding(catalog(),[13,53]),decision='equivalent_under_stated_reading_for_this_sentence',
        references=[dict(url='https://korpora.org/Kant/aa08/036.html',title='Kant AA VIII036',accessed='2026-10-20',
            use='第四文全文と前後の足枷・少数者の文脈を照合。原刊483頁のschmalestenという綴りは資料内で保持する。')],
        original_page=dict(path=IMAGE,visually_inspected=True,page=483),interpretation_limits=LIMITS,
        revised_statement_indices=[13,53],supersedes_pending_sentence_judgment='data/limited-consequence-reading-v1.json',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        new_verified_sentence_characters=136,preserved_reviewed_sentence_characters=408,paragraph_reviewed_sentence_characters=544,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-11]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert len(new.document['statements'])==54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[13,53]
    assert [new.document['statements'][i]['body']['symbol'] for i in (13,53)]==['r2in','r2iy']
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        record=read(path);validate_hashes(ROOT,record['source_sha256']);indices=[s['index'] for s in record['selection']['statements']]
        assert record['selection']==selection_binding(old,indices)==selection_binding(new,indices)
    for path,indices in SENTENCES:
        record=read(path);validate_hashes(ROOT,record['source_sha256']);assert record['selection']==selection_binding(new,indices)
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    target=read(PRIOR[0]);assert target['native']['native_departure_cause_limitation_and_two_backgrounds_executed']
    assert target['native']['cases']['other_reliable_activity']==[True]*7
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(added_definitions=11,added_primitives=0,authored_statements=54,preserved_statements=52,revised_statement_indices=[13,53],
        preserved_review_selections=12,reviewed_nonblank_characters=2212,preserved_reviewed_sentence_characters=408,
        target_formal_checks_reused_with_identical_definitions=True,roundtrips=True)


@lru_cache(None)
def reading_checks():
    record=reading();assert read(AUDIT)==record;validate_hashes(ROOT,record['source_sha256'])
    pieces=record['clauses'];assert ''.join(p['text'] for p in pieces)==record['source']['text']
    assert all(a['range'][1]==b['range'][0] for a,b in zip(pieces,pieces[1:]))
    assert all(set(p['definitions'])<=set(record['selection']['dependencies']) for p in pieces)
    assert sum(not c.isspace() for c in record['source']['text'])==136
    assert record['paragraph_reviewed_sentence_characters']==108+139+161+136
    prior=set()
    for path in COVERAGE:
        row=read(path)['alignment'];assert row['unit_sha256']==record['source']['unit_sha256']
        prior.update(range(row['start'],row['end']))
    added=[i for i in range(474,634) if i not in prior and not record['source']['text'][i-474].isspace()]
    assert added==[575] and record['source']['text'][575-474]==','
    assert read(BASIS)['status']=='fourth_sentence_adopted_with_explicit_nonliteral_correspondence'
    return dict(source_partition_parts=9,reviewed_fourth_sentence_characters=136,paragraph_reviewed_sentence_characters=544,
        new_candidate_nonblank_positions=added,new_candidate_nonblank_characters=1,
        source_equivalence_is_reviewer_judgment_not_test_result=True,original_page_inspected=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('reference',reference_checks),('bodily',bodily_checks),('mapping',mapping_checks),('structure',structure_checks),('reading',reading_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    record=reading();paths=set(build())|set(catalog().source_sha256)|set(record['source_sha256'])|{
        AUDIT,DOC,'scripts/compose_fourth_sentence.py','scripts/check_fourth_sentence.py','scripts/register_fourth_sentence.py',
        'tests/test_fourth_sentence.py','scripts/check_learned_familiarity.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/check_attributed_focus.py'}
    for path in PRIOR:paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='whole_fourth_sentence_reviewed_under_explicit_reading',document=FULL,**results,
        alignment=dict(**record['source'],definitions=['r2in','r2iy','r2ix','r2iw','r2ir'],status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,new_covered_characters=1,
        new_verified_sentence_characters=136,preserved_reviewed_sentence_characters=408,paragraph_reviewed_sentence_characters=544,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
