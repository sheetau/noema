"""Visible continuation frames for bounded structural-circle documents.

Page payloads are induced forests of the grammatical tree. All continuation
numbers and completion marks are actual glyphs. Decoding checks global scopes
and every local branch; no filenames, AST sidecars or document lookup table.
"""
from scripts.structural_circle import (
    grammar_tree, render_tree, read_geometry, PublicWriter, Reader, Vocabulary,
    catalogue, _shape_set, require, family_glyph, modifier_glyph,
)

FRAME = ('utterance', None)
CONTINUE = ('sequence', 1)
FINISH = ('sequence', 3)
FORMAT = 2
MAX_TOTAL = 16384
MAX_PAGES = 512


def mark(pair):
    return [_shape_set(family_glyph(pair[0])['shapes']), _shape_set(modifier_glyph(pair[1])['shapes'])]


def header(vocabulary, ordinal, pages, total, offset, length):
    w=PublicWriter(vocabulary,automatic=False)
    for n in (FORMAT,16,vocabulary.document()['edition'],ordinal,pages,total,offset,length):
        w.natural(n)
    w.end()
    return mark(FRAME)+[_shape_set(g['shapes']) for g in w.glyphs]


def fragment_tree(global_children, start, end, head_count):
    """Restrict existing edges to the interval; do not invent payload edges."""
    count=end-start
    children=[[] for _ in range(head_count+count+2)]
    for i in range(head_count-1):children[i]=[i+1]
    incoming=set()
    for i in range(start,end):
        selected=[c for c in global_children[i] if start<=c<end]
        incoming.update(selected)
        children[head_count+i-start]=[head_count+c-start for c in selected]
    roots=[head_count+i-start for i in range(start,end) if i not in incoming]
    children[head_count-1]=roots+[head_count+count]
    children[-2]=[len(children)-1]
    return children


def compile_pages(document, vocabulary=None, *, payload=96, sharing=False, **layout):
    v=vocabulary or Vocabulary()
    require(type(payload) is int and 1<=payload<=512, 'Invalid page payload')
    writer=PublicWriter(v,automatic=sharing)
    canonical=writer.document(document)
    tokens=[_shape_set(g['shapes']) for g in writer.glyphs]
    require(len(tokens)<=MAX_TOTAL,'Framed document exceeds token budget')
    restored,tree=grammar_tree(tokens,v)
    require(restored==canonical,'Public grammar conversion differs')
    pages=(len(tokens)+payload-1)//payload
    require(pages<=MAX_PAGES,'Framed document exceeds page budget')
    result=[]
    for ordinal,start in enumerate(range(0,len(tokens),payload)):
        end=min(start+payload,len(tokens))
        head=header(v,ordinal,pages,len(tokens),start,end-start)
        suffix=mark(FINISH if ordinal==pages-1 else CONTINUE)
        local=head+tokens[start:end]+suffix
        children=fragment_tree(tree,start,end,len(head))
        result.append(render_tree(local,children,v,**layout))
    return result


def decode_pages(pages, vocabulary=None):
    v=vocabulary or Vocabulary()
    body=[];records=[];first=None
    for ordinal,page in enumerate(pages):
        require(ordinal<MAX_PAGES,'Framed document exceeds page budget')
        tokens,local_tree=read_geometry(page,v)
        require(tokens[:2]==mark(FRAME),'Missing visible continuation header')
        r=Reader(tokens[2:],v)
        fmt,native,edition,index,count,total,offset,length=(r.natural() for _ in range(8))
        r.end();head_count=r.i+2
        require(fmt==FORMAT and native==16 and edition==v.document()['edition'],'Unknown structural page edition')
        require(index==ordinal and 1<=count<=MAX_PAGES and 1<=total<=MAX_TOTAL,'Missing, repeated or reordered page')
        require(offset==len(body) and 1<=length<=512 and offset+length<=total,'Broken visible continuation extent')
        if first is None:first=(count,total)
        require(first==(count,total),'Mixed page extents')
        require(ordinal<count,'Extra structural page')
        require(len(tokens)==head_count+length+2,'Page payload length differs')
        require(tokens[-2:]==mark(FINISH if ordinal==count-1 else CONTINUE),'Incorrect final/continuation mark')
        records.append((offset,offset+length,head_count,local_tree))
        body.extend(tokens[head_count:-2])
    require(first is not None and len(records)==first[0] and len(body)==first[1],'Incomplete structural document')
    document,global_tree=grammar_tree(body,v)
    for start,end,head_count,actual in records:
        require(actual==fragment_tree(global_tree,start,end,head_count),'Page branches disagree with continued grammatical scopes')
    return document
