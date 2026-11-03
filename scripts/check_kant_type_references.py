"""Scoped type contraction with saved declaration and statement ink."""
from functools import lru_cache
import hashlib,json
from noema.constructed_discourse import function_sort,description_sort,sequence_sort,question_sort
from scripts import kant_public_fragment as writing,kant_scoped_types as types
from scripts import check_kant_declarations as declarations
from scripts import check_kant_saved_declarations as saved
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_page_public_context import ROOT
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.kant_structural_trial import prepare as trial,report

OUT=ROOT/'output/kant-type-references'
RUN=ROOT/'.noema-project/runs/kant-type-references-v2'


def type_cases():
    a=description_sort(function_sort(['individual'],'content'))
    b=sequence_sort('number');c=question_sort([])
    return [
        ('adjacent',[a,a]),('outward',[a,b,a]),('farther',[a,b,c,a]),
        ('nested',[a,function_sort([a,a],a)]),
        ('closed-inner',[a,function_sort([b],b),b]),
        ('ranked',[description_sort('number',2),description_sort('number',2)]),
        ('function-result',[function_sort([a],a)]),
        ('base-unchanged',['individual','individual']),
    ]


@lru_cache(maxsize=1)
def inputs():
    return [(key,*declarations.canonical(dict(kind='primitive',name=declarations.name(),parameters=values,result='truth')))
            for key,values in type_cases()]


def cases():return [(key,'型参照：'+key,source) for key,source,_ in inputs()]


@lru_cache(maxsize=10)
def checked(index):
    key,source,published=inputs()[index]
    drawing=writing.compile_declaration(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    if writing.decode_declaration(list(reversed(from_svg(svg))),lexicon=declarations.reader_without_target(published,source['name']))!=source:
        raise ValueError('Type contraction changed declaration: '+key)
    plain=types.type_list_tokens(source['parameters'],references=False)
    short=types.type_list_tokens(source['parameters'])
    return dict(key=key,label=cases()[index][1],source=source,svg=svg,width=drawing['width'],syntax_sha256=syntax_hash(source),
        expanded_header_tokens=len(plain),current_header_tokens=len(short),type_reference_tokens=[t for t in short if t in types.REFERENCE_TOKENS],
        branch_limits=drawing.get('branch_limits',[]),unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


@lru_cache(maxsize=1)
def preserved_rows():
    rows=[dict(row,mode='statement') for row in declarations.preserved_rows()]
    for module,report_name in ((declarations,'reports/kant-declarations-v2.json'),(saved,'reports/kant-saved-declarations-v1.json')):
        report_=json.loads((ROOT/report_name).read_text(encoding='utf-8'))
        if module is declarations:entries=declarations.inputs()
        else:
            published,ds=saved.inputs()
            entries=[(key,label,source,published) for (key,label,_),source in zip(saved.cases(),ds)]
        for key,_,source,published in entries:
            path=(module.OUT/(key+'.svg')).relative_to(ROOT).as_posix()
            old=next(r for r in report_['diagnostics'] if r['key']==key)
            if syntax_hash(source)!=old['syntax_sha256']:raise ValueError('Saved declaration syntax changed')
            rows.append(dict(path=path,stamp=report_['source_sha256'][path],source=source,published=published,mode='declaration'))
    return rows


@lru_cache(maxsize=64)
def preserved(index):
    row=preserved_rows()[index];raw=(ROOT/row['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['stamp']:raise ValueError('Saved ink changed')
    shapes=list(reversed(from_svg(raw.decode('utf-8'))))
    if row['mode']=='declaration':
        reader=declarations.reader_without_target(row['published'],row['source']['name'])
        recovered=writing.decode_declaration(shapes,lexicon=reader)
    else:
        reader=LexicalContext.from_published(row['context'].published()) if row['context'] else None
        recovered=writing.decode(shapes,lexicon=reader)
    if recovered!=row['source']:raise ValueError('Type reader changed saved syntax')
    return dict(svg=row['path'],syntax_sha256=syntax_hash(row['source']),mode=row['mode'])


def pins():
    result=saved.pins()
    names={'scripts/kant_scoped_types.py','scripts/check_kant_type_references.py','tests/test_kant_type_references.py',
        'docs/kant-type-references.md','reports/kant-saved-declarations-v1.json'}
    names.update(r['path'] for r in preserved_rows())
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    return dict(sorted(result.items()))


def prepare():
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=preserved,
        preserved_count=len(preserved_rows()),schema='kant-type-references-1',version=writing.VERSION,
        title='完結した引数型を参照する',intro='型列の範囲内で同じ複合型を短縮し、元の型へ戻します。',
        limits=['Scoped type notation only; no new meaning or target-type oracle',
                'Dictionary document, line/page layout and final appearance remain incomplete'])


def build_report():return report(OUT,pins)
