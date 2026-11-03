"""Public words and a bounded native grammar in the Kant drawing geometry.

This is an experimental fragment, not the frozen script. Placement follows the
actual Kant generator's rail search, radial routing and accumulated ink moment.
Unlike that generator, neither lexical identity nor branch position uses a
document registry. References to the nearest two binders are bounded here.
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
    vocabulary, words, root_words, parts_for, read_word, mark_boundaries, declarations_for,
)
from noema.constructed_discourse import normalize_document
from noema.grammar import number_word
from scripts.kant_lexical_context import use_context

VERSION = 'kant-public-fragment-5-public-context'
ARITY = {'and': 2, 'or': 2, 'implies': 2, 'equal': 2, 'not': 1,
         'quote': 1, 'forall': 1, 'exists': 1, 'bound0': 0, 'bound1': 0,
         'function_ref': 0, 'and_shared': 2, 'lambda_individual': 1, 'evaluate': 2,
         'quote_raise': 1}
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
    'quote_raise': ((LARGE, 'nested', 1, 'radius'),),
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
    if token in ARITY:
        return ARITY[token]
    return len(words()[token][1]['parameters'])


def validate_native(statement):
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
    collect(statement)
    if not used <= words().keys():
        raise ValueError('Unknown public word')
    declarations = declarations_for(tuple(sorted(used)))
    checked = normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=declarations, statements=[statement]))['statements'][0]
    if checked != statement:
        raise ValueError('Fragment requires canonical native syntax')
    return statement


def forms(token, x=0., y=PITCH):
    if token not in GRAMMAR:
        result = _glyph(root_words()[token][1]['form'], x, y)
        return [result]
    result = []
    for radius, pair, direction, mode in GRAMMAR[token]:
        special = pair == 'small-concentric'
        g = nucleus(x, y, radius, None if special else pair,
                    direction, mode=mode)
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
    if kind == 'call' and set(node) == {'kind', 'symbol', 'arguments'}:
        token = node['symbol']
        if token not in words() or not isinstance(node['arguments'], list):
            raise ValueError('Unknown public root')
        children, child_scope = node['arguments'], scope
    elif kind == 'function_ref' and set(node) == {'kind', 'symbol'}:
        if node['symbol'] not in words():
            raise ValueError('Unknown public function reference')
        token, children, child_scope = kind, [], scope
    elif kind == 'lambda' and set(node) == {'kind', 'parameters', 'body'}:
        if (len(scope) >= 2 or not isinstance(node['parameters'], list) or len(node['parameters']) != 1
            or set(node['parameters'][0]) != {'name','sort'} or node['parameters'][0]['sort'] != 'individual'):
            raise ValueError('Fragment supports one individual lambda parameter')
        token,children,child_scope = 'lambda_individual',[node['body']],(*scope,node['parameters'][0]['name'])
    elif kind == 'evaluate' and set(node) == {'kind','content','situation'}:
        token,children,child_scope = kind,[node['content'],node['situation']],scope
    elif kind in ('and', 'or', 'implies', 'equal', 'not') and set(node) == {'kind', 'arguments'}:
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
        if len(scope) >= 2 or node['sort'] != 'individual':
            raise ValueError('Fragment supports two individual binders per scope')
        token, children, child_scope = kind, [node['body']], (*scope, node['variable'])
    elif kind == 'variable' and set(node) == {'kind', 'name'}:
        if node['name'] not in scope:
            raise ValueError('Unbound variable, including across a quotation')
        token = 'bound'+str(len(scope)-1-scope.index(node['name']))
        children, child_scope = [], scope
    else:
        raise ValueError('Native constructor outside this fragment')
    if len(children) != arity(token):
        raise ValueError('Public arity mismatch')
    return token, children, child_scope


def events(statement, branch=True, sharing=True):
    if not isinstance(statement, dict) or set(statement) != {'kind', 'body'} or statement['kind'] != 'assert':
        raise ValueError('Fragment expects one explicit assertion')
    result = []
    def emit(token, side, path):
        parts = parts_for().get(token, (token,))
        for i, part in enumerate(parts):
            event = dict(token=part, side=side if i == len(parts)-1 else None,
                         depth=len(path), path=list(path))
            if i == 0 and token in words():
                event['word'] = token
            result.append(event)
    def visit(node, scope, path):
        token, children, child_scope = split(node, scope)
        if token == 'function_ref':
            emit(token, None, path)
            emit(node['symbol'], None, path)
            return
        if sharing and branch and token == 'and' and all(
            c.get('kind') == 'call' and set(c) == {'kind', 'symbol', 'arguments'}
            and c['symbol'] in words() and words()[c['symbol']][1]['parameters'] == ['individual']
            and words()[c['symbol']][1]['result'] == 'truth' and len(c['arguments']) == 1
            for c in children):
            a, b = children
            if a['arguments'] == b['arguments']:
                shared, descendants, _ = split(a['arguments'][0], scope)
                single = shared in root_words() or shared in ('bound0', 'bound1')
                if single and not descendants and not near(forms(shared)[0]['radius'], LARGE):
                    # One visible argument is expanded at precisely these two
                    # call sites. No conjunction flattening or hidden paths.
                    emit('and_shared', shared, path)
                    emit(a['symbol'], None, path+(0,))
                    emit(b['symbol'], None, path+(1,))
                    return
        # Fixed public argument slot, not the middle of unknown leaf candidates.
        slot = len(children)//2 if len(children) >= 2 else None
        side = None
        if branch and slot is not None:
            side_token, descendants, _ = split(children[slot], child_scope)
            # A large circle spans all three rails and blocks a continuation
            # passing beside it. Keep it on the main flow, as in the Kant
            # generator's medium/small-only satellite rule.
            single = side_token in GRAMMAR and side_token != 'function_ref' or side_token in root_words()
            if single and not descendants and not near(forms(side_token)[0]['radius'], LARGE):
                side = side_token
        emit(token, side, path)
        for i, child in enumerate(children):
            if side is None or i != slot:
                visit(child, child_scope, path+(i,))
    visit(statement['body'], (), ())
    validate_native(statement)
    if len(result) > 512:
        raise ValueError('Fragment expression budget')
    return mark_boundaries(result)


def compile_statement(statement, *, branch=True, silent=True, sharing=True, lexicon=None, local_checks=True):
    with use_context(lexicon):
        return _compile_statement(statement, branch=branch, silent=silent, sharing=sharing, local_checks=local_checks)


def _compile_statement(statement, *, branch=True, silent=True, sharing=True, local_checks=True):
    """Reuse the Kant search with public glyphs and visible terminal arguments."""
    stream = events(statement, branch, sharing)
    # A required silent seam joins centers on one rail. If any nucleus in a
    # consecutive seam run is large, choose the middle rail for the entire
    # run before placement. Do not discover this only after placing its prefix.
    fixed_middle = set()
    start = 0
    for end in range(1, len(stream)+1):
        if end == len(stream) or not stream[end].get('lexical_seam'):
            if any(near(forms(e['token'])[0]['radius'], LARGE) for e in stream[start:end]):
                fixed_middle.update(range(start, end))
            start = end
    shapes, paths, groups, invisible = [], [], [], []
    previous = None
    previous_entry = None
    moment = 0.
    for event_index, event in enumerate(stream):
        # Same candidate-window strategy as the actual Kant generator. A
        # candidate is provisional: the complete sentence is checked below.
        # Keep the complete-prefix mode for independent equivalence probes.
        first = groups[-3] if local_checks and len(groups) >= 3 else None
        recent = shapes[first['shape_start']:] if first else shapes
        recent_paths = paths[first['path_start']:] if first else paths
        token = event['token']
        template = forms(token)[0]
        radius = template['radius']
        choices = []
        for y in ([PITCH] if near(radius, LARGE) else [0., PITCH, 2*PITCH]):
            if event_index in fixed_middle and not near(y, PITCH):
                continue
            if event.get('lexical_seam') and previous and not near(y, previous['y']):
                continue
            for extra in (0., 12., 28., 48., 72., 104., 160.):
                left = groups[-1]['right']+MIN_GAP+extra if groups else 12.
                x = left-template['left']
                found = False
                for main in forms(token, x, y):
                    local, local_paths = deepcopy(main['shapes']), deepcopy(main['paths'])
                    side_ports = []
                    side = None
                    if event['side'] is not None:
                        side_template = forms(event['side'])[0]
                        side_r = side_template['radius']
                        side_y = PITCH if near(side_r, LARGE) else (
                            2*PITCH-y if y != PITCH else 0. if moment > 0 else 2*PITCH)
                        # A large terminal cannot be stacked across rails. Its
                        # local branch remains asymmetric and ends before main continuation.
                        side_x = x if side_y != y and abs(side_y-y) >= radius+side_r+MIN_GAP else (
                            main['right']+side_r+2*MIN_RUN+PITCH)
                        side = forms(event['side'], side_x, side_y)[0]
                        local += side['shapes']; local_paths += side['paths']
                        link = route(main['exit'], side['entry'],
                                     [s for s in local if s['kind'] == 'circle'], event['depth'], local)
                        if link is None:
                            continue
                        p, segments = link
                        local += segments; local_paths.append(p); side_ports.append(p[0])
                    edge = None
                    seam = previous and (event.get('lexical_seam') or
                        silent and token == 'quote' and near(previous['y'], y))
                    if previous:
                        if seam:
                            edge = dict(kind='invisible', centers=[(previous['x'], previous['y']), (x, y)])
                        else:
                            link = route(previous, main['entry'],
                                [s for s in recent+local if s['kind'] == 'circle'], event['depth'], recent+local,
                                forbidden_start=() if previous_entry is None else (previous_entry,),
                                forbidden_end=side_ports)
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
                    imbalance = abs(moment+delta)/MEDIUM**2
                    score = max(0., imbalance-2.)*14+imbalance*.35+(right-left)*.11
                    if previous and near(previous['y'], y):
                        score += 2
                    if previous and near(abs(previous['y']-y), 2*PITCH):
                        score += 22
                    choices.append((score, main, side, local, local_paths, edge, delta, right))
                    found = True
                if found:
                    break
        if not choices:
            raise ValueError('No legal public placement: '+token+' at '+str(event['path']))
        _, main, side, local, local_paths, edge, delta, right = min(choices, key=lambda c:c[0])
        shape_start, path_start = len(shapes), len(paths)
        shapes += local; paths += local_paths; moment += delta
        groups.append(dict(token=token, center=[main['x'], main['y']], right=right,
                           shape_start=shape_start,path_start=path_start,
                           side=None if side is None else [side['x'], side['y']]))
        if edge and edge['kind'] == 'invisible':
            invisible.append(edge)
        previous, previous_entry = main['exit'], edge.get('entry_port') if edge else None
    geometry_check(shapes, paths, invisible)
    # Metadata is diagnostic only; decode() below accepts just the primitives.
    return dict(version=VERSION, shapes=shapes, groups=groups, width=groups[-1]['right']+12.)


def decode(shapes, *, lexicon=None):
    with use_context(lexicon):
        return _decode(shapes)


def _decode(shapes):
    geometry = read_geometry(shapes)
    flow = decompose_flow(geometry)
    tokens = []
    for nucleus_ in flow['nuclei']:
        key = feature(geometry, nucleus_['circles'])
        if key not in table():
            raise ValueError('Unknown visible public word')
        tokens.append(table()[key])
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
    linear = [tokens[i] for i in main]
    side_positions = {i for i, sides in enumerate(flow['side']) if sides}
    stops = set()
    for a, b in recover_seams(geometry):
        ends = []
        for point in (a, b):
            owners = [i for i, n in enumerate(flow['nuclei']) if any(
                math.dist(geometry['circles'][c]['center'], point) < 1e-5 for c in n['circles'])]
            if len(owners) != 1 or owners[0] not in main:
                raise ValueError('Silent seam outside the main flow')
            ends.append(main.index(owners[0]))
        if ends[1] != ends[0]+1 or linear[ends[1]] not in {*root_words(), 'quote'}:
            raise ValueError('Silent seam outside a word/quotation entry')
        stops.add(ends[1])
    position = 0
    serial = 0
    def take_word():
        nonlocal position
        token, position = read_word(linear, position, stops=stops, sides=side_positions)
        return token, flow['side'][position-1]
    def read(scope, side_id=None):
        nonlocal position, serial
        if side_id is None:
            if position >= len(main):
                raise ValueError('Incomplete visible expression')
            if linear[position] in root_words():
                token, sides = take_word()
            else:
                index = position; position += 1
                token = linear[index]
                sides = flow['side'][index]
        else:
            token, sides = tokens[side_id], []
            if arity(token) or flow['nuclei'][side_id]['size'] == 'large':
                raise ValueError('Nonterminal word used as a terminal dependency')
        count = arity(token)
        if sides and count < 2:
            raise ValueError('Unexpected terminal dependency')
        if token == 'function_ref':
            name, attached = take_word()
            if attached:
                raise ValueError('Arguments attached to a bare function reference')
            return dict(kind='function_ref', symbol=name)
        if token == 'and_shared':
            if len(sides) != 1:
                raise ValueError('Shared conjunction requires one visible terminal argument')
            subject = read(scope, sides[0])
            applications = []
            for _ in range(2):
                name, attached = take_word()
                entry = words()[name][1]
                if attached or entry['parameters'] != ['individual'] or entry['result'] != 'truth':
                    raise ValueError('Shared conjunction requires two unary individual predicates')
                applications.append(dict(kind='call', symbol=name, arguments=[deepcopy(subject)]))
            return dict(kind='and', arguments=applications)
        child_scope = () if token == 'quote' else scope
        saved_serial = serial
        if token == 'quote':
            serial = 0
        if token in ('forall', 'exists', 'lambda_individual'):
            if len(scope) >= 2:
                raise ValueError('Binder depth outside this fragment')
            child_scope = (*scope, 'v'+number_word(serial))
            serial += 1
        children = [read(child_scope, sides[0]) if sides and i == count//2 else read(child_scope)
                    for i in range(count)]
        if token in words():
            return dict(kind='call', symbol=token, arguments=children)
        if token.startswith('bound'):
            distance = int(token[-1])
            if distance >= len(scope):
                raise ValueError('Unbound visible variable')
            return dict(kind='variable', name=scope[-1-distance])
        if token == 'quote':
            serial = saved_serial
            return dict(kind='quote', body=children[0])
        if token == 'quote_raise':
            child = children[0]
            if child['kind'] != 'quote':
                raise ValueError('Quotation rank marker must precede a quotation')
            return dict(child, rank=child.get('rank', 0)+1)
        if token in ('forall', 'exists'):
            return dict(kind=token, variable=child_scope[-1], sort='individual', body=children[0])
        if token == 'lambda_individual':
            return dict(kind='lambda',parameters=[dict(name=child_scope[-1],sort='individual')],body=children[0])
        if token == 'evaluate':
            return dict(kind='evaluate',content=children[0],situation=children[1])
        return dict(kind=token, arguments=children)
    result = dict(kind='assert', body=read(()))
    if position != len(main):
        raise ValueError('Trailing visible words')
    return validate_native(result)
