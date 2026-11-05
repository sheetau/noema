"""Document entry point, including a circular end after a type repeat."""
from scripts.concept2_compact import CompactDocumentCodec


class DocumentReader(CompactDocumentCodec):
    def parse(self,tokens,**options):
        # A primitive's result can end in repeated type-list closures (nested
        # question types). The writer adds a circle because a record cannot end
        # in a bare vertical repeat stroke. A spelling's own word-end is mandatory
        # and must never be stripped by this rule.
        if (len(tokens)>=3 and tokens[0]==('record','primitive') and
                tokens[-1]==('word-end',) and tokens[-2][0]=='repeat'):
            tokens=tokens[:-1]
        return super().parse(tokens,**options)
