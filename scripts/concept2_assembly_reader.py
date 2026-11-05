"""The accepted alphabet, with a scoped header for arbitrary branch values."""
from scripts.concept2_codec_v9 import Codec
from scripts.concept2_compact import CompactNotationMixin
from scripts.concept2_fast_reader import FastInkMixin
from scripts.concept2_document_reader import DocumentReader


class AssemblyCodec(CompactNotationMixin,FastInkMixin,Codec):pass


class AssemblyDocumentReader(DocumentReader,Codec):pass
