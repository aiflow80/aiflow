from .logger import root_logger as logger

logger.info("Initializing aiflow...")
from .launcher import Launcher
from .mui import mui

launcher = Launcher()  # Create instance without starting server

logger.info("aiflow initialization completed")

__all__ = ['mui']