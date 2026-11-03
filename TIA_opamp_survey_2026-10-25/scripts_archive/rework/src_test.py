import schemdraw, schemdraw.elements as elm
schemdraw.use("matplotlib")
d = schemdraw.Drawing(show=False)
d.add(elm.Line().at((0, 0)).to((0, 1)))          # leaves the drawing direction "up"
a = d.add(elm.SourceI().at((1, 0)).to((1, -1.4)))
b = d.add(elm.SourceI().endpoints((2, 0), (2, -1.4)))
c = d.add(elm.SourceI().at((3, 0)).theta(-90).length(1.4))
for n, e in (("to", a), ("endpoints", b), ("theta+length", c)):
    print(n, [round(v, 2) for v in e.start], [round(v, 2) for v in e.end])
