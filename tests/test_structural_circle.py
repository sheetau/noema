from copy import deepcopy
from itertools import permutations
import pytest

from noema.constructed_discourse import normalize_document
from scripts.check_structural_circle import cases, specimens, full_vocabulary
from scripts.check_visible_syntax import vocabulary, call, doc, assertion, named, quant, variable, logic, num, quote
from scripts import structural_circle as sc
from scripts.visible_syntax import Writer
from scripts.visible_lexical_script import _shape_set, _translate
from scripts.balanced_circle_script import circle, line, LARGE, MEDIUM, SMALL


def test_all_bounded_documents_and_statement_exhibits_roundtrip():
    assert len(specimens()) == 40
    assert all(r['svg'].count('<circle') for r in specimens())


@pytest.mark.parametrize('corner', ['square','bevel'])
def test_translated_scaled_reordered_segmented_ink(corner):
    document = cases()[8][2]
    shapes = sc.compile_document(document,corners=corner)['shapes']
    changed = []
    for s in _translate(shapes, 213.35, -917.2, 1.73):
        if s['kind']=='circle': changed.append(s)
        else:
            a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
            m=((a[0]+b[0])/2,(a[1]+b[1])/2)
            changed.extend((line(b,m),line(m,a)))
    assert sc.decode(list(reversed(changed)))==document


@pytest.mark.parametrize('order', list(permutations(('aki','nao','book'))))
def test_all_three_argument_orders(order):
    d=doc(assertion(call('give',*(call(n) for n in order))),roots=('give','aki','nao','book'))
    assert sc.decode(sc.from_svg(sc.to_svg(sc.compile_document(d)['shapes'])))==d


def test_independent_drawing_decoded_without_calling_compiler(monkeypatch):
    # A handwritten public statement. No glyph generator/renderer is called.
    step=sc.STEP; half=sc.ROW/2
    shapes=[circle(0,0,LARGE),circle(0,0,MEDIUM),circle(step,0,MEDIUM),
            circle(2*step,0,LARGE),circle(3*step,-half,MEDIUM),circle(3*step,half,MEDIUM)]
    paths=[((0,0),(LARGE,0)),((step,0),(step+MEDIUM,0)),
           ((2*step,0),(2*step,-LARGE)),((3*step,-half),(3*step,-half-MEDIUM)),
           ((3*step,half),(3*step,half+MEDIUM)),
           ((LARGE,0),(step-MEDIUM,0)),((step+MEDIUM,0),(2*step-LARGE,0)),
           ((2*step+LARGE,0),(2.5*step,0)),((2.5*step,-half),(2.5*step,half)),
           ((2.5*step,-half),(3*step-MEDIUM,-half)),((2.5*step,half),(3*step-MEDIUM,half))]
    shapes.extend(line(a,b) for a,b in paths)
    monkeypatch.setattr(sc,'render_tree',lambda *a,**k:pytest.fail('Decoder invoked renderer'))
    assert sc.decode(shapes,mode='statement')==assertion(call('above',call('birdone'),call('treeone')))


def test_branch_topology_is_checked_even_if_flattened_tokens_match():
    w=Writer(vocabulary());w.document(cases()[0][2]);tokens=[_shape_set(g['shapes']) for g in w.glyphs]
    chain=[[i+1] if i<len(tokens)-1 else [] for i in range(len(tokens))]
    bad=sc.render_tree(tokens,chain,vocabulary())['shapes']
    with pytest.raises(ValueError,match='grammatical scopes'): sc.decode(bad)


@pytest.mark.parametrize('mutation',['missing-circle','unknown-circle','missing-line','extra-line','hidden-field','wrong-radius','gap','crossing','bad-diagonal'])
def test_malformed_geometry_is_not_repaired(mutation):
    shapes=deepcopy(sc.compile_document(cases()[0][2])['shapes'])
    circles=[s for s in shapes if s['kind']=='circle'];lines=[s for s in shapes if s['kind']=='line']
    if mutation=='missing-circle': shapes.remove(circles[-1])
    elif mutation=='unknown-circle': shapes.append(circle(12345,9182,SMALL))
    elif mutation=='missing-line': shapes.remove(lines[-1])
    elif mutation=='extra-line': shapes.append(line((10000,10000),(10100,10000)))
    elif mutation=='hidden-field': circles[0]['source']='secret'
    elif mutation=='wrong-radius': circles[-1]['r']*=.9
    elif mutation=='gap': lines[-1]['x2']+=5
    elif mutation=='crossing': shapes.append(line((0,-1000),(0,1000)))
    else: shapes.append(line((10000,10000),(10013,10013)))
    with pytest.raises(ValueError): sc.decode(shapes)


