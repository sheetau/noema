"""Check prospective scope, unspecified contents and exact paired report links."""
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
from scripts.compose_clerical_report_forecast import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,DETAILS,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_paired_church_reports import EXTRA,LOCAL,DOMAIN,SCENES,model as speech_model
from scripts.check_teaching_policy import substitute
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v174.json'
REPORT='reports/clerical-report-forecast-v1.json'
AUDIT='data/clerical-report-forecast-reading-v1.json'
DOC='docs/clerical-report-forecast-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/representative-teaching-evidence-v1.json'
PRIOR=tuple('reports/'+n+'-v1.json' for n in ('clerical-explanation','institutional-teaching-grounds','paired-church-reports'))
MORE=''.join('r z'+n+'[] a.' for n in NAMES if n not in ('person','role','church','subject'))+'r zref[] d.r zx[] a.r zy[] a.'
VALUES=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]'
ACTUAL=VALUES+' k zutterance[] r[k zchurch[]] r[k zjudgment[]] r[p zmessage] r[p zreasons] p zaudience'
FUTURES=('now','one','two')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,query=None,boundaries=(),finite=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    # Diagnostic replacement values must precede definitions after substitution.
    prefix=parse('p:'+EXTRA+LOCAL+MORE)
    doc['declarations']=prefix['declarations']+doc['declarations']
    if query is None:
        args=ACTUAL if target=='r4x' else VALUES if target=='r4z' else ''
        query='k '+target+'['+args+']'
        if target!='r42b':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    if finite:
        # Replace only the six witness quantifiers, keeping the nine binding
        # quantifiers and all production source unchanged.
        def reduce(node):
            if isinstance(node,dict):
                if node.get('kind')=='exists' and node.get('variable') in witness_names:
                    choices=witness_names[node['variable']]
                    bodies=[reduce(substitute(node['body'],node['variable'],value)) for value in choices]
                    result=bodies[-1]
                    for body in reversed(bodies[:-1]):result=dict(kind='or',arguments=[body,result])
                    return result
                return {k:reduce(v) for k,v in node.items()}
            if isinstance(node,list):return [reduce(v) for v in node]
            return node
        declaration=next(d for d in doc['declarations'] if d['name']=='r4y')
        # Normalization renames binders; identify the six consecutive nested
        # witness quantifiers by their position after the nine-individual bind.
        nodes=[]
        def find(node):
            if isinstance(node,dict):
                if node.get('kind')=='exists':nodes.append(node)
                for v in node.values():find(v)
            elif isinstance(node,list):
                for v in node:find(v)
        find(declaration['body']);assert len(nodes)==15,len(nodes)
        expressions=('k zutterance[]','r[k zchurch[]]','r[k zjudgment[]]','r[p zmessage]','r[p zreasons]','p zaudience')
        def expression(text):return parse(format_graph(prefix,'compact')+'q[e['+text+']['+text+']].')['statements'][0]['body']['arguments'][0]
        witness_names={node['variable']:[expression(text)] for node,text in zip(nodes[9:],expressions)}
        witness_names[nodes[12]['variable']].append(expression('r[p zalias]'))
        declaration['body']=reduce(declaration['body'])
        doc=parse(format_graph(doc,'compact'))
    return doc


def run(doc,v,domain=DOMAIN,scenes=SCENES):return evaluate(doc,v,domain,scenes,True)


@lru_cache(None)
def native_checks():
    doc=fixture('r4x');rows={}
    for variant in ('baseline','no_event','other_speaker','missing_second','reversed','no_our_reference','no_pointing','other_reasons','other_reference','unassigned_recipient'):
        v=speech_model(doc,variant);v.update({ 'z'+n:lambda n=n:n for n in NAMES if n not in ('person','role','church','subject')})
        v['zref']=lambda:'now'
        v['h6t']=lambda scope,p,ref:ref=='now' and (scope,p) in (('students','first'),('members','second')) and not(variant=='unassigned_recipient' and p=='second')
        v['h252a']=lambda a,p,code,ref,at:variant!='no_pointing' and (a,p,symbol(code),code.rank,ref,at)==('utterance','person',
            'zaudience' if variant=='other_reasons' else 'zreasons',0,'other' if variant=='other_reference' else 'now','now')
        domain=tuple(dict.fromkeys((*DOMAIN,*NAMES)))
        actual=run(doc,v,domain);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    for n in ('h252a','h6t'):
        v['h252a']=lambda *a:True;v['h6t']=lambda *a:True;v[n]=unknown
        try:run(doc,v,domain)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,native_ranked_pair_evaluated=True,same_pointed_range_and_fixed_audiences=True,reported_facts_unknown=True)


