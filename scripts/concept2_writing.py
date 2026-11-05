"""Unified document entry: accepted glyphs, scoped sharing and branch frames.

Definitions are checked as native declarations at their actual depth. The
expression codec's temporary lambda/equality wrapper is not a source node and
must not consume the document's depth budget. Its redundant check is deferred
only inside a declaration transaction, which always validates before returning.
"""
from copy import deepcopy
from noema.constructed_discourse import normalize_document
from scripts.concept2_codec_v9 import Codec
from scripts.concept2_shared_document import SharedDocumentReader
from scripts.concept2_document import empty_document,full_parts,references,signature


class WritingReader(SharedDocumentReader,Codec):
    _definition_transaction=False

    def _check_quote_ranks(self,value):
        if isinstance(value,list):
            for v in value:self._check_quote_ranks(v)
        elif isinstance(value,dict):
            if value.get('kind')=='quote' and self.evaluation_requirement(value['body'])>value.get('rank',0):
                raise ValueError('Quoted evaluation must target lower ranks, including referenced definitions')
            for v in value.values():self._check_quote_ranks(v)

    def canonical_record(self,record):
        if record.get('kind')!='definition':return super().canonical_record(record)
        if self.document['statements']:raise ValueError('Declaration follows a statement')
        name=record['name'];parts=tuple(full_parts(name));deps=references(record)
        if name in self.declarations or parts in self.aliases:raise ValueError('Duplicate declaration or reserved spelling')
        if deps-set(self.declarations):raise ValueError('Unknown, forward, or recursive declaration reference')
        self._check_quote_ranks(record)
        document=dict(empty_document(),declarations=[signature(self.declarations[n]) for n in sorted(deps)]+[record])
        return normalize_document(document)['declarations'][-1]

    def validate_native(self,statement):
        body=statement.get('body',{})
        args=body.get('arguments',[])
        if (self._definition_transaction and statement.get('kind')=='assert' and body.get('kind')=='equal'
                and len(args)==2 and args[0]==args[1] and args[0].get('kind')=='lambda'):
            return deepcopy(statement)
        return super().validate_native(statement)

    def encode_record(self,record,*,sharing=True):
        previous=self._definition_transaction
        self._definition_transaction=record.get('kind')=='definition'
        try:return super().encode_record(record,sharing=sharing)
        finally:self._definition_transaction=previous

    def parse(self,tokens,**options):
        previous=self._definition_transaction
        self._definition_transaction=bool(tokens and tokens[0]==('record','definition'))
        try:return super().parse(tokens,**options)
        finally:self._definition_transaction=previous
