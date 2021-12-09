import logging
import sys

# https://stackoverflow.com/a/384125

L_SERVER = 'Server'
L_CLIENT = 'Client'
L_COMMON = 'Common'

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}

logging.getLogger(L_CLIENT).setLevel(logging.DEBUG)
logging.getLogger(L_SERVER).setLevel(logging.DEBUG)
logging.getLogger(L_COMMON).setLevel(logging.DEBUG)


class CustomFormat(logging.Formatter):

    def __init__(self, c: int):
        super(CustomFormat, self).__init__(
            COLOR_SEQ % (30 + WHITE) +
            "[{asctime}] "
            + COLOR_SEQ % (30 + c)
            + " [{name:^8s}] "
            + RESET_SEQ
            + " {levelname} {message}",
            style="{"
        )

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = (
                    COLOR_SEQ % (30 + COLORS[levelname])
                    + "[{levelname:^9s}]"
                    + RESET_SEQ
            ).format(levelname=levelname)
        return logging.Formatter.format(self, record)


hs = logging.StreamHandler(stream=sys.stdout)
hs.setFormatter(CustomFormat(MAGENTA))

hc = logging.StreamHandler(stream=sys.stdout)
hc.setFormatter(CustomFormat(CYAN))

hg = logging.StreamHandler(stream=sys.stdout)
hg.setFormatter(CustomFormat(GREEN))

logging.getLogger(L_CLIENT).addHandler(hc)
logging.getLogger(L_SERVER).addHandler(hs)
logging.getLogger(L_COMMON).addHandler(hg)


def set_level(level: int):
    logging.getLogger(L_CLIENT).setLevel(level)
    logging.getLogger(L_SERVER).setLevel(level)
    logging.getLogger(L_COMMON).setLevel(level)


__all__ = ['logging', 'L_SERVER', 'L_CLIENT', 'L_COMMON', 'set_level']
