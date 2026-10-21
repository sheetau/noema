"""Check common witnesses, discourse scope and the reviewed complete sentence."""
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
from scripts.compose_clerical_practical_benefit import ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,CASE_NAMES,WITNESSES,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_teaching_policy import substitute

INDEX='data/semantic-review-index-v175.json'
REPORT='reports/clerical-practical-benefit-v1.json'
AUDIT='data/clerical-practical-benefit-reading-v1.json'
DOC='docs/clerical-practical-benefit-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/representative-teaching-evidence-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('clerical-report-forecast','practical-benefit-extraction','personal-endorsement-case','latent-truth-compatibility'))
SCENES=('reference','actual','other')
LOWER=('r43b','r424','r42s','r42w','r42y')
EXTRA=''.join('r z'+n+'[] a.' for n in (*CASE_NAMES,'other'))+'r zref[] d.r zpoint[] d.r zotherref[] d.r zpersonalias[] a.r zbundlealias[] a.r zrefalias[] d.'
ARGS=' '.join('k z'+n+'[]' for n in CASE_NAMES)+' r[k zperson[]] r[k zbundle[]] r[k zref[]] k zref[]'


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
    query='k '+target+'['+('' if target in ('r43j','r43k') else ARGS)+']'
    if target!='r43k':query='t['+query+'][k zpoint[]]'
    doc=parse(format_graph(doc,'compact')+'q['+query+'].')
    if finite:
        # Diagnostic only: one explicit assignment for the nine outer universal
        # binders; keep both native individual existentials and enumerate the
        # three description witnesses. Production retains all typed domains.
        declaration=next(d for d in doc['declarations'] if d['name']=='r43j')
        def expression(text):return parse(format_graph(prefix,'compact')+'q[e['+text+']['+text+']].')['statements'][0]['body']['arguments'][0]
        universals=[];existentials=[]
        def find(node):
            if isinstance(node,dict):
                if node.get('kind')=='forall':universals.append(node)
                if node.get('kind')=='exists':existentials.append(node)
                for v in node.values():find(v)
            elif isinstance(node,list):
                for v in node:find(v)
        find(declaration['body']);assert len(universals)==9 and len(existentials)==5
        assignments={n['variable']:expression('k z'+name+'[]') for n,name in zip(universals,NAMES)}
        choices={n['variable']:[expression(t) for t in texts] for n,texts in zip(existentials[2:],(
            ('r[k zperson[]]','r[k zpersonalias[]]'),('r[k zbundle[]]','r[k zbundlealias[]]'),('r[k zref[]]','r[k zrefalias[]]')))}
        def reduce(node):
            if isinstance(node,dict):
                name=node.get('variable')
                if node.get('kind')=='forall' and name in assignments:return reduce(substitute(node['body'],name,assignments[name]))
                if node.get('kind')=='exists' and name in choices:
                    bodies=[reduce(substitute(node['body'],name,v)) for v in choices[name]]
                    return dict(kind='or',arguments=bodies)
                return {k:reduce(v) for k,v in node.items()}
            if isinstance(node,list):return [reduce(v) for v in node]
            return node
        declaration['body']=reduce(declaration['body']);doc=parse(format_graph(doc,'compact'))
    return doc


def run(doc,v,domain=None):return evaluate(doc,v,domain or (*CASE_NAMES,'other'),SCENES,True)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*CASE_NAMES,'other')})
    v.update(zref=lambda:'reference',zpoint=lambda:'actual',zotherref=lambda:'other',h232v=lambda:'reference',
        zpersonalias=lambda:'person',zbundlealias=lambda:'bundle',zrefalias=lambda:'reference')
    return v


def expected():
    ten=(*NAMES,'bundle','reference','actual')
    return dict(r43b=ten,r42s=ten,
        r424=('person','church','creed','subject','standard','bundle','reference','zperson','zbundle','zref','actual'),
        r42w=('person','bundle','reference','actual'),r42y=('person','bundle','subject','religion','reference','actual'))


def install(v,truth=(True,)*5,variant=None):
    for i,name in enumerate(LOWER):
        want=list(expected()[name])
        if variant and variant[0]==name:want[variant[1]]=variant[2] if len(variant)>2 else 'other'
        def relation(*args,want=tuple(want),name=name,bit=truth[i]):
            if name=='r424':args=(*args[:7],*(symbol(c) for c in args[7:10]),args[10])
            return bit and tuple(args)==want
        v[name]=relation


@lru_cache(None)
def connection_checks():
    doc=fixture('r43i',LOWER);table=[]
    for bits in product((False,True),repeat=5):
        v=base(doc);install(v,bits);result=run(doc,v);assert result==[all(bits)],(bits,result);table.append([*bits,result[0]])
    positions={}
    for name,values in expected().items():
        positions[name]=[]
        for i in range(len(values)):
            v=base(doc);install(v,variant=(name,i));assert run(doc,v)==[False],(name,i);positions[name].append(i)
        v=base(doc);install(v);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(five_condition_truth_table=table,independent_argument_positions=positions,boundaries=list(LOWER),
        unknown_refused=True,shared_context_and_name_codes=True)


