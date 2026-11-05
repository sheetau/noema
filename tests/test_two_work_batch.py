from copy import deepcopy
from pathlib import Path
from scripts.long_run import LongRun
from scripts.two_work_batch import process_records,render_record
from scripts.concept2_document import full_name
from scripts import concept2_composition as c


def name(root):return full_name([c.old.root_symbol(root)])
def primitive(root):return dict(kind='primitive',name=name(root),parameters=[],result='individual')
def statement(root):
    value=dict(kind='call',symbol=name(root),arguments=[])
    return dict(kind='assert',body=dict(kind='equal',arguments=[value,value]))


def run(tmp,records,renderer=render_record,reuse=None):
    with LongRun(tmp/'run',dict(records=records)) as job:
        return process_records(records,tmp/'out',job,'test-implementation',renderer=renderer,reuse=reuse)


def test_failure_blocks_only_dependants_and_next_independent_record_finishes(tmp_path):
    def fail_first(writer,tokens,width):
        if ('root','aki') in tokens:raise ValueError('Simulated missing glyph')
        return render_record(writer,tokens,width)
    records=[primitive('aki'),primitive('home'),statement('aki'),statement('home')]
    report=run(tmp_path,records,fail_first)
    assert report['scan_complete'] and not report['validation_success']
    assert [r['status'] for r in report['records']]==['failed','passed','blocked_dependency','passed']


def test_repair_reuses_unchanged_successes_but_rechecks_affected_inputs(tmp_path):
    records=[primitive('aki'),primitive('home'),statement('aki'),statement('home')]
    before=run(tmp_path/'before',records)
    after=run(tmp_path/'same',records,reuse=tmp_path/'before/out')
    assert after['validation_success']
    assert all(r['decoding']=='inherited-unchanged-content' for r in after['records'])
    altered=deepcopy(records);altered[0]['result']='number'
    fixed=run(tmp_path/'fixed',altered,reuse=tmp_path/'before/out')
    assert fixed['validation_success']
    assert [r['decoding'] for r in fixed['records']]==['fresh-ink','inherited-unchanged-content','fresh-ink','inherited-unchanged-content']


def test_corrupt_cached_ink_is_not_reused(tmp_path):
    records=[primitive('home'),statement('home')];before=run(tmp_path/'before',records)
    target=tmp_path/'before/out'/before['records'][0]['svg'];target.write_text('bad ink',encoding='utf-8')
    after=run(tmp_path/'after',records,reuse=tmp_path/'before/out')
    assert after['validation_success'] and after['records'][0]['decoding']=='fresh-ink'
    target.unlink()
    missing=run(tmp_path/'missing',records,reuse=tmp_path/'before/out')
    assert missing['validation_success'] and missing['records'][0]['decoding']=='fresh-ink'


def test_direct_row_layout_preserves_a_long_typed_definition(tmp_path):
    function=primitive('home');function['parameters']=['individual']
    body=dict(kind='variable',name='va')
    for _ in range(28):body=dict(kind='call',symbol=name('home'),arguments=[body])
    definition=dict(kind='definition',name=name('book'),parameters=[dict(name='va',sort='individual')],result='individual',body=body)
    report=run(tmp_path,[function,definition],lambda writer,tokens,width:render_record(writer,tokens,400))
    assert report['validation_success'] and report['records'][1]['rows']>1


def test_wrong_but_valid_decoded_record_does_not_poison_later_dictionary(tmp_path):
    def wrong(writer,tokens,width):
        if ('root','aki') in tokens:tokens=[('root','home') if t==('root','aki') else t for t in tokens]
        return render_record(writer,tokens,width)
    report=run(tmp_path,[primitive('aki'),primitive('home'),statement('home')],wrong)
    assert [r['status'] for r in report['records']]==['failed','passed','passed']


def test_malformed_cache_falls_through_to_other_work_or_fresh_ink(tmp_path):
    records=[primitive('home')];first=run(tmp_path/'first',records)
    second=run(tmp_path/'second',records)
    target=tmp_path/'first/out'/(first['records'][0]['cache_key']+'.json')
    target.write_text('[]',encoding='utf-8')
    reused=run(tmp_path/'reused',records,reuse=[tmp_path/'first/out',tmp_path/'second/out'])
    assert reused['validation_success'] and reused['records'][0]['decoding']=='inherited-unchanged-content'
