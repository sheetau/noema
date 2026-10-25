"""A public visible grammar for native Noema 0.16 documents.

Only geometric primitives and the shared vocabulary enter the decoder. Native
normalization checks types and alpha-renames bindings; no sentence registry is
consulted and no semantic simplification occurs.
"""
from noema.constructed_discourse import normalize_document
from noema.grammar import number_word
from scripts.visible_lexical_script import _glyph, _shape_set, require
from scripts.visible_word_forms import Word, canonical, symbol, read_symbol, _marker
from scripts.visible_syntax_vocabulary import Vocabulary, FAMILIES, KEYWORDS, family_glyph, modifier_glyph
from scripts.visible_syntax_geometry import render, recognize, to_svg, from_svg
from scripts.balanced_circle_script import SMALL, PITCH, nucleus

MAX_BITS = 256
MAX_DEPTH = 128
END_GLYPH = nucleus(0., PITCH, SMALL, None, mode='none')
END = _shape_set(END_GLYPH['shapes'])
FIXED = {
    'quoted_lift': ('description',), 'evaluate': ('content','situation'),
    'message_content': ('message',), 'question': ('function',),
    'length': ('sequence',), 'position': ('sequence','index','value'),
    'concat': ('left','right'), 'fold': ('sequence','initial','step'),
}
LOGIC = {'not':1, 'and':2, 'or':2, 'implies':2, 'iff':2, 'equal':2}
TYPE_NAMES = {'individual':'individual', 'number':'number', 'truth':'truth',
              'situation':'situation', 'content':'content_type', 'message':'message_type'}
# This native tag is longer than the public table's operation label.
KEYWORD_ALIAS = {'quoted_application':'quoted_apply'}


class Writer:
    def __init__(self, vocabulary):
        self.v = vocabulary
        self.glyphs = []

    def keyword(self, key):
        family, direction = KEYWORDS[KEYWORD_ALIAS.get(key,key)]
        self.glyphs.extend((family_glyph(family), modifier_glyph(direction)))

    def end(self):
        self.glyphs.append(END_GLYPH)

    def natural(self, n):
        require(type(n) is int and 0 <= n < 2**MAX_BITS, 'Natural number exceeds bit budget')
        self.glyphs.extend(modifier_glyph(None if b=='0' else 0) for b in bin(n)[2:])
        self.end()

    def name(self, value):
        word = read_symbol(value,self.v)
        if word.kind != 'root': self.glyphs.append(_marker(word.kind,0.))
        self.glyphs.extend(_glyph(self.v.resolve(p)[1]['form']) for p in word.parts)
        if word.kind != 'root': self.end()

    def type(self, t):
        if isinstance(t,str):
            self.keyword(TYPE_NAMES[t])
            return
        kind = t['kind']
        self.keyword('question' if kind=='question' else kind+'_type')
        if kind in ('function','question'):
            for p in t['parameters']: self.type(p)
            self.end()
        if kind=='description': self.natural(t.get('rank',0))
        if kind=='sequence': self.type(t['element'])
        elif kind!='question': self.type(t['result'])

    def parameters(self, parameters):
        for p in parameters: self.type(p['sort'])
        self.end()

    def expr(self, e, env=()):
        k = e['kind']
        if k=='call':
            word = read_symbol(e['symbol'],self.v)
            if word.kind != 'root': self.keyword('call')
            self.name(e['symbol'])
            for a in e['arguments']: self.expr(a,env)
            if word.kind != 'root': self.end()
            return
        self.keyword(('negative' if e['numerator']<0 else 'nonnegative') if k=='number' else k)
        if k=='number':
            self.natural(abs(e['numerator']))
            self.natural(e['denominator'])
        elif k=='variable':
            require(e['name'] in env, 'Unbound visible variable')
            self.natural(tuple(reversed(env)).index(e['name']))
        elif k in LOGIC:
            for a in e['arguments']: self.expr(a,env)
        elif k in ('forall','exists','content'):
            if k!='content': self.type(e['sort'])
            self.expr(e['body'],env+(e['variable'],))
        elif k in ('quote','disquote'):
            self.natural(e.get('rank',0))
            self.expr(e['body'] if k=='quote' else e['description'], () if k=='quote' else env)
        elif k=='function_ref': self.name(e['symbol'])
        elif k=='lambda':
            self.parameters(e['parameters'])
            self.expr(e['body'],env+tuple(p['name'] for p in e['parameters']))
        elif k in ('apply','quoted_application','answer_matches'):
            self.expr(e['question'] if k=='answer_matches' else e['function'],env)
            for a in e['arguments']: self.expr(a,env)
            self.end()
        elif k=='message':
            self.keyword(e['force'])
            self.expr(e['content'],env)
        elif k=='sequence':
            self.type(e['element'])
            for a in e['items']: self.expr(a,env)
            self.end()
        elif k in FIXED:
            for field in FIXED[k]: self.expr(e[field],env)
        else: raise ValueError('Unsupported native expression: '+str(k))

    def statement(self, s):
        self.keyword(s['kind'])
        if s['kind']=='suppose':
            self.expr(s['condition'])
            for child in s['statements']: self.statement(child)
            self.end()
        else: self.expr(s['body'])

    def document(self, document):
        doc = normalize_document(document)
        require(doc['schema_version']=='0.16', 'Visible grammar version supports Noema 0.16')
        self.keyword('document')
        self.natural(16)
        self.natural(self.v.document()['edition'])
        for d in doc['declarations']:
            word = read_symbol(d['name'],self.v)
            if d['kind']=='primitive':
                require(word.kind=='root' and d==self.v.declaration(word.parts[0]),
                        'Primitive differs from public vocabulary')
                self.keyword('import')
                self.name(d['name'])
            else:
                require(word.kind!='root', 'Definitions need compositional names')
                require(word.kind!='proper' or (d['parameters']==[] and d['result']=='individual'),
                        'Proper names designate individuals')
                self.keyword('definition')
                self.name(d['name'])
                self.parameters(d['parameters'])
                self.type(d['result'])
                self.expr(d['body'],tuple(p['name'] for p in d['parameters']))
        self.end()
        for s in doc['statements']: self.statement(s)
        self.end()
        return doc