def test_svg_hidden_ink_and_nonfinite_coordinates_rejected():
    shapes=sc.compile_document(cases()[0][2])['shapes']
    with pytest.raises(ValueError):sc.from_svg(sc.to_svg(shapes).replace('<circle ','<circle opacity="0" ',1))
    shapes[0]['x']=float('nan')
    with pytest.raises(ValueError):sc.decode(shapes)


def test_quote_cannot_capture_outer_binder_and_free_variable_is_rejected():
    w=Writer(vocabulary());w.keyword('assert');w.keyword('forall');w.type('individual')
    w.keyword('quote');w.natural(0);w.keyword('variable');w.natural(0)
    with pytest.raises(ValueError,match='Unbound'):
        sc.grammar_tree([_shape_set(g['shapes']) for g in w.glyphs],vocabulary(),'statement')


def test_alpha_renaming_preserves_ink_and_bound_slot_change_does_not():
    a=doc(assertion(quant('forall','x',logic('equal',variable('x'),variable('x')))))
    b=doc(assertion(quant('forall','other',logic('equal',variable('other'),variable('other')))))
    assert sc.compile_document(a)==sc.compile_document(b)
    assert sc.compile_document(cases()[5][2])!=sc.compile_document(cases()[6][2])


def test_dictionary_order_is_not_a_word_number():
    from scripts.visible_syntax_vocabulary import Vocabulary
    v=vocabulary().document();v['entries']=dict(reversed(list(v['entries'].items())))
    d=cases()[0][2]
    assert sc.compile_document(d,Vocabulary(v))==sc.compile_document(d,vocabulary())


def test_shared_public_definition_is_imported_without_changing_meaning():
    v=full_vocabulary()
    # Public shared definitions are a declaration contract, not arbitrary IDs.
    name=next(n for n in v.document()['definitions'] if v.word(n).kind=='compound')
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=v.imports([name]),statements=[]))
    assert sc.decode(sc.compile_document(d,v)['shapes'],v)==d
    bad=deepcopy(d)
    bad['declarations'][-1]['body']=dict(kind='not',arguments=[bad['declarations'][-1]['body']])
    with pytest.raises(ValueError):sc.compile_document(bad,v)


def test_every_public_glyph_and_both_branch_forms_are_used_and_read():
    v=full_vocabulary()
    table=sc.catalogue(v)
    first=_shape_set(sc.family_glyph('utterance')['shapes'])
    tokens=[first,*[key for key in table if key!=first]]
    children=[list(range(1,len(tokens)))]+[[] for _ in tokens[1:]]
    for corners in ('square','bevel'):
        shapes=sc.render_tree(tokens,children,v,corners=corners)['shapes']
        recovered,tree=sc.read_geometry(sc.from_svg(sc.to_svg(shapes)),v)
        assert recovered==tokens and tree==children


def test_long_lexical_chain_does_not_use_python_recursive_layout():
    # Geometry supports long prefixes without recursion proportional to glyphs.
    token=_shape_set(sc.modifier_glyph(0)['shapes'])
    tokens=[token]*700;children=[[i+1] if i<699 else [] for i in range(700)]
    drawing=sc.render_tree(tokens,children,vocabulary())
    assert drawing['glyphs']==700


def test_all_grammar_operations_including_scoped_sharing_are_exercised():
    from scripts.visible_syntax_vocabulary import KEYWORDS
    from scripts.visible_sharing import SHARING
    seen=set()
    class CoverageReader(sc.StructuralReader):
        def keyword(self):
            k=super().keyword();seen.add(k);return k
    for _,_,d in cases():
        w=sc.PublicWriter(vocabulary(),automatic=False);w.document(d)
        CoverageReader([_shape_set(g['shapes']) for g in w.glyphs],vocabulary()).document()
    expr=logic('equal',num(7,3),num(11,5))
    d=doc(assertion(logic('and',expr,expr)))
    w=sc.PublicWriter(vocabulary(),automatic=True);w.document(d)
    CoverageReader([_shape_set(g['shapes']) for g in w.glyphs],vocabulary()).document()
    assert set(KEYWORDS)|set(SHARING) <= seen
    assert sc.decode(sc.compile_document(d,sharing=True)['shapes'])==d
    assert sc.compile_document(d,sharing=True)['glyphs'] < sc.compile_document(d)['glyphs']


def test_partial_duplicate_corner_stroke_is_rejected():
    shapes=sc.compile_document(cases()[0][2])['shapes']
    # Find an external bevel (glyph marks have circle centers at grid columns).
    bevel=next(s for s in shapes if s['kind']=='line' and abs(s['x2']-s['x1'])==sc.BEVEL and abs(s['y2']-s['y1'])==sc.BEVEL)
    x=min(bevel['x1'],bevel['x2']);y=bevel['y2']
    shapes.append(line((x,y),(x+sc.BEVEL/2,y)))
    with pytest.raises(ValueError):sc.decode(shapes)
