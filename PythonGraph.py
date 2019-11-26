from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import plotly.offline as po
import plotly.graph_objects as go
import numpy as np
import datetime as dt
import os.path
import tempfile

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

if 'GC' not in dir():
    import GC

SAMPLES = list(range(1, 91))
NTHCOLOR  = "orangered"
MAXCOLOR  = NTHCOLOR
THISCOLOR = "limegreen"
CURCOLOR  = "magenta"

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

class PeakWattMeasure:
    def __init__(self, timestamp, data, duration):
        self.timestamp = timestamp
        self.duration = duration
        allSamples = moving_average(data, duration)
        self.watts = np.max(allSamples)
        idx = np.where(allSamples == self.watts)[0][0]
        # allSamples is 'duration' shorter than data because we can't
        # get a moving average until we have a full window so we must
        # subtract 'duration' from the index
        self.start = idx # - duration + duration
        self.data = np.array(data)[self.start:self.start + duration]

def moving_average(a, n) :
    ret = np.cumsum(a, dtype = float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def max_watts(pwr, t):
    return np.max(moving_average(pwr, t))

def get_peaks(peakWatts, current):
    cdt = dt.datetime.combine(current['date'], current['time'])
    season = []
    for a in GC.activities():
        if a.date() < GC.season()['start'][0]:
            continue
        if a.date() >= GC.season()['end'][0]:
            continue
        if a == cdt:
            continue
        if a not in peakWatts:
            pwr = GC.series(GC.SERIES_WATTS, activity = a)
            if not pwr:
                continue
            peakWatts[a] = [PeakWattMeasure(a, pwr, d) for d in SAMPLES]
        season.append(peakWatts[a])

    if not season:
        return None

    alltime = [sorted(c, key = lambda x: x.watts) if c else [0] * len(SAMPLES)
               for c in [[pw[d - 1] for pw in season] for d in SAMPLES]]
    thistime = [list(filter(lambda x: x.timestamp < cdt, c)) for c in alltime]

    n = min(10, len(alltime[0]))

    maxDates =  [str(p[-1].timestamp.date()) for p in alltime]
    nthDates =  [str(p[-n].timestamp.date()) for p in alltime]
    thisDates = [str(p[-1].timestamp.date()) for p in thistime]
    maxW = [p[-1].watts for p in alltime]
    nthW = [p[-n].watts for p in alltime]
    thisW = [p[-1].watts for p in thistime]
    currentPwr = GC.series(GC.SERIES_WATTS, activity = cdt)
    current = [PeakWattMeasure(cdt, currentPwr, d) for d in SAMPLES]
    currW = [c.watts for c in current]
    return {'seconds': SAMPLES,
            'maxW': maxW, 'maxDates': maxDates,
            'nthW': nthW, 'nthDates': nthDates,
            'thisW': thisW, 'thisDates': thisDates,
            'currentW': currW, 'current': current,
            'all': alltime, 'this': thistime}

def get_subdata(data, second, season):
    maxW = data['all'][second][-1]
    maxName = "%dW Max %s (%s)" % (
        maxW.watts, season['name'][0], maxW.timestamp.date())
    thisW = data['this'][second][-1]
    thisName = "%dW Local Max (%s)" % (thisW.watts, thisW.timestamp.date())
    curW = data['current'][second]
    curName = "%dW Current effort (%s)" % (curW.watts, curW.timestamp.date())
    subdata = {
        'seconds': list(range(1, second + 1)),
        'maxW': maxW.data,
        'maxName': maxName,
        'thisW': thisW.data,
        'thisName': thisName,
        'currentW': curW.data,
        'currentName': curName,
    }
    return subdata


def plot_main(data, current, season):
    title = current['Workout_Code']
    layout = go.Layout(title = go.layout.Title(text = title))
    fig = go.Figure(layout = layout)

    scNth = go.Scatter(x = data['seconds'], y = data['nthW'],
                       mode = 'lines', name = '', hoverinfo = "y+text",
                       line = {'width': 0, 'color': NTHCOLOR},
                       text = data['nthDates'])
    scMax = go.Scatter(x = data['seconds'], y = data['maxW'],
                       mode = 'lines', name = "%s Max" % season['name'][0],
                       hoverinfo = "y+text", fill = "tonexty",
                       line = {'width': 0, 'color': MAXCOLOR},
                       text = data['maxDates'])
    scThis = go.Scatter(x = data['seconds'], y = data['thisW'],
                        mode = 'lines', name = "Local Max",
                        hoverinfo = "y+text", line = {'color': THISCOLOR},
                        text = data['thisDates'])
    scCur = go.Scatter(x = data['seconds'], y = data['currentW'],
                       mode = 'lines', hoverinfo = "y",
                       line = {'color': CURCOLOR}, name = str(current['date']))

    fig.add_trace(scNth)
    fig.add_trace(scMax)
    fig.add_trace(scThis)
    fig.add_trace(scCur)

    return fig

def plot_sub(data):
    title = "%d seconds effort" % data['seconds'][-1]
    sfig = None
    if sfig is None:
        layout = go.Layout(title = go.layout.Title(text = title))
        sfig = go.Figure(layout = layout)

        scMax = go.Scatter(x = data['seconds'], y = data['maxW'],
                           mode = 'lines', name = data['maxName'],
                           line = {'color': MAXCOLOR})
        scThis = go.Scatter(x = data['seconds'], y = data['thisW'],
                            mode = 'lines', name = data['thisName'],
                           line = {'color': THISCOLOR})
        scCur = go.Scatter(x = data['seconds'], y = data['currentW'],
                           mode = 'lines', name = data['currentName'],
                           line = {'color': CURCOLOR})
        sfig.add_trace(scMax)
        sfig.add_trace(scThis)
        sfig.add_trace(scCur)
    else:
        sfig.update_traces(x = data['seconds'], y = data['maxW'],
                           name = data['maxName'],
                           selector = dict(line = {'color': MAXCOLOR}))
        sfig.update_traces(x = data['seconds'], y = data['thisW'],
                           name = data['thisName'],
                           selector = dict(line = {'color': THISCOLOR}))
        sfig.update_traces(x = data['seconds'], y = data['currentW'],
                           name = data['currentName'],
                           selector = dict(line = {'color': CURCOLOR}))


    return sfig

class GCHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith('/powergraph'):
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if not self.server.data:
            self.wfile.write(bytes("<html>No data</html>", 'UTF-8'))
            return

        if '?' in self.path:
            getargs = self.path.split("?")[-1]
            args = dict([a.split("=") for a in getargs.split("&")])
        else:
            args = {}

        if 'second' in args:
            js = ONCLICKSUB
            subdata = get_subdata(
                self.server.data, int(args['second']), self.server.season)
            fig = plot_sub(subdata)
        else:
            js = ONCLICKMAIN
            fig = plot_main(
                self.server.data, self.server.current, self.server.season)

        script = '<script type="text/javascript">%s</script>' % js
        div = po.plot(fig, output_type = 'div', include_plotlyjs = 'cdn')
        self.wfile.write(bytes("<html>%s%s</html>" % (div, script), 'UTF-8'))

def run(addr = '', port = 8000):
    httpd = ThreadingHTTPServer((addr, port), GCHandler)
    httpd.peakWatts = {}
    httpd.main_thread = threading.Thread(target = httpd.serve_forever)
    httpd.main_thread.start()
    return httpd

if 'srv' not in dir():
    srv = run()

srv.season = GC.season()
srv.current = GC.activityMetrics()
srv.data = get_peaks(srv.peakWatts, srv.current)
GC.webpage("http://localhost:%d/powergraph" % srv.server_port)
