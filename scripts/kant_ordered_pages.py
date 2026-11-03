"""Page order is document order; visible row ends carry expression continuation."""
import math
from scripts.kant_item_rows import ROW_GAP,pack_rows,split_rows,vertical_bounds
from scripts.kant_folded_flow import decode_page


def paginate(rows,max_height):
    if not isinstance(max_height,(float,int)) or not math.isfinite(max_height) or max_height<=0:
        raise ValueError('Expected positive finite page height')
    pages=[];pending=[];height=0.
    for row in rows:
        if not row:raise ValueError('Empty page row')
        extent=max(vertical_bounds(s)[1] for s in row)-min(vertical_bounds(s)[0] for s in row)
        if extent>max_height:raise ValueError('A whole row exceeds page height')
        needed=extent+(ROW_GAP if pending else 0.)
        if pending and height+needed>max_height:
            pages.append(pack_rows(pending));pending=[];height=0.;needed=extent
        pending.append(row);height+=needed
    if pending:pages.append(pack_rows(pending))
    if not pages:raise ValueError('Document requires at least one row')
    return pages


def decode_pages(pages,**options):
    rows=[]
    for page in pages:
        found=split_rows(page)
        if not found:raise ValueError('Empty physical page')
        rows+=found
    if not rows:raise ValueError('Document requires at least one page')
    return decode_page(pack_rows(rows),**options)
