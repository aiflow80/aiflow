from aiflow.logger import root_logger as logger

from aiflow.launcher import Launcher
from aiflow.mui import mui

launcher = Launcher()  

from aiflow.events.event_base import event_base
from aiflow.events import run  # Import run from events package, not from event_base

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

__all__ = ['mui', 'logger', 'module', 'run']