"""Small distinguishing interpretations, not a general translation proof."""
import sys
sys.dont_write_bytecode = True
import json
import os
from fractions import Fraction
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.environ.get('NOEMA_SOURCE', str(ROOT.parent / 'noema')))
from noema.constructed import parse

samples = json.loads((ROOT / 'src/samples.json').read_text(encoding='utf-8'))
statements = {s['id']:parse(s['source'])['statements'][0]['body'] for s in samples}
domain = ['aki','nao','booka','bookb']
checks = 0

def evaluate(node, model, env=None):
    env = {} if env is None else env
    kind = node['kind']
    ev = lambda n: evaluate(n,model,env)
    if kind == 'variable': return env[node['name']]
    if kind == 'number': return Fraction(node['numerator'],node['denominator'])
    if kind == 'call': return model[node['symbol']](*(ev(n) for n in node['arguments']))
    if kind == 'quote': return node['body']
    if kind == 'function_ref': return model[node['symbol']]
    if kind == 'apply': return ev(node['function'])(*(ev(n) for n in node['arguments']))
    if kind == 'sequence': return tuple(ev(n) for n in node['items'])
    if kind == 'length': return Fraction(len(ev(node['sequence'])))
    if kind in ('forall','exists'):
        values = [Fraction(-1),Fraction(0),Fraction(2,3)] if node['sort']=='number' else domain
        results = (evaluate(node['body'],model,{**env,node['variable']:x}) for x in values)
        return (all if kind=='forall' else any)(results)
    values = [ev(n) for n in node['arguments']]
    if kind == 'not': return not values[0]
    if kind == 'and': return values[0] and values[1]
    if kind == 'or': return values[0] or values[1]
    if kind == 'implies': return not values[0] or values[1]
    if kind == 'equal': return values[0] == values[1]
    raise ValueError(kind)

def check(id, model, expected):
    global checks
    actual=evaluate(statements[id],model)
    assert actual is expected, (id,actual,expected)
    checks+=1

people=lambda x:x in ('aki','nao')
books=lambda x:x in ('booka','bookb')
base={'person':people,'book':books}
# Different books per reader must not become one shared book, or no readers.
different={('aki','booka'),('nao','bookb')}
check('ja-scope',{**base,'read':lambda x,b:(x,b) in different},True)
check('ja-scope',{**base,'read':lambda x,b:b=='booka'},False)
check('ja-unread',{**base,'choose':lambda x,b:x=='aki' and b=='booka','read':lambda x,b:False},True)
check('ja-unread',{**base,'choose':lambda x,b:x=='aki' and b=='booka','read':lambda x,b:x=='nao' and b=='booka'},False)
# Quoting a proposition must not execute it or assert that it is true.
def forbidden(*args): raise AssertionError('A quoted proposition was evaluated')
report={'taro':lambda:'taro','hanako':lambda:'hanako','come':forbidden}
check('ja-quote',{**report,'say':lambda person,quote:False},True)
check('ja-quote',{**report,'say':lambda person,quote:quote['kind']=='not'},False)
check('en-recommend',{**base,'recommend':lambda x,b:(x,b) in different,'read':lambda x,b:(x,b) in different},True)
check('en-recommend',{**base,'recommend':lambda x,b:(x,b) in different,'read':lambda x,b:True},False)
only={'mina':lambda:'aki','door':lambda:'door','open':lambda d:True}
check('en-only',{**only,'know':lambda x,q:x=='aki'},True)
check('en-only',{**only,'know':lambda x,q:people(x)},False)
check('en-only',{**only,'open':lambda d:False,'know':lambda x,q:x=='aki'},False)
unless={'reviewer':people,'proposal':lambda:'proposal'}
check('en-unless',{**unless,'agree':lambda x:x=='aki','accept':lambda p:False},True)
check('en-unless',{**unless,'agree':lambda x:x=='aki','accept':lambda p:True},False)
# Agreement is necessary, not sufficient: rejection can still occur.
check('en-unless',{**unless,'agree':lambda x:True,'accept':lambda p:False},True)
zh={**base,'table':lambda:'table','me':lambda:'aki','on':lambda b,t:b=='booka'}
check('zh-topic',{**zh,'read':lambda x,b:b=='bookb'},True)
check('zh-topic',{**zh,'read':lambda x,b:b=='booka'},False)
check('fr-relative',{**base,'read':lambda x,b:b=='booka','like':lambda x,b:False},True)
check('fr-relative',{**base,'read':lambda x,b:b=='booka','like':lambda x,b:x=='nao' and b=='booka'},False)
for id,left,right in [('es-notall','arrive','stay'),('de-relative','silent','agree'),('ar-notall','glitter','gold')]:
    check(id,{left:people,right:lambda x:x=='aki'},True)
    check(id,{left:people,right:people},False)
check('math-fraction',{'add':lambda a,b:a+b},True)
check('math-fraction',{'add':lambda a,b:a-b},False)
check('math-commute',{'add':lambda a,b:a+b},True)
check('math-commute',{'add':lambda a,b:a-b},False)
check('math-sequence',{},True)
check('reading',{'aki':lambda:'aki','book':lambda:'booka','nao':lambda:'nao','give':lambda x,b,y:(x,b,y)==('aki','booka','nao')},True)

# Bound all circles, arcs, lines and dots using the adopted geometry parser.
from scripts import concept2_composition as geometry
for sample in samples:
    path=ROOT / 'public/glyphs' / f'{sample["id"]}.svg'
    raw=path.read_text(encoding='utf-8')
    tree=ET.fromstring(raw)
    _,_,width,height=map(float,tree.attrib['viewBox'].split())
    left,top,right,bottom=geometry.bounds(geometry.from_svg(raw))
    assert 1 < left < right < width-1 and 1 < top < bottom < height-1, sample['id']
print(f'{checks} distinguishing evaluations passed; all 15 SVG viewports contain their complete geometry.')
print('Finite examples check scope and interpretation, not general natural-language equivalence.')
