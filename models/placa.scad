// Exemplo opcional: requer OpenSCAD externo. Medidas em mm.
nome = "BAMBU";
largura = 100;
profundidade = 30;
espessura = 3;
union() {
    translate([-largura/2, -profundidade/2, 0])
        cube([largura, profundidade, espessura]);
    translate([0, 0, espessura - 0.1])
        linear_extrude(height=1.1)
            text(nome, size=10, halign="center", valign="center", font="Arial");
}
