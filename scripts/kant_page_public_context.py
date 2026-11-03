"""Reuse the already reviewed public-name bridge for the actual Kant page.

This reads pinned saved declarations and mappings. It does not instantiate the
long historical profile chain, redraw its old books, or rerun semantic models.
The source-name mapping is used only by the bridge check, never by the decoder.
"""
from functools import lru_cache
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from noema.constructed import parse
from scripts.shared_modality import renamed
from scripts.check_kant_geometry_reader import source_entries
from scripts.kant_lexical_context import LexicalContext, use_context
from scripts.kant_public_fragment import validate_native

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'examples/v016/kant-reviewed-complete-v1.noema'
NATIVE = 'examples/v016/kant-public-revolution-visible-v1.noema'
BRIDGE = 'data/kant-public-revolution-visible-bridge-v1.json'
EVIDENCE = 'reports/kant-public-revolution-visible-v1.json'
REFERENCE_SPELLINGS = 'data/kant-reference-spellings-v1.json'


@lru_cache(maxsize=1)
def inputs():
    bridge = json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))
    evidence = json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8'))
    for name in (SOURCE, NATIVE, BRIDGE):
        if evidence['source_sha256'].get(name) != hashlib.sha256((ROOT/name).read_bytes()).hexdigest():
            raise ValueError('Saved public bridge input changed: '+name)
    original = parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    native = parse((ROOT/NATIVE).read_text(encoding='utf-8'))
    if not (len(bridge['source_statement_indices']) == len(bridge['visible_statement_indices'])
            == len(bridge['source_statements'])):
        raise ValueError('Mismatched public bridge lists')
    by_source = {source:(slot,visible) for slot,(source,visible) in enumerate(zip(
        bridge['source_statement_indices'],bridge['visible_statement_indices']))}
    if len(by_source) != len(bridge['source_statement_indices']):
        raise ValueError('Duplicate source index in public bridge')
    declarations = {d['name']:d for d in original['declarations']}
    public_declarations = {d['name']:d for d in native['declarations']}
    selected = []
    for row in source_entries():
        index = row['statement']
        slot, visible = by_source[index]
        if bridge['source_statements'][slot] != original['statements'][index]:
            raise ValueError('Reviewed source assertion differs')
        if renamed(original['statements'][index],bridge['mapping']) != native['statements'][visible]:
            raise ValueError('Saved public assertion differs from exact name substitution')
        source = row['compiled']['source']
        expected = deepcopy(original['statements'][index])
        public_expected = deepcopy(native['statements'][visible])
        expanded = row.get('expanded_definition')
        if expanded:
            declaration = declarations[expanded]
            if (expected['body'] != dict(kind='call',symbol=expanded,arguments=[])
                or declaration['kind'] != 'definition' or declaration['parameters']):
                raise ValueError('Invalid top-level display expansion')
            public_declaration = public_declarations[bridge['mapping'][expanded]]
            if renamed(declaration,bridge['mapping']) != public_declaration:
                raise ValueError('Displayed definition changed in public bridge')
            expected['body'] = deepcopy(declaration['body'])
            public_expected['body'] = deepcopy(public_declaration['body'])
        if source != expected or renamed(source,bridge['mapping']) != public_expected:
            raise ValueError('Frozen display is not the exact declared expansion')
        selected.append(dict(statement=index,source=source,
                             public=renamed(source,bridge['mapping']),visible_statement=visible))
    return dict(native=native,bridge=bridge,selected=selected)


@lru_cache(maxsize=2)
def context(compact=True):
    return LexicalContext(inputs()['native'],compact=compact)


def selected(compact=True):
    ctx=context(compact)
    with use_context(ctx):
        for row in inputs()['selected']:
            validate_native(row['public'])
    return inputs()['selected']


@lru_cache(maxsize=1)
def reference_spellings():
    specification=json.loads((ROOT/REFERENCE_SPELLINGS).read_text(encoding='utf-8'))
    if specification['schema']!='kant-reference-spellings-1':
        raise ValueError('Unknown reference spelling rules')
    requested=specification['entries'];pending=set(requested);found={};paths=[REFERENCE_SPELLINGS]
    name=specification['meaning_basis'];seen=set()
    # Read only the meaning-basis chain needed for the requested existing entries.
    # Do not instantiate historical profiles or parse every old manuscript.
    while pending:
        if not name or name in seen:raise ValueError('Reference meaning basis is incomplete or cyclic')
        seen.add(name);paths.append(name)
        basis=json.loads((ROOT/name).read_text(encoding='utf-8'))
        for symbol_ in pending.copy():
            if symbol_ in basis.get('primitives',{}):
                found[symbol_]=basis['primitives'][symbol_];pending.remove(symbol_)
        name=basis.get('inherited_meaning_basis') or basis.get('revises_meaning_basis')
    bridge=inputs()['bridge'];declarations={d['name']:d for d in bridge['source_declarations']}
    result={}
    for old,row in requested.items():
        if any(found[old][k]!=row[k] for k in ('parameters','result','meaning_ja')):
            raise ValueError('Reference spelling changes the recorded meaning: '+old)
        if any(declarations[old][k]!=row[k] for k in ('parameters','result')):
            raise ValueError('Reference spelling changes its source signature: '+old)
        result[bridge['mapping'][old]]=dict(parts=row['parts'],meaning_ja=row['meaning_ja'])
    return result,paths


@lru_cache(maxsize=2)
def reference_context(compact=True):
    spellings,_=reference_spellings()
    return LexicalContext(inputs()['native'],compact=compact,declared_spellings=spellings)