@lru_cache(None)
def binding_checks():
    rows=[]
    for position in range(9):
        values=tuple('y' if i==position else 'x' for i in range(9))
        query='t[k r4y[l[a]['+' '.join('k z'+x+'[]' for x in values)+'] k zref[]]][k zpoint[]]'
        doc=fixture('r4y',query,('r4x',),finite=True)
        for code in ('zmessage','zalias'):
            v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            v.update(zx=lambda:'x',zy=lambda:'y',zref=lambda:'now',zpoint=lambda:'now',zutterance=lambda:'x',zaudience=lambda p:p=='x')
            def candidate(*args):
                good=tuple(args[:9])==values and args[9]=='now' and args[10]=='x' and symbol(args[11])=='zchurch' and symbol(args[12])=='zjudgment' and symbol(args[13])==code and symbol(args[14])=='zreasons'
                assert callable(args[15])
                return Content(FUTURES,(good,)*3)
            v['r4x']=candidate
            assert run(doc,v,('x','y'),FUTURES)==[True],(position,code)
        rows.append(position)
    full=fixture('r4y',query,('r4x',))
    try:run(full,v,('x','y'),FUTURES)
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Unbounded witnesses silently restricted')
    # Shape and exact order also reject undersized/oversized binding lists.
    for length in (8,10):
        q='t[k r4y[l[a]['+' '.join('k zx[]' for _ in range(length))+'] k zref[]]][k zpoint[]]'
        d=fixture('r4y',q,('r4x',),finite=True);v['r4x']=lambda *a:Content(FUTURES,(True,)*3)
        assert run(d,v,('x',),FUTURES)==[False]
    return dict(independent_positions=rows,two_alternative_message_witnesses=True,boundaries=['r4x'],
        diagnostic_fixed_other_witnesses=True,wrong_lengths_rejected=True,full_domain_refused=refusal)


