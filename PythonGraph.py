from plotly.offline import plot
import plotly.graph_objects as go
import numpy as np
import datetime as dt
import os.path

samples = list(range(1, 91))

def moving_average(a, n) :
    ret = np.cumsum(a, dtype = float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def max_watts(pwr, t):
    return np.max(moving_average(pwr, t))

if 'peakWatts' not in dir():
    peakWatts = {}

def get_peaks(cdt):
    season = []
    for a in GC.activities():
        if a.date() < GC.season()['start'][0]:
            continue
        if a.date() >= GC.season()['end'][0]:
            continue
        if a == cdt:
            continue
        pwr = GC.series(GC.SERIES_WATTS, activity = a)
        if not pwr:
            continue
        if a not in peakWatts:
            peakWatts[a] = [(a, max_watts(pwr, d)) for d in samples]
        season.append(peakWatts[a])

    if not season:
        return None

    alltime = [sorted(c, key = lambda x: x[1]) if c else [0] * len(samples)
               for c in [[pw[d - 1] for pw in season] for d in samples]]
    thistime = [list(filter(lambda x: x[0] < cdt, c)) for c in alltime]

    n = min(10, len(alltime[0]))

    maxDates =  [str(p[0][0].date()) for p in alltime]
    nthDates =  [str(p[-n][0].date()) for p in alltime]
    thisDates = [str(p[-n][0].date()) for p in thistime]
    maxW = [p[-1][1] for p in alltime]
    nthW = [p[-n][1] for p in alltime]
    thisW = [p[-1][1] for p in thistime]
    currW = [max_watts(GC.series(GC.SERIES_WATTS, activity = cdt), d)
             for d in samples]
    return {'seconds': samples,
            'max': maxW, 'maxDates': maxDates,
            'nth': nthW, 'nthDates': nthDates,
            'this': thisW, 'thisDates': thisDates,
            'current': currW}


def gcPlot(data, title):
    scNth = go.Scatter(x = data['seconds'], y = data['nth'],
                       mode = 'lines', name = '', hoverinfo = "y+text",
                       line = {'width': 0}, text = data['nthDates'])
    scMax = go.Scatter(x = data['seconds'], y = data['max'],
                       mode = 'lines', name = "%s Max" % GC.season()['name'][0],
                       hoverinfo = "y+text", fill = "tonexty",
                       line = {'width': 0}, text = data['maxDates'])
    scThis = go.Scatter(x = data['seconds'], y = data['this'],
                        mode = 'lines', name = "Local Max",
                        hoverinfo = "y+text", text = data['thisDates'])
    scCur = go.Scatter(x = data['seconds'], y = data['current'],
                       mode = 'lines', hoverinfo = "y", name = str(cdt.date()))

    layout = go.Layout(title = go.layout.Title(text = title))

    fig = go.Figure(layout = layout)
    fig.add_trace(scNth)
    fig.add_trace(scMax)
    fig.add_trace(scThis)
    fig.add_trace(scCur)

    f = plot(fig, filename = "powergraph.html", auto_open = False)
    GC.webpage("file://%s" % os.path.abspath(f))

current = GC.activityMetrics()
cdt = dt.datetime.combine(current['date'], current['time'])
data = get_peaks(cdt)
if data:
    gcPlot(data, current['Workout_Code'])
