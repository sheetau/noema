"""Verify adoption appraisals and review the complete fifth sentence."""
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
from scripts.compose_posterity_rights_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure,NAMES,NODES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

INDEX='data/semantic-review-index-v183.json'
REPORT='reports/posterity-rights-v1.json'
READING='data/posterity-rights-reading-v1.json'
DOC='docs/posterity-rights-v1.md'
LEXICAL='data/posterity-rights-lexical-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('cohort-covenant-denial','human-vocation-offense','posterity-repudiation'))
SCENES=('reference','candidate','context','first','last')
EXTRA='r zone[] a.r ztwo[] a.'+''.join('r z'+s+'[] d.' for s in SCENES)
SEQ=('one','two','one','two','two','one')
LITERAL='l[a]['+' '.join('k z'+n+'[]' for n in SEQ)+']'
TRIPLE='l[a][k zone[] k ztwo[] k zone[]]'
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
def run(doc,v,domain=('one','two')):return evaluate(doc,v,domain,SCENES,True)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zone=lambda:'one',ztwo=lambda:'two',h26av=lambda:'reference',h254z=lambda a:'first',
        h26ax=lambda:'one',h26ay=lambda:'two',h255n=lambda:'context')
    v.update({'z'+s:lambda s=s:s for s in SCENES});return v
def content(value):return Content(SCENES,tuple(value and p=='candidate' for p in SCENES))
def unknown_check(doc,model,names):
    for name in names:
        v=model();v[name]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return list(names)
def adoption_model(doc,variant='baseline',all_decisions=False):
    v=base(doc)
    v['h26bk']=lambda a,r,t:variant!='no_decisions' and(a,t)==('two','first') and(r=='one' or all_decisions)
    v['dg']=lambda a,t:variant!='not_occurred' and(a,t)==('two','first')
    def adopt(act,g,a,r,ref,c,t):
        expected=['two','one','two',r if all_decisions else 'one','reference','candidate','first']
        keys=('act','group','agreement','resolution','reference','candidate','anchor')
        for i,key in enumerate(keys):
            if variant=='other_'+key:expected[i]='other'
        return (act,g,a,r,ref,c,t)==tuple(expected)
    v['h26bu']=adopt;return v
@lru_cache(None)
def adoption_checks():
    doc=fixture(('r5d5',),'q[t[k r5d5['+TRIPLE+']][k zcandidate[]]].');rows={}
    for variant in ('baseline','no_decisions','not_occurred',*('other_'+k for k in ('act','group','agreement','resolution','reference','candidate','anchor'))):
        actual=run(doc,adoption_model(doc,variant));assert actual==[variant=='baseline'];rows[variant]=actual[0]
    for length in (2,4):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in ('one','two','one','one')[:length])+']'
        d=fixture(('r5d5',),'q[t[k r5d5['+seq+']][k zcandidate[]]].');assert run(d,adoption_model(d))==[False]
    return dict(same_adoption_and_actual_occurrence=rows,wrong_lengths_rejected=True,
        unknown_rejected=unknown_check(doc,lambda:adoption_model(doc),('h26bk','dg','h26bu','h254z')))

def norm_model(doc,permit=False,oppose=True,grave=True,defiant=True,variant='baseline',all_decisions=False):
    v=adoption_model(doc,all_decisions=all_decisions)
    def norm(s,p,r,c,b,sign,t):
        return normalized((s,p,r,c,b,t))==('one','one','two',('r5d5',0),('one','two',b.items[2] if all_decisions else 'one'),'candidate')
    v['h7l']=lambda *a:permit and a[5] and norm(*a)
    v['h7k']=lambda *a:oppose and not a[5] and norm(*a)
    def appraisal(*a):
        want=['one','one','one','two',('r5d5',0),('one','two',a[5].items[2] if all_decisions else 'one'),'reference','candidate']
        for i,k in enumerate(('source','nature','group','role','code','bindings','reference','point')):
            if variant=='other_'+k:want[i]=('r5db',0) if i==4 else ('two','one','one') if i==5 else 'other'
        return normalized(a)==tuple(want)
    v['h26bt']=lambda *a:grave and appraisal(*a);v['h26bv']=lambda *a:defiant and appraisal(*a)
    return v