@lru_cache(None)
def witness_checks():
    doc=fixture('r43j',('r35t',*LOWER),True);rows={}
    for variant in ('baseline','split_bundle','alternate_person_name','alternate_bundle_name','alternate_reference_name','missing_religion','no_frame'):
        v=base(doc);install(v)
        v['r35t']=lambda *args:variant!='no_frame' and tuple(args)==(*NAMES,'reference')
        if variant=='split_bundle':install(v,variant=('r42s',9))
        if variant.startswith('alternate_'):
            idx,code={'alternate_person_name':(7,'zpersonalias'),'alternate_bundle_name':(8,'zbundlealias'),
                      'alternate_reference_name':(9,'zrefalias')}[variant]
            install(v,variant=('r424',idx,code))
        if variant=='missing_religion':v['r42y']=lambda *args:False
        result=run(doc,v);wanted=variant in ('baseline','no_frame') or variant.startswith('alternate_')
        assert result==[wanted],(variant,result);rows[variant]=result[0]
    full=fixture('r43j',('r35t',*LOWER));v=base(full);install(v);v['r35t']=lambda *a:True
    try:run(full,v,('other',))
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Unbounded names silently restricted')
    return dict(contrasts=rows,diagnostic_outer_case_instantiated=True,diagnostic_description_choices=2,
        native_bundle_and_religion_existentials=True,all_branches_share_one_bundle=True,full_domain_refused=refusal,
        boundaries=['r35t',*LOWER])


@lru_cache(None)
def discourse_checks():
    doc=fixture('r43k');rows={};observed=[]
    for variant in ('baseline','no_claim','wrong_author','wrong_content','wrong_context','no_concession','reversed_reason','wrong_contrast',
                    'wrong_minimum','missing_first_emphasis','missing_second_emphasis','wrong_prior','wrong_background','wrong_continuation','reversed_order','merged_nodes'):
        v=base(doc);v.update(wa=lambda:'author',h252s=lambda:'prior' if variant=='merged_nodes' else 'sentence',h252b=lambda:'prior',h247t=lambda:'background',h232o=lambda:'reference')
        def outer(node,who,code,ctx):
            return (node,who,symbol(code),code.rank,ctx)==('sentence','other' if variant=='wrong_author' else 'author',
                'r42a' if variant=='wrong_content' else 'r43j',3,'other' if variant=='wrong_context' else 'reference')
        v['h236i']=lambda node,who,code,ctx:variant!='no_claim' and outer(node,who,code,ctx)
        def pair(node,who,whole,first,second,ctx,expected):
            observed.append((symbol(first),symbol(second),first.rank,second.rank))
            return outer(node,who,whole,ctx) and (symbol(first),symbol(second),first.rank,second.rank)==(*expected,2,2)
        v['h252t']=lambda n,w,c,a,b,ctx:variant!='no_concession' and pair(n,w,c,a,b,ctx,('r43d','r43e'))
        v['h252u']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,('r43e','r43h') if variant=='reversed_reason' else ('r43h','r43e'))
        v['h252v']=lambda n,w,c,a,b,ctx:pair(n,w,c,a,b,ctx,('r43e','r43g') if variant=='wrong_contrast' else ('r43f','r43g'))
        v['h252w']=lambda n,w,c,a,ctx:outer(n,w,c,ctx) and (symbol(a),a.rank)==('r43f' if variant=='wrong_minimum' else 'r43g',2)
        v['h252x']=lambda n,w,c,a,ctx:outer(n,w,c,ctx) and a.rank==2 and symbol(a) in (
            ('r43g',) if variant=='missing_first_emphasis' else ('r43f',) if variant=='missing_second_emphasis' else ('r43f','r43g'))
        v['h252y']=lambda n,w,p,pc,b,bc,c,ctx:outer(n,w,c,ctx) and (
            p,symbol(pc),pc.rank,b,symbol(bc),bc.rank)==('prior','r43j' if variant=='wrong_prior' else 'r42a',3,
            'background','r42a' if variant=='wrong_background' else 'r4l',3) and variant!='wrong_continuation'
        v['ue']=lambda p,n,ctx:(p,n,ctx)==(('sentence','prior','reference') if variant=='reversed_order' else ('prior','sentence','reference'))
        if variant=='merged_nodes':
            for name in ('h236i','h252t','h252u','h252v','h252w','h252x','h252y','ue'):v[name]=lambda *args:True
        result=run(doc,v,('author','sentence','prior','background','other'));assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    return dict(contrasts=rows,rank_three_whole_rank_two_families=True,reason_targets_undertaking=True,
        possibility_and_compatibility_both_emphasized=True,contents_not_executed=True)


