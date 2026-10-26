"""Link optional libraries into visible definitions using an unchanged core.

Only the authoring step needs the libraries. The resulting document is decoded
with the core vocabulary alone; no library registry or local name table is read.
"""
from copy import deepcopy

from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_word_forms import read_symbol
from scripts.visible_public_page import shared_name
from scripts.visible_lexical_script import require


def link(document, libraries=(), *, roots=(), vocabulary=None):
    """Preserve all authored records; add only the transitive library imports.

    Inputs use visible spellings, not source-manuscript identifiers. Explicit
    roots also retain unused definitions, e.g. when publishing a whole library.
    Collisions are errors even in unused supplied libraries. Identical library
    declarations can be shared; differently named equal bodies stay distinct.
    """
    core = vocabulary or SensesVocabulary()
    require(document.get('schema_version') == document.get('lexicon_version') == '0.16',
            'Linking requires explicit Native 0.16')
    available = {d['name']: d for d in core.imports(core._words)}
    authored = []

    def add(declaration):
        name = declaration['name']; word = read_symbol(name, core)
        public = shared_name(core, word)
        if public is not None:
            require(declaration == core.declaration(public), 'Core meaning changed: ' + name)
        else:
            require(declaration['kind'] == 'definition' and word.kind != 'root',
                    'Non-core primitive needs an explicit meaning contract: ' + name)
            require(word.kind != 'proper' or (not declaration['parameters'] and declaration['result'] == 'individual'),
                    'Proper names designate individuals')
        require(name not in available or available[name] == declaration,
                'Conflicting visible definition: ' + name)
        available[name] = deepcopy(declaration)

    for library in libraries:
        library = normalize_document(library)
        require(library['schema_version'] == library['lexicon_version'] == '0.16', 'Library edition differs')
        require(not library['statements'], 'A library cannot silently add assertions')
        for declaration in library['declarations']:
            add(declaration)
    for declaration in document['declarations']:
        require(declaration['name'] not in authored, 'Repeated authored declaration')
        add(declaration); authored.append(declaration['name'])

    active, done, ordered = set(), set(), []

    def visit(name):
        require(name in available, 'Unknown dependency: ' + name)
        require(name not in active, 'Cyclic definitions: ' + name)
        if name in done:
            return
        active.add(name)
        for dependency in sorted(_references(available[name].get('body'))):
            visit(dependency)
        active.remove(name); done.add(name); ordered.append(deepcopy(available[name]))

    for name in [*authored, *sorted(set(roots)), *sorted(_references(document['statements']))]:
        visit(name)
    result = deepcopy(document); result['declarations'] = ordered
    return normalize_document(result)


def main(argv=None):
    import argparse
    from pathlib import Path
    from noema.constructed import parse, format_graph
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source', type=Path)
    cli.add_argument('--library', type=Path, action='append', default=[])
    cli.add_argument('--retain', action='append', default=[], help='Visible spelling to retain even when unused')
    args = cli.parse_args(argv)
    try:
        result = link(parse(args.source.read_text(encoding='utf-8')),
                      [parse(p.read_text(encoding='utf-8')) for p in args.library], roots=args.retain)
        print(format_graph(result))
    except (ValueError, OSError) as error:
        cli.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
