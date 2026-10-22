"""Check per-prospect grounds, finite diagnostics and unbounded-domain refusal."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_prospect_grounded_apprehension import (ROOT, LIBRARY, BASIS, OLD_LIBRARY,
    OLD_BASIS, MEANINGS, PRIMITIVES, LIMITS, DESCRIPTION, inherited, fixed_relations, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/prospect-grounded-apprehension-v1.md'
SOURCE='data/tenth-paragraph-source-reading-v1.json'
READING='data/prospect-grounded-apprehension-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
INDEX='data/semantic-review-index-v203.json'
DOMAIN=('person','other','state','second','reason','spare')
SCENES=('reference','alternate','point','later','safe','harm','doom')
FILES=('artifacts/ninth-paragraph-source-v2/page-493.jpg',
 'artifacts/tenth-paragraph-source-v1/page-494.jpg',
 'artifacts/eighth-paragraph-source-v1/kant-aa08-041.html',
 'artifacts/tenth-paragraph-source-v1/kant-aa08-042.html')

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def z(n):return 'k z'+n+'[]'
def topic(c):return json.loads(c.syntax)['symbol']
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(mode='local',restricted=False):
    d=deepcopy(catalog().document);d['statements']=[]
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r ztarget[a d] c.d ztopic[person a] e[b point[k ztarget[v person v point]]].'
    extra+='d zalias[person a] e[k ztopic[v person]].'
    extra+='d zold[person a topic '+DESCRIPTION+' reference d] e[b point[u[k rvx[v person v topic v point '+fixed_relations()+']]]].'
    if mode=='local':query='q[t[k r6es['+z('person')+' r[p ztopic] '+z('reference')+']]['+z('point')+']].'
    elif mode=='old':query='q[t[k zold['+z('person')+' r[p ztopic] '+z('reference')+']]['+z('point')+']].'
    elif mode=='all':query='q[t[k r6et['+z('person')+' '+z('reference')+']]['+z('point')+']].'
    elif mode=='quote':query='q[e[r[p r6et]][r[p r6et]]].'
    else:raise AssertionError(mode)
    d=parse(format_graph(d,'compact')+extra+query)
    if restricted:
        node=next(r for r in d['declarations'] if r['name']=='r6er')['body']
        assert node['kind']=='forall' and node['sort']['kind']=='description'
        instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
          arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=s))]) for s in ('ztopic','zalias')]
        node.clear();node.update(kind='and',arguments=instances)
        prefix=closure(d,('ztopic','zalias'));names={r['name'] for r in prefix}
        d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in names]
        d=parse(format_graph(d,'compact'))
    return d

def model(bits=(True,)*7,*,mixed=False,second=False):
    experienced,directed,aversive,anticipated,adverse,available,supports=bits
    states=('state','second') if second else ('state',)
    def future(e,t,p):
        return anticipated and t=='point' and (e,p) in ({('state','harm'),('state','doom')} if mixed else {('state','harm'),('second','doom')} if second else {('state','harm')})
    v={'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)}
    v.update(ztarget=unknown,
      h26u4=lambda p,e,t:experienced and(p,t)==('person','point') and e in states,
      h26u5=lambda e,c,t:directed and e in states and t=='point' and topic(c)=='ztopic',
      h26u6=lambda e,t:aversive and e in states and t=='point',h26u7=future,
      h26va=lambda p,r,t:adverse and(p,r)==('person','reference') and t in ('harm','doom'),
      h26vb=lambda p,r,ref,t:available and(p,r,ref,t)==('person','reason','reference','point'),
      h26vc=lambda p,r,c,ref,t,end:supports and(p,r,ref,t,end)==('person','reason','reference','point','harm') and topic(c)=='ztopic')
    return v
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown relation accepted')

@lru_cache(None)
def prospect_checks():
    d=fixture();old=fixture('old');rows={}
    for bits in product((False,True),repeat=7):
        expected=not all(bits[:5]) or all(bits[5:])
        assert run(d,model(bits))==[expected],bits
    assert run(d,model(mixed=True))==[False]
    assert run(old,model(mixed=True))==[True]
    assert run(d,model(second=True))==[False]
    v=model(mixed=True);original=v['h26vc']
    v['h26vc']=lambda p,r,c,ref,t,end:original(p,r,c,ref,t,'harm') and end in ('harm','doom')
    assert run(d,v)==[True]
    v=model(mixed=True);v['h26va']=lambda p,r,t:(p,r,t)==('person','reference','harm')
    assert run(d,v)==[True]  # An anticipated but non-adverse possibility needs no fear ground.
    v=model(mixed=True);v['h26u7']=lambda e,t,p:(e,t,p)==('state','point','harm')
    assert run(d,v)==[True]  # A merely possible unanticipated harm is outside this fear.
    v=model(second=True);v['h26u4']=lambda p,e,t:(p,e,t)==('person','state','point')
    assert run(d,v)==[True]
    for name in PRIMITIVES:
        v=model();v[name]=unknown;rejects(d,v)
    return dict(boolean_combinations=128,mixed_supported_and_unsupported_prospects=dict(old_clear=True,new_clear=False),
      different_episode_cannot_cancel=True,all_feared_prospects_supported=True,unanticipated_and_nonadverse_excluded=True,
      unexperienced_state_excluded=True,unknown_relations_rejected=True,native='All new definitions used by r6es and the original rvv execute; no deep boundaries replaced.')

@lru_cache(None)
def binding_checks():
    d=fixture();cases={}
    # Every support/availability argument must identify the same participant or setting.
    for name,expected in (
      ('h26vb',('person','reason','reference','point')),
      ('h26vc',('person','reason','ztopic','reference','point','harm'))):
        for i in range(len(expected)):
            v=model();different=list(expected)
            different[i]={'person':'other','reason':'spare','ztopic':'zalias','reference':'alternate','point':'later','harm':'doom'}[expected[i]]
            def changed(*args,different=tuple(different),name=name):
                values=list(args)
                if name=='h26vc':values[2]=topic(values[2])
                return tuple(values)==different
            v[name]=changed;assert run(d,v)==[False],(name,i)
            cases[name+':'+str(i)]=False
    for slot,new in (('person','other'),('reference','alternate'),('point','later')):
        # Keep an experienced fear at the changed setting, but grounds at the original one.
        v=model()
        if slot=='person':
            v['zperson']=lambda:'other';v['h26u4']=lambda p,e,t:(p,e,t)==('other','state','point')
            v['h26va']=lambda p,r,t:(p,r,t)==('other','reference','harm')
        elif slot=='reference':
            v['zreference']=lambda:'alternate';v['h26va']=lambda p,r,t:(p,r,t)==('person','alternate','harm')
        else:
            v['zpoint']=lambda:'later';v['h26u4']=lambda p,e,t:(p,e,t)==('person','state','later')
            v['h26u5']=lambda e,c,t:(e,t)==('state','later') and topic(c)=='ztopic'
            v['h26u6']=lambda e,t:(e,t)==('state','later')
            v['h26u7']=lambda e,t,p:(e,t,p)==('state','later','harm')
        assert run(d,v)==[False],slot
    v=model();v['h26vc']=lambda p,r,c,ref,t,end:(p,r,ref,t,end)==('person','reason','reference','point','harm') and topic(c)=='zalias'
    assert run(d,v)==[False]
    # A second reason may legitimately ground a second prospect; one universal reason is not required.
    v=model(mixed=True);v['h26vb']=lambda p,r,ref,t:(p,ref,t)==('person','reference','point') and r in ('reason','spare')
    v['h26vc']=lambda p,r,c,ref,t,end:(p,ref,t)==('person','reference','point') and topic(c)=='ztopic' and(r,end) in (('reason','harm'),('spare','doom'))
    assert run(d,v)==[True]
    return dict(argument_positions=cases,changed_person_reference_point_cannot_borrow_grounds=True,
      extensionally_equal_description_does_not_transfer_support=True,different_reasons_for_different_prospects_allowed=True)

@lru_cache(None)
def domain_checks():
    d=fixture('all',True)
    assert run(d,model())==[True] and run(d,model(mixed=True))==[False]
    v=model();v['h26u5']=lambda e,c,t:(e,t)==('state','point') and topic(c) in ('ztopic','zalias')
    assert run(d,v)==[False]  # Same extension does not give the alias a reason.
    try:run(fixture('all'),model())
    except ValueError as e:assert 'description domain' in str(e),str(e)
    else:raise AssertionError('Full description domain silently restricted')
    q=fixture('quote');v={r['name']:unknown for r in q['declarations'] if r['kind']=='primitive'}
    assert run(q,v)==[True]
    return dict(full_description_domain_refused=True,two_actual_body_instances_only=True,
      quotations_and_target_properties_not_executed=True,finite_model_not_a_universal_proof=True)

def source_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');text=u['text']
    return dict(status='tenth_paragraph_visual_collation_not_semantic_review',source_unit=u['id'],unit_sha256=u['text_sha256'],
      first_sentence=dict(range=[0,303],text=text[:303],nonblank_characters=len(''.join(text[:303].split())),facsimile_pages=[493]),
      paragraph=dict(range=[0,len(text)],nonblank_characters=len(''.join(text.split())),facsimile_pages=[493,494],
        page_break_offset=text.index('nach und nach fähiger')),
      observations=[
       '第一文Aber auch nurからnur gehorcht!まで原刊493頁内に収まる。続くSo zeigt、Ein größerer Grad、Wenn dennの各文も同頁に始まる。',
       '原刊のräson-nirt、befremdli-cher、betrach-tet、al-lemなどの行末分綴を除いて読む。字形と句読点を固定転記の意味へ追加しない。',
       '493頁本文末はhandeln、欄外のnachはキャッチワード。494頁冒頭nach und nach fähiger wirdからWürde gemäß zu behandeln. *)までがu0017の続きで、欄外語を重複させない。',
       '494頁の署名・地名日付・脚注はu0017本文の外。既存の別単位の対応を保持し、段落本文へ重複統合しない。',
       'AA VIII41–42の保存HTMLは異版対照用。固定転記のwohl...、verschaft、auszubreiten等の綴りを自動的にAAへ置換しない。'],
      evidence=[dict(path=p,url=url,sha256=digest((ROOT/p).read_bytes())) for p,url in zip(FILES,(
       'https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00533/full/full/0/default.jpg',
       'https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00534/full/full/0/default.jpg',
       'https://www.korpora.org/Kant/aa08/041.html','https://www.korpora.org/Kant/aa08/042.html'))],
      lexical_evidence=dict(url='https://www.kassiber.de/grimmschatten.htm',section='Adelung transcription, proverb paragraph',
       excerpt='Seinen eigenen Schatten fliehen, figürlich, sich ohne Ursache fürchten.',
       access='Web search/open text reconfirmed; direct HTML fetch returned HTTP 403. No complete local HTML claimed.',
       inference='理由のない恐れという関連用例。正当化の理由として候補ごとに評価することは本プロジェクトの明示的な解釈。辞書原刊未照合。'),
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,*FILES)})

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    phrase='sich nicht vor Schatten fürchtet';start=u['text'].index(phrase)
    return dict(status='per_prospect_grounded_apprehension_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[start,start+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,OLD_LIBRARY,OLD_BASIS)})

@lru_cache(None)
def structure_checks():
    c=catalog();old,meanings=inherited();assert not c.document['statements']
    for d in old['declarations']:
        assert c.entries[d['name']]['declaration']==d
        assert c.entries[d['name']]['meaning_ja']==meanings[d['name']]
    for path in (BASIS,SOURCE,READING):
        record=read(path);validate_hashes(ROOT,record.get('source_sha256',record.get('import_source_sha256',{})))
    assert read(SOURCE)==source_record() and read(READING)==reading_record()
    assert read(SOURCE)['first_sentence']['nonblank_characters']==257
    assert read(SOURCE)['paragraph']['nonblank_characters']==992
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for n in MEANINGS:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_four_definitions_unchanged=True,
      source_hashes_valid=True,notation_roundtrips=True,new_minimum_quote_ranks={n:0 for n in MEANINGS},new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,encoded(source_record()))
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={n:f() for n,f in (('prospects',prospect_checks),('bindings',binding_checks),('domain',domain_checks),('structure',structure_checks))}
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,SOURCE,READING,INVENTORY,INDEX,OLD_LIBRARY,OLD_BASIS,*FILES,
      'scripts/compose_prospect_grounded_apprehension.py','scripts/check_prospect_grounded_apprehension.py','tests/test_prospect_grounded_apprehension.py',
      'scripts/compose_supported_apprehension.py','scripts/compose_described_apprehension.py','scripts/compose_grounded_step.py',
      'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='per_prospect_grounding_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
