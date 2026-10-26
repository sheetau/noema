"""Visibly framed volumes of one typed document, without local name indices.

The edition-twelve vocabulary and older book readers are unchanged. Volumes
carry explicit continuation offsets; definitions, bindings and quotes retain
their original scope across physical boundaries.
"""
from copy import deepcopy
from dataclasses import dataclass
from bisect import bisect_right, bisect_left
import math

from noema.constructed_discourse import normalize_document
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_public_page import PublicWriter, PublicLayoutReader, shared_name
from scripts.visible_syntax import Reader, END
from scripts.visible_syntax_vocabulary import KEYWORDS, family_glyph, modifier_glyph
from scripts.visible_sharing import SHARING, nodes, MAX_EXPANDED_NODES
from scripts.visible_word_forms import Word, canonical, symbol, read_symbol
from scripts.visible_page import LayoutReader, packet, split_rows, vertical_bounds, FRAMES, MAX_ROWS
from scripts.visible_syntax_geometry import render, recognize, clean, MAX_GLYPHS, MAX_SHAPES
from scripts.visible_lexical_script import require, _shape_set, _translate
from scripts.balanced_circle_script import MIN_GAP, STROKE
from scripts.visible_senses_book import MAX_PAGES

COLLECTION = ('utterance', None)
require(COLLECTION not in (*KEYWORDS.values(), *SHARING.values()), 'Collection operation collision')
FORMAT = 1
MAX_DECLARATIONS = 16384
MAX_STATEMENTS = 4096
MAX_COLLECTION_NODES = 524288
MAX_COLLECTION_GLYPHS = 4194304
MAX_VOLUMES = 4096
DEFAULT_PAYLOAD = 2048


def check_document(document):
    require(document['schema_version'] == '0.16', 'Collection grammar requires explicit Noema 0.16')
    require(len(document['declarations']) <= MAX_DECLARATIONS, 'Collection declaration budget exceeded')
    require(len(document['statements']) <= MAX_STATEMENTS, 'Collection statement budget exceeded')
    require(nodes(document) <= MAX_COLLECTION_NODES, 'Collection expanded-node budget exceeded')
    require(all(nodes(r) <= MAX_EXPANDED_NODES for r in document['declarations'] + document['statements']),
            'A logical record exceeds the unchanged expansion budget')


class CollectionReader(PublicLayoutReader):
    """Decode the old body grammar with a separately bounded record ledger."""
    def document(self):
        require(self.keyword() == 'document', 'Missing document header')
        require(self.natural() == 16, 'Unsupported Native edition')
        require(self.natural() == self.v.document()['edition'], 'Shared vocabulary edition differs')
        declarations, statements = [], []
        expanded = 0

        def account(record):
            nonlocal expanded
            count = nodes(record)
            require(count <= MAX_EXPANDED_NODES, 'Logical record expansion budget exceeded')
            expanded += count
            require(expanded <= MAX_COLLECTION_NODES, 'Collection expansion budget exceeded')

        while self.peek() != END:
            require(len(declarations) < MAX_DECLARATIONS, 'Collection declaration budget exceeded')
            self.expansion_work = 0
            k, word = self.keyword(), self.word(); name = shared_name(self.v, word)
            if k == 'import':
                require(name is not None, 'Unknown shared word import')
                record = self.v.declaration(name)
            else:
                require(k == 'definition' and word.kind != 'root', 'Expected definition or import')
                require(name is None, 'Local definition shadows a shared public word')
                self.serial = 0; parameters = self.parameters(); result = self.type()
                require(word.kind != 'proper' or (parameters == [] and result == 'individual'),
                        'Proper names designate individuals')
                body = self.expr(tuple(p['name'] for p in parameters))
                record = dict(kind='definition', name=symbol(word, self.v), parameters=parameters,
                              result=result, body=body)
            account(record); declarations.append(record)
        self.end()
        while self.peek() != END:
            require(len(statements) < MAX_STATEMENTS, 'Collection statement budget exceeded')
            self.expansion_work = 0
            record = self.statement(); account(record); statements.append(record)
        self.end()
        require(self.i == len(self.tokens), 'Extra collection body syntax')
        document = normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
                                            declarations=declarations, statements=statements))
        check_document(document)
        return document


