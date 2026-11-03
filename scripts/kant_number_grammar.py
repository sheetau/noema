"""Canonical signed rationals in a delimited, geometry-defined numeral mode."""
from functools import lru_cache
from math import gcd

START_TOKENS=frozenset(('number_positive','number_negative'))
END='bound0'
MAX_DIGITS=128


@lru_cache(maxsize=1)
def components():
    # Resolve the nine single-medium shapes by geometry, never by a word's
    # dictionary position. Their ordinary lexical readings remain unchanged.
    from scripts import kant_public_fragment as p
    def token(shapes):
        geometry=p.read_geometry(shapes)
        return p.table()[p.feature(geometry,range(len(geometry['circles'])))]
    digits=tuple(token(p.nucleus(0,p.PITCH,p.MEDIUM,None,d,
        mode='none' if d is None else 'radius')['shapes']) for d in (None,*range(8)))
    separator=token([p.circle(0,p.PITCH,p.MEDIUM),p.circle(0,p.PITCH,p.SMALL)])
    return digits,separator


def number_tokens(node):
    if not isinstance(node,dict) or set(node)!={'kind','numerator','denominator'} or node['kind']!='number':
        raise ValueError('Expected a native number')
    a,b=node['numerator'],node['denominator']
    if type(a) is not int or type(b) is not int or b<=0 or gcd(abs(a),b)!=1:
        raise ValueError('Number must be a canonical rational')
    digits,separator=components()
    def unsigned(value):
        result=[]
        while True:
            value,remainder=divmod(value,9);result.append(digits[remainder])
            if not value:break
            if len(result)>=MAX_DIGITS:raise ValueError('Numeral exceeds digit resource limit')
        return result[::-1]
    return [('number_negative' if a<0 else 'number_positive'),*unsigned(abs(a)),
        *([separator,*unsigned(b)] if b!=1 else []),END]


def read_number(start,take):
    if start not in START_TOKENS:raise ValueError('Expected a numeral start')
    digits,separator=components();values={token:i for i,token in enumerate(digits)}
    def unsigned():
        value=0;count=0;zero=False
        while True:
            token=take()
            if token not in values:
                if not count:raise ValueError('Numeral requires a digit')
                return value,token
            if count and zero:raise ValueError('Leading zero in numeral')
            count+=1
            if count>MAX_DIGITS:raise ValueError('Numeral exceeds digit resource limit')
            digit=values[token];zero=count==1 and digit==0
            value=value*9+digit
    a,stop=unsigned();b=1
    if stop==separator:
        b,stop=unsigned()
        if b<2 or gcd(a,b)!=1:raise ValueError('Fraction must have a reduced denominator greater than one')
    if stop!=END:raise ValueError('Expected numeral end')
    if start=='number_negative':
        if a==0:raise ValueError('Negative zero is not canonical')
        a=-a
    return dict(kind='number',numerator=a,denominator=b)
