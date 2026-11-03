"""Public words and a bounded native grammar in the Kant drawing geometry.

This is an experimental fragment, not the frozen script. Placement follows the
actual Kant generator's rail search, radial routing and accumulated ink moment.
Unlike that generator, neither lexical identity nor branch position uses a
document registry. Outward references compose over the visible binder scope.
"""
from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
import json
import math

from scripts.balanced_circle_script import (
    SMALL, MEDIUM, LARGE, PITCH, MIN_GAP, MIN_RUN, EPS, circle, nucleus,
    near,
)
from scripts.kant_geometry_rules import geometry_check
from scripts.kant_readable_flow import route, boundary_port
from scripts.kant_geometry_reader import read_geometry, recover_seams
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_lexical_script import _glyph
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_word_forms import Word, symbol
from scripts.kant_public_lexicon import (
    vocabulary, words, root_words, parts_for, read_word, mark_boundaries, declarations_for, spellings,
)
from noema.constructed_discourse import normalize_document
from noema.grammar import number_word
from scripts.kant_lexical_context import use_context
from scripts.kant_scoped_types import TYPE_TOKENS, LIST_TOKENS, type_tokens, type_list_tokens, read_type, read_type_list
from scripts.kant_function_grammar import expression_type,application_type,require_description,require_question
from scripts.kant_number_grammar import START_TOKENS as NUMBER_STARTS,number_tokens,read_number

VERSION = 'kant-public-fragment-30-bound-argument-contact'
DECLARATION_TOKENS = frozenset(('primitive', 'definition'))
STATEMENT_TOKENS = frozenset(('ask_truth', 'suppose'))
APPLICATIONS = frozenset(('apply','quoted_application'))
SIGNATURE_HEADS = APPLICATIONS | {'answer_matches'}
DYNAMIC_ARITY = SIGNATURE_HEADS | {'sequence'}
MESSAGE_FORCES = ('assert','ask','direct')
SEQUENCE_FIELDS = {'length':('sequence',),'position':('sequence','index','value'),
                   'concat':('left','right'),'fold':('sequence','initial','step')}
RAIL_PAIRS={'small-upper-left-rim':(-1,-1),'small-upper-right-rim':(1,-1),
            'small-lower-left-rim':(-1,1),'small-lower-right-rim':(1,1)}
ARITY = {'and': 2, 'or': 2, 'implies': 2, 'equal': 2, 'not': 1, 'iff': 2,
         'question': 1, 'message_content': 1, 'full_name': 0, 'spelling': 0, **{'message_'+force:1 for force in MESSAGE_FORCES},
         'quote': 1, 'forall': 1, 'exists': 1, 'bound0': 0, 'bound1': 0,
         'function_ref': 0, 'and_shared': 2, 'lambda_individual': 1, 'evaluate': 2,
         'quote_raise': 1, 'bound_shift': 1, 'quoted_lift': 1, 'disquote': 1, 'content': 1,
         'forall_typed': 1, 'exists_typed': 1, 'lambda_typed': 1,
         **dict.fromkeys(TYPE_TOKENS | LIST_TOKENS | NUMBER_STARTS | STATEMENT_TOKENS | DECLARATION_TOKENS, 0),
         **{name:len(fields) for name,fields in SEQUENCE_FIELDS.items()}}
# Each tuple is a declared allograph, not an unconstrained rotation search.
# Existing lexical directions remain unchanged: rain S and above N are distinct.
GRAMMAR = {
    'and': ((MEDIUM, 'offset-left', None, 'none'),),
    'or': ((MEDIUM, 'offset-left', 6, 'radius'),),
    'not': ((MEDIUM, None, 3, 'radius'),),
    'implies': ((MEDIUM, 'offset-left', 2, 'radius'),),
    'equal': tuple((LARGE, None, d, 'outer') for d in (1, 7, 3, 5)),
    'quote': tuple((LARGE, 'nested', d, 'radius') for d in (2, 6)),
    'forall': ((LARGE, 'nested', 4, 'radius'),),
    'exists': ((LARGE, 'nested', 0, 'radius'),),
    'bound0': ((SMALL, None, None, 'none'),),
    'bound1': tuple((LARGE, 'small-concentric', d, 'outer') for d in (1, 7, 3, 5)),
    'function_ref': tuple((LARGE, 'nested', d, 'radius') for d in (5, 3)),
    'and_shared': ((MEDIUM, 'offset-left', 0, 'radius'),),
    'lambda_individual': ((LARGE, 'offset', 4, 'radius'),),
    'evaluate': ((MEDIUM, 'offset-left', 1, 'radius'),),
    'apply': ((LARGE, 'offset-left', 1, 'radius'),),
    'quoted_application': ((LARGE, 'small-upper-left-rim', 1, 'radius'),),
    'quoted_lift': ((LARGE, 'small-upper-right-rim', 3, 'radius'),),
    'disquote': ((LARGE, 'small-lower-left-rim', 7, 'radius'),),
    'content': ((LARGE, 'small-lower-right-rim', 5, 'radius'),),
    'quote_raise': ((LARGE, 'nested', 1, 'radius'),),
    'bound_shift': ((MEDIUM, 'offset-left', 7, 'radius'),),
    'forall_typed': ((LARGE, 'offset-left', 4, 'radius'),),
    'exists_typed': ((LARGE, 'offset-left', 0, 'radius'),),
    'lambda_typed': ((LARGE, 'offset', 0, 'radius'),),
    'type_individual': ((LARGE, 'small-offset-left', 0, 'radius'),),
    'type_number': ((LARGE, 'small-offset-left', 1, 'radius'),),
    'type_truth': ((LARGE, 'small-offset-left', 2, 'radius'),),
    'type_situation': ((LARGE, 'small-offset-left', 3, 'radius'),),
    'type_content': ((LARGE, 'small-offset-left', 5, 'radius'),),
    'type_message': ((LARGE, 'small-offset-left', 6, 'radius'),),
    'type_sequence': ((LARGE, 'nested', 1, 'outer'),),
    'type_description': ((LARGE, 'nested', 3, 'outer'),),
    'type_question': ((LARGE, 'nested', 5, 'outer'),),
    'type_function': ((LARGE, 'nested', 7, 'outer'),),
    'types_more': ((LARGE, 'offset-left', 2, 'radius'),),
    'types_end': ((LARGE, 'offset-left', 6, 'radius'),),
    'number_positive': ((LARGE, 'offset', 5, 'outer'),),
    'number_negative': ((LARGE, 'offset', 3, 'outer'),),
    'sequence': ((LARGE, 'offset-left', 7, 'outer'),),
    'length': ((LARGE, 'offset', 6, 'radius'),),
    'position': ((LARGE, 'offset', 2, 'radius'),),
    'concat': ((LARGE, 'offset', 5, 'radius'),),
    'fold': ((LARGE, 'offset', 3, 'radius'),),
    'iff': ((LARGE, 'offset-left', 1, 'outer'),),
    'question': ((LARGE, 'nested', 7, 'radius'),),
    'answer_matches': ((LARGE, 'offset-left', 7, 'radius'),),
    'message_assert': ((LARGE, 'small-upper-left-rim', 0, 'radius'),),
    'message_ask': ((LARGE, 'small-upper-left-rim', 2, 'radius'),),
    'message_direct': ((LARGE, 'small-upper-left-rim', 4, 'radius'),),
    'message_content': ((LARGE, 'small-upper-left-rim', 1, 'outer'),),
    'ask_truth': ((LARGE, 'small-upper-left-rim', 3, 'radius'),),
    'suppose': ((LARGE, 'small-upper-left-rim', 7, 'radius'),),
    'primitive': ((LARGE, 'small-upper-right-rim', 0, 'radius'),),
    'definition': ((LARGE, 'small-upper-right-rim', 4, 'radius'),),
    'full_name': ((LARGE, 'small-upper-right-rim', 2, 'radius'),),
    'spelling': ((LARGE, 'small-lower-left-rim', 0, 'radius'),),
}


