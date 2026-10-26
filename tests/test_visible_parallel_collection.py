from copy import deepcopy
import pytest

from scripts import visible_collection as collection
from scripts.visible_parallel_collection import decode_files, _read_page, _recognized_pages
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_word_forms import Word
from scripts.shared_modality import call
from scripts.visible_parallel_render import iter_rendered_volumes


@pytest.fixture(scope='module')
def exhibit(tmp_path_factory):
    directory = tmp_path_factory.mktemp('parallel-visible')
    vocabulary = SensesVocabulary()
    document = dict(schema_version='0.16', lexicon_version='0.16',
                    declarations=vocabulary.imports({'red', 'aki'}),
                    statements=[dict(kind='assert', body=call(vocabulary._symbols['red'],
                                call(vocabulary._symbols['aki']))) for _ in range(12)])
    compiled = collection.compile_collection(document, Word('proper', ('book',)),
                                             vocabulary, payload=64)
    paths = []
    for i, page in enumerate(compiled['pages']):
        path = directory / f'{i}.svg'
        path.write_text(to_svg(page['shapes']), encoding='utf-8')
        paths.append(path)
    assert len(paths) > 1
    return paths, vocabulary


def test_parallel_and_serial_decoding_match_original(exhibit):
    paths, vocabulary = exhibit
    expected = collection.decode_collection(
        (from_svg(p.read_text(encoding='utf-8')) for p in paths), vocabulary)
    original = collection.recognize
    assert decode_files(paths, vocabulary, workers=2) == expected
    assert decode_files(paths, vocabulary, workers=1) == expected
    assert collection.recognize is original


@pytest.mark.parametrize('change', ['reverse', 'omit', 'repeat'])
def test_parallel_keeps_order_and_completeness_checks(exhibit, change):
    paths, vocabulary = exhibit
    changed = list(reversed(paths)) if change == 'reverse' else paths[:-1] if change == 'omit' else [paths[0], *paths]
    original = collection.recognize
    for workers in (1, 2):
        with pytest.raises(ValueError):
            decode_files(changed, vocabulary, workers=workers)
        assert collection.recognize is original


def test_unknown_svg_is_rejected_in_worker(exhibit, tmp_path):
    paths, vocabulary = exhibit
    bad = tmp_path / 'unknown.svg'
    text = paths[0].read_text(encoding='utf-8')
    bad.write_text(text.replace('</svg>', '<alien /></svg>'), encoding='utf-8')
    original = collection.recognize
    with pytest.raises(ValueError):
        decode_files([bad, *paths[1:]], vocabulary, workers=2)
    assert collection.recognize is original


def test_changed_row_cannot_reuse_worker_result(exhibit):
    page, rows = _read_page(exhibit[0][0])
    original = collection.recognize
    with _recognized_pages([(page, rows)]) as pages:
        next(pages)
        invalid = deepcopy(rows[0][0])
        invalid[0]['kind'] = 'unknown'
        with pytest.raises(ValueError):
            collection.recognize(invalid)
    assert collection.recognize is original


@pytest.mark.parametrize('workers', [0, -1, 33, True, 1.5])
def test_invalid_worker_budget(workers):
    with pytest.raises(ValueError):
        decode_files([], workers=workers)


def test_parallel_render_keeps_every_shape_row_and_volume(exhibit):
    paths, vocabulary = exhibit
    document = decode_files(paths, vocabulary, workers=1)['document']
    options = dict(payload=64, max_width=3200., row_gap=80.)
    original = list(collection.iter_collection_volumes(document, Word('proper', ('book',)),
                                                       vocabulary, **options))
    parallel = list(iter_rendered_volumes(document, Word('proper', ('book',)),
                                         vocabulary, workers=2, **options))
    assert parallel == original
    assert [to_svg(p['shapes']) for v in parallel for p in v['pages']] == [
        to_svg(p['shapes']) for v in original for p in v['pages']]


@pytest.mark.parametrize('options', [{'max_width': 0}, {'row_gap': 0}, {'payload': 1}])
def test_parallel_render_keeps_layout_rejections(exhibit, options):
    paths, vocabulary = exhibit
    document = decode_files(paths, vocabulary, workers=1)['document']
    for workers in (1, 2):
        with pytest.raises(ValueError):
            list(iter_rendered_volumes(document, Word('proper', ('book',)),
                                       vocabulary, workers=workers, **options))
