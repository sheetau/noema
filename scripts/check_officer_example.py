"""Check serious counterfactual harm, command obedience, and sentence binding."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue, SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_officer_example import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, NAMES, PRIMITIVES, MEANINGS, LIMITS, parent, dependency, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_command_deliberation import (
    profile_model, discussion_model, EXTRA as COMMAND_EXTRA, STATES, POINTS, SCENES, key)
from scripts.check_officer_command_binding import DOMAIN as OFFICER_DOMAIN

INDEX = 'data/semantic-review-index-v166.json'
REPORT = 'reports/officer-example-v1.json'
AUDIT = 'data/officer-example-reading-v1.json'
DOC = 'docs/officer-example-v1.md'
EVIDENCE = 'data/officer-example-evidence-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ('reports/scholarly-compatibility-v1.json','reports/command-deliberation-v1.json')
DOMAIN = OFFICER_DOMAIN + ('work','discussion','factor','result','degree','mechanism','community')
EXTRA = COMMAND_EXTRA + 'r zwork[] a.r zhigh[h[a] c h[a] c] c.'


def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, sign=True, bindings=('issuer','person','office','action')):
    target = dict(profile='r32w', harm='r32x', obedience='r32y', adapter='r32z',
                  norm='r322', scope='r323', quantifier='r324', discourse='r325')[kind]
    doc = deepcopy(catalog().document)
    if kind == 'quantifier':
        for d in doc['declarations']:
            if d['name'] in ('r323','r32u','r322','r32x'):
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc,[target]), statements=[])
    polarity = 'e[k zperson[]][k zperson[]]' if sign else 'u[e[k zperson[]][k zperson[]]]'
    args = dict(
        profile='k zvariables[] p zequations k zfactor[] p zchecked p zatleast p zhigh',
        harm='k zperson[] k zdiscussion[] k zwork[] k zref[]',
        obedience='k zissuer[] k zperson[] k zoffice[] k zaction[] '+polarity+' k zref[]',
        adapter='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+'] '+polarity+' k zref[]',
        norm='k zissuer[] k zperson[] k zoffice[] k zaction[] '+polarity+' k zref[]',
        scope=' '.join('k z'+n+'[]' for n in NAMES)+' '+polarity+' k zref[]',
        quantifier='', discourse='')[kind]
    call = 'k '+target+'['+args+']'
    if kind in ('harm','obedience','adapter','norm','quantifier'): call = 't['+call+'][k zref[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v = {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in (*NAMES,'discussion','other'): v['z'+n] = lambda n=n:n
    v.update(zref=lambda:'reference', h232v=lambda:'reference')
    return v


@lru_cache(None)
def profile_checks():
    doc, rows = fixture('profile'), {}
    for name,table,grades,high,expected in (
        ('serious_loss',(False,)*4,(3,3,1,1),True,True),
        ('small_loss',(False,)*4,(3,3,1,1),False,False),
        ('high_degree_without_loss',(False,)*4,(1,1,1,1),True,False),
        ('improvement',(False,)*4,(1,1,3,3),True,False),
        ('every_solution_loses',(False,True,False,True),(3,4,1,2),True,True),
        ('one_solution_ties',(False,True,False,True),(3,4,1,3),True,False),
        ('one_solution_gains',(False,True,False,True),(3,4,1,5),True,False),
        ('no_on_solution',(False,False,True,False),(3,3,1,1),True,False),
        ('no_off_solution',(True,False,False,False),(3,3,1,1),True,False)):
        v = profile_model(doc,table=table,grades=grades)
        v['zhigh'] = lambda on,off:high
        actual = evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual == [expected], (name,actual); rows[name] = actual[0]
    for variant in ('unassessed','incomparable','one_pair_not_severe'):
        v = profile_model(doc,table=(False,True,False,True),grades=(3,4,1,2),variant=variant)
        v['zhigh'] = lambda on,off: variant!='one_pair_not_severe' or (key(on),key(off))!=((True,True),(False,True))
        if variant=='incomparable': v['zatleast'] = lambda left,right:key(left)==key(right)
        actual = evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[False], (variant,actual); rows[variant]=actual[0]
    return dict(contrasts=rows, nonempty_all_solution_pairs=True, direction_and_degree_independent=True)


def harm_model(doc,variant='baseline',log=None):
    v=base(doc)
    grades=(3,3,1,1)
    def prefix(args):
        if log is not None: log.add(tuple(args[:5]))
        assert args[:4]==('person','discussion','work','reference') and args[4] in SCENES
    def provider(value):
        def call(*args): prefix(args); return value(*args[5:])
        return call
    v.update(h243l=provider(lambda:SequenceValue(('factor','result'),'"individual"')),
        h243m=provider(lambda item,state:False), h243n=provider(lambda:'factor'),
        h243o=provider(lambda state:POINTS[STATES.index(key(state))]),
        cg=lambda p,a,s:(p,a)==('person','other' if variant=='other_activity' else 'discussion') and s in ('onlow','onhigh'),
        h242n=lambda work,ref,point:(work,ref)==('other' if variant=='other_work' else 'work','reference') and point in POINTS,
        h242o=lambda work,ref,left,right:(work,ref)==('work','reference') and grades[POINTS.index(left)]>=grades[POINTS.index(right)],
        h243p=lambda work,ref,on,off:'degree' if (work,ref)==('work','reference') and on in ('onlow','onhigh') and off in ('offlow','offhigh') else 'other',
        h243q=lambda work,ref,degree:(work,ref,degree)==('work','other' if variant=='other_degree_reference' else 'reference','degree') and variant!='small_loss')
    return v


@lru_cache(None)
def harm_checks():
    doc, rows, seen = fixture('harm'), {}, set()
    for variant in ('baseline','other_activity','other_work','other_degree_reference','small_loss'):
        v=harm_model(doc,variant,seen)
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'], (variant,actual)
        assert not v['cg']('person','discussion','reference')
        rows[variant]=actual[0]
    assert seen and {p[-1] for p in seen}==set(SCENES)
    return dict(contrasts=rows, native_alignment_and_serious_loss=True,
                same_person_activity_work_reference_and_evaluation=True, no_actual_execution_required=True)


def obedience_model(doc,sign=True,variant='baseline'):
    v=base(doc)
    def matches(source,person,role,action,code,polarity,ref):
        return (source,person,role,action,symbol(code),polarity,ref)==(
            'other' if variant=='other_source' else 'issuer','person','office','action','zzq',sign,
            'offlow' if variant=='other_reference' else 'reference')
    v.update(h7a=lambda *args:variant!='missing_demand' and matches(*args),
        h234b=lambda *args:variant!='unguided_coincidence' and matches(*args[:-1]),
        cg=lambda p,a,s:(p,a)==('person','action') and (not sign if variant=='wrong_execution' else sign))
    return v


@lru_cache(None)
def obedience_checks():
    rows={}
    small=('issuer','person','office','action','other')
    for sign in (False,True):
        doc=fixture('obedience',sign)
        for variant in ('baseline','missing_demand','unguided_coincidence','other_source','other_reference','wrong_execution'):
            actual=evaluate(doc,obedience_model(doc,sign,variant),small,SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual);rows[str((sign,variant))]=actual[0]
        for bindings in ((),('issuer','person','office'),('issuer','person','office','action'),
                         ('person','issuer','office','action'),('issuer','person','office','action','other')):
            doc=fixture('adapter',sign,bindings)
            actual=evaluate(doc,obedience_model(doc,sign),small,('reference',),True)
            assert actual==[bindings==('issuer','person','office','action')],(sign,bindings,actual)
            rows[str((sign,bindings))]=actual[0]
    return dict(contrasts=rows, native_signed_compliance_and_guidance=True, exact_four_bindings=True)


@lru_cache(None)
def norm_checks():
    rows={}
    for sign in (False,True):
        doc=fixture('norm',sign)
        for variant in ('baseline','absent','wrong_target_polarity','wrong_required_polarity','other_source','other_role','other_reference'):
            v=base(doc)
            def demand(source,person,role,code,bindings,targetsign,ref,requiredsign,point):
                return variant!='absent' and (source,person,role,symbol(code),code.rank,tuple(bindings.items),targetsign,ref,requiredsign,point)==(
                    'other' if variant=='other_source' else 'issuer','person','other' if variant=='other_role' else 'office',
                    'r32z',1,('issuer','person','office','action'),not sign if variant=='wrong_target_polarity' else sign,
                    'offlow' if variant=='other_reference' else 'reference',variant!='wrong_required_polarity','reference')
            v['h243r']=demand
            assert all(v[n] is unknown for n in ('cg','h7a','h234b'))
            actual=evaluate(doc,v,DOMAIN,SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual);rows[str((sign,variant))]=actual[0]
    return dict(contrasts=rows, target_polarity_distinct_from_positive_obligation=True, compliance_not_executed=True)


@lru_cache(None)
def scope_checks():
    rows={}
    for sign in (False,True):
        doc=fixture('scope',sign)
        for variant in ('baseline','other_work','other_assigned_role','other_command_action'):
            v=discussion_model(doc,sign=sign);v['zwork']=lambda:'work'
            v.update(h237y=lambda work,ref:(work,ref)==('work','reference'),
                h237h=lambda work,ref:'mechanism', h237i=lambda work,ref:'community',
                h237d=lambda mech,work,ref:FunctionValue(('individual',),'truth',lambda p:p=='person'),
                h237c=lambda person,community,ref:(person,community,ref)==('person','community','reference'),
                h237e=lambda p,m,w,r:'other' if variant=='other_assigned_role' else 'office',
                h237f=lambda p,role,m,w,r:(p,role,m,w,r)==('person','office','mechanism','work','reference'),
                h237x=lambda p,role,w,a,r:(p,role,w,a,r)==('person','office','other' if variant=='other_work' else 'work',
                    'other' if variant=='other_command_action' else 'action','reference'))
            actual=evaluate(doc,v,DOMAIN,SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual);rows[str((sign,variant))]=actual[0]
    return dict(contrasts=rows, native_officer_command_and_same_assigned_work=True)


@lru_cache(None)
def quantifier_checks():
    doc,rows=fixture('quantifier'),{}
    mixed=('x','y','y','x','y','x','y','x')
    for variant in ('baseline','no_intent_no_harm','no_intent_no_obligation','intent_no_harm','negative_command',
                    'other_discussion_work','wrong_obedience_person','wrong_obedience_source','wrong_action',
                    'wrong_harmed_work','wrong_harmed_person','wrong_harmed_activity','wrong_harm_evaluation','empty_scope'):
        v=base(doc);selectedsign=variant!='negative_command'
        v['r323']=lambda *args:variant!='empty_scope' and args==(*mixed,selectedsign,'reference')
        wanted=(mixed[0],mixed[1],mixed[2],mixed[5],mixed[6],selectedsign,'y','reference')
        v['r32u']=lambda *args:variant not in ('no_intent_no_harm','no_intent_no_obligation') and args==wanted
        v['h237x']=lambda p,role,w,a,r:(p,role,w,a,r)==(mixed[0],mixed[1],
            'y' if variant=='other_discussion_work' else mixed[7],'y','reference')
        def norm(source,person,role,action,sign,ref):
            good=variant!='no_intent_no_obligation' and (source,person,role,action,sign,ref)==(
                'y' if variant=='wrong_obedience_source' else mixed[3],
                'y' if variant=='wrong_obedience_person' else mixed[0],mixed[1],
                'x' if variant=='wrong_action' else mixed[6],selectedsign,'reference')
            return Content(SCENES,tuple(good for _ in SCENES))
        def harm(p,a,w,ref):
            good=variant not in ('no_intent_no_harm','intent_no_harm') and (p,a,w,ref)==(
                'y' if variant=='wrong_harmed_person' else mixed[0],
                'x' if variant=='wrong_harmed_activity' else 'y',
                'y' if variant=='wrong_harmed_work' else mixed[7],'reference')
            return Content(SCENES,tuple(good and (s!='reference' if variant=='wrong_harm_evaluation' else True) for s in SCENES))
        v.update(r322=norm,r32x=harm)
        actual=evaluate(doc,v,('x','y'),SCENES,True)
        expected=variant in ('baseline','no_intent_no_harm','negative_command','other_discussion_work','empty_scope')
        assert actual==[expected],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, duty_independent_of_intent=True, independent_eight_individual_and_boolean_quantifiers=True,
        boundaries=['r323/r32u/r322/r32x are typed boundaries for quantifier checks; their native components are checked separately.'])


@lru_cache(None)
def discourse_checks():
    doc,rows=fixture('discourse'),{}
    for variant in ('baseline','wrong_prior','wrong_content','missing_example','wrong_order','wrong_context'):
        v=base(doc)
        v.update(h243t=lambda:'sentence',h242c=lambda:'general',h242i=lambda:'prior',wa=lambda:'author',h232o=lambda:'reference',
            h236i=lambda n,a,code,ctx:(n,a,symbol(code),code.rank,ctx)==('sentence','author','r324',3,'reference'),
            h243s=lambda n,a,prior,general,current,ctx:variant!='missing_example' and (
                n,a,prior,symbol(general),general.rank,symbol(current),current.rank,ctx)==('sentence','author',
                'prior' if variant=='wrong_prior' else 'general','r3n',3,'r323' if variant=='wrong_content' else 'r324',3,
                'offlow' if variant=='wrong_context' else 'reference'),
            ue=lambda prior,n,ctx:variant!='wrong_order' and (prior,n,ctx)==('prior','sentence','reference'))
        actual=evaluate(doc,v,DOMAIN+('sentence','general','prior','author'),SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert all(v[n] is unknown for n in ('h243l','h243r','cg'))
    return dict(contrasts=rows, rank_three_example_and_attribution=True, hypothetical_content_not_executed=True)


@lru_cache(None)
def unknown_checks():
    doc=fixture('harm');names=('h243l','h243m','h243n','h243o','h243p','h243q','h242n','h242o','cg')
    for name in names:
        v=harm_model(doc);v[name]=unknown
        try:evaluate(doc,v,DOMAIN,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=list(names))


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('So ',['h243s','r325'],'先行する職務内の制約の例示。'),
        ('würde es sehr verderblich sein, ',['r32w','r32x','r324'],'同じ事務に対する、仮定した実行による重大な低下。'),
        ('wenn ein Offizier, ',['r32k','r323','r324'],'同じ任用された将校についての条件的な例示。'),
        ('dem von seinen Oberen etwas anbefohlen wird, ',['r32l','r32m','r32n','r32j'],'同じ組織の上官から本人へ提示された、指定極性の指示。'),
        ('im Dienste ',['cb','h243j','h237x','r323'],'同じ担当職務・事務を遂行する場面。'),
        ('über die Zwekmäßigkeit oder Nützlichkeit dieses Befehls ',['r32q','r32r','r32s','r32t','h243h'],'同じ命令の目的への寄与または同じ組織の実務上の利害への寄与という検討の論点。'),
        ('laut vernünfteln wollte; ',['h243k','h232p','ca','h243i','r32u','r324'],'声に出して理拠を述べ検討しようとする意向。実行済みとはしない。'),
        ('er muß gehorchen.', ['r32y','r32z','r322','r324'],'同じ指示の内容への対応と指示に従う調整を要求する。意向の有無にかかわらず同じ命令事例に属する規範内容。'),
    ]
    cursor,clauses=2123,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==2331
    text=unit['text'][2123:2331];count=sum(not c.isspace() for c in text)
    evidence=read(EVIDENCE)
    for page in evidence['pages']:assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='officer_example_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[2123,2331],text=text),
        selection=selection_binding(catalog(),[82]),clauses=clauses,interpretation=LIMITS,unresolved=[],
        decision='equivalent_under_stated_reading_for_the_officer_example',whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,preserved_reviewed_sentence_characters=1814,
        paragraph_reviewed_sentence_characters=1814+count,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '固定原文を原刊485〜486頁の記録と照合し、改頁のüberを重複せずSoからgehorchenまで通読した。',
            '将校・上官・任用役職・指揮順序・同じ組織・提示行為・対象行為・極性を通して追跡し、同じ勤務上の事務と議論へ接続した。',
            '目的適合と有用性は明示した二つの評価観点であり、問いの対象と肯定的な評価結論を分けた。勤務中の発声を全読者への公的発信にしていない。',
            '害を意向だけや単なる命令不履行へ置き換えず、同じ議論の仮定的実行と事務の低下へ結んだ。高い程度を厳密な低下と別に要求する。',
            '服従要求を意向条件の外に置き、否定命令にも対応した。要求の報告と実際の履行・正当性を区別し、同じ要求に基づく調整を保持した。',
            'Soの例示は先行する職務内の制約へ結び、直前の学識者の可能性と次文の批評の自由を撤回する内容を加えない。',
            '固定背景の頑健な比較、実務上の評価基準、当該指示の上官を規範源とすることは採用解釈として明示した。これらを原文の唯一の解釈や現実の因果の証明としない。'],
        original_pages=evidence['pages'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (
            FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,*PRIOR,*(page['path'] for page in evidence['pages']))})


@lru_cache(None)
def structure_checks():
    old,new,lib=parent(),catalog(),dependency()
    assert new.document['statements'][:82]==old.document['statements'] and len(new.document['statements'])==83
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in lib.entries.items():
        assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    prior=read('data/scholarly-compatibility-reading-v1.json')
    assert prior['selection']==selection_binding(new,[81]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for p in (FULL,CORE):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation)
            assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=82,added_statements=1,preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=178,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,s in build().items():write_exact(ROOT/p,s)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('profile',profile_checks),('harm',harm_checks),('obedience',obedience_checks),('norm',norm_checks),
                    ('scope',scope_checks),('quantifier',quantifier_checks),('discourse',discourse_checks),
                    ('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{
        INDEX,AUDIT,DOC,EVIDENCE,INVENTORY,*PRIOR,'data/scholarly-compatibility-reading-v1.json',
        'scripts/compose_officer_example.py','scripts/check_officer_example.py','tests/test_officer_example.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_command_deliberation.py',
        'scripts/check_officer_command_binding.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='officer_example_hypothetical_serious_harm_and_obedience',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[82],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
