d ga[radius b x b y b z b] c[
  w[k aa[n p a b v radius]][
    e[k ab[k ad[v x v x] k ab[k ad[v y v y] k ad[v z v z]]]][k ad[v radius v radius]]
  ]
].
d gb[speed b light b beta b radius b time b x b y b z b] c[
  w[k cm[v speed v light v beta]][
    k ga[v radius k ad[v beta k ab[v x k ac[k ad[v speed v time]]]] v y v z]
  ]
].
d gc[beta b radius b x b y b z b] c[
  w[k aa[n p a b v beta]][k ga[v radius k ad[v beta v x] v y v z]]
].
d gd[beta b radius b longitudinal b transversey b transversez b] c[
  w[k aa[n p a b v beta]][w[k aa[n p a b v radius]][w[k aa[n p a b v longitudinal]][
    w[e[k ad[v beta v longitudinal]][v radius]][
      w[e[v transversey][v radius]][e[v transversez][v radius]]
    ]
  ]]]
].
d ge[speed b light b radius b longitudinal b] c[
  w[k aa[n p a b v light]][w[k aa[n p a b v radius]][w[k aa[n p a b v longitudinal]][
    w[k aa[k ad[v speed v speed] k ad[v light v light]]][
      e[k ad[k ad[v light v light] k ad[v longitudinal v longitudinal]]][
        k ad[k ad[v radius v radius] k ab[k ad[v light v light] k ac[k ad[v speed v speed]]]]
      ]
    ]
  ]]]
].
d gg[radius b] h[b b b b] c[i[time b x b y b z b][k ga[v radius v x v y v z]]].
d gh[speed b light b beta b radius b] h[b b b b] c[
  i[time b x b y b z b][k gb[v speed v light v beta v radius v time v x v y v z]]
].
d gi[body h[b b b b] c instant b] h[b b b] c[
  i[x b y b z b][c[v body][v instant v x v y v z]]
].
d gj[body h[b b b b] c] c[
  f first b[f second b[f x b[f y b[f z b[
    z[c[v body][v first v x v y v z]][c[v body][v second v x v y v z]]
  ]]]]]
].
d gl[first a second a frame a context d lengthunit a timeunit a instant b firstx b firsty b firstz b secondx b secondy b secondz b] c[
  w[u[e[v first][v second]]][
    w[k pa[v first v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz]][
      k pa[v second v frame v context v lengthunit v timeunit v instant v secondx v secondy v secondz]
    ]
  ]
].
d gm[body h[a] c first a second a frame a context d lengthunit a timeunit a instant b firstx b firsty b firstz b secondx b secondy b secondz b] c[
  w[c[v body][v first]][w[c[v body][v second]][
    k gl[v first v second v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz v secondx v secondy v secondz]
  ]]
].
d gn[radius h[b] c x h[b] c y h[b] c z h[b] c] c[
  w[k ba[v radius]][w[k ba[v x]][w[k ba[v y]][w[k ba[v z]][
    w[k bg[k bb[n p a b] v radius]][
      e[k bd[k cd[v x v x] k bd[k cd[v y v y] k cd[v z v z]]]][k cd[v radius v radius]]
    ]
  ]]]]
].
d go[speed h[b] c light h[b] c beta h[b] c radius h[b] c time h[b] c x h[b] c y h[b] c z h[b] c] c[
  w[k cl[v speed v light v beta]][w[k ba[v time]][w[k ba[v x]][
    k gn[v radius k cd[v beta k bf[v x k cd[v speed v time]]] v y v z]
  ]]]
].
d gp[beta h[b] c radius h[b] c longitudinal h[b] c transversey h[b] c transversez h[b] c] c[
  w[k ba[v beta]][w[k ba[v radius]][w[k ba[v longitudinal]][w[k ba[v transversey]][w[k ba[v transversez]][
    w[k bg[k bb[n p a b] v beta]][w[k bg[k bb[n p a b] v radius]][w[k bg[k bb[n p a b] v longitudinal]][
      w[e[k cd[v beta v longitudinal]][v radius]][
        w[e[v transversey][v radius]][e[v transversez][v radius]]
      ]
    ]]]
  ]]]]]
].
d gq[event a tube h[b b b b] c frame a context d lengthunit a timeunit a instant b x b y b z b] c[
  w[k pa[v event v frame v context v lengthunit v timeunit v instant v x v y v z]][
    c[v tube][v instant v x v y v z]
  ]
].
d gr[tube h[b b b b] c first a second a frame a context d lengthunit a timeunit a instant b firstx b firsty b firstz b secondx b secondy b secondz b] c[
  w[k gl[v first v second v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz v secondx v secondy v secondz]][
    w[k gq[v first v tube v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz]][
      k gq[v second v tube v frame v context v lengthunit v timeunit v instant v secondx v secondy v secondz]
    ]
  ]
].
d gs[body h[a] c tube h[b b b b] c first a second a frame a context d lengthunit a timeunit a instant b firstx b firsty b firstz b secondx b secondy b secondz b] c[
  w[k gm[v body v first v second v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz v secondx v secondy v secondz]][
    k gr[v tube v first v second v frame v context v lengthunit v timeunit v instant v firstx v firsty v firstz v secondx v secondy v secondz]
  ]
].
