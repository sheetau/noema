r ca[a a d] c.
r cb[a a a d] c.
r cc[a a d] c.
r cd[a d] c.
r ce[a d] c.
r cf[a a d] c.
r cg[a a d] c.
d da[person a activity a role a now d] c[
  w[k ca[v person v activity v now]][
    w[k cb[v person v activity v role v now]][
      w[k cd[v role v now]][g audience a[w[k cc[v activity v audience v now]][k ce[v audience v now]]]]
    ]
  ]
].
d db[person a activity a role a now d] c[
  w[k ca[v person v activity v now]][
    w[k cb[v person v activity v role v now]][k cf[v person v role v now]]
  ]
].
d dc[person a activity a] e[b scene[k cg[v person v activity v scene]]].
d dd[regime a person a role a] e[
  b scene[f activity a[y[k da[v person v activity v role v scene]][
    k bf[v regime v person v role k dc[v person v activity] v scene]
  ]]]
].
d de[regime a person a role a] e[
  b scene[g activity a[w[k db[v person v activity v role v scene]][
    k bb[v regime v person v role k dc[v person v activity] v scene]
  ]]]
].
d df[assessor a regulator a office a regime a person a role a now d] c[
  k aa[v assessor v regulator v office k dd[v regime v person v role] v now]
].
d dg[assessor a regulator a office a regime a person a role a now d] c[
  k ab[v assessor v regulator v office k de[v regime v person v role] v now]
].
d dh[assessor a regulator a office a regime a person a role a] c[
  f scene d[k df[v assessor v regulator v office v regime v person v role v scene]]
].
