"""Check course geometry, semantic contrasts, distribution and grading boundaries."""
from copy import deepcopy
from functools import lru_cache
from html import unescape
from itertools import product
from pathlib import Path
import json
import re
import zipfile
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.reader_course import *
from scripts.visible_senses_book import decode_book
from scripts.visible_sharing import SharedReader
from scripts.visible_word_forms import canonical
from scripts.visible_page import FRAMES
from scripts.visible_lexical_script import _shape_set
from scripts.visible_word_forms import _marker
from scripts.visible_syntax import END

REPORT='reports/reader-course-v1.json'
def svg_blocks(text):return re.findall(r'<svg\b.*?</svg>',text,re.S)
def legend_reader(svg):
    tokens=recognize(from_svg(svg));r=SharedReader(tokens,vocabulary())
    if r.take()!=FRAMES['start'] or r.natural()!=0 or tokens[-1]!=FRAMES['finish']:raise ValueError('Missing legend scale frame')
    return r
def finish_legend(r):
    if r.take()!=FRAMES['finish'] or r.i!=len(r.tokens):raise ValueError('Extra legend geometry')
def saved_assets():
    text=(OUT/'learner/exercises.html').read_text(encoding='utf-8')
    sections=re.findall(r'<section class="exercise" data-question="(\d+)">(.*?)</section>',text,re.S)
    if len(sections)!=17 or len({k for k,s in sections})!=17:raise ValueError('Missing or duplicate exercises')
    return {k:svg_blocks(s) for k,s in sections}

def saved_geometry_checks():
    assets=saved_assets();results=[]
    for key,svgs in assets.items():
        if key in basic_documents():
            if len(svgs)!=1:raise ValueError('Basic exercise page count differs')
            d=decode_page(from_svg(svgs[0]),vocabulary())['document'];wanted=basic_documents()[key]
        else:
            d=decode_book([from_svg(s) for s in svgs],vocabulary())['document']
            from scripts.check_visible_senses_library import native_example
            wanted=native_example(ADVANCED[key])
        if vocabulary().decode_names(d)!=wanted:raise ValueError('Exercise geometry differs: '+key)
        results.append(dict(id=key,pages=len(svgs),sha256=[digest(s.encode('utf-8')) for s in svgs]))
    return results

def dictionary_checks():
    text=(OUT/'learner/dictionary.html').read_text(encoding='utf-8')
    articles=re.findall(r'<article class="card wordcard"><h2>(.*?)</h2>(.*?)</article>',text,re.S)
    if len(articles)!=375 or {unescape(n) for n,a in articles}!=set(vocabulary()._words):raise ValueError('Dictionary inventory differs')
    for escaped,article in articles:
        name=unescape(escaped);svgs=svg_blocks(article)
        if len(svgs)!=1:raise ValueError('Dictionary word has wrong glyph count')
        r=legend_reader(svgs[0]);word=r.word()
        if word!=vocabulary().word(name):raise ValueError('Dictionary spelling differs: '+name)
        finish_legend(r)
        if list(map(float,ET.fromstring(svgs[0]).get('viewBox').split()))[1::2]!=[-64.,192.]:raise ValueError('Dictionary scale differs')
        e=vocabulary().entry(name)
        if escape(e['meaning']) not in article or any(escape(x) not in article for x in e['roles']+e['context']+e['contrast']):raise ValueError('Dictionary meaning differs: '+name)
    return dict(words=375,definitions=352,primitive_declarations=23)