@lru_cache(None)
def qualification_checks():
    doc=fixture(('r5d6','r5d7'),'q[k r5d6[k zone[] k ztwo[] k zone[] k zcandidate[]]].q[k r5d7[k zone[] k zone[] k ztwo[] k zone[] k zcandidate[]]].');rows={}
    for permit,oppose,grave,defiant in product((False,True),repeat=4):
        v=norm_model(doc,permit,oppose,grave,defiant);actual=run(doc,v)
        assert actual==[permit and not oppose,oppose and grave and defiant];rows[str((permit,oppose,grave,defiant))]=actual
        assert v['dg'] is not unknown  # supplied but quotation must not call it
        v['dg']=unknown;v['h26bu']=unknown;assert run(doc,v)==actual
    contrasts={}
    for k in ('source','nature','group','role','code','bindings','reference','point'):
        actual=run(doc,norm_model(doc,variant='other_'+k));assert actual==[False,False];contrasts[k]=False
    return dict(qualification_and_two_appraisals=rows,exact_normative_target=contrasts,adoption_not_executed=True,
        unknown_rejected=unknown_check(doc,lambda:norm_model(doc),('h7l','h7k','h26bt','h26bv')))

def nature(v):
    v['h26bo']=lambda n,c,r:normalized((n,c,r))==('one',('aa',0),'reference')
    v['h26bp']=lambda n,b,r:(n,b,r)==('one','two','reference')
    v['h26bq']=v['h26bp']
    v['h26br']=lambda b,c,r:normalized((b,c,r))==('two',('r5dw',0),'reference')
    v['h26bs']=lambda n,s,r:(n,s,r)==('one','one','reference')
    return v
@lru_cache(None)
def resolution_checks():
    args=' '.join('k z'+n+'[]' for n in SEQ)
    doc=fixture(('r5ea',),'q[k r5ea['+args+' k zcandidate[]]].');rows={}
    for variant in ('baseline','missing_second_adoption','second_not_defiant','no_decisions','no_nature_ground'):
        v=nature(norm_model(doc,all_decisions=True))
        if variant=='missing_second_adoption':
            original=v['h26bu'];v['h26bu']=lambda *a:a[3]!='two' and original(*a)
        if variant=='second_not_defiant':
            original=v['h26bv'];v['h26bv']=lambda *a:a[5].items[2]!='two' and original(*a)
        if variant=='no_decisions':v['h26bk']=lambda *a:False
        if variant=='no_nature_ground':v['h26bs']=lambda *a:False
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert 'h26as' not in v and v['h256o'] is unknown
    return dict(native_all_decisions_same_nature_and_qualification=rows,goal_and_enlightenment_not_executed=True,no_definition_boundaries=True)

@lru_cache(None)
def connection_checks():
    matrices={};tables={}
    for root,target in (('r5eb','r5ea'),('r5ec','r5dv'),('r5ee','r5eb')):
        def case(selected,expected,length=0):
            names=['two' if i==selected else 'one' for i in range(6)]
            if length<0:names.pop()
            if length>0:names.append('one')
            seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
            boundary=(target,) if root=='r5eb' else ('r5db',target)
            doc=fixture((root,),'q[t[k '+root+'['+seq+']][k zcandidate[]]].',boundary);v=base(doc)
            wanted=tuple('two' if i==expected else 'one' for i in range(6))
            if root=='r5eb':v[target]=lambda *a:a==(*wanted,'candidate')
            else:
                v['r5db']=lambda b:content(True);v[target]=lambda b:content(tuple(b.items)==wanted)
            return run(doc,v)[0]
        matrix=[]
        for i,j in product(range(6),repeat=2):
            actual=case(i,j);assert actual==(i==j);matrix.append(actual)
        assert not case(0,0,-1) and not case(0,0,1);matrices[root]=matrix
    for root,target in (('r5ec','r5dv'),('r5ee','r5eb')):
        doc=fixture((root,),'q[t[k '+root+'['+LITERAL+']][k zcandidate[]]].',('r5db',target));rows={}
        for formed,result in product((False,True),repeat=2):
            v=base(doc);v['r5db']=lambda b:content(formed);v[target]=lambda b:content(result)
            actual=run(doc,v);assert actual==[not formed or result];rows[str((formed,result))]=actual[0]
        tables[root]=rows
    scopes={}
    for root,target in (('r5ed','r5ec'),('r5ef','r5ee')):
        doc=fixture((root,),'q[t[k '+root+'[]][k zcandidate[]]].',('r5dc',target));rows={};left=('one',)*6;right=('two',)*6
        for a,b,c,d in product((False,True),repeat=4):
            v=base(doc);v['r5dc']=lambda *x:(a and x==(*left,'candidate')) or(b and x==(*right,'candidate'))
            v[target]=lambda bs:content((c and tuple(bs.items)==left) or(d and tuple(bs.items)==right))
            actual=run(doc,v);assert actual==[(not a or c) and(not b or d)];rows[str((a,b,c,d))]=actual[0]
        scopes[root]=rows
    doc=fixture(('r5eg',),'q[t[k r5eg[]][k zcandidate[]]].',('r5d3','r5ed','r5ef'))
    for values in product((False,True),repeat=3):
        v=base(doc)
        for n,value in zip(('r5d3','r5ed','r5ef'),values):v[n]=lambda value=value:content(value)
        assert run(doc,v)==[all(values)]
    return dict(exact_six_position_matrices=matrices,conditional_tables=tables,same_candidate_scopes=scopes,
        whole_requires_both_main_clauses_and_adoption_appraisal=True,
        boundaries=['r5ea or r5db/target for binding and conditional','r5dc/conditional for universal','r5d3/r5ed/r5ef for conjunction'])

