"""Preserved contextual attention-value and noteworthiness conventions."""
CONTRACTS={'contextualattentionvalue': {'parameters': [{'kind': 'description', 'result': 'content'}, 'situation'],
                              'result': 'number',
                              'arguments': ['subject', 'context'],
                              'meaning_ja': '記述された事柄へ注意を向ける価値の文脈的な評価値。内容の真理値や驚きの度合いとは区別する。'},
 'contextualnoteworthiness': {'parameters': ['number', 'situation'],
                              'result': 'truth',
                              'arguments': ['degree', 'context'],
                              'meaning_ja': '注意を向ける価値が、その文脈で注目に値する基準に入るという条件。著者の評価を全読者共通の尺度にはしない。'}}
SOURCE_RELATIONS={'zld': 'contextualattentionvalue', 'zle': 'contextualnoteworthiness'}
