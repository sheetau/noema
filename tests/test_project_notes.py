import sqlite3
import pytest
from scripts.project_notes import Ledger, restore_document, sha


def test_revision_conflict_and_original_preserved(tmp_path):
    ledger=Ledger(tmp_path/'ledger.sqlite',create=True)
    ledger.put('current','次の作業','元の要件',0)
    ledger.put('current','次の作業','追記した要件',1)
    with pytest.raises(ValueError,match='Stale'):
        ledger.put('current','誤更新','古い手元の内容',1)
    assert ledger.get('current')['body']=='追記した要件'
    assert [r['body'] for r in ledger.db.execute('SELECT body FROM revisions ORDER BY revision')]==['元の要件','追記した要件']
    ledger.close()


def test_archive_backup_restore_exact_bytes_and_guards(tmp_path):
    ledger=Ledger(tmp_path/'ledger.sqlite',create=True)
    raw='元の文書\r\n条件と例外を保持\r\n'.encode('utf-8')
    ledger.archive('docs/old.md',raw,'no remaining references')
    ledger.archive('docs/old.md',raw,'idempotent')
    with pytest.raises(ValueError,match='changed'):
        ledger.archive('docs/old.md',raw+b'x','overwrite')
    ledger.put('current','現在','保持する内容',0)
    ledger.backup(tmp_path/'backup.sqlite')
    backup=Ledger(tmp_path/'backup.sqlite')
    assert backup.get('current')['body']=='保持する内容'
    target=tmp_path/'restore'
    restore_document(backup,'docs/old.md',target)
    assert (target/'docs/old.md').read_bytes()==raw
    with pytest.raises(ValueError,match='overwrite'):
        restore_document(backup,'docs/old.md',target)
    with pytest.raises(ValueError,match='relative'):
        restore_document(backup,'../outside.md',target)
    assert ledger.search('例外',1)[0]['kind']=='archive'
    assert ledger.document('docs/old.md')['sha256']==sha(raw)
    with ledger.db:
        ledger.db.execute('UPDATE documents SET raw=? WHERE path=?',(b'corrupt','docs/old.md'))
    with pytest.raises(ValueError,match='hash mismatch'):
        ledger.document('docs/old.md')
    backup.close();ledger.close()


def test_missing_database_is_not_empty_backlog(tmp_path):
    path=tmp_path/'missing.sqlite'
    with pytest.raises(FileNotFoundError,match='restore'):
        Ledger(path)
    assert not path.exists()


def test_archive_path_confinement_and_bounded_search(tmp_path):
    ledger=Ledger(tmp_path/'ledger.sqlite',create=True)
    with pytest.raises(ValueError,match='relative'):
        ledger.archive('../escape.md',b'data','bad')
    with pytest.raises(ValueError,match='Nonempty'):
        ledger.search('')
    with pytest.raises(ValueError,match='limit'):
        ledger.search('x',100)
    ledger.close()
