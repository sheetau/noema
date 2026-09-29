d da[] h[a] b[i[axis a][n p a b]].
d db[left h[a] b right h[a] b] h[a] b[i[axis a][k ab[c[v left][v axis] c[v right][v axis]]]].
d dc[dimension h[a] b] h[a] b[i[axis a][k ac[c[v dimension][v axis]]]].
d dd[left h[a] b right h[a] b] h[a] b[k db[v left k dc[v right]]].
d de[dimension h[a] b power b] h[a] b[i[axis a][k ad[c[v dimension][v axis] v power]]].
d df[left h[a] b right h[a] b] c[f axis a[e[c[v left][v axis]][c[v right][v axis]]]].
d dg[dimension h[a] b] c[k df[v dimension k da[]]].
d dh[basis a dimension h[a] b] c[
  f axis a[w[y[e[v axis][v basis]][e[c[v dimension][v axis]][n p b b]]][
    y[u[e[v axis][v basis]]][e[c[v dimension][v axis]][n p a b]]
  ]]
].
d di[leftkind a rightkind a leftdim h[a] b rightdim h[a] b leftscale b rightscale b] c[
  w[e[v leftkind][v rightkind]][w[k df[v leftdim v rightdim]][w[k aa[n p a b v leftscale]][k aa[n p a b v rightscale]]]]
].
d dj[leftkind a rightkind a leftdim h[a] b rightdim h[a] b leftscale b rightscale b left b right b] c[
  w[k di[v leftkind v rightkind v leftdim v rightdim v leftscale v rightscale]][
    e[k ad[v leftscale v left]][k ad[v rightscale v right]]
  ]
].
d dk[leftkind a rightkind a leftdim h[a] b rightdim h[a] b leftscale b rightscale b left h[b] c right h[b] c] c[
  w[k di[v leftkind v rightkind v leftdim v rightdim v leftscale v rightscale]][
    w[k ba[v left]][w[k ba[v right]][e[k bj[v leftscale v left]][k bj[v rightscale v right]]]]
  ]
].
d ds[first b second b third b] c[w[k aa[n p a b v first]][w[k aa[n p a b v second]][k aa[n p a b v third]]]].
d dl[leftdim h[a] b rightdim h[a] b resultdim h[a] b leftscale b rightscale b resultscale b left b right b result b] c[
  w[k ds[v leftscale v rightscale v resultscale]][w[k df[v resultdim k db[v leftdim v rightdim]]][
    e[k ad[v resultscale v result]][k ad[k ad[v leftscale v left] k ad[v rightscale v right]]]
  ]]
].
d dm[leftdim h[a] b rightdim h[a] b resultdim h[a] b leftscale b rightscale b resultscale b left b right b result b] c[
  w[k ds[v leftscale v rightscale v resultscale]][w[u[e[v right][n p a b]]][
    w[k df[v resultdim k dd[v leftdim v rightdim]]][
      e[k ad[k ad[v resultscale v result] k ad[v rightscale v right]]][k ad[v leftscale v left]]
    ]
  ]]
].
d dn[lengthaxis a timeaxis a speedkind a lightkind a lengthdim h[a] b timedim h[a] b speeddim h[a] b lightdim h[a] b factordim h[a] b] c[
  w[u[e[v lengthaxis][v timeaxis]]][w[e[v speedkind][v lightkind]][
    w[k dh[v lengthaxis v lengthdim]][w[k dh[v timeaxis v timedim]][
      w[k df[v speeddim k dd[v lengthdim v timedim]]][w[k df[v lightdim k dd[v lengthdim v timedim]]][k dg[v factordim]]]
    ]]
  ]]
].
d dp[speedscale b lightscale b factorscale b speed b light b factor b] c[
  w[k ds[v speedscale v lightscale v factorscale]][k cm[k ad[v speedscale v speed] k ad[v lightscale v light] k ad[v factorscale v factor]]]
].
d do[lengthaxis a timeaxis a speedkind a lightkind a lengthdim h[a] b timedim h[a] b speeddim h[a] b lightdim h[a] b factordim h[a] b speedscale b lightscale b factorscale b speed b light b factor b] c[
  w[k dn[v lengthaxis v timeaxis v speedkind v lightkind v lengthdim v timedim v speeddim v lightdim v factordim]][
    k dp[v speedscale v lightscale v factorscale v speed v light v factor]
  ]
].
d dq[lengthaxis a timeaxis a speedkind a lightkind a lengthdim h[a] b timedim h[a] b speeddim h[a] b lightdim h[a] b factordim h[a] b speedscale b lightscale b factorscale b speed h[b] c light h[b] c factor h[b] c] c[
  w[k dn[v lengthaxis v timeaxis v speedkind v lightkind v lengthdim v timedim v speeddim v lightdim v factordim]][
    w[k ds[v speedscale v lightscale v factorscale]][
      k cl[k bj[v speedscale v speed] k bj[v lightscale v light] k bj[v factorscale v factor]]
    ]
  ]
].
