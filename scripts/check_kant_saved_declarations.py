"""Write actual saved declarations, preserving source name/meaning bridges."""
from functools import lru_cache
import hashlib,json,time
from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.check_kant_declarations import reader_without_target,pins as prior_pins
from scripts.shared_modality import renamed
from scripts.kant_lexical_context import LexicalContext
from scripts import kant_public_fragment as writing
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

ORIGINALS=('aa','hztb','ev','va','rqwd')
OUT=ROOT/'output/kant-saved-declarations'
RUN=ROOT/'.noema-project/runs/kant-saved-declarations-v1'


@lru_cache(maxsize=1)
def inputs():
    baseline=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=baseline['source_sha256'][name]:
            raise ValueError('Saved declaration input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'));rows=[]
    for original in ORIGINALS:
        source=next(d for d in bridge['source_declarations'] if d['name']==original)
        target=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][original])
        if renamed(source,bridge['mapping'])!=target:raise ValueError('Source declaration or name bridge changed')
        rows.append(target)
    return published,rows


def cases():return [(key,'保存宣言 '+key+'：名前・型・本体',d) for key,d in zip(ORIGINALS,inputs()[1])]


@lru_cache(maxsize=5)
def checked(index):
    published,rows=inputs();source=rows[index];key,label,_=cases()[index]
    start=time.perf_counter()
    drawing=writing.compile_declaration(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=writing.decode_declaration(list(reversed(from_svg(svg))),lexicon=reader_without_target(published,source['name']))
    if recovered!=source:raise ValueError('Saved declaration changed: '+key)
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],seconds=time.perf_counter()-start,
        syntax_sha256=syntax_hash(source),original_symbol=key,public_symbol=source['name'],
        declaration_kind=source['kind'],target_body_and_signature_absent=True,
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'reports/kant-declarations-v2.json',
                 'scripts/check_kant_saved_declarations.py','tests/test_kant_saved_declarations.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-saved-declarations-1',version=writing.VERSION,title='保存辞書の宣言を直接書く',
        intro='原始語1件と定義4件を、確認用の全称式・等式を加えずに書き戻します。',
        limits=['Five actual declarations with public spellings and unchanged dependencies',
                'No new semantic judgments; complete dictionary order, document layout and visual approval remain'])


def build_report():return report(OUT,pins)
