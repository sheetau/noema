from copy import deepcopy
from itertools import permutations, product
import pytest

from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.check_visible_syntax import (vocabulary,named,call,variable,num,logic,quant,quote,doc,
                                         assertion,integrated_document,specimens,semantic_contrasts)
from scripts.visible_syntax import (Writer,Reader,compile_document,decode_document,to_svg,from_svg,
                                   END,END_GLYPH,MAX_BITS)
from scripts.visible_syntax_geometry import render,recognize
from scripts.visible_syntax_vocabulary import Vocabulary, family_glyph, modifier_glyph
from scripts.visible_word_forms import Word,symbol
from scripts.visible_lexical_script import _shape_set,_translate,_glyph,check_extension,Lexicon
from scripts.balanced_circle_script import LARGE,MEDIUM,SMALL,PITCH,line,circle


def roundtrip(document,**layout):
    shapes=compile_document(document,vocabulary(),**layout)['shapes']
    assert decode_document(from_svg(to_svg(shapes)),vocabulary())==normalize_document(document)
    return shapes


def raw(writer): return Reader([_shape_set(g['shapes']) for g in writer.glyphs],vocabulary())


def test_integrated_document_contains_visible_definition_types_numbers_quotes_and_scopes():
    d=integrated_document()
    assert len(d['declarations'])==3 and len(d['statements'])==4
    roundtrip(d)
    for entry in specimens(): assert decode_document(from_svg(entry['svg']))==entry['document']
    assert len({_shape_set(e['compiled']['shapes']) for e in specimens()[:3]})==3


def test_public_extension_preserves_old_forms_and_registry_order_is_irrelevant():
    check_extension(Lexicon(),vocabulary())
    v=vocabulary().document(); v['entries']=dict(reversed(list(v['entries'].items())))
    other=Vocabulary(v)
    entry=specimens()[0]
    assert compile_document(entry['document'],other)==entry['compiled']
    assert decode_document(entry['compiled']['shapes'],other)==entry['document']


@pytest.mark.parametrize('order',list(permutations(('aki','nao','book'))))
def test_every_argument_of_three_place_relation_is_preserved(order):
    d=doc(assertion(call('give',*(call(n) for n in order))),roots=('give','aki','nao','book'))
    restored=decode_document(roundtrip(d))
    # Vary one position at a time over a two-value diagnostic domain. These
    # are argument-binding diagnostics, not a full-domain semantic proof.
    for slot in range(3):
        for bit in (0,1):
            objects={n:0 for n in order}; objects[order[slot]]=bit
            prim={named(n):(lambda n=n:objects[n]) for n in order}
            prim[named('give')]=lambda *args:args[slot]==1
            result=evaluate_document(restored,individuals=(0,1),situations=('now',),primitives=prim)
            assert result[0]['value']==bool(bit)


def test_negation_scope_has_distinguishing_two_value_models():
    rows=semantic_contrasts()
    assert any(r['not_all']!=r['all_not'] for r in rows)


@pytest.mark.parametrize('inner_reference',[False,True])
def test_binding_distance_keeps_outer_and_inner_variable_distinct(inner_reference):
    body=quant('forall','x',quant('exists','y',logic('not',logic('equal',variable('x'),variable('y' if inner_reference else 'x')))))
    d=doc(assertion(body)); restored=decode_document(roundtrip(d))
    values=evaluate_document(restored,individuals=(0,1),situations=('now',),primitives={})
    assert values[0]['value']==inner_reference


def test_alpha_renaming_and_fraction_reduction_only():
    a=doc(assertion(quant('forall','x',logic('equal',variable('x'),variable('x')))))
    b=doc(assertion(quant('forall','other',logic('equal',variable('other'),variable('other')))))
    assert compile_document(a)==compile_document(b)
    assert compile_document(doc(assertion(logic('equal',num(2,4),num(1,2)))))==compile_document(doc(assertion(logic('equal',num(1,2),num(1,2)))))
    assert compile_document(doc(assertion(logic('equal',num(1),num(2)))))!=compile_document(doc(assertion(logic('equal',num(2),num(1)))))


def test_proper_and_compound_names_in_visible_definitions():
    names=[symbol(Word(k,('home','town')),vocabulary()) for k in ('proper','compound')]
    definitions=[dict(kind='definition',name=n,parameters=[],result='individual',body=call('home')) for n in names]
    d=doc(assertion(logic('equal',*(dict(kind='call',symbol=n,arguments=[]) for n in names))),roots=('home',),definitions=definitions)
    roundtrip(d)
    assert names[0]!=names[1]


