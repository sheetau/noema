from dataclasses import asdict
import json
from pathlib import Path
import pytest
from noema.constructed import parse
from scripts.circle_alphabet import Atom,RECIPES,ALPHABET,glyph,spelling,geometry_check,rows,recover,svg_document


def test_all_geometric_components_obey_the_concept():
    for role in RECIPES:geometry_check(glyph(Atom('',role))[0])
    for c in ALPHABET:geometry_check(spelling(c))
    for role,text in [('name','ab'),('digits','cp'),('edition','n:'),('open','['),('close',']'),('empty','[]'),('end','.')]:
        geometry_check(glyph(Atom(text,role))[0])
    assert len({json.dumps(spelling(c),sort_keys=True) for c in ALPHABET})==32
    assert len({json.dumps(glyph(Atom('',r))[0],sort_keys=True) for r in RECIPES})==len(RECIPES)


@pytest.mark.parametrize('path',[
    'examples/v08/definitions.noema','examples/v010/conditional-directive.noema',
    'examples/v014/circle-alphabet-samples.noema','examples/v015/person-dependent-reports.noema',
    'examples/v016/personal-message-purpose.noema','examples/v016/local-reciprocity-custom.noema'])
def test_canonical_ast_and_role_tags_round_trip(path):
    text=Path(path).read_text(encoding='utf-8');doc=parse(text)
    record=[[asdict(a) for a in row] for row in rows(doc)]
    assert recover(record)==doc
    import xml.etree.ElementTree as ET
    root=ET.fromstring(svg_document(text,width=3000,scale=.4))
    metadata=json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
    assert recover(metadata['atoms'])==doc
    record[-1][0]['role']='ask' if record[-1][0]['role']!='ask' else 'assert'
    with pytest.raises(ValueError):recover(record)


def test_reused_surface_letter_has_contextual_shapes():
    assert glyph(Atom('a','type_individual'))!=glyph(Atom('a','suppose'))
    assert glyph(Atom('s','assert'))!=glyph(Atom('s','disquote'))
    # Identifiers do not acquire the grammatical meaning of their letters.
    assert glyph(Atom('s','name'))!=glyph(Atom('s','assert'))
