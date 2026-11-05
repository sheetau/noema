"""Reject the legacy optimizer's unpaired-dot candidate, retaining valid sharing.

Successful legacy encodings are byte-for-byte unchanged. Only its specific
candidate-construction failure selects the already checked scope-local planner.
The frozen decoder, geometry, native checks and cache acceptance stay unchanged.
"""
from scripts.concept2_writing import WritingReader
from scripts.concept2_sharing import candidate_plan
from scripts.concept2_document import full_parts
from scripts.concept2_compact import compact_runs
from scripts.kant_type_grammar import type_tokens


class RepairWritingReader(WritingReader):
    def encode_record(self,record,*,sharing=True):
        try:return super().encode_record(record,sharing=sharing)
        except AssertionError as error:
            if str(error)!='Unpaired dot':raise
        record=self.canonical_record(record)
        previous=self._definition_transaction
        self._definition_transaction=record['kind']=='definition'
        try:
            if record['kind']!='definition':
                return self.encode(candidate_plan(record,self.dictionary)['plan'])
            header=[('record','definition'),*self._raw_word(full_parts(record['name']))]
            header.extend(('op','quotation-rank') if t=='quote_raise' else ('type',t) for t in type_tokens(record['result']))
            value=dict(kind='lambda',parameters=record['parameters'],body=record['body'])
            plan=candidate_plan(value,self.dictionary)['plan']
            return compact_runs(header+self.encode(plan,expression=True))
        finally:self._definition_transaction=previous


def main():
    from scripts import two_work_batch as batch,two_work_run as runner
    from scripts.two_work_inventory import sha
    original=runner.checked_pins
    def pins():
        result=original();path='scripts/two_work_repair.py';result[path]=sha(path);return result
    # The cache identity continues to describe the unchanged renderer/decoder.
    # process_records recomputes tokens with this producer before every lookup;
    # changed plans therefore cannot reuse a different ink/tape pair.
    batch.WritingReader=RepairWritingReader
    runner.checked_pins=pins
    runner.main()


if __name__=='__main__':main()
