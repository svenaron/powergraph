from .webserver import start
from .plotter import SprintMeasure, get_maindata

srv = None

def find_sprints(GC, sprints, samples = None):
    if samples is None:
        samples = list(range(1, 91))
    for a in GC.activities():
        if a not in sprints:
            pwr = GC.series(GC.SERIES_WATTS, activity = a)
            cad = GC.series(GC.SERIES_CAD, activity = a)
            spd = GC.series(GC.SERIES_KPH, activity = a)
            sprints[a] = [SprintMeasure(a, d, pwr, cad, spd) for d in samples]

def refresh_goldencheetah(GC):
    global srv
    if srv is None:
        srv = start()
        srv.sprints = {}

    find_sprints(GC, srv.sprints)

    # Only the main python-thread can use the GC object so we refresh
    # the data here
    srv.season = GC.season()
    srv.current = GC.activityMetrics()
    srv.activities = GC.activities()
    srv.data = get_maindata(
        srv.sprints, srv.current, srv.season, srv.activities)
    GC.webpage("http://%s:%d/powergraph" % (srv.server_host, srv.server_port))

def dump(GC, fname = 'gcdump.pickle'):
    """Dump data, to use in testing"""
    import pickle
    keys = [GC.SERIES_WATTS, GC.SERIES_CAD, GC.SERIES_KPH]
    acts = GC.activities()
    data = {a: {k: list(GC.series(k, activity = a)) for k in keys}
            for a in acts}
    with open(fname, 'wb') as f:
        pickle.dump(data, f)
