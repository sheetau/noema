"""Explicit rational analogue of restored cut definitions; not a real-cut proof."""
from copy import deepcopy
from fractions import Fraction
import json

from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue,SequenceValue
from noema.meaning_catalog import _references
from scripts.shared_cut_analysis import DEFINITIONS,require
from scripts.shared_cut_products import CUT
from scripts.shared_modality import call,v,op
from scripts.shared_reference import definition
from scripts.check_shared_real_cuts import num


def scalar_sorts(value):
    if value==CUT:return 'number'
    if isinstance(value,dict):return {k:scalar_sorts(v) for k,v in value.items()}
    if isinstance(value,list):return [scalar_sorts(v) for v in value]
    return value


def rational_projection(native,targets):
    """Change the represented value domain explicitly, retaining operator order.

    Only the 17 selected analysis bodies are projected. Their real-cut operands
    become rationals and their lower arithmetic becomes exact scalar arithmetic.
    Quantifiers are still over ALL rationals or sequences, never finite samples.
    """
    source={d['name']:d for d in normalize_document(native)['declarations']}
    arithmetic=['rationalbelow','rationaladd','rationalnegate','rationalmultiply']
    declarations=[deepcopy(source[n]) for n in arithmetic]
    def add(name,params,body,result='truth'):
        declarations.append(definition(name,[(p,'number') for p in params],result,body))
    add('cutvalid',['x'],op('equal',v('x'),v('x')))
    add('rationalcut',['x'],v('x'),'number')
    add('cutincluded',['left','right'],op('not',call('rationalbelow',v('right'),v('left'))))
    add('cutless',['left','right'],call('rationalbelow',v('left'),v('right')))
    add('cutadd',['left','right'],call('rationaladd',v('left'),v('right')),'number')
    add('cutdifference',['left','right'],call('rationaladd',v('left'),call('rationalnegate',v('right'))),'number')
    add('cutproduct',['left','right'],call('rationalmultiply',v('left'),v('right')),'number')
    # Kept explicit, so unsupported proof interpretations fail instead of
    # silently dropping the reciprocal from the derivative's difference quotient.
    declarations.append(dict(kind='primitive',name='cutreciprocal',parameters=['number'],result='number'))
    declarations += [scalar_sorts(d) for d in native['declarations'] if d['name'] in DEFINITIONS.values()]
    table={d['name']:d for d in declarations};needed=set(targets);pending=list(targets)
    require(needed<=set(table),'Unknown rational projection target')
    while pending:
        for name in _references(table[pending.pop()]):
            require(name in table,'Projection has an unknown dependency')
            if name not in needed:needed.add(name);pending.append(name)
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[d for d in declarations if d['name'] in needed],statements=[]))


def scalar_call(native,name,values,expected_number=None):
    doc=rational_projection(native,[name]);target=next(d for d in doc['declarations'] if d['name']==name)
    arithmetic=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,
        rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    primitive_names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    require(primitive_names<=set(arithmetic),'Unsupported scalar evaluation primitive')
    handlers={n:arithmetic[n] for n in primitive_names};args=[]
    def cell(fields):
        fields=tuple(Fraction(x) for x in fields)
        require(len(fields)==3,'A scalar cell has exactly three fields')
        return FunctionValue(('number',),'number',lambda i:fields[int(i)] if i in (0,1,2) else Fraction(0))
    for i,(p,value) in enumerate(zip(target['parameters'],values,strict=True)):
        sort=p['sort']
        if sort=='number':value=Fraction(value)
        elif sort['kind']=='sequence':
            value=SequenceValue(tuple(cell(f) for f in value),json.dumps(sort['element'],sort_keys=True,separators=(',',':')))
        elif callable(value):value=FunctionValue(('number',),'number',value)
        else:value=cell(value)
        label='diagnosticinput'+chr(97+i)
        doc['declarations'].append(dict(kind='primitive',name=label,parameters=[],result=sort))
        handlers[label]=lambda value=value:value;args.append(call(label))
    body=call(name,*args)
    if expected_number is not None:
        expected_number=Fraction(expected_number)
        body=op('equal',body,num(expected_number.numerator,expected_number.denominator))
    doc['statements']=[dict(kind='ask',body=body)]
    return evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=handlers)[0]['value']


def partition_diagnostics(native):
    rows=[]
    def check(label,target,values,expected,number=None):
        actual=scalar_call(native,target,values,number)
        require(actual==expected,'Projected partition diagnostic failed: '+label)
        rows.append(dict(name=label,target=target,expected=expected,actual=actual))
    for tag in (0,Fraction(1,2),1):check('tag_'+str(tag),'cuttaggedcell',((0,1,tag),),True)
    for label,cell in [('outside_left',(0,1,-1)),('outside_right',(0,1,2)),('zero_width',(1,1,1)),('negative_width',(1,0,0))]:
        check(label,'cuttaggedcell',(cell,),False)
    halves=((0,Fraction(1,2),Fraction(1,4)),(Fraction(1,2),1,Fraction(3,4)))
    for label,cells,lower,upper,expected in [
        ('connected',halves,0,1,True),('gap',((0,Fraction(1,4),0),(Fraction(1,2),1,1)),0,1,False),
        ('overlap',((0,Fraction(3,4),0),(Fraction(1,2),1,1)),0,1,False),
        ('reversed',tuple(reversed(halves)),0,1,False),('duplicated',(halves[0],halves[0],halves[1]),0,1,False),
        ('missing_end',(halves[0],),0,1,False),('empty',(),0,1,False),('wrong_start',halves,-1,1,False)]:
        check(label,'cutpartition',(cells,lower,upper),expected)
    check('mesh_strict','cutmeshbelow',(halves,1),True)
    check('mesh_equal_boundary','cutmeshbelow',(halves,Fraction(1,2)),False)
    check('mesh_negative','cutmeshbelow',(halves,-1),False)
    check('empty_mesh_is_vacuous','cutmeshbelow',((),1),True)
    check('empty_sum','cutriemannsum',((),lambda x:x),True,0)
    check('constant_sum','cutriemannsum',(((0,3,2),(3,10,8)),lambda x:Fraction(4,5)),True,8)
    check('tag_changes_identity_sum','cutriemannsum',(((0,1,0),),lambda x:x),False,1)
    for position,offset in [('left',Fraction(0)),('middle',Fraction(1,2)),('right',Fraction(1))]:
        cells=tuple((Fraction(i,3),Fraction(i+1,3),(i+offset)/3) for i in range(3))
        check(position+'_partition','cutpartition',(cells,0,1),True)
        check(position+'_affine_sum','cutriemannsum',(cells,lambda x:2*x+3),True,4+2*(offset-Fraction(1,2))/3)
    return rows