def body_stream(document, vocabulary):
    """Intern geometric tokens; do not retain millions of duplicate drawings."""
    document = normalize_document(document); check_document(document)
    writer = PublicWriter(vocabulary); tokens = []; table = {}; interned = {}

    def flush():
        for glyph in writer.glyphs:
            key = _shape_set(glyph['shapes'])
            key = interned.setdefault(key, key)
            if key not in table:
                table[key] = glyph
            tokens.append(key)
        writer.glyphs = []
        require(len(tokens) <= MAX_COLLECTION_GLYPHS, 'Collection glyph budget exceeded')

    writer.keyword('document'); writer.natural(16); writer.natural(vocabulary.document()['edition']); flush()
    for d in document['declarations']:
        word = read_symbol(d['name'], vocabulary); name = shared_name(vocabulary, word)
        if name is not None:
            require(d == vocabulary.declaration(name), 'Declaration differs from public meaning')
            writer.keyword('import'); writer.name(d['name'])
        else:
            require(d['kind'] == 'definition' and word.kind != 'root', 'Local names require visible definitions')
            require(word.kind != 'proper' or (d['parameters'] == [] and d['result'] == 'individual'),
                    'Proper names designate individuals')
            writer.keyword('definition'); writer.name(d['name']); writer.parameters(d['parameters'])
            writer.type(d['result']); writer.expr(d['body'], tuple(p['name'] for p in d['parameters']))
        flush()
    writer.end(); flush()
    for s in document['statements']:
        writer.statement(s); flush()
    writer.end(); flush()
    trace = CollectionReader(tokens, vocabulary)
    require(trace.document() == document, 'Collection body changes normalized syntax')
    return tokens, table, trace.legal_boundaries(), document


@dataclass(frozen=True)
class Header:
    label: Word
    ordinal: int
    volumes: int
    total: int
    offset: int
    length: int
    declarations: int
    statements: int


class HeaderReader(LayoutReader):
    def __init__(self, tokens, vocabulary):
        super().__init__(tokens, vocabulary)
        self.keywords[COLLECTION] = 'collection'

    def header(self):
        require(self.keyword() == 'collection', 'Missing visible collection header')
        require(self.natural() == FORMAT, 'Unknown collection format')
        require(self.natural() == 16, 'Unsupported collection Native edition')
        require(self.natural() == self.v.document()['edition'], 'Collection vocabulary differs')
        label = self.word()
        require(label.kind in ('proper', 'compound'), 'Collection needs a visibly delimited label')
        values = [self.natural() for _ in range(7)]; self.end()
        h = Header(label, *values)
        require(0 <= h.ordinal < h.volumes <= MAX_VOLUMES, 'Invalid volume position or total')
        require(0 < h.total <= MAX_COLLECTION_GLYPHS and 0 <= h.offset < h.total,
                'Invalid collection extent')
        require(0 < h.length <= MAX_PAGES * MAX_GLYPHS and h.offset + h.length <= h.total,
                'Invalid volume extent')
        require(h.declarations <= MAX_DECLARATIONS and h.statements <= MAX_STATEMENTS,
                'Collection record budget exceeded')
        return h


def header_stream(header, vocabulary):
    w = PublicWriter(vocabulary)
    w.glyphs.extend((family_glyph(COLLECTION[0]), modifier_glyph(COLLECTION[1])))
    w.natural(FORMAT); w.natural(16); w.natural(vocabulary.document()['edition'])
    w.name(symbol(header.label, vocabulary))
    for key in ('ordinal', 'volumes', 'total', 'offset', 'length', 'declarations', 'statements'):
        w.natural(getattr(header, key))
    w.end()
    tokens = [_shape_set(g['shapes']) for g in w.glyphs]
    reader = HeaderReader(tokens, vocabulary)
    require(reader.header() == header and reader.i == len(tokens), 'Header changes during encoding')
    return tokens, dict(zip(tokens, w.glyphs)), reader.legal_boundaries()


def partition(tokens, boundaries, payload):
    require(type(payload) is int and 32 <= payload <= MAX_PAGES * MAX_GLYPHS - 256,
            'Invalid volume payload target')
    offsets = []; start = 0; ordered = sorted(boundaries)
    while start < len(tokens):
        index = bisect_right(ordered, start + payload) - 1
        end = ordered[index] if index >= 0 else start
        require(end > start, 'Volume cannot contain an indivisible syntax unit')
        offsets.append((start, end)); start = end
        require(len(offsets) <= MAX_VOLUMES, 'Collection volume budget exceeded')
    return offsets


