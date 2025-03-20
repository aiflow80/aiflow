from .logger import root_logger as logger

logger.info("Initializing aiflow...")
from aiflow.launcher import Launcher
from aiflow.mui import mui
from aiflow.events.event_base import event_base

launcher = Launcher()  
module = launcher.caller_file

def init(wait_timeout=30):
    ready = event_base.wait_until_ready(timeout=wait_timeout)
    if ready:
        logger.info("EventBase is ready, rendering can begin")
    else:
        logger.warning("EventBase not ready, timeout occurred")
    
    return ready

logger.info("aiflow initialization completed")

if init():
    pass
else:
    logger.error("aiflow initialization failed, starting event base")

__all__ = ['mui', 'logger', 'module']