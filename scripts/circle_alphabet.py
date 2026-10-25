"""Opt-in circle/line writing prototype for the existing Noema 0.8--0.16 AST.

This is a deterministic renderer, not a change to the parser or a translator.
Semantic operator glyphs and spelled identifiers have separate namespaces.
"""
from dataclasses import dataclass, asdict
from html import escape
import json
import math
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.constructed_discourse import EDITIONS, MESSAGE_SORTS, LOGIC, QUANTIFIERS, FORCES, normalize_document
from noema.grammar import number_word
from noema.semantics import ALPHABET

VERSION='circle-1-draft'
RAILS=(0,24,48)
RADII=(6,14,22)
STROKE=1.8

# Size = operator / reference / subtype. Height = binding / relation / argument.
# The final component is the local attachment within that family.
FAMILIES={
    (22,0): ['primitive','definition','assert','ask','perform','suppose'],
    (22,24): ['not','and','or','implies','iff','equal'],
    (22,48): ['forall','exists','lambda'],
    (14,24): ['call','function_ref','apply','variable'],
    (14,0): ['content','evaluate','message_content','quote','disquote','quoted_application','quoted_lift','question'],
    (14,48): ['sequence','length','position','fold','concat'],
    (6,48): ['type_individual','type_number','type_truth','type_situation','type_content','type_message'],
    (6,0): ['type_sequence','type_description','type_question','type_function'],
    (6,24): ['message_assert','message_ask','message_direct','number','positive','negative','answer_matches'],
}
RECIPES={name:(radius,y,feature) for (radius,y),names in FAMILIES.items() for feature,name in enumerate(names)}

@dataclass(frozen=True)
class Atom:
    text:str
    role:str

def atom(text,role):return [Atom(text,role)]
def bracket(parts):return atom('[','open')+parts+atom(']','close') if parts else atom('[]','empty')
def flatten(parts):return [item for part in parts for item in part]

def typed(sort):
    if isinstance(sort,str):return atom({v:k for k,v in MESSAGE_SORTS.items()}[sort],'type_'+sort)
    kind=sort['kind']
    if kind=='sequence':return atom('j','type_sequence')+bracket(typed(sort['element']))
    if kind=='description':
        return atom('i','type_description')+(atom(number_word(sort['rank']),'digits') if sort.get('rank') else [])+bracket(typed(sort['result']))
    if kind=='question':return atom('g','type_question')+bracket(flatten(map(typed,sort['parameters'])))
    if kind=='function':return atom('h','type_function')+bracket(flatten(map(typed,sort['parameters'])))+typed(sort['result'])
    raise ValueError('Unknown sort: '+kind)

def parameters(params):return flatten(atom(p['name'],'name')+typed(p['sort']) for p in params)

def expression(node):
    kind=node['kind']
    if kind=='variable':return atom('v',kind)+atom(node['name'],'name')
    if kind=='number':
        return atom('n',kind)+atom('u' if node['numerator']<0 else 'p','negative' if node['numerator']<0 else 'positive')+atom(number_word(abs(node['numerator'])),'digits')+atom(number_word(node['denominator']),'digits')
    if kind=='call':return atom('k',kind)+atom(node['symbol'],'name')+bracket(flatten(map(expression,node['arguments'])))
    if kind=='function_ref':return atom('p',kind)+atom(node['symbol'],'name')
    if kind=='lambda':return atom('i',kind)+bracket(parameters(node['parameters']))+bracket(expression(node['body']))
    if kind=='content':return atom('b',kind)+atom(node['variable'],'name')+bracket(expression(node['body']))
    if kind=='quote':return atom('r',kind)+(atom(number_word(node['rank']),'digits') if node.get('rank') else [])+bracket(expression(node['body']))
    if kind=='sequence':return atom('l',kind)+bracket(typed(node['element']))+bracket(flatten(map(expression,node['items'])))
    if kind=='message':return atom('j '+{v:k for k,v in FORCES.items()}[node['force']],'message_'+node['force'])+bracket(expression(node['content']))
    if kind=='question':return atom('j v',kind)+bracket(expression(node['function']))
    if kind in ('apply','quoted_application','answer_matches'):
        word,field={'apply':('c','function'),'quoted_application':('o a','function'),'answer_matches':('h','question')}[kind]
        return atom(word,kind)+bracket(expression(node[field]))+bracket(flatten(map(expression,node['arguments'])))
    simple={'length':('d',['sequence']),'position':('a',['sequence','index','value']),
            'fold':('q',['sequence','initial','step']),'concat':('m',['left','right']),
            'quoted_lift':('o r',['description']),'disquote':('s',['description']),
            'message_content':('o',['message']),'evaluate':('t',['content','situation'])}
    if kind in simple:
        word,fields=simple[kind]
        return atom(word,kind)+flatten(bracket(expression(node[f])) for f in fields)
    logic={v:k for k,v in LOGIC.items()}
    if kind in logic:return atom(logic[kind],kind)+flatten(bracket(expression(a)) for a in node['arguments'])
    quantifiers={v:k for k,v in QUANTIFIERS.items()}
    if kind in quantifiers:return atom(quantifiers[kind],kind)+atom(node['variable'],'name')+typed(node['sort'])+bracket(expression(node['body']))
    raise ValueError('Unknown expression: '+kind)

