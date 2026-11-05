"""Read retained v7 ink with the extended reader; never redraw old previews."""
import hashlib
import json
from pathlib import Path
import time
from scripts.concept2_document import complete_public_dictionary
from scripts.concept2_codec_v8 import Codec
from scripts.long_run import atomic_json

ROOT=Path(__file__).resolve().parents[1]


def main():
    start=time.perf_counter();base=ROOT/'output/kant-concept2-v7'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    dictionary=complete_public_dictionary(read(ROOT/'output/kant-presentation-spellings/dictionary.json'))
    codec=Codec(dictionary);trace=read(base/'trace.json')['cases'];extended=read(base/'extended-trace.json')['cases'];verified={}
    def check(file,expected,page=False):
        path=base/file;raw=path.read_bytes()
        recovered=codec.read_page(raw.decode())['statements'] if page else codec.read_svg(raw.decode())['native']
        if recovered!=expected:raise ValueError('Retained v7 syntax differs: '+file)
        verified[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
    for r in trace:check(f'statement-{r["statement"]}.svg',r['public'])
    check('kant-reading.svg',[r['public'] for r in trace],True)
    check('kant-page.svg',[r['public'] for r in trace],True)
    for r in extended:check('extended-'+r['key']+'.svg',r['source'])
    check('extended-reading.svg',[r['source'] for r in extended],True)
    report=dict(schema='concept2-v8-retained-ink-1',native_exact=True,svg_files=len(verified),
        unchanged_svg_sha256=verified,seconds=round(time.perf_counter()-start,3),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
            'scripts/concept2_codec_v8.py','scripts/concept2_document.py','scripts/check_concept2_v8_compatibility.py',
            'scripts/concept2_geometry_v5.py','output/kant-presentation-spellings/dictionary.json')})
    atomic_json(ROOT/'output/concept2-v8-compatibility.json',report)
    print(json.dumps({k:report[k] for k in ('native_exact','svg_files','seconds')}))


if __name__=='__main__':main()
