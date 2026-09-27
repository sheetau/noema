"""Verify written scope roundtrips and the live local editor; never translate fixtures."""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from noema.definition_probe import digest
from noema.grammar import parse, format_graph
from noema.script import encode
from noema.semantics import require

SAMPLES = (
    ('collective', 'g:w-w i[no w[mu][si] fo].'),
    ('each', 'g:w-p a[w[mu][si]][po p a].'),
    ('each_not', 'g:w-p a[w[mu][si]][u[po p a]].'),
    ('not_each', 'g:u[w-p a[w[mu][si]][po p a]].'),
    ('reuse', 'g:w-p a[w[mu][si]o pets][po p a]. w-w i[no p pets fo].'),
    ('nested', 'g:w-p team[w[w[mu][si]][w[fo][mu]]][w-p member[p team][no p member p team]].'),
    ('derived', 'g:d w-p door[w[maj-sai][maj-saj]][t 6-sam qo n"葵" p door].'),
    ('question', 'g:b w-p a[w[mu m c][si]][no p a c].'),
)
CODE = ('noema/language.py', 'noema/grammar.py', 'noema/semantics.py', 'noema/derivation.py',
        'noema/render.py', 'noema/cli.py', 'noema/resources/editor.html', 'scripts/verify_written_v07.py')


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--port', type=int, default=8765)
    args = cli.parse_args()
    require(0 < args.port <= 65535, 'Invalid local port')
    base = f'http://127.0.0.1:{args.port}'

    def post(path, payload):
        request = Request(base + path, json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                          {'Content-Type': 'application/json'})
        with urlopen(request, timeout=120) as response:
            return json.load(response)

    samples = []
    for name, text in SAMPLES:
        graph = parse(text)
        full, compact = (format_graph(graph, notation) for notation in ('full', 'compact'))
        require(parse(full) == parse(compact) == graph, 'Written scope roundtrip changed')
        for form in (full, compact, encode(compact, 'v2')):
            result = post('/inspect', {'text': form})
            require(result['graph'] == graph == parse(result['script']), 'Live editor scope differs')
        samples.append({'name': name, 'full': full, 'compact': compact,
                        'full_characters': len(full), 'compact_characters': len(compact),
                        'roundtrip_equal': True, 'http_inspection_equal': True})
    for text in (SAMPLES[0][1], SAMPLES[1][1]):
        for language in ('ja', 'en'):
            result = post('/translate', {'text': text, 'direction': 'from_noema', 'language': language})
            require(result['status'] == 'unsupported' and result['text'] is None, 'Legacy translation lost group application')
    try:
        post('/inspect', {'text': 'g:w-p a[w[mu][si]][po p a]. po p a.'})
    except HTTPError as error:
        require(error.code == 400 and 'not been introduced' in json.load(error)['error'], 'Wrong escaping-reference error')
    else:
        raise AssertionError('Live editor accepted an escaped bound member')
    regressions = []
    # Both expectations were checked against the unchanged 27b21cf source and the same weights.
    for text, status in (('The dog chases the cat.', 'confirmed'), ('A dog chases a cat.', 'unresolved')):
        result = post('/translate', {'text': text, 'direction': 'to_noema', 'language': 'en'})
        require(result['status'] == status, 'Existing English analyzer status changed')
        if status == 'confirmed':
            require(parse(result['canonical']) == parse('d:ih mu si.'), 'Existing English meaning changed')
        else:
            require(result['text'] is None, 'Unresolved English input fabricated output')
        regressions.append({'input': text, 'status': status, 'baseline_equal': True})
    report = {'scope': 'written_collective_and_distribution_not_natural_language_translation',
              'samples': samples, 'all_counts_include_headers_and_whitespace': True,
              'http_inspection_forms_checked': len(samples) * 3, 'http_scope_escape_rejected': True,
              'http_legacy_reverse_application_rejected': 4, 'english_regression_baseline_commit': '27b21cf',
              'english_regressions': regressions,
              'source_sha256': {p: digest(p) for p in CODE}}
    path = Path('reports/written-v07.json')
    if path.exists():
        require(json.loads(path.read_text(encoding='utf-8')) == report, 'Written verification report differs')
    else:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'samples': len(samples), 'http_forms': len(samples) * 3,
                      'full_characters': sum(s['full_characters'] for s in samples),
                      'compact_characters': sum(s['compact_characters'] for s in samples),
                      'english_regressions_equal': len(regressions)}))


if __name__ == '__main__':
    main()
