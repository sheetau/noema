"""Check shared references, nonexhaustive examples and nested purpose discourse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,DescriptionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_covenant_question import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v180.json'
REPORT='reports/covenant-question-v1.json'
READING='data/covenant-question-reading-v1.json'
DOC='docs/covenant-question-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/covenant-entitlement-v1.json','reports/mediated-guardianship-v1.json','reports/classis-self-name-v1.json')
SCENES=('reference','candidate','context')
EXTRA='r zone[] a.r ztwo[] a.r zpoint[] d.'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra+query)

def base(doc):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(zone=lambda:'one',ztwo=lambda:'two',zpoint=lambda:'candidate',h255o=lambda:'reference',h255n=lambda:'context')
    return values
def run(doc,v,domain=('one','two')):return evaluate(doc,v,domain,SCENES,True)
def content(value):return Content(SCENES,tuple(value and p=='candidate' for p in SCENES))

@lru_cache(None)
def reference_checks():
    q='q[t[k r47m[]][k zpoint[]]].q[t[k r47n[]][k zpoint[]]].q[e[k r47o[]][k r47p[]]].'
    doc=fixture(('r47m','r47n','r47o','r47p'),q,('r47i',));rows={}
    for variant in ('baseline','assessor','role','community','reference','no_entitlement'):
        v=base(doc);v.update(h255q=lambda:'role',h255r=lambda:'community')
        v['h255p']=lambda community,ref:'assessor' if (community,ref)==('community','reference') else 'other'
        for key,n in (('role','h255q'),('community','h255r'),('reference','h255o')):
            if variant==key:v[n]=lambda key=key:'context' if key=='reference' else 'other'
        if variant=='assessor':v['h255p']=lambda *a:'other'
        v['r47i']=lambda *args:content(variant!='no_entitlement' and args==('assessor','role','community','reference'))
        actual=run(doc,v,('one','two','assessor','role','community','other'));assert actual==[variant=='baseline',variant!='baseline',False],(variant,actual);rows[variant]=actual
    return dict(common_reference_contrasts=rows,native_negative_content_and_distinct_question_answer_force=True,
        boundary='r47i; existential normative construction checked in covenant-entitlement-v1')

@lru_cache(None)
def example_checks():
    doc=fixture(('r47q','r47r','r47s','r47t','r47u','r47v'),''.join('q[t[k '+n+'[k zone[]]][k zpoint[]]].' for n in ('r47q','r47r','r47s','r47t','r47u','r47v')),
        ('r47e','r46f','r46k','r46n'))
    rows={}
    for council,classis,selfname in product((False,True),repeat=3):
        v=base(doc);v.update(h254u=lambda:'title',h254v=lambda:'usage')
        v['r47e']=lambda body,ref:(body,ref)==('one','reference')
        v['r46f']=lambda body,ref:council and (body,ref)==('one','reference')
        v['r46k']=lambda body,ref:classis and (body,ref)==('one','reference')
        v['r46n']=lambda body,title,usage,ref:selfname and (body,title,usage,ref)==('one','title','usage','reference')
        actual=run(doc,v,('one','two','title','usage'));expected=[True,council,classis and selfname,classis,selfname,council or (classis and selfname)]
        assert actual==expected,(council,classis,selfname,actual);rows[str((council,classis,selfname))]=actual
    return dict(native_classification_and_selfname_conjunction_and_inclusive_alternatives=rows,
        general_scope_can_hold_without_either_example=True,boundaries=['r47e','r46f','r46k','r46n'])

@lru_cache(None)
def purpose_checks():
    correct=('one','two','two','one','two')
    choices=[(),correct,correct[:-1],(*correct,'one')]+[tuple(('two' if x=='one' else 'one') if i==j else x for j,x in enumerate(correct)) for i in range(5)]
    rows={}
    for seq in choices:
        literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
        doc=fixture(('r47w','r47x','r47z'),''.join('q[t[k '+n+'['+literal+']][k zpoint[]]].' for n in ('r47w','r47x','r47z')),('r466','r47b'))
        v=base(doc);v['h254z']=lambda agreement:'reference' if agreement=='two' else 'context'
        v['r466']=lambda body,community,subject,ref:content((body,community,subject,ref)==('one','two','one','reference'))
        v['r47b']=lambda body,agreement,community,subject,ref:content((body,agreement,community,subject,ref)==('one','two','two','one','reference'))
        actual=run(doc,v)
        # Creed remains a formation parameter but does not change the projected goal.
        valid=len(seq)==5 and tuple(seq[i] for i in (0,1,3,4))==('one','two','one','two')
        assert actual==[valid]*3,(seq,actual);rows[str(seq)]=actual
    literal='l[a]['+' '.join('k z'+n+'[]' for n in correct)+']'
    doc=fixture(('r47w','r47x','r47z'),''.join('q[t[k '+n+'['+literal+']][k zpoint[]]].' for n in ('r47w','r47x','r47z')),('r466','r47b'))
    truth_table={}
    for baseline,focus in product((False,True),repeat=2):
        v=base(doc);v['h254z']=lambda a:'reference';v['r466']=lambda *a:content(baseline);v['r47b']=lambda *a:content(focus)
        actual=run(doc,v);assert actual==[baseline,focus,baseline and focus];truth_table[str((baseline,focus))]=actual
    return dict(exact_five_argument_projection=rows,native_goal_conjunction=truth_table,
        creed_is_preserved_as_formation_argument_not_new_guardianship_target=True,
        boundaries=['r466','r47b; native future and causal dependencies checked in mediated-guardianship-v1'])

@lru_cache(None)
def expectation_checks():
    seq=('one','two','two','one','two');literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
    doc=fixture(('r47y',),'q[t[k r47y['+literal+']][k zpoint[]]].');rows={}
    for variant in ('baseline','tie','reverse','missing_reflexive','wrong_bindings','wrong_reference','wrong_view'):
        v=base(doc);v['wa']=lambda:'one'
        def comparison(view,left,right,bindings,reference):
            if (view,tuple(bindings.items),reference)!=('two' if variant=='wrong_view' else 'one',
                tuple(reversed(seq)) if variant=='wrong_bindings' else seq,'context' if variant=='wrong_reference' else 'reference'):return False
            pair=(symbol(left),symbol(right));assert left.rank==right.rank==0
            accepted={('r47w','r47w'),('r47x','r47x')}
            if variant=='missing_reflexive':accepted.remove(('r47x','r47x'))
            accepted.add(('r47x','r47w') if variant=='reverse' else ('r47w','r47x'))
            if variant=='tie':accepted.add(('r47x','r47w'))
            return pair in accepted
        v['h256e']=comparison;actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(strict_two_member_expectation_order=rows,quoted_purposes_not_executed=True)

def normalized(args):
    return tuple((symbol(a),a.rank) if isinstance(a,DescriptionValue) else a for a in args)

@lru_cache(None)
def discourse_checks():
    doc=fixture(('r472','r473'),'q[k r472[]].q[k r473[]].',extra='')
    nodes=('h254d','h255s','h255t','h255u','h255v','h255w','h255x','h255y','h255z','h256a','h256b')
    q=('r47o',0);pos=('r47m',0);neg=('r47n',3);a='author';ctx='context'
    expected={
        'hzcr':{('h255s',a,q,ctx)},
        'h256c':{('h255v',a,q,('r47q',0),('r47r',0),('r47s',0),('r47v',0),ctx)},
        'h256d':{('h255w',a,q,('r47t',0),('r47u',0),ctx)},
        'h234k':{('h255w',a,'h255v',ctx)},
        'h256f':{('h255y',a,q,('r47f',0),('r47z',0),('r47w',0),('r47x',0),('r47y',0),ctx)},
        'h256g':{('h256a',a,q,pos,ctx)},
        'h256i':{('h255s',a,'h254d',('r45y',3),q,ctx)},
        'h236i':{('h255t',a,neg,ctx)},
        'h236m':{('h255u',a,'h255s','h255t',neg,ctx)},
        'hzcs':{(a,'h255s','h255t',ctx)},
        'h256h':{('h255z',a,neg,pos,ctx)},
        'ue':{('h254d','h255s',ctx),('h255x','h255y',ctx),('h255s','h255t',ctx),('h255u','h256b',ctx)},
    }
    question_relations={'hzcr','h256c','h256d','h234k','h256f','h256g','h256i'}
    rows={}
    for variant in ('baseline',*expected,'author','context','merged','unknown'):
        v=base(doc);v.update({n:lambda n=n:n for n in nodes});v['wa']=lambda:'other' if variant=='author' else a
        for n,wanted in expected.items():v[n]=lambda *args,n=n,wanted=wanted:n!=variant and normalized(args) in wanted
        if variant=='context':v['h255n']=lambda:'reference'
        if variant=='merged':
            v['h255t']=lambda:'h255s'
            for n in expected:v[n]=lambda *a:True
        if variant=='unknown':
            v['h256f']=unknown
            try:run(doc,v,nodes+(a,'other'))
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError('unknown was accepted')
            continue
        actual=run(doc,v,nodes+(a,'other'))
        wanted=[variant not in question_relations|{'ue','author','context'},variant not in (set(expected)-question_relations)|{'author','context','merged'}]
        assert actual==wanted,(variant,actual,wanted);rows[variant]=actual
        # All norm, formation, guidance and temporal truth callbacks remain unknown.
        assert all(v[n] is unknown for n in ('h7l','h7k','h255l','h255k','dc','h256e'))
    return dict(contrasts=rows,closed_same_contents_and_authorship=True,quotation_not_execution=True,unknown_rejected=True,
        answer_intro_precedes_answer_body_not_its_containing_whole=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    parts=[
        ('Aber ',['h256i','r45y'],'前段落の不合理評価を受け、対照的な反対考慮として問いを出す。'),
        ('sollte nicht ',['r47o','h256g'],'資格があるのではという仮の見込みを持つ否定疑問。'),
        ('eine Gesellschaft von Geistlichen, ',['r47e','r47h','r47i'],'教会関係の職務者・代表者からなる団体の一般範囲を検討する。'),
        ('etwa eine Kirchenversammlung, oder eine ehrwürdige Klassis ',['h256c','r47r','r47s','r47v'],'教会会議または敬称付き自己呼称を持つClassisを非網羅的に例示する。'),
        ('(wie sie sich unter den Holländern selbst nennt) ',['h234k','h256d','r47t','r47u'],'同じClassisの名称を、同じ用法共同体での自己呼称として説明する括弧。'),
        ('berechtigt sein, ',['r47g','r47m','rdu','h255p'],'同じ合意形成に正当な規範上の資格があるかを問う。'),
        ('sich eidlich unter einander ',['r46x','r46y','r47d'],'同じ団体の固定した全当事者が、同じ引受け行為で互いへの宗教上の宣誓をする。'),
        ('auf ein gewisses unveränderliches Symbol zu verpflichten, ',['r46p','r46q','r46r','r46t','r46u','hzcg'],'同じ特定の信条を維持し実質変更を認めない条項への拘束を引き受ける。'),
        ('um so eine unaufhörliche Obervormundschaft ',['h255l','h255m','r466','r47w'],'その営みにより中断しない上位後見を行う共同目的。'),
        ('über jedes ihrer Glieder ',['r462','r464'],'同じ団体の各時点の全成員への宗教的な上位後見。'),
        ('und vermittelst ihrer über das Volk zu führen, ',['r463','r464','h255j'],'同じ成員の後見を介して同じ共同体の全人民へ及ぶ団体の指導。'),
        ('und diese so gar zu verewigen?', ['r47b','r47c','r47x','r47y','r47z','h256f'],'同じ後見の、同じ合意による終点なしの成立・維持までを目的とする取り立て。'),
    ]
    cursor=0;clauses=[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==409 and unit['text'][409:410]==' '
    for text,names,meaning in (
        ('Ich sage: ',['h236m','h236i'],'著者自身が同じ問いへの回答者だと明示する。'),
        ('das ist ',['r47n','hzcs'],'同じ資格事例の存在を否定する応答として先の問いを受ける。'),
        ('ganz ',['h256h'],'部分的な例外や留保のない拒否を強調する。'),
        ('unmöglich.',['r47j','r47n'],'当該の規範上の資格の例は一つもない。物理的不可能性へ読み替えない。')):
        if cursor==409:cursor=410
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==443
    page=read('data/mediated-guardianship-reading-v1.json')['primary_page']
    assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='covenant_question_and_answer_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,443],text=unit['text'][:443]),
        selection=selection_binding(catalog(),[96,97]),clauses=clauses,interpretation=LIMITS,unresolved=[],
        decision='equivalent_under_stated_reading_for_covenant_question_and_answer',whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][:443]),
        semantic_equivalence_automatically_proved=False,original_page=dict(**page,visually_inspected=True),
        holistic_review=[
            '原刊488頁と固定原文を照合し、問いとその直後の回答を一組として通読した。一般団体の範囲を維持し、二つの例示を資格の候補範囲への排他的制限にしない。Classisの分類と自己呼称の同じ対象を保った。',
            '特定の同じ信条への不変の拘束、固定全当事者の同じ相互宣誓、宣誓行為の共同目的への参加を、同じ形成内容の中に保持した。引用の外側で当事者・神的権威・契約の現実的な実在を断言しない。',
            '各時点の全成員と、その成員の指導を媒介にした全人民への上位後見を同じ団体・主題・共同体に結んだ。基準側と永続化側は合意の同じ固定基準を使い、sogarによる強調を目的の内側に置いた。',
            'berechtigtを正当な規範上の資格と読み、否定疑問と回答を同じ肯定命題から構成した。dasはその資格への問いを受け、ganz unmöglichはその全面的拒否とする。後続の契約の無効性はここに先取りしない。',
            'Aberの対照、sollte nichtの仮の期待、括弧説明、Ich sageの明示的な回答者帰属、ganzの強調と本文順序を確認した。検査結果をこの通読判断の代用にはしていない。第六段落全体は未判断。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,page['path'],*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:96]==old.document['statements'] and len(new.document['statements'])==98
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in dependency().entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=96,added_statements=2,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=read(READING)['newly_reviewed_sentence_characters'])

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('references',reference_checks),('examples',example_checks),('purposes',purpose_checks),('expectation',expectation_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,read(READING)['original_page']['path'],
        'scripts/compose_covenant_question.py','scripts/check_covenant_question.py','tests/test_covenant_question.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_covenant_entitlement.py'}
    return dict(status='covenant_question_and_answer_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[96,97],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