class Reader:
    def __init__(self, signatures, vocabulary):
        self.tokens, self.v, self.i, self.serial = signatures, vocabulary, 0, 0
        self.families = {_shape_set(family_glyph(f)['shapes']):f for f in FAMILIES}
        self.modifiers = {_shape_set(modifier_glyph(d)['shapes']):d for d in [None,*range(8)]}
        self.keywords = {pair:key for key,pair in KEYWORDS.items()}
        self.names = {_shape_set(_marker(k,0.)['shapes']):k for k in ('compound','proper')}
        self.roots = {_shape_set(_glyph(e['form'])['shapes']):n
                      for n,e in self.v.document()['entries'].items()}

    def peek(self):
        require(self.i < len(self.tokens), 'Truncated visible syntax')
        return self.tokens[self.i]

    def take(self):
        token = self.peek()
        self.i += 1
        return token

    def end(self):
        require(self.take()==END, 'Expected visible end marker')

    def keyword(self):
        token = self.take()
        require(token in self.families, 'Expected grammar family')
        modifier = self.take()
        require(modifier in self.modifiers, 'Expected grammar modifier')
        pair = self.families[token], self.modifiers[modifier]
        require(pair in self.keywords, 'Unknown grammar operation')
        return self.keywords[pair]

    def natural(self):
        digits = []
        while self.peek()!=END:
            token = self.take()
            require(token in self.modifiers and self.modifiers[token] in (None,0), 'Invalid binary digit')
            digits.append(0 if self.modifiers[token] is None else 1)
            require(len(digits)<=MAX_BITS, 'Natural number exceeds bit budget')
        self.end()
        require(digits and (len(digits)==1 or digits[0]==1), 'Empty or noncanonical natural number')
        n = 0
        for d in digits: n = n*2+d
        return n

    def word(self):
        token = self.take()
        if token in self.roots: return Word('root',(self.roots[token],))
        require(token in self.names, 'Unknown visible name')
        parts = []
        while self.peek()!=END:
            part = self.take()
            require(part in self.roots, 'Unknown word component')
            parts.append(self.roots[part])
        self.end()
        return canonical(Word(self.names[token],tuple(parts)),self.v)

    def fresh(self):
        value = 'v'+number_word(self.serial)
        self.serial += 1
        return value

    def type(self, depth=0):
        require(depth<=MAX_DEPTH, 'Visible sort nesting limit')
        k = self.keyword()
        primitive = {v:n for n,v in TYPE_NAMES.items()}
        if k in primitive: return primitive[k]
        require(k in ('function_type','question','sequence_type','description_type'), 'Expected type')
        if k=='sequence_type': return dict(kind='sequence',element=self.type(depth+1))
        if k=='description_type':
            rank = self.natural()
            return dict(kind='description',result=self.type(depth+1),**({'rank':rank} if rank else {}))
        parameters = []
        while self.peek()!=END: parameters.append(self.type(depth+1))
        self.end()
        if k=='question': return dict(kind='question',parameters=parameters)
        return dict(kind='function',parameters=parameters,result=self.type(depth+1))

    def parameters(self):
        parameters = []
        while self.peek()!=END:
            parameters.append(dict(name=self.fresh(),sort=self.type()))
        self.end()
        return parameters

    def expr(self, env=(), depth=0):
        require(depth<=MAX_DEPTH, 'Visible expression nesting limit')
        def child(inner=env): return self.expr(inner,depth+1)
        if self.peek() in self.roots:
            word = self.word()
            arity = len(self.v.resolve(word.parts[0])[1]['parameters'])
            return dict(kind='call',symbol=symbol(word,self.v),arguments=[child() for _ in range(arity)])
        k = self.keyword()
        if k=='call':
            word = self.word()
            require(word.kind!='root', 'Root calls use their public arity')
            args = []
            while self.peek()!=END: args.append(child())
            self.end()
            return dict(kind='call',symbol=symbol(word,self.v),arguments=args)
        if k in ('nonnegative','negative'):
            n,d = self.natural(),self.natural()
            require(d>0 and (k!='negative' or n!=0), 'Invalid signed rational')
            return dict(kind='number',numerator=(-n if k=='negative' else n),denominator=d)
        if k=='variable':
            distance = self.natural()
            require(distance<len(env), 'Unbound visible variable')
            return dict(kind=k,name=env[-1-distance])
        if k in LOGIC: return dict(kind=k,arguments=[child() for _ in range(LOGIC[k])])
        if k in ('forall','exists','content'):
            t = self.type() if k!='content' else None
            v = self.fresh()
            return dict(kind=k,variable=v,**({'sort':t} if t is not None else {}),body=child(env+(v,)))
        if k in ('quote','disquote'):
            rank = self.natural()
            if k=='quote':
                saved,self.serial = self.serial,0
                try: body=child(())
                finally: self.serial=saved
            else: body=child()
            # Keep explicit zero for disquote until native type checking, so
            # an incorrectly printed rank cannot be silently inferred away.
            annotation = {'rank':rank} if rank or k=='disquote' else {}
            return dict(kind=k,**({'body':body} if k=='quote' else {'description':body}),**annotation)
        if k=='function_ref': return dict(kind=k,symbol=symbol(self.word(),self.v))
        if k=='lambda':
            parameters = self.parameters()
            return dict(kind=k,parameters=parameters,body=child(env+tuple(p['name'] for p in parameters)))
        if k in ('apply','quoted_apply','answer_matches'):
            head,args = child(),[]
            while self.peek()!=END: args.append(child())
            self.end()
            return dict(kind='quoted_application' if k=='quoted_apply' else k,
                        **({'question':head} if k=='answer_matches' else {'function':head}),arguments=args)
        if k=='message':
            force = self.keyword()
            require(force in ('assert','ask','direct'), 'Invalid message force')
            return dict(kind=k,force=force,content=child())
        if k=='sequence':
            t,items = self.type(),[]
            while self.peek()!=END: items.append(child())
            self.end()
            return dict(kind=k,element=t,items=items)
        if k in FIXED: return dict(kind=k,**{field:child() for field in FIXED[k]})
        raise ValueError('Unexpected expression operation: '+k)

    def statement(self, depth=0):
        require(depth<=MAX_DEPTH, 'Visible statement nesting limit')
        self.serial = 0
        k = self.keyword()
        require(k in ('assert','ask','perform','suppose'), 'Expected statement')
        if k=='suppose':
            condition, statements = self.expr(),[]
            while self.peek()!=END: statements.append(self.statement(depth+1))
            self.end()
            return dict(kind=k,condition=condition,statements=statements)
        return dict(kind=k,body=self.expr())

    def document(self):
        require(self.keyword()=='document', 'Missing visible document header')
        require(self.natural()==16, 'Unsupported Noema edition')
        require(self.natural()==self.v.document()['edition'], 'Unknown shared vocabulary edition')
        declarations,statements = [],[]
        while self.peek()!=END:
            k,word = self.keyword(),self.word()
            if k=='import':
                require(word.kind=='root', 'Imports must be shared roots')
                declarations.append(self.v.declaration(word.parts[0]))
            else:
                require(k=='definition' and word.kind!='root', 'Expected definition or import')
                self.serial=0
                parameters = self.parameters()
                result = self.type()
                require(word.kind!='proper' or (parameters==[] and result=='individual'),
                        'Proper names designate individuals')
                body = self.expr(tuple(p['name'] for p in parameters))
                declarations.append(dict(kind='definition',name=symbol(word,self.v),
                                         parameters=parameters,result=result,body=body))
        self.end()
        while self.peek()!=END: statements.append(self.statement())
        self.end()
        require(self.i==len(self.tokens), 'Extra visible syntax after document')
        return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                                       declarations=declarations,statements=statements))


def compile_document(document, vocabulary=None, **layout):
    writer = Writer(vocabulary or Vocabulary())
    writer.document(document)
    return render(writer.glyphs,**layout)


def decode_document(shapes, vocabulary=None):
    return Reader(recognize(shapes),vocabulary or Vocabulary()).document()
