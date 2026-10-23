"""Check and explicitly review the first sentence of the two-frame measurement."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_material_relative_frame import RS,FS
from scripts.check_rod_methods import value
from scripts.compose_measured_space_sentence import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,COORDINATES,LIMITS,build

DOC='docs/measured-space-sentence-v1.md';SOURCE='data/einstein-measured-space-source-reading-v1.json'
READING='data/einstein-measured-space-sentence-reading-v1.json';SOURCE_PARENT='data/einstein-spatial-coverage-source-reading-v1.json'
PRIOR='data/einstein-parallel-choice-review-v1.json'
DEPENDENCIES=('reports/spatial-coverage-v1.json','reports/coordinate-measurement-v1.json','reports/axis-projection-v1.json','reports/parallel-choice-v1.json','reports/frame-instruments-v1.json')
DOMAIN=('frame','moving','restrod','movingrod','history','place','point','x','y','z','lengthunit','timeunit','author','paper','section','motionnode','previousnode','node','Kname','kname','xname','yname','zname','xiname','etaname','zetaname')
POINTS=('context','initial','discourse','other')

def forbidden(*xs):raise ValueError('Unknown measured-space input')
def constants():
    mapping={'ra':'frame','zbm':'moving','zcj':'history','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','zb4':'initial','zb6':'context','ri':'discourse','rd':'author','eirf':'paper','eisms':'section','zcg':'motionnode','zco':'previousnode','zc2':'node','eisnb':'Kname','eisna':'kname'}
    mapping.update(dict(zip((r[0] for r in COORDINATES),('xname','yname','zname','xiname','etaname','zetaname'))))
    return {n:lambda x=x:x for n,x in mapping.items()}

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eivf','eivg','eivl','eiwn','eixs','eipw','eigy','eivv','eixq'}
    if name=='eix3':boundaries.add('eixt')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jms'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmscontent',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmscontent',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jmscontent',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown measured-space' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                wrong=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{wrong}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def setting_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    families={a:FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:c(Q(i+(1 if p=='point' else 0))))) for i,a in enumerate(('x','y','z'))}
    members=FunctionValue(('individual',),'truth',lambda p:p=='point')
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in ('point','place') for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    hist=norm(['restrod','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*families.values()])
    rows={'eivf':{('frame','initial'),('moving','initial')},'eivg':{('frame','moving','initial')},'eivl':{('frame','moving','initial')},'eiwn':{('history',)},'eixs':{('context',)},'eipw':{('restrod','frame','context'),('movingrod','moving','context')},'eigy':{hist},'eivv':{('movingrod','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def family(body,frame,lu,tu,axis,ctx):
        if (body,frame,lu,tu,ctx)!=('restrod','frame','lengthunit','timeunit','context') or axis not in families:forbidden()
        return families[axis]
    m|={'zci':lambda h:'context','zby':lambda frame,ctx:'restrod' if frame=='frame' else 'movingrod','eirh':lambda b,p,ctx:(b,p,ctx)==('restrod','point','context'),'eislu':family,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2))}
    check=lambda mm:run('eixt',['context'],mm);count=perturb(check,m,rows,norm)
    assert not check(m|{'zci':lambda h:'other'});count+=1
    # The rest-side rod is not replaced by the comoving rod, nor its frame by K.
    assert not check(m|{'eipw':relation({('restrod','frame','context'),('movingrod','frame','context')})});count+=1
    unknowns(check,m,('zby','zci','eirh','eislu','eisls','eislt'))
    count+=perturb(lambda mm:run('eix3',[],mm),{'eixt':relation({('context',)})},{'eixt':{('context',)}})
    return dict(cases=count,initial_configuration_same_selected_parallel_history_and_all_measurements=True,rest_ruler_and_comoving_ruler_have_distinct_frame_conditions=True,physical_construction_is_closed_quoted_content=True)

@lru_cache(None)
def coordinate_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    values={('frame','x'):Q(2),('frame','y'):Q(3),('frame','z'):Q(4),('moving','x'):Q(-5),('moving','y'):Q(6),('moving','z'):Q(7)}
    def selected(place,frame,role,unit,ctx):
        if (place,unit,ctx)!=('place','lengthunit','context') or (frame,role) not in values:forbidden()
        return c(values[frame,role])
    rows={'eixq':{('place',f,a,'context') for f,a in values}}
    m|={'zcy':selected,'eixq':relation(rows['eixq'])}
    frames={'ra':'frame','zbm':'moving'};roles={'yn':'x','yo':'y','yp':'z'}
    for sign,printed,rule,f,a in COORDINATES:
        frame,axis=frames[f],roles[a];number=values[frame,axis]
        assert run(rule,['place',c(number),'context'],m);count+=1
        assert not run(rule,['place',c(number+1),'context'],m);count+=1
        row=('place',frame,axis,'context')
        assert not run(rule,['place',c(number),'context'],m|{'eixq':relation(rows['eixq']-{row})});count+=1
        unknowns(lambda mm:run(rule,['place',c(number),'context'],mm),m,('zcy','eixq','ba','sca'))
    args=['place','moving','y',c(Q(6)),'context'];norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    count+=perturb(lambda mm:run('eixu',args,mm),m,{'eixq':{('place','moving','y','context')}},norm)
    return dict(cases=count,all_six_symbols_bound_to_exact_frame_and_axis=True,negative_and_unequal_cross_frame_coordinates_allowed=True,measured_unique_value_required_not_candidate_label_alone=True)

def notation_rows():
    names=('xname','yname','zname','xiname','etaname','zetaname')
    return {'eislo':{(name,rule,'paper','discourse') for name,(_,_,rule,_,_) in zip(names,COORDINATES)},'eisd4':{('node','author','Kname','frame','paper','discourse'),('node','author','kname','moving','paper','discourse')}}

@lru_cache(None)
def presentation_checks():
    rows=notation_rows();m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eix4',[],mm),m,rows)
    assert run('eix4',[],m|{n:forbidden for n in ('eixu','eixq','zcy','eixt')});count+=1
    rows=notation_rows()|{'eislz':{('node','author','eix3','section','discourse')},'ug':{('node','author','eix3','section','discourse')},'zao':{('motionnode','node','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eix5',[],mm),m,rows)
    assert run('eix5',[],m|{n:forbidden for n in ('eixt','eix3','eiwn','eixs','eivv','eisnc','eism4')});count+=1
    rows={'eir3':{('node','author','paper','eix6','discourse')},'ue':{('previousnode','node','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eix7',[],mm),m,rows)
    assert run('eix7',[],m|{n:forbidden for n in ('eislz','ug','zao','eixt','eix3','eix5','eisnc')});count+=1
    return dict(cases=count,thought_setting_and_adoption_in_same_scope=True,source_presentation_not_command_or_actual_measurement_report=True,quoted_rules_and_physical_content_not_executed_by_attribution=True)

def source_record():
    old=json.loads(read(SOURCE_PARENT));validate_hashes(ROOT,old['source_sha256'])
    assert old['range']==[0,240] and old['source_nonblank_characters']==176
    assert old['text']=='Wir denken uns nun den Raum sowohl vom ruhenden System [M0075] aus mittels des ruhenden Maßstabes als auch vom bewegten System [M0076] mittels des mit ihm bewegten Maßstabes ausgemessen und so die Koordinaten [M0077] bez. [M0078] ermittelt.'
    result=deepcopy(old);result.update(version='einstein-measured-space-source-reading-v1',reviewer='assistant_sentence_rereading_using_preserved_visual_collation')
    result['math']=[m for m in old['math'] if m['id'] in ('M0075','M0076','M0077','M0078')]
    result['observations']=['Wir denken unsは著者の想定行為で、ausgemessen/ermitteltの完了した配置を内容とする。','sowohl/als auchとbez.はKでx,y,z、kでξ,η,ζを得る二組の対応である。','静止側の物差しと移動系に同伴する同じ物差しをそれぞれの基準系へ結ぶ。','soはその同じ空間測定による座標取得であり、独立の測定や値の等置ではない。']
    result['remaining']=['第二文の時計配置点の時刻設定、§1の光信号手順、追加指示とt/τ','u0045全体の意味判断']
    paths=set(old['source_sha256'])|{SOURCE_PARENT,DOC};result['source_sha256']={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};return result

CLAUSES=(
 ('Wir denken uns nun ',['eix5','eix6','eix7'],'著者の声が同じ論考で測定済みの配置を今想定し採用するという提示。命令・実験報告・単なる可能性へ替えない。'),
 ('den Raum sowohl vom ruhenden System [M0075] aus ',['eixt','eixs','eixr','eixn'],'既出の静止系Kを第一側とし、同じ全空間の地点・三成分を漏れなく対象とする。'),
 ('mittels des ruhenden Maßstabes ',['eixt','eixd','eixe','eixg'],'初期と同じK側の物差しの静止・剛性・校正と、同じ方法での実測を保持する。'),
 ('als auch vom bewegten System [M0076] ',['eixt','eiwn','eixs','eixr'],'同じ運動系kを第二側とし、前段の同じ運動候補を想定内容の中で選ぶ。許容から実現を推論しない。'),
 ('mittels des mit ihm bewegten Maßstabes ',['eixt','eivv','eipw','eixg'],'同じk側の物差しがKに対して既出の運動に同伴し、k自身では静止する。別の道具やK側の静止を代用しない。'),
 ('ausgemessen und so ',['eix3','eixs','eixn','eixp','eixq'],'同じ空間について測定され値が得られた配置を想定する。個々の測定配置で対象の位置と軸・尺度を保ち、取得値を同じ実測の存在と全有効候補の一意性へ結ぶ。'),
 ('die Koordinaten [M0077] bez. [M0078] ermittelt.',['eixu','eixv','eixw','eixx','eixy','eixz','eix2','eix4'],'Kのx,y,zとkのξ,η,ζをそれぞれの第一・第二・第三役割へ結ぶ。負・零の座標を許し、両系の値の一致や同じ原点・正方向を加えない。'),
)

@lru_cache(None)
def reading_record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);offset=0;clauses=[]
    for text,symbols,reason in CLAUSES:
        assert source['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==240
    paths=set(build())|set(catalog.source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_measured_space_sentence.py','scripts/check_measured_space_sentence.py','tests/test_measured_space_sentence.py'}
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    return dict(schema_version='noema-sentence-reading-1',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],text=source['text']),selection=selection_binding(catalog,[INDEX]),clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_measured_space_sentence',whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=176,semantic_equivalence_automatically_proved=False,holistic_review=['第一文全体を前段の初期計器・運動設定・仮定採用の権原と、後続の時刻設定に照らして通読した。思考上の構成として測定済みの空間を置く声、両系それぞれの同じ物差しの静止・同伴、全地点と三成分の実測、soによる同じ測定と座標取得、bez.による六記号の二組の対応を保持したと判断する。','射影・校正・配置の保存・値の一意性は明示した操作的読解である。原文に測定アルゴリズムが逐語的に記されているとはせず、同義性の自動証明又は物理的実現の証明にもしていない。第一文の判断を第二文やu0045全体の完了へ加算しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==271
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[268,269])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);oldann=json.loads(read('data/spatial-coverage-identifiers-v1.json'))['entries'];assert json.loads(read(ANNOTATIONS))['entries'][:len(oldann)]==oldann
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==1 and ds['eix6']['body']['force']=='assert'
    assert all(not ds[n]['parameters'] and ds[n]['result']=='individual' for n in PRIMITIVES)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();assert json.loads(read(READING))==reading_record()
    return dict(new_definitions=len(MEANINGS),new_designation_primitives=6,new_relation_primitives=0,preserved_statements=270,added_statements=1,prior_meanings_and_reviews_preserved=True,whole_sentence_completion=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('setting',setting_checks),('coordinates',coordinate_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(reading_record()['source_sha256'])|{READING,'scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_rod_methods.py','scripts/check_tau_differential.py','scripts/compose_spatial_coverage.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='measured_space_sentence_checked_and_reviewed',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},whole_sentence_semantically_verified=True,newly_reviewed_sentence_characters=176,semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
