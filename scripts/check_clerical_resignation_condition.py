"""Check shared cross-sentence witnesses and scoped explanatory attribution."""
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
from scripts.compose_clerical_resignation_condition import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,CASE_NAMES,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_teaching_policy import substitute

INDEX='data/semantic-review-index-v176.json'
REPORT='reports/clerical-resignation-condition-v1.json'
AUDIT='data/clerical-resignation-condition-reading-v1.json'
DOC='docs/clerical-resignation-condition-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/representative-teaching-evidence-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('clerical-practical-benefit','perceived-doctrinal-conflict','conscientious-service-exit'))
SCENES=('reference','actual','other')
DOMAIN=(*CASE_NAMES,'other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
EXTRA+='r zpersonalias[] a.r zbundlealias[] a.r zreligionalias[] a.r zrefalias[] d.r zcriterion[] a.'
ARGS=' '.join('k z'+('criterion' if n=='religion' else n)+'[]' for n in CASE_NAMES)+' r[k zperson[]] r[k zbundle[]] r[k zref[]] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def finite_witnesses(doc):
    """Diagnostic restriction; production keeps the full typed domains."""
    prefix=parse('p:'+EXTRA)
    def expr(text):return parse(format_graph(prefix,'compact')+'q[e['+text+']['+text+']].')['statements'][0]['body']['arguments'][0]
    for declaration in doc['declarations']:
        if declaration['name'] not in ('r434','r436') or declaration['kind']!='definition':continue
        universals=[];existentials=[]
        def find(node):
            if isinstance(node,dict):
                if node.get('kind')=='forall':universals.append(node)
                if node.get('kind')=='exists':existentials.append(node)
                for v in node.values():find(v)
            elif isinstance(node,list):
                for v in node:find(v)
        find(declaration['body'])
        if declaration['name']=='r436':
            assert len(universals)==9 and len(existentials)==5
            assignments={n['variable']:expr('k z'+name+'[]') for n,name in zip(universals,NAMES)}
            choices={n['variable']:[expr(t) for t in texts] for n,texts in zip(existentials[2:],(
                ('r[k zperson[]]','r[k zpersonalias[]]'),('r[k zbundle[]]','r[k zbundlealias[]]'),('r[k zref[]]','r[k zrefalias[]]')))}
        else:
            assert not universals and len(existentials)==1
            assignments={};choices={existentials[0]['variable']:[expr('r[k '+n+'[]]') for n in ('zreligion','zreligionalias')]}
        def reduce(node):
            if isinstance(node,dict):
                name=node.get('variable')
                if node.get('kind')=='forall' and name in assignments:return reduce(substitute(node['body'],name,assignments[name]))
                if node.get('kind')=='exists' and name in choices:return dict(kind='or',arguments=[reduce(substitute(node['body'],name,v)) for v in choices[name]])
                return {k:reduce(v) for k,v in node.items()}
            if isinstance(node,list):return [reduce(v) for v in node]
            return node
        declaration['body']=reduce(declaration['body'])
    return parse(format_graph(doc,'compact'))


@lru_cache(None)
def fixture(target,boundaries=(),finite=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    doc['declarations']=parse('p:'+EXTRA)['declarations']+doc['declarations']
    query='k '+target+'['+('' if target in ('r436','r437') else ARGS)+']'
    if target!='r437':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    return finite_witnesses(doc) if finite else doc


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN})
    v.update(zref=lambda:'reference',zpoint=lambda:'actual',h232v=lambda:'reference',
        zpersonalias=lambda:'person',zbundlealias=lambda:'bundle',zreligionalias=lambda:'religion',zrefalias=lambda:'reference',zcriterion=lambda:'religion')
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


@lru_cache(None)
def connection_checks():
    doc=fixture('r434',('r433',),True);rows={}
    expected=('person','role','bundle','religion','reference','zperson','zbundle','zreligion','zref','actual')
    for position in range(len(expected)):
        for mismatch in (False,True):
            v=base(doc);wanted=list(expected)
            if mismatch:wanted[position]='other'
            v['r433']=lambda *args,wanted=tuple(wanted):(*args[:5],*(symbol(c) for c in args[5:9]),args[9])==wanted
            result=run(doc,v);assert result==[not mismatch],(position,mismatch,result)
            rows[str(position)+'_mismatch' if mismatch else str(position)+'_baseline']=result[0]
    v=base(doc);v['r433']=lambda *a:symbol(a[7])=='zreligionalias'
    assert run(doc,v)==[True]
    for name in ('zreligion','zreligionalias'):v[name]=lambda:'other'
    assert run(doc,v)==[False] # Even a permissive lower boundary cannot bypass the name identity.
    v=base(doc);v['r433']=unknown
    try:run(doc,v)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown conditional accepted')
    doc=fixture('r435',('r43i','r434'));table=[]
    expected15=(*CASE_NAMES,'zperson','zbundle','zref','reference')
    def install(v,bits=(True,True),mismatch=None):
        for name,bit in zip(('r43i','r434'),bits):
            wanted=list(expected15)
            if mismatch and mismatch[0]==name:wanted[mismatch[1]]='other'
            def content(*args,wanted=tuple(wanted),bit=bit):
                actual=(*args[:11],*(symbol(c) for c in args[11:14]),args[14])
                return Content(SCENES,tuple(bit and actual==wanted and p=='actual' for p in SCENES))
            v[name]=content
    for bits in product((False,True),repeat=2):
        v=base(doc);install(v,bits);result=run(doc,v);assert result==[all(bits)];table.append([*bits,result[0]])
    for name in ('r43i','r434'):
        for i in range(15):
            v=base(doc);install(v,mismatch=(name,i));assert run(doc,v)==[False],(name,i)
    return dict(conditional_argument_contrasts=rows,criterion_alias_allowed=True,criterion_name_identity_required=True,
        joint_truth_table=table,all_fifteen_arguments_shared=True,boundaries=['r433','r43i','r434'],unknown_refused=True)


