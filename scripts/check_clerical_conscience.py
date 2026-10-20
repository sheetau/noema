"""Check the whole conscience sentence, referent scope and unchanged judgments."""
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
from scripts.compose_clerical_conscience import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,ARRANGEMENT,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_conscientious_imputation import model as imputation_model,DOMAIN as ITEMS,TIMES as POINTS
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v172.json'
REPORT='reports/clerical-conscience-v1.json'
AUDIT='data/clerical-conscience-reading-v1.json'
DOC='docs/clerical-conscience-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/officer-example-evidence-v1.json'
IMAGE='artifacts/officer-example-v1/page-486.jpg'
LEXICAL=('data/imputation-evidence-v1.json','data/conscience-evidence-v1.json')
PRIOR=('reports/clerical-public-freedom-v1.json','reports/conscientious-imputation-v1.json')
DOMAIN=('x','y')
TIMES=('reference','evaluation')
DISCOURSE=('author','prior','sentence','other')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,query,extra='',boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    return parse(format_graph(doc,'compact')+extra+'q['+query+'].')


def base(doc):return {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}


@lru_cache(None)
def native_checks():
    extra='r zperson[] a.r zscholar[] a.r zref[] d.r zevaluation[] d.'
    bindings=('person',)*9+('other',)
    args=' '.join('k zperson[]' for _ in NAMES)+' k zscholar[] k zref[]'
    doc=fixture('r37w','t[k r37w['+args+']][k zevaluation[]]',extra)
    rows={}
    for name,kwargs,scope,expected in [
        ('warranted_imputation',{},('matter','matterb'),False),
        ('unwarranted_self_blame',dict(bits=(True,True,True,True,False,True)),('matter','matterb'),True),
        ('no_candidate',dict(bits=(True,True,True,True,True,False)),('matter','matterb'),True),
        ('second_matter',dict(matter='matterb'),('matter','matterb'),False),
        ('outside_scope',dict(matter='matterb'),('matter',),True),
        ('empty_scope',{},(),True),
    ]:
        v=base(doc);v.update(imputation_model(**kwargs));seen=[]
        def pertinent(person,matter,code,values,ref):
            seen.append((person,symbol(code),code.rank,tuple(values.items),ref))
            assert seen[-1]==('person','r37v',2,bindings,'reference')
            return matter in scope
        v.update(zscholar=lambda:'other',h247k=pertinent)
        actual=evaluate(doc,v,ITEMS,POINTS,True)
        assert actual==[expected] and seen,(name,actual);rows[name]=actual[0]
    # Vary each role/referent independently at the actual r37w -> h247k boundary.
    for position in range(10):
        selected=tuple('y' if i==position else 'x' for i in range(10))
        args=' '.join('k z'+x+'[]' for x in selected)+' k zref[]'
        direct=fixture('r37w','t[k r37w['+args+']][k zpoint[]]',
            'r zx[] a.r zy[] a.r zref[] d.r zpoint[] d.')
        v=base(direct);v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'evaluation')
        for n in ('fa','se','fb','h247h','h247i','h247j'):v[n]=lambda *a:False
        seen=[]
        def pertinent(person,matter,code,values,ref):
            seen.append(matter)
            assert (person,symbol(code),code.rank,tuple(values.items),ref)==(selected[0],'r37v',2,selected,'reference')
            return True
        v['h247k']=pertinent
        assert evaluate(direct,v,DOMAIN,TIMES,True)==[True] and set(seen)==set(DOMAIN),position
    # Unknown scope or assessment must not be converted into the negative claim.
    rejected=[]
    for n in ('h247k','fa','se','fb','h247h','h247i','h247j'):
        v=base(doc);v.update(imputation_model());v.update(zscholar=lambda:'other',h247k=lambda *args:args[1]=='matter');v[n]=unknown
        try:evaluate(doc,v,ITEMS,POINTS,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(contrasts=rows,definitions_replaced_by_primitives=False,exact_rank_two_arrangement_and_ten_bindings=True,
        independently_checked_scope_binding_positions=list(ARRANGEMENT),
        quoted_teaching_and_public_norms_not_executed=True,unknown_inputs_rejected=rejected)


@lru_cache(None)
def arrangement_checks():
    extra='r zx[] a.r zy[] a.r zref[] d.r zpoint[] d.'
    def setup(selected,bits=(True,)*4):
        query='t[k r37v[l[a]['+' '.join('k z'+v+'[]' for v in selected)+'] k zref[]]][k zpoint[]]'
        doc=fixture('r37v',query,extra,('r35t','r36h','r37l'))
        v=base(doc);v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'reference',zpoint=lambda:'evaluation')
        nine=selected[:9];person,role,church,congregation,students,members,creed,subject,standard=nine
        scholar=selected[9]
        v.update(r35t=lambda *a:bits[0] and a==(*nine,'reference'),cd=lambda *a:bits[1] and a==(scholar,'reference'),
            r36h=lambda *a:Content(TIMES,(False,bits[2] and a==(*nine,'reference'))),
            r37l=lambda *a:Content(TIMES,(False,bits[3] and a==(person,scholar,church,creed,subject,'reference'))))
        return doc,v
    positions=[]
    for position in range(10):
        selected=tuple('y' if i==position else 'x' for i in range(10))
        doc,v=setup(selected);assert evaluate(doc,v,DOMAIN,TIMES,True)==[True],position;positions.append(ARRANGEMENT[position])
    table=[]
    for bits in product((False,True),repeat=4):
        doc,v=setup(('x',)*10,bits);actual=evaluate(doc,v,('x',),TIMES,True)
        assert actual==[all(bits)],(bits,actual);table.append(dict(inputs=bits,result=actual[0]))
    for count in (0,9,11):
        doc,v=setup(('x',)*10)
        query='t[k r37v[l[a]['+' '.join('k zx[]' for _ in range(count))+'] k zref[]]][k zpoint[]]'
        doc=fixture('r37v',query,extra,('r35t','r36h','r37l'))
        assert evaluate(doc,v,('x',),TIMES,True)==[False],count
    return dict(independent_binding_positions=positions,truth_table=table,wrong_lengths_rejected=[0,9,11],
        boundaries=['r35t','r36h','r37l'],boundary_evidence=list(PRIOR),
        same_clerical_case_teaching_and_public_arrangement=True)