@lru_cache(None)
def forecast_checks():
    doc=fixture('r4z',boundaries=('r4y',));rows={}
    domain=(*NAMES,'author')
    for variant in ('baseline','empty','missing_second','not_future','present_only','wrong_viewpoint','wrong_goal','wrong_bindings','wrong_reference','wrong_evaluation'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update({'z'+n:lambda n=n:n for n in NAMES});v.update(zref=lambda:'now',zpoint=lambda:'now',wa=lambda:'author')
        selected=() if variant=='empty' else ('now',) if variant=='present_only' else ('one','two')
        def candidates(who,code,bindings,ref,at,point):
            return point in selected and (who,symbol(code),code.rank,tuple(bindings.items),ref,at)==(
                'person' if variant=='wrong_viewpoint' else 'author','r4x' if variant=='wrong_goal' else 'r4y',2,
                tuple(reversed(NAMES)) if variant=='wrong_bindings' else NAMES,'one' if variant=='wrong_reference' else 'now','one' if variant=='wrong_evaluation' else 'now')
        v['h247z']=candidates
        v['tx']=lambda now,c:now=='now' and c in (('one',) if variant=='not_future' else ('one','two'))
        v['r4y']=lambda bindings,ref:Content(FUTURES,tuple(tuple(bindings.items)==NAMES and ref=='now' and at in (('one',) if variant=='missing_second' else ('one','two')) for at in FUTURES))
        result=run(doc,v,domain,FUTURES);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    # Candidate content may have different inner witnesses: content remains
    # inside the candidate quantifier, not one description chosen outside it.
    for n in ('h247z','tx','r4y'):
        v[n]=unknown
        try:run(doc,v,domain,FUTURES)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        if n=='h247z':v[n]=candidates
        if n=='tx':v[n]=lambda *a:True
    integrated=fixture('r4z',boundaries=('r4x',),finite=True)
    v={d['name']:unknown for d in integrated['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda:'x' for n in NAMES})
    v.update(wa=lambda:'x',zref=lambda:'now',zpoint=lambda:'now',zutterance=lambda:'x',zaudience=lambda p:True)
    v['h247z']=lambda who,code,bindings,ref,at,candidate:(who,symbol(code),code.rank,tuple(bindings.items),ref,at)==('x','r4y',2,('x',)*9,'now','now') and candidate in ('one','two')
    v['tx']=lambda now,candidate:now=='now' and candidate in ('one','two')
    v['r4x']=lambda *args:Content(FUTURES,(False,symbol(args[13])=='zmessage',symbol(args[13])=='zalias'))
    assert run(integrated,v,('x',),FUTURES)==[True]
    return dict(contrasts=rows,nonempty_all_selected_candidates=True,actual_present_not_required=True,unknown_refused=True,
        boundary='r4y',same_nine_bindings_reference_and_goal_rank=True,
        different_inner_witnesses_across_candidates_evaluated=True,integrated_diagnostic_boundary='r4x')


@lru_cache(None)
def case_checks():
    doc=fixture('r42a',boundaries=('r35t','r4z'));rows=[]
    for position in range(9):
        selected=tuple('y' if i==position else 'x' for i in range(9))
        for holds in (False,True):
            v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            v.update(h232v=lambda:'now',zpoint=lambda:'now',r35t=lambda *args:tuple(args)==(*selected,'now'),
                r4z=lambda *args:Content(SCENES,(holds or tuple(args)!=(*selected,'now'),)*2))
            result=run(doc,v,('x','y'));assert result==[holds],(position,holds,result)
        rows.append(position)
    return dict(independent_nine_case_positions=rows,boundaries=['r35t','r4z'])


@lru_cache(None)
def discourse_checks():
    doc=fixture('r42b');domain=('author','previous','example','other');rows={}
    for variant in ('baseline','no_claim','wrong_author','wrong_content','wrong_context','no_example','reversed_example','wrong_prior','reversed_order','merged_nodes'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        v.update(wa=lambda:'author',h252b=lambda:'previous' if variant=='merged_nodes' else 'example',h247t=lambda:'previous',h232o=lambda:'now')
        v['h236i']=lambda n,a,c,ctx:variant!='no_claim' and (n,a,symbol(c),c.rank,ctx)==('example','other' if variant=='wrong_author' else 'author','r4l' if variant=='wrong_content' else 'r42a',3,'other' if variant=='wrong_context' else 'now')
        v['h252c']=lambda n,a,p,pc,e,ec,ctx:variant!='no_example' and (n,a,p,symbol(pc),pc.rank,e,symbol(ec),ec.rank,ctx)==('example','author','example' if variant=='reversed_example' else 'previous','r42a' if variant=='wrong_prior' else 'r4l',3,'example','r42a',3,'now')
        v['ue']=lambda p,e,c:variant!='reversed_order' and (p,e,c)==('previous','example','now')
        if variant=='merged_nodes':v.update(h236i=lambda *a:True,h252c=lambda *a:True,ue=lambda *a:True)
        actual=run(doc,v,domain);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,rank_three_attribution_and_example_direction=True,contents_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][3794:3898]
    parts=[('Er wird sagen: ',['r35t','h247z','tx','r4x','r4y','r4z'],'同じ職務事例の本人の発言を、将来の採用候補で見込む例示。'),
        ('unsere Kirche ',['h247y','r4w'],'引用内の話者を含む複数者の所属先として同じ教会を指示する。'),
        ('lehrt dieses oder jenes; ',['r4n','r4o','r4r','r4t','r4y'],'内容を特定せず、候補内で選んだ同じNoema発話を教会が教えると報告する。'),
        ('das sind die Beweisgründe, ',['h252a','r4p','r4q','r4s','r4u'],'指示された同じ範囲を、その教示判断に用いる論拠の完全な一覧として報告する。'),
        ('deren sie sich bedient.',['fc','h247w','r4p','r4q','h247x'],'同じ教会が同じ判断で用いる論拠であるという報告を続ける。客観的な支持とは分ける。')]
    cursor=3794;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==3898 and sum(not c.isspace() for c in text)==88
    pages=read(EVIDENCE)['pages']
    for page in pages:assert page['visually_inspected'] and digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='clerical_report_forecast_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3794,3898],text=text),selection=selection_binding(catalog(),[90]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_prospective_report_example',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=88,
        preserved_reviewed_sentence_characters=3242,paragraph_reviewed_sentence_characters=3330,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁の文と直前の教示の性格付け、後続の本人の確信・内面の宗教・辞職条件を読み、文全体と依存構成を照合した。',
            'Er・unsere Kirche・sieを同じ事例内で結び、wird sagenの見込みと候補内の実際の二報告を分けた。著者の例示の帰属から現実の発言を導いていない。',
            'dieses oder jenesは具体的教義を未指定とする例示的な不特定表現と読み、候補内の存在量化で保持した。二つの特定命題や全候補に共通する一つの教義を補っていない。',
            '両報告が同じ内側の発話、教会、主題を保持し、論拠報告に同じ判断と指示範囲を結ぶことを確認した。使用論拠と便宜上の理由・実際の支持を区別する。',
            '語句を連続して覆い、引用の段階と非事実性、宛先の範囲、説明的な順序、前文への例示関係を点検した。有限診断は構成の一部の評価と接続検査であり、同義性の自動証明ではない。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIOR,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:90]==old.document['statements'] and len(new.document['statements'])==91
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-explanation-reading-v1.json');assert prior['selection']==selection_binding(new,[89]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=90,added_statements=1,preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=88,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('native',native_checks),('bindings',binding_checks),('forecast',forecast_checks),('cases',case_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIOR,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-explanation-reading-v1.json','scripts/compose_clerical_report_forecast.py','scripts/check_clerical_report_forecast.py',
        'tests/test_clerical_report_forecast.py','scripts/check_paired_church_reports.py','scripts/check_teaching_policy.py',
        'scripts/check_institutional_teaching_grounds.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_protected_remarks.py','scripts/compose_civic_example.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='prospective_clerical_reports_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[90],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