@lru_cache(maxsize=1)
def reserved_forms():
    """Reserve the other published roots before extending this native fragment.

    Only their public forms are needed here, not their definitions or models.
    Keeping those meanings unchanged does not require revalidating them.
    """
    source = json.loads(files('noema').joinpath(
        'resources/visible-defined-vocabulary-v1.json').read_text(encoding='utf-8'))
    if source['schema'] != 'noema-visible-defined-vocabulary-source-1' or source['edition'] != 2:
        raise ValueError('Unknown public root reservation')
    return source['forms']


def arity(token):
    if token in APPLICATIONS:raise ValueError('Application arity requires the visible function type')
    if token=='answer_matches':raise ValueError('Answer arity requires the visible question type')
    if token=='sequence':raise ValueError('Sequence arity requires its delimited item list')
    if token in ARITY:
        return ARITY[token]
    if token not in words():raise ValueError('Unknown public word signature')
    return len(words()[token][1]['parameters'])


def side_slot(token,*,count=None):
    """A public signature fixes the side role before any argument is read."""
    count=arity(token) if count is None else count
    if count<2:
        return None
    if token in words():
        situations=[i for i,t in enumerate(words()[token][1]['parameters']) if t=='situation']
        if situations:
            return situations[-1]
    return count//2


def side_order(token,supplied=(),*,count=None):
    """A prefix of this public order identifies any visible branch count."""
    count=arity(token) if count is None else count
    available=[i for i in range(count) if i not in supplied]
    if len(available)<2:return []
    if token=='sequence':return available[:-1]
    first=side_slot(token,count=count)
    if first not in available:return available[1:]
    continuation=next(i for i in available if i!=first)
    return [first]+[i for i in available if i not in (first,continuation)]


def event_sides(event):
    return ([] if event['side'] is None else [event['side']])+event.get('extra_sides',[])


def terminal_word(token):
    if token not in words() and token not in ('bound0','bound1'):
        return False
    parts=parts_for().get(token,(token,))
    return (arity(token)==0 and len(parts)<=4
            and all(not near(forms(p)[0]['radius'],LARGE) for p in parts))


def shared_slot(token):
    """One public role per predicate; never choose it from argument values."""
    if token not in words():
        return None
    entry=words()[token][1]
    if entry['result']!='truth':
        return None
    situations=[i for i,t in enumerate(entry['parameters']) if t=='situation']
    if situations:
        return situations[-1]
    if entry['parameters']==['individual']:
        return 0
    return None


def used_words(value):
    used = set()
    def collect(value):
        if isinstance(value, dict):
            if value.get('kind') in ('call', 'function_ref'):
                used.add(value['symbol'])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(value)
    return used


def validate_native(statement):
    used = used_words(statement)
    if not used <= words().keys():
        raise ValueError('Unknown public word')
    declarations = declarations_for(tuple(sorted(used)))
    checked = normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=declarations, statements=[statement]))['statements'][0]
    if checked != statement:
        raise ValueError('Fragment requires canonical native syntax')
    return statement


def validate_declaration(declaration, *, new_name=False):
    if new_name:
        from scripts.visible_word_forms import read_symbol
        if read_symbol(declaration.get('name'),vocabulary()).kind not in ('root','compound'):
            raise ValueError('Declaration requires a root or compound name')
    elif declaration.get('name') not in parts_for():
        raise ValueError('Declaration requires a published name spelling')
    used=used_words(declaration)
    if declaration['name'] in used:
        raise ValueError('Declaration cannot depend on itself')
    if not used<=words().keys():raise ValueError('Unknown declaration dependency')
    dependencies=declarations_for(tuple(sorted(used)))
    if any(d['name']==declaration['name'] for d in dependencies):
        raise ValueError('Declaration cannot depend on itself indirectly')
    checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[*dependencies,declaration],statements=[]))['declarations'][-1]
    if checked!=declaration:raise ValueError('Declaration requires canonical native syntax')
    return declaration


def validate_spelling(record):
    from scripts.visible_word_forms import canonical
    if set(record)!={'kind','name','parts'} or record['kind']!='spelling':
        raise ValueError('Expected a spelling record')
    name=record['name'];parts=record['parts']
    if name not in words():raise ValueError('Spelling target is not declared')
    if name in root_words():raise ValueError('Cannot rename a root word')
    if not isinstance(parts,list) or not 2<=len(parts)<=4:raise ValueError('Spelling requires two to four root components')
    word=canonical(Word('compound',tuple(parts)),vocabulary())
    if list(word.parts)!=parts:raise ValueError('Spelling requires canonical root components')
    tokens=tuple(symbol(Word('root',(part,)),vocabulary()) for part in parts)
    existing=spellings().get(tokens)
    if existing is not None:
        raise ValueError('Spelling already registered' if existing==name else 'Spelling collides with another word')
    return record


def forms(token, x=0., y=PITCH):
    if isinstance(token,tuple):
        from scripts.kant_root_overlap import forms as overlap_forms
        return overlap_forms(token,x,y)
    if token not in GRAMMAR:
        result = _glyph(root_words()[token][1]['form'], x, y)
        return [result]
    result = []
    for radius, pair, direction, mode in GRAMMAR[token]:
        if pair in RAIL_PAIRS:
            # One rail of vertical separation, with the small center exactly
            # on the large rim. Both external ports remain on the large ring.
            g=nucleus(x,y,radius,None,direction,mode=mode)
            sx,sy=RAIL_PAIRS[pair]
            g['shapes'].append(circle(x+sx*math.sqrt(radius**2-PITCH**2),y+sy*PITCH,SMALL))
            g.update(pair=pair,companion=SMALL)
            result.append(g)
            continue
        special = pair == 'small-concentric'
        g = nucleus(x, y, radius, None if special else 'offset-left' if pair=='small-offset-left' else pair,
                    direction, mode=mode, companion=SMALL if pair=='small-offset-left' else None)
        if pair == 'small-concentric':
            g['shapes'].append(circle(x, y, SMALL))
        result.append(g)
    return result