def render_volume(tokens, table, boundaries, vocabulary, *, max_width=4800., row_gap=64.):
    """The existing page, row and book limits also apply to each volume."""
    require(type(max_width) in (int, float) and math.isfinite(max_width) and max_width > 0, 'Invalid page width')
    require(type(row_gap) in (int, float) and math.isfinite(row_gap) and row_gap >= 2 * MIN_GAP + STROKE,
            'Insufficient row separation')
    require(len(tokens) <= MAX_PAGES * MAX_GLYPHS, 'Volume payload exceeds budget')
    glyphs = [table[t] for t in tokens]; ordered = sorted(boundaries); rows = []; offset = 0
    while offset < len(tokens):
        require(len(rows) < MAX_ROWS, 'Volume row budget exceeded; select a smaller payload target')
        best = None
        for end in (i for i in ordered if offset < i <= min(len(tokens), offset + MAX_GLYPHS - 32)):
            row = packet(glyphs[offset:end], len(rows), final=end == len(tokens), vocabulary=vocabulary)
            drawing = render(row)
            if drawing['width'] > max_width:
                break
            best = end, drawing
        require(best is not None, 'Page width cannot contain an indivisible syntax unit')
        end, drawing = best; rows.append((drawing, end - offset)); offset = end
    pages = []; shapes = []; count = 0; row_count = 0; bottom = None

    def flush():
        nonlocal shapes, count, row_count, bottom
        require(len(pages) < MAX_PAGES, 'Volume page budget exceeded; select a smaller payload target')
        clean(shapes); pages.append(dict(shapes=shapes, glyphs=count, rows=row_count))
        shapes = []; count = 0; row_count = 0; bottom = None

    for drawing, n in rows:
        if shapes and (len(shapes) + len(drawing['shapes']) > MAX_SHAPES or count + n > MAX_GLYPHS):
            flush()
        require(len(drawing['shapes']) <= MAX_SHAPES and n <= MAX_GLYPHS, 'Row exceeds page budget')
        low, high = vertical_bounds(drawing['shapes']); shift = 0. if bottom is None else bottom + row_gap - low
        shapes.extend(_translate(drawing['shapes'], 0., shift)); bottom = high + shift
        count += n; row_count += 1
    if shapes:
        flush()
    return pages


def iter_collection_volumes(document, label, vocabulary=None, *, payload=DEFAULT_PAYLOAD, **layout):
    """Render one bounded volume at a time, retaining no earlier page geometry."""
    v = vocabulary or SensesVocabulary(); label = canonical(label, v)
    tokens, table, boundaries, doc = body_stream(document, v)
    parts = partition(tokens, boundaries, payload); page_count = 0; ordered = sorted(boundaries)
    for ordinal, (start, end) in enumerate(parts):
        h = Header(label, ordinal, len(parts), len(tokens), start, end - start,
                   len(doc['declarations']), len(doc['statements']))
        head, local_table, local_boundaries = header_stream(h, v); local_table.update(table)
        selected = ordered[bisect_left(ordered, start):bisect_right(ordered, end)]
        breaks = local_boundaries | {len(head) + i - start for i in selected}
        rendered = render_volume(head + tokens[start:end], local_table, breaks, v, **layout)
        yield dict(pages=rendered, first_page=page_count, offset=start, length=end-start,
                   body_glyphs=len(tokens), document=doc)
        page_count += len(rendered)


def compile_collection(document, label, vocabulary=None, **options):
    """Convenience collector for small exhibits; the CLI streams large ones."""
    pages = []; volumes = []; result = None
    for result in iter_collection_volumes(document, label, vocabulary, **options):
        pages.extend(result['pages'])
        volumes.append(dict(first_page=result['first_page'], pages=len(result['pages']),
                            offset=result['offset'], length=result['length']))
    return dict(pages=pages, volumes=volumes, body_glyphs=result['body_glyphs'], document=result['document'])


def volume_streams(pages, vocabulary):
    """Find volume boundaries from visible final-row marks, not filenames."""
    tokens = []; boundaries = []; ordinal = 0; page_count = 0; total_pages = 0
    for page in pages:
        total_pages += 1
        require(total_pages <= MAX_VOLUMES * MAX_PAGES, 'Collection page budget exceeded')
        require(page_count < MAX_PAGES, 'Volume page budget exceeded')
        rows = split_rows(page); page_glyphs = 0; page_count += 1
        for row_index, row in enumerate(rows):
            require(ordinal < MAX_ROWS, 'Volume row budget exceeded')
            visible = recognize(row); r = Reader(visible, vocabulary)
            require(r.take() == FRAMES['start'] and r.natural() == ordinal,
                    'Missing, repeated or reordered volume row')
            ordinal += 1
            ending = visible[-1]
            require(ending in (FRAMES['finish'], FRAMES['continue']), 'Missing volume row ending')
            part = visible[r.i:-1]
            require(part and not any(t in FRAMES.values() for t in part), 'Empty or misplaced row framing')
            if tokens:
                boundaries.append(len(tokens))
            tokens.extend(part); page_glyphs += len(part)
            require(page_glyphs <= MAX_GLYPHS and len(tokens) <= MAX_PAGES * MAX_GLYPHS,
                    'Page or volume payload exceeds budget')
            if ending == FRAMES['finish']:
                require(row_index == len(rows) - 1, 'A volume ends before its page ends')
                yield tokens, boundaries, page_count, ordinal
                tokens = []; boundaries = []; ordinal = 0; page_count = 0
    require(not tokens and ordinal == 0, 'Truncated final volume')


