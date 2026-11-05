"""Final artifact audit, reusing completed ink decoding and semantic judgments."""
import argparse,hashlib,json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_fastparse import parse_source
from scripts.two_work_assemble import renamed
from scripts.two_work_presentation import expand_head
from scripts.long_run import LongRun,atomic_json,fingerprint

BASE='output/two-work-final-v2'


class Links(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.ids=set();self.images=0;self.math=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for k in ('href','src'):
            if k in a:self.links.append(a[k])
        self.images+=tag=='img';self.math+=tag=='math'


def document_check(work,report):
    folder=ROOT/BASE/work;d=read(folder/'recovered-document.json');prepared=read(folder/'prepared-document.json')
    if d!=prepared or parse_source((folder/'recovered.noema').read_text(encoding='utf-8'))!=d:raise ValueError('Recovered publication differs')
    ink=read(folder/'ink/report.json');records=d['declarations']+d['statements']
    if not ink['validation_success'] or len(ink['records'])!=len(records):raise ValueError('Incomplete ink evidence')
    for i,(r,expected) in enumerate(zip(ink['records'],records,strict=True)):
        if r['index']!=i or r['status']!='passed' or r['native']!=expected:raise ValueError('Wrong ink record')
    state=read('data/work-state.json');workid=work+('-1784' if work=='kant' else '-1905')
    active=read(state['review_index'])['works'][workid];source=parse_source((ROOT/active['document']).read_text(encoding='utf-8'))
    bridge=read(f'output/two-work-assembly-v2/{work}-bridge.json')
    expansion=read(f'output/two-work-presentation-v1/{work}-expansions.json')
    toc=read(folder/'source-alignment.json');positions=toc['source_to_edition'];declarations={x['name']:x for x in d['declarations']}
    for i,original in enumerate(source['statements']):
        row=expansion[i]
        if row['statement']!=i or row['unexpanded']!=renamed(original,bridge['mapping']):raise ValueError('Source assertion correspondence changed')
        expanded,steps=expand_head(row['unexpanded'],declarations)
        if expanded!=d['statements'][positions[str(i)]] or steps!=row['definitions']:raise ValueError('Definition expansion or order changed')
    inventory=read(active['source_inventory']);units=[u for u in inventory['units'] if u['kind']!='editorial']
    if len(units)!=len(toc['units']):raise ValueError('Source unit omission')
    for original,published in zip(units,toc['units'],strict=True):
        if any(published[k]!=v for k,v in original.items()):raise ValueError('Original source content changed')
    if toc['math']!=inventory['math'] or toc['identifiers']!=read(active['identifier_annotations']):raise ValueError('Source math or identification changed')
    catalog=read(folder/'meanings.json')
    for declaration in d['declarations']:
        if declaration['kind']=='primitive':
            contract=catalog[declaration['name']]['contract']
            if any(contract[k]!=declaration[k] for k in ('parameters','result')):raise ValueError('Primitive contract missing or changed')
    # Auxiliary assertions retain the preparation's complete source-checked AST.
    if d!=read(f'output/two-work-edition-v1/{work}.json'):raise ValueError('Auxiliary or declaration content changed')
    return dict(records=len(records),source_assertions=len(source['statements']),source_units=len(units),
        declarations=len(d['declarations']),auxiliary_assertions=len(d['statements'])-len(source['statements']),
        math=len(toc['math']),identifier_entries=len(toc['identifiers']['entries']),
        source_correspondence_exact=True,native_export_exact=True,decoding=dict(Counter(r['decoding'] for r in ink['records'])))


def check_links(folder):
    pages={p.resolve():Links(p.read_text(encoding='utf-8')) for p in folder.rglob('*.html')};links=0
    for path,parsed in pages.items():
        for href in parsed.links:
            u=urlsplit(href)
            if u.scheme or u.netloc:continue
            target=(path.parent/unquote(u.path)).resolve() if u.path else path
            if not target.is_file():raise ValueError('Missing publication link: '+str(path)+' -> '+href)
            if u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:raise ValueError('Missing publication anchor: '+href)
            links+=1
    return dict(html_pages=len(pages),local_links=links,images=sum(p.images for p in pages.values()),math_occurrences=sum(p.math for p in pages.values()),all_targets_exist=True)


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--run',required=True);args=cli.parse_args()
    report=read(BASE+'/report.json')
    if not report['complete'] or not report['scan_complete'] or report['changed_inputs']:raise ValueError('Both-work verification has not completed')
    pins=dict(report['source_sha256']);pins['scripts/check_two_work_publication.py']=sha('scripts/check_two_work_publication.py')
    names=[BASE+'/report.json',BASE+'/status.json']
    for work in ('kant','einstein'):
        names += [BASE+'/'+work+'/'+s for s in ('ink/report.json','recovered-document.json','recovered.noema','prepared-document.json','source-alignment.json','meanings.json')]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/BASE).rglob('*.html')]
    pins.update({p:sha(p) for p in names})
    result=dict(schema='noema-two-work-publication-audit-1',source_sha256=pins,works={})
    with LongRun(ROOT/args.run,dict(source_sha256=pins)) as run:
        for i,(path,expected) in enumerate(pins.items()):
            if sha(path)!=expected:raise ValueError('Pinned source changed: '+path)
        for work in ('kant','einstein'):
            run.emit('progress',stage='Source and recovered document '+work,completed=0,total=2)
            result['works'][work]=run.step(work,pins,lambda:document_check(work,report))
            entries=read(BASE+'/'+work+'/ink/report.json')['records']
            for start in range(0,len(entries),128):
                chunk=entries[start:start+128]
                run.emit('progress',stage='Published ink bytes '+work,completed=start,total=len(entries))
                def check():
                    for row in chunk:
                        if sha(ROOT/BASE/work/'ink'/row['svg'])!=row['svg_sha256']:raise ValueError('Published ink differs from verified artifact')
                    return dict(records=len(chunk),content=fingerprint([(r['svg'],r['svg_sha256']) for r in chunk]))
                run.step(work+'-ink-'+str(start),[(r['svg'],r['svg_sha256']) for r in chunk],check)
        run.emit('progress',stage='Whole publication links',completed=0,total=1)
        result['links']=run.step('links',pins,lambda:check_links(ROOT/BASE))
        result.update(complete=True,semantic_carry=report['semantic_carry'],method='Recheck output bytes, source correspondence and publication integrity; reuse exact ink decoding. No new semantic judgments.')
        atomic_json(ROOT/'reports/two-work-final-publication-v1.json',result)
        run.emit('progress',stage='Final publication audit complete',completed=1,total=1)
        print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False))


if __name__=='__main__':main()
