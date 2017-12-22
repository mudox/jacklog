# -*- coding: utf-8 -*-

import logging
import textwrap
from datetime import timedelta
from typing import NamedTuple

from .screen import sgr
from .settings import colors, margin, symbols, symbolWidth


class _Last(NamedTuple):
  head: str
  relativeCreated: int  # in milliseconds


class Formatter(logging.Formatter):

  def __init__(self, compact, interval=2000):
    super().__init__()

    self._compact = compact
    self._interval = interval

    self._last = _Last(head='', relativeCreated=0)

  def format(self, record):
    self._record = record

    # self._head
    symbolColor = colors[record.levelname.lower()]
    siteColor = colors['file']

    symbol = symbols[record.levelname.lower()]
    subsystem = (record.name == '__main__') and 'main' or record.name

    head1 = sgr(f'{symbol:{symbolWidth}}{subsystem}', symbolColor)
    head2 = sgr(f'[{record.filename}] {record.funcName}', siteColor)
    self._head = f'{head1} {head2}'

    # self._message
    self._message = super().format(record).strip()

    # self._inOneLine
    if self._message.startswith('o:'):
      self._inOneLine = True
      self._message = self._message[2:]
    else:
      self._inOneLine = False

    # format
    if not self._compact:
      lines = self._formatRegularly()
    else:
      lines = self._formatCompactly()

    self._last = _Last(
        head=self._head,
        relativeCreated=record.relativeCreated
    )

    # indent 1 space for the sake of aesthetic
    lines = textwrap.indent(lines, '\x20' * margin)
    return lines

  def _formatRegularly(self):
    headLine = self._head
    message = textwrap.indent(self._message, '\x20' * symbolWidth)

    if self._head == self._last.head:
      if self._timeLine is not None:
        lines = f'\n{self._timeLine}\n\n{message}'
      else:
        lines = f'\n{message}'
    else:
      if self._timeLine is not None:
        lines = f'\n{self._timeLine}\n\n{headLine}\n{message}'
      else:
        lines = f'\n{headLine}\n{message}'

    return lines

  def _formatCompactly(self):
    message = textwrap.indent(self._message, '\x20' * symbolWidth)

    if self._inOneLine:
      lines = f'{self._head}\x20{message[symbolWidth:]}'
    else:
      if self._head == self._last.head:
        # continue line symbol
        message = sgr('·\x20', colors['time']) + message[2:]
        lines = message
      else:
        lines = f'{self._head}\n{message}'

    return lines

  def _timeLine(self):
    # time line ?
    milliseconds = self._record.relativeCreated - self._last.relativeCreated
    if milliseconds > self._interval:
      timeLine = f'\x20\x20─── {timedelta(milliseconds=milliseconds)} elapsed'
      timeLine = sgr(timeLine, colors['time'])
    else:
      timeLine = None