def feature(geometry, ids):
    """Observable word signature; merging a ray with a connection is harmless.

    All centers, relative offsets, center directions and terminal diagonals
    matter. External ports are layout, and the ray/external extent distinction
    carries no lexical contrast. Thus authored SVG segmentation is irrelevant.
    """
    cs = [geometry['circles'][i] for i in ids]
    main = max(cs, key=lambda c: {'small': 0, 'medium': 1, 'large': 2}[c['size']])
    return tuple(sorted((c['size'], round(c['center'][0]-main['center'][0], 5),
                         round(c['center'][1]-main['center'][1], 5),
                         -1 if c['center_direction'] is None else c['center_direction'],
                         tuple(c['outer_diagonals'])) for c in cs))


@lru_cache(maxsize=1)
def table():
    result = {}
    for token in (*root_words(), *GRAMMAR):
        for g in forms(token):
            geometry = read_geometry(g['shapes'])
            key = feature(geometry, range(len(geometry['circles'])))
            if key in result and result[key] != token:
                raise ValueError('Public word collision')
            result[key] = token
    return result


def split(node, scope=()):
    """Validate the exact supported native syntax before producing any ink."""
    if not isinstance(node, dict):
        raise ValueError('Expected native expression')
    kind = node.get('kind')
    if kind == 'number':
        token,children,child_scope=number_tokens(node)[0],[],scope
    elif kind=='sequence' and set(node)=={'kind','element','items'}:
        if not isinstance(node['items'],list):raise ValueError('Sequence items must be an array')
        token,children,child_scope=kind,node['items'],scope
    elif kind in SEQUENCE_FIELDS and set(node)=={'kind',*SEQUENCE_FIELDS[kind]}:
        token,children,child_scope=kind,[node[k] for k in SEQUENCE_FIELDS[kind]],scope
    elif kind=='question' and set(node)=={'kind','function'}:
        token,children,child_scope=kind,[node['function']],scope
    elif kind=='answer_matches' and set(node)=={'kind','question','arguments'}:
        if not isinstance(node['arguments'],list):raise ValueError('Expected answer argument list')
        token,children,child_scope=kind,[node['question'],*node['arguments']],scope
    elif kind=='message' and set(node)=={'kind','force','content'}:
        if node['force'] not in MESSAGE_FORCES:raise ValueError('Unknown message force')
        token,children,child_scope='message_'+node['force'],[node['content']],scope
    elif kind=='message_content' and set(node)=={'kind','message'}:
        token,children,child_scope=kind,[node['message']],scope
    elif kind == 'call' and set(node) == {'kind', 'symbol', 'arguments'}:
        token = node['symbol']
        if token not in words() or not isinstance(node['arguments'], list):
            raise ValueError('Unknown public root')
        children, child_scope = node['arguments'], scope
    elif kind == 'function_ref' and set(node) == {'kind', 'symbol'}:
        if node['symbol'] not in words():
            raise ValueError('Unknown public function reference')
        token, children, child_scope = kind, [], scope
    elif kind == 'lambda' and set(node) == {'kind', 'parameters', 'body'}:
        params=node['parameters']
        if not isinstance(params,list) or any(not isinstance(p,dict) or set(p)!={'name','sort'} for p in params):
            raise ValueError('Invalid lambda parameters')
        token='lambda_individual' if len(params)==1 and params[0]['sort']=='individual' else 'lambda_typed'
        children,child_scope = [node['body']],(*scope,*(p['name'] for p in params))
    elif kind == 'evaluate' and set(node) == {'kind','content','situation'}:
        token,children,child_scope = kind,[node['content'],node['situation']],scope
    elif kind == 'content' and set(node) == {'kind','variable','body'}:
        token,children,child_scope = kind,[node['body']],(*scope,node['variable'])
    elif kind in APPLICATIONS and set(node) == {'kind','function','arguments'}:
        if not isinstance(node['arguments'],list):raise ValueError('Expected function argument list')
        token,children,child_scope = kind,[node['function'],*node['arguments']],scope
    elif kind in ('quoted_lift','disquote') and set(node) in ({'kind','description'},{'kind','description','rank'}):
        if 'rank' in node and (kind!='disquote' or type(node['rank']) is not int or node['rank']<0):
            raise ValueError('Invalid disquotation rank')
        token,children,child_scope = kind,[node['description']],scope
    elif kind in ('and', 'or', 'implies', 'equal', 'not', 'iff') and set(node) == {'kind', 'arguments'}:
        token, children, child_scope = kind, node['arguments'], scope
        if not isinstance(children, list):
            raise ValueError('Expected argument list')
    elif kind == 'quote' and set(node) == {'kind', 'body', 'rank'}:
        if type(node['rank']) is not int or not 1 <= node['rank'] <= 128:
            raise ValueError('Quotation rank outside the drawing resource limit')
        child = deepcopy(node)
        if child['rank'] == 1:
            del child['rank']
        else:
            child['rank'] -= 1
        token, children, child_scope = 'quote_raise', [child], scope
    elif kind == 'quote' and set(node) == {'kind', 'body'}:
        token, children, child_scope = kind, [node['body']], ()
    elif kind in ('forall', 'exists') and set(node) == {'kind', 'variable', 'sort', 'body'}:
        token = kind if node['sort']=='individual' else kind+'_typed'
        children, child_scope = [node['body']], (*scope, node['variable'])
    elif kind == 'variable' and set(node) == {'kind', 'name'}:
        if node['name'] not in scope:
            raise ValueError('Unbound variable, including across a quotation')
        distance = scope[::-1].index(node['name'])
        if distance < 2:
            token, children, child_scope = 'bound'+str(distance), [], scope
        else:
            # The reference is unchanged; one nearest binder is excluded from
            # its search. Repeating this rule needs no indexed glyph inventory.
            token, children, child_scope = 'bound_shift', [node], scope[:-1]
    else:
        raise ValueError('Native constructor outside this fragment')
    if token not in DYNAMIC_ARITY and len(children) != arity(token):
        raise ValueError('Public arity mismatch')
    return token, children, child_scope


def shared_argument_token(node,scope):
    if node.get('kind')!='and' or len(node['arguments'])!=2:return None
    a,b=node['arguments']
    if not all(c.get('kind')=='call' and c['symbol'] in words() and shared_slot(c['symbol']) is not None
        and len(c['arguments'])==arity(c['symbol']) for c in (a,b)):return None
    slots=[shared_slot(c['symbol']) for c in (a,b)]
    types=[words()[c['symbol']][1]['parameters'][s] for c,s in zip((a,b),slots)]
    if types[0]!=types[1] or a['arguments'][slots[0]]!=b['arguments'][slots[1]]:return None
    token,children,_=split(a['arguments'][slots[0]],scope)
    return token if not children and terminal_word(token) else None


def event_count(stream):
    return len(stream)+sum(event_count(side) if isinstance(side,list)
        else len(parts_for().get(side,(side,))) for e in stream for side in event_sides(e))


