"""Reuse the existing repeat marks for type headers and binder distances."""
from scripts.concept2_codec_v8 import Codec
from scripts.concept2_document import DocumentCodec
from scripts.concept2_fast_reader import FastInkMixin


def repeatable(t):
    return (t[0] in ('root','lig','lig-alt','role-use','word-use','type') or
            t in (('op','quotation-rank'),('op','scope-hop'))) and t!=('root','aki')


def expand_repeats(tokens):
    result=[];previous=None
    for t in tokens:
        if t[0]=='repeat':
            if previous is None or not repeatable(previous) or len(t)!=2 or t[1] not in (2,3,4,5):
                raise ValueError('Invalid repeat target or count')
            result.extend([previous]*(t[1]-1))
        else:result.append(t)
        previous=t
    return result


def compact_runs(tokens):
    tokens=expand_repeats(tokens);result=[];i=0
    while i<len(tokens):
        t=tokens[i];j=i+1
        while repeatable(t) and j<len(tokens) and tokens[j]==t and j-i<5:j+=1
        result.append(t)
        if j-i>1:result.append(('repeat',j-i))
        i=j
    if result and result[-1][0]=='repeat':result.append(('word-end',))
    return result


class CompactNotationMixin:
    def encode(self,plan,*,compress=True,**options):
        tokens=super().encode(plan,compress=False,**options)
        return compact_runs(tokens) if compress else tokens

    def parse(self,tokens,**options):
        return super().parse(expand_repeats(tokens),**options)


class CompactCodec(CompactNotationMixin,FastInkMixin,Codec):pass


class CompactDocumentCodec(CompactNotationMixin,FastInkMixin,DocumentCodec):
    def encode_record(self,record,*,sharing=True):
        return compact_runs(super().encode_record(record,sharing=sharing))
