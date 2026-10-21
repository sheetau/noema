"""Check whole-sentence generalization, scoped reasons and preserved judgments."""
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
from scripts.compose_clerical_private_conclusion import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_teaching_policy import substitute

INDEX='data/semantic-review-index-v177.json'
REPORT='reports/clerical-private-conclusion-v1.json'
AUDIT='data/clerical-private-conclusion-reading-v1.json'
DOC='docs/clerical-private-conclusion-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/congregational-private-use-evidence-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('clerical-resignation-condition','congregational-private-use','delegated-teaching-freedom'))
SCENES=('reference','actual','other')
DOMAIN=(*NAMES,'occasion','activity','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
EXTRA+='r zmeaning[a] e.d zmessage[subject a] f[j s[k zmeaning[v subject]]].d zalias[subject a] f[k zmessage[v subject]].'
ARGS=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[] k zoccasion[] k zactivity[] r[p zmessage]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,boundaries=(),finite=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    prefix=parse('p:'+EXTRA);doc['declarations']=prefix['declarations']+doc['declarations']
    query='k '+target+'['+('' if target in ('r44q','r44r') else ARGS)+']'
    if target!='r44r':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    if finite:
        declaration=next(d for d in doc['declarations'] if d['name']=='r44q');variables=[]
        body=declaration['body']['body']
        while body['kind']=='forall':variables.append(body);body=body['body']
        assert len(variables)==12
        def expr(t):return parse(format_graph(prefix,'compact')+'q[e['+t+']['+t+']].')['statements'][0]['body']['arguments'][0]
        assignments={n['variable']:expr('k z'+name+'[]') for n,name in zip(variables[:9],NAMES)}
        message=variables[-1]['variable'];choices=[expr('r[p '+n+']') for n in ('zmessage','zalias')]
        def reduce(node):
            if isinstance(node,dict):
                if node.get('kind')=='forall':
                    var=node['variable']
                    if var in assignments:return reduce(substitute(node['body'],var,assignments[var]))
                    if var==message:return dict(kind='and',arguments=[reduce(substitute(node['body'],var,c)) for c in choices])
                return {k:reduce(v) for k,v in node.items()}
            if isinstance(node,list):return [reduce(v) for v in node]
            return node
        declaration['body']=reduce(declaration['body']);doc=parse(format_graph(doc,'compact'))
    return doc


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN})
    v.update(zref=lambda:'reference',zpoint=lambda:'actual',h232v=lambda:'reference')
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


@lru_cache(None)
def connection_checks():
    rows={};wanted=('church','person','role','subject','zmessage','reference')
    for target,lower in (('r44m','r44e'),('r44n','r44i'),('r44o','r44j')):
        doc=fixture(target,(lower,));expected=('congregation','church','subject','reference','actual') if target=='r44m' else wanted
        for i in range(len(expected)+1):
            v=base(doc);want=list(expected)
            if i<len(expected):want[i]='other'
            if target=='r44m':v[lower]=lambda *a,want=tuple(want):a==want
            else:
                def content(*a,want=tuple(want)):
                    actual=(*a[:4],symbol(a[4]),a[5])
                    return Content(SCENES,tuple(actual==want and p=='actual' for p in SCENES))
                v[lower]=content
            result=run(doc,v);assert result==[i==len(expected)],(target,i,result);rows[target+':'+str(i)]=result[0]
    doc=fixture('r44p',('r44n','r44o'));table=[]
    for bits in product((False,True),repeat=2):
        v=base(doc)
        for name,bit in zip(('r44n','r44o'),bits):v[name]=lambda *a,bit=bit:Content(SCENES,tuple(bit and p=='actual' for p in SCENES))
        result=run(doc,v);assert result==[all(bits)];table.append([*bits,result[0]])
    return dict(wrapper_arguments=rows,actual_and_normative_pair_table=table,boundaries=['r44e','r44i','r44j','r44n','r44o'])


