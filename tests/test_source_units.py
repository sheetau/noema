import pytest

from noema.source_units import segment, digest


def wrap(body):
    return '<html><body><div id="metadata">outside</div><div style="display:table; text-align:justify;">' + body + '</div></body></html>'


def test_inline_words_equation_structure_pages_and_notes_are_not_dropped():
    math = '<math><mfrac><mi>x</mi><msup><mi>y</mi><mn>2</mn></msup></mfrac></math>'
    source = wrap('<span class="pagenum" id="891"></span><div>Title</div>'
                  '<p>Daß die Elektrodynamik <b>Maxwell</b>s &amp; field <sup class="reference"><a href="#cite_note-1">[1]</a></sup>.</p>'
                  '<center>' + math + '.</center><ol><li id="cite_note-1"><span class="mw-cite-backlink">↑</span>Author note.</li></ol>')
    r = segment(source, 'einstein-1905')
    assert [u['kind'] for u in r['units']] == ['frontmatter', 'body', 'equation', 'author_note']
    assert r['units'][1]['text'] == 'Daß die Elektrodynamik Maxwells & field .'
    assert r['math'][0]['mathml'] == math
    assert r['math'][0]['sha256'] == digest(math)
    assert source[r['math'][0]['source_start']:r['math'][0]['source_end']] == math
    assert r['annotations'][1]['targets'] == ['#cite_note-1']
    assert r['units'][1]['annotation_ids'] == ['A0002']
    assert r['units'][-1]['source_ids'] == ['cite_note-1']
    assert r['audit']['nonblank_text_nodes'] == r['audit']['assigned_text_nodes']
    assert 'outside' not in str(r)


def test_kant_author_note_is_kept_separate_from_editorial_apparatus():
    source = wrap('<p>Aufklärung ist der Ausgang des Menschen.</p><p>*) Author note.</p>'
                  '<h2>Anmerkungen (Wikisource)</h2><ol><li id="cite_note-1">Editor note.</li></ol>')
    r = segment(source, 'kant-1784')
    assert [u['kind'] for u in r['units']] == ['body', 'author_note', 'editorial', 'editorial']
    assert r['audit']['semantic_coverage'] == 'not_started'


def test_text_between_nested_blocks_is_accounted_for():
    r = segment(wrap('<div><p>Aufklärung ist der Ausgang.</p>Tail <b>text</b>.<div>Nested</div>End.</div>'), 'kant-1784')
    assert [u['text'] for u in r['units']] == ['Aufklärung ist der Ausgang.', 'Tail text.', 'Nested', 'End.']


@pytest.mark.parametrize('body', ['<p>Aufklärung ist der Ausgang.</p><img src="diagram.png">',
                                 '<p>Aufklärung ist der Ausgang.</p><table><tr><td>data</td></tr></table>',
                                 '<p>Unrecognized beginning.</p>'])
def test_unsupported_material_and_missing_author_boundary_are_not_silently_accepted(body):
    with pytest.raises(ValueError):
        segment(wrap(body), 'kant-1784')


def test_ambiguous_and_malformed_html_are_rejected():
    with pytest.raises(ValueError, match='Ambiguous'):
        segment(wrap('') + wrap(''), 'kant-1784')
    with pytest.raises(ValueError, match='Mismatched'):
        segment(wrap('<p>Aufklärung ist der Ausgang.</div>'), 'kant-1784')
    with pytest.raises(ValueError, match='Unresolved'):
        segment(wrap('<p>Aufklärung ist der Ausgang.<sup class="reference"><a href="#cite_note-9">9</a></sup></p>'), 'kant-1784')
