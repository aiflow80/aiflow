from libz.logger import root_logger as logger

from libz.launcher import Launcher
from libz.mui import mui

launcher = Launcher()  

from libz.events import event_base  # Import run from events package, not from event_base

# Expose the events dictionary references
events = event_base.events
events_store = event_base.events_store
state = event_base.state

def init(wait_timeout=30):
    try:
        ready = event_base.wait_until_ready(timeout=wait_timeout)
        if ready:
            event_base.set_caller_file(launcher.caller_file)
        else:
            logger.warning("EventBase not ready, timeout occurred")
        
        return ready
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt during initialization, shutting down...")
        launcher.cleanup()
        launcher.force_exit()
        return False

try:
    if init():
        pass
    else:
        logger.error("aiflow initialization failed, starting event base")
except KeyboardInterrupt:
    logger.info("KeyboardInterrupt received during module loading, shutting down...")
    launcher.force_exit()

__all__ = ['mui', 'events', 'events_store', 'state', 'logger']