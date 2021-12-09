import logging
import sys

from .interfaces import *
from .abstract import *

logging.getLogger('Client').setLevel(logging.DEBUG)
logging.getLogger('Server').setLevel(logging.DEBUG)

h = logging.StreamHandler(stream=sys.stdout)
h.setFormatter(logging.Formatter("{name}-{levelname}-{asctime}-{thread}-{message}", style="{"))

logging.getLogger('Client').addHandler(h)
logging.getLogger('Server').addHandler(h)