@lru_cache(None)
def witness_checks():
    # r434 itself is checked above; here both content boundaries deliberately
    # accept either religion so that shared quantification alone must reject a split.
    doc=fixture('r436',('r35t','r43i','r434'),True);rows={}
    for variant in ('baseline','split_bundle','split_religion','alternate_names','missing_prior','missing_conditional','no_frame'):
        v=base(doc);v['r35t']=lambda *a:variant!='no_frame' and tuple(a)==(*NAMES,'reference')
        names=('zpersonalias','zbundlealias','zrefalias') if variant=='alternate_names' else ('zperson','zbundle','zref')
        for target in ('r43i','r434'):
            bundle='other' if variant=='split_bundle' and target=='r434' else 'bundle'
            religion='other' if variant=='split_religion' and target=='r434' else 'religion'
            expected=(*NAMES,bundle,religion,*names,'reference')
            missing=(variant,target) in (('missing_prior','r43i'),('missing_conditional','r434'))
            def content(*a,expected=expected,missing=missing):
                actual=(*a[:11],*(symbol(c) for c in a[11:14]),a[14])
                return Content(SCENES,tuple(not missing and actual==expected and p=='actual' for p in SCENES))
            v[target]=content
        result=run(doc,v);assert result==[variant in ('baseline','alternate_names','no_frame')],(variant,result)
        rows[variant]=result[0]
    full=fixture('r436',('r35t','r43i','r434'));v=base(full)
    v.update(r35t=lambda *a:True,r43i=lambda *a:Content(SCENES,(True,)*3),r434=lambda *a:Content(SCENES,(True,)*3))
    try:run(full,v,('other',))
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Unbounded description domain silently restricted')
    return dict(contrasts=rows,both_sentences_share_bundle_and_religion=True,native_individual_existentials=True,
        diagnostic_outer_case_instantiated=True,diagnostic_name_choices=2,boundaries=['r35t','r43i','r434'],full_domain_refused=refusal)


