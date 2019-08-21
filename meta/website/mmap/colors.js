var cmap_z = [{"label" :  " < -2.5 &sigma;", "upper" : -2.5, "text" : "black", "fill" : '#440154'},
              {"label" : "-2.5 &mdash; -2 &sigma;", "upper" : -2, "text" : "black", "fill" : '#482172'},
              {"label" : "-2 &mdash; -1.5 &sigma;", "upper" : -1.5, "text" : "white", "fill" : '#423D84'},
              {"label" : "-1.5 &mdash; -1 &sigma;", "upper" : -1.0, "text" : "white", "fill" : '#38578C'},
              {"label" : "-1 &mdash; 0.5 &sigma;", "upper" : -.5, "text" : "white", "fill" : '#2D6F8E'},
              {"label" : "-0.5 &mdash; 0 &sigma;", "upper" : 0, "text" : "white", "fill" : '#24858D'},
              {"label" : "0 &mdash; .5 &sigma;", "upper" : .5, "text" : "white", "fill" : '#1E9A89'},
              {"label" : "0.5 &mdash; 1 &sigma;", "upper" : 1.0, "text" : "white", "fill" : '#2AB07E'},
              {"label" : "1 &mdash; 1.5 &sigma;", "upper" : 1.5, "text" : "white", "fill" : '#51C468'},
              {"label" : "1.5 &mdash; 2 &sigma;", "upper" : 2, "text" : "black", "fill" : '#86D449'},
              {"label" :  "2 &mdash; 2.5 &sigma;", "upper" : 2.5, "text" : "black", "fill" : '#C2DF22'},
              {"label" :  " > 2.5 &sigma;", "upper" : 3, "text" : "black", "fill" : '#FDE724'},];

function getColor(d) {
  for (var vi in cmap_z) {
    if (d <= cmap_z[vi].upper) {
      return cmap_z[vi].fill;
    }
  }
  return '#BBB';
}
    
