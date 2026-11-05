"""Document writer using scope-local expression sharing; reading is unchanged."""
from scripts.concept2_document_reader import DocumentReader
from scripts.concept2_document import full_parts
from scripts.concept2_compact import compact_runs
from scripts.concept2_sharing import choose_plan
from scripts.kant_type_grammar import type_tokens


class SharedDocumentReader(DocumentReader):
    def encode_record(self,record,*,sharing=True):
        if not sharing or record['kind'] in ('primitive','spelling'):
            return super().encode_record(record,sharing=sharing)
        record=self.canonical_record(record)
        if record['kind']!='definition':
            return self.encode(choose_plan(record,self)['plan'])
        header=[('record','definition'),*self._raw_word(full_parts(record['name']))]
        header.extend(('op','quotation-rank') if t=='quote_raise' else ('type',t) for t in type_tokens(record['result']))
        value=dict(kind='lambda',parameters=record['parameters'],body=record['body'])
        plan=choose_plan(value,self,expression=True)['plan']
        return compact_runs(header+self.encode(plan,expression=True))
