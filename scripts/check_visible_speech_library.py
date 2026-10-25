"""Visible speech profiles with explicit relations and closed descriptions."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_speech_vocabulary import SpeechVocabulary,ROOT,MANIFEST,LIBRARY,BASIS
from scripts.visible_speech_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.visible_word_forms import Word,symbol
from scripts.shared_speech import I,S,T,C,U,OCCURS,PRESENTS,CONVEYS,TARGETS,SOLICITS,UNDERTAKES,SUPPORTS,REASONSHOWN,AUTHORITY,BEFORE,raw
from scripts.shared_reference import lam,definition,truth
from scripts.shared_modality import v,call,op
from scripts.shared_time import q,allof

OUT=ROOT/'output/visible-speech-library-v1'
EXAMPLES=(('request','speechrequest',False),('request-outcome','requestrealized',False),
    ('promise','speechpromise',True),('promise-outcome','promiserealized',True),
    ('accepted','speechaccepted',False),('declined','speechdeclined',False),
    ('advice','speechadvice',False),('command','speechcommand',False))
SOURCES={label:'examples/v016/visible-speech-'+label+'-v1.noema' for label,n,p in EXAMPLES}


@lru_cache(maxsize=1)
def vocabulary():return SpeechVocabulary()
@lru_cache(maxsize=1)
def new_names():return tuple(d['name'] for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
def eq(a,b):return op('equal',a,b)
def quote(n):return dict(kind='quote',body=dict(kind='function_ref',symbol=n))
def quantify(parameters,body):
    for n,t in reversed(parameters):body=q('forall',n,t,body)
    return body
def doc(names,extra=(),body=None):
    result=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(names),statements=[])))
    result['declarations']+=list(extra)
    if body is not None:result['statements']=[dict(kind='assert',body=body)]
    return normalize_document(result)
def local(parts):return symbol(Word('compound',parts),vocabulary())
def matches(sort,expected):
    parameters=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
    return lam(parameters,allof(*(eq(v(n),e) for (n,t),e in zip(parameters,expected))))


def speech_example(name,promise=False):
    person=call('aki');recipient=call('nao');context=v('context');outcome=v('outcome')
    action=local(('book','fly','fly'));message=local(('book','fly','book'))
    # These are controlled role-binding examples. The stipulated content holds
    # for Aki, not Nao; it is not a claim about actual behavior by named people.
    action_def=definition(action,[('actor',I)],C,dict(kind='content',variable='world',body=eq(v('actor'),person)))
    message_def=definition(message,[('subject',I)],U,dict(kind='message',force='assert' if promise else 'ask',
        content=call(action,v('subject'))))
    target=person if promise else recipient
    received=[person,recipient,recipient,quote(message),context]
    values=dict(person=person,activity=person,recipient=recipient,subject=recipient,message=quote(message),context=context,
        action=quote(action),actor=target,reason=person,goal=quote(action),role=recipient,outcome=outcome)
    values.update(occurs=matches(OCCURS,[person,context]),presents=matches(PRESENTS,[person,person,context]),
        conveys=matches(CONVEYS,received),receives=matches(CONVEYS,received),understands=matches(CONVEYS,received),
        accepts=matches(CONVEYS,received),declines=lam([('arg'+chr(97+i),t) for i,t in enumerate(CONVEYS['parameters'])],truth(False)),
        targets=matches(TARGETS,[person,recipient,quote(message),target,quote(action),context]),
        solicits=matches(SOLICITS,[person,person,recipient,quote(action),context]),
        undertakes=matches(UNDERTAKES,[person,recipient,person,quote(action),context]),
        supports=matches(SUPPORTS,[person,person,recipient,quote(action),quote(action),context]),
        reasonshown=matches(REASONSHOWN,[person,recipient,person,context]),
        claims=lam([('arg'+chr(97+i),t) for i,t in enumerate(AUTHORITY['parameters'])],truth(False)),
        before=matches(BEFORE,[context,outcome]))
    params=next(d['parameters'] for d in raw()['declarations'] if d['name']==name)
    body=call(name,*(values[p['name']] for p in params))
    expected=name not in ('requestrealized','speechdeclined','speechcommand')
    if not expected:body=op('not',body)
    guard=op('not',eq(person,recipient));ps=[('context',S)]
    if name.endswith('realized'):
        ps.append(('outcome',S));guard=op('and',guard,op('not',eq(context,outcome)))
    return doc([name,'aki','nao'],[action_def,message_def],quantify(ps,op('implies',guard,body)))


def model():return {vocabulary().declaration('aki')['name']:lambda:'a',vocabulary().declaration('nao')['name']:lambda:'b'}


@lru_cache(maxsize=1)
def cases():
    rows=[];vocab=vocabulary()
    examples=[('dictionary',doc(new_names()))]+[(label,speech_example(n,p)) for label,n,p in EXAMPLES]
    for label,native in examples:
        encoded=vocab.encode(native);w=PublicWriter(vocab);w.document(encoded)
        page=compile_page(encoded,vocab,max_width=4800.);svg=to_svg(page['shapes'])
        decoded=decode_page(from_svg(svg),vocab)['document']
        if decoded!=encoded or vocab.decode_names(decoded)!=native:raise ValueError('Speech shape decoding differs: '+label)
        result=[]
        if label!='dictionary':
            result=evaluate_document(decoded,individuals=('a','b'),situations=('now','later'),primitives=model(),max_steps=1000000)
            if result!=[dict(kind='assert',value=True)]:raise ValueError('Visible speech meaning differs: '+label)
        rows.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=result,glyphs=len(w.glyphs)))
    return rows


@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in new_names():
        d=vocab.declaration(name);parameters=[('arg'+chr(97+i),p['sort']) for i,p in enumerate(d['parameters'])]
        invocation=call(d['name'],*(v(n) for n,t in parameters));body=quantify(parameters,eq(invocation,invocation))
        quoted=quote(d['name'])
        # Realization evaluates rank-zero action descriptions. Its own quoted
        # function reference must therefore live at rank one.
        if name in ('requestrealized','promiserealized'):quoted['rank']=1
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=eq(quoted,quoted))]))
        w=PublicWriter(vocab);w.document(native);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Typed speech call differs: '+name)
        rows.append(dict(name=name,parts=list(vocab.word(name).parts),quotation_rank=quoted.get('rank',0),glyphs=len(w.glyphs),shapes=len(shapes)))
    return rows


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    for row in cases():
        if row['label'] in SOURCES:
            target=ROOT/SOURCES[row['label']];text=format_graph(row['native'])+'\n'
            if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible speech differs')
            if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
        (OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    preview()


def preview():
    from PIL import Image,ImageDraw
    for start in range(0,len(new_names()),10):
        canvas=Image.new('RGB',(1180,850),'white');draw=ImageDraw.Draw(canvas)
        for i,name in enumerate(new_names()[start:start+10]):
            x,y=(i%2)*590+24,(i//2)*170+12
            w=PublicWriter(vocabulary());w.name(vocabulary().declaration(name)['name'])
            shapes=render(w.glyphs)['shapes'];scale=.8
            lo=min(s['y']-s['r'] if s['kind']=='circle' else min(s['y1'],s['y2']) for s in shapes)
            for s in shapes:
                if s['kind']=='circle':
                    cx,cy,r=x+s['x']*scale,y+30+(s['y']-lo)*scale,s['r']*scale
                    draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline='#203438',width=2)
                else:draw.line((x+s['x1']*scale,y+30+(s['y1']-lo)*scale,x+s['x2']*scale,y+30+(s['y2']-lo)*scale),fill='#203438',width=2)
            draw.text((x,y),name,fill='#203438')
        canvas.save(OUT/('speech-forms-'+str(start//10+1)+'.png'))


def build_report():
    for row in cases():
        if row['label'] in SOURCES and parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))!=row['native']:
            raise ValueError('Published speech example differs')
    result=dict(schema='noema-visible-speech-evidence-1',edition=8,words=218,root_words=30,shared_compounds=188,
        shared_definitions=197,shared_primitives=21,new_single_glyphs=0,new_primitive_declarations=0,
        typed_call_shape_decoding=word_checks(),shape_decoding=[dict(label=r['label'],glyphs=r['glyphs'],rows=r['page']['rows'],
            shapes=len(r['page']['shapes']),result=r['result'],svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    preserved=['reports/visible-generality-v1.json','reports/shared-speech-v1.json']
    paths=[MANIFEST,LIBRARY,BASIS,*SOURCES.values(),'scripts/visible_speech_vocabulary.py','scripts/visible_speech_page.py',
        'scripts/check_visible_speech_library.py','tests/test_visible_speech_library.py','docs/visible-speech-v1.md',*preserved]
    for report in preserved:
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(hashes)
        for p,digest in hashes.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Prior evidence changed: '+p)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['Every visible declaration, description and lambda body recovers from circle/line geometry.',
        'Examples stipulate social relations in Native lambdas; only the two existing individual names have host interpretations.',
        'Person/activity and recipient/subject deliberately share fixture values; complete slot diagnostics are separately in shared-speech evidence.',
        'Finite role-binding examples are not evidence for real intentions, commitments, authority or behavior.',
        'Typed higher-order call and quotation roundtrips test syntax, not all function values.',
        'No raster OCR or third-party reading; frozen geometry and resource limits unchanged.']
    return result
