"""Compose complete saved items into bounded flows, paragraphs and pages."""
import math
from scripts import kant_saved_item_join as joining, kant_public_fragment as writing
from scripts import kant_folded_flow as folded
from scripts.kant_item_rows import ROW_GAP, vertical_bounds, shifted
from scripts.balanced_circle_script import PITCH, EPS
from scripts.visible_syntax_geometry import clean, MAX_SHAPES
from scripts.long_run import fingerprint


def physical_pages(rows, paragraph_starts, max_height):
    if not isinstance(max_height, (int, float)) or not math.isfinite(max_height) or max_height <= 0:
        raise ValueError('Expected positive finite page height')
    if not rows:
        raise ValueError('Document requires rows')
    starts = set(paragraph_starts)
    if any(type(i) is not int or not 0 <= i < len(rows) for i in starts):
        raise ValueError('Paragraph row index out of range')
    pages = []
    page = []
    height = 0.
    row_counts = []
    count = 0
    for index, row in enumerate(rows):
        row = clean(row)
        low = min(vertical_bounds(s)[0] for s in row)
        high = max(vertical_bounds(s)[1] for s in row)
        extent = high - low
        if extent > max_height + EPS:
            raise ValueError('A whole row exceeds page height')
        gap = ROW_GAP + (2 * PITCH if index in starts else 0.) if page else 0.
        if page and (height + gap + extent > max_height + EPS or len(page) + len(row) > MAX_SHAPES):
            pages.append(page)
            row_counts.append(count)
            page = []
            height = 0.
            count = 0
            gap = 0.
        page += shifted(row, height + gap - low)
        height += gap + extent
        count += 1
    if page:
        pages.append(page)
        row_counts.append(count)
    return pages, row_counts


def compose(paragraphs, *, reader, row_width, page_height, circle_budget=256, checkpoint=None):
    """Paragraphs contain lists of canonical-rail shapes, not source ASTs.

    The checkpoint callback is (key, content_inputs, action) -> JSON result.
    A pinned LongRun.step can supply it. Reading still uses only visible ink.
    """
    if type(circle_budget) is not int or not 1 <= circle_budget <= 1024:
        raise ValueError('Circle budget must be between 1 and 1024')
    if not paragraphs or any(not p for p in paragraphs):
        raise ValueError('Empty document or paragraph')
    checkpoint = checkpoint or (lambda key, inputs, action: action())
    source_reader = reader.fork()
    rows = []
    flows = []
    starts = []
    breaks = []
    paragraph_rows = []
    for paragraph_index, items in enumerate(paragraphs):
        starts.append(len(rows))
        pending = []
        drawing = None
        count = 0
        first = 0
        flow_reader = source_reader.fork()
        def flush():
            flow_index = len(flows)
            key = 'fold-' + str(flow_index)
            result = checkpoint(key, dict(shapes=fingerprint(drawing), width=row_width),
                lambda: folded.fold(drawing, row_width))
            first_row = len(rows)
            rows.extend(result['row_shapes'])
            flows.append(dict(paragraph=paragraph_index, first_item=first, items=len(pending),
                circles=count, first_row=first_row, rows=len(result['row_shapes'])))
        for item_index, original in enumerate(items):
            shapes = clean(original)
            circles = sum(s['kind'] == 'circle' for s in shapes)
            next_reader, records = writing.decode_run(shapes, reader=source_reader)
            if len(records) != 1:
                raise ValueError('Each paragraph input must be one complete item')
            if circles > circle_budget:
                raise ValueError('A complete item exceeds the flow circle budget')
            reason = None
            result = None
            if pending:
                if count + circles > circle_budget:
                    reason = 'flow-circle-budget'
                else:
                    def attempt():
                        try:
                            joined = joining.join([*pending, shapes], reader=flow_reader)
                        except ValueError as error:
                            if str(error) != 'No unchanged-ink junction within the bounded route choices':
                                raise
                            return dict(accepted=False, reason='unchanged-ink-junction-unavailable')
                        return dict(accepted=True, shapes=joined['shapes'])
                    result = checkpoint('join-'+str(paragraph_index)+'-'+str(item_index),
                        dict(shapes=fingerprint([*pending, shapes]),
                            reader=fingerprint([flow_reader.context.document, flow_reader.context.parts,
                                sorted(flow_reader.context.spellings.items()), flow_reader.result(True)])), attempt)
                    if not result['accepted']:
                        reason = result['reason']
                if reason:
                    flush()
                    breaks.append(dict(paragraph=paragraph_index, before_item=item_index, reason=reason))
                    pending = []
                    count = 0
            if not pending:
                first = item_index
                flow_reader = source_reader.fork()
                drawing = shapes
            else:
                drawing = result['shapes']
            pending.append(shapes)
            count += circles
            source_reader = next_reader
        flush()
        paragraph_rows.append(len(rows) - starts[-1])
    pages, page_row_counts = physical_pages(rows, starts, page_height)
    return dict(pages=pages, page_row_counts=page_row_counts, rows=len(rows),
        paragraph_first_rows=starts, paragraph_rows=paragraph_rows, flows=flows, breaks=breaks,
        expected=source_reader.result(True))