def events(statement, branch=True, sharing=True, subexpressions=True, unbranched=(),nested=True,
           multiple=False,branch_limits=None,full_names=False):
    is_declaration=statement.get('kind') in DECLARATION_TOKENS
    is_spelling=statement.get('kind')=='spelling'
    if is_spelling:validate_spelling(statement)
    elif is_declaration:validate_declaration(statement,new_name=full_names)
    else:validate_native(statement)
    result = []
    def contains_sharing(node,scope):
        if shared_argument_token(node,scope) is not None:return True
        _,children,child_scope=split(node,scope)
        return any(contains_sharing(c,child_scope) for c in children)
    def emit(token, side, path, output,extra_sides=()):
        parts = parts_for().get(token, (token,))
        for i, part in enumerate(parts):
            event = dict(token=part, side=side if i == len(parts)-1 else None,
                         depth=len(path), path=list(path))
            if i == 0 and token in parts_for():
                event['word'] = token
            if i==len(parts)-1 and extra_sides:event['extra_sides']=list(extra_sides)
            output.append(event)
    def application(token,children,child_scope,path,output,allow_branches,supplied=(),header=()):
        order=side_order(token,supplied,count=len(children) if token in DYNAMIC_ARITY else None)
        limit=(branch_limits or {}).get(path,len(order) if multiple else 1)
        attached={}
        if branch and allow_branches and path not in unbranched and (not supplied or multiple):
            for slot in order[:limit]:
                side_token, descendants, _ = split(children[slot], child_scope)
                if not descendants and terminal_word(side_token):
                    attached[slot]=side_token
                elif subexpressions and (nested or not (sharing and contains_sharing(children[slot],child_scope))):
                    candidate=[]
                    visit(children[slot],child_scope,path+(slot,),candidate,nested)
                    attached[slot]=mark_boundaries(candidate)
                else:break
        sides=list(attached.values())
        emit(token,sides[0] if sides else None,path,output,sides[1:])
        for part in header:emit(part,None,path,output)
        for i,child in enumerate(children):
            if i not in supplied and i not in attached:
                visit(child,child_scope,path+(i,),output,allow_branches)
    def visit(node, scope, path, output, allow_branches=True):
        token, children, child_scope = split(node, scope)
        if token in NUMBER_STARTS:
            # Digits use existing shapes, but are not lexical word entries.
            for part in number_tokens(node):
                output.append(dict(token=part,side=None,depth=len(path),path=list(path)))
            return
        if token=='sequence':
            application(token,children,child_scope,path,output,allow_branches,header=type_tokens(node['element']))
            emit('types_end',None,path,output)
            return
        if token in ('forall_typed','exists_typed','lambda_typed'):
            emit(token,None,path,output)
            header=(type_list_tokens([p['sort'] for p in node['parameters']]) if token=='lambda_typed'
                    else type_tokens(node['sort']))
            for part in header:emit(part,None,path,output)
            visit(children[0],child_scope,path+(0,),output,allow_branches)
            return
        if token == 'function_ref':
            emit(token, None, path,output)
            emit(node['symbol'], None, path,output)
            return
        shared=shared_argument_token(node,scope) if sharing and branch and allow_branches and path not in unbranched else None
        if shared is not None:
            slots=[shared_slot(c['symbol']) for c in children]
            emit('and_shared', shared, path,output)
            for j,(predicate,slot) in enumerate(zip(children,slots)):
                application(predicate['symbol'],predicate['arguments'],scope,path+(j,),output,allow_branches,(slot,))
            return
        application(token,children,child_scope,path,output,allow_branches)
    def visit_statement(node,path):
        if node['kind']=='suppose':
            emit('suppose',None,path,result)
            visit(node['condition'],(),path+(0,),result)
            for i,child in enumerate(node['statements']):
                visit_statement(child,path+(i+1,))
            emit('types_end',None,path,result)
        else:
            if node['kind']=='ask' and expression_type(node['body'],(),words())=='truth':
                emit('ask_truth',None,path,result)
            visit(node['body'],(),path,result)
    if is_spelling:
        emit('spelling',None,(),result)
        emit(statement['name'],None,(),result)
        emit('types_end',None,(),result)
        for part in statement['parts']:
            result.append(dict(token=symbol(Word('root',(part,)),vocabulary()),side=None,depth=0,path=[]))
        emit('types_end',None,(),result)
    elif is_declaration:
        kind=statement['kind']
        emit(kind,None,(),result)
        if full_names:
            from scripts.visible_word_forms import read_symbol
            emit('full_name',None,(),result)
            word=read_symbol(statement['name'],vocabulary())
            for part in word.parts:
                result.append(dict(token=symbol(Word('root',(part,)),vocabulary()),side=None,depth=0,path=[]))
            emit('types_end',None,(),result)
        else:emit(statement['name'],None,(),result)
        parameters=statement['parameters']
        types=parameters if kind=='primitive' else [p['sort'] for p in parameters]
        for token in type_list_tokens(types):emit(token,None,(),result)
        if kind=='primitive':
            for token in type_tokens(statement['result']):emit(token,None,(),result)
        else:visit(statement['body'],tuple(p['name'] for p in parameters),(0,),result)
    else:visit_statement(statement,())
    if event_count(result) > 512:
        raise ValueError('Fragment expression budget')
    return mark_boundaries(result)


def compile_statement(statement, **options):
    if statement.get('kind') in DECLARATION_TOKENS|{'spelling'}:raise ValueError('Expected a statement, not a declaration')
    return _compile_item(statement,**options)


def compile_declaration(declaration, **options):
    if declaration.get('kind') not in DECLARATION_TOKENS:raise ValueError('Expected a declaration')
    return _compile_item(declaration,**options)


def compile_spelling(record, **options):
    if record.get('kind')!='spelling':raise ValueError('Expected a spelling record')
    return _compile_item(record,**options)


def _compile_item(statement, *, branch=True, silent=True, sharing=True, lexicon=None, local_checks=True, contacts=True, subexpressions=True, interleave=True,nested=True,multiple=False,full_names=False,overlap=False):
    with use_context(lexicon):
        unbranched=set();branch_limits={}
        while True:
            try:
                drawing=_compile_statement(statement, branch=branch, silent=silent, sharing=sharing,
                    local_checks=local_checks,contacts=contacts,subexpressions=subexpressions,unbranched=unbranched,
                    interleave=interleave,nested=nested,multiple=multiple,branch_limits=branch_limits,full_names=full_names,overlap=overlap)
                drawing['unbranched_paths']=[list(p) for p in sorted(unbranched)]
                if multiple:drawing['branch_limits']=[dict(path=list(p),maximum=k) for p,k in sorted(branch_limits.items())]
                return drawing
            except PlacementFailure as error:
                if error.branch_counts:
                    path,count=error.branch_counts[-1]
                    branch_limits[path]=count-1
                    continue
                candidates=[p for p in error.candidates if p not in unbranched]
                if not candidates:raise
                # An optional branch without a legal continuation stays on
                # the main flow. Its tokens, type and references are retained.
                unbranched.add(candidates[-1])


class PlacementFailure(ValueError):
    def __init__(self,message,candidates,branch_counts=()):
        super().__init__(message)
        self.candidates=candidates
        self.branch_counts=branch_counts


def single_medium(glyph):
    return near(glyph['radius'],MEDIUM) and sum(s['kind']=='circle' for s in glyph['shapes'])==1


def fixed_middle_events(stream):
    result=set();start=0
    for end in range(1,len(stream)+1):
        if end==len(stream) or not stream[end].get('lexical_seam'):
            if any(near(forms(e['token'])[0]['radius'],LARGE) for e in stream[start:end]):
                result.update(range(start,end))
            start=end
    return result


