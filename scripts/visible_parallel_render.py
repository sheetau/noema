"""Render independent collection volumes on CPUs using the frozen renderer."""
from bisect import bisect_left, bisect_right
from collections import deque
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from scripts import visible_collection as collection

_VOCABULARY = None


def _initialize(vocabulary):
    global _VOCABULARY
    _VOCABULARY = vocabulary


def _render(job):
    tokens, table, boundaries, layout, start, length = job
    pages = collection.render_volume(tokens, table, boundaries, _VOCABULARY, **layout)
    return pages, start, length


def iter_rendered_volumes(document, label, vocabulary=None, *, workers=4,
                          payload=collection.DEFAULT_PAYLOAD, **layout):
    """Same volume order, row packing and geometry as iter_collection_volumes.

    The parent uses the original body/header encoders and partitioner. Each
    worker receives only one volume's glyphs, runs the original render_volume,
    and returns pages. At most twice the worker count is submitted ahead.
    """
    if type(workers) is not int or not 1 <= workers <= 32:
        raise ValueError('Worker count must be an integer from 1 to 32')
    if workers == 1:
        yield from collection.iter_collection_volumes(document, label, vocabulary,
                                                       payload=payload, **layout)
        return
    vocabulary = vocabulary or collection.SensesVocabulary()
    label = collection.canonical(label, vocabulary)
    tokens, table, boundaries, document = collection.body_stream(document, vocabulary)
    parts = collection.partition(tokens, boundaries, payload)
    ordered = sorted(boundaries)

    def jobs():
        for ordinal, (start, end) in enumerate(parts):
            header = collection.Header(label, ordinal, len(parts), len(tokens), start,
                                       end-start, len(document['declarations']),
                                       len(document['statements']))
            head, local, limits = collection.header_stream(header, vocabulary)
            body = tokens[start:end]
            # Same precedence as local.update(table), without unused glyphs.
            local.update({token: table[token] for token in set(body) | (set(head) & set(table))})
            selected = ordered[bisect_left(ordered, start):bisect_right(ordered, end)]
            breaks = limits | {len(head)+i-start for i in selected}
            yield head+body, local, breaks, layout, start, end-start

    with ProcessPoolExecutor(max_workers=workers,
                             mp_context=multiprocessing.get_context('spawn'),
                             initializer=_initialize, initargs=(vocabulary,)) as pool:
        pending = deque()
        source = iter(jobs())
        page_count = 0
        try:
            for _ in range(workers * 2):
                job = next(source, None)
                if job is None:
                    break
                pending.append(pool.submit(_render, job))
            while pending:
                pages, start, length = pending.popleft().result()
                yield dict(pages=pages, first_page=page_count, offset=start, length=length,
                           body_glyphs=len(tokens), document=document)
                page_count += len(pages)
                job = next(source, None)
                if job is not None:
                    pending.append(pool.submit(_render, job))
        finally:
            for future in pending:
                future.cancel()