def statement(node):
    kind=node['kind']
    if kind=='suppose':parts=atom('a',kind)+bracket(expression(node['condition']))+bracket(flatten(map(statement,node['statements'])))
    else:parts=atom({'assert':'s','ask':'q','perform':'l'}[kind],kind)+bracket(expression(node['body']))
    return parts+atom('.','end')

def rows(document):
    doc=normalize_document(document)
    result=[atom({v:k for k,v in EDITIONS.items()}[doc['schema_version']]+':','edition')]
    for d in doc['declarations']:
        parts=atom('r' if d['kind']=='primitive' else 'd',d['kind'])+atom(d['name'],'name')
        parts+=bracket(flatten(map(typed,d['parameters'])) if d['kind']=='primitive' else parameters(d['parameters']))+typed(d['result'])
        if d['kind']=='definition':parts+=bracket(expression(d['body']))
        result.append(parts+atom('.','end'))
    result.extend(map(statement,doc['statements']))
    return result

def recover(records):
    """Decode structured atoms; never claim optical recovery from arbitrary pixels."""
    doc=parse('\n'.join(' '.join(a['text'] for a in row) for row in records))
    expected=[[asdict(a) for a in row] for row in rows(doc)]
    if records!=expected:raise ValueError('Role tags or canonical spelling differ')
    return doc

def circle(x,y,r):return dict(kind='circle',x=x,y=y,r=r)
def line(x1,y1,x2,y2):return dict(kind='line',x1=x1,y1=y1,x2=x2,y2=y2)

def shape(radius,y,feature):
    """A radial entry, one circle and one of eight orthogonal/45-degree endings."""
    incoming=[line(0,48,24,48)] if y==48 else [line(0,48,24,24)]+([line(24,24,24,0)] if y==0 else [])
    extras=[line(60,y,84,y),line(60,0,60,24),line(60,24,60,48),line(60,0,60,48),
            line(60,48,84,24),line(60,24,84,0),line(60,0,84,24),line(60,24,84,48)]
    return incoming+[circle(24,y,radius),line(24,y,60,y),extras[feature]]

def shifted(shapes,x):
    return [{k:v+x if k in ('x','x1','x2') else v for k,v in s.items()} for s in shapes]

