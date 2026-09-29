"""Connect answer questions to the preserved definition of enlightenment."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.language import convert
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    doc = convert(parse((ROOT / 'examples/v011/kant-linked-draft.noema').read_text(encoding='utf-8')), '0.12')
    # Keep declarations ahead of all utterances; the old motto is still retained.
    statements, doc['statements'] = doc['statements'], []
    fragment = (ROOT / 'examples/fragments/kant-questions.noema.inc').read_text(encoding='utf-8')
    doc = parse(format_graph(doc, 'compact') + '\n' + fragment)
    doc['statements'] = statements + doc['statements']
    text = format_graph(doc, 'compact') + '\n'
    basis = json.loads((ROOT / 'data/kant-linked-basis-v1.json').read_text(encoding='utf-8'))
    additions = json.loads((ROOT / 'data/kant-question-additions-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'kant-question-basis-v1'
    basis['document'] = 'examples/v012/kant-questions.noema'
    basis['primitives'].extend(additions['primitives'])
    basis['definitions'].update(additions['definitions'])
    basis['unresolved'].extend(additions['unresolved'])
    audit_basis(doc, basis)
    return text, basis


def main():
    text, basis = composed()
    outputs = {basis['document']: text, 'data/kant-question-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
    for name, body in outputs.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored question draft differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Kant answer questions composed; source meaning remains partial')


if __name__ == '__main__':
    main()
