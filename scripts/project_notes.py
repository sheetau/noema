"""Private handoff ledger and archived documents; no daemon or language changes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / '.noema-project/ledger.sqlite'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Ledger:
    def __init__(self, path, *, create=False):
        self.path = Path(path).resolve()
        if create:
            if self.path.exists():
                raise ValueError('Ledger already exists')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.path)
            self.db.executescript('''
                PRAGMA user_version=1;
                CREATE TABLE notes (
                    key TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
                    revision INTEGER NOT NULL, updated TEXT NOT NULL,
                    source_path TEXT, source_sha256 TEXT);
                CREATE TABLE revisions (
                    key TEXT NOT NULL, revision INTEGER NOT NULL, title TEXT NOT NULL,
                    body TEXT NOT NULL, updated TEXT NOT NULL, actor TEXT NOT NULL,
                    PRIMARY KEY(key, revision));
                CREATE TABLE documents (
                    path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, raw BLOB NOT NULL,
                    body TEXT NOT NULL, reason TEXT NOT NULL, imported TEXT NOT NULL);
                CREATE TABLE retained (
                    path TEXT PRIMARY KEY, reason TEXT NOT NULL, details TEXT NOT NULL);
            ''')
            self.db.commit()
        else:
            if not self.path.is_file():
                raise FileNotFoundError('Project ledger missing; restore a backup. Do not create an empty handoff.')
            self.db = sqlite3.connect(self.path.as_uri()+'?mode=rw', uri=True, timeout=30)
        self.db.row_factory = sqlite3.Row
        if self.db.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Unsupported ledger schema')

    def close(self):
        self.db.close()

    def get(self, key):
        row = self.db.execute('SELECT * FROM notes WHERE key=?', (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        return dict(row)

    def put(self, key, title, body, expected_revision, *, source_path=None, source_sha256=None):
        if not all(isinstance(x, str) and x.strip() for x in (key, title, body)):
            raise ValueError('Nonempty key, title and body required')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.db.execute('SELECT * FROM notes WHERE key=?', (key,)).fetchone()
            previous = old['revision'] if old else 0
            if type(expected_revision) is not int or expected_revision != previous:
                raise ValueError('Stale revision; read current note before updating')
            revision = previous + 1
            when = stamp()
            self.db.execute('INSERT INTO notes VALUES (?,?,?,?,?,?,?) '
                'ON CONFLICT(key) DO UPDATE SET title=excluded.title,body=excluded.body,'
                'revision=excluded.revision,updated=excluded.updated',
                (key,title,body,revision,when,source_path,source_sha256))
            self.db.execute('INSERT INTO revisions VALUES (?,?,?,?,?,?)',
                            (key,revision,title,body,when,'agent'))
        return self.get(key)

    def archive(self, path, raw, reason):
        safe_relative(path)
        expected = sha(raw)
        existing = self.db.execute('SELECT sha256 FROM documents WHERE path=?',(path,)).fetchone()
        if existing:
            if existing['sha256'] != expected:
                raise ValueError('Archived source changed; do not overwrite history: '+path)
            return
        body = raw.decode('utf-8')
        with self.db:
            self.db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?)',
                            (path,expected,raw,body,reason,stamp()))

    def document(self, path):
        row = self.db.execute('SELECT * FROM documents WHERE path=?',(path,)).fetchone()
        if row is None:
            raise KeyError(path)
        if sha(row['raw']) != row['sha256']:
            raise ValueError('Archived document hash mismatch: '+path)
        return row

    def search(self, query, limit=8):
        if not query.strip() or not 1 <= limit <= 50:
            raise ValueError('Nonempty query and limit 1..50 required')
        rows = self.db.execute('''SELECT key AS id, title, body, 'note' AS kind FROM notes
            WHERE instr(title,?)>0 OR instr(body,?)>0
            UNION ALL SELECT path AS id,path AS title,body,'archive' AS kind FROM documents
            WHERE instr(path,?)>0 OR instr(body,?)>0 LIMIT ?''',
            (query,query,query,query,limit)).fetchall()
        results=[]
        for row in rows:
            pos=max(0,row['body'].find(query)-80)
            results.append(dict(id=row['id'],kind=row['kind'],title=row['title'],
                                excerpt=row['body'][pos:pos+480]))
        return results

    def backup(self, destination):
        dest=Path(destination).resolve()
        if dest == self.path or dest.exists():
            raise ValueError('Backup destination already exists')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(dest) as target:
            self.db.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup integrity check failed')
        return str(dest)


def safe_relative(name):
    p=Path(name)
    if p.is_absolute() or p.drive or p.root or '..' in p.parts or not p.parts:
        raise ValueError('Expected a confined relative path')
    return p


def restore_document(ledger, name, root):
    root=Path(root).resolve()
    dest=(root/safe_relative(name)).resolve()
    if not dest.is_relative_to(root):
        raise ValueError('Restore target escapes workspace')
    row=ledger.document(name)
    if dest.exists():
        raise ValueError('Refusing to overwrite existing file')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as stream:
        stream.write(row['raw'])
    return dict(path=str(dest),sha256=row['sha256'])


def brief(ledger, root):
    state=json.loads((root/'data/work-state.json').read_text(encoding='utf-8'))
    index=json.loads((root/state['review_index']).read_text(encoding='utf-8'))
    return dict(current=ledger.get('current'),
        handoff=[dict(r) for r in ledger.db.execute('SELECT key,title,revision FROM notes WHERE key!=? ORDER BY key',('current',))],
        active_manuscripts={k:v['document'] for k,v in index['works'].items()},
        review_index=state['review_index'],progress_report=state['progress_report'],
        commands='docs/project-records.md',goal_control='No goal is started by this command.')


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--db',type=Path,default=DEFAULT_DB)
    sub=cli.add_subparsers(dest='command',required=True)
    sub.add_parser('brief')
    get=sub.add_parser('get'); get.add_argument('key')
    history=sub.add_parser('revisions'); history.add_argument('key'); history.add_argument('--limit',type=int,default=5)
    search=sub.add_parser('search'); search.add_argument('query'); search.add_argument('--limit',type=int,default=8)
    doc=sub.add_parser('document'); doc.add_argument('path')
    put=sub.add_parser('put'); put.add_argument('--file',type=Path,required=True)
    backup=sub.add_parser('backup'); backup.add_argument('--output',type=Path,required=True)
    restore=sub.add_parser('restore-document'); restore.add_argument('path')
    reason=sub.add_parser('why'); reason.add_argument('path')
    args=cli.parse_args()
    ledger=Ledger(args.db)
    try:
        if args.command=='brief': result=brief(ledger,ROOT)
        elif args.command=='get': result=ledger.get(args.key)
        elif args.command=='document':
            row=ledger.document(args.path)
            result={k:row[k] for k in row.keys() if k!='raw'}
        elif args.command=='revisions':
            if not 1<=args.limit<=50: raise ValueError('Limit must be 1..50')
            result=[dict(r) for r in ledger.db.execute('SELECT * FROM revisions WHERE key=? ORDER BY revision DESC LIMIT ?', (args.key,args.limit))]
        elif args.command=='search': result=ledger.search(args.query,args.limit)
        elif args.command=='put':
            data=json.loads(args.file.read_text(encoding='utf-8'))
            if set(data)!={'key','title','body','expected_revision'}:
                raise ValueError('Expected key, title, body, expected_revision only')
            result=ledger.put(**data)
        elif args.command=='backup': result=dict(backup=ledger.backup(args.output))
        elif args.command=='restore-document': result=restore_document(ledger,args.path,ROOT)
        elif args.command=='why':
            row=ledger.db.execute('SELECT * FROM retained WHERE path=?',(args.path,)).fetchone()
            if row is None: raise KeyError(args.path)
            result=dict(row);result['details']=json.loads(result['details'])
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        ledger.close()


if __name__=='__main__':
    main()