def spelling(char):
    index=ALPHABET.index(char)
    radius,y=((6,0),(6,24),(6,48),(14,24))[index//8]
    return shape(radius,y,index%8)

def glyph(a):
    if a.role in RECIPES:return shape(*RECIPES[a.role]),92
    if a.role in ('name','digits','edition'):
        # A concentric introducer makes the spelling namespace visible.
        r1,r2={'name':(22,6),'digits':(14,6),'edition':(22,14)}[a.role]
        shapes=[line(0,24,24,24),circle(24,24,r1),circle(24,24,r2),line(24,24,48,24)]
        x=56
        for c in (a.text[:-1] if a.role=='edition' else a.text):
            shapes+=shifted(spelling(c),x);x+=92
        return shapes,x
    if a.role=='open':return [line(0,48,24,24),line(24,24,36,24)],44
    if a.role=='close':return [line(0,24,12,24),line(12,24,36,48)],44
    if a.role=='empty':return [line(0,48,12,48),line(12,48,36,24),line(36,24,60,48),line(60,48,72,48)],80
    if a.role=='end':return [dict(kind='dot',x=12,y=48,r=2.5)],28
    raise ValueError('Unknown glyph role: '+a.role)

def geometry_check(shapes):
    circles=[s for s in shapes if s['kind']=='circle']
    for c in circles:
        assert c['r'] in RADII and c['y'] in RAILS
    for s in shapes:
        if s['kind']!='line':continue
        dx,dy=s['x2']-s['x1'],s['y2']-s['y1']
        assert dx or dy
        assert dx==0 or dy==0 or abs(dx)==abs(dy)
        if dy==0:assert s['y1'] in RAILS
        for c in circles:
            t=max(0,min(1,((c['x']-s['x1'])*dx+(c['y']-s['y1'])*dy)/(dx*dx+dy*dy)))
            distance=math.hypot(s['x1']+t*dx-c['x'],s['y1']+t*dy-c['y'])
            if distance<=c['r']+1e-8:
                assert abs(dx*(c['y']-s['y1'])-dy*(c['x']-s['x1']))<1e-8,'Nonradial circle contact'

def layout(atoms,width=1440,scale=.58):
    placed=[];x=0;y=0
    for a in atoms:
        shapes,advance=glyph(a)
        if advance*scale>width:raise ValueError('Identifier too wide; choose a wider page or smaller scale')
        if x and x+advance*scale>width:x=0;y+=108*scale
        placed.append((a,shapes,x,y));x+=(advance+12)*scale
    return placed,y+90*scale

def svg_document(text,width=1440,scale=.58):
    doc=parse(text);record=rows(doc);groups=[];y=40
    for row in record:
        placed,height=layout(row,width,scale)
        for a,shapes,x,dy in placed:
            components=[]
            for s in shapes:
                if s['kind'] in ('circle','dot'):
                    components.append(f'<circle cx="{s["x"]}" cy="{s["y"]}" r="{s["r"]}"'+(' fill="currentColor"' if s['kind']=='dot' else '')+'/>')
                else:components.append(f'<line x1="{s["x1"]}" y1="{s["y1"]}" x2="{s["x2"]}" y2="{s["y2"]}"/>')
            groups.append(f'<g data-role="{escape(a.role)}" data-source="{escape(a.text,quote=True)}" transform="translate({40+x} {y+dy}) scale({scale})">'+''.join(components)+'</g>')
        y+=height+20
    metadata=json.dumps(dict(version=VERSION,atoms=[[asdict(a) for a in row] for row in record]),ensure_ascii=False)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width+80}" height="{y+40}" viewBox="0 0 {width+80} {y+40}"><metadata>{escape(metadata)}</metadata><rect width="100%" height="100%" fill="white"/><g fill="none" stroke="currentColor" color="#171c20" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">'+''.join(groups)+'</g></svg>'

def spec():
    return dict(version=VERSION,rails=RAILS,circle_radii=RADII,stroke_width=STROKE,
                writing_direction='left_to_right',source_editions=list(EDITIONS.values()),
                recipes={k:list(v) for k,v in RECIPES.items()},
                spelling_alphabet=ALPHABET,
                namespace_introducers={'name':[22,6],'digits':[14,6],'edition':[22,14]},
                limits=['Semantic structure is read from the parsed AST, not inferred from symbol spellings.',
                        'Structured atoms decode to canonical Noema; this is not an OCR system.',
                        'Draft for visual feedback; existing v1/v2 encodings and fonts remain authoritative.'])

def main():
    import argparse
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input','-i',type=Path,required=True)
    cli.add_argument('--output','-o',type=Path,required=True)
    cli.add_argument('--width',type=int,default=1440)
    cli.add_argument('--scale',type=float,default=.58)
    args=cli.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(svg_document(args.input.read_text(encoding='utf-8'),args.width,args.scale),encoding='utf-8',newline='\n')

if __name__=='__main__':main()
