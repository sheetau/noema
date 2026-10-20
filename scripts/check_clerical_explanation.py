"""Check the same teaching message, its nonfactive characterization and Denn."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_clerical_explanation import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_teaching_policy import EXTRA_LOCAL,PROVIDERS,SMALL,SCENES,local_model,two_messages
from scripts.check_representative_policy import appointment_values,PAST_SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v173.json'
REPORT='reports/clerical-explanation-v1.json'
AUDIT='data/clerical-explanation-reading-v1.json'
DOC='docs/clerical-explanation-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/representative-teaching-evidence-v1.json'
LEXICAL='data/teaching-discretion-lexical-v1.json'
PRIOR=tuple('reports/'+n+'-v1.json' for n in ('clerical-conscience','representative-teaching','representative-policy','teaching-discretion'))
DISCOURSE=('author','reason','prior','other')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,query=None,boundaries=(),finite=False,extra=''):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    prefix=parse('p:'+EXTRA_LOCAL+extra+PROVIDERS)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[deepcopy(providers.get(d['name'],d)) for d in doc['declarations']]
    if query is None:
        args=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]'
        if target=='r4k':args+=' k zoccasion[] k zactivity[]'
        if target in ('r4k','r4g'):args+=' r[p zmessage]'
        if target in ('r4l','r4m'):args=''
        query='k '+target+'['+args+']'
        if target!='r4m':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    return parse(format_graph(two_messages(doc),'compact')) if finite else doc


def presentation_values(doc,variant='baseline'):
    v=local_model(doc,variant)
    v['h247n']=lambda p,r,c,s,at:(p,r,c,s,at)==('person','role','church','subject','outcome')
    def characterize(p,a,recipient,s,message,description,bindings,ref,at):
        return variant!='no_characterization' and not(variant=='missed_second_recipient' and recipient=='overlap') and (
            p,a,s,symbol(message),message.rank,symbol(description),description.rank,tuple(bindings.items),ref,at)==(
            'other' if variant=='wrong_speaker' else 'person','activity','subject',
            'zbadmessage' if variant=='different_message' else 'zmessage',0,'r4i' if variant=='only_positive' else 'r4j',2,NAMES,
            'other' if variant=='wrong_reference' else 'reference','outcome')
    def contrast(p,a,recipient,s,message,negative,positive,bindings,ref,at):
        return variant!='no_contrast' and (p,a,s,symbol(message),message.rank,symbol(negative),negative.rank,
            symbol(positive),positive.rank,tuple(bindings.items),ref,at)==('person','activity','subject','zmessage',0,
            'r4i' if variant=='reversed_contrast' else 'r4h',2,'r4h' if variant=='reversed_contrast' else 'r4i',2,NAMES,'reference','outcome')
    v.update(h247r=characterize,h247s=contrast)
    return v


@lru_cache(None)
def native_checks():
    doc=fixture('r4k');rows={}
    for variant in ('baseline','congregation_task','no_event','other_presenter','no_recipient_reached','position_role',
        'no_characterization','missed_second_recipient','wrong_speaker','different_message','only_positive','wrong_reference','no_contrast','reversed_contrast'):
        v=presentation_values(doc,variant)
        for n in ('h247p','h247q','h246m','h247o','zjudge'):v[n]=unknown
        actual=evaluate(doc,v,SMALL,SCENES,True)
        assert actual==[variant in ('baseline','congregation_task')],(variant,actual);rows[variant]=actual[0]
    for n in ('h247r','h247s','h246o','f2'):
        v=presentation_values(doc);v[n]=unknown
        try:evaluate(doc,v,SMALL,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,native_official_teaching=True,all_actual_assigned_recipients=True,
        exact_same_message_and_rank_two_characterization=True,quoted_discretion_appointment_and_conformity_not_executed=True)


@lru_cache(None)
def property_checks():
    doc=fixture('r4g');rows=[]
    for appointed,conforms in product((False,True),repeat=2):
        v=local_model(doc);appointment=appointment_values(doc,'baseline' if appointed else 'absent_terms')
        v.update({n:f for n,f in appointment.items() if f is not unknown})
        v['zpass']=lambda *args:Content(PAST_SCENES,(True,)*len(PAST_SCENES))
        v['zjudge']=lambda subject,code:Content(PAST_SCENES,tuple(conforms and subject=='subject' and symbol(code)=='zmessage' for _ in PAST_SCENES))
        actual=evaluate(doc,v,SMALL,PAST_SCENES,True)
        assert actual==[appointed and conforms],(appointed,conforms,actual);rows.append(dict(appointed=appointed,message_conforms=conforms,result=actual[0]))
    return dict(truth_table=rows,native_appointment_and_same_message_criteria=True,general_appointment_alone_does_not_qualify_arbitrary_message=True)


@lru_cache(None)
def binding_checks():
    def case(values,code='zmessage',reference='reference',bits=(True,True)):
        query='t[k r4j[l[a]['+' '.join('k z'+x+'[]' for x in values)+'] r[p '+code+'] k zref[]]][k zpoint[]]'
        doc=fixture('r4j',query,('r4e','r4g'),extra='r zx[] a.r zy[] a.')
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:reference,zpoint=lambda:'outcome')
        if len(values)==9:
            p,r,c,cong,students,members,creed,subject,standard=values
            expected_negative=(c,p,r,subject,code,0,reference)
        else:expected_negative=()
        def negative(source,p,r,s,message,ref):
            good=(source,p,r,s,symbol(message),message.rank,ref)==expected_negative
            return Content(SCENES,(good and bits[0],)*len(SCENES))
        def positive(*args):
            good=tuple(args[:-2])==tuple(values) and args[-2]==reference and symbol(args[-1])==code and args[-1].rank==0
            return Content(SCENES,(good and bits[1],)*len(SCENES))
        v.update(r4e=negative,r4g=positive)
        return evaluate(doc,v,('x','y'),SCENES,True)
    for position in range(9):
        values=tuple('y' if i==position else 'x' for i in range(9))
        for code in ('zmessage','zbadmessage'):
            assert case(values,code)==[True],(position,code)
    for bits in product((False,True),repeat=2):assert case(('x',)*9,bits=bits)==[all(bits)]
    for length in (0,8,10):assert case(('x',)*length)==[False],length
    assert case(('x',)*9,reference='other')==[True]
    return dict(independent_nine_positions_and_two_messages=True,reference_forwarded=True,wrong_lengths_rejected=[0,8,10],
        independent_property_conjunction=True,boundaries=['r4e','r4g'],native_property_evidence=[PRIOR[-1],'property_checks'])


@lru_cache(None)
def scope_checks():
    doc=fixture('r4l',boundaries=('r372','r4k'),finite=True);rows={}
    names=(*NAMES,'occasion','activity');domain=('x','y');times=('reference','outcome')
    for position in range(len(names)):
        selected=tuple('y' if i==position else 'x' for i in range(len(names)))
        for fail in (False,True):
            v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'};seen=set();forwarded=set()
            fixed=(*selected[:9],'reference',*selected[9:])
            def actual(*args):
                key=(*args[:-1],symbol(args[-1]));seen.add(key)
                return Content(times,(key==(*fixed,'zbadmessage'),)*2)
            def presented(*args):
                key=(*args[:-1],symbol(args[-1]));forwarded.add(key)
                return Content(times,(not fail or key!=(*fixed,'zbadmessage'),)*2)
            v.update(h232v=lambda:'reference',zpoint=lambda:'outcome',r372=actual,r4k=presented)
            result=evaluate(doc,v,domain,times,True)
            assert result==[not fail] and (*fixed,'zbadmessage') in forwarded,(position,fail,result)
            # A universal quantifier stops at its first counterexample.
            # Successful cases must traverse the complete diagnostic domain;
            # failures must reach the selected counterexample at every slot.
            assert seen==forwarded and (*fixed,'zbadmessage') in seen
            if not fail:assert len(seen)==2**len(names)*2
            rows[names[position]+('_fail' if fail else '_pass')]=result[0]
    complete=fixture('r4l',boundaries=('r372','r4k'))
    try:evaluate(complete,v,domain,times,True)
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Full message domain silently reduced')
    return dict(contrasts=rows,all_case_task_activity_and_message_positions=True,full_domain_refused=refusal,
        boundaries=['r372','r4k'],two_messages_only_in_diagnostic=True)


def discourse_model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(h247t=lambda:'reason',h247m=lambda:'prior',wa=lambda:'author',h232o=lambda:'reference')
    v['h236i']=lambda node,author,code,ctx:variant!='no_claim' and (node,author,symbol(code),code.rank,ctx)==(
        'reason','other' if variant=='wrong_author' else 'author','r4j' if variant=='wrong_content' else 'r4l',3,'other' if variant=='wrong_context' else 'reference')
    v['ud']=lambda author,premises,conclusion,ctx:variant!='no_explanation' and (author,conclusion,ctx)==('author','reason' if variant=='wrong_conclusion' else 'prior','reference') and {
        n for n in DISCOURSE if premises(n)}==({'prior'} if variant=='reversed_reason' else {'reason'})
    v['ue']=lambda a,b,c:variant!='reversed_order' and (a,b,c)==('prior','reason','reference')
    return v


@lru_cache(None)
def discourse_checks():
    doc=fixture('r4m');rows={}
    for variant in ('baseline','no_claim','wrong_author','wrong_content','wrong_context','no_explanation','wrong_conclusion','reversed_reason','reversed_order'):
        actual=evaluate(doc,discourse_model(doc,variant),DISCOURSE,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=discourse_model(doc);v.update(h247t=lambda:'prior',h236i=lambda *a:True,ud=lambda *a:True,ue=lambda *a:True)
    assert evaluate(doc,v,DISCOURSE,SCENES,True)==[False]
    return dict(contrasts=rows,distinct_reason_and_conclusion=True,quotation_not_executed=True)


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('Denn, ',['ud','r4m'],'本一文を直前の良心の文の説明として提示する。'),
        ('was er zu Folge seines Amts, ',['r35t','r357','cb','r372'],'同じ本人の同じ職務上の教示の内容を受ける。'),
        ('als Geschäftträger der Kirche, ',['cf','h246k','h247n','r37z','r372'],'同じ教会の業務を委託された立場を保持する。'),
        ('lehrt, das stellt er als etwas vor, ',['f2','h247r','r4j','r4k'],'実際の教示の同じ内容を、その性格付けを備えるものとして担当宛先へ提示する。'),
        ('in Ansehung dessen er nicht freie Gewalt hat ',['h247p','r4d','r4e','r4h'],'同じ主題・発話について自由な内容決定権限の組合せを否定する。'),
        ('nach eigenem Gutdünken zu lehren, ',['h247q','r4d','r4e'],'本人の判断を他者の規定で制限されない最終的な基準とすること。思考や個々の実務判断の全否定にはしない。'),
        ('sondern ',['h247s','r4h','r4i','r4k'],'本人による提示の中で否定側に代わる肯定的な性格付けを対置する。'),
        ('das er nach Vorschrift ',['r35s','rfu','r374','r375','r376','r377','r4g'],'同じ発話への採用基準適合と、同じ全担当機会の方針を引用内容で結ぶ。'),
        ('und im Namen eines andern ',['h247o','r37z','r373','r374'],'本人と異なる同じ教会の立場で、その名による提示を目的内容に保持する。'),
        ('vorzutragen angestellt ist.',['r4a','r4b','r4c','r4g','r4i'],'同じ一般的教示方針への同じ過去任用と現職を結び、当該発話を規定に沿う内容として位置付ける。'),
    ]
    cursor,clauses=3528,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==3793
    text=unit['text'][3528:3793];count=sum(not c.isspace() for c in text);assert count==222
    pages=read(EVIDENCE)['pages']
    for page in pages:assert page['visually_inspected'] and digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='clerical_explanation_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[3528,3793],text=text),selection=selection_binding(catalog(),[89]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_teaching_characterization_and_explanation',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,
        preserved_reviewed_sentence_characters=3020,paragraph_reviewed_sentence_characters=3242,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁末尾と487頁冒頭の連続を確認し、当該文と後続の教会の教え・確信・内面の宗教・辞職の説明を読み、依存群と全文を照合した。連続した全文範囲を語句対応で覆う。',
            '同じ全聖職者事例の全職務上の実教示について、was/das/dessenと後続dasを同じ主題・閉じた発話へ固定した。本人の学識者としての別の活動を職務上の教示に混ぜない。',
            '提示される性格付けは、自由な自己裁量の否定と他者の規定・名による任用である。同じ発話への規定適合を引用内に加え、一般的任用だけで任意の内容を任用対象としていないことを確認した。',
            '任用方針の全機会・期間・宛先と追加教示への条件を保持した。過去任用と現在の職務保持を分け、引用内容の評価でのみ必要な時点・行為・条件が結ばれることを追った。',
            'sondernは教示者による性格付けの中の対置、Dennは著者による前文への説明として段階を分けた。提示関係から裁量否定・任用・内容の真理を実行せず、説明から全職務行為の無条件免責を導かない。',
            '有限診断での全称範囲の接続と、原定義の全発話記述域を区別した。今回の通読判断は明示解釈下の文単位判断であり、第五段落全体や二作品の完成ではない。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,LEXICAL,*PRIOR,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['statements'][:89]==old.document['statements'] and len(new.document['statements'])==90
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-conscience-reading-v1.json');assert prior['selection']==selection_binding(new,[88]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=89,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=222,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('native',native_checks),('property',property_checks),('bindings',binding_checks),('scope',scope_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,LEXICAL,*PRIOR,
        *[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-conscience-reading-v1.json','scripts/compose_clerical_explanation.py','scripts/check_clerical_explanation.py',
        'tests/test_clerical_explanation.py','scripts/check_teaching_policy.py','scripts/check_representative_policy.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_protected_remarks.py','scripts/compose_civic_example.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='clerical_exposition_characterized_as_prescribed_representative_appointment',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[89],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
