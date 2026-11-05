"""Content-only integration audit; preserves semantic and geometry boundaries."""
import json
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
from noema.constructed_discourse import normalize_document
from scripts.semantic_boundaries import raw,composed,basis
from scripts.two_work_inventory import ROOT,read,sha
from scripts.two_work_fastparse import parse_source
from scripts.two_work_run import semantic_inputs
from scripts.two_work_assemble import renamed
from scripts.long_run import LongRun,atomic_json

RUN='.noema-project/runs/semantic-boundaries-final-v1'
OUT='output/semantic-boundaries-v1'


class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag in ('a','img'):self.links.append(a.get('href',a.get('src','')))


def prepare():
    paths=['scripts/semantic_boundaries.py','scripts/check_semantic_boundaries.py','scripts/publish_semantic_boundaries.py',
           'scripts/verify_semantic_boundaries_release.py','tests/test_semantic_boundaries.py','docs/semantic-boundaries-v1.md',
           'data/general-language-catalog-v1.json','data/general-language-catalog-v2.json','data/semantic-boundaries-basis-v1.json',
           'data/general-language-release-v2.json','data/work-state.json','examples/v016/semantic-boundaries-v1.noema',
           'reports/semantic-boundaries-v3.json',OUT+'/index.html',OUT+'/report.json',OUT+'/document.json',OUT+'/source.json',
           OUT+'/examples.json',OUT+'/source.noema','scripts/long_run.py','scripts/two_work_run.py']
    pins={p:sha(p) for p in paths}
    with LongRun(ROOT/RUN,dict(source_sha256=pins),resume=(ROOT/RUN).exists()) as run:
        baseline=semantic_inputs(run);assert baseline['unchanged']
        old=read('data/general-language-catalog-v1.json');new=read('data/general-language-catalog-v2.json')
        assert all(new['entries'][n]==r for n,r in old['entries'].items())
        assert len(new['entries'])==1952 and len(raw())==43
        assert len({r['symbol'] for r in new['entries'].values()})==1952
        for path,h in new['source_sha256'].items():
            if sha(path)!=h:raise ValueError('Catalog source changed: '+path)
        meaning=read('reports/semantic-boundaries-v3.json')
        for path,h in meaning['source_sha256'].items():
            if sha(path)!=h:raise ValueError('Meaning input changed: '+path)
        assert read('data/semantic-boundaries-basis-v1.json')==basis()
        assert parse_source((ROOT/'examples/v016/semantic-boundaries-v1.noema').read_text(encoding='utf-8'))==composed()
        source=read(OUT+'/source.json');visible=read(OUT+'/document.json');alignment=read(OUT+'/examples.json');ink=read(OUT+'/report.json')
        assert parse_source((ROOT/(OUT+'/source.noema')).read_text(encoding='utf-8'))==source
        assert normalize_document(renamed(source,alignment['names']))==visible
        assert visible['declarations']+visible['statements']==[r['native'] for r in ink['records']]
        assert ink['validation_success'] and ink['counts']=={'passed':195}
        for path,h in ink['source_sha256'].items():
            if sha(path)!=h:raise ValueError('Writing input changed: '+path)
        for i,r in enumerate(ink['records']):
            if i%32==0:run.emit('progress',stage='Visible artifact hashes',completed=i,total=len(ink['records']))
            if sha(OUT+'/ink/'+r['cache_key']+'.svg')!=r['svg_sha256']:raise ValueError('Ink changed')
        parser=Links();parser.feed((ROOT/(OUT+'/index.html')).read_text(encoding='utf-8'));missing=[]
        for target in parser.links:
            u=urlsplit(target)
            if u.scheme:continue
            if u.path:
                if not (ROOT/OUT/unquote(u.path)).is_file():missing.append(target)
            elif u.fragment and unquote(u.fragment) not in parser.ids:missing.append(target)
        assert not missing,missing
        assert len(parser.ids)==len(set(parser.ids))
        # Existing native meanings and writing implementation were not edited.
        # Preserve their full audit rather than launching old model suites.
        result=dict(schema='noema-semantic-boundary-completion-1',preserved_works=baseline,old_catalog_unchanged=1909,
            new_definitions=43,new_common_primitives=0,total_catalog=1952,native_examples=len(alignment['cases']),
            visible_records=195,writing_success=True,links=dict(checked=len(parser.links),missing=missing),
            semantic_evidence='reports/semantic-boundaries-v3.json',focused_tests='tests/test_semantic_boundaries.py',
            theoretical_constructions=['arbitrary well-formed value types','heterogeneous typed binding without quoted variable capture',
                'finite reachability without a fixed path bound','unbounded indexed processes','self-referential content as constraints'],
            completion_scope='Meaning-level compositional expressivity; human reception and universal effective evaluation excluded',
            source_sha256=pins)
        for p,h in pins.items():
            if sha(p)!=h:raise ValueError('Input changed during final audit: '+p)
        atomic_json(ROOT/RUN/'result.json',result);run.emit('progress',stage='Complete',completed=1,total=1)


def build_report():return read(RUN+'/result.json')