@lru_cache(None)
def scope_checks():
    doc=fixture('r37x','t[k r37x[]][k zpoint[]]','r zpoint[] d.',('r35t','r37w'))
    rows={}
    for position in range(9):
        selected=tuple('y' if i==position else 'x' for i in range(9))
        for fail in (False,True):
            seen=set();forwarded=set();v=base(doc)
            def case(*args):seen.add(args);return args==(*selected,'reference')
            def content(*args):
                forwarded.add(args)
                return Content(TIMES,(True,not fail or args!=(*selected,selected[0],'reference')))
            v.update(h232v=lambda:'reference',zpoint=lambda:'evaluation',r35t=case,
                h247d=lambda p,r:p,cd=lambda *args:True,r37w=content)
            actual=evaluate(doc,v,DOMAIN,TIMES,True)
            assert actual==[not fail] and (*selected,selected[0],'reference') in forwarded
            assert seen=={(*xs,'reference') for xs in product(DOMAIN,repeat=9)}
            rows[NAMES[position]+('_fail' if fail else '_pass')]=actual[0]
    v=base(doc);v.update(h232v=lambda:'reference',zpoint=lambda:'evaluation',r35t=lambda *args:False,
        h247d=lambda p,r:p,cd=lambda *args:False,r37w=lambda *args:Content(TIMES,(False,False)))
    assert evaluate(doc,v,DOMAIN,TIMES,True)==[True]
    v['r35t']=lambda *a:a==('x',)*9+('reference',);v['r37w']=lambda *a:Content(TIMES,(True,True))
    assert evaluate(doc,v,DOMAIN,TIMES,True)==[False]
    return dict(contrasts=rows,empty_case_does_not_assert_existence=True,scholarly_role_required=True,
        all_nine_case_fields_and_same_person_bound_scholar=True,
        boundaries=['r35t','r37w'],r37w_evaluated_natively_in_native_checks=True)


def discourse_model(doc,variant='baseline'):
    v=base(doc);v.update(h247m=lambda:'sentence',h247e=lambda:'prior',wa=lambda:'author',h232o=lambda:'reference')
    def claim(node,author,code,ctx):
        return variant!='no_claim' and (node,author,symbol(code),code.rank,ctx)==('sentence',
            'other' if variant=='wrong_author' else 'author','r37o' if variant=='wrong_content' else 'r37x',3,
            'evaluation' if variant=='wrong_context' else 'reference')
    def addition(node,author,prior,left,current,right,ctx):
        expected=['sentence','author','prior','r37o',3,'sentence','r37x',3,'reference']
        fields=('node','presenter','prior_node','prior_content','prior_rank','added_node','added_content','added_rank','context')
        for i,f in enumerate(fields):
            if variant=='addition_'+f:expected[i]='other'
        return variant!='no_addition' and (node,author,prior,symbol(left),left.rank,current,symbol(right),right.rank,ctx)==tuple(expected)
    v.update(h236i=claim,h247l=addition,ue=lambda a,b,c:variant!='reversed_order' and (a,b,c)==('prior','sentence','reference'))
    return v


