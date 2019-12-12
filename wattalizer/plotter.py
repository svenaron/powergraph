import plotly.offline as po
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
import datetime as dt

NTHCOLOR  = "orangered"
MAXCOLOR  = NTHCOLOR
THISCOLOR = "limegreen"
CURCOLOR  = "magenta"

class SprintMeasure:
    def __init__(self, timestamp, duration,
                 watts = None, cadence = None, speed = None):
        self.timestamp = timestamp
        self.duration = duration
        watts = watts or [0] * duration
        cadence = cadence or [0] * duration
        speed = speed or [0] * duration
        averageWatts = moving_average(watts, duration)
        self.peakWatts = np.max(averageWatts)
        idx = np.where(averageWatts == self.peakWatts)[0][0]
        # averageWatts is 'duration' shorter than watts because we can't
        # get a moving average until we have a full window so we must
        # add 'duration' when indexing in the original powerData
        self.start = idx # - duration + duration
        self.watts = np.array(watts)[self.start:self.start + duration]
        self.cadence = np.array(cadence)[self.start:self.start + duration]
        self.speed = np.array(speed)[self.start:self.start + duration]

        self.peakWattsCadence = sum(self.cadence) / duration
        self.peakWattsSpeed = sum(self.speed) / duration

def moving_average(a, n) :
    ret = np.cumsum(a, dtype = float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def get_maindata(sprints, current, season, activities):
    cdt = dt.datetime.combine(current['date'], current['time'])
    samples = [m.duration for m in sprints[cdt]]
    data = []
    for k in activities:
        if k.date() < season['start'][0]:
            continue
        if k.date() >= season['end'][0]:
            continue
        if k == cdt:
            continue
        data.append(sprints[k])

    if not data:
        return None

    alltime = [sorted(c, key = lambda x: x.peakWatts) if c else [0] * len(samples)
               for c in [[pw[d - 1] for pw in data] for d in samples]]
    thistime = [list(filter(lambda x: x.timestamp < cdt, c)) for c in alltime]

    n = min(10, len(alltime[0]))

    maxDates =  [str(p[-1].timestamp.date()) for p in alltime]
    nthDates =  [str(p[-n].timestamp.date()) for p in alltime]
    thisDates = [str(p[-1].timestamp.date()) for p in thistime]
    maxW = [p[-1].peakWatts for p in alltime]
    maxWCad = [p[-1].peakWattsCadence for p in alltime]
    nthW = [p[-n].peakWatts for p in alltime]
    nthWCad = [p[-n].peakWattsCadence for p in alltime]
    thisW = [p[-1].peakWatts for p in thistime]
    thisWCad = [p[-1].peakWattsCadence for p in thistime]
    currW = [c.peakWatts for c in sprints[cdt]]
    currWCad = [c.peakWattsCadence for c in sprints[cdt]]
    return {'seconds': samples,
            'maxW': maxW, 'maxDates': maxDates, 'maxWCad': maxWCad,
            'nthW': nthW, 'nthDates': nthDates, 'nthWCad': nthWCad,
            'thisW': thisW, 'thisDates': thisDates, 'thisWCad': thisWCad,
            'currentW': currW, 'currentWCad': currWCad,
            'all': alltime, 'this': thistime, 'current': sprints[cdt]}

def get_subdata(data, second, season):
    idx = second - 1
    maxW = data['all'][idx][-1]
    maxName = "%dW Max %s (%s)" % (
        maxW.peakWatts, season['name'][0], maxW.timestamp.date())
    thisW = data['this'][idx][-1]
    thisName = "%dW Local Max (%s)" % (thisW.peakWatts, thisW.timestamp.date())
    curW = data['current'][idx]
    curName = "%dW Current effort (%s)" % (curW.peakWatts, curW.timestamp.date())
    subdata = {
        'seconds': list(range(second)),
        'maxW': maxW.watts,
        'maxCad': maxW.cadence,
        'maxSpeed': maxW.speed,
        'maxName': maxName,
        'thisW': thisW.watts,
        'thisCad': thisW.cadence,
        'thisSpeed': thisW.speed,
        'thisName': thisName,
        'currentW': curW.watts,
        'currentCad': curW.cadence,
        'currentSpeed': curW.speed,
        'currentName': curName,
    }

    return subdata


def main_fig(data, current, season):
    title = current['Workout_Code']
    layout = go.Layout(title = go.layout.Title(text = title))
    fig = go.Figure(layout = layout)

    text = {}
    for k in ['nth', 'max', 'this']:
        vals = zip(data["%sWCad" % k], data["%sDates" % k])
        text[k] = ["%d rpm<br>%s" % (c, d) for (c, d) in vals]
    text['current'] = ["%d rpm" % c for c in data['currentWCad']]

    scNth = go.Scatter(x = data['seconds'], y = data['nthW'],
                       mode = 'lines', name = '', hoverinfo = "y+text",
                       line = {'width': 0, 'color': NTHCOLOR},
                       text = text['nth'])
    scMax = go.Scatter(x = data['seconds'], y = data['maxW'],
                       mode = 'lines', name = "%s Max" % season['name'][0],
                       hoverinfo = "y+text", fill = "tonexty",
                       line = {'width': 0, 'color': MAXCOLOR},
                       text = text['max'])
    scThis = go.Scatter(x = data['seconds'], y = data['thisW'],
                        mode = 'lines', name = "Local Max",
                        hoverinfo = "y+text", line = {'color': THISCOLOR},
                        text = text['this'])
    scCur = go.Scatter(x = data['seconds'], y = data['currentW'],
                       mode = 'lines', hoverinfo = "y+text",
                       line = {'color': CURCOLOR}, name = str(current['date']),
                       text = text['current'])

    fig.add_trace(scNth)
    fig.add_trace(scMax)
    fig.add_trace(scThis)
    fig.add_trace(scCur)

    fig.update_layout(yaxis_ticksuffix = 'W')

    return fig

def sub_fig(data):
    sfig = sp.make_subplots(
        rows = 3, subplot_titles = ['Watts', 'Cadence', 'Speed'],
        shared_xaxes = True)
    title = "%d seconds effort" % len(data['seconds'])
    sfig.update_layout(title_text = title)

    wMax = go.Scatter(x = data['seconds'], y = data['maxW'],
                       mode = 'lines', name = data['maxName'],
                       line = {'color': MAXCOLOR})
    wThis = go.Scatter(x = data['seconds'], y = data['thisW'],
                        mode = 'lines', name = data['thisName'],
                       line = {'color': THISCOLOR})
    wCur = go.Scatter(x = data['seconds'], y = data['currentW'],
                       mode = 'lines', name = data['currentName'],
                       line = {'color': CURCOLOR})

    sfig.add_trace(wMax , row = 1, col = 1)
    sfig.add_trace(wThis, row = 1, col = 1)
    sfig.add_trace(wCur , row = 1, col = 1)
    sfig.update_yaxes(ticksuffix = 'W', row = 1, col = 1)

    cMax = go.Scatter(x = data['seconds'], y = data['maxCad'],
                       mode = 'lines', name = data['maxName'],
                       line = {'color': MAXCOLOR}, showlegend = False)
    cThis = go.Scatter(x = data['seconds'], y = data['thisCad'],
                        mode = 'lines', name = data['thisName'],
                       line = {'color': THISCOLOR}, showlegend = False)
    cCur = go.Scatter(x = data['seconds'], y = data['currentCad'],
                       mode = 'lines', name = data['currentName'],
                       line = {'color': CURCOLOR}, showlegend = False)

    sfig.add_trace(cMax,  row = 2, col = 1)
    sfig.add_trace(cThis, row = 2, col = 1)
    sfig.add_trace(cCur,  row = 2, col = 1)
    sfig.update_yaxes(ticksuffix = 'rpm', row = 2, col = 1)

    sMax = go.Scatter(x = data['seconds'], y = data['maxSpeed'],
                       mode = 'lines', name = data['maxName'],
                       line = {'color': MAXCOLOR}, showlegend = False)
    sThis = go.Scatter(x = data['seconds'], y = data['thisSpeed'],
                        mode = 'lines', name = data['thisName'],
                       line = {'color': THISCOLOR}, showlegend = False)
    sCur = go.Scatter(x = data['seconds'], y = data['currentSpeed'],
                       mode = 'lines', name = data['currentName'],
                       line = {'color': CURCOLOR}, showlegend = False)

    sfig.add_trace(sMax,  row = 3, col = 1)
    sfig.add_trace(sThis, row = 3, col = 1)
    sfig.add_trace(sCur,  row = 3, col = 1)
    sfig.update_yaxes(ticksuffix = 'kph', row = 3, col = 1)

    return sfig
