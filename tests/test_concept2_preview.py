from copy import deepcopy
import math
import pytest
from scripts import concept2_preview as c


def test_orthogonal_cutouts_survive_ink_only_svg_roundtrip():
    for mode in ('cross','cut','eclipse'):
        shapes=c.orthogonal_pair(c.L,c.M,mode)
        ink=c.from_svg(c.svg(shapes,width=200,height=200))
        c.validate_geometry(ink)
        assert len(ink)==2


def test_rejects_eccentric_containment_and_nonradial_lines():
    with pytest.raises(ValueError,match='Eccentric containment'):
        c.validate_geometry([c.circle(c.M),c.circle(c.S,4)])
    with pytest.raises(ValueError,match='Nonradial'):
        c.validate_geometry([c.circle(c.M),c.line((-50,5),(50,5))])


def test_unfilled_binder_small_circle_remains_unconnected_after_layout():
    for kind in ('lambda','forall'):
        tape=[dict(kind=kind),dict(kind='variable')]
        drawing=c.compile_tape(tape);unit=drawing['placed'][0]
        c.validate_geometry(drawing['shapes'])
        center=(unit['x'],unit['rail'])
        for s in drawing['shapes']:
            if s['kind']!='line':continue
            a=(s['x1'],s['y1']);b=(s['x2'],s['y2']);dx=b[0]-a[0];dy=b[1]-a[1]
            t=max(0,min(1,((center[0]-a[0])*dx+(center[1]-a[1])*dy)/(dx*dx+dy*dy)))
            assert math.dist(center,(a[0]+t*dx,a[1]+t*dy))>c.S+c.EPS


def test_quotes_preserve_rank_and_function_reference_vs_call():
    decl={'x':dict(parameters=[])};spell={'x':['wrakizq']};aliases={('wrakizq',):'x'}
    shapes=[]
    for mode in ('call','function_ref'):
        for rank in (None,1,3):
            leaf=dict(kind=mode,symbol='x')
            if mode=='call':leaf['arguments']=[]
            q=dict(kind='quote',body=leaf)
            if rank is not None:q['rank']=rank
            source=dict(kind='assert',body=q);tape=c.to_tape(source,spell)
            assert c.from_tape(tape,decl,aliases)==source
            shapes.append(c.svg(c.compile_tape(tape)['shapes']))
    assert len(set(shapes))==6


def test_infix_association_and_argument_order_are_not_flattened():
    decl={s:dict(parameters=[]) for s in 'xyz'}
    spell={s:['wr'+r+'zq'] for s,r in zip('xyz',('aki','book','home'))}
    aliases={tuple(v):k for k,v in spell.items()}
    def leaf(s):return dict(kind='call',symbol=s,arguments=[])
    def join(a,b):return dict(kind='and',arguments=[a,b])
    a,b,z=map(leaf,'xyz')
    sources=[join(join(a,b),z),join(a,join(b,z)),join(b,join(a,z))]
    tapes=[]
    for body in sources:
        source=dict(kind='assert',body=body);tape=c.to_tape(source,spell)
        assert c.from_tape(tape,decl,aliases)==source;tapes.append(tape)
    assert all(tapes[i]!=tapes[j] for i in range(3) for j in range(i))


def test_spelling_ligatures_retain_order_and_folding_keeps_matching_rails():
    parts=['wrbookzq','wrhomezq','wrroundzq','wrakizq']
    assert [p for x in c.spell(parts) for p in x['expansion']]==parts
    tape=[dict(kind='word',parts=parts,mode='call') for _ in range(12)]
    d=c.compile_tape(tape);folded=c.fold_paragraph([d],max_width=500)
    assert len(folded)>2
    for a,b in zip(folded,folded[1:]):
        assert a['exit_rail']==b['entry_rail']
        assert a['exit_rail'] is not None


def test_unknown_syntax_is_rejected_not_omitted():
    with pytest.raises(ValueError,match='Unimplemented'):
        c.to_tape(dict(kind='assert',body=dict(kind='future_operator')), {})
