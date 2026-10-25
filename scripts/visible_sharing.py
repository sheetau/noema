"""Visible lexical sharing expands to native syntax, never to evaluated values."""
from collections import Counter
from copy import deepcopy
import json

from scripts.visible_syntax import Writer,Reader,MAX_DEPTH
from scripts.visible_syntax_geometry import render,recognize,to_svg,from_svg
from scripts.visible_syntax_vocabulary import Vocabulary,family_glyph,modifier_glyph
from scripts.visible_lexical_script import _shape_set,require

SHARING={'share':('application',1),'reuse':('application',3)}
MAX_EXPANDED_NODES=8192


def key(expr): return json.dumps(expr,sort_keys=True,separators=(',',':'))


def nodes(value):
    if isinstance(value,dict): return (1 if 'kind' in value else 0)+sum(nodes(v) for v in value.values())
    if isinstance(value,list): return sum(nodes(v) for v in value)
    return 0


def children(expr):
    if expr['kind']=='quote': return []
    fields=('body','content','situation','description','function','question','message',
            'sequence','index','value','initial','step','left','right')
    return [*expr.get('arguments',[]),*expr.get('items',[]),
            *(expr[f] for f in fields if f in expr)]


def free_variables(expr,bound=frozenset()):
    k=expr['kind']
    if k=='quote': return set()
    if k=='variable': return set() if expr['name'] in bound else {expr['name']}
    inner=bound
    if k in ('forall','exists','content'): inner=bound|{expr['variable']}
    elif k=='lambda': inner=bound|{p['name'] for p in expr['parameters']}
    return set().union(*(free_variables(c,inner) for c in children(expr)))


class SharedWriter(Writer):
    def __init__(self,vocabulary,*,automatic=True):
        super().__init__(vocabulary)
        self.shared=[]
        self.uses=[]
        self.automatic=automatic
        self.share_count=0

    def document(self,document):
        normalized=super().document(document)
        require(nodes(normalized)<=MAX_EXPANDED_NODES,'Expanded document exceeds node budget')
        return normalized

    def keyword(self,k):
        if k not in SHARING: return super().keyword(k)
        family,direction=SHARING[k]
        self.glyphs.extend((family_glyph(family),modifier_glyph(direction)))

    def cost(self,expr,env):
        w=Writer(self.v); w.expr(expr,env)
        return len(w.glyphs)

    def candidate(self,expr,env):
        counts,values=Counter(),{}
        def visit(e):
            k=key(e)
            if free_variables(e)<=set(env) and k not in self.shared:
                counts[k]+=1; values[k]=e
            for c in children(e): visit(c)
        for c in children(expr): visit(c)
        options=[]
        for k,count in counts.items():
            if count<2: continue
            cost=self.cost(values[k],env)
            # Innermost reference is two operation glyphs plus 0 and its end.
            saving=count*(cost-4)-(2+cost)
            if saving>0: options.append((saving,cost,k))
        return values[max(options)[2]] if options else None

    def expr(self,e,env=()):
        k=key(e)
        if k in self.shared:
            distance=list(reversed(self.shared)).index(k)
            self.uses[-1-distance]+=1
            self.keyword('reuse'); self.natural(distance)
            return
        if e['kind']=='quote':
            saved,self.shared=self.shared,[]
            saved_uses,self.uses=self.uses,[]
            try: super().expr(e,env)
            finally: self.shared,self.uses=saved,saved_uses
            return
        candidate=self.candidate(e,env) if self.automatic else None
        if candidate is None: return super().expr(e,env)
        start,prior_uses,prior_count=len(self.glyphs),list(self.uses),self.share_count
        self.keyword('share')
        self.expr(candidate,env)
        self.shared.append(key(candidate)); self.uses.append(0); self.share_count+=1
        try: super().expr(e,env)
        finally:
            self.shared.pop()
            uses=self.uses.pop()
        # A nested common expression can remove most literal occurrences of
        # an outer one. Compare the actual emitted spelling, including every
        # reference, and retain only bindings still used at least twice.
        plain=SharedWriter(self.v,automatic=False)
        plain.shared=list(self.shared); plain.uses=[0]*len(self.shared)
        plain.expr(e,env)
        if uses<2 or len(self.glyphs)-start>=len(plain.glyphs):
            self.glyphs[start:]=plain.glyphs
            self.uses[:]=[a+b for a,b in zip(prior_uses,plain.uses)]
            self.share_count=prior_count


class SharedReader(Reader):
    def __init__(self,signatures,vocabulary):
        super().__init__(signatures,vocabulary)
        self.keywords.update({pair:name for name,pair in SHARING.items()})
        self.special={tuple((_shape_set(family_glyph(f)['shapes']),
                            _shape_set(modifier_glyph(d)['shapes']))):n for n,(f,d) in SHARING.items()}
        self.quote_prefix=(_shape_set(family_glyph('quotation')['shapes']),
                           _shape_set(modifier_glyph(0)['shapes']))
        self.shared=[]
        self.expansion_work=0

    def expr(self,env=(),depth=0):
        require(depth<=MAX_DEPTH,'Visible expression nesting limit')
        prefix=tuple(self.tokens[self.i:self.i+2])
        operation=self.special.get(prefix)
        if operation=='share':
            self.keyword()
            value=self.expr(env,depth+1)
            require(free_variables(value)<=set(env),'Shared expression captures an unavailable variable')
            entry=dict(value=value,free=free_variables(value),uses=0)
            self.shared.append(entry)
            try: body=self.expr(env,depth+1)
            finally: self.shared.pop()
            require(entry['uses']>=2,'Shared expression must have at least two references')
            return body
        if operation=='reuse':
            self.keyword(); distance=self.natural()
            require(distance<len(self.shared),'Unbound shared reference')
            entry=self.shared[-1-distance]
            require(entry['free']<=set(env),'Shared reference escapes its binding scope')
            self.expansion_work+=nodes(entry['value'])
            require(self.expansion_work<=MAX_EXPANDED_NODES,'Shared expansion exceeds node budget')
            entry['uses']+=1
            return deepcopy(entry['value'])
        if prefix==self.quote_prefix:
            saved,self.shared=self.shared,[]
            try: return super().expr(env,depth)
            finally: self.shared=saved
        return super().expr(env,depth)

    def document(self):
        document=super().document()
        require(nodes(document)<=MAX_EXPANDED_NODES,'Expanded document exceeds node budget')
        return document


def compile_document(document,vocabulary=None,**layout):
    w=SharedWriter(vocabulary or Vocabulary()); w.document(document)
    return render(w.glyphs,**layout)


def decode_document(shapes,vocabulary=None):
    return SharedReader(recognize(shapes),vocabulary or Vocabulary()).document()
