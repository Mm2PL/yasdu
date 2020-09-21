import argparse
import sys
import types
import typing

from .io import load
from .frame import LoadedFrame


class ArgumentsNamespace:
    load_file: typing.Optional[str]
    no_sources: bool
    assume_yes: bool
    no_ipython: bool


def _show_frames(d, globals_ref, no_sources=False):
    """Implementation of frames() function in REPL"""
    files = {}
    print('Available frames')
    for num, frame in enumerate(d):
        frame: LoadedFrame
        fail_cause = None
        line = '# unable to load sources'
        if no_sources:
            line = '# sources disabled'
        else:
            if frame.file not in files:
                try:
                    with open(frame.file, 'r') as f:
                        files[frame.file] = f.readlines()
                except FileNotFoundError:
                    fail_cause = 'File not found'

            if frame.file in files:
                if frame.f_line > len(files[frame.file]):
                    line = '# file too small to find line'
                else:
                    line = files[frame.file][frame.f_line - 1].rstrip('\r\n').lstrip('  ')

        if fail_cause:
            line += ': ' + fail_cause

        suffix = ''
        if frame.frame_number == (globals_ref.get('_lframe').frame_number if '_lframe' in globals_ref else 0):
            suffix = ' <--'

        print(f'  {num}. {frame.file}:{frame.f_line} {line}{suffix}')


def _update_ipython_prompt(shell, frame):
    shell.prompts.note = frame.interactive_prompt_prefix


def _update_sys_prompt(frame):
    sys.ps1 = frame.interactive_prompt_prefix + ' >>> '
    sys.ps2 = frame.interactive_prompt_prefix + ' ... '


def _update_frame(d, globals_ref, count_frames):
    """Implementation of up() and down() functions in REPL"""
    if '_lframe' in globals_ref:
        current_frame = globals_ref['_lframe'].frame_number  # _lframe if exists, will always be a LoadedFrame
    else:
        raise RuntimeError('Unable to get current frame!!!')
    new_frame = current_frame + count_frames
    if new_frame > len(d) - 1 or new_frame < 0:
        print('Frame out of range.')
        return
    else:
        frame = d[new_frame]
        globals_ref['_lframe'] = frame

        globals_ref.update(frame.f_globals)
        globals_ref.update(frame.f_locals)

    if 'frames' in globals_ref:
        globals_ref['frames']()

    if 'get_ipython' in globals_ref:
        _update_ipython_prompt(globals_ref['get_ipython'](), frame)
    else:
        _update_sys_prompt(frame)


def _show_sources(d, globals_ref, no_sources, count_lines):
    """Implementation of sources() function in REPL"""
    if no_sources:
        print('Sources are disabled.')
        return
    frame = globals_ref.get('_lframe')
    if not frame:
        print('Unable to get frame')
        return
    start_display = frame.f_line - count_lines
    stop_display = frame.f_line + count_lines
    try:
        with open(frame.file) as f:
            for num, line in enumerate(f):
                if stop_display > num > start_display:
                    if num == frame.f_line - 1:
                        print('->', line.rstrip('\r\n'))
                    else:
                        print('  ', line.rstrip('\r\n'))
    except FileNotFoundError:
        print(f'{frame.file}: File not found')


def ask_yes_no(prompt, default=True) -> bool:
    """
    Asks a yes/no question to the user

    :param prompt: The prompt to show the user. "[y/n]" will be added to the end.
    :param default: The default answer (activated by leaving the input empty). \
    Can be True (yes), False (no), None (forces user to pick)
    """
    if default is True:
        prompt = prompt + ' [Y/n]'
    elif default is False:
        prompt = prompt + ' [y/N]'
    elif default is None:
        prompt = prompt + ' [y/n]'
    else:
        raise LookupError('Invalid yes/no prompt default, possible values are True (yes), False (no), '
                          'None (no default)')

    while 1:
        try:
            ans = input(prompt).casefold().rstrip(' .!\\')
        except (KeyboardInterrupt, EOFError):
            return False

        if ans == '' and default is not None:
            return default

        if ans in ['yes', 'y']:
            return True
        elif ans in ['no', 'n']:
            return False
        else:
            print('Answer "yes" or "no".')


def _main():
    p = argparse.ArgumentParser()
    action_group = p.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-l', '--load', metavar='FILE', dest='load_file',
                              help='Loads given file and starts a Python interpreter')
    p.add_argument('-S', '--no-sources', dest='no_sources', action='store_true',
                   help='Disables reading the sources from disk and showing them, useful if they have changed.')
    p.add_argument('-y', dest='assume_yes', action='store_true',
                   help='Assume yes to all questions')
    p.add_argument('--no-ipython', dest='no_ipython', action='store_true',
                   help='Disables IPython support.')
    args = p.parse_args(namespace=ArgumentsNamespace())
    if args.load_file:
        if not args.assume_yes and not ask_yes_no('Loading dump files can allow them to execute code. '
                                                  'Do you still want to proceed?', default=False):
            print('Exitting.')
            exit(0)
        d = load(args.load_file)

        sys.ps1 = '>>>'
        sys.ps2 = '...'

        globals_ref: typing.Dict[str, typing.Union[types.LambdaType, typing.List[LoadedFrame], LoadedFrame]] = {
            'frames': lambda: _show_frames(d, globals_ref, no_sources=args.no_sources),
            'dump': d,
            'up': lambda: _update_frame(d, globals_ref, -1),
            'down': lambda: _update_frame(d, globals_ref, 1),
            'sources': lambda c=15: _show_sources(d, globals_ref, args.no_sources, c)
        }
        globals_ref['frames']()
        d[0].interact(globals_ref, no_ipython=args.no_ipython)


if __name__ == '__main__':
    _main()
