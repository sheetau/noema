"""Actual action occurrence, distinct from its roles or consequences."""
CONTRACTS={'actionoccurrence': {'parameters': ['individual', 'situation'],
                      'result': 'truth',
                      'arguments': ['act', 'context'],
                      'meaning_ja': 'この文脈で、その行為が実際に生じる。行為の構成員や結果の因果的な説明は別条件である。'}}
SOURCE_RELATIONS={'dg':{'public':'actionoccurrence','source':'kant-1784'}}
EXTRA={}
MATH_ALIASES={}
