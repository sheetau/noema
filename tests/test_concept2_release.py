"""Release coverage at the lexical/geometry boundary, beyond bare glyph matching."""
import math
from collections import Counter
from scripts.concept2_writing import WritingReader
from scripts.concept2_document import full_name
from scripts import concept2_composition as c, concept2_geometry_v5 as g


def test_every_root_and_ligature_can_name_a_visible_declaration():
    forms=WritingReader().forms
    for token in forms:
        if token[0] not in ('root','lig','lig-alt'):continue
        parts=[c.old.root_symbol(n) for n in token[1:]]
        record=dict(kind='primitive',name=full_name(parts),parameters=[],result='individual')
        writer=WritingReader();tokens=writer.encode_record(record)
        ordinary=('lig',*token[1:]) if token[0]=='lig-alt' else token
        assert ordinary in tokens,token
        tokens=[token if t==ordinary else t for t in tokens]
        drawing=g.layout(writer.units(tokens))[0]
        assert WritingReader().read_svg(c.svg(drawing['shapes']))['native']==record,token


def test_registered_circle_intersections_use_only_the_three_permitted_pairs():
    observed=Counter()
    allowed={tuple(sorted((round(a,4),round(b,4)))) for a,b in ((g.S,g.M),(g.S,g.L),(g.M,g.L))}
    for token,unit in WritingReader().forms.items():
        g.ink_check(unit['shapes'])
        circles=list({(s['x'],s['y'],s['r']):s for s in unit['shapes'] if s['kind']=='arc'}.values())
        for i,a in enumerate(circles):
            for b in circles[:i]:
                d=math.hypot(a['x']-b['x'],a['y']-b['y'])
                if d and abs(d*d-a['r']**2-b['r']**2)<.001:
                    pair=tuple(sorted((round(a['r'],4),round(b['r'],4))))
                    assert pair in allowed,(token,pair)
                    observed[pair]+=1
    assert set(observed)==allowed