def guide_checks():
    text=(OUT/'learner/index.html').read_text(encoding='utf-8')
    section=re.search(r'<section id="reference">(.*?)</section>',text,re.S).group(1)
    svgs=svg_blocks(section);names=list(curriculum()['keywords'])
    if len(svgs)!=len(names):raise ValueError('Grammar legend count differs')
    for name,svg in zip(names,svgs,strict=True):
        r=legend_reader(svg)
        if r.keyword()!=name:raise ValueError('Grammar operation differs')
        finish_legend(r)
    frames=svg_blocks(re.search(r'<section id="rows">(.*?)</section>',text,re.S).group(1))
    expected=[FRAMES[k] for k in curriculum()['frames']]+[_shape_set(_marker(k,0.)['shapes']) for k in curriculum()['markers']]+[END]
    if len(frames)!=len(expected):raise ValueError('Frame legend count differs')
    for svg,token in zip(frames,expected,strict=True):
        r=legend_reader(svg)
        if r.take()!=token:raise ValueError('Frame or name marker differs')
        finish_legend(r)
    numbers=svg_blocks(re.search(r'<section id="numbers">(.*?)</section>',text,re.S).group(1))
    if len(numbers)!=6:raise ValueError('Numeral legend count differs')
    for svg,n in zip(numbers,(0,1,2,3,12,16),strict=True):
        r=legend_reader(svg)
        if r.natural()!=n:raise ValueError('Binary numeral differs')
        finish_legend(r)
    for key,d in teaching_documents().items():
        expected=rendered_basic(key,True)['svg']
        if expected not in text or vocabulary().decode_names(decode_page(from_svg(expected),vocabulary())['document'])!=d:raise ValueError('Worked example differs')
    return dict(grammar_operations=len(names),row_markers=4,name_markers=2,worked_documents=2)

def unknown(*args):raise ValueError('Unspecified course interpretation')
def model(**changes):
    d=dict(aki=lambda:'a',nao=lambda:'b',book=lambda:'a',home=lambda:'a',town=lambda:'b',
        rain=unknown,red=unknown,round=unknown,above=unknown,inside=unknown,give=unknown)
    d.update(changes);return d
def values(key,m):
    d=basic_documents()[key];primitives={x['name']:m[x['name']] for x in d['declarations'] if x['kind']=='primitive'}
    return evaluate_document(d,individuals=('a','b'),situations=('now',),primitives=primitives,max_steps=2000000)
def answers(keys,m):return [values(k,m)[0]['value'] for k in keys]

@lru_cache(maxsize=1)
def semantic_checks():
    count=0
    for a,b in product((False,True),repeat=2):
        m=model(red=lambda x:a if x=='a' else b,rain=lambda x:a)
        if answers(('03','04','08','14'),m)!=[not(a and b),not a and not b,a,a]:raise ValueError('Negation, question or evaluation differs')
        count+=1
    pairs=list(product(('a','b'),repeat=2))
    for mask in range(16):
        rel={p for i,p in enumerate(pairs) if mask&(1<<i)}
        expected=[('a','b') in rel,all(any((x,y) in rel for y in ('a','b')) for x in ('a','b')),
            all(any((y,x) in rel for y in ('a','b')) for x in ('a','b'))]
        if answers(('01','05','06'),model(above=lambda x,y:(x,y) in rel))!=expected:raise ValueError('Relation binding differs')
        count+=1
    for a,b in product((False,True),repeat=2):
        m=model(red=lambda x:a,round=lambda x:b,rain=lambda x:a,above=lambda *x:a,inside=lambda *x:b)
        if answers(('10','12'),m)!=[a and b,a and b]:raise ValueError('Definition or sharing differs')
        if values('11',model(rain=lambda x:a,red=lambda x:b))!=[dict(kind='suppose',condition_value=a,statements=[dict(kind='ask',value=b)])]:raise ValueError('Assumption scope differs')
        count+=1
    if answers(('07',),model())!=[True] or values('09',model())!=[]:raise ValueError('Quotation or definition asserts hidden content')
    if answers(('13',),model())!=[False] or answers(('13',),model(nao=lambda:'a'))!=[True]:raise ValueError('Sequence order or referent identity differs')
    wanted=('b','a','a');fixed=[]
    if answers(('02',),model(give=lambda *a:a==wanted))!=[True]:raise ValueError('Giving roles differ')
    for slot in range(3):
        other=list(wanted);other[slot]='b' if other[slot]=='a' else 'a'
        if answers(('02',),model(give=lambda *a:a==tuple(other)))!=[False]:raise ValueError('Misbound giving role accepted')
        fixed.append(slot)
    return dict(models=count,individuals=2,relation_tables=16,giving_fixed_slot_diagnostics=fixed,
        quotation_without_truth=True,definition_without_assertion=True,referent_identity_contrast=True)

