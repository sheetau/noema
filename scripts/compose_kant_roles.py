"""Compose general normative relations and role-relative uses of reason."""
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'examples/v011/kant-public-private.noema'
BASIS = ROOT / 'data/kant-public-private-basis-v1.json'


def compose():
    text = (ROOT / 'examples/v011/normative-roles.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/kant-public-private.noema.inc').read_text(encoding='utf-8')
    return format_graph(parse(text), 'compact') + '\n'


def composed_basis():
    basis = json.loads((ROOT / 'data/normative-roles-basis-v1.json').read_text(encoding='utf-8'))
    additions = json.loads((ROOT / 'data/kant-roles-additions-v1.json').read_text(encoding='utf-8'))
    basis.update(version='kant-public-private-basis-v1', document=TARGET.relative_to(ROOT).as_posix(), status='partial_semantic_draft')
    basis['primitives'].extend(additions['primitives'])
    basis['definitions'].update(additions['definitions'])
    basis['unresolved'].extend(additions['unresolved'])
    audit_basis(parse(compose()), basis)
    return basis


def main():
    text = compose()
    for path, body in ((TARGET, text), (BASIS, json.dumps(composed_basis(), ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored role draft or basis differs')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Kant public/private role draft reproduced; source coverage remains partial')


if __name__ == '__main__':
    main()