def assemble(streams, vocabulary):
    """Validate header/continuation grammar before interpreting the full body."""
    body = []; body_breaks = set(); first = None; volumes = 0; page_total = 0; row_total = 0
    for tokens, breaks, pages, rows in streams:
        require(volumes < MAX_VOLUMES, 'Collection volume budget exceeded')
        r = HeaderReader(tokens, vocabulary); h = r.header(); start = r.i
        require(h.ordinal == volumes, 'Missing, repeated or reordered volume')
        require(h.offset == len(body) and len(tokens) - start == h.length, 'Volume continuation differs')
        if first is None:
            first = h
        require((h.label, h.volumes, h.total, h.declarations, h.statements) ==
                (first.label, first.volumes, first.total, first.declarations, first.statements),
                'Mixed collection labels or extents')
        header_breaks = r.legal_boundaries()
        require(all(i in header_breaks for i in breaks if i < start), 'Row divides a collection header field')
        body_breaks.add(len(body))
        body_breaks.update(len(body) + i - start for i in breaks if i >= start)
        body.extend(tokens[start:]); volumes += 1; page_total += pages; row_total += rows
        require(len(body) <= MAX_COLLECTION_GLYPHS, 'Collection glyph budget exceeded')
    require(first is not None and volumes == first.volumes and len(body) == first.total,
            'Incomplete collection')
    trace = CollectionReader(body, vocabulary); document = trace.document()
    require(body_breaks <= trace.legal_boundaries(), 'Volume or row divides an indivisible syntax unit')
    require(len(document['declarations']) == first.declarations and len(document['statements']) == first.statements,
            'Collection record counts differ')
    return dict(document=document, label=first.label, volumes=volumes, pages=page_total,
                rows=row_total, body_glyphs=len(body))


def decode_collection(pages, vocabulary=None, *, public_names=False):
    v = vocabulary or SensesVocabulary()
    result = assemble(volume_streams(pages, v), v)
    if public_names:
        result['document'] = v.decode_names(result['document'])
    return result


def main(argv=None):
    import argparse, json
    from pathlib import Path
    from noema.constructed import parse, format_graph
    from scripts.visible_syntax_geometry import to_svg, from_svg
    cli = argparse.ArgumentParser(description=__doc__); sub = cli.add_subparsers(dest='command', required=True)
    write = sub.add_parser('render'); write.add_argument('source', type=Path); write.add_argument('directory', type=Path)
    write.add_argument('--label', nargs='+', required=True, help='Known root components of the collection title')
    write.add_argument('--public-names', action='store_true'); write.add_argument('--payload', type=int, default=DEFAULT_PAYLOAD)
    read = sub.add_parser('decode'); read.add_argument('sources', type=Path, nargs='+')
    read.add_argument('--public-names', action='store_true'); args = cli.parse_args(argv)
    try:
        v = SensesVocabulary()
        if args.command == 'render':
            doc = parse(args.source.read_text(encoding='utf-8'))
            if args.public_names:
                doc = v.encode(doc)
            require(not args.directory.exists() or not any(args.directory.iterdir()), 'Output directory must be new or empty')
            args.directory.mkdir(parents=True, exist_ok=True)
            count = 0; volumes = 0
            for result in iter_collection_volumes(doc, Word('proper', tuple(args.label)), v, payload=args.payload):
                for page in result['pages']:
                    count += 1
                    (args.directory / ('page-' + str(count).zfill(5) + '.svg')).write_text(to_svg(page['shapes']), encoding='utf-8', newline='\n')
                volumes += 1
            print(json.dumps(dict(pages=count, volumes=volumes)))
        else:
            result = decode_collection((from_svg(p.read_text(encoding='utf-8')) for p in args.sources), v,
                                       public_names=args.public_names)
            print(format_graph(result['document']))
    except (ValueError, OSError) as error:
        cli.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