def word_branch(token, main, moment, depth, *, contacts=True):
    """Place a closed prefix expression or legacy terminal word on one branch."""
    stream=token if isinstance(token,list) else [dict(token=p,**({'word':token} if i==0 else {}))
        for i,p in enumerate(parts_for().get(token,(token,)))]
    parts=[e['token'] for e in stream]
    fixed_middle=fixed_middle_events(stream)
    template=forms(parts[0])[0]
    side_r=template['radius'];radius=main['radius'];x,y=main['x'],main['y']
    side_y=2*PITCH-y if y!=PITCH else (0. if moment>0 else 2*PITCH)
    side_x=x if len(parts)==1 and abs(side_y-y)>=radius+side_r+MIN_GAP else main['right']+side_r+2*MIN_RUN+PITCH
    shapes=[];paths=[];previous=main['exit'];entry=None;first_port=None;centers=[];right=main['right']
    last_glyph=None;contact_used=False;invisible=[]
    for index,part in enumerate(parts):
        event=stream[index]
        seam=bool(event.get('lexical_seam'))
        local_template=forms(part)[0]
        start=side_x if index==0 else right+MIN_GAP-local_template['left']
        chosen=None
        if (contacts and not contact_used and not event.get('word') and not seam and last_glyph
            and index not in fixed_middle
            and single_medium(last_glyph) and single_medium(local_template)):
            contact_y=PITCH if not near(previous['y'],PITCH) else side_y
            glyph=forms(part,previous['x']+PITCH,contact_y)[0]
            start_port=boundary_port(previous,(glyph['x'],glyph['y']))
            if entry is None or math.dist(start_port,entry)>=EPS:
                try:geometry_check(main['shapes']+shapes+glyph['shapes'],main['paths']+paths+glyph['paths'])
                except ValueError:pass
                else:chosen=glyph,None,[],'contact'
        for extra in (0.,12.,28.,48.,72.,104.,160.):
            if chosen is not None:break
            glyph=forms(part,start+extra,previous['y'] if seam else PITCH if index in fixed_middle else side_y)[0]
            obstacles=main['shapes']+shapes+glyph['shapes']
            if seam:
                edge=dict(kind='invisible',centers=[(previous['x'],previous['y']),(glyph['x'],glyph['y'])])
                try:geometry_check(obstacles,main['paths']+paths+glyph['paths'],invisible+[edge])
                except ValueError:continue
                chosen=glyph,None,[],'seam';break
            link=route(previous,glyph['entry'],[s for s in obstacles if s['kind']=='circle'],depth,obstacles,
                       forbidden_start=() if entry is None else (entry,),detours=isinstance(token,list))
            if link is None:continue
            path,segments=link
            try:geometry_check(obstacles+segments,main['paths']+paths+glyph['paths']+[path])
            except ValueError:continue
            chosen=glyph,path,segments,'visible';break
        if chosen is None:return None
        glyph,path,segments,kind=chosen
        if index==0:first_port=path[0]
        shapes+=glyph['shapes']+segments;paths+=glyph['paths']+([] if path is None else [path])
        centers.append([glyph['x'],glyph['y']]);right=glyph['right']
        entry=None if kind=='seam' else boundary_port(glyph['entry'],(previous['x'],previous['y']) if kind=='contact' else path[-2])
        if kind=='contact':contact_used=True
        if kind=='seam':invisible.append(dict(kind='invisible',centers=[(previous['x'],previous['y']),(glyph['x'],glyph['y'])]))
        previous=glyph['exit'];last_glyph=glyph
    return dict(shapes=shapes,paths=paths,port=first_port,centers=centers,invisible=invisible)


