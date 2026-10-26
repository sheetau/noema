"""Bounded CPU parallelism for SVG recognition; unchanged collection validation.

Workers run the original SVG, row and geometry readers. The parent consumes
results in input order and runs the original framing, vocabulary, scope and
collection checks. No semantic judgment or persistent cache is introduced.
"""
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
import multiprocessing
from pathlib import Path
from threading import RLock

from scripts import visible_collection as collection
from scripts.visible_page import split_rows
from scripts.visible_syntax_geometry import from_svg, recognize

_LOCK = RLock()


def _read_page(path):
    shapes = from_svg(Path(path).read_text(encoding='utf-8'))
    rows = split_rows(shapes)
    return shapes, [(row, recognize(row)) for row in rows]


def _ordered_pages(paths, workers):
    # spawn also on Unix: workers must never inherit the parent's adapter.
    with ProcessPoolExecutor(max_workers=workers,
                             mp_context=multiprocessing.get_context('spawn')) as pool:
        pending = deque()
        source = iter(paths)
        try:
            for _ in range(workers * 2):
                path = next(source, None)
                if path is None:
                    break
                pending.append(pool.submit(_read_page, path))
            while pending:
                yield pending.popleft().result()
                path = next(source, None)
                if path is not None:
                    pending.append(pool.submit(_read_page, path))
        finally:
            for future in pending:
                future.cancel()


@contextmanager
def _recognized_pages(results):
    """Reuse only the exact next row just checked by an original worker.

    A mismatch takes the original path. There is no shape rounding, filename
    trust or cached pass/fail decision. Restore the alias even on bad input.
    """
    with _LOCK:
        original = collection.recognize
        ready = deque()

        def checked(row):
            if ready and row == ready[0][0]:
                return deepcopy(ready.popleft()[1])
            return original(row)

        def pages():
            for shapes, rows in results:
                ready.clear()
                ready.extend(rows)
                yield shapes

        collection.recognize = checked
        try:
            yield pages()
        finally:
            collection.recognize = original


def decode_files(paths, vocabulary=None, *, workers=4, public_names=False):
    if type(workers) is not int or not 1 <= workers <= 32:
        raise ValueError('Worker count must be an integer from 1 to 32')
    paths = (str(Path(p).resolve()) for p in paths)
    # One worker is a direct baseline without subprocess startup or an adapter.
    if workers == 1:
        return collection.decode_collection(
            (from_svg(Path(p).read_text(encoding='utf-8')) for p in paths),
            vocabulary, public_names=public_names)
    results = _ordered_pages(paths, workers)
    try:
        with _recognized_pages(results) as pages:
            return collection.decode_collection(pages, vocabulary,
                                                public_names=public_names)
    finally:
        results.close()


def main(argv=None):
    import argparse
    import importlib
    import json
    import sys
    import time
    from noema.constructed import format_graph

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('sources', type=Path, nargs='+')
    cli.add_argument('--workers', type=int, default=4)
    cli.add_argument('--vocabulary', help='Trusted local module:factory, or default senses vocabulary')
    cli.add_argument('--public-names', action='store_true')
    args = cli.parse_args(argv)
    try:
        vocabulary = None
        if args.vocabulary:
            module, factory = args.vocabulary.split(':', 1)
            vocabulary = getattr(importlib.import_module(module), factory)()
        started = time.perf_counter()
        result = decode_files(args.sources, vocabulary, workers=args.workers,
                              public_names=args.public_names)
        print(format_graph(result['document']))
        print(json.dumps(dict(pages=result['pages'], workers=args.workers,
                              seconds=time.perf_counter()-started)), file=sys.stderr)
    except (ValueError, OSError) as error:
        cli.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
