from copy import deepcopy
import pytest
from scripts.concept2_assembly_reader import AssemblyCodec,AssemblyDocumentReader
from scripts.concept2_assembly import assemble_call,expand_plan
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from scripts.concept2_document import empty_document
from tests.test_concept2_document import name,primitive,call,var,eq,assertion
from tests.test_concept2_sharing import both,seed


def scope(body):return dict(form='scope',quotation=True,body=body)


def check(plan,expected,codec,width=600):
    tokens=codec.encode(plan);drawing=g.layout(codec.units(tokens))[0];rows=g.fold([drawing],width);shapes=[]
    for i,row in enumerate(rows):shapes+=g.move(row['shapes'],80,80+i*170)
    reader=AssemblyCodec(codec.dictionary)
    assert reader.read_page(c.svg(shapes))['statements']==[expected]
    return tokens,rows


def test_arbitrarily_long_branch_values_keep_native_order_across_lines():
    codec=AssemblyDocumentReader(seed());values=[]
    for n in (3,8,15):
        value=call(name('aki'))
        for _ in range(n):value=call(name('book','home','round'),value)
        values.append(value)
    source=call(name('give'),*values)
    for lanes in ((-1,0,1),(1,-1,0)):
        plan=scope(assertion(assemble_call(source,codec.dictionary,lanes=lanes)))
        assert expand_plan(plan,codec.dictionary)==assertion(source)
        tokens,rows=check(plan,assertion(source),codec,width=530)
        assert len(rows)>=3
        assert ('select' if lanes==(-1,0,1) else 'branch',*lanes) in tokens


def test_header_binding_does_not_change_outer_variables_or_escape_its_scope():
    codec=AssemblyDocumentReader(seed())
    source=call(name('give'),var('va'),call(name('book','home','round'),var('va')),var('va'))
    frame=assemble_call(source,codec.dictionary,lanes=(1,-1,0))
    word=lambda s:dict(kind='call',symbol=dict(form='word',parts=codec.dictionary['selected_spellings'][s]),arguments=[])
    body=both(eq(dict(form='role-definition',lane=0,value=word(name('aki'))),word(name('aki'))),
        dict(kind='forall',variable='va',sort='individual',body=frame),
        eq(dict(form='role-use',lane=0),word(name('aki'))))
    plan=scope(assertion(body));expected=expand_plan(plan,codec.dictionary)
    check(plan,expected,codec)


def test_typed_and_quoted_payload_binders_retain_their_native_numbering():
    function=dict(kind='function',parameters=['number'],result='number')
    description=dict(kind='description',result='truth')
    seed_doc=dict(empty_document(),declarations=[primitive(name('rain'),[function,function,description],'truth')])
    codec=AssemblyDocumentReader(seed_doc)
    lam=lambda n:dict(kind='lambda',parameters=[dict(name=n,sort='number')],body=var(n))
    quote=dict(kind='quote',body=eq(dict(kind='number',numerator=1,denominator=1),dict(kind='number',numerator=1,denominator=1)))
    source=call(name('rain'),lam('va'),lam('vb'),quote)
    expected=codec.canonical_record(assertion(source))
    plan=scope(assertion(assemble_call(expected['body'],codec.dictionary)))
    check(plan,expected,codec)


def test_argument_separators_inside_header_values_are_not_header_ends():
    seed_doc=seed();seed_doc['declarations'].append(primitive(name('round'),['individual']*7,'individual'))
    codec=AssemblyDocumentReader(seed_doc)
    v=call(name('round'),*[call(name('aki'))]*7)
    source=call(name('give'),v,v,v)
    check(scope(assertion(assemble_call(source,codec.dictionary))),assertion(source),codec)


def test_nested_frames_and_unclosed_or_duplicate_header_rejection():
    seed_doc=seed();seed_doc['declarations'].append(primitive(name('round'),['individual']*2,'individual'))
    codec=AssemblyDocumentReader(seed_doc)
    inner=call(name('round'),call(name('aki')),call(name('aki')))
    source=call(name('give'),inner,call(name('aki')),call(name('aki')))
    frame=assemble_call(source,codec.dictionary)
    frame['bindings'][0]['value']=assemble_call(inner,codec.dictionary)
    plan=scope(assertion(frame));tokens,_=check(plan,assertion(source),codec)
    with pytest.raises(ValueError):codec.parse(tokens[:-1])
    duplicate=deepcopy(plan);duplicate['body']['body']['bindings'][1]['lane']=-1
    with pytest.raises(ValueError):codec.encode(duplicate)


def test_no_new_shapes_or_changes_to_accepted_alphabet():
    from scripts.concept2_document_reader import DocumentReader
    assert AssemblyDocumentReader().forms==DocumentReader().forms
