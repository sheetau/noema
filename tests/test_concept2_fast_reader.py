from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.concept2_codec_v8 import Codec
from scripts.concept2_fast_reader import FastCodec,FastInkMixin,move_ink
from scripts.concept2_document import DocumentCodec
from scripts import concept2_geometry_v5 as g,concept2_composition as composition
from tests.test_concept2_document import records,drawing


class FastDocumentCodec(FastInkMixin,DocumentCodec):pass


def test_shallow_primitive_translation_is_exact_and_isolated():
    source=[g.circle(g.M),g.line((0,0),(10,10)),dict(kind='dot',x=5.,y=7.,r=g.D)]
    before=deepcopy(source);moved=move_ink(source,53.11,-29.65)
    assert moved==g.move(source,53.11,-29.65)
    moved[0]['x']=99
    assert source==before


def test_fast_and_baseline_dictionary_readers_and_bad_ink():
    writer=DocumentCodec();old=DocumentCodec();fast=FastDocumentCodec()
    for r in records():
        d=drawing(writer,r);raw=composition.svg(d['shapes'])
        assert old.read_svg(raw)==fast.read_svg(raw)
        bad=composition.svg(d['shapes']+[g.line((-80,0),(-60,0))])
        for reader in (DocumentCodec(),FastDocumentCodec()):
            with pytest.raises((ValueError,KeyError)):reader.read_svg(bad)
        writer.register(r)
    assert old.result()==fast.result()


def test_all_glyphs_in_neighbor_context_and_memo_is_input_local():
    dictionary=dict(native=dict(declarations=[]),selected_spellings={},aliases=[])
    old=Codec(dictionary);fast=FastCodec(dictionary)
    for t in old.forms:
        # Repeat needs a lexical predecessor; a bare dot needs a preceding host.
        tokens=[('root','book'),t,('root','aki')]
        d=g.layout(old.units(tokens))[0];raw=composition.svg(d['shapes'])
        assert old.read_svg(raw,fragment=True)==fast.read_svg(raw,fragment=True),t
    raw=composition.svg(g.layout(old.units([('root','book'),('root','aki')]))[0]['shapes'])
    assert old.read_svg(raw,fragment=True)==fast.read_svg(raw,fragment=True)
    bad=raw.replace('</svg>','<line x1="-80" y1="0" x2="-60" y2="0" stroke="black"/></svg>')
    with pytest.raises(ValueError):fast.read_svg(bad,fragment=True)
    assert old.read_svg(raw,fragment=True)==fast.read_svg(raw,fragment=True)
