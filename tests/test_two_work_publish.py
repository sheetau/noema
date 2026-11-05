import hashlib
from scripts.two_work_publish import source_html,publish_work
from scripts.two_work_run import run_both
from tests.test_two_work_batch import primitive,statement,run
from scripts.two_work_fastparse import parse_source


def test_source_math_is_visible_and_exact():
    raw='<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>V</mi></math>'
    assert source_html(dict(text='Speed [M0001] < limit'),{'M0001':dict(mathml=raw,sha256=hashlib.sha256(raw.encode()).hexdigest())})=='Speed '+raw+' &lt; limit'


def test_second_work_runs_after_first_work_infrastructure_failure():
    seen=[];report=dict(works={})
    def execute(work):
        seen.append(work)
        if work=='kant':raise OSError('missing file')
        return dict(validation_success=True)
    run_both(execute,report,lambda:None)
    assert seen==['kant','einstein'] and report['works']['einstein']['validation_success']
    assert not report['works']['kant']['scan_complete']


def test_reading_edition_has_one_main_occurrence_shared_links_and_separate_annotations(tmp_path):
    records=[primitive('home'),statement('home'),statement('home')]
    report=run(tmp_path/'check',records)
    document=dict(schema_version='0.16',lexicon_version='0.16',declarations=records[:1],statements=records[1:])
    units=[dict(id='kant-1784:u0001',text='First',kind='body',edition_statements=[0],edition_first_occurrence=[0],annotation_ids=[]),
           dict(id='kant-1784:u0002',text='Second',kind='body',edition_statements=[0],edition_first_occurrence=[],annotation_ids=[])]
    toc=dict(units=units,math=[],annotations=[],identifiers=dict(entries=[]),main_statements=1)
    out=tmp_path/'edition'
    result=publish_work(out,'kant',document,toc,{},dict(mapping={}),report)
    assert result['main_assertions']==1 and result['auxiliary_assertions']==1
    assert 'u0001.html#s0' in (out/'u0002.html').read_text(encoding='utf-8')
    assert parse_source((out/'recovered.noema').read_text(encoding='utf-8'))==document
