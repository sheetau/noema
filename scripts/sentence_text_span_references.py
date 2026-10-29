"""Exact spans in fixed sentence transcriptions, counted as Unicode scalars."""
from fractions import Fraction


class SentenceTextSpanReferences:
    def __init__(self,texts,spans):
        self.texts=dict(texts)
        for key,text in self.texts.items():
            if not isinstance(key,tuple) or len(key)!=3 or not isinstance(text,str):
                raise ValueError('Invalid fixed sentence transcription')
            if any(0xD800<=ord(char)<=0xDFFF for char in text):
                raise ValueError('Sentence transcription must contain Unicode scalars')
        self.spans={}
        for key,target in spans.items():
            if not isinstance(key,tuple) or len(key)!=5:
                raise ValueError('Invalid sentence text span binding')
            normalized=self._key(*key)
            if normalized in self.spans and self.spans[normalized]!=target:
                raise ValueError('Conflicting sentence text span binding')
            self.spans[normalized]=target

    @staticmethod
    def _integer(value):
        if isinstance(value,bool) or not isinstance(value,(int,Fraction)) or value!=int(value):
            raise ValueError('Sentence character boundary must be an integer')
        return int(value)

    def _key(self,document,sentence,first,past_last,presentation):
        first=self._integer(first);past_last=self._integer(past_last)
        key=(document,sentence,presentation)
        if key not in self.texts:
            raise ValueError('Unknown fixed sentence transcription')
        if not 0<=first<past_last<=len(self.texts[key]):
            raise ValueError('Sentence character span is empty, reversed or outside the text')
        return document,sentence,first,past_last,presentation

    def span(self,document,sentence,first,past_last,presentation):
        key=self._key(document,sentence,first,past_last,presentation)
        if key not in self.spans:
            raise ValueError('Unknown sentence text span')
        return self.spans[key]

    def handlers(self):return dict(sentencetextspanreference=self.span)
