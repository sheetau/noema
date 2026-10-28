"""Practical goal and convenience assessment with explicit state descriptions."""
CONTRACTS={'practicalgoalattainment': {'parameters': ['individual', 'situation'],
                             'result': 'truth',
                             'arguments': ['person', 'scene'],
                             'meaning_ja': 'その人について、この仮定例で問題となる実用上の目的が満たされる。本人の思考・努力を目的達成の定義に織り込まない。対象の目的は解釈の前提として明示する。'},
 'contextualconvenienceburden': {'parameters': ['number', 'situation'],
                                 'result': 'truth',
                                 'arguments': ['burden', 'context'],
                                 'meaning_ja': 'この文脈で、本人の負担が「これほど便利」と評価する水準に収まるという基準。特定の数値、単位、別の状態との優劣を原文へ補わない。'},
 'convenienceassessmentperson': {'parameters': ['individual', 'situation'],
                                 'result': 'truth',
                                 'arguments': ['person', 'context'],
                                 'meaning_ja': '便宜さについての一般的な評価をこの文脈で適用する人物の範囲。全人類を無条件に全称化せず、評価する範囲は明示した解釈の前提とする。'}}
SOURCE_RELATIONS={'sj': {'public': 'practicalgoalattainment', 'source': 'kant-1784'},
 'uk': {'public': 'contextualconvenienceburden', 'source': 'kant-1784'},
 'um': {'public': 'convenienceassessmentperson', 'source': 'kant-1784'}}
EXTRA={'stateconveniencecandidate': {'parameters': ['individual',
                                              {'kind': 'description',
                                               'result': {'kind': 'function',
                                                          'parameters': ['individual'],
                                                          'result': 'content'}},
                                              'situation',
                                              'situation'],
                               'result': 'truth',
                               'arguments': ['person', 'state_description', 'context', 'case'],
                               'meaning_ja': '指定した状態の性質記述について、その状態にある場合の便宜さを評価するため、同じ本人と基準文脈で採用する仮定状況。対象の状態は閉じた性質記述で指定し、別の状態の候補へ自動的に交換しない。候補への採用だけでは記述された状態や目的の成立、低負担を認定せず、引用記述を実行しない。現実の履歴や別の評価の範囲とは区別し、未知の採用関係は補わない。'}}
MATH_ALIASES={}
SPECIALIZATIONS={'uj': {'public': 'stateconveniencecandidate',
        'property': 'bf',
        'parameters': ['individual', 'situation', 'situation'],
        'result': 'truth',
        'arguments': ['person', 'context', 'case'],
        'meaning_ja': '未成熟の状態にある場合の便宜さを評価するため、その本人と文脈について採用する仮定状況。現実の履歴や、前後の文の評価範囲を自動的に同一視しない。',
        'interpretation': '源ujの状態指定を、既存bfの閉じた性質記述を固定する合成で保持する。状態の成立そのものはrj/rk/ulで要求する。'}}
