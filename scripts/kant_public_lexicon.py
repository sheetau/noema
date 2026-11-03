"""Published root/compound spellings with finite maximal-munch boundaries.

There is no per-document name table or word-number encoding. A boundary is
needed only when the following root would otherwise extend the intended word.
"""
from functools import lru_cache
import inspect
import json
from pathlib import Path

from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_word_forms import Word, symbol
from scripts.kant_lexical_context import ACTIVE


@lru_cache(maxsize=1)
def vocabulary():
    return SensesVocabulary()


@lru_cache(maxsize=1)
def _base_words():
    v = vocabulary()
    data = v.document()
    return {symbol(v.word(name), v): (name, v.entry(name))
            for name in (*data['entries'], *data['compounds'])}


def words():
    context = ACTIVE.get()
    return context.words if context is not None else _base_words()


@lru_cache(maxsize=1)
def root_words():
    v = vocabulary()
    return {symbol(Word('root', (name,)), v): (name, entry)
            for name, entry in v.document()['entries'].items()}


@lru_cache(maxsize=1)
def _base_spellings():
    v = vocabulary()
    result = {}
    for token, (name, _) in _base_words().items():
        word = v.word(name)
        parts = tuple(symbol(Word('root', (part,)), v) for part in word.parts)
        if parts in result:
            raise ValueError('Published root/compound spelling collision')
        result[parts] = token
    return result


def spellings():
    context = ACTIVE.get()
    return context.spellings if context is not None else _base_spellings()


@lru_cache(maxsize=1)
def _base_parts():
    return {token: parts for parts, token in _base_spellings().items()}


def parts_for():
    context = ACTIVE.get()
    return context.parts if context is not None else _base_parts()


@lru_cache(maxsize=1)
def _base_prefixes():
    return {parts[:i] for parts in _base_spellings() for i in range(1, len(parts)+1)}


def prefixes():
    context = ACTIVE.get()
    return context.prefixes if context is not None else _base_prefixes()


def read_word(tokens, start, *, stops=(), sides=()):
    """Read one public word; no source AST or expected name is accepted.

    A silent boundary or an argument attached to a component closes the word.
    Otherwise use the longest published spelling beginning at this position.
    """
    parts = []
    best = None
    for i in range(start, len(tokens)):
        if i != start and i in stops:
            break
        if tokens[i] not in root_words():
            break
        parts.append(tokens[i])
        key = tuple(parts)
        if key not in prefixes():
            break
        if key in spellings():
            best = spellings()[key], i+1
        if i in sides:
            break
    if best is None:
        raise ValueError('Unknown public word spelling')
    return best


def mark_boundaries(stream):
    """Insert only necessary lexical stops, determined before any layout.

    Word parts stay ordinary root shapes. This is linear in the number of
    events times the longest public spelling (currently three components).
    """
    tokens = [event['token'] for event in stream]
    sides = {i for i, event in enumerate(stream) if event['side'] is not None}
    stops = set()
    for i in range(len(stream)-1, -1, -1):
        expected = stream[i].get('word')
        if expected is None:
            continue
        end = i+len(parts_for()[expected])
        actual = read_word(tokens, i, stops=stops, sides=sides)
        if actual != (expected, end):
            if actual[1] <= end:
                raise ValueError('Public word cannot be delimited by a suffix boundary')
            stops.add(end)
            if read_word(tokens, i, stops=stops, sides=sides) != (expected, end):
                raise ValueError('Public word boundary did not disambiguate spelling')
    for i in stops:
        stream[i]['lexical_seam'] = True
    return stream


@lru_cache(maxsize=256)
def _base_declarations(tokens):
    """Reuse actual definitions, including dependencies, for native type checks."""
    return vocabulary().imports([_base_words()[token][0] for token in tokens])


def declarations_for(tokens):
    context = ACTIVE.get()
    return context.declarations_for(tokens) if context is not None else _base_declarations(tokens)


def source_paths():
    """Pin the actual vocabulary constructors and their declared source files."""
    root = Path(__file__).resolve().parents[1]
    paths = {'scripts/kant_public_lexicon.py', 'scripts/shared_modality.py',
             'scripts/visible_word_forms.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
             'noema/meaning_catalog.py', 'noema/grammar.py', 'noema/semantics.py'}
    manifests = {'noema/resources/visible-lexicon-v1.json',
                 'noema/resources/visible-vocabulary-v1.json',
                 'noema/resources/visible-defined-vocabulary-v1.json'}
    for cls in type(vocabulary()).__mro__:
        if not cls.__module__.startswith('scripts.'):
            continue
        module = inspect.getmodule(cls)
        paths.add(Path(module.__file__).resolve().relative_to(root).as_posix())
        if hasattr(module, 'MANIFEST'):
            manifests.add(module.MANIFEST)
    def referenced(value):
        if isinstance(value, dict):
            for child in value.values():
                referenced(child)
        elif isinstance(value, list):
            for child in value:
                referenced(child)
        elif isinstance(value, str) and len(value) < 240 and value.startswith(('examples/', 'data/')):
            if (root/value).is_file():
                paths.add(value)
    for manifest in manifests:
        paths.add(manifest)
        referenced(json.loads((root/manifest).read_text(encoding='utf-8')))
    return sorted(paths)