@lru_cache(None)
def generalization_checks():
    doc=fixture('r44q',('r44a','r44l'),True);rows={}
    selected={('occasion','activity','zmessage'),('other','activity','zalias')}
    for variant in ('baseline','missing_first','missing_second','wrong_reference','wrong_person','no_use','extra_use_fails'):
        v=base(doc)
        def content(*args,target):
            fixed=(*NAMES,'reference');actual=(*args[:10],args[10],args[11],symbol(args[12]))
            triples=set(selected)
            if variant=='extra_use_fails' and target=='r44a':triples.add(('occasion','other','zalias'))
            if variant=='no_use' and target=='r44a':triples=set()
            if target=='r44l':
                if variant=='missing_first':triples.discard(('occasion','activity','zmessage'))
                if variant=='missing_second':triples.discard(('other','activity','zalias'))
                if variant=='wrong_reference':fixed=(*NAMES,'other')
                if variant=='wrong_person':fixed=('other',*NAMES[1:],'reference')
            truth=actual[:10]==fixed and actual[10:] in triples
            return Content(SCENES,tuple(truth and p=='actual' for p in SCENES))
        v['r44a']=lambda *a:content(*a,target='r44a')
        v['r44l']=lambda *a:content(*a,target='r44l')
        result=run(doc,v);assert result==[variant in ('baseline','no_use')],(variant,result);rows[variant]=result[0]
    full=fixture('r44q',('r44a','r44l'));v=base(full)
    v.update(r44a=lambda *a:Content(SCENES,(False,)*3),r44l=lambda *a:Content(SCENES,(True,)*3))
    try:run(full,v,('other',))
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Full utterance domain silently restricted')
    return dict(contrasts=rows,native_occasion_activity_universals=True,diagnostic_case_instantiated=True,
        diagnostic_utterance_choices=2,all_uses_including_additional_utterance_required=True,no_actual_instance_asserted=True,
        full_domain_refused=refusal,boundaries=['r44a','r44l'])