@lru_cache(None)
def discourse_checks():
    doc=fixture('r437');rows={};nodes=('author','prior','sentence','passage','other')
    variants=('baseline','wrong_author','wrong_context','wrong_whole','wrong_passage','swapped_components','wrong_family',
        'missing_prior_component','missing_current_component','reversed_reason','extra_grounds','reversed_order',
        'wrong_concession','wrong_prior_reason','wrong_contrast','wrong_minimum','missing_first_emphasis','missing_second_emphasis',
        'merge_sentences','merge_prior_passage','merge_current_passage')
    for variant in variants:
        v=base(doc);v.update(wa=lambda:'author',h252s=lambda:'prior',h2526=lambda:'sentence',h2527=lambda:'passage',h232o=lambda:'reference')
        def common(w,c,ctx):return (w,symbol(c),c.rank,ctx)==('other' if variant=='wrong_author' else 'author',
            'r43j' if variant=='wrong_whole' else 'r436',3,'other' if variant=='wrong_context' else 'reference')
        v['h236i']=lambda n,w,c,ctx:n==('prior' if variant=='wrong_passage' else 'passage') and common(w,c,ctx)
        def component(n,w,c,part,ctx):
            expected={'prior':'r434','sentence':'r43i'} if variant=='swapped_components' else {'prior':'r43i','sentence':'r434'}
            if variant=='wrong_family':expected['sentence']='r43g'
            return common(w,c,ctx) and part.rank==2 and symbol(part)==expected.get(n) and not (
                (variant,n) in (('missing_prior_component','prior'),('missing_current_component','sentence')))
        v['h253a']=component
        def pair(n,w,c,a,b,ctx,expected):return n=='prior' and common(w,c,ctx) and (symbol(a),symbol(b),a.rank,b.rank)==(*expected,2,2)
        v['h252t']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,('r43e','r43d') if variant=='wrong_concession' else ('r43d','r43e'))
        v['h252u']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,('r43e','r43h') if variant=='wrong_prior_reason' else ('r43h','r43e'))
        v['h252v']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,('r43g','r43f') if variant=='wrong_contrast' else ('r43f','r43g'))
        v['h252w']=lambda n,w,c,a,ctx:n=='prior' and common(w,c,ctx) and (symbol(a),a.rank)==('r43f' if variant=='wrong_minimum' else 'r43g',2)
        v['h252x']=lambda n,w,c,a,ctx:n=='prior' and common(w,c,ctx) and a.rank==2 and symbol(a) in (
            ('r43g',) if variant=='missing_first_emphasis' else ('r43f',) if variant=='missing_second_emphasis' else ('r43f','r43g'))
        def explanation(w,grounds,conclusion,ctx):
            selected=tuple(n for n in nodes if grounds(n))
            expected=(('prior',),'sentence') if variant=='reversed_reason' else (('sentence','other'),'prior') if variant=='extra_grounds' else (('sentence',),'prior')
            return (w,selected,conclusion,ctx)==('author',*expected,'reference')
        v['ud']=explanation
        v['ue']=lambda a,b,ctx:(a,b,ctx)==(('sentence','prior','reference') if variant=='reversed_order' else ('prior','sentence','reference'))
        if variant.startswith('merge_'):
            if variant=='merge_sentences':v['h2526']=lambda:'prior'
            elif variant=='merge_prior_passage':v['h2527']=lambda:'prior'
            else:v['h2527']=lambda:'sentence'
            for name in ('h236i','h253a','h252t','h252u','h252v','h252w','h252x','ud','ue'):v[name]=lambda *a:True
        result=run(doc,v,nodes);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    return dict(contrasts=rows,shared_scope_component_attribution=True,prior_discourse_rebound_to_same_whole=True,
        rank_three_whole_rank_two_components=True,conditional_explains_prior_sentence=True,quoted_content_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][4279:4407]
    parts=[
        ('Denn ',['ud','r437'],'後続の条件文全体を先行文の説明として提示する。現実の無抵触を証明する含意とはしない。'),
        ('glaubte er das letztere darin zu finden, ',['r43n','r43p','r43q','r43r','r434'],'同じ本人が、同じ規定群に同じ内面的宗教基準に反するものを自分で見いだすと信じる場合。信念の内容を現実に実行しない。'),
        ('so würde er sein Amt mit Gewissen nicht verwalten können; ',['r43s','r43t','r43u','r43w','r432','r433'],'その仮定の各候補で、同じ本人が同じ職務を良心上許容される仕方で務めることは実践上可能でない。'),
        ('er müßte es niederlegen.',['r43x','r43y','r43z','r432','r433'],'同じ仮定の帰結として、同じ本人が同じ職務を自分の行為で手放すことを良心上の基準が要求する。実際の退任とは分ける。')]
    cursor=4279;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t,(cursor,t)
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==4407 and sum(not c.isspace() for c in text)==107
    pages=read(EVIDENCE)['pages']
    for page in pages:assert page['visually_inspected'] and digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='clerical_resignation_condition_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[4279,4407],text=text),selection=selection_binding(catalog(),[92]),
        shared_context=dict(range=[3899,4407],previous_sentence=[3899,4278],prior_characters_not_recounted=325),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_clerical_resignation_condition',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=107,
        preserved_reviewed_sentence_characters=3655,paragraph_reviewed_sentence_characters=3762,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁で先行の実益・無抵触の留保、条件文全文、後続の私的使用の結論を照合した。Dennを前文への説明提示として、セミコロン後も同じ仮定の帰結として読んだ。',
            'das letztereを内面的宗教に反するもの、darinを先行の規定群、二つのerを同じ本人、sein Amtとesを同じ職務へ対応させた。前文と条件文を共通の量化内へ置き、規定群・宗教基準・呼称を別々に選び直さない。',
            '本人の見いだすことを内容とする信念と、その内容の真理を分けた。前文の全検討場合の無抵触は、本人が抵触を見いだすと信じる仮定を排除しない。仮定の選択と真理検討・実践可能性の各範囲を混同していない。',
            '良心に適う遂行がどれか一つ可能なら不能ではないこと、遂行と許容の同一活動、辞職要求と将来の自己による職務保持終結を点検した。良心上の規範源を明示し、不能だけから義務を導かず、原文の両帰結を連言した。',
            '連続二文の著者帰属と各文章箇所への部分内容の帰属を同じ範囲で結んだ。前文の譲歩・理由・対照・最低限・強調も同じ全体の下に保持し、Dennを論理的証明へ変えていない。',
            '連続した全語句と句読点の作用範囲を対応させた。旧92主張を保ち、追加107文字だけを今回分とする。有限診断、原文通読、単位全体の判断を区別し、第五段落全体は未完とする。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:92]==old.document['statements'] and len(new.document['statements'])==93
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in dependency().entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-practical-benefit-reading-v1.json');assert prior['selection']==selection_binding(new,[91]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=92,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=107,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('connections',connection_checks),('witnesses',witness_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-practical-benefit-reading-v1.json','scripts/compose_clerical_resignation_condition.py','scripts/check_clerical_resignation_condition.py',
        'tests/test_clerical_resignation_condition.py','scripts/check_teaching_policy.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_clerical_practical_benefit.py','scripts/compose_civic_example.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='clerical_resignation_condition_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[92],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
