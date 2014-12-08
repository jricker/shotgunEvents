import mw_events
reload(mw_events)
from mw_events import Events
import mw_shotgun_keys
mw = Events()
#########################################################################################################################
def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""
    # Callbacks are called in registration order.
    reg.registerCallback(mw_shotgun_keys.scriptName, mw_shotgun_keys.scriptKey, process_event)
def process_event(sg, logger, event, args):
    mw.distrubute_event(event)