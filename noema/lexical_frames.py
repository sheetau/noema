"""Uncalibrated definition matching on predicted frames, without oracle spans."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file

from .definition_probe import DefinitionIndex, definitions, digest
from .encoder import FrozenEncoder
from .event_gate import GatedEventFrameAnalyzer
from .japanese_pas_aligned import AlignedJapanesePAS
from .language import policy
from .semantics import require
from .shared_matcher import CompatibilityHead, query_features, predict

MISSING_COMPONENTS = ("polarity_and_scope", "time", "quantity", "names", "qualifiers", "reference_identity",
                      "speech_act_and_clause_relations", "unknown_concept_rejection", "calibrated_acceptance")


class SharedConceptMatcher:
    """A single frozen head scores any supplied definition; no word-specific head."""
    def __init__(self, report='reports/shared-matcher-v1', artifacts='artifacts/shared-matcher-v1'):
        root = Path(report)
        run = json.loads((root / 'run.json').read_text(encoding='utf-8'))
        training = json.loads((root / 'linear-training.json').read_text(encoding='utf-8'))
        require(run['status'] == 'complete', 'Incomplete concept matcher training')
        for path, sha in run['source_sha256'].items():
            require(digest(path) == sha, 'Concept matcher dependency changed')
        bank_path = root / 'definitions.json'
        require(digest(bank_path) == run['definitions_sha256'], 'Concept definitions changed')
        bank = json.loads(bank_path.read_text(encoding='utf-8'))
        require(bank == definitions(), 'Current concept definitions differ from the frozen bank')
        weight_path = Path(artifacts) / 'linear.safetensors'
        require(digest(weight_path) == training['weights_sha256'], 'Concept matcher weights changed')
        self.encoder = FrozenEncoder('minilm', offline=True)
        for key in ('id', 'revision', 'max_length', 'key', 'dtype', 'attention', 'pooling', 'seed'):
            require(self.encoder.metadata[key] == run['model'][key], 'Concept encoder contract changed')
        self.index = DefinitionIndex(self.encoder, bank)
        self.head = CompatibilityHead(self.encoder.dimension, rank=0)
        self.head.load_state_dict(load_file(str(weight_path)), strict=True)
        self.head.eval().requires_grad_(False)
        self.metadata = {'head': 'shared_linear_three_coefficients', 'weights_sha256': digest(weight_path),
                         'definitions_sha256': digest(bank_path), 'candidate_count': len(self.index.ids),
                         'training_runtime': run['model'], 'runtime': self.encoder.metadata,
                         'trained_parameters': sum(p.numel() for p in self.head.parameters())}

    def match(self, text, spans):
        require(isinstance(text, str) and bool(text), 'Expected source text')
        require(len({(s['start'], s['end']) for s in spans}) == len(spans), 'Duplicate concept query span')
        rows = []
        for span in spans:
            a, b = span['start'], span['end']
            require(type(a) is int and type(b) is int and 0 <= a < b <= len(text), 'Invalid concept query span')
            rows.append({'id': f'{a}:{b}', 'text': text, 'start': a, 'end': b, 'span': text[a:b]})
        if not rows:
            return []
        features = query_features(self.encoder, rows)
        with torch.inference_mode():
            scores = self.head(features, self.index.vectors)
        return predict(scores, rows, self.index.ids)


def frame_queries(output):
    text = output['analysis']['text']
    spans = set()
    for frame in output['frames']:
        spans.add((frame['predicate']['start'], frame['predicate']['end']))
        mentions = {m['id']: m for m in frame['mentions']}
        require(len(mentions) == len(frame['mentions']), 'Duplicate mention ID')
        for role in frame['roles']:
            require(role['target'] in mentions, 'Role target is not a predicted mention')
            if role['role'] != 'none':
                mention = mentions[role['target']]
                spans.add((mention['start'], mention['end']))
    require(all(type(a) is int and type(b) is int and 0 <= a < b <= len(text) for a, b in spans), 'Invalid predicted query span')
    return [{'start': a, 'end': b} for a, b in sorted(spans)]


def assemble_lexical_frames(output, matches):
    queries = frame_queries(output)
    require([(m['start'], m['end']) for m in matches] == [(s['start'], s['end']) for s in queries],
            'Concept matches do not correspond to predicted spans')
    concepts = policy('0.7')[1]
    lookup = {}
    for match in matches:
        require(match['span'] == output['analysis']['text'][match['start']:match['end']], 'Matched source span changed')
        top = match['top']
        require(top and top[0]['concept'] in concepts, 'Invalid concept ranking')
        lookup[match['start'], match['end']] = top[0]['concept']
    def candidate(span):
        return {'start': span['start'], 'end': span['end'], 'concept': lookup[span['start'], span['end']]}
    frames = []
    for frame in output['frames']:
        predicate = candidate(frame['predicate'])
        mentions = {m['id']: m for m in frame['mentions']}
        roles = [{'role': role['role'], **candidate(mentions[role['target']])}
                 for role in frame['roles'] if role['role'] != 'none']
        spec, errors = concepts[predicate['concept']], []
        if spec['kind'] not in ('event', 'state'):
            errors.append('predicate_is_not_event_or_state')
        for role in roles:
            concept = concepts[role['concept']]
            if concept['kind'] not in ('entity', 'place'):
                errors.append('argument_is_not_entity_or_place')
            if role['role'] not in spec.get('roles', []):
                errors.append('role_incompatible_with_predicate')
            else:
                allowed = spec.get('role_types', {}).get(role['role'], ['place'] if role['role'] in ('location', 'source', 'destination') else ['entity'])
                if concept['kind'] not in allowed:
                    errors.append('argument_type_incompatible_with_role')
            if role['concept'] == 'ag':
                errors.append('named_person_requires_name_extraction')
        if len({r['role'] for r in roles}) != len(roles):
            errors.append('multiple_arguments_for_one_role')
        frames.append({'source': frame['source'], 'predicate': predicate, 'roles': roles,
                       'structural_errors': sorted(set(errors))})
    return {'status': 'research_lexical_frames', 'confirmed': False, 'document': None,
            'source': output['analysis']['text'], 'frames': frames, 'concept_matches': matches,
            'missing_components': list(MISSING_COMPONENTS)}


class LexicalFrameAnalyzer:
    def __init__(self):
        self.structure = GatedEventFrameAnalyzer()
        self.structure.frame.parser = AlignedJapanesePAS()
        self.matcher = SharedConceptMatcher()
        self.metadata = {'structure': self.structure.frame.parser.metadata, 'matcher': self.matcher.metadata,
                         'event_selection_sha256': digest('reports/event-gate-v6/selection.json'),
                         'frame_selection_sha256': digest('reports/multi-frame-v5/selection.json')}

    def analyze(self, text):
        structure = self.structure.analyze(text)
        matches = self.matcher.match(text, frame_queries(structure))
        return {**assemble_lexical_frames(structure, matches), 'structure': structure}
