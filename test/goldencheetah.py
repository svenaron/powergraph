import os
import datetime
import pickle

class Bindings():
    SERIES_WATTS = 10
    SERIES_CAD = 1
    SERIES_KPH = 6
    def __init__(self, dump = "gcdump.pickle"):
        dirname = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(dirname, dump), 'rb') as f:
            self.gcdump = pickle.load(f)

    def activities(self):
        return self.gcdump.keys()

    def series(self, datatype, activity = None):
        if activity:
            act = self.gcdump[activity]
        else:
            act = self.gcdump[sorted(self.gcdump.keys())[-1]]
        return act.get(datatype, [])

    def activityMetrics(self):
        timestamp = sorted(self.gcdump.keys())[-1]
        return {'date': timestamp.date(), 'time': timestamp.time(),
                'Workout_Code': "Fake Workout"}

    def season(self):
        dates = sorted(self.gcdump.keys())
        return {'name': "Fake season",
                'start': [dates[0].date()], 'end': [dates[-1].date()]}

    def webpage(self, url):
        os.system("firefox '%s'" % url)
