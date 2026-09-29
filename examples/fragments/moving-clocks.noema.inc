d ha[speed b light b rate b] c[
  w[k aa[n p a b v light]][w[k aa[n p a b v rate]][
    w[k aa[k ad[v speed v speed] k ad[v light v light]]][
      e[k ad[k ad[v light v light] k ad[v rate v rate]]][k ab[k ad[v light v light] k ac[k ad[v speed v speed]]]]
    ]
  ]]
].
d hb[speed b light b beta b rate b] c[
  w[k cm[v speed v light v beta]][e[k ad[v beta v rate]][n p b b]]
].
d hc[speed b light b beta b time b proper b] c[
  k fh[v speed v light v beta v time k ad[v speed v time] n p a b n p a b v proper n p a b n p a b n p a b]
].
d hd[speed b light b beta b first b firstproper b last b lastproper b] c[
  w[k aa[v first v last]][
    w[k hc[v speed v light v beta v first v firstproper]][k hc[v speed v light v beta v last v lastproper]]
  ]
].
d he[speed b light b rate b duration b elapsed b lost b] c[
  w[k ha[v speed v light v rate]][w[u[k aa[v duration n p a b]]][
    w[e[v elapsed][k ad[v rate v duration]]][e[v lost][k ab[v duration k ac[v elapsed]]]]
  ]]
].
d hf[rate b lag b] c[
  w[k aa[n p a b v rate]][w[u[k aa[n p b b v rate]]][e[v lag][k ab[n p b b k ac[v rate]]]]]
].
d hg[squaredratio b rate b lag b approximation b error b] c[
  w[u[k aa[v squaredratio n p a b]]][w[k aa[v squaredratio n p b b]][w[k aa[n p a b v rate]][
    w[e[k ad[v rate v rate]][k ab[n p b b k ac[v squaredratio]]]][
      w[k hf[v rate v lag]][
        w[e[k ad[n p c b v approximation]][v squaredratio]][e[v error][k ab[v lag k ac[v approximation]]]]
      ]
    ]
  ]]]
].
d hh[speed b light b squaredratio b] c[
  w[k aa[n p a b v light]][w[k aa[k ad[v speed v speed] k ad[v light v light]]][
    e[k ad[k ad[v light v light] v squaredratio]][k ad[v speed v speed]]
  ]]
].
d hi[speed b light b squaredratio b rate b lag b approximation b error b] c[
  w[k hh[v speed v light v squaredratio]][k hg[v squaredratio v rate v lag v approximation v error]]
].
d hj[speed b light b squaredratio b rate b lag b approximation b error b duration b elapsed b lost b approximatelost b errorlost b] c[
  w[k hi[v speed v light v squaredratio v rate v lag v approximation v error]][
    w[k he[v speed v light v rate v duration v elapsed v lost]][
      w[e[v approximatelost][k ad[v duration v approximation]]][e[v errorlost][k ad[v duration v error]]]
    ]
  ]
].
d hk[scale b offset b coordinate b reading b] c[
  w[k aa[n p a b v scale]][e[v reading][k ab[k ad[v scale v coordinate] v offset]]]
].
d hl[speed h[b] c light h[b] c beta h[b] c rate h[b] c] c[
  w[k cl[v speed v light v beta]][k ch[v beta v rate]]
].
d hm[rate h[b] c duration h[b] c elapsed h[b] c lost h[b] c] c[
  w[k ba[v rate]][w[k ba[v duration]][w[k ba[v elapsed]][w[k ba[v lost]][
    w[k bg[k bb[n p a b] v rate]][w[k bc[v rate k bb[n p b b]]][w[k ca[v duration]][
      w[e[v elapsed][k cd[v rate v duration]]][e[v lost][k bf[v duration v elapsed]]]
    ]]]
  ]]]]
].
