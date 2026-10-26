from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_two_principles as check
from scripts import two_principles_profile as profile
from scripts.light_speed_time_profile import LightSpeedTimeVocabulary
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def ask(body):return dict(kind='ask',body=body)
def apply(fn,n=0):return dict(kind='apply',function=fn,arguments=[check.author.num(n)])
def domain():return tuple(set(check.BASE.values())|{'other','setting','frame'})


def test_profile_preserves_previous_meanings_and_reuses_newtonian_frames():
    old=LightSpeedTimeVocabulary();new=check.vocabulary()
    assert len(old._words)==579 and len(new._words)==632
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert profile.REUSED=={'newtonianframe'}
    assert new._symbols['newtonianframe']==old._symbols['newtonianframe']
    assert len(profile.FIELD_CONTRACTS)==12 and len(profile.ALL_CONTRACTS)==53


def test_visible_document_and_backprojection_preserve_all_source_bodies():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:32]==old['statements']
    assert len(doc['statements'])==40 and len(check.source_excerpt()['declarations'])==206
    assert check.backprojection(doc)==check.source_excerpt()


def test_actual_paragraphs_keep_second_principle_distinct_from_its_speed_explanation():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['sentence_positions']==dict(wu=[16,1],vk=[17,1],wt=[18,1],eisll=[18,2])
    assert b['source_statement_indices']==list(range(83,88)) and len(b['source_units'])==6
    eq=b['equation_attachment'];assert eq['one_sentence'] and eq['paragraph']==18
    a,z=eq['first_unit_range'];assert b['source_units']['einstein-1905:u0026']['text'][a:z]=='Hierbei ist'
    assert eq['math']['definition']=='eiov' and eq['math']['id']=='M0042'
    assert b['heading_positions']==dict(firstpartheading=1,eisk2=3)


def test_outer_attribution_preserves_every_context_and_relation():
    rows=check.diagnostics();assert len(rows)==18 and rows[0]['values']==[True]*5
    assert all(not all(r['values']) for r in rows[1:])


def test_divisions_following_scope_axes_and_designations_bind_without_executing_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
    for old in (*check.ROLE_ASSIGNMENTS,*check.HEADINGS,*check.DESIGNATIONS,*check.AXES):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        h['expected']=lambda old=old:check.BASE[old]
        assert evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)[0]['value']
        h['expected']=lambda:'other'
        assert not evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)[0]['value']


@pytest.mark.parametrize('field',range(4))
def test_division_and_following_references_reject_each_unknown_key(field):
    doc=deepcopy(check.document());n=check.names()
    for old,(node,_) in check.ROLE_ASSIGNMENTS.items():
        roles=check.role_model(check.BASE)
        key=(check.BASE['eirf'],check.BASE[node],check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.BASE['ri'])
        value=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=value
        doc['statements']=[ask(op('equal',call(n[old]),call(n[old])))]
        h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,roles).items()})
        with pytest.raises(ValueError,match='Unknown temporal reference'):
            evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)


def test_native_segment_fields_preserve_every_slot_and_segment_identity():
    # Two distinguishing segments, varying one component at a time: binding diagnostics.
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result='individual') for n in ('x','y')]
    entities=list(check.FIELDS)[:9];readings=list(check.FIELDS)[9:]
    doc['statements']=[ask(op('equal',call(m[old],call(t)),call('y'))) for t in ('x','y') for old in entities]
    doc['statements'] += [ask(apply(call(m[old],call(t)))) for t in ('x','y') for old in readings]
    for changed in (None,*range(12)):
        row=['x']*9;cuts=[cut(0) for _ in range(3)]
        if changed is not None:
            if changed<9:row[changed]='y'
            else:cuts[changed-9]=cut(1)
        model=profile.PrincipleRecords(entities={'x':row,'y':['y']*9},readings={'x':cuts,'y':[cut(1)]*3})
        h=handlers(doc)|dict(x=lambda:'x',y=lambda:'y')
        h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
        assert [r['value'] for r in evaluate_document(doc,individuals=('x','y'),situations=('s',),primitives=h)]==[
            *[changed==i for i in range(9)],*[True]*9,*[changed==i for i in range(9,12)],*[True]*3]


