from reportlab.graphics import renderSVG
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib import colors


def save_reliability(path, metrics, title):
    drawing = Drawing(600,390)
    chart = LinePlot()
    chart.x,chart.y,chart.width,chart.height = 65,95,470,235
    chart.xValueAxis.valueMin=chart.yValueAxis.valueMin=0
    chart.xValueAxis.valueMax=chart.yValueAxis.valueMax=1
    chart.xValueAxis.valueStep=chart.yValueAxis.valueStep=.2
    points = [(b['mean_probability'],b['positive_rate']) for b in metrics['bins'] if b['count']]
    chart.data = [[(0,0),(1,1)],points]
    chart.lines[0].strokeColor=colors.gray
    chart.lines[0].strokeDashArray=[4,4]
    chart.lines[1].strokeColor=colors.darkblue
    chart.lines[1].symbol=makeMarker('FilledCircle')
    drawing.add(chart)
    drawing.add(String(30,365,title,fontSize=11))
    drawing.add(String(175,65,'Probabilidade media por faixa',fontSize=10))
    drawing.add(String(10,340,'Taxa observada de derivacao',fontSize=10))
    counts = ', '.join(str(b['count']) for b in metrics['bins'])
    drawing.add(String(30,35,'n por faixa [0,.1), ... [.9,1]: '+counts,fontSize=9))
    drawing.add(String(30,15,f"Total n={metrics['n']}; faixas vazias omitidas; linha cinza = calibracao ideal",fontSize=9))
    renderSVG.drawToFile(drawing,str(path))
