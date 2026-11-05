"""v4 trunk reading, with a limited backward-ray variant for declared words."""
from copy import deepcopy
from scripts import concept2_geometry_v5 as g
from scripts.concept2_codec_v6 import Codec as PreviousCodec,EXTRA_OPERATORS


class Codec(PreviousCodec):
    def __init__(self,dictionary):
        super().__init__(dictionary)
        self.backward_word_keys=[]
        self.previous_word_forms={}
        for label in range(8):
            token=('word-use',label);old=self.forms[token]
            arcs=[s for s in old['shapes'] if s['kind']=='arc']
            # Use a backward ray only where both identity arcs meet it.
            if not all(any(abs(s['r']-r)<g.EPS and g.on_arc(s,180) for s in arcs) for r in (g.M,g.L)):continue
            # The outgoing edge must meet the rim, not add a second center ray.
            if not any(abs(s['r']-g.M)<g.EPS and g.on_arc(s,0) for s in arcs):continue
            self.previous_word_forms[token]=deepcopy(old)
            shapes=[s for s in arcs if abs(s['r']-g.S)>g.EPS]
            shapes.append(g.line((0,0),(-g.L,0)))
            self.forms[token]=g.unit(token,shapes,fixed=old['fixed'])
            self.backward_word_keys.append(label)
        self._prepare_recognition()

    def encode(self,plan,*,compress=True,branch=True,reference_style='trunk'):
        if reference_style not in ('trunk','confluence'):raise ValueError('Unknown reference style')
        tokens=super().encode(plan,compress=compress,branch=branch)
        if reference_style=='confluence':return tokens
        result=[]
        for token in tokens:
            if token[0] in ('select-directed','merge'):
                lanes=token[1:]
                # Exactly v4's policy: ascending distinct references use the
                # compact selection; other orders and repetitions use the trunk.
                token=('select' if list(lanes)==sorted(set(lanes)) else 'branch',*lanes)
            result.append(token)
        return result
