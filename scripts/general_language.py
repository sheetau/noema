"""Small dependency closures from the public inventory, without history imports."""
from copy import deepcopy
from functools import lru_cache
from scripts.two_work_inventory import read
from scripts.concept2_document import references
from noema.constructed_discourse import normalize_document

INVENTORY='data/general-language-catalog-v1.json'


@lru_cache(maxsize=1)
def entries():
    result=read(INVENTORY)
    if result['issues'] or result['spelling_collisions']:raise ValueError('Public inventory is unresolved')
    return result['entries']


def dependencies(names,extra=()):
    declarations={n:r['declaration'] for n,r in entries().items()}
    for d in extra:
        if d['name'] in declarations and declarations[d['name']]!=d:raise ValueError('Do not redefine public meanings')
        declarations[d['name']]=d
    ordered=[];active=set();done=set()
    def visit(name):
        if name in active:raise ValueError('Cyclic definition')
        if name in done:return
        d=declarations[name];active.add(name)
        for child in sorted(references(d)):visit(child)
        active.remove(name);done.add(name);ordered.append(deepcopy(d))
    for name in names:visit(name)
    return ordered


def document(extra,statements=()):
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=dependencies([d['name'] for d in extra],extra),statements=list(statements)))
