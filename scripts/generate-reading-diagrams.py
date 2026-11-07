"""Three teaching schematics using adopted glyph components; not source documents."""
import sys
sys.dont_write_bytecode = True
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(os.environ.get('NOEMA_SOURCE', ROOT.parent / 'noema')).resolve()))
from scripts.concept2_writing import WritingReader
from scripts.concept2_document import full_name, full_parts
from noema.constructed import parse
import json
from scripts import concept2_composition as c, concept2_geometry_v5 as g

writer = WritingReader()
destination = ROOT / 'public/diagrams'
destination.mkdir(parents=True, exist_ok=True)
ns = '{http://www.w3.org/2000/svg}'


def glyph(token, x, y, color='#eee'):
    raw = c.svg(c.move(writer.forms[token]['shapes'], x, y), width=360, height=166)
    group = list(ET.fromstring(raw))[0]
    group.set('stroke', color)
    for node in group.iter():
        if node.get('fill') == '#203438': node.set('fill', color)
    return ET.tostring(group, encoding='unicode')


def save(name, title, drawing):
    guides = '<path d="M0 34H360M0 132H360" stroke="#141414" stroke-dasharray="2 4"/><path d="M0 50H360M0 83H360M0 116H360" stroke="#141414"/>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="166" viewBox="0 0 360 166"><title>{title}</title>{guides}{drawing}</svg>\n'
    (destination / name).write_text(svg, encoding='utf-8', newline='\n')


row = g.layout(writer.units([('root','book'), ('root','home'), ('word-end',)]), max_width=310)[0]
left,top,right,bottom = c.bounds(row['shapes'])
shapes = c.move(row['shapes'], (360-right-left)/2, 83)
group = list(ET.fromstring(c.svg(shapes, width=360, height=166)))[0]
group.set('stroke','#eee')
save('spelling.svg', 'Roots book and home, followed by the word-end marker',
    ET.tostring(group,encoding='unicode') + '<g fill="#888" font-family="Consolas,monospace" font-size="11"><text x="50" y="157">book · home</text><text x="249" y="157">word end</text></g>')

save('branches.svg', 'A schematic trunk and three ordered argument positions',
    '<g transform="translate(29 0)">' + glyph(('root','give'),45,83,'#666') +
    '<path d="M69 83H112M112 83L145 50H263M112 83H263M112 83L145 116H263" fill="none" stroke="#eee" stroke-width="1.65"/>'
    '<g fill="#eee" font-family="Consolas,monospace" font-size="12"><text x="280" y="54">01</text><text x="280" y="87">02</text><text x="280" y="120">03</text></g></g>')

# A complete quotation of the shared, zero-argument home term, including its
# word terminator and genuine connections. Check the undecorated ink first.
symbol = full_name([c.old.root_symbol('home')])
record = parse(f'p:\nr {symbol}[] a.\n')['declarations'][0]
writer.register(record)
tokens = [('op','quote-open')] + writer._raw_word(full_parts(symbol)) + [('op','quote-close')]
row = g.layout(writer.units(tokens), max_width=2000)[0]
raw = c.svg(row['shapes'], pad=2)
recovered = writer.read_svg(raw, fragment=True)['tokens']
assert recovered == tokens
assert writer.parse(recovered, expression=True) == {'kind':'quote','body':{'kind':'call','symbol':symbol,'arguments':[]}}
left,top,right,bottom = c.bounds(row['shapes'])
dx = (360-right-left)/2
assert right-left < 350

def group(shapes, color):
    root = ET.fromstring(c.svg(c.move(shapes,dx,83),width=360,height=166))
    node = list(root)[0]; node.set('stroke',color)
    return ET.tostring(node,encoding='unicode')

brackets = [shape for unit in row['placed'] if unit['token'] in [('op','quote-open'),('op','quote-close')] for shape in unit['shapes']]
save('scope.svg', 'A syntactically complete quotation of home',
    group(row['shapes'],'#666') + group(brackets,'#eee') +
    '<text x="180" y="157" fill="#888" text-anchor="middle" font-family="Consolas,monospace" font-size="11">quotation scope</text>')
evidence = ROOT / 'output/reading-scope'
evidence.mkdir(exist_ok=True,parents=True)
(evidence/'scope.svg').write_text(raw,encoding='utf-8',newline='\n')
(evidence/'verification.json').write_text(json.dumps({'tokens':recovered,'expression':writer.parse(recovered,expression=True),'decoded':True},indent=2),encoding='utf-8')
print('Generated three reading schematics; core glyphs read without modification.')
