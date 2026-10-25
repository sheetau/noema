"""Visible answer scopes and retained adoption changes with Native fixture bodies."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_conversation_vocabulary import ConversationVocabulary,ROOT,MANIFEST,LIBRARIES
from scripts.visible_conversation_page import PublicWriter,compile_page,decode_page,decode_document,to_svg,from_svg
from scripts.visible_syntax_geometry import render
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import I,S,T,U,C,lam,definition,truth
from scripts.shared_modality import v,call,op
from scripts.shared_time import q,allof
from scripts.shared_conversation import D,OWNERS,CLAIMS,WITHDRAW,CORRECT,BEFORE
from scripts.shared_speech import OCCURS,PRESENTS,CONVEYS
from scripts.shared_answers import matches

OUT=ROOT/'output/visible-conversation-library-v1'
LABELS=('partial-answer','complete-answer','paired-answer','paired-projection','accepted','corrected','withdrawn','linked','claim-truths')
SOURCES={label:'examples/v016/visible-conversation-'+label+'-v1.noema' for label in LABELS}


@lru_cache(maxsize=1)
def vocabulary():return ConversationVocabulary()
@lru_cache(maxsize=1)
def new_names():return tuple(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['spellings'])
def local(parts):return symbol(Word('compound',parts),vocabulary())
def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def eq(a,b):return op('equal',a,b)
def quantify(ps,body):
    for n,t in reversed(ps):body=q('forall',n,t,body)
    return body
def question(function):return dict(kind='question',function=function)
def seq(sort,items):return dict(kind='sequence',element=sort,items=list(items))
def guarded(body):return op('implies',op('not',eq(call('aki'),call('nao'))),body)
def doc(extra=(),body=None,names=()):
    required=set(names)
    def collect(x):
        if isinstance(x,list):
            for y in x:collect(y)
        elif isinstance(x,dict):
            if x.get('kind') in ('call','function_ref') and x['symbol'] in vocabulary()._words:required.add(x['symbol'])
            for y in x.values():collect(y)
    collect(list(extra));collect(body)
    d=vocabulary().decode_names(normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary().imports(required),statements=[])))
    d['declarations']+=list(extra)
    if body is not None:d['statements']=[dict(kind='assert',body=body)]
    return normalize_document(d)


def unary_definitions():
    names=[local(('book','aki',x)) for x in ('aki','nao','book')]
    x=v('candidate');one=eq(x,call('aki'));both=op('or',one,eq(x,call('nao')))
    return names,[definition(n,[('candidate',I)],T,b) for n,b in zip(names,(one,both,truth(False)))]


def pair_definitions():
    names=[local(('book','fruit',x)) for x in ('aki','nao','book')]
    first=v('first');second=v('second')
    one=op('and',eq(first,call('aki')),eq(second,call('aki')))
    both=op('and',eq(first,second),op('or',eq(first,call('aki')),eq(first,call('nao'))))
    return names,[definition(n,[('first',I),('second',I)],T,b) for n,b in zip(names,(one,both,truth(False)))]


def answer_example(label):
    if label in ('partial-answer','complete-answer'):
        (one,both,empty),extra=unary_definitions();query=question(ref(both));p=ref(one);n=ref(empty)
        if label=='partial-answer':
            bodies=[call('answersound',query,p,n),call('answerpartial',query,p,n,truth(False)),
                op('not',call('answercomplete',query,p,n,truth(True))),call('answerunsettled',p,n,call('nao'))]
        else:
            bodies=[call('answercomplete',query,ref(both),n,truth(True)),
                op('not',call('answercomplete',query,ref(both),n,truth(False))),
                call('answerpartial',query,ref(both),n,truth(False)),
                call('answernone',question(n)),call('answercomplete',question(n),n,n,truth(True))]
    else:
        (one,both,empty),extra=pair_definitions();query=question(ref(both));p=ref(one);n=ref(empty)
        if label=='paired-answer':
            bodies=[call('pairanswerpartial',query,p,n,truth(False)),op('not',call('pairanswercomplete',query,p,n,truth(True))),
                call('pairanswercomplete',query,ref(both),n,truth(True)),call('pairanswerunsettled',p,n,call('nao'),call('nao'))]
        else:
            bodies=[matches(call('answerfirstquestion',query),call('aki')),matches(call('answersecondquestion',query),call('nao')),
                op('not',matches(query,call('aki'),call('nao'))),op('not',matches(call('answerafterfirst',query,call('aki')),call('nao'))),
                matches(call('answerbeforesecond',query,call('nao')),call('nao'))]
    return doc(extra,guarded(allof(*bodies)))


def form_names():return [local(('book','town',x)) for x in ('aki','nao')]
def forms():
    (one,both,empty),extra=unary_definitions();query=question(ref(both))
    conditions=[call('answercomplete',query,ref(one),ref(empty),truth(True)),
        call('answerpartial',query,ref(one),ref(empty),truth(False))]
    for name,condition in zip(form_names(),conditions):
        extra.append(definition(name,[('subject',I)],U,dict(kind='message',force='assert',content=dict(kind='content',variable='world',body=condition))))
    return extra
def instance(form):return call('utteranceinstance',quote(ref(form_names()[form])),quote(call('aki')))
INITIAL=(('aki',1),);ADOPTED=INITIAL+(('nao',0),);CORRECTED=INITIAL+(('nao',1),)
def state(entries):return [seq(I,[call(owner) for owner,form in entries]),seq(D,[instance(form) for owner,form in entries])]
def matching(sort,expected):
    ps=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
    return lam(ps,allof(*(eq(v(n),e) for (n,t),e in zip(ps,expected))))


def conversation_example(label):
    extra=forms();context=v('context');ps=[('context',S)]
    if label=='accepted':
        # One Native relation is reused in the four uptake positions. In this
        # fixture the relations hold at every context; time order is checked
        # separately by the linked document.
        receive=local(('book','town','fruit'))
        pnames=('activity','recipient','subject','message','context')
        expected=[call('aki'),call('nao'),call('aki'),quote(ref(form_names()[0]))]
        extra.append(definition(receive,list(zip(pnames,CONVEYS['parameters'])),T,
            allof(*(eq(v(n),value) for n,value in zip(pnames,expected)))))
        occurs=lam([('activity',I),('context',S)],eq(v('activity'),call('aki')))
        presents=lam([('person',I),('activity',I),('context',S)],op('and',eq(v('person'),call('aki')),eq(v('activity'),call('aki'))))
        body=call('commitmentaccepted',*state(INITIAL),*state(ADOPTED),call('aki'),call('aki'),call('nao'),call('aki'),
            quote(ref(form_names()[0])),context,occurs,presents,*([ref(receive)]*4),quote(call('aki')))
    elif label=='corrected':
        expected=[call('nao'),call('aki'),instance(0),instance(1),call('nao'),context]
        body=call('commitmentcorrected',*state(ADOPTED),*state(CORRECTED),call('nao'),instance(0),instance(1),call('aki'),call('nao'),context,matching(CORRECT,expected))
    elif label=='withdrawn':
        expected=[call('nao'),call('nao'),instance(1),call('aki'),context]
        body=call('commitmentwithdrawn',*state(CORRECTED),*state(INITIAL),call('nao'),instance(1),call('nao'),call('aki'),context,matching(WITHDRAW,expected))
    elif label=='linked':
        ps=[('start',S),('middle',S),('end',S)]
        ordering=lam([('first',S),('second',S)],op('or',op('and',eq(v('first'),v('start')),eq(v('second'),v('middle'))),
            op('and',eq(v('first'),v('middle')),eq(v('second'),v('end')))))
        links=[]
        for entries,start,end in ((ADOPTED,'start','middle'),(CORRECTED,'middle','end')):
            links.append(call('conversationlinked',call('aki'),call('aki'),*state(entries),*state(entries),v(start),v(end),ordering))
        distinct=allof(*(op('not',eq(v(a),v(b))) for a,b in [('start','middle'),('start','end'),('middle','end')]))
        body=op('implies',distinct,allof(*links))
    else:
        evaluate=lambda f:dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='disquote',description=instance(f))),situation=context)
        body=op('and',op('not',evaluate(0)),evaluate(1))
    return doc(extra,quantify(ps,guarded(body)))


def native_examples():return [(label,answer_example(label) if label in LABELS[:4] else conversation_example(label)) for label in LABELS]
def model(document):
    known={'aki':lambda:'a','nao':lambda:'b','rationaladd':lambda a,b:a+b}
    return {d['name']:known[vocabulary()._by_symbol[d['name']]] for d in document['declarations'] if d['kind']=='primitive'}


@lru_cache(maxsize=1)
def cases():
    result=[];vocab=vocabulary()
    for label,native in [('dictionary',doc(names=new_names()))]+native_examples():
        encoded=vocab.encode(native);w=PublicWriter(vocab);w.document(encoded)
        page=compile_page(encoded,vocab,max_width=4800.);svg=to_svg(page['shapes'])
        decoded=decode_page(from_svg(svg),vocab)['document']
        if decoded!=encoded or vocab.decode_names(decoded)!=native:raise ValueError('Conversation geometry differs: '+label)
        values=[]
        if label!='dictionary':
            values=evaluate_document(decoded,individuals=('a','b'),situations=('start','middle','end'),primitives=model(decoded),max_steps=1000000)
            if values!=[dict(kind='assert',value=True)]:raise ValueError('Decoded conversation meaning differs: '+label)
        result.append(dict(label=label,native=native,encoded=encoded,page=page,svg=svg,result=values,glyphs=len(w.glyphs)))
    return result


@lru_cache(maxsize=1)
def word_checks():
    rows=[];vocab=vocabulary()
    for name in new_names():
        d=vocab.declaration(name);ps=[('arg'+chr(97+i),p['sort']) for i,p in enumerate(d['parameters'])]
        invocation=call(d['name'],*(v(n) for n,t in ps));body=quantify(ps,eq(invocation,invocation))
        quoted=quote(ref(d['name']))
        if name=='commitmentaccepted':quoted['rank']=1
        native=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocab.imports([name]),
            statements=[dict(kind='assert',body=body),dict(kind='assert',body=eq(quoted,quoted))]))
        w=PublicWriter(vocab);w.document(native);shapes=render(w.glyphs)['shapes']
        if decode_document(from_svg(to_svg(shapes)),vocab)!=native:raise ValueError('Typed conversation call differs: '+name)
        rows.append(dict(name=name,parts=list(vocab.word(name).parts),quotation_rank=quoted.get('rank',0),glyphs=len(w.glyphs),shapes=len(shapes)))
    return rows


def preview():
    from PIL import Image,ImageDraw
    OUT.mkdir(parents=True,exist_ok=True)
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
        canvas.save(OUT/('conversation-forms-'+str(start//10+1)+'.png'))


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    for row in cases():
        if row['label'] in SOURCES:
            target=ROOT/SOURCES[row['label']];text=format_graph(row['native'])+'\n'
            if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published visible conversation differs')
            if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
        (OUT/(row['label']+'.svg')).write_text(row['svg'],encoding='utf-8',newline='\n')
    preview()


def build_report():
    for row in cases():
        if row['label'] in SOURCES and parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))!=row['native']:
            raise ValueError('Published conversation example differs')
    result=dict(schema='noema-visible-conversation-evidence-1',edition=9,words=252,root_words=30,shared_compounds=222,
        shared_definitions=231,shared_primitives=21,new_single_glyphs=0,new_primitive_declarations=0,
        typed_call_shape_decoding=word_checks(),shape_decoding=[dict(label=r['label'],glyphs=r['glyphs'],rows=r['page']['rows'],
            shapes=len(r['page']['shapes']),result=r['result'],svg_sha256=hashlib.sha256(r['svg'].encode()).hexdigest()) for r in cases()])
    preserved=['reports/visible-speech-v1.json','reports/shared-answers-v1.json','reports/shared-conversation-v1.json']
    paths=[MANIFEST,*SOURCES.values(),'scripts/visible_conversation_vocabulary.py','scripts/visible_conversation_page.py',
        'scripts/check_visible_conversation_library.py','tests/test_visible_conversation_library.py','docs/visible-conversation-v1.md',*preserved]
    for spec in LIBRARIES:paths.extend(spec.values())
    for report in preserved:
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend(hashes)
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=['All visible declarations, types, quotes, functions and binders recover from circle/line geometry.',
        'Nine meaning documents form a connected fixture; the history is split into uptake, correction, withdrawal, links and claim truth.',
        'Social grounding is stipulated in Native functions. Uptake conditions hold at every context; the link document explicitly checks a three-point order.',
        'Only existing individual names and rational addition use host interpretations. Two individuals and three situations make distinctness guards satisfiable.',
        'These finite examples do not establish real acceptance, correction, withdrawal or the truth of a real answer.',
        'Typed higher-order and sequence quantification roundtrips test syntax, not exhaustive evaluation of unbounded domains.',
        'No raster OCR or third-party reading. Frozen glyphs and resource limits remain unchanged.']
    return result