@lru_cache(None)
def discourse_checks():
    doc=fixture('r37y','k r37y[]');rows={}
    variants=('baseline','no_claim','wrong_author','wrong_content','wrong_context','no_addition','reversed_order',
        *('addition_'+s for s in ('node','presenter','prior_node','prior_content','prior_rank','added_node','added_content','added_rank','context')))
    for variant in variants:
        actual=evaluate(doc,discourse_model(doc,variant),DISCOURSE,TIMES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    v=discourse_model(doc);v.update(h247m=lambda:'prior',h236i=lambda *a:True,h247l=lambda *a:True,ue=lambda *a:True)
    assert evaluate(doc,v,DISCOURSE,TIMES,True)==[False]
    for n in ('h236i','h247l','ue'):
        v=discourse_model(doc);v[n]=unknown
        try:evaluate(doc,v,DISCOURSE,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,distinct_nodes=True,quoted_world_and_arrangement_not_executed=True,
        same_presenter_context_and_ordered_addition=True,unknown_inputs_rejected=['h236i','h247l','ue'])


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('Es ist ',['r37x','h236i','r37y'],'虚辞Esを別の指示対象にせず、後続の範囲内の非存在を著者の主張内容とする。'),
        ('hiebei ',['r35t','r36h','r37l','r37v','h247k','r37w'],'同じ聖職者の職務教示と学識者としての公的伝達、それらの併存を固定した構成で参照する。'),
        ('auch ',['h247l','r37y'],'直前の自由・使命の提示を受けてこの否定も加える。尺度的強化や撤回とはしない。'),
        ('nichts, ',['r37u','r37w','r37x'],'この構成に関する全事柄について帰責可能性を否定し、既に無害と判断したものだけへ絞らない。'),
        ('was dem Gewissen ',['fa','se','fb','r37r'],'関係節の同じ事柄を同じ本人の道徳的自己判断の対象とする。良心を機能上の自己評価として読む。'),
        ('zur Last gelegt werden ',['h247h','h247i','r37s'],'同じ事柄を本人の落ち度として帰すること。根拠をもって帰責できるという採用解釈を可能性の内側に置く。'),
        ('könnte.',['h247j','r37t','r37u'],'同じ事柄を保持する候補のいずれかで正当な自己帰責が成立する可能性を、nichtsの作用域で否定する。'),
    ]
    cursor,clauses=3453,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==3527
    text=unit['text'][3453:3527];count=sum(not c.isspace() for c in text);assert count==62
    page=next(p for p in read(EVIDENCE)['pages'] if p['page']==486)
    assert digest((ROOT/IMAGE).read_bytes())==page['sha256']
    return dict(status='clerical_conscience_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[3453,3527],text=text),selection=selection_binding(catalog(),[88]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_scoped_conscientious_non_imputability',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,
        preserved_reviewed_sentence_characters=2958,paragraph_reviewed_sentence_characters=3020,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁で職務教示と任用、公的伝達の自由と使命、本一文、続くDennの開始を目視通読した。関係節を含む連続した全範囲を上記の語句対応で覆う。',
            'hiebeiの範囲を先行と同じ人・職務・教会・会衆・生徒・成員・信条・主題・基準と本人の学識者の立場へ結ぶ。二立場の併存への評価も含む構成範囲であり、単独活動の集合だけにはしない。',
            'r37vは先行するr35t、cd、r36h、r37lを十個体列で合成する。h247kへ渡す段階2の記述と束縛列・基準を追い、原語名だけを内容として代用していないことを確認した。',
            'nichtsは対象範囲の全件に及び、その内側で候補と判断を存在量化する。現に帰責したものの不存在や全候補での帰責不成立という一部条件へ縮めず、一つの対象・候補・正当な判断でもあれば否定が不成立となる。',
            '良心を本人の道徳的自己判断として読む。実際の罪悪感や誤った自責の可能性を扱う文には変えない。帰責内容・正当化・候補範囲の明示した意味規約は維持し、その哲学的一般理論の完成を主張しない。',
            'auchは自由・使命に続く追加提示として接続する。前の内容を撤回せず、帰責の不存在を自由からの論理的帰結にはしない。帰属・追加・本文順序の評価では引用した構成も否定内容も実行しない。'],
        original_page=page,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,IMAGE,*LEXICAL,*PRIOR)})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['statements'][:88]==old.document['statements'] and len(new.document['statements'])==89
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-public-freedom-reading-v1.json')
    assert prior['selection']==selection_binding(new,[87]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=88,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=62,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('native',native_checks),('arrangement',arrangement_checks),('scope',scope_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,IMAGE,*LEXICAL,*PRIOR,
        'data/clerical-public-freedom-reading-v1.json','scripts/compose_clerical_conscience.py','scripts/check_clerical_conscience.py',
        'tests/test_clerical_conscience.py','scripts/check_conscientious_imputation.py','scripts/compose_civic_example.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_protected_remarks.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='clerical_scoped_conscientious_non_imputability',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[88],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
