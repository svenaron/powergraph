from threading import Thread
from bottle import Bottle, request, run
from . import plotter

ONCLICKMAIN = """
var pgDiv = document.getElementsByClassName("plotly-graph-div");
pgDiv[0].on('plotly_click', function(data){
  window.location.href = '/powergraph?second=' + data.points[0].x;
});
"""

ONCLICKSUB = """
var pgDiv = document.getElementsByClassName("plotly-graph-div");
pgDiv[0].on('plotly_doubleclick', function(){
  window.location.href = '/powergraph';
});
"""

app = Bottle()

@app.route('/powergraph')
def powergraph():
    if not request.app.data:
        return "<html>No data</html>"

    if request.query.second:
        js = ONCLICKSUB
        subdata = plotter.get_subdata(
            request.app.data, int(request.query.second), request.app.season)
        fig = plotter.sub_fig(subdata)
    else:
        js = ONCLICKMAIN
        fig = plotter.main_fig(
            request.app.data, request.app.current, request.app.season)

    script = '<script type="text/javascript">%s</script>' % js
    div = plotter.po.plot(fig, output_type = 'div', include_plotlyjs = 'cdn')
    return "<html>%s%s</html>" % (div, script)

def start(host = '127.0.0.1', port = 8000):
    def run_app():
        run(app, host = host, port = port)
    app.main_thread = Thread(target = run_app, daemon = True)
    app.server_port = port
    app.server_host = host
    app.main_thread.start()
    return app
