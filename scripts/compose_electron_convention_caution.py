"""Connect alternative operational definitions and a requirement for careful comparison."""
from scripts.compose_electron_alternative_conventions import *

PARENT=FULL
PARENT_BASIS=BASIS
PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-electron-convention-caution.noema'
CORE='examples/v014/electron-convention-caution-core.noema'
BASIS='data/electron-convention-caution-basis-v1.json'
ANNOTATIONS='data/electron-convention-caution-identifiers-v1.json'
MAP='h['+POINT+'] '+POINT
CHOICES=[('forcemethod','a'),('accelerationmethod','a'),('forcemap',MAP),('accelerationmap',MAP),('alternative','d')]
MAPS=CHOICES[2:4]
RESPONSE=MAPS+OLD+COEFFICIENTS
COMPARISON=[('person','a'),('activity','a'),('left','a'),('right','a'),('context','d')]
DESCRIPTION='i[h[a a] e]'
PRIMITIVES={
 'eiszc':([('method','a'),('selector',code(CONVENTION,POINT))]+CONVENTION+[('map',MAP),('alternative','d')], '同じ物理設定と単位を保った仮定的alternativeで、selectorの元の量にmethodという操作的な定義を採り、その全応答比較域で元の三成分から新しい三成分への評価がmapであるという関係。methodは系・時計・測定作用などにより数量を定める物理的手続きで、所望の質量を得るための任意の曲線当てはめではない。元と同じ定義も許し、差や係数の成立は含めない。'),
 'eiszd':([('method','a'),('selector',code(CONVENTION,POINT))]+CONVENTION+[('alternative','d')], '同じ物理配置についてmethodの操作・測定対象・時空参照の定義がselectorに指定された元の規約と実質的に異なる。名称の違いだけでは成立せず、結果の数値差から定義の差を逆算しない。ある境界で同じ値を与えることは許す。'),
 'eisze':([('scope','a'),('source','d'),('alternative','d')], 'scopeの議論で考慮する、同じ物理条件で規約を採り替える仮定的な比較状況の範囲。状況の選定は議論上の関連性によって結果より先に固定し、係数の差が出る候補だけを事後に集めない。差、存在、全称範囲は合成側で述べる。'),
 'eiszf':([('theory','a'),('law','a'),('context','d')], 'lawがtheoryの体系的な説明・予測内容を構成する法則であるという内容上の所属。単なる文書の引用や名称の一致ではない。理論や法則が真であることを含意しない。'),
 'eiszg':([('activity','a'),('person','a'),('left','a'),('right','a'),('context','d')], 'personがleftとrightの数量・前提・予測の対応や差を検討する比較活動activity。方法上の要求を適用する実行中又は企図された活動を含み、実際の遂行や結論の存在は含意しない。'),
 'eiszh':([('activity','a'),('aspect','a'),('context','d')], 'activityで誤った比較を避けるために検討すべき事項の文脈上の全範囲。数量の定義、解釈、単位、物理事例の同一性等を含み、注意の有無や得られた結果によって都合よく選び直さない。'),
 'eiszi':([('person','a'),('activity','a'),('aspect','a'),('context','d')], 'personが同じactivityのaspectに持続的に注意を向け、その内容と根拠を能動的に吟味・点検している関係。単なる知識の所有、気分、結果の正しさではなく注意深い遂行を指す。'),
 'eiszj':([('person','a'),('activity','a'),('description',DESCRIPTION),('standard','a'),('context','d')], '同じperson/activityでdescriptionが指定する段階的に実現される性質又は手続きの程度が、standardの文脈上通常の基準を大きく上回る。吟味の広さ・深さ・持続などの程度を評価し、固定数値、完全性、成功を要求しない。引用した手続きをこの関係だけで実行しない。'),
}
REFERENCES={'eiszk':'理論比較での注意深い吟味の通常程度を測る当該議論の基準。','eiszl':'u0259前半、別の力・加速度の定義なら別の質量数値になるという箇所。','eiszm':'u0259後半、そこから電子運動の理論比較への強い注意要求を導く箇所。'}
MEANINGS={
 'enp':'同じCONVENTIONから元のkの力三成分を取る射影。',
 'enq':'同じCONVENTIONから元のKの実三加速度を取る射影。',
 'enr':'元の縦横係数を三加速度へ適用した力と、その加速度を、それぞれ指定した操作的再評価mapへ渡し、新しい有効三成分が同じ候補係数の成分式を満たすこと。',
 'ens':'全ての有効な三加速度入力でenrを満たし、新しい加速度には縦及び横の非零応答があるという係数同定。現在の一つの零入力だけで係数を決めず、全入力の実験済みを主張しない。',
 'ent':'同じ物理設定に力と加速度の二操作的規約を選び、少なくとも一方が元と異なり、関連する仮定状況の範囲に入るという選択条件。質量の差を選択条件に埋め込まない。',
 'enu':'同じ元のμβ³,μβ²の応答から二mapで再評価した係数をensで同定し、少なくとも縦横の一方が元と異なるという結論。',
 'env':'動く電子の同じ元のemf設定の下で、entの関連する別定義が非空で、その全てについて異なる二係数の組が得られるという条件文。無制限のあらゆる定義でも、単なる一例の存在でもない。',
 'enw':'同じ固定された電子・二系・出来事・単位を共有する全設定でenvを述べる閉じた前半内容。',
 'enx':'三成分評価を変更しない恒等map。',
 'eny':'三加速度の縦をβ³、横二成分をβ²で再評価するmap。物理的な実現は同じ履歴のenzで別に結ぶ。',
 'enz':'既存enkの同じ両履歴・初期運動式を保持し、enyで元の三加速度から得る値が同じkの実newax/neway/newazであるという具体的な橋渡し。これだけを原文の一般条件文としない。',
 'en2':'議論で選択される体系的な物理理論であり、電子の運動の変化を対象とする法則をその内容として持つこと。法則の真理や特定の力公式を理論の資格へ入れない。',
 'en3':'同じ主体・活動・文脈で異なる二つの電子運動理論を比較することと、既存比較手続きの主体・左右・主題を一致させる。',
 'en4':'同じ比較活動における慎重な手続き。関連する事項が非空で全事項を持続的に吟味し、意味・単位・事例対応を確認する前に数値差だけから不一致を結論しない。唯一の辞書的定義ではなく明示した方法上の読み。',
 'en5':'同じ注意深い手続きen4を行い、その程度が文脈上の通常基準を大きく上回ること。sehrを単なる手続きの有無へ縮めない。',
 'en6':'電子運動の異なる理論を比較する全主体・活動について、同じ主体がen5の手続きを行うべきだという方法上の要求。実際の比較の存在や遵守を主張しない。',
 'en7':'前半enwを著者が明白な条件文として述べ、そこから後半en6の要求を導く提示。前の二質量への照応、前後二句の順序、著者への帰属を保持し、事実から規範を機械的に証明しない。',
 'eoa':'別定義と非常に慎重な比較への要求の全文メッセージ。',
 'eob':'u0259全文を同じ著者・論説へ帰属し、二質量の表示に続ける主張426。',
}
LIMITS=[
 'u0259全文の明示した読み。原文が特定の別規約を列挙したとはしない。関連する操作的定義の全てを非空の文脈範囲で扱い、その範囲は質量差が得られるかを見て選び直さない。係数の存在・差は著者が述べる条件文の後件であり、入力の定義や有限検査で真にしてしまわない。',
 '同じ動く電子、低速質量、電荷、単位、物理配置を保った規約変更と読む。v>0での議論であり、静止境界の同値や補償する再定義もあり得る。全ての想像可能な数学関数の変更が必ず質量を変えるという無制限の主張ではない。',
 '新しい操作的評価は固定された物理配置での元の三成分から新しい三成分へのmapとして明示する。全応答域での係数同定を用い、任意の曲線当てはめ、別電子や別単位への交換、零応答だけでの同定を許さない。kの加速度への変更は同じ実履歴に結ぶ既存の具体例であって原文全体の代用ではない。',
 '慎重さは関連事項への持続的吟味と、意味・単位・同じ事例への対応を確認してから不一致を判定する手続きとして読む。原文が検査項目を列挙したとはせず、sehrはその吟味の程度が通常基準を大きく超えることとして別に保持する。成功、完全性又は必ず結論を出す義務ではない。',
 'manは比較を行う一般の主体。mussは方法上の要求であり現実の遵守ではない。Natürlichは著者による明白さの提示、man ersieht darausは前半から要求への著者の推論提示であり、物理的真理や規範の正当性の証明ではない。',
 '全実数域の係数同定と引用内容の意味は有限診断だけでは証明しない。新しい基本関係は操作的定義の対応・変更、文脈選択、理論の内容所属、比較、注意事項、吟味、程度という一般的役割であり、文全体の真理を原始記号に格納しない。旧426主張と元の意味を保存する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    beta=k('soy',k('tc'),k('eisxt'));square=k('shv',beta,beta);cube=k('shv',square,beta)
    old=[k('shv',v('mass'),cube),k('shv',v('mass'),square)]
    vector=lambda xs:k('ekbe',*xs)
    axes=ROLES[:3]
    text+=define('enp',CONVENTION,v('force'),POINT)+define('enq',CONVENTION,vector(args(ACCEL)),POINT)
    aa=vector(args(ACCEL));ff=vector([k('shv',v(n),v(a)) for n,a in [('oldlongitudinal','ax'),('oldtransverse','ay'),('oldtransverse','az')]])
    na=app(v('accelerationmap'),aa);nf=app(v('forcemap'),ff)
    components=[app(p,k(axis)) for p in (na,nf) for axis in axes]
    text+=define('enr',RESPONSE+ACCEL,both(*(k('ba',x) for x in components),k('seph',*args(COEFFICIENTS),*components)))
    valid=both(*(k('ba',x) for x in args(ACCEL)))
    nonzero=lambda i:op('u',k('sca',app(na,k(axes[i])),ZERO))
    text+=define('ens',RESPONSE,both(*(k('ba',x) for x in args(OLD+COEFFICIENTS)),quantified('f',ACCEL,op('y',valid,k('enr',*args(RESPONSE+ACCEL)))),quantified('g',ACCEL,both(valid,nonzero(0))),quantified('g',ACCEL,both(valid,op('x',nonzero(1),nonzero(2))))))
    methods=[('forcemethod','enp','forcemap'),('accelerationmethod','enq','accelerationmap')]
    chosen=[k('eiszc',v(m),'r[p '+s+']',*args(CONVENTION),v(f),v('alternative')) for m,s,f in methods]
    changed=[k('eiszd',v(m),'r[p '+s+']',*args(CONVENTION),v('alternative')) for m,s,f in methods]
    text+=define('ent',CONVENTION+CHOICES,both(k('eisze',k('eisxg'),v('context'),v('alternative')),*chosen,op('x',*changed)))
    text+=define('enu',CONVENTION+CHOICES+COEFFICIENTS,both(k('ens',*args(MAPS),*old,*args(COEFFICIENTS)),k('enn',*old,*args(COEFFICIENTS))))
    choice=k('ent',*args(CONVENTION+CHOICES))
    text+=define('env',CONVENTION,op('y',both(k('emf',*args(CONVENTION),*old),k('bg',ZERO,k('eisxt'))),both(quantified('g',CHOICES,choice),quantified('f',CHOICES,op('y',choice,quantified('g',COEFFICIENTS,k('enu',*args(CONVENTION+CHOICES+COEFFICIENTS))))))))
    text+=mass_content('enw',k('env',*mass_args()))
    text+=define('enx',[('input',POINT)],v('input'),POINT)
    text+=define('eny',[('input',POINT)],vector([k('shv',factor,app(v('input'),k(axis))) for factor,axis in zip((cube,square,square),axes)]),POINT)
    mapped=k('eny',k('enq',*args(CONVENTION)))
    text+=define('enz',CONVENTION,both(k('enk',*args(CONVENTION)),*(k('sca',app(mapped,k(axis)),v(n)) for axis,n in zip(axes,('newax','neway','newaz')))))
    ctx=v('context');law=v('law');theory=v('theory')
    text+=define('en2',[('theory','a'),('context','d')],both(k('eisvd',theory,k('eirf'),k('eisxg'),ctx),quantified('g',[('law','a')],both(k('vd',law,ctx),k('eisxn',law,k('eisxh'),k('ra'),ctx),k('eiszf',theory,law,ctx)))))
    person,activity,left,right=map(v,('person','activity','left','right'))
    metadata=['actor','left','right','topic'];policy=['cases','concludes','interpretations','meanings','units','corresponds','leftvalue','rightvalue']
    text+=define('en3',COMPARISON,both(k('eiszg',activity,person,left,right,ctx),k('en2',left,ctx),k('en2',right,ctx),op('u',op('e',left,right)),*(op('e',app(k('zrc'+n),activity),x) for n,x in zip(metadata,(person,left,right,k('zrcsubject'))))))
    relevant=k('eiszh',activity,v('aspect'),ctx)
    care=both(quantified('g',[('left','a'),('right','a')],k('en3',*args(COMPARISON))),k('seqm',person,activity,k('zrcsubject'),ctx,*[k('zrc'+n) for n in metadata+policy]),quantified('g',[('aspect','a')],relevant),quantified('f',[('aspect','a')],op('y',relevant,k('eiszi',person,activity,v('aspect'),ctx))))
    text+=define('en4',[('person','a'),('activity','a')],'b context['+care+']','e')
    text+=define('en5',[('person','a'),('activity','a')],'b context['+both(op('t',k('en4',person,activity),ctx),k('eiszj',person,activity,'r[p en4]',k('eiszk'),ctx))+']','e')
    p=v('point');who=k('rd');scope=k('eisxg');paper=k('eirf')
    true=op('e',who,who)
    text+=content('en6',quantified('f',COMPARISON[:-1],op('y',k('en3',*args(COMPARISON[:-1]),p),k('zrcmust',who,person,k('zrcrole'),activity,'r[p en5]',true,p))))
    text+=content('en7',both(k('uh',k('eiszl'),who,quote('enw'),scope,p),k('zdg',k('eiszl'),who,quote('enw'),scope,p),k('eiswm',k('eiszl'),who,k('eisy3'),quote('enb'),paper,p),k('zc',k('eiszm'),who,quote('enw'),quote('en6'),scope,p),k('uh',k('eiszm'),who,quote('en6'),scope,p),k('ue',k('eiszl'),k('eiszm'),p)))
    text+='d eoa[] f[j s[k en7[]]].\n'
    text+=define('eob',[],both(k('eir3',k('eiszl'),who,paper,quote('eoa'),k('ri')),k('ue',k('eisy6'),k('eiszl'),k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==426
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eob',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='alternative_conventions_and_very_careful_comparison',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[426]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
