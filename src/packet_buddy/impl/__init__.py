import logging
import sys

logging.getLogger('ICMPClient').setLevel(logging.DEBUG)
logging.getLogger('ICMPServer').setLevel(logging.DEBUG)

h = logging.StreamHandler(stream=sys.stdout)
h.setFormatter(logging.Formatter("{name}-{levelname}-{asctime}-{thread}-{message}", style="{"))

logging.getLogger('ICMPClient').addHandler(h)
logging.getLogger('ICMPServer').addHandler(h)

from .server import ICMPServer
from .client import ICMPClient
from .common import BasicMessage