@lru_cache(None)
def discourse_checks():
    doc=fixture(('r5eh',),'q[k r5eh[]].',extra='');author='author';ctx='context';whole=('r5eg',3);f=lambda n:(n,0)
    expected={
      'h236i':{(node,author,(c,3),ctx) for node,c in (('h26bx','r5eg'),('h26by','r5d3'),('h26bz','r5d4'),('h26b2','r5ed'),('h26b3','r5ef'))},
      'h257m':{('h26by',author,'h26bd',whole,f('r5db'),f('r5db'),ctx)},
      'h257n':{(node,author,whole,f('r5db'),f(c),ctx) for node,c in (('h26by','r5dz'),('h26b2','r5dv'),('h26b3','r5eb'))},
      'h26bw':{('h26b4',author,('r5d4',3),f('r5dw'),ctx)},
      'h257o':{('h26b5',author,whole,f('r5dv'),ctx)},
      'h26b6':{('h26bz',author,'h26by',ctx),('h26b3',author,'h26b2',ctx)},
      'ue':{(a,b,ctx) for a,b in (('h26bd','h26bx'),('h26by','h26bz'),('h26bz','h26b2'),('h26b5','h26b3'))},
    };rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','merged_nodes','missing_reason','reverse_reason','unknown'):
        v=base(doc);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else author
        for n,wanted in expected.items():v[n]=lambda *a,n=n,wanted=wanted:n!=variant and normalized(a) in wanted
        def reason(a,premises,conclusion,context):
            selected=frozenset(n for n in NODES if premises(n))
            return variant!='missing_reason' and (a,conclusion,context)==(author,'h26by' if variant=='reverse_reason' else 'h26b2',ctx) and selected in (frozenset(('h26by','h26bz')),frozenset(('h26b3',)))
        v['ud']=reason
        if variant=='wrong_context':v['h255n']=lambda:'reference'
        if variant=='merged_nodes':
            v['h26by']=lambda:'h26bx'
            for n in (*expected,'ud'):v[n]=lambda *a:True
        if variant=='unknown':
            v['h26bw']=unknown
            try:run(doc,v,(*NODES,author,'other'))
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('unknown focus')
            continue
        actual=run(doc,v,(*NODES,author,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26bo','h26bu','h26bv','h7k','h7l','h26as','h244j'):assert v[n] is unknown
    return dict(all_attributions_supplements_focus_fullness_reasons=rows,quoted_truth_not_executed=True,unknown_rejected=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=1005;clauses=[]
    for text,names,reading in (
      ('Das wäre ',['r5db','r5d2','r5d3','h257m','h257n'],'直前の同じ企てが形成された場合の仮定であり、実在の断言ではない。'),
      ('ein Verbrechen wider die menschliche Natur, ',['r5dx','r5dy','r5dz','h26bs','h26bt'],'人としての同じ本性を規範の根拠にした禁止と重大な侵害評価。刑法上の判決や実害の成功ではない。'),
      ('deren ursprüngliche Bestimmung ',['r5dx','r5d4'],'同じ人間本性に元来属する展開の使命を相対節の補足として述べる。'),
      ('gerade in diesem Fortschreiten besteht; ',['r5dw','h26br','h26bw'],'同じ啓蒙全般の進展こそが使命を成す内容であるという同定と焦点。'),
      ('und die Nachkommen sind also ',['r5ds','r5ed','ud'],'同じ先行時代後の全人々へ拒否資格を述べ、前半を根拠とする帰結として提示する。'),
      ('vollkommen dazu berechtigt, ',['r5dt','r5du','r5dv','h257o'],'同じ決議を拒否する選択に全面的な資格がある。全手段の許可や実際の拒否にはしない。'),
      ('jene Beschlüsse, ',['h26bk','r5du','r5ea'],'同じ合意により採択された非空の全決議への照応。'),
      ('als unbefugter und frevelhafter Weise genommen, ',['r5d5','r5d6','r5d7','r5ea','r5ef','h26bu','h26bv','h26b6','ud'],'同じ決議の採択が資格を欠き、人間本性を不遜に顧みず重大に侵害するあり方であるという理由を伴う補足。採択は同じ仮定の内側。'),
      ('zu verwerfen.',['r5dp','r5dq','r5dr','r5dt','r5ec'],'その決議を自分への拘束根拠として受け入れない実践的応答への資格。受容の不在や不履行だけで代用しない。')):
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=reading));cursor+=len(text)
    assert cursor==1264
    page=read('data/covenant-question-reading-v1.json')['original_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='posterity_rights_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[1005,1264],text=unit['text'][1005:1264]),selection=selection_binding(catalog(),[100]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_posterity_rights_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][1005:1264]),
        semantic_equivalence_automatically_proved=False,original_page=page|dict(visually_inspected=True),lexical_evidence=LEXICAL,
        holistic_review=[
          '原刊488頁と固定原文を前後を含めて読み、Dasが同じ形成の企て、derenが同じ人間本性、diesemが同じ啓蒙進展、jeneが同じ合意の全決議を受けることを構成までたどった。',
          '本性・本来的使命・内容同定はr5dxの各関係に分け、啓蒙進展r5crを引用して結んだ。人間本性を経験的習慣に替えず、使命の達成や全員の現在の進歩を追加しない。相対節は候補の選別条件にせず独立した補足として保持する。',
          '前半の重大な違反は同じ企てへの禁止と本性への侵害評価。後半の決議採択は同じ先行集団・合意・決議・形成基準へ結び、正当な資格の欠如と不遜な侵害評価を区別した。仮定内の採択を現実の事件として断言しない。',
          '後代は先行時代より後に生きる人々として全履歴に量化する。資格は各人・全決議への同じ拒否選択の積極的許可であり、全員の同時拒否や全手段の無制限な許可を要求しない。実行された拒否内容を構成する際も、受容の真理や実際の非受容を勝手に補わない。',
          '同じ仮定と六対象の下で前半・後半・採択評価を結び、本文全体と各節を著者へ帰属した。geradeの同定焦点、vollkommenの全面性、alsoとalsの根拠提示、補足と順序を保持する。帰属は引用内容を実行せず、理由提示を論理的妥当性の証明にしない。',
          '全語句を連続した固定原文範囲と対応させて通読した。基本関係には意味規約があり、一文専用の不透明な真偽記号で置き換えていない。これは明示した読みの下でのアシスタントの判断であり、自動同値性証明、独立査読、原著者の規範判断の真理の証明ではない。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,LEXICAL,page['path'],*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:100]==old.document['statements'] and len(new.document['statements'])==101
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,indices in (('data/covenant-question-reading-v1.json',[96,97]),('data/covenant-nullity-reading-v1.json',[98]),('data/cohort-covenant-denial-reading-v1.json',[99])):
        assert read(p)['selection']==selection_binding(new,indices)
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=100,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=864,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=226)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in [('adoption',adoption_checks),('qualification',qualification_checks),('resolutions',resolution_checks),('connection',connection_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,LEXICAL,INVENTORY,*PRIORS,read(READING)['original_page']['path'],
        'data/covenant-question-reading-v1.json','data/covenant-nullity-reading-v1.json','data/cohort-covenant-denial-reading-v1.json',
        'scripts/compose_posterity_rights_sentence.py','scripts/check_posterity_rights_sentence.py','tests/test_posterity_rights_sentence.py',
        'scripts/compose_cohort_covenant_purpose.py','scripts/check_covenant_nullity.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='posterity_rights_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[100],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