def expression_cases():
    one,two=num(1),num(2)
    eq=logic('equal',one,one)
    lam=dict(kind='lambda',parameters=[dict(name='x',sort='number')],body=variable('x'))
    truthfn=dict(kind='lambda',parameters=[dict(name='x',sort='number')],body=logic('equal',variable('x'),one))
    seq=dict(kind='sequence',element='number',items=[one,two])
    content=dict(kind='content',variable='world',body=eq)
    message=dict(kind='message',force='direct',content=content)
    return [
        logic(k,eq,*(() if k=='not' else (logic('equal',one,two),))) for k in ('not','and','or','implies','iff')
    ]+[
        logic('equal',num(-7,3),num(-14,6)),
        logic('equal',dict(kind='apply',function=lam,arguments=[two]),two),
        logic('equal',dict(kind='disquote',description=quote(one)),one),
        logic('equal',quote(dict(kind='disquote',description=quote(one)),1),quote(dict(kind='disquote',description=quote(one)),1)),
        logic('equal',dict(kind='quoted_lift',description=quote(one)),quote(quote(one))),
        logic('equal',dict(kind='quoted_application',function=quote(lam),arguments=[quote(two)]),quote(dict(kind='apply',function=lam,arguments=[two]))),
        dict(kind='answer_matches',question=dict(kind='question',function=truthfn),arguments=[one]),
        logic('equal',dict(kind='length',sequence=seq),two),
        dict(kind='position',sequence=seq,index=num(0),value=one),
        logic('equal',dict(kind='concat',left=seq,right=dict(kind='sequence',element='number',items=[])),seq),
        logic('equal',dict(kind='fold',sequence=seq,initial=one,step=dict(kind='lambda',parameters=[dict(name='a',sort='number'),dict(name='b',sort='number')],body=variable('b'))),two),
        logic('equal',dict(kind='message_content',message=message),content),
        quant('forall','w',dict(kind='evaluate',content=content,situation=variable('w')),sort='situation'),
    ]


@pytest.mark.parametrize('expression',expression_cases())
def test_native_expression_families(expression): roundtrip(doc(assertion(expression)))


@pytest.mark.parametrize('sort',[
    'individual','number','truth','situation','content','message',
    dict(kind='function',parameters=['number'],result='number'),
    dict(kind='sequence',element='individual'),dict(kind='question',parameters=['number','individual']),
    dict(kind='description',result='truth'),dict(kind='description',rank=2,result='number'),
    dict(kind='function',parameters=[dict(kind='sequence',element='number')],result=dict(kind='description',rank=1,result='number')),
])
def test_native_types_are_visible_in_bound_variables(sort):
    roundtrip(doc(assertion(quant('forall','x',logic('equal',variable('x'),variable('x')),sort=sort))))


def test_function_reference_questions_and_message_performance():
    fn=dict(kind='function_ref',symbol=named('rain'))
    body=call('rain',call('home'))
    d=doc(dict(kind='ask',body=dict(kind='question',function=fn)),
          dict(kind='perform',body=dict(kind='message',force='assert',content=dict(kind='content',variable='w',body=body))),
          roots=('rain','home'))
    roundtrip(d)


@pytest.mark.parametrize('rail,gap',list(product((0,2),(80.,120.))))
def test_layout_scale_translation_and_segment_storage_do_not_change_reading(rail,gap):
    d=specimens()[0]['document']; shapes=roundtrip(d,first_rail=rail,gap=gap)
    changed=[]
    for s in _translate(shapes,173.5,-99.25,1.7):
        if s['kind']=='circle': changed.append(s)
        else:
            a,b=(s['x1'],s['y1']),(s['x2'],s['y2']); mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
            changed.extend((line(b,mid),line(mid,a)))
    assert decode_document(list(reversed(changed)))==d


def test_independent_hand_drawn_branch_reads_argument_order(monkeypatch):
    # assert = concentric L/M with east ray, then medium east modifier.
    # above = L north ray. Its two terminal arguments branch upper/lower
    # at different x coordinates. Nothing here calls the renderer.
    rings=[(50,32,LARGE),(50,32,MEDIUM),(180,32,MEDIUM),
           (320,32,LARGE),(510,0,MEDIUM),(680,64,MEDIUM)]
    strokes=[((50,32),(50+LARGE,32)),((180,32),(180+MEDIUM,32)),
             ((320,32),(320,32-LARGE)),((510,0),(510,-MEDIUM)),
             ((680,64),(680,64+MEDIUM)),
             ((50+LARGE,32),(180-MEDIUM,32)),((180+MEDIUM,32),(320-LARGE,32)),
             ((320+LARGE,32),(400,32)),((400,32),(432,0)),((432,0),(510-MEDIUM,0)),
             ((400,32),(432,64)),((432,64),(680-MEDIUM,64))]
    shapes=[circle(x,y,r) for x,y,r in rings]+[line(a,b) for a,b in strokes]
    import scripts.visible_syntax as module
    monkeypatch.setattr(module,'compile_document',lambda *a,**kw:pytest.fail('Decoder called compiler'))
    reader=Reader(recognize(shapes),vocabulary())
    assert reader.statement()==assertion(call('above',call('birdone'),call('treeone')))
    assert reader.i==len(reader.tokens)