def test_native_division_roles_keep_heading_parent_depth_number_and_following_boundary():
    doc=deepcopy(check.document());n=check.names();m=check.mapping()
    doc['declarations'] += [dict(kind='primitive',name='candidate',parameters=[],result='individual'),
                            dict(kind='primitive',name='context',parameters=[],result='situation')]
    expected=dict(eisdx=('firstpartheading','eisdx','doc','doc',1,1,'body'),
        eisdy=('firstsectionheading','eisdy','eisdx','doc',2,1,'body'),
        eiskz=('eisk2','eiskz','eisdx','doc',2,2,'body'),wv=('wv','doc','wu','body'))
    for old,role in check.reference_roles().items():
        doc['statements']=[ask(call(role,call('candidate'),call('context')))]
        for candidate,context in [(old,'body'),('other','body'),(old,'front')]:
            seen=[]
            def relation(*args):
                seen.append(args);return args==expected[old]
            h=handlers(doc)|dict(candidate=lambda:candidate,context=lambda:context)
            h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
            h[m['eisci' if old=='wv' else 'eisdv']]=relation
            assert evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)[0]['value']==(candidate==old and context=='body')
            assert len(seen)==1
            row=list(expected[old]);row[0 if old=='wv' else 1]=candidate;row[-1]=context
            assert seen[0]==tuple(row)


@pytest.mark.parametrize('name,kwargs,key',[
    ('comparisonlengthunit','lengthunits',('f','g','s')),
    ('comparisontimeunit','timeunits',('f','g','s')),
    ('commonvelocity','velocities',('f','g','l','t','a','s')),
    ('momentreading','moments',('m','f','t','s')),
    ('pointcoordinate','coordinates',('p','m','f','l','a','s'))])
def test_coordinate_candidate_records_bind_every_frame_unit_point_time_axis_and_context(name,kwargs,key):
    value='u' if kwargs.endswith('units') else cut(1)
    h=profile.PrincipleRecords(**{kwargs:{key:value}}).handlers()[name]
    assert h(*key) is value
    for i in range(len(key)):
        bad=list(key);bad[i]='other'
        with pytest.raises(ValueError,match='Unknown principle record'):h(*bad)


def test_record_shapes_slots_and_cut_types_reject_unknown_inputs_and_copy_rows():
    row=list('abcdefghi');h=profile.PrincipleRecords(entities={'r':row},readings={'r':[cut(i) for i in range(3)]},axes={('f','s'):['x','y','z']}).handlers()
    row[0]='changed';assert h['segmententity']('r',0)=='a'
    for n in range(3):assert h['frameaxisreference']('f',Fraction(n+1),'s')=='xyz'[n]
    for name,args,base,size in [('segmententity',['r'],0,9),('segmentreading',['r'],0,3),('frameaxisreference',['f'],1,3)]:
        for slot in (True,0.0,Fraction(1,2),base-1,base+size):
            with pytest.raises(ValueError,match='principle slot'):h[name](*args,slot,*(['s'] if name=='frameaxisreference' else []))
        with pytest.raises(ValueError,match='Unknown principle record'):h[name]('unknown',base,*(['s'] if name=='frameaxisreference' else []))
    with pytest.raises(ValueError,match='Unknown principle record'):h['frameaxisreference']('f',1,'other')
    for kwargs in ({'entities':{'x':['a']*8}},{'readings':{'x':[cut(1)]*2}},{'axes':{('f','s'):['x','y']}},
                   {'readings':{'x':[cut(1),False,cut(1)]}},{'coordinates':{('p','m','f','l','a','s'):FunctionValue(('individual',),'truth',forbidden)}}):
        with pytest.raises(ValueError):profile.PrincipleRecords(**kwargs)


def test_changed_quantifier_motion_speed_scope_or_forwarding_cannot_reuse_evidence():
    for old in ('eion','eiom','eioj','eiot','eiov','eiow','wv','eisdy','yn','wf','wq','principlerolepart'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