def _compile_statement(statement, *, branch=True, silent=True, sharing=True, local_checks=True,contacts=True,subexpressions=True,unbranched=(),interleave=True,nested=True,multiple=False,branch_limits=None,full_names=False,overlap=False):
    """Reuse the Kant search with public glyphs and visible terminal arguments."""
    stream = events(statement, branch, sharing, subexpressions,unbranched,nested and interleave,
        multiple and interleave,branch_limits,full_names)
    if overlap:
        from scripts.kant_root_overlap import compact_events
        stream=compact_events(stream)
    if interleave and any(isinstance(e['side'],list) or e.get('extra_sides') for e in stream):
        from scripts.kant_interleaved_layout import compile_stream
        try:return compile_stream(stream,contacts=contacts)
        except PlacementFailure as error:
            def branch_counts(chain):
                result=[]
                for event in chain:
                    sides=event_sides(event)
                    if len(sides)>1:result.append((tuple(event['path']),len(sides)))
                    for side in sides:
                        if isinstance(side,list):result+=branch_counts(side)
                return result
            counts=sorted(branch_counts(stream),key=lambda item:(len(item[0]),item[0]))
            if counts:raise PlacementFailure(str(error),[],counts) from error
            def nested_paths(chain,inside=False):
                result=[]
                for e in chain:
                    if inside and e['side'] is not None and e['token']!='and_shared':
                        result.append(tuple(e['path']))
                    if isinstance(e['side'],list):result+=nested_paths(e['side'],True)
                return result
            candidates=sorted(set(nested_paths(stream)),key=lambda p:(len(p),p))
            if candidates:
                raise PlacementFailure(str(error),candidates) from error
            drawing=_compile_statement(statement,branch=branch,silent=silent,sharing=sharing,
                local_checks=local_checks,contacts=contacts,subexpressions=subexpressions,
                unbranched=unbranched,interleave=False,nested=False,overlap=overlap)
            drawing['layout']='serial-fallback'
            drawing['interleaving_failure']=str(error)
            return drawing
    # A required silent seam joins centers on one rail. If any nucleus in a
    # consecutive seam run is large, choose the middle rail for the entire
    # run before placement. Do not discover this only after placing its prefix.
    fixed_middle = fixed_middle_events(stream)
    shapes, paths, groups, invisible = [], [], [], []
    previous = None
    previous_entry = None
    moment = 0.
    word_contact=False
    for event_index, event in enumerate(stream):
        if event.get('word') is not None:word_contact=False
        # Same candidate-window strategy as the actual Kant generator. A
        # candidate is provisional: the complete sentence is checked below.
        # Keep the complete-prefix mode for independent equivalence probes.
        first = groups[-3] if local_checks and len(groups) >= 3 else None
        recent = shapes[first['shape_start']:] if first else shapes
        recent_paths = paths[first['path_start']:] if first else paths
        token = event['token']
        template = forms(token)[0]
        radius = template['radius']
        contact_candidate=(contacts and not word_contact and previous is not None
            and token in root_words() and not event.get('word') and not event.get('lexical_seam')
            and near(previous['radius'],MEDIUM) and single_medium(template)
            and single_medium(forms(stream[event_index-1]['token'])[0]))
        choices = []
        for y in ([PITCH] if near(radius, LARGE) else [0., PITCH, 2*PITCH]):
            if event_index in fixed_middle and not near(y, PITCH):
                continue
            if event.get('lexical_seam') and previous and not near(y, previous['y']):
                continue
            can_touch=contact_candidate and near(abs(y-previous['y']),PITCH)
            for extra in ((None,) if can_touch else ())+(0., 12., 28., 48., 72., 104., 160.):
                touching=extra is None
                left = groups[-1]['right']+MIN_GAP+(extra or 0.) if groups else 12.
                x = previous['x']+PITCH if touching else left-template['left']
                found = False
                for main in forms(token, x, y):
                    local, local_paths = deepcopy(main['shapes']), deepcopy(main['paths'])
                    side_ports = []
                    side = None
                    if event['side'] is not None:
                        side=word_branch(event['side'],main,moment,event['depth'],contacts=contacts)
                        if side is None:continue
                        local+=side['shapes'];local_paths+=side['paths'];side_ports.append(side['port'])
                    edge = None
                    seam = previous and (event.get('lexical_seam') or
                        silent and token == 'quote' and near(previous['y'], y) and not groups[-1]['side_centers'])
                    if previous:
                        if touching:
                            start_port=boundary_port(previous,(x,y))
                            if previous_entry is not None and math.dist(start_port,previous_entry)<EPS:continue
                            entry_port=boundary_port(main['entry'],(previous['x'],previous['y']))
                            if any(math.dist(entry_port,p)<EPS for p in side_ports):continue
                            edge=dict(kind='tangent',entry_port=entry_port)
                        elif seam:
                            edge = dict(kind='invisible', centers=[(previous['x'], previous['y']), (x, y)])
                        else:
                            link = route(previous, main['entry'],
                                [s for s in recent+local if s['kind'] == 'circle'], event['depth'], recent+local,
                                forbidden_start=() if previous_entry is None else (previous_entry,),
                                forbidden_end=side_ports,detours=True)
                            if link is None:
                                continue
                            p, segments = link
                            local += segments; local_paths.append(p)
                            edge = dict(kind='visible', entry_port=boundary_port(main['entry'], p[-2]))
                    try:
                        geometry_check(recent+local, recent_paths+local_paths)
                    except ValueError:
                        continue
                    circles = [s for s in local if s['kind'] == 'circle']
                    delta = sum(c['r']**2*(c['y']-PITCH)/PITCH for c in circles)
                    right = max(c['x']+c['r'] for c in circles)
                    # A branch may occupy the rightward port. Do not commit
                    # a middle-rail nucleus if its forced-middle successor
                    # then has no legal continuation. Test the actual next
                    # form, not an arbitrary direction/semantic allograph.
                    next_index=event_index+1
                    if side and next_index<len(stream) and not stream[next_index].get('lexical_seam'):
                        next_token=stream[next_index]['token']
                        next_template=forms(next_token)[0]
                        probe_x=right+MIN_GAP+160-next_template['left']
                        available=False
                        for probe_y in ([PITCH] if next_index in fixed_middle else [0.,PITCH,2*PITCH]):
                            for probe in forms(next_token,probe_x,probe_y):
                                obstacles=recent+local+probe['shapes']
                                entry_port=edge.get('entry_port') if edge else None
                                link=route(main['exit'],probe['entry'],
                                    [s for s in obstacles if s['kind']=='circle'],stream[next_index]['depth'],obstacles,
                                        forbidden_start=() if entry_port is None else (entry_port,),detours=True)
                                if link is not None:
                                    available=True;break
                            if available:break
                        if not available:continue
                    imbalance = abs(moment+delta)/MEDIUM**2
                    score = max(0., imbalance-2.)*14+imbalance*.35+(right-left)*.11
                    if previous and near(previous['y'], y):
                        score += 2
                    if previous and near(abs(previous['y']-y), 2*PITCH):
                        score += 22
                    choices.append((score, main, side, local, local_paths, edge, delta, right))
                    found = True
                if found and not touching:
                    break
        if not choices:
            raise PlacementFailure('No legal public placement: '+str(token)+' at '+str(event['path']),
                [tuple(e['path']) for e in stream[:event_index+1] if isinstance(e['side'],list)])
        _, main, side, local, local_paths, edge, delta, right = min(choices, key=lambda c:c[0])
        shape_start, path_start = len(shapes), len(paths)
        shapes += local; paths += local_paths; moment += delta
        if side:invisible+=side['invisible']
        groups.append(dict(token=token, center=[main['x'], main['y']], right=right,
                           shape_start=shape_start,path_start=path_start,main_right=main['right'],
                           expression_branch=isinstance(event['side'],list),
                           lexical_contact=bool(edge and edge['kind']=='tangent'),
                           side=None if side is None else side['centers'][0],
                           side_centers=[] if side is None else side['centers']))
        if edge and edge['kind'] == 'invisible':
            invisible.append(edge)
        if edge and edge['kind']=='tangent':word_contact=True
        previous, previous_entry = main['exit'], edge.get('entry_port') if edge else None
    geometry_check(shapes, paths, invisible)
    # Metadata is diagnostic only; decode() below accepts just the primitives.
    return dict(version=VERSION, shapes=shapes, groups=groups, width=max(g['right'] for g in groups)+12.)


def decode(shapes, *, lexicon=None):
    with use_context(lexicon):
        return _decode(shapes)


def decode_declaration(shapes, *, lexicon=None):
    with use_context(lexicon):
        return _decode(shapes,declaration=True)


def decode_item(shapes, *, lexicon=None):
    with use_context(lexicon):
        return _decode(shapes,declaration=None)


def decode_run(shapes, *, reader):
    """Read a whole flow transactionally, learning only completed items."""
    pending=reader.fork()
    items=_decode(shapes,declaration=None,reader=pending)
    return pending,items


