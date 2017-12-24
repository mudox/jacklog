# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from os.path import basename, getmtime
from pathlib import Path
from sys import argv
from time import time

from .formatter import Formatter
from .screen import sgr
from .settings import settings as cfg

__version__ = '1.1'


def configure(
    appName,
    fileName=None,
    logTTY=None,
    compact=True,
    eventInterval=2000,
    sessionInterval=5,
    wrap=None
):
  """ Configure logging system.

  Arguments:

    appName (str): jacklog will create f"~/.local/share/{appName}/log"
      automaticall,

    fileName (str): the name of log file that will be created, defaults to
      `{appName}.log`

    tty (Path or str): specified tty file to log directly to the corresponding
      terminal.

    compact (bool): compact relayout mode, less separating empty lines,
      defaults to False.

    eventInterval (int): time limit to add a time line in milliseconds.
      default to 2s.

    sessionInterval (int): time limit to add a session time line in seconds,
      defaults to 5s.

    wrap (int): textwrap maximum width, default to not wrap text.
  """

  if fileName is None:
    fileName = f'{appName}.log'

  rootLogger = logging.getLogger()
  rootLogger.setLevel(logging.NOTSET)

  # log to file
  logFile = Path(f'~/.local/share/{appName}/log/{fileName}').expanduser()
  logFile.parent.mkdir(parents=True, exist_ok=True)
  if not logFile.exists():  # avoid change mtime if file exists
    logFile.touch(exist_ok=True)

  logToFile = logging.FileHandler(logFile)
  logToFile.setFormatter(Formatter(compact, eventInterval))
  rootLogger.addHandler(logToFile)

  # log to tty if any
  if logTTY is not None:
    logToTTY = logging.FileHandler(logTTY)
    logToTTY.setFormatter(Formatter(compact, eventInterval))
    rootLogger.addHandler(logToTTY)

  _logSessionLine(
      logFile,
      logTTY,
      interval=sessionInterval,
      compact=compact)


def _sessionTimeLine(logFile, interval):
  # time separator
  mtime = getmtime(logFile)
  seconds = time() - mtime

  if seconds > interval:
    indent = cfg.margin + cfg.symbolWidth
    timeLine = ('·' * indent) + f'[ {timedelta(seconds=seconds)} ]'
    timeLine = sgr(timeLine, cfg.colors['time'])
    timeLine = f'{timeLine}'

    padding = []
    for _ in range(cfg.sessionTimeLinePadding):
      padding.append('')

    lines = padding + [timeLine] + padding
    return '\n'.join(lines)

  else:
    return None


def _logSessionLine(logFile, tty, interval, compact):
  launchSymbol = f'{cfg.symbols["launch"]:{cfg.symbolWidth}}'
  launchSymbol = sgr(launchSymbol, cfg.colors['launch'])

  timestamp = sgr(str(datetime.now()), cfg.colors['time'])

  cmd = basename('\x20'.join(argv))
  cmd = sgr(cmd, cfg.colors['launch'])

  launchLine = f'\x20{launchSymbol}{timestamp} {cmd}'
  launchLine = f'\n{launchLine}\n\n' if compact else f'\n\n{launchLine}\n\n'

  timeLine = _sessionTimeLine(logFile, interval)
  launchLine = f'{timeLine or ""}{launchLine}'

  launchLine = f'\x1b[38;5;242m{launchLine}\x1b[0m'
  with logFile.open('a') as file:
    file.write(launchLine)

  if tty is not None:
    if isinstance(tty, Path):
      with tty.open('a') as file:
        file.write(launchLine)
    elif isinstance(tty, str):
      with open(tty, 'a') as file:
        file.write(launchLine)
    else:
      raise RuntimeError(
          'argument `tty` must be either of type `Path` or `str`')