def distribution_checks():
    names={'index.html','dictionary.html','exercises.html'}
    if {p.name for p in (OUT/'learner').iterdir()}!=names:raise ValueError('Extra learner file')
    with zipfile.ZipFile(OUT/'noema-reader-v1.zip') as z:
        if set(z.namelist())!=names or len(z.namelist())!=3:raise ValueError('Unexpected distributed file')
        for name in names:
            if z.read(name)!=(OUT/'learner'/name).read_bytes():raise ValueError('ZIP differs from current learner files')
    text=(OUT/'learner/exercises.html').read_text(encoding='utf-8')
    if any(marker in text for marker in ('"correct"','"reason"','answers.json','reviewer/','"declarations"','"statements"')):raise ValueError('Answer material leaked into exercises')
    for p in (OUT/'learner').iterdir():
        content=p.read_text(encoding='utf-8')
        if re.search(r'(?:src|href)=["\']https?://',content):raise ValueError('Course requires an external resource')
    return dict(learner_files=sorted(names),answer_files_distributed=False,external_resources=0)

def verify_published(root=ROOT):
    report=json.loads((root/REPORT).read_text(encoding='utf-8'))
    for path,wanted in {**report['source_sha256'],**report['artifact_sha256']}.items():
        if digest((root/path).read_bytes())!=wanted:raise ValueError('Published course input differs: '+path)
    return report['exercise_sha256']

def prepare():
    from scripts.reader_course import prepare as build
    build()

def build_report():
    rows=saved_geometry_checks();assets=saved_assets();identity=exercise_identity(assets)
    key=json.loads((OUT/'reviewer/answers.json').read_text(encoding='utf-8'))
    if key['exercise_sha256']!=identity or key['exercises']!=[dict(id=x['id'],correct=x['correct'],reason=x['reason']) for x in curriculum()['exercises']]:raise ValueError('Reviewer key differs')
    for k,d in basic_documents().items():
        if parse((OUT/('reviewer/exercise-'+k+'.noema')).read_text(encoding='utf-8'))!=d:raise ValueError('Reviewer source differs')
    result=dict(schema='noema-reader-course-report-1',edition=12,exercise_sha256=identity,exercises=rows,
        dictionary=dictionary_checks(),guide=guide_checks(),semantics=semantic_checks(),distribution=distribution_checks(),
        human_participants=0,independent_reading_verified=False,artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.rglob('*')) if p.is_file() and p.suffix in ('.html','.json','.noema','.zip')})
    paths=[SOURCE,'scripts/reader_course.py','scripts/check_reader_course.py','tests/test_reader_course.py','docs/noema-reader-v1.md']
    for old in ('reports/visible-senses-v1.json','reports/visible-sharing-v1.json'):
        prior=json.loads((ROOT/old).read_text(encoding='utf-8'));paths.extend([old,*prior['source_sha256']])
        for path,h in prior['source_sha256'].items():
            if digest((ROOT/path).read_bytes())!=h:raise ValueError('Previous evidence differs: '+path)
    result['source_sha256']={p:digest((ROOT/p).read_bytes()) for p in sorted(set(paths))}
    result['limits']=['Machine geometry recovery and finite semantic contrasts verify the administered material, not actual human reading.',
        'Multiple-choice answers cannot establish independent authorship, free reconstruction, productive writing or arbitrary-document comprehension.',
        'Participant role and prior answer exposure are self-reports; software does not authenticate independence.',
        'No participant responses have been collected; synthetic grader tests are not reader-study data.',
        'The learner ZIP contains only three offline HTML files; source exercises and answer keys are separate reviewer artifacts.']
    return result
