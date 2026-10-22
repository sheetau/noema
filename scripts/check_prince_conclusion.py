"""Check native individual attainment, shared merit and nonfactive emphasis."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_prince_conclusion import ROOT,LIBRARY,BASIS,PROFILE,RESPONSE,GROUND,STANDARD,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts import check_qualified_prince_frame as frame
from scripts import check_judgment_performance_quality as quality
from scripts.check_motive_causes import unknown
from scripts.check_pastoral_roles import evaluate

DOC='docs/prince-conclusion-v1.md';READING='data/prince-conclusion-reading-v1.json'
REPORT='reports/prince-conclusion-v1.json';INVENTORY=frame.INVENTORY;INDEX=frame.INDEX
PRIORS=('reports/qualified-prince-frame-v1.json','reports/religious-collective-assessment-v1.json','reports/judgment-performance-quality-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/eighth-paragraph-source-v1/kant-aa08-041.html')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,mode='discourse'):
    d=deepcopy(catalog().document);extra='';ds=[]
    if mode=='native':
        extra=quality.prior.prior.EXTRA+quality.prior.REFERENCES
        replacements={
            'h26kb':'r zone[] a.r ztwo[] a.r zchoose[a i[a] i[a]] i[a].d h26kb[matter a reference d] i[a][k zchoose[v matter r[k zone[]] r[k ztwo[]]]].',
            'h223h':'r zqualitycontext[] d.d h223h[point d] i[d][r[k zqualitycontext[]]].'}
        for x in d['declarations']:
            if x['name'] in replacements:
                replacement=parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+replacements[x['name']])['declarations'][len(ds):]
                ds.extend(replacement)
            else:ds.append(x)
        d['declarations']=ds
        for declaration in ('r zone[] a.','r ztwo[] a.','r zchoose[a i[a] i[a]] i[a].','r zqualitycontext[] d.'):extra=extra.replace(declaration,'')
    elif mode=='merit':
        extra=frame.self_report.prior.EXTRA
        extra+='r zability[a d] c.r zqualified[a d] c.r zground[a d] c.r zperformed[a a a d] c.'
        extra+='r zcriterion[a '+RESPONSE+' '+GROUND+' d] c.r zsecond[a '+RESPONSE+' '+GROUND+' d] c.'
        extra+='d zresponse[] h[a a a] e[i[speaker a activity a subject a][b point[k zperformed[v speaker v activity v subject v point]]]].'
        extra+='d zgrounded[] h[a] e[i[subject a][b point[k zground[v subject v point]]]].'
        for n,relation in (('zstandard','zcriterion'),('zotherstandard','zsecond')):
            extra+='d '+n+'[] '+STANDARD+'[i[subject a response '+RESPONSE+' ground '+GROUND+'][b point[k '+relation+'[v subject v response v ground v point]]]].'
        for x in d['declarations']:
            if x['name'] in ('r5xv','r5xj'):
                relation='zability' if x['name']=='r5xv' else 'zqualified'
                prefix=parse('p:r '+relation+'[a d] c.d zstub[] h[a] e[i[actor a][b point[k '+relation+'[v actor v point]]]].')
                ds.append(prefix['declarations'][0]);x['body']=prefix['declarations'][1]['body']
        d['declarations']=ds+d['declarations']
        for relation in ('zability','zqualified'):
            if any(x['name']==relation for x in ds):extra=extra.replace('r '+relation+'[a d] c.','')
    else:
        extra=frame.self_report.prior.EXTRA+frame.self_report.prior.PROVIDERS+frame.self_report.PROVIDERS
        extra+='r zsavequalified['+PROFILE+'] c.r zsaveenlightened['+PROFILE+'] c.'
        prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e','h26nh')}
        additions=[x for x in prefix['declarations'] if x['name'] not in replacements]
        d['declarations']=additions+[replacements.get(x['name'],x) for x in d['declarations']]
        roots=(*roots,*(x['name'] for x in additions));extra=''
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)

def run(d,v,domain=frame.DOMAIN,scenes=frame.SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=frame.DOMAIN,scenes=frame.SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown input accepted')

@lru_cache(None)
def ability_checks():
    direct='k r5xv[k ztopic[] k zanchor[]]';quoted='s[k r5xw[r[k ztopic[]] r[k zanchor[]]]]'
    d=fixture(('r5xv','r5xw'),''.join('q[t[c['+f+'][k zperson[]]][k zcontext[]]].' for f in (direct,quoted)),'native');rows={}
    for variant in ('baseline','quality_failure','unqualified_profile','wrong_reference','wrong_standard_context','nonreligious','empty_matters','guided','wrong_person'):
        v=quality.ability_model(d,variant)
        v.update(h26j7=lambda topic,r:variant!='nonreligious' and (topic,r)==('one','now'),h26ka=v['ztopics'])
        if variant=='empty_matters':v['h26ka']=lambda *a:False
        if variant=='guided':v['ad']=lambda *a:True
        if variant=='wrong_person':v['zperson']=lambda:'other'
        got=run(d,v,quality.prior.DOMAIN,quality.prior.SCENES);assert got==[variant=='baseline']*2,(variant,got);rows[variant]=got
    for n in ('h26ka','h26j7','h26j4','hzuq','ae','ad'):
        v=quality.ability_model(d);v.update(h26j7=lambda t,r:(t,r)==('one','now'),h26ka=v['ztopics']);v[n]=unknown
        rejects(d,v,quality.prior.DOMAIN,quality.prior.SCENES)
    return dict(native_scope_reference_quality_and_standing_ability=rows,unknown_rejected=True,
        direct_and_rank_seven_dequotation_agree=True,
        boundary='Native h223h returns the fixed quality-context name, checked against the anchor; native h26kb selects the same two matter names. No ability profile is stubbed in this test.')

REPLY='r[k zresponse[]]';GROUND_CODE='r[k zgrounded[]]'
STANDARDS='l['+STANDARD+'][k zstandard[] k zotherstandard[]]'
MERIT_ARGS=REPLY+' '+GROUND_CODE+' '+STANDARDS

def merit_model(d,ability=True,ground=True,first=True,second=True,qualified=True):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*frame.DOMAIN,*frame.SCENES)})
    v.update(zability=lambda p,s:ability and (p,s)==('actor','now'),zqualified=lambda p,s:qualified and (p,s)==('actor','now'),
        zground=lambda p,s:ground and (p,s)==('actor','now'))
    def criterion(p,r,g,s,ok):
        return ok and (p,s)==('actor','now') and json.loads(r.syntax)==dict(kind='call',symbol='zresponse',arguments=[]) and json.loads(g.syntax)==dict(kind='call',symbol='zgrounded',arguments=[])
    v.update(zcriterion=lambda *a:criterion(*a,first),zsecond=lambda *a:criterion(*a,second))
    return v

@lru_cache(None)
def merit_checks():
    call='k r5xx['+frame.z('topic')+' '+frame.REF+' '+MERIT_ARGS+']'
    q='q[t[c['+call+']['+frame.ACTOR+']]['+frame.NOW+']].'
    d=fixture(('r5xx',),q,'merit');rows=[]
    for bits in product((False,True),repeat=4):
        v=merit_model(d,*bits);got=run(d,v);assert got==[all(bits)],(bits,got);assert v['zperformed'] is unknown;rows.append(dict(inputs=bits,result=got[0]))
    for name in ('zability','zground','zcriterion','zsecond'):
        v=merit_model(d);v[name]=unknown;rejects(d,v)
    for name in ('zability','zground'):
        v=merit_model(d);v[name]=lambda p,s:(p,s)==('person','now');assert run(d,v)==[False]
    empty=fixture(('r5xx',),q.replace(STANDARDS,'l['+STANDARD+'][]'),'merit');assert run(empty,merit_model(empty))==[False]
    wrong=fixture(('r5xx',),q.replace(REPLY,'r[i[speaker a activity a subject a][b point[e[v subject][v subject]]]]'),'merit')
    assert run(wrong,merit_model(wrong))==[False]
    # Fixed settings use actual members of this small domain; role binding was
    # evaluated natively in the pinned qualified-prince report.
    args=' '.join([frame.ACTOR]*8+[frame.REF])
    general=fixture(('r5xy',),'q[t[k r5xy['+args+' '+MERIT_ARGS+']]['+frame.NOW+']].','merit')
    for qualified,ability,ground in product((False,True),repeat=3):
        got=run(general,merit_model(general,ability,ground,qualified=qualified),('actor','person'))
        assert got==[not qualified or (ability and ground)],(qualified,ability,ground,got)
    return dict(sixteen_conjunction_cases=rows,nonempty_all_criteria_same_response_and_ground=True,
        shared_subject_and_point=True,general_condition_eight_cases=True,no_actual_response_execution=True,unknown_rejected=True,
        boundary='Only qualification and ability truth boundaries are replaced here; ro5, its actual ground, all criteria and universal quantification execute natively. This does not validate still-unspecified praise/merit criteria.')

ENLIGHT='k r5xw[r['+frame.z('topic')+'] r['+frame.REF+']]'
SAVE='q[k zsavequalified['+frame.PCODES['qualified']+']].q[k zsaveenlightened['+ENLIGHT+']].'
DISC=' '.join(frame.z(n) for n in ('event','otherperson','actor','group'))+' '+frame.ARGS+' '+frame.z('otherpoint')
def discourse_model(d):
    v,saved=frame.base(d)
    for n in list(v):
        if n.startswith('h26') or n in ('cf','hzwn','hzxf','fa','aa'):v[n]=unknown
    v.update(zsavequalified=lambda c:saved.update(qualified=frame.identity(c)) is None,
        zsaveenlightened=lambda c:saved.update(enlightened=frame.identity(c)) is None)
    v['h26no']=lambda node,author,scope,b,p,c:(node,author,scope,frame.identity(b),frame.identity(p),c)==('otherperson','actor','group',saved['qualified'],saved['enlightened'],'otherpoint')
    v['h26nq']=lambda node,author,scope,clause,b,p,c:(node,author,scope,clause,frame.identity(b),frame.identity(p),c)==('event','actor','group','otherperson',saved['qualified'],saved['enlightened'],'otherpoint')
    return v,saved

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5xq','r5xw','r5x3'),SAVE+'q[k r5x3['+DISC+']].');v,_=discourse_model(d);assert run(d,v)==[True]*3
    for name,size in (('h26no',6),('h26nq',7)):
        v,_=discourse_model(d);v[name]=unknown;rejects(d,v)
        for pos in range(size):
            v,_=discourse_model(d);old=v[name]
            def changed(*a):
                b=list(a);b[pos]=frame.z('person') if pos not in ((3,4) if name=='h26no' else (4,5)) else a[pos-1 if pos==(4 if name=='h26no' else 5) else pos+1]
                return old(*b)
            v[name]=changed;assert run(d,v)==[True,True,False],(name,pos)
    for name in frame.NAMES:
        v,_=discourse_model(d)
        if name=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[frame.SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[frame.DOMAIN.index('person' if item==name else item)]
        assert run(d,v)==[True,True,False],name
    return dict(thirteen_presentation_arguments_checked=True,all_nine_closed_references_checked=True,
        complete_qualification_boundary=True,emphatic_subject_distinct_from_scalar_object=True,unknown_rejected=True,no_world_content_executed=True)

def reading_record():
    units={u['id']:u for u in read(INVENTORY)['units']};u=units['kant-1784:u0015'];start=u['text'].index('ist selbst');end=u['text'].index(' von der dankbaren')
    return dict(status='individual_attainment_and_open_merit_dependency',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,context_units={n:units[n]['text_sha256'] for n in ('kant-1784:u0014','kant-1784:u0016')},
        integration_requirements=[
            dict(part='gepriesen als derjenige',reuse=['ro7','roa','hzgb'],missing='肯定的報告と区別した強い肯定的評価の表明。同じ対象の解放功績を称揚する内容。'),
            dict(part='verdient',reuse=['ro5','r5xx','r5xy'],missing='具体的な功績内容とその功績にこの応答がふさわしいという全適用基準。実行と義務は含めない。'),
            dict(part='dankbaren',reuse=['roo','ror','rot','rov'],missing='間接的・共同の恩恵の認識と、その行為者へ向く好意的承認。認識や称賛の同時成立だけで感謝にしない。'),
            dict(part='Welt und Nachwelt',reuse=['roj','rok','hzgi'],missing='現在と後代の人々の全範囲。片側だけを選ぶhzgjの選言で両側からの適合を代替しない。未来の実演を断言しない。'),
            dict(part='zuerst ... entschlug',reuse=['rod','hzge','roi'],missing='同じ人類、政府側の妨げからの離脱、実現への寄与、比較履歴内の最初の達成。全員の内面の能力取得と混同しない。'),
            dict(part='Jedem ... Gewissensangelegenheit',reuse=['r5v7','r5s6'],missing='良心が判断する全事項・各本人の理性使用を自由にする内容。宗教事項だけへ無条件に縮めない。'),
        ],whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements']
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,new_verified_characters=0,
        compact_full_v2_roundtrips=True,parent_meanings_unchanged=True,pinned_prior_evidence_valid=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('ability',ability_checks),('merit',merit_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_prince_conclusion.py','scripts/check_prince_conclusion.py','tests/test_prince_conclusion.py',
        'scripts/check_qualified_prince_frame.py','scripts/check_self_report_dignity.py','scripts/check_designation_rejection.py',
        'scripts/check_religious_freedom_policy.py','scripts/check_judgment_performance_quality.py','scripts/check_qualified_judgment.py',
        'scripts/check_topical_standing.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='individual_attainment_and_shared_merit_scaffold_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
