"""Check general adoption, the two-way criterion and the complete sixth sentence."""
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
from scripts.compose_legislative_touchstone import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,parent,dependencies,build,closure,NAMES,FOUR_NAMES,NODES
from scripts.check_rational_self_imposition import SCENES,ARGS,SEQ,model as self_model
from scripts.check_law_enactment import EXTRA,PROVIDER,DOMAIN
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_covenant_nullity import normalized

INDEX='data/semantic-review-index-v184.json'
REPORT='reports/legislative-touchstone-v1.json'
READING='data/legislative-touchstone-reading-v1.json'
DOC='docs/legislative-touchstone-v1.md'
LEXICAL='data/legislative-touchstone-lexical-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/posterity-rights-v1.json','reports/law-enactment-v1.json','reports/rational-self-imposition-v1.json')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),provider=True):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    if provider:
        prefix=deepcopy(parent().document);prefix.update(declarations=closure(prefix,['h7k','h7l']),statements=[])
        provided=parse(format_graph(prefix,'compact')+EXTRA+PROVIDER+'r zalternative[] d.')
        ns={d['name'] for d in provided['declarations']}
        doc['declarations']=provided['declarations']+[d for d in doc['declarations'] if d['name'] not in ns]
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN,scenes=SCENES):return evaluate(doc,v,domain,scenes,True)
def model(doc,variant='baseline',permission=True,prohibition=False,actor='actor'):
    v=self_model(doc,variant);v.update(h26ci=lambda:'community',h26cj=lambda:'other')
    oldcd=v['h26cd'];v['h26cd']=lambda a,s,p,c,l,r,h,t:s==actor and oldcd(a,'people',p,c,l,r,h,t)
    oldallow,oldrequire=v['h245c'],v['h237z']
    permit_at='alternative' if variant=='second_success' else 'candidate'
    def match(s,p,r,c,b,ref,sign,t):
        expected=['other',actor,'community',('r5ev',1),(actor,'people','community','law'),'reference',True,permit_at]
        changes={'wrong_source':(0,'actor'),'wrong_bearer':(1,'other'),'wrong_role':(2,'activity'),'wrong_code':(3,('r5en',1)),
                 'wrong_reference':(5,'outside'),'wrong_sign':(6,False),'wrong_permission_candidate':(7,'outside')}
        if variant in changes:
            i,value=changes[variant];expected[i]=value
        if variant.startswith('wrong_binding_'):
            items=list(expected[4]);items[int(variant[-1])]='other';expected[4]=tuple(items)
        return normalized((s,p,r,c,b,ref,sign,t))==tuple(expected)
    v['h245c']=lambda s,p,r,c,b,ref,sign,t:(permission and match(s,p,r,c,b,ref,sign,t)) if symbol(c)=='r5ev' else oldallow(s,p,r,c,b,ref,sign,t)
    v['h237z']=lambda s,p,r,c,b,ref,sign,t:(prohibition and match(s,p,r,c,b,ref,not sign,t)) if symbol(c)=='r5ev' else oldrequire(s,p,r,c,b,ref,sign,t)
    return v
def rejects_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)
@lru_cache(None)
def permission_checks():
    doc=fixture(('r5ew',),'q[k r5ew[k zactor[] '+ARGS+' k zcandidate[]]].');rows={}
    for allowed,opposed in product((False,True),repeat=2):
        v=model(doc,permission=allowed,prohibition=opposed);v['dg']=unknown;v['h26cf']=unknown
        actual=run(doc,v);assert actual==[allowed and not opposed];rows[str((allowed,opposed))]=actual[0]
    contrasts={}
    for variant in ('wrong_source','wrong_bearer','wrong_role','wrong_code','wrong_reference','wrong_sign','wrong_permission_candidate',*('wrong_binding_'+str(i) for i in range(4))):
        actual=run(doc,model(doc,variant));assert actual==[False];contrasts[variant]=actual[0]
    return dict(permission_conflict_table=rows,exact_actor_and_four_targets=contrasts,quoted_adoption_not_executed=True,
        unknown_rejected=rejects_unknown(doc,('h245c','h237z')))
