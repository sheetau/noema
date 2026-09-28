"""Strict conversion of annotated WiC-TSV pairs; no lexical lookup or inference use."""
from collections import Counter
import re

from .semantics import require

REVISION = '7bddf326add99eb40a2b85a331deffafead2a73f'
REPOSITORY = 'semantic-web-company/wic-tsv'


def parse_split(examples, definitions, labels, split):
    require(split in ('train', 'dev'), 'Only labeled official splits are supported')
    example_lines, definition_lines, label_lines = (s.splitlines() for s in (examples, definitions, labels))
    require(len(example_lines) == len(definition_lines) == len(label_lines) > 0, 'WiC-TSV parallel file lengths differ')
    rows = []
    for line, (example, definition, label) in enumerate(zip(example_lines, definition_lines, label_lines, strict=True), 1):
        fields = example.split('\t')
        require(len(fields) == 3, f'Invalid WiC-TSV columns at line {line}')
        lemma, index, text = fields
        require(index.isascii() and index.isdigit(), f'Invalid target index at line {line}')
        tokens = list(re.finditer(r'\S+', text))
        index = int(index)
        require(index < len(tokens), f'Target index out of range at line {line}')
        token = tokens[index]
        require(token.group().casefold() == lemma.casefold(), f'Target surface differs at line {line}')
        require(label in ('T', 'F') and definition.strip(), f'Invalid definition or label at line {line}')
        rows.append({'id': f'wic-tsv:{split}:{line}', 'language': 'en', 'text': text,
                     'start': token.start(), 'end': token.end(), 'span': token.group(),
                     'definition': definition, 'matches': label == 'T',
                     'annotation': {'lemma': lemma, 'word_index': index, 'line': line}})
    return rows


def audit(splits):
    summaries = {}
    for split, rows in splits.items():
        keys = [(r['text'], r['start'], r['end'], r['definition']) for r in rows]
        groups = {}
        for key, row in zip(keys, rows, strict=True):
            groups.setdefault(key, set()).add(row['matches'])
        require(all(len(v) == 1 for v in groups.values()), 'Conflicting labels for identical annotated input')
        summaries[split] = {'rows': len(rows), 'positive': sum(r['matches'] for r in rows),
                            'negative': sum(not r['matches'] for r in rows),
                            'lemmas': len({r['annotation']['lemma'].casefold() for r in rows}),
                            'contexts': len({r['text'] for r in rows}), 'definitions': len({r['definition'] for r in rows}),
                            'duplicate_input_rows': len(keys) - len(set(keys))}
    def values(split, kind):
        return {(r['text'], r['start'], r['end'], r['definition']) if kind == 'pairs' else
                r['annotation']['lemma'].casefold() if kind == 'lemmas' else r['text'] for r in splits[split]}
    overlaps = {kind: len(values('train', kind) & values('dev', kind)) for kind in ('pairs', 'contexts', 'lemmas')}
    return {'splits': summaries, 'train_dev_overlap': overlaps, 'language': 'en', 'source_target_scope': 'nouns',
            'official_test_labels_available': False, 'noema_concept_mapping': False}