def reading():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012');text=u['text'][3899:4278]
    parts=[
        ('Er zieht alsdann ',['r35t','r43c','h252y'],'同じ本人について、前文の代表的説明の場合を受けて実益を得ると述べる。'),
        ('allen praktischen Nutzen für seine Gemeinde aus Satzungen, ',['h252p','h252q','h252r','r43a','r43b','r42j'],'固定した同じ規定群から、その会衆への全実益を同じ活動で得る。'),
        ('die er selbst nicht mit voller Ueberzeugung unterschreiben würde, ',['r424','r43d'],'本人自身の見解として賛同を問われるなら、同じ規定群全体に十分な確信で賛同はしない。'),
        ('zu deren Vortrag er sich gleichwohl anheischig machen kann, ',['r42s','r43e','h252t'],'それでも同じ規定群の説明を責任をもって引き受けられる。'),
        ('weil es doch nicht ganz unmöglich ist, ',['r42w','r43f','r43h','h252u','h252x'],'理由として、真理の可能性を全排除できないことをなお押し出す。'),
        ('daß darin Wahrheit verborgen läge, ',['r42t','h252k'],'同じ規定群に含まれる命題部分に、本人には明らかでない真理がある可能性。'),
        ('auf alle Fälle aber wenigstens doch ',['r42y','h252v','h252w','h252x'],'対照して、同じ検討の全場合における次の内容を最低限の保証として強調する。'),
        ('nichts der innern Religion widersprechendes darin angetroffen wird.', ['r42k','h252m','h252n','r42x','r43g'],'同じ規定群に、指定した内面的宗教基準に実践上反する命題部分は含まれない。')]
    cursor=3899;clauses=[]
    for t,names,meaning in parts:
        assert u['text'][cursor:cursor+len(t)]==t,(cursor,t)
        clauses.append(dict(range=[cursor,cursor+len(t)],text=t,definitions=names,reading=meaning));cursor+=len(t)
    assert cursor==4278 and sum(not c.isspace() for c in text)==325
    pages=read(EVIDENCE)['pages']
    for page in pages:assert page['visually_inspected'] and digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='clerical_practical_benefit_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[3899,4278],text=text),selection=selection_binding(catalog(),[91]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_clerical_practical_benefit',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=325,
        preserved_reviewed_sentence_characters=3330,paragraph_reviewed_sentence_characters=3655,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊487頁の全文と直前の教会の教示・論拠の報告例、後続の抵触を信じた場合の辞職条件を照合した。alsdannを同じ代表的説明の場合への継続として読み、前の発言例の実現を追加していない。',
            '本人・職務・教会・会衆・規定群を同じ事例に結び、実益・賛同・説明引受け・真理・無抵触の各枝が異なる規定群を選べない量化順序を確認した。三呼称を明示的に存在量化し、前提内容の構成に本人・対象・基準との一致を保持する。',
            '全実益を得る強い読みと、共同の会衆を受益対象とする範囲を点検した。実際の結果と因果は著者の内容の内側にあり、教義の真理や各会員の一様な利益とは同一化していない。',
            '十分な確信での賛同の仮定的否定と、説明を引き受ける実践的可能性を分けた。gleichwohlをこの対照の譲歩に、weilを可能性と無抵触の連言から引受け可能性への理由提示に結んだ。',
            '可能性に対する全場合の無抵触、最低限の保証、二つの強調を同じ量化内の内容関数へ結んだ。肯定の可能性を現実の真理へ、無抵触を許容や説明の履行へ変えていない。',
            '連続する全語句と代名詞を対応させ、著者・第五段落文脈・直前文への順序を保持した。局所診断は閉じた内容の接続を確かめるもので、原文との同義性を機械的に証明したものではない。'],
        original_pages=pages,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in pages])})


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:91]==old.document['statements'] and len(new.document['statements'])==92
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    prior=read('data/clerical-report-forecast-reading-v1.json');assert prior['selection']==selection_binding(new,[90]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    return dict(preserved_statements=91,added_statements=1,preserved_whole_unit_reviews=len(reviews),new_definitions=len(MEANINGS),
        new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=325,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for n,f in [('connections',connection_checks),('witnesses',witness_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,*PRIORS,*[p['path'] for p in read(EVIDENCE)['pages']],
        'data/clerical-report-forecast-reading-v1.json','scripts/compose_clerical_practical_benefit.py','scripts/check_clerical_practical_benefit.py',
        'tests/test_clerical_practical_benefit.py','scripts/check_teaching_policy.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_civic_example.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='clerical_practical_benefit_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[91],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