@lru_cache(None)
def adoption_checks():
    doc=fixture(('r5ex','r5es'),'q[k r5ex['+ARGS+']].q[k r5es['+ARGS+']].');rows={}
    for actor in ('actor','people'):
        actual=run(doc,model(doc,actor=actor));assert actual==[True,actor=='people'];rows[actor]=actual
    for variant in ('reconfirmation','second_success','one_of_two','split_witness','no_activity','no_effect','split_effect_activity','split_times','empty_candidates','empty_law','missing_person','cycle'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('reconfirmation','second_success','one_of_two'),False],(variant,actual);rows[variant]=actual
    for permission,prohibition in ((False,False),(True,True)):
        assert run(doc,model(doc,permission=permission,prohibition=prohibition))==[False,False]
    return dict(native_general_adoption_and_self_difference=rows,no_definition_boundaries=True,
        same_actor_same_candidate=True,unknown_rejected=rejects_unknown(doc,('h26cf','h245c','h237z','h26cd','h26ce')))
@lru_cache(None)
def binding_checks():
    matrices={}
    for root,target,names in (('r5ev','r5el',FOUR_NAMES),('r5ey','r5ex',NAMES),('r5ez','r5ei',NAMES)):
        def case(i,j,length=0):
            bound=list(names)
            if length<0:bound.pop()
            if length>0:bound.append('law')
            seq='l[a]['+' '.join('k z'+n+'[]' for n in bound)+']'
            q='q[t[k '+root+'['+seq+(' k zreference[]' if root=='r5ev' else '')+']][k zcandidate[]]].'
            d=fixture((root,),q,(target,));v=model(d)
            v.update({'z'+n:lambda k=k:'beta' if k==i else 'alpha' for k,n in enumerate(names)})
            wanted=tuple('beta' if k==j else 'alpha' for k in range(len(names)))
            if target=='r5el':wanted+=('reference','candidate')
            if target=='r5ei':wanted+=('reference',)
            v[target]=lambda *a:a==wanted
            return run(d,v,('alpha','beta'))[0]
        rows=[]
        for i,j in product(range(len(names)),repeat=2):
            actual=case(i,j);assert actual==(i==j);rows.append(actual)
        assert not case(0,0,-1) and not case(0,0,1);matrices[root]=rows
    return dict(exact_positions=matrices,wrong_lengths_rejected=True,boundaries=['r5el for four-target adapter','r5ex/r5ei for three-target adapters'])
@lru_cache(None)
def criterion_checks():
    d=fixture(('r5e2',),'q[t[k r5e2[]][k zreference[]]].',('r5ei','r5ex','r5es'));rows=[]
    cases=(('alpha',)*3,('beta',)*3)
    for scope1,scope2,legal1,legal2,self1,self2 in product((False,True),repeat=6):
        v=model(d);v['r5ei']=lambda *a:a[-1]=='reference' and ((scope1 and a[:-1]==cases[0]) or(scope2 and a[:-1]==cases[1]))
        v['r5ex']=lambda *a:(legal1 and a==cases[0]) or(legal2 and a==cases[1])
        v['r5es']=lambda *a:(self1 and a==cases[0]) or(self2 and a==cases[1])
        expected=(not scope1 or legal1==self1) and(not scope2 or legal2==self2)
        actual=run(d,v,('alpha','beta'));assert actual==[expected]
        rows.append(dict(bits=[scope1,scope2,legal1,legal2,self1,self2],value=actual[0]))
    # Every position of a mixed tuple is in scope; no homogeneous-only quantification.
    mixed=[]
    for i in range(3):
        wanted=tuple('beta' if k==i else 'alpha' for k in range(3));v=model(d)
        v['r5ei']=lambda *a:a==(*wanted,'reference');v['r5ex']=lambda *a:a==wanted;v['r5es']=lambda *a:False
        actual=run(d,v,('alpha','beta'));assert actual==[False];mixed.append(actual[0])
    return dict(two_independent_law_frames=rows,mixed_tuple_failures=mixed,
        necessary_and_sufficient_not_just_necessary=True,empty_scope_not_existence=True,
        boundaries=['r5ei','r5ex','r5es'],native_components='adoption checks and prior law-enactment/rational-self-imposition reports')
