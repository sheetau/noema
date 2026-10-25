from copy import deepcopy
from itertools import product
import pytest

from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_sharing import SharedWriter,SharedReader,compile_document,decode_document,free_variables
from scripts.visible_shared_page import compile_page,decode_page,SharedLayoutReader
from scripts.visible_syntax import Writer,Reader
from scripts.visible_syntax_geometry import render,recognize
from scripts.visible_lexical_script import _shape_set,_translate
from scripts.visible_page import packet
from scripts.check_visible_syntax import vocabulary,doc,assertion,num,logic,quant,variable,call,named,quote
from scripts.check_visible_sharing import specimen,integrated_document


def signatures(w): return [_shape_set(g['shapes']) for g in w.glyphs]


def manual(body,roots=()):
    w=SharedWriter(vocabulary(),automatic=False)
    w.keyword('document'); w.natural(16); w.natural(1)
    for n in roots: w.keyword('import'); w.name(named(n))
    w.end(); w.keyword('assert'); body(w); w.end()
    return w


def reuse(w,n=0): w.keyword('reuse'); w.natural(n)


def read(w): return SharedReader(signatures(w),vocabulary()).document()


def test_shared_sequence_argument_and_quoted_syntax_restore_exact_document():
    s=specimen()
    assert s['shared_glyphs']<s['ordinary_glyphs']
    assert s['sharing_binders']>0
    assert decode_page(s['page']['shapes'])['document']==integrated_document()
    values=evaluate_document(integrated_document(),individuals=(0,1),situations=('now',),primitives={})
    assert [row['value'] for row in values]==[True,True]


@pytest.mark.parametrize('a,b',[(1,2),(12345,678),(0,1),(-777,13)])
def test_automatic_sharing_never_increases_these_numeric_cases(a,b):
    d=doc(assertion(logic('equal',num(a,b),num(a,b))))
    ordinary=Writer(vocabulary()); ordinary.document(d)
    shared=SharedWriter(vocabulary()); shared.document(d)
    assert len(shared.glyphs)<=len(ordinary.glyphs)
    assert decode_document(compile_document(d)['shapes'])==d


def test_shared_short_subject_is_explicit_and_not_inferred_from_contact():
    def body(w):
        w.keyword('share'); w.expr(call('aki'))
        w.keyword('and')
        w.name(named('red')); reuse(w)
        w.name(named('round')); reuse(w)
    w=manual(body,roots=('aki','red','round'))
    d=doc(assertion(logic('and',call('red',call('aki')),call('round',call('aki')))),roots=('aki','red','round'))
    assert decode_document(render(w.glyphs)['shapes'])==d
    for red,round_ in product((False,True),repeat=2):
        result=evaluate_document(read(w),individuals=('a','b'),situations=('now',),primitives={
            named('aki'):lambda:'a',named('red'):lambda x:red,named('round'):lambda x:round_})
        assert result[0]['value']==(red and round_)
    # Removing the explicit sharing operator leaves a malformed assertion;
    # proximity or its original connection tree supplies no implicit sharing.
    stream=signatures(w); start=next(i for i in range(len(stream)-1) if tuple(stream[i:i+2]) in SharedReader([],vocabulary()).special)
    with pytest.raises(ValueError): SharedReader(stream[:start]+stream[start+2:],vocabulary()).document()


def test_shared_free_variable_is_not_recaptured_by_inner_quantifier():
    def body(w):
        w.keyword('forall'); w.type('individual')
        w.keyword('share'); w.keyword('variable'); w.natural(0)
        w.keyword('exists'); w.type('individual')
        w.keyword('and'); w.keyword('equal'); reuse(w); w.keyword('variable'); w.natural(1)
        w.keyword('not'); w.keyword('equal'); reuse(w); w.keyword('variable'); w.natural(0)
    w=manual(body)
    expected=doc(assertion(quant('forall','x',quant('exists','y',logic('and',
        logic('equal',variable('x'),variable('x')),logic('not',logic('equal',variable('x'),variable('y'))))))))
    restored=decode_document(render(w.glyphs)['shapes'])
    assert restored==expected
    assert evaluate_document(restored,individuals=(0,1),situations=('now',),primitives={})[0]['value'] is True


def test_automatic_sharing_stays_inside_the_binder_that_introduces_its_variable():
    long=dict(kind='sequence',element='individual',items=[variable('y')]*5)
    d=doc(assertion(quant('forall','x',quant('exists','y',logic('equal',long,long)))))
    w=SharedWriter(vocabulary()); w.document(d)
    assert w.share_count>0
    assert read(w)==d
    assert decode_document(render(w.glyphs)['shapes'])==d


def test_nested_shares_reference_the_explicit_outer_distance():
    def body(w):
        w.keyword('share'); w.expr(num(7))
        w.keyword('share'); w.expr(num(9))
        w.keyword('and')
        w.keyword('equal'); reuse(w,1); reuse(w,1)
        w.keyword('equal'); reuse(w,0); reuse(w,0)
    expected=doc(assertion(logic('and',logic('equal',num(7),num(7)),logic('equal',num(9),num(9)))))
    assert read(manual(body))==expected


def test_bound_names_inside_a_copied_function_are_alpha_normalized():
    def body(w):
        w.keyword('share')
        w.expr(dict(kind='lambda',parameters=[dict(name='x',sort='number')],body=variable('x')))
        w.keyword('equal')
        for n in (1,2):
            w.keyword('apply'); reuse(w); w.expr(num(n)); w.end()
    lam=dict(kind='lambda',parameters=[dict(name='a',sort='number')],body=variable('a'))
    expected=doc(assertion(logic('equal',*(dict(kind='apply',function=lam,arguments=[num(n)]) for n in (1,2)))))
    assert read(manual(body))==expected