def _decode(shapes, *, declaration=False, reader=None):
    geometry = read_geometry(shapes)
    observed_flow = decompose_flow(geometry,terminal_words=True,branch_seams=True,large_branches=True,
        local_continuation=True,nested_branches=True,multiple_branches=True)
    from scripts.kant_root_overlap import expand_flow
    tokens,flow,expanded,overlap_pairs=expand_flow(geometry,observed_flow)
    # Only large terminal diagonals may end freely outside a circle in this
    # fragment. Do not silently prune arbitrary line-only decoration.
    for vertex in geometry['vertices']:
        if vertex['degree'] != 1 or vertex['centers'] or vertex['rims']:
            continue
        if not any(c['size'] == 'large' and
                   any(math.dist(vertex['point'], [c['center'][0]+LARGE*(1 if d in (1,7) else -1),
                                                   c['center'][1]+LARGE*(1 if d in (1,3) else -1)]) < 1e-5
                       for d in ([c['center_direction']] if c['center_direction'] in (1,3,5,7) else [])
                       +c['outer_diagonals']) for c in geometry['circles']):
            raise ValueError('Uninterpreted free terminal stroke')
    main = flow['main']
    branches=flow['branch_groups']
    streams=[main,*(chain for groups in branches.values() for chain in groups)]
    locations={n:(s,i) for s,chain in enumerate(streams) for i,n in enumerate(chain)}
    stream_stops=[set() for _ in streams]
    linear = [tokens[i] for i in main]
    side_positions = {i for i,n in enumerate(main) if n in branches}
    for a, b in recover_seams(geometry,branch_seams=True):
        ends = []
        for endpoint,point in enumerate((a, b)):
            owners = [i for i, n in enumerate(observed_flow['nuclei']) if any(
                math.dist(geometry['circles'][c]['center'], point) < 1e-5 for c in n['circles'])]
            if len(owners) != 1:
                raise ValueError('Silent seam outside an expression flow')
            owner=expanded[owners[0]][-1 if endpoint==0 else 0]
            if owner not in locations:raise ValueError('Silent seam outside an expression flow')
            ends.append(locations[owner])
        (sa,ia),(sb,ib)=ends
        if sa!=sb or ib!=ia+1 or tokens[streams[sb][ib]] not in {*root_words(), 'quote'}:
            raise ValueError('Silent seam outside a word/quotation entry')
        stream_stops[sb].add(ib)
    stops=stream_stops[0]
    position = 0
    serial = 0
    lexical_pairs=set()
    lexical_word_pairs=set()
    bound_argument_pairs=set()
    def take_word():
        nonlocal position
        start=position
        token, position = read_word(linear, position, stops=stops, sides=side_positions)
        pairs={tuple(sorted(pair)) for pair in zip(main[start:position-1],main[start+1:position])}
        lexical_pairs.update(pairs);lexical_word_pairs.update(pairs)
        owner=main[position-1]
        sides=branches.get(owner,[])
        for side in sides:
            if len(side)==1 and tokens[side[0]]=='bound0':
                bound_argument_pairs.add(tuple(sorted((owner,side[0]))))
        return token, sides
    def take_type_token():
        nonlocal position
        if position>=len(main):
            raise ValueError('Incomplete visible type header')
        if main[position] in branches or position in stops:
            raise ValueError('Type header cannot carry a terminal argument or lexical seam')
        token=linear[position];position+=1
        return token
    def read(scope, side_ids=None):
        nonlocal position, serial, main, linear, side_positions, stops
        if side_ids is not None:
            saved=position,main,linear,side_positions,stops
            main=side_ids;linear=[tokens[i] for i in main];position=0
            side_positions={i for i,n in enumerate(main) if n in branches}
            stops=stream_stops[locations[main[0]][0]]
            try:
                result=read(scope)
                if position!=len(main):raise ValueError('Branch must contain exactly one complete expression')
                return result
            finally:position,main,linear,side_positions,stops=saved
        if position >= len(main):
            raise ValueError('Incomplete visible expression')
        if linear[position] in root_words():
            token, sides = take_word()
        else:
            index = position; position += 1
            token = linear[index]
            sides = branches.get(main[index],[])
        count = None if token in DYNAMIC_ARITY else arity(token)
        if count is not None and sides and len(sides)>=count:
            raise ValueError('Unexpected terminal dependency')
        if token in TYPE_TOKENS | LIST_TOKENS:
            raise ValueError('Type constructor outside a visible type header')
        if token in STATEMENT_TOKENS:
            raise ValueError('Statement head inside an expression')
        if token in DECLARATION_TOKENS or token in ('full_name','spelling'):
            raise ValueError('Declaration head inside an expression')
        if token=='sequence':
            element=read_type(take_type_token)
            items=[read(scope,side) for side in sides]
            initial_count=len(items)
            while position<len(main) and linear[position]!='types_end':
                items.append(read(scope))
            if position>=len(main):raise ValueError('Missing visible sequence end')
            if sides and len(items)==initial_count:
                raise ValueError('Sequence branches require a final main item')
            take_type_token()  # The end cannot carry a branch or word seam.
            return dict(kind='sequence',element=element,items=items)
        if token in NUMBER_STARTS:
            previous=None
            def take_number_token():
                nonlocal position,previous
                if position>=len(main):raise ValueError('Incomplete visible numeral')
                if main[position] in branches or position in stops:
                    raise ValueError('Numeral cannot carry a branch or lexical seam')
                current=main[position]
                if previous is not None:lexical_pairs.add(tuple(sorted((previous,current))))
                previous=current
                value=linear[position];position+=1
                return value
            return read_number(token,take_number_token)
        if token in ('forall_typed','exists_typed','lambda_typed'):
            sorts=read_type_list(take_type_token) if token=='lambda_typed' else [read_type(take_type_token)]
            names=tuple('v'+number_word(serial+i) for i in range(len(sorts)))
            serial+=len(sorts)
            body=read((*scope,*zip(names,sorts)))
            if token=='lambda_typed':
                return dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in zip(names,sorts)],body=body)
            return dict(kind=token.removesuffix('_typed'),variable=names[0],sort=sorts[0],body=body)
        if token == 'function_ref':
            name, attached = take_word()
            if attached:
                raise ValueError('Arguments attached to a bare function reference')
            return dict(kind='function_ref', symbol=name)
        if token in SIGNATURE_HEADS:
            # The function/question is child zero on the main continuation.
            # Its public type supplies arity before any argument is consumed.
            head=read(scope)
            actual=expression_type(head,scope,words())
            type_=require_question(actual) if token=='answer_matches' else application_type(token,actual)
            count=1+len(type_['parameters'])
            order=side_order(token,count=count)
            if len(sides)>len(order):
                raise ValueError('Too many branches for the visible '+('question' if token=='answer_matches' else 'function')+' type')
            attached=dict(zip(order,sides))
            arguments=[read(scope,attached[i]) if i in attached else read(scope) for i in range(1,count)]
            return dict(kind=token,**{('question' if token=='answer_matches' else 'function'):head},arguments=arguments)
        if token == 'bound_shift':
            if len(scope) < 3:
                raise ValueError('Outward reference outside the visible scope')
            if position >= len(main) or linear[position] not in ('bound1', 'bound_shift'):
                raise ValueError('Outward marker must precede an outer binding reference')
            return read(scope[:-1])
        if token == 'and_shared':
            if len(sides)!=1:
                raise ValueError('Shared conjunction requires one visible terminal argument')
            subject = read(scope, sides[0])
            if subject['kind']!='variable' and not (subject['kind']=='call' and not subject['arguments']):
                raise ValueError('Shared conjunction requires a terminal subject')
            applications = []
            shared_sort = None
            for _ in range(2):
                name, attached = take_word()
                entry = words()[name][1]
                slot=shared_slot(name)
                if slot is None:
                    raise ValueError('Shared conjunction requires predicates with a public shared role')
                order=side_order(name,(slot,))
                if len(attached)>len(order):
                    raise ValueError('Too many branches on a shared predicate')
                attached=dict(zip(order,attached))
                sort=entry['parameters'][slot]
                if shared_sort is not None and shared_sort!=sort:
                    raise ValueError('Shared conjunction argument sorts differ')
                shared_sort=sort
                arguments=[deepcopy(subject) if i==slot else read(scope,attached[i]) if i in attached else read(scope)
                           for i in range(len(entry['parameters']))]
                applications.append(dict(kind='call', symbol=name, arguments=arguments))
            return dict(kind='and', arguments=applications)
        child_scope = () if token == 'quote' else scope
        saved_serial = serial
        if token == 'quote':
            serial = 0
        if token in ('forall', 'exists', 'lambda_individual', 'content'):
            child_scope = (*scope, ('v'+number_word(serial),'situation' if token=='content' else 'individual'))
            serial += 1
        attached=dict(zip(side_order(token),sides))
        children = [read(child_scope,attached[i]) if i in attached else read(child_scope)
                    for i in range(count)]
        if token in words():
            return dict(kind='call', symbol=token, arguments=children)
        if token in SEQUENCE_FIELDS:
            return dict(kind=token,**dict(zip(SEQUENCE_FIELDS[token],children)))
        if token=='question':return dict(kind=token,function=children[0])
        if token=='message_content':return dict(kind=token,message=children[0])
        if token.startswith('message_'):
            return dict(kind='message',force=token.removeprefix('message_'),content=children[0])
        if token.startswith('bound'):
            distance = int(token[-1])
            if distance >= len(scope):
                raise ValueError('Unbound visible variable')
            return dict(kind='variable', name=scope[-1-distance][0])
        if token == 'quote':
            serial = saved_serial
            return dict(kind='quote', body=children[0])
        if token == 'quote_raise':
            child = children[0]
            if child['kind'] != 'quote':
                raise ValueError('Quotation rank marker must precede a quotation')
            return dict(child, rank=child.get('rank', 0)+1)
        if token in ('forall', 'exists'):
            return dict(kind=token, variable=child_scope[-1][0], sort='individual', body=children[0])
        if token == 'lambda_individual':
            return dict(kind='lambda',parameters=[dict(name=child_scope[-1][0],sort='individual')],body=children[0])
        if token == 'evaluate':
            return dict(kind='evaluate',content=children[0],situation=children[1])
        if token == 'content':
            return dict(kind='content',variable=child_scope[-1][0],body=children[0])
        if token in ('quoted_lift','disquote'):
            actual=require_description(expression_type(children[0],scope,words()))
            rank=actual.get('rank',0) if token=='disquote' else 0
            return dict(kind=token,description=children[0],**({'rank':rank} if rank else {}))
        return dict(kind=token, arguments=children)
    def take_statement_token():
        nonlocal position
        if main[position] in branches or position in stops:
            raise ValueError('Statement head/end cannot carry a branch or lexical seam')
        token=linear[position];position+=1
        return token
    def read_statement(depth=0):
        nonlocal serial
        if depth>128:raise ValueError('Statement nesting exceeds 128 levels')
        if position>=len(main):raise ValueError('Incomplete visible statement')
        serial=0
        if linear[position]=='suppose':
            take_statement_token()
            condition=read(())
            if expression_type(condition,(),words())!='truth':
                raise ValueError('Assumption condition requires truth sort')
            children=[]
            while position<len(main) and linear[position]!='types_end':
                children.append(read_statement(depth+1))
            if position>=len(main):raise ValueError('Missing visible assumption end')
            take_statement_token()
            if not children:raise ValueError('Assumption scope requires statements')
            return dict(kind='suppose',condition=condition,statements=children)
        explicit=linear[position]=='ask_truth'
        if explicit:take_statement_token()
        body=read(())
        actual=expression_type(body,(),words())
        if explicit:
            if actual!='truth':raise ValueError('Truth question marker requires truth sort')
            kind='ask'
        elif actual=='truth':kind='assert'
        elif actual=='message':kind='perform'
        elif isinstance(actual,dict) and actual.get('kind')=='question':kind='ask'
        else:raise ValueError('Statement body has wrong sort')
        return dict(kind=kind,body=body)
    new_name=False
    def read_root_parts(limit):
        nonlocal position
        from scripts.visible_word_forms import read_symbol
        parts=[];previous=None
        while position<len(main) and linear[position]!='types_end':
            token=linear[position]
            if token not in root_words():raise ValueError('Full name requires root components')
            if len(parts)>=limit:raise ValueError('Full name component budget')
            if main[position] in branches or position in stops:
                raise ValueError('Full name cannot carry branches or lexical seams')
            current=main[position]
            if previous is not None:
                pair=tuple(sorted((previous,current)))
                lexical_pairs.add(pair);lexical_word_pairs.add(pair)
            previous=current;position+=1
            parts.append(read_symbol(token,vocabulary()).parts[0])
        if not parts:raise ValueError('Empty full name')
        if position>=len(main):raise ValueError('Missing full name end')
        take_statement_token()
        return parts
    def read_full_name():
        from scripts.visible_word_forms import MAX_PARTS
        take_statement_token()
        parts=read_root_parts(MAX_PARTS)
        return symbol(Word('root' if len(parts)==1 else 'compound',tuple(parts)),vocabulary())
    def read_declaration():
        nonlocal serial,new_name
        if not main or linear[position] not in DECLARATION_TOKENS:
            raise ValueError('Expected a visible declaration head')
        kind=take_statement_token()
        if position>=len(main):raise ValueError('Missing declaration name')
        if linear[position]=='full_name':
            name=read_full_name();new_name=True
        else:
            name,sides=take_word()
            if sides:raise ValueError('Declaration name cannot carry arguments')
        types=read_type_list(take_type_token)
        if kind=='primitive':
            return dict(kind=kind,name=name,parameters=types,result=read_type(take_type_token))
        parameters=[dict(name='v'+number_word(i),sort=t) for i,t in enumerate(types)]
        serial=len(parameters)
        scope=tuple((p['name'],p['sort']) for p in parameters)
        body=read(scope)
        return dict(kind=kind,name=name,parameters=parameters,result=expression_type(body,scope,words()),body=body)
    def read_item(mode):
        nonlocal new_name,serial
        new_name=False;serial=0
        is_spelling=mode is None and position<len(main) and linear[position]=='spelling'
        if is_spelling:
            take_statement_token()
            if position>=len(main):raise ValueError('Missing spelling target')
            name,sides=take_word()
            if sides:raise ValueError('Spelling target cannot carry arguments')
            if position>=len(main) or linear[position]!='types_end':raise ValueError('Missing spelling target end')
            take_statement_token()
            return validate_spelling(dict(kind='spelling',name=name,parts=read_root_parts(4)))
        if mode is None:mode=position<len(main) and linear[position] in DECLARATION_TOKENS
        result=read_declaration() if mode else read_statement()
        return validate_declaration(result,new_name=new_name) if mode else validate_native(result)
    if reader is None:
        result=read_item(declaration)
    else:
        result=[]
        while position<len(main):
            with use_context(reader.context):item=read_item(None)
            reader.register(item)
            result.append(item)
        if not result:raise ValueError('Empty visible item run')
    if position != len(main):
        raise ValueError('Trailing visible words')
    if not overlap_pairs<=lexical_word_pairs:
        raise ValueError('Overlapping roots must belong to one lexical word')
    owners={c:i for i,n in enumerate(flow['nuclei']) for c in n['circles']}
    for relation in geometry['relations']:
        if relation['kind']!='tangent':continue
        pair=tuple(sorted(owners[c] for c in relation['circles']))
        if pair in bound_argument_pairs and sorted(flow['nuclei'][i]['size'] for i in pair)==['medium','small'] and all(
            len(flow['nuclei'][i]['circles'])==1 for i in pair):
            continue
        if pair not in lexical_pairs or any(
            flow['nuclei'][i]['size']!='medium' or len(flow['nuclei'][i]['circles'])!=1 for i in pair):
            raise ValueError('Contact must join word/numeral medium components or a direct bound0 argument')
    return result