@lru_cache(None)
def discourse_checks():
    d=fixture(('r5e4',),'q[k r5e4[]].',provider=False);author='author';ctx='context';whole=('r5e2',3);scope=('r5ez',1);question=('r5eu',1)
    expected={
      'h236i':{('h26co',author,whole,ctx)},
      'h26ck':{('h26cp',author,'h26cq',whole,scope,('r5ey',1),question,ctx)},
      'h26cl':{('h26cr',author,'h26cq',scope,question,ctx)},
      'h26cm':{('h26cp',author,whole,('r5e3',0),ctx)},
      'ue':{('h26bx','h26co',ctx),('h26cp','h26cq',ctx)},
    };rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','merged_nodes','different_question','different_property','wrong_scope','assertion_instead','unknown'):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else author;v['h255n']=lambda:'reference' if variant=='wrong_context' else ctx
        wanted=deepcopy(expected)
        for key,index,value in (('different_question',6,('r5ev',1)),('different_property',5,('r5et',1)),('wrong_scope',4,('r5ey',1)),('assertion_instead',6,('r5et',1))):
            if variant==key:
                row=list(next(iter(wanted['h26ck'])));row[index]=value;wanted['h26ck']={tuple(row)}
        for n,values in wanted.items():v[n]=lambda *a,n=n,values=values:n!=variant and normalized(a) in values
        if variant=='merged_nodes':
            v['h26cq']=lambda:'h26cp'
            for n in expected:v[n]=lambda *a:True
        if variant=='unknown':
            v['h26cl']=unknown
            try:run(d,v,(*NODES,author,'other'),('context','reference'))
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('unknown deliberative presentation')
            continue
        actual=run(d,v,(*NODES,author,'other'),('context','reference'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26cf','h245c','h237z','h26cn','h26cd'):assert v[n] is unknown
    return dict(whole_criterion_question_deliberation_metaphor_and_order=rows,
        questions_norms_enactment_and_literal_stone_not_executed=True,unknown_rejected=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=1265;clauses=[]
    for text,names,reading in (
      ('Der Probierstein ',['r5e2','r5e3','h26cm'],'法の許容性の肯否を見分ける基準。金属の品質を調べる道具への見立てを別に保持する。'),
      ('alles dessen, ',['r5ez','r5e2'],'全ての検討対象の法内容へ同じ基準を適用する。許容されると既知の案だけへ範囲を絞らない。'),
      ('was über ein Volk als Gesetz beschlossen werden kann, ',['r5ei','r5ev','r5ew','r5ex','r5ey'],'任意の同じ政治的共同体の全人民に、公的な規律として、ある主体が同じ法を正当に採択し得ること。採択主体を特定の君主に固定しない。'),
      ('liegt in der Frage: ',['r5e2','h26ck'],'基準を、同じ対象の問いの肯否を調べることに置く。物理的な位置ではない。肯定側も否定側も対応させる明示読解。'),
      ('ob ein Volk sich selbst ',['r5em','r5en','r5eu'],'同じ人民を採択主体と法の宛先の双方へ束縛して問う。現実の全員一致や直接投票を補わない。'),
      ('wohl ',['h26cl'],'可能性がはたして成り立つか、思案・吟味を促す問いの調子。答えや数値確率を付加しない。'),
      ('ein solches Gesetz ',['r5ei','r5ej','r5ez','r5et'],'判定対象と同じ法律・全条項・同じ共同体の三対象を問いにも引き継ぐ。別の許容しやすい法律へ替えない。'),
      ('auferlegen könnte?',['r5el','r5em','r5ep','r5eq','r5er','r5es','r5et','r5eu'],'同じ反事実的経過における自己賦課と規範的資格を存在量化し、その肯否を問う。現実の採択・現在の制度的権能とは区別する。')):
        assert unit['text'][cursor:cursor+len(text)]==text,(cursor,text)
        clauses.append(dict(range=[cursor,cursor+len(text)],text=text,definitions=names,reading=reading));cursor+=len(text)
    assert cursor==1436
    pages=read('data/law-enactment-reading-v1.json')['primary_pages']
    for page in pages:assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    return dict(status='legislative_touchstone_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[1265,1436],text=unit['text'][1265:1436]),selection=selection_binding(catalog(),[101]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_legislative_touchstone_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][1265:1436]),
        semantic_equivalence_automatically_proved=False,original_pages=pages,lexical_evidence=LEXICAL,
        holistic_review=[
          '原刊488頁末から489頁冒頭へ続く文を固定原文と照合した。489頁は問いを疑問符で閉じ、直後に暫定的な秩序の可能性を検討する。AA版では句点である版差を保持し、文範囲を変更しない。',
          '二度のein Volkとein solches Gesetzは同じ三対象を共有する。人民の完全な成員、非空の法の全条項、採択の内容と生起、制度的な成立、全条項の同一点での規律を既存のr5eiからr5enへ追跡した。',
          '受動的な採択の主体は存在量化し、同じ主体と同じ候補の資格・採択を結んだ。自己賦課は同じ全人民を主体へ固定する。一般主体の許容と自己主体の許容を別の関係として与え、その対応を著者の主張にするため、基準が恒真になる定義にはしていない。',
          '全検討範囲で一般立法の可能性と自己賦課の可能性の同値を述べる。「試金石」を肯否の両方を判定する基準と読む選択であり、単なる必要条件への縮小ではない。特定の主体への権限付与、対象の存在、現実の採択や全法律の正当性は付け加えない。',
          '試金石の道具側の意味と、判定基準への見立てを分けた。liegtはその基準を問いへ置く提示であり、物理的位置を補わない。wohlはその同じ問いへの思案的態度であり、回答の不確定さを実際の否定や高確率の肯定へ変えない。',
          '著者帰属は全基準内容、同じ範囲・判定性質・問い、その質問箇所、思案的な提示、道具への見立て、前文との順序を保持する。引用によって規範、採択、道具の存在や問いの答えを評価・断言しない。',
          '全語句を連続した原文範囲とNoema構成へ対応させて通読した。これは採用した読みの下でのアシスタントの意味判断であり、検査の通過から同値性を自動認定したもの、唯一の読解の証明、独立査読ではない。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,LEXICAL,*(x['path'] for x in pages),*PRIORS)})
@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:101]==old.document['statements'] and len(new.document['statements'])==102
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,indices in (('data/covenant-question-reading-v1.json',[96,97]),('data/covenant-nullity-reading-v1.json',[98]),('data/cohort-covenant-denial-reading-v1.json',[99]),('data/posterity-rights-reading-v1.json',[100])):
        assert read(p)['selection']==selection_binding(new,indices)
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=101,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=1090,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=144)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in [('permission',permission_checks),('adoption',adoption_checks),('bindings',binding_checks),('criterion',criterion_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,LEXICAL,INVENTORY,*PRIORS,*(p['path'] for p in read(READING)['original_pages']),
        'data/covenant-question-reading-v1.json','data/covenant-nullity-reading-v1.json','data/cohort-covenant-denial-reading-v1.json','data/posterity-rights-reading-v1.json',
        'scripts/compose_legislative_touchstone.py','scripts/check_legislative_touchstone.py','tests/test_legislative_touchstone.py',
        'scripts/compose_law_enactment.py','scripts/check_law_enactment.py','scripts/check_rational_self_imposition.py',
        'scripts/check_covenant_nullity.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='legislative_touchstone_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[101],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
