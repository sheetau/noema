"""Collect already published contracts without importing historical validators."""
from scripts.two_work_inventory import ROOT,read,sha
from scripts.concept2_document import full_name
from scripts import concept2_composition as c
from scripts.kant_public_lexicon import words
from scripts.long_run import atomic_json


def main():
    plan=read('output/two-work-plan-v1.json');out=ROOT/'output/two-work-edition-v1'
    pins={'scripts/two_work_catalog.py':sha('scripts/two_work_catalog.py')};public={}
    for token,(name,entry) in words().items():
        public[token]=dict(label=name,contract=entry,origin='shared vocabulary')
    for path in sorted((ROOT/'noema/resources').glob('visible-*.json')):
        data=read(path)
        if not data.get('spellings') or not data.get('basis'):continue
        basis=read(data['basis']);primitives=basis.get('primitives',{})
        if isinstance(primitives,list):primitives={d['symbol']:d for d in primitives}
        for name,parts in data['spellings'].items():
            if name not in primitives:continue
            token=full_name([c.old.root_symbol(p) for p in parts])
            public[token]=dict(label=name,contract=primitives[name],origin=data['basis'],manifest=path.relative_to(ROOT).as_posix())
    counts={}
    for work in ('kant','einstein'):
        document=read(out/(work+'.json'));bridge=read(f'output/two-work-assembly-v2/{work}-bridge.json');entries={}
        for old,new in bridge['mapping'].items():
            if old in plan['works'][work]['meanings']:
                entries.setdefault(new,dict(source_meanings=[]))['source_meanings'].append(dict(symbol=old,**plan['works'][work]['meanings'][old]))
        for d in document['declarations']:
            row=entries.setdefault(d['name'],dict(source_meanings=[]))
            if d['kind']=='definition':continue
            if d['name'] in public:row.update(public[d['name']])
            else:
                candidates=[x for x in row['source_meanings'] if x['kind']=='primitive' and
                            all(x['contract'][k]==d[k] for k in ('parameters','result'))]
                if not candidates:raise ValueError('Unpublished primitive contract: '+d['name'])
                row.update(label=candidates[0]['symbol'],contract=candidates[0]['contract'],origin=candidates[0]['basis'])
            if any(row['contract'][k]!=d[k] for k in ('parameters','result')):raise ValueError('Published contract signature changed')
            for key in ('origin','manifest'):
                if row.get(key) and (ROOT/row[key]).is_file():pins[row[key]]=sha(row[key])
        atomic_json(out/(work+'-catalog.json'),entries)
        counts[work]=dict(primitives=sum(d['kind']=='primitive' for d in document['declarations']),entries=len(entries))
    atomic_json(out/'catalog-report.json',dict(source_sha256=pins,works=counts))
    print(counts)


if __name__=='__main__':main()