@pytest.mark.parametrize('mutation',['remove','extra','field','tiny','disconnect','invisible'])
def test_unknown_malformed_or_hidden_ink_is_rejected(mutation):
    shapes=deepcopy(specimens()[0]['compiled']['shapes'])
    if mutation=='remove': shapes.pop()
    elif mutation=='extra': shapes.append(circle(100000.,32.,SMALL))
    elif mutation=='field': shapes[0]['meaning']='above'
    elif mutation=='tiny': shapes[0]['r']*=.9
    elif mutation=='disconnect':
        longest=max((s for s in shapes if s['kind']=='line'),key=lambda s:abs(s['x2']-s['x1']))
        shapes.remove(longest)
    else:
        with pytest.raises(ValueError): from_svg(to_svg(shapes).replace('<circle ','<circle opacity="0" ',1))
        return
    with pytest.raises(ValueError): decode_document(shapes)


def test_rank_and_quote_capture_are_checked_after_visible_parsing():
    w=Writer(vocabulary()); w.keyword('quote'); w.natural(0); w.keyword('variable'); w.natural(0)
    with pytest.raises(ValueError,match='Unbound'): raw(w).expr(('outer',))
    bad=dict(kind='disquote',description=quote(num(1),1),rank=0)
    w=Writer(vocabulary()); w.keyword('document'); w.natural(16); w.natural(1); w.end()
    w.statement(assertion(logic('equal',bad,num(1)))); w.end()
    with pytest.raises(ValueError,match='rank annotation'): raw(w).document()


@pytest.mark.parametrize('bits',[[],[0,0],[0,1],[1]*(MAX_BITS+1)])
def test_invalid_natural_numbers_rejected(bits):
    w=Writer(vocabulary()); w.glyphs=[modifier_glyph(0 if bit else None) for bit in bits]+[END_GLYPH]
    with pytest.raises(ValueError): raw(w).natural()


def test_invalid_boundaries_versions_and_forward_references_rejected():
    w=Writer(vocabulary()); w.document(integrated_document())
    with pytest.raises(ValueError): Reader(raw(w).tokens[:-1],vocabulary()).document()
    with pytest.raises(ValueError): Reader(raw(w).tokens+[END],vocabulary()).document()
    bad=Writer(vocabulary()); bad.keyword('document'); bad.natural(15); bad.natural(1); bad.end(); bad.end()
    with pytest.raises(ValueError,match='edition'): raw(bad).document()
    bad=Writer(vocabulary()); bad.keyword('document'); bad.natural(16); bad.natural(1); bad.end()
    bad.statement(assertion(call('rain',call('home')))); bad.end()
    with pytest.raises(ValueError,match='Unknown'): raw(bad).document()


def test_type_and_argument_count_errors_rejected_from_visible_input():
    bad=Writer(vocabulary()); bad.keyword('document'); bad.natural(16); bad.natural(1)
    for n in ('rain','home'): bad.keyword('import'); bad.name(named(n))
    bad.end(); bad.statement(assertion(call('rain',num(1)))); bad.end()
    with pytest.raises(ValueError,match='sort mismatch'): raw(bad).document()


def test_typed_definition_binders_and_reference_preserve_parameter_order():
    name=symbol(Word('compound',('above','home')),vocabulary())
    definition=dict(kind='definition',name=name,parameters=[dict(name=n,sort='individual') for n in ('x','y')],
                    result='truth',body=call('above',variable('y'),variable('x')))
    d=doc(assertion(dict(kind='call',symbol=name,arguments=[call('aki'),call('nao')])),
          roots=('above','aki','nao'),definitions=[definition])
    restored=decode_document(roundtrip(d))
    for slot in (0,1):
        result=evaluate_document(restored,individuals=(0,1),situations=('now',),primitives={
            named('aki'):lambda:0,named('nao'):lambda:1,named('above'):lambda *args:args[slot]==1})
        assert result[0]['value']==(slot==0)


def test_integrated_definition_does_not_assert_its_truth_automatically():
    d=integrated_document()
    for raining in (False,True):
        rows=evaluate_document(d,individuals=('home',),situations=('now',),primitives={
            named('home'):lambda:'home',named('rain'):lambda who:raining})
        assert [r['value'] for r in rows[:3]]==[raining,True,True]


@pytest.mark.parametrize('operation',['unknown','zero-denominator','negative-zero','wrong-arity','recursive'])
def test_invalid_grammar_and_declarations_are_not_repaired(operation):
    w=Writer(vocabulary()); w.keyword('document'); w.natural(16); w.natural(1)
    name=symbol(Word('compound',('rain','home')),vocabulary())
    if operation in ('wrong-arity','recursive'):
        w.keyword('definition'); w.name(name); w.end(); w.type('number')
        if operation=='recursive': w.expr(dict(kind='call',symbol=name,arguments=[]))
        else: w.expr(num(1))
    w.end(); w.keyword('assert')
    if operation=='unknown':
        w.glyphs.extend((family_glyph('logic'),modifier_glyph(None)))
    elif operation in ('zero-denominator','negative-zero'):
        w.keyword('equal'); w.keyword('negative' if operation=='negative-zero' else 'nonnegative')
        w.natural(0 if operation=='negative-zero' else 1); w.natural(1 if operation=='negative-zero' else 0)
        w.expr(num(1))
    else: w.expr(logic('equal',dict(kind='call',symbol=name,arguments=[num(1)]),num(1)))
    w.end()
    with pytest.raises(ValueError): raw(w).document()
