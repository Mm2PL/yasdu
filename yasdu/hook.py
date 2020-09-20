import datetime
import sys
import traceback
import types
import typing

from yasdu import dump


def hook():
    """Hooks sys.excepthook with yasdu.dump()."""
    sys.excepthook = _hook


def _frames_from_traceback(tb: types.TracebackType) -> typing.List[types.FrameType]:
    """Extract frames from traceback object"""
    output = []
    current = tb
    while 1:
        output.append(current.tb_frame)
        if current.tb_next:
            current = current.tb_next
        else:
            break
    return output


def _hook(type_, val, tb):
    """Hook used in yasdu.hook()."""
    dump(
        f'yasdu_autodump_{datetime.datetime.now().isoformat()}.json',
        (
                f'This is an automatic dump it has been triggered by an exception:\n'
                + ''.join(traceback.format_exception(type_, val, tb))
        ),
        _frames_from_traceback(tb)
    )
    return sys.__excepthook__(type_, val, tb)


__all__ = ['hook']