@lru_cache(None)
def discourse_checks():
    doc=fixture('r44r');rows={};nodes=('sentence','prior','definition','teaching','context','author','other')
    for variant in ('baseline','wrong_author','wrong_whole','wrong_context','first_reason_reversed','second_reason_reversed',
        'second_reason_omits_norm','wrong_respect','addition_reversed','wrong_concession','wrong_grounds','wrong_conclusion','reversed_order','merged_nodes'):
        v=base(doc);v.update(h253g=lambda:'prior' if variant=='merged_nodes' else 'sentence',h2526=lambda:'prior',
            h236s=lambda:'definition',h247t=lambda:'teaching',h2527=lambda:'context',wa=lambda:'author',h232o=lambda:'reference')
        def outer(n,w,c,ctx):return (n,w,symbol(c),c.rank,ctx)==('sentence','other' if variant=='wrong_author' else 'author',
            'r436' if variant=='wrong_whole' else 'r44q',3,'other' if variant=='wrong_context' else 'reference')
        v['h236i']=outer
        def pair(n,w,c,a,b,ctx,allowed):return outer(n,w,c,ctx) and a.rank==b.rank==2 and (symbol(a),symbol(b)) in allowed
        reasons=[('r44m','r44b'),('r44c','r44p')]
        if variant=='first_reason_reversed':reasons[0]=tuple(reversed(reasons[0]))
        if variant=='second_reason_reversed':reasons[1]=tuple(reversed(reasons[1]))
        if variant=='second_reason_omits_norm':reasons[1]=('r44c','r44n')
        v['h253h']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,reasons)
        v['h253i']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,[('r44m','r44p') if variant=='wrong_respect' else ('r44b','r44p')])
        v['h253j']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,[('r44o','r44n') if variant=='addition_reversed' else ('r44n','r44o')])
        v['h253k']=lambda n,w,c,a,ctx:outer(n,w,c,ctx) and (symbol(a),a.rank)==('r44b' if variant=='wrong_concession' else 'r44m',2)
        def explanation(w,grounds,conclusion,ctx):
            actual={n for n in nodes if grounds(n)}
            expected={'prior'} if variant=='wrong_grounds' else {'definition','teaching','context'}
            return actual==expected and (w,conclusion,ctx)==('author','prior' if variant=='wrong_conclusion' else 'sentence','reference')
        v['ud']=explanation
        v['ue']=lambda a,b,ctx:(a,b,ctx)==(('sentence','prior','reference') if variant=='reversed_order' else ('prior','sentence','reference'))
        if variant=='merged_nodes':
            for n in ('h236i','h253h','h253i','h253j','h253k','ud','ue'):v[n]=lambda *a:True
        result=run(doc,v,nodes);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    return dict(contrasts=rows,two_distinct_reasons_and_targets=True,normative_negation_is_additional=True,
        same_private_capacity_limits_claim=True,scale_concession_preserved=True,also_grounds_and_order=True,contents_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][4408:4734]
    parts=[
        ('Der Gebrauch also, ',['r44q','ud'],'同じ私的使用の定義と先行の代表教示の説明を受けた結論として提示する。'),
        ('den ein angestellter Lehrer von seiner Vernunft vor seiner Gemeinde macht, ',['r372','r44a'],'同じ任用された聖職者が、その会衆の前で実際に教示し理性を使う全該当事例。'),
        ('ist bloß ein Privatgebrauch; ',['r44b','r2zj','r2zi'],'同じ使用の職務の立場では私的分類を満たし、公的分類を満たさない。'),
        ('weil diese immer nur eine häusliche, ',['r44d','r44e','r44m','h253h'],'理由として、同じ会衆が当該集会としての全関連機会に組織内の範囲を保つことを示す。'),
        ('obzwar noch so große, ',['h253e','r44e','h253k'],'規模がいかに大きくても家内的性格を保つという譲歩。現実の巨大集会の存在は補わない。'),
        ('Versammlung ist; ',['h253c','h253d','r44d'],'家の共同の用事になぞらえた内部的な人々の集まりとしての会衆。'),
        ('und in Ansehung dessen ist er, als Priester, nicht frei, ',['r44n','r4e','h253i'],'同じ本人が同じ職務上の使用について、当該教示内容を独立に決定する自由な権限を現に持たない。'),
        ('und darf es auch nicht sein, ',['r44o','r44h','r44j','h237z','h253j'],'それに加え、同じ自由内容を同じ委託職務の責任規範が認めない負の要求。'),
        ('weil er einen fremden Auftrag ausrichtet.',['r37z','r44c','h253b','h253h'],'同じ本人が自分とは異なる同じ教会の委託業務を同じ活動で遂行することを、非自由と負の要求の理由として示す。')]
    cursor=4408;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t,(cursor,t)
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==4734 and sum(not c.isspace() for c in text)==275
    pages=read(EVIDENCE)['pages']
    for p in pages:assert p['visually_inspected'] and digest((ROOT/p['path']).read_bytes())==p['sha256']
    return dict(status='clerical_private_conclusion_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[4408,4734],text=text),selection=selection_binding(catalog(),[93]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_clerical_private_conclusion',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=275,
        preserved_reviewed_sentence_characters=3762,paragraph_reviewed_sentence_characters=4037,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁の対象文全文と前後を通読し、Lehrerを同じ任用された聖職者、dieseを会衆、esを同じ自由の状態、fremden Auftragを同じ教会の委託業務へ結んだ。後続の学識者としての別の立場の自由を否定していない。',
            '全該当事例・担当機会・活動・発話を量化し、実際に同じ会衆へ教示する理性使用を対象とした。規範的否定のある例だけや一つの成功例へ対象を絞らず、全発話記述域の有限評価を拒否する。',
            '家内的な集会という比喩的な性格を、家屋・血縁・小人数の断定へ変えていない。全関連機会と規模の候補でその性格が保たれること、規模への譲歩、読者世界との対照を保持した。',
            '現実の非自由と同じ自由内容への負の要求を区別し、auchを後者の追加とした。規範源・本人・職務・発話・主題・基準をそろえ、引用内容を要求時に実行していない。教示行為自体を禁止する内容にもしていない。',
            '第一のweilを家内的性格から私的分類へ、第二のweilを委託遂行から非自由と負の要求へ接続した。in Ansehung dessenを同じ私的使用の立場への限定とし、alsoを先行説明からの結論の提示とした。提示した理由を客観的な論理的証明や因果へ強めていない。',
            '連続する全語句・句読点の作用範囲・本文順序を確認し、旧93主張と14全単位判断を保持する。今回の275文字を文単位で加えるが、第五段落全体と二作品の完了は主張しない。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:93]==old.document['statements'] and len(new.document['statements'])==94
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in dependency().entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-resignation-condition-reading-v1.json');assert prior['selection']==selection_binding(new,[92]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=93,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        new_reviewed_sentence_characters=275,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('connections',connection_checks),('generalization',generalization_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-resignation-condition-reading-v1.json','scripts/compose_clerical_private_conclusion.py','scripts/check_clerical_private_conclusion.py',
        'tests/test_clerical_private_conclusion.py','scripts/check_teaching_policy.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_representative_teaching.py','scripts/compose_confessional_teaching.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='clerical_private_use_conclusion_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[93],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
