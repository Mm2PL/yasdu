import datetime
import sys
import traceback

import typing

from yasdu import dump

old_hook: typing.Optional[typing.Callable] = None


def hook():
    global old_hook
    old_hook = sys.excepthook
    sys.excepthook = _hook


def _hook(type_, val, tb):
    dump(
        f'yasdu_autodump_{datetime.datetime.now().isoformat()}.json',
        (
                f'This is an automatic dump it has been triggered by an exception:\n'
                + ''.join(traceback.format_exception(type_, val, tb))
        )
    )
    import IPython
    IPython.embed()
    if old_hook:
        return old_hook(type_, val, tb)


__all__ = ['hook', 'old_hook']
