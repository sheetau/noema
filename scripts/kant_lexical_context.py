"""Explicit, published declarations and reversible abbreviations of their names.

The context contains definitions, not shapes assigned by declaration rank.
Abbreviations retain ordered components of the existing published spelling.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from itertools import combinations
import hashlib
import json

from noema.meaning_catalog import _references
from scripts.visible_word_forms import Word, read_symbol, symbol

ACTIVE = ContextVar('kant_public_lexical_context', default=None)


@contextmanager
def use_context(context):
    if context is None:
        yield
        return
    token = ACTIVE.set(context)
    try:
        yield
    finally:
        ACTIVE.reset(token)


def abbreviate(full, *, maximum=4, declared=None):
    """Shortest uniquely identifying ordered subsequence, else the full name.

    All complete public spellings are reserved. A candidate must occur in only
    one compound, regardless of the order of declarations. Within the shortest
    length prefer retaining both ends, then the narrowest span, then positions.
    This does not generate a code from a name's row number, hash, or spelling.
    """
    selected = {token: parts for parts, token in full.items()}
    declared=declared or {}
    reserved={parts:token for token,parts in declared.items()}
    selected.update(declared)
    pending = {token for parts, token in full.items() if len(parts) > 2}
    pending.difference_update(declared)
    for size in range(2, maximum+1):
        owners = {}
        candidates = {}
        for parts, token in full.items():
            if len(parts) < size:
                continue
            own = {}
            for positions in combinations(range(len(parts)), size):
                sequence = tuple(parts[i] for i in positions)
                # Do not steal any already published complete name.
                if sequence in full and full[sequence] != token:
                    continue
                if sequence in reserved and reserved[sequence] != token:
                    continue
                preference = (-(positions[0] == 0)-(positions[-1] == len(parts)-1),
                              positions[-1]-positions[0], positions)
                if sequence not in own or preference < own[sequence]:
                    own[sequence] = preference
            for sequence in own:
                if sequence in owners and owners[sequence] != token:
                    owners[sequence] = None
                else:
                    owners.setdefault(sequence, token)
            if token in pending:
                candidates[token] = own
        for token, own in candidates.items():
            unique = [s for s in own if owners[s] == token]
            if unique:
                selected[token] = min(unique, key=lambda s: own[s])
                pending.remove(token)
    aliases = dict(full)
    for token, parts in selected.items():
        if parts in aliases and aliases[parts] != token:
            raise ValueError('Abbreviated public word collision')
        aliases[parts] = token
    return selected, aliases


class LexicalContext:
    """A declared extension; native input must already have been type checked."""
    def __init__(self, document, *, compact=True, declared_spellings=None):
        from scripts.kant_public_lexicon import vocabulary, _base_words, _base_spellings
        v = vocabulary()
        # A decoder's dictionary must never contain the source assertions.
        self.document = dict(schema_version=document['schema_version'],
            lexicon_version=document['lexicon_version'],
            declarations=deepcopy(document['declarations']),statements=[])
        self.compact = compact
        self.declared_spellings=deepcopy(declared_spellings or {})
        self.words = deepcopy(_base_words())
        self.declarations = {d['name']: deepcopy(d) for d in v.imports([n for n, _ in self.words.values()])}
        self.full_spellings = dict(_base_spellings())
        seen = set()
        for d in document['declarations']:
            token = d['name']
            if token in seen:
                raise ValueError('Duplicate declaration in lexical context')
            seen.add(token)
            word = read_symbol(token, v)
            if word.kind not in ('root', 'compound'):
                raise ValueError('Context needs a root or compound spelling')
            parameters = d['parameters'] if d['kind'] == 'primitive' else [p['sort'] for p in d['parameters']]
            if token in self.declarations and self.declarations[token] != d:
                raise ValueError('Context changes an existing public definition: '+token)
            if token not in self.words:
                self.words[token] = (token, dict(parameters=deepcopy(parameters), result=deepcopy(d['result'])))
            self.declarations[token] = deepcopy(d)
            parts = tuple(symbol(Word('root', (p,)), v) for p in word.parts)
            if parts in self.full_spellings and self.full_spellings[parts] != token:
                raise ValueError('Context spelling collision')
            self.full_spellings[parts] = token
        declared={}
        for token,row in self.declared_spellings.items():
            if (token not in self.words or token in _base_words() or not isinstance(row,dict)
                or set(row)!={'parts','meaning_ja'} or not isinstance(row['meaning_ja'],str)
                or not row['meaning_ja'].strip() or not isinstance(row['parts'],list)
                or not 2<=len(row['parts'])<=4):
                raise ValueError('Invalid explicit semantic spelling')
            parts=tuple(symbol(Word('root',(p,)),v) for p in row['parts'])
            if (parts in self.full_spellings and self.full_spellings[parts]!=token
                or parts in declared.values()):
                raise ValueError('Explicit spelling collides with a published word')
            declared[token]=parts
        self.parts, self.spellings = abbreviate(self.full_spellings,declared=declared) if compact else (
            {t:p for p,t in self.full_spellings.items()}, dict(self.full_spellings))
        if not compact:
            self.parts.update(declared)
            self.spellings.update({parts:token for token,parts in declared.items()})
        self.prefixes = {parts[:i] for parts in self.spellings for i in range(1, len(parts)+1)}
        self.fingerprint = hashlib.sha256(json.dumps(dict(document=self.document,
            selected=self.parts,declared_spellings=self.declared_spellings),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        self._imports = {}

    def published(self):
        return dict(schema='kant-public-context-dictionary-2',fingerprint=self.fingerprint,
            compact=self.compact,native=deepcopy(self.document),
            declared_spellings=deepcopy(self.declared_spellings),
            selected_spellings={t:list(p) for t,p in self.parts.items()},
            aliases=[dict(parts=list(p),symbol=t) for p,t in sorted(self.spellings.items())])

    @classmethod
    def from_published(cls, value):
        if (set(value) != {'schema','fingerprint','compact','native','selected_spellings','aliases','declared_spellings'}
            or value['schema'] != 'kant-public-context-dictionary-2'
            or type(value['compact']) is not bool or value['native'].get('statements') != []):
            raise ValueError('Expected a public dictionary without source assertions')
        result=cls(value['native'],compact=value['compact'],declared_spellings=value['declared_spellings'])
        if result.published()!=value:
            raise ValueError('Published dictionary spelling or fingerprint differs')
        return result

    def declarations_for(self, tokens):
        if tokens in self._imports:
            return self._imports[tokens]
        active, done, order = set(), set(), []
        def visit(token):
            if token in done:
                return
            if token in active or token not in self.declarations:
                raise ValueError('Unknown or recursive public declaration')
            active.add(token)
            d = self.declarations[token]
            for ref in sorted(_references(d.get('body'))):
                visit(ref)
            active.remove(token);done.add(token);order.append(deepcopy(d))
        for token in tokens:
            visit(token)
        self._imports[tokens] = order
        return order