def test_quotation_has_its_own_sharing_environment():
    def body(w):
        w.keyword('share'); w.expr(num(1))
        w.keyword('equal')
        for _ in range(2):
            w.keyword('quote'); w.natural(0); reuse(w)
    with pytest.raises(ValueError,match='Unbound shared'): read(manual(body))
    d=doc(assertion(logic('equal',quote(logic('equal',num(9999),num(9999))),quote(logic('equal',num(9999),num(9999))))))
    assert decode_document(compile_document(d)['shapes'])==d


@pytest.mark.parametrize('uses',[0,1])
def test_unused_and_single_use_shares_are_rejected(uses):
    def body(w):
        w.keyword('share'); w.expr(num(1)); w.keyword('equal')
        for i in range(2): reuse(w) if i<uses else w.expr(num(1))
    with pytest.raises(ValueError,match='at least two'): read(manual(body))


def test_out_of_scope_wrong_type_and_unavailable_binding_rejected():
    with pytest.raises(ValueError,match='Unbound shared'): read(manual(lambda w:reuse(w)))
    def wrong_type(w):
        w.keyword('share'); w.expr(num(1)); w.keyword('and'); reuse(w); reuse(w)
    with pytest.raises(ValueError): read(manual(wrong_type))
    def missing_binding(w):
        w.keyword('share'); w.keyword('variable'); w.natural(0)
        w.keyword('equal'); reuse(w); reuse(w)
    with pytest.raises(ValueError,match='Unbound visible'): read(manual(missing_binding))


def test_expansion_bomb_is_rejected_before_large_ast_is_built():
    def body(w):
        w.keyword('share'); w.expr(logic('equal',num(1),num(1)))
        for _ in range(16):
            w.keyword('share'); w.keyword('and'); reuse(w); reuse(w)
        w.keyword('and'); reuse(w); reuse(w)
    with pytest.raises(ValueError,match='node budget'): read(manual(body))


def test_sharing_is_not_truth_value_or_commutative_normalization():
    a=logic('equal',num(1),num(2)); b=logic('equal',num(2),num(1))
    d=doc(assertion(logic('equal',quote(a),quote(b))))
    result=decode_document(compile_document(d)['shapes'])
    assert result==d
    assert evaluate_document(result,individuals=(0,),situations=('now',),primitives={})[0]['value'] is False


@pytest.mark.parametrize('width',[1800.,2400.,3600.])
def test_shared_scope_survives_row_breaks_and_paragraphs(width):
    d=integrated_document(); page=compile_page(d,max_width=width,paragraph_starts=(0,1))
    assert decode_page(_translate(page['shapes'],121.5,-32.,1.25))==dict(document=d,paragraph_starts=[0,1])


def test_all_old_pages_read_and_no_sharing_preserves_old_layout():
    from scripts.check_visible_page import specimens
    from scripts.check_visible_syntax import integrated_document as old_document
    for e in specimens():
        assert decode_page(e['page']['shapes'])==dict(document=old_document(),paragraph_starts=e['paragraphs'])
        assert compile_page(old_document(),automatic=False,max_width=e['max_width'],paragraph_starts=e['paragraphs'])==e['page']


def test_row_cannot_split_new_sharing_keyword_or_reference_number():
    d=doc(assertion(logic('equal',num(12345),num(12345))))
    w=SharedWriter(vocabulary()); w.document(d)
    trace=SharedLayoutReader(signatures(w),vocabulary()); trace.document()
    special=SharedReader([],vocabulary()).special
    cut=next(i+1 for i in range(len(w.glyphs)-1) if tuple(signatures(w)[i:i+2]) in special)
    rows=[render(packet(w.glyphs[:cut],0))['shapes'],render(packet(w.glyphs[cut:],1,final=True))['shapes']]
    shapes=rows[0]+_translate(rows[1],0,170.)
    with pytest.raises(ValueError,match='indivisible'): decode_page(shapes)


def test_overlapping_nested_candidates_expand_and_do_not_grow():
    # Repeated enclosing expressions can subsume literal uses of an inner
    # candidate. Validate the emitted binders, not just the initial counts.
    values=[num(1234567,891),dict(kind='sequence',element='number',items=[num(n) for n in range(5)])]
    for value in values:
        base=logic('equal',value,value)
        previous=base
        for depth in range(5):
            expression=logic('and',previous,logic('or',previous,base))
            d=doc(assertion(expression))
            ordinary=Writer(vocabulary()); ordinary.document(d)
            shared=SharedWriter(vocabulary()); shared.document(d)
            assert len(shared.glyphs)<=len(ordinary.glyphs)
            assert read(shared)==d
            previous=expression


def test_shared_page_cli_recovers_native_text_and_paragraphs(tmp_path,capsys):
    import json
    from pathlib import Path
    from noema.constructed import parse
    from scripts.visible_shared_page import main
    source=Path(__file__).resolve().parents[1]/'examples/v016/visible-shared-argument-v1.noema'
    target=tmp_path/'shared.svg'
    assert main(['render',str(source),str(target),'--width','3000','--paragraph','1'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(target)])==0
    assert json.loads(capsys.readouterr().out)==dict(document=integrated_document(),paragraph_starts=[1])
    assert main(['decode',str(target),'--native'])==0
    assert parse(capsys.readouterr().out)==integrated_document()


def test_older_decoder_rejects_new_sharing_instead_of_guessing():
    d=doc(assertion(logic('equal',num(12345),num(12345))))
    w=SharedWriter(vocabulary()); w.document(d)
    assert w.share_count>0
    with pytest.raises(ValueError,match='Unknown grammar'): Reader(signatures(w),vocabulary()).document()
