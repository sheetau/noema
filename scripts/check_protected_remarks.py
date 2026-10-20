"""Check protection of each coordinated activity without executing the bans."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_protected_remarks import (
    ROOT,FULL,CORE,BASIS,ANNOTATIONS,NAMES,PUBLIC,PRIMITIVES,MEANINGS,LIMITS,parent,dependency,build,closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

INDEX='data/semantic-review-index-v167.json'
REPORT='reports/protected-remarks-v1.json'
AUDIT='data/protected-remarks-reading-v1.json'
DOC='docs/protected-remarks-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='data/officer-example-evidence-v1.json'
IMAGE='artifacts/officer-example-v1/page-486.jpg'
PRIOR=('reports/officer-example-v1.json','reports/military-remarks-v1.json')
SCENES=('reference','other')
CONSTANTS=(*NAMES,'regulator','standard','policy','other')
DOMAIN=CONSTANTS+('prior','sentence','author')
EXTRA=''.join('r z'+n+'[] a.' for n in CONSTANTS)+'r zref[] d.'
PAYLOADS={'r33g':('r33d',3),'r33h':('r33e',4),'r33i':('r33f',5)}
BANS={'r33j':('r33g',5,(1,3,4)),'r33k':('r33h',6,(1,3,4,5)),'r33l':('r33i',7,(1,3,4,5,6))}


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,target=None,bindings=()):
    target=target or dict(protection='r33m',prior='r33n',scope='r33o',regulators='r33p',quantifier='r33q',discourse='r33r')[kind]
    boundaries={
        'payload':('r33d','r33e','r33f'), 'prior':('r323',), 'scope':('r33n','r33c'),
        'regulators':('r33m',), 'quantifier':('r33o','r33p'),
    }.get(kind,())
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    if kind in ('payload','ban'):
        args='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+']'+(' k zref[]' if kind=='ban' else '')
    else:
        names=dict(protection=('regulator','person','scholar','making','presenting','notes','audience'),
                   prior=('person','office','institution'),scope=NAMES,regulators=PUBLIC,quantifier=(),discourse=())[kind]
        args=' '.join('k z'+n+'[]' for n in names)+(' k zref[]' if names else '')
    call='k '+target+'['+args+']'
    if kind not in ('prior','scope','discourse'):call='t['+call+'][k zref[]]'
    return parse(format_graph(doc,'compact')+EXTRA+'q['+call+'].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in CONSTANTS:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',h232v=lambda:'reference')
    return v


@lru_cache(None)
def payload_checks():
    rows={}
    # Each position alone differs from the others. This exercises every binding
    # independently on a two-element domain without a Cartesian execution of
    # the already checked record construction inside r33d/e/f.
    for target,(callee,size) in PAYLOADS.items():
        for special in range(size):
            bindings=tuple('person' if i==special else 'other' for i in range(size))
            doc=fixture('payload',target,bindings);v=base(doc)
            wanted=tuple('x' if i==special else 'y' for i in range(size))
            v.update(zperson=lambda:'x',zother=lambda:'y')
            v[callee]=lambda *args:Content(SCENES,tuple(args==wanted for _ in SCENES))
            actual=evaluate(doc,v,('x','y'),SCENES,True)
            assert actual==[True],(target,special,actual)
        for size_delta in (-1,1):
            bindings=('person',)*(size+size_delta)
            doc=fixture('payload',target,bindings);v=base(doc);v['zperson']=lambda:'x'
            v[callee]=lambda *args:Content(SCENES,(True,True))
            assert evaluate(doc,v,('x','y'),SCENES,True)==[False],(target,size_delta)
        rows[target]=dict(independent_slots=size,short_and_long_lists_refused=True)
    return dict(adapters=rows,boundaries=['r33d/e/f execution contents are typed boundaries here; military-remarks checks their native record and execution conditions.'])


@lru_cache(None)
def ban_checks():
    rows={}
    for target,(payload,size,positions) in BANS.items():
        for special in range(size):
            bindings=tuple('person' if i==special else 'other' for i in range(size))
            wanted=tuple('x' if i==special else 'y' for i in range(size))
            doc=fixture('ban',target,bindings);v=base(doc);v.update(zperson=lambda:'x',zother=lambda:'y')
            def demand(source,person,role,code,args,sign,point):
                return (source,person,role,symbol(code),code.rank,tuple(args.items),sign,point)==(
                    *wanted[:3],payload,0,tuple(wanted[i] for i in positions),False,'reference')
            v['h7k']=demand
            actual=evaluate(doc,v,('x','y'),SCENES,True)
            assert actual==[True],(target,special,actual)
            assert v['cg'] is unknown
        for delta in (-1,1):
            doc=fixture('ban',target,('person',)*(size+delta));v=base(doc);v['zperson']=lambda:'x';v['h7k']=lambda *a:True
            assert evaluate(doc,v,('x','y'),SCENES,True)==[False],(target,delta)
        rows[target]=dict(independent_slots=size,negative_requirement=True,invalid_lengths_refused=True)
    return dict(adapters=rows,payload_not_executed=True)


def protection_model(doc,variant='baseline',seen=None):
    v=base(doc)
    v.update(h244d=lambda ref:'standard' if ref=='reference' else 'other',
        h235r=lambda regulator,ref:'policy' if (regulator,ref)==('regulator','reference') else 'other')
    expected={'r33j':('regulator','person','scholar','making','notes'),
              'r33k':('regulator','person','scholar','presenting','notes','audience'),
              'r33l':('regulator','person','scholar','making','presenting','notes','audience')}
    def requirement(source,person,role,code,bindings,ref,sign,point):
        name=symbol(code)
        if seen is not None:seen.add((name,point))
        absent={'allow_making_ban':'r33j','allow_submission_ban':'r33k','allow_joint_ban':'r33l'}.get(variant)
        return name!=absent and (source,person,role,code.rank,tuple(bindings.items),ref,sign,point)==(
            'other' if variant=='wrong_standard' else 'standard','other' if variant=='wrong_regulator' else 'regulator',
            'other' if variant=='wrong_policy_role' else 'policy',1,
            tuple('other' if variant=='wrong_person' and n=='person' else n for n in expected[name]),
            'other' if variant=='wrong_reference' else 'reference',variant=='wrong_polarity','reference')
    v['h237z']=requirement
    return v


@lru_cache(None)
def protection_checks():
    doc,rows,seen=fixture('protection'),{},set()
    for variant in ('baseline','allow_making_ban','allow_submission_ban','allow_joint_ban','wrong_standard',
                    'wrong_regulator','wrong_policy_role','wrong_person','wrong_reference','wrong_polarity'):
        v=protection_model(doc,variant,seen)
        assert all(v[n] is unknown for n in ('h7k','cg','h244b','h244c','h243u','h243v') if n in v)
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    assert seen=={(n,p) for n in BANS for p in SCENES}
    return dict(contrasts=rows,all_three_ban_contents_protected=True,protection_is_not_actual_absence_of_bans=True,
                no_execution_truth_or_permission_inferred=True)


@lru_cache(None)
def prior_checks():
    doc,rows=fixture('prior'),{}
    for variant in ('baseline','negative_command','no_command','wrong_person','wrong_office','wrong_institution','wrong_reference'):
        v=base(doc)
        v.update(zperson=lambda:'x',zoffice=lambda:'y',zinstitution=lambda:'x')
        wanted=('y' if variant=='wrong_person' else 'x','x' if variant=='wrong_office' else 'y',
                'y' if variant=='wrong_institution' else 'x','y','x','y','x','y',variant!='negative_command',
                'other' if variant=='wrong_reference' else 'reference')
        v['r323']=lambda *args:variant!='no_command' and args==wanted
        actual=evaluate(doc,v,('x','y'),SCENES,True)
        assert actual==[variant in ('baseline','negative_command')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, same_officer_role_institution_preserved=True,
                boundaries=['r323 is a typed boundary; officer-example checks the native command case.'])


@lru_cache(None)
def scope_checks():
    doc,rows=fixture('scope'),{}
    for variant in ('baseline','no_prior','other_public_person','other_office','other_institution','other_notes','other_audience'):
        v=base(doc)
        v['r33n']=lambda p,office,institution,ref:variant!='no_prior' and (p,office,institution,ref)==('person','office','institution','reference')
        wanted=list(NAMES)+['reference']
        if variant not in ('baseline','no_prior'):wanted[NAMES.index({'other_public_person':'person'}.get(variant,variant[6:]))]='other'
        # r33c has office,institution followed by the same PUBLIC argument order.
        v['r33c']=lambda *args:args==tuple(wanted)
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,boundaries=['r33n and r33c are typed boundaries for their common person/role/institution join; native components are separately checked.'])


@lru_cache(None)
def regulator_checks():
    doc,rows=fixture('regulators'),{}
    for variant in ('both_protected','second_unprotected','none_selected','wrong_reference','wrong_activity','wrong_notes','wrong_audience','wrong_evaluation'):
        v=base(doc)
        for n in CONSTANTS:v['z'+n]=lambda n=n:'x' if n in ('person','presenting','notes','field') else 'y'
        v['h244e']=lambda regulator,ref:variant!='none_selected' and ref=='reference' and regulator in ('x','y')
        wanted=['x','y','y','x','x','y','reference'] # person,scholar,making,presenting,notes,audience,ref
        index={'wrong_reference':6,'wrong_activity':3,'wrong_notes':4,'wrong_audience':5}.get(variant)
        if index is not None:wanted[index]='other' if index==6 else ('y' if wanted[index]=='x' else 'x')
        def protected(regulator,*args):
            good=args==tuple(wanted) and not (variant=='second_unprotected' and regulator=='y')
            return Content(SCENES,tuple(good and (point=='other' if variant=='wrong_evaluation' else True) for point in SCENES))
        v['r33m']=protected
        actual=evaluate(doc,v,('x','y'),SCENES,True)
        assert actual==[variant in ('both_protected','none_selected')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows, all_selected_regulators=True,boundaries=['r33m is a typed boundary here; protection checks execute its three demands natively.'])


@lru_cache(None)
def quantifier_checks():
    doc,rows=fixture('quantifier'),{}
    mixed=('x','y','x','y','x','y','x','y','x')
    for variant in ('baseline','empty_scope','second_failure','wrong_person','wrong_making','wrong_presenting',
                    'wrong_scholar','wrong_notes','wrong_audience','wrong_field','wrong_reference','wrong_evaluation'):
        v=base(doc)
        chosen=set() if variant=='empty_scope' else {mixed,('y',)*9} if variant=='second_failure' else {mixed}
        v['r33o']=lambda *args:args[:-1] in chosen and args[-1]=='reference'
        wanted=[mixed[NAMES.index(n)] for n in PUBLIC]+['reference']
        if variant.startswith('wrong_') and variant!='wrong_evaluation':
            name=variant[6:];i=7 if name=='reference' else PUBLIC.index(name)
            wanted[i]='other' if i==7 else ('y' if wanted[i]=='x' else 'x')
        def protected(*args):
            good=args==tuple(wanted)
            return Content(SCENES,tuple(good and (point=='other' if variant=='wrong_evaluation' else True) for point in SCENES))
        v['r33p']=protected
        actual=evaluate(doc,v,('x','y'),SCENES,True)
        assert actual==[variant in ('baseline','empty_scope')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,independent_nine_argument_quantification=True,
                boundaries=['r33o/r33p are typed boundaries for the whole conditional; their joins and regulator quantification are separately checked.'])


@lru_cache(None)
def discourse_checks():
    doc,rows=fixture('discourse'),{}
    for variant in ('baseline','wrong_prior','wrong_content','wrong_dimension','wrong_order','wrong_context'):
        v=base(doc)
        v.update(h244f=lambda:'sentence',h243t=lambda:'prior',wa=lambda:'author',h232o=lambda:'reference',
            h236i=lambda n,a,code,ctx:(n,a,symbol(code),code.rank,ctx)==('sentence','author','r33q',3,'reference'),
            h236k=lambda n,a,prior,old,current,new,dimension,ctx:(n,a,prior,symbol(old),old.rank,current,symbol(new),new.rank,symbol(dimension),ctx)==(
                'sentence','author','other' if variant=='wrong_prior' else 'prior','r324',3,'sentence',
                'r324' if variant=='wrong_content' else 'r33q',3,'r33n' if variant=='wrong_dimension' else 'r2zg',
                'other' if variant=='wrong_context' else 'reference'),
            ue=lambda prior,current,ctx:variant!='wrong_order' and (prior,current,ctx)==('prior','sentence','reference'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h237z'] is unknown and v['h244d'] is unknown
    return dict(contrasts=rows,rank_three_contrast_and_attribution=True,content_not_executed=True)


@lru_cache(None)
def unknown_checks():
    doc=fixture('protection')
    for name in ('h244d','h235r','h237z'):
        v=protection_model(doc);v[name]=unknown
        try:evaluate(doc,v,DOMAIN,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=['h244d','h235r','h237z'])


def reading():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0012')
    parts=[
        ('Es kann ihm ',['r33n','r33o','r33q'],'先行する同じ将校への規範的な保護。物理的能力とはしない。'),
        ('aber ',['h236k','r33r'],'同じ本人の職務内の制約と学識者としての活動を対照する。'),
        ('billigermaßen ',['h244d','r33m'],'公正・道理に照らした評価の規範源を固定する。'),
        ('nicht verwehrt werden, ',['r33j','r33k','r33l','r33m','r33p'],'関係する規制者へ、同じ作成・提出・両実行を禁じてはならないと要求する。'),
        ('als Gelehrter, ',['r2zi','r33b','r33c','r33o'],'同じ本人が学識者として理性を用い、公衆へ見解を向ける活動の立場。'),
        ('über die Fehler im Kriegesdienste ',['r326','r33a','h244a'],'同じ軍務領域について、備えるべき条件の不充足という論点を扱う。'),
        ('Anmerkungen zu machen, ',['h243w','h243x','h243y','r33d','r33g'],'同じ所見のまとまりを本人が作成する内容。記録は実行の中に置く。'),
        ('und diese seinem Publikum ',['r33b','r33f','r33i','cc','ce'],'作成と提出を同じ注記・本人の同じ公衆へ結ぶ。'),
        ('zur Beurtheilung vorzulegen.', ['h242g','h243z','hztl','r327','r33e','r33h'],'公衆が同じ注記を判断することを目指し、その検討に供する。目的達成は要求しない。'),
    ]
    cursor,clauses=2332,[]
    for text,names,meaning in parts:
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=meaning));cursor+=len(text)
    assert cursor==2512
    text=unit['text'][2332:2512];count=sum(not c.isspace() for c in text)
    evidence=read(EVIDENCE);page=next(p for p in evidence['pages'] if p['page']==486)
    assert digest((ROOT/IMAGE).read_bytes())==page['sha256']
    return dict(status='protected_remarks_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',
        document=FULL,meaning_basis=BASIS,source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[2332,2512],text=text),
        selection=selection_binding(catalog(),[83]),clauses=clauses,interpretation=LIMITS,unresolved=[],
        decision='equivalent_under_stated_reading_for_protected_scholarly_remarks',whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=count,preserved_reviewed_sentence_characters=1992,
        paragraph_reviewed_sentence_characters=1992+count,semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁で前文の服従要求から当該文末まで通読し、ihmを同じ将校に戻し、次の市民の納付の例と混ぜないことを確認した。',
            '公正・道理に照らした規範と現職の上官の命令を区別し、禁止拒否を現実の許可・無禁止・実行へ移していない。',
            '同じ注記を作る活動、提出する活動、両方を行う活動の各禁止を拒否し、片方のみの禁止を見落としていない。',
            '軍務の欠点という論点を同じ領域と評価条件へ結び、注記が述べる欠点の現実の真理や原文外の具体的欠陥を追加していない。',
            '制作済み記録を前件に置かず、同じ注記と同じ公衆の束縛を、活動構成、実行内容、内外の規範引用を通して保持した。',
            '公衆の判断は提出の目的として引用し、全読者の実際の判断・理解・同意を条件にしていない。',
            'aberは役割別の対照として保持し、先行文の職務内の制約・服従要求を撤回しない。公正さの評価枠組みと上位の禁止拒否という読みは解釈として明示し、唯一の倫理理論を証明したとはしない。'],
        original_page=page,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,EVIDENCE,IMAGE,*PRIOR)})


@lru_cache(None)
def structure_checks():
    old,new,lib=parent(),catalog(),dependency()
    assert new.document['statements'][:83]==old.document['statements'] and len(new.document['statements'])==84
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p in PRIOR:validate_hashes(ROOT,read(p)['source_sha256'])
    prior=read('data/officer-example-reading-v1.json')
    assert prior['selection']==selection_binding(new,[82]);validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT)==reading()
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for p in (FULL,CORE):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation)
            assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=83,added_statements=1,preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=156,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,s in build().items():write_exact(ROOT/p,s)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('payload',payload_checks),('bans',ban_checks),('protection',protection_checks),('prior',prior_checks),
                    ('scope',scope_checks),('regulators',regulator_checks),('quantifier',quantifier_checks),
                    ('discourse',discourse_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{
        INDEX,AUDIT,DOC,INVENTORY,EVIDENCE,IMAGE,*PRIOR,'data/officer-example-reading-v1.json',
        'scripts/compose_protected_remarks.py','scripts/check_protected_remarks.py','tests/test_protected_remarks.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='equitable_protection_of_officer_scholarly_remarks',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[83],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
