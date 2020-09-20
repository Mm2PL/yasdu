import argparse
import sys
import types
import typing

from yasdu.shell import ask_yes_no
from .io import load
from .frame import LoadedFrame


class ArgumentsNamespace:
    load_file: typing.Optional[str]
    no_sources: bool
    yes_please_load_the_dump: bool


def _show_frames(d, globals_ref, locals_ref, no_sources=False):
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
                if frame.f_line > len(files[frame.file]) - 1:
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


def _update_frame(d, globals_ref, locals_ref, count_frames):
    if '_lframe' in globals_ref:
        current_frame = globals_ref['_lframe'].frame_number  # _lframe if exists, will always be a LoadedFrame
    elif '_lframe' in locals_ref:
        current_frame = locals_ref['_lframe'].frame_number  # _lframe if exists, will always be a LoadedFrame
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
        locals_ref.update(frame.f_locals)

    if 'frames' in globals_ref:
        globals_ref['frames']()

    if 'get_ipython' in globals_ref:
        _update_ipython_prompt(globals_ref['get_ipython'](), frame)
    else:
        _update_sys_prompt(frame)


def _show_sources(d, globals_ref, locals_ref, no_sources, count_lines):
    if no_sources:
        print('Sources are disabled.')
        return
    frame = globals_ref.get('_lframe')
    if not frame:
        frame = locals_ref.get('_lframe')
    if not frame:
        print('Unable to get frame')
        return
    start_display = frame.f_line - count_lines
    stop_display = frame.f_line + count_lines
    try:
        with open(frame.file) as f:
            for num, line in enumerate(f):
                if stop_display > num > start_display:
                    if num == frame.f_line-1:
                        print('->', line.rstrip('\r\n'))
                    else:
                        print('  ', line.rstrip('\r\n'))
    except FileNotFoundError:
        print(f'{frame.file}: File not found')


def _main():
    p = argparse.ArgumentParser()
    action_group = p.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-l', '--load', metavar='FILE', dest='load_file',
                              help='Loads given file and starts a Python interpreter')
    p.add_argument('-S', '--no-sources', dest='no_sources', action='store_true',
                   help='Disables reading the sources from disk and showing them, useful if they have changed.')
    p.add_argument('-y', dest='yes_please_load_the_dump', action='store_true',
                   help='Loads the dump without asking you.')
    args = p.parse_args(namespace=ArgumentsNamespace())
    if args.load_file:
        if not args.yes_please_load_the_dump and not ask_yes_no('Loading dump files can allow them to execute code. '
                                                                'Do you still want to proceed?', default=False):
            print('Exitting.')
            exit(0)
        d = load(args.load_file)

        sys.ps1 = '>>>'
        sys.ps2 = '...'

        locals_ref = {}
        globals_ref: typing.Dict[str, typing.Union[types.LambdaType, typing.List[LoadedFrame], LoadedFrame]] = {
            'frames': lambda: _show_frames(d, globals_ref, locals_ref, no_sources=args.no_sources),
            'd': d,
            'up': lambda: _update_frame(d, globals_ref, locals_ref, -1),
            'down': lambda: _update_frame(d, globals_ref, locals_ref, 1),
            'sources': lambda c=15: _show_sources(d, globals_ref, locals_ref, args.no_sources, c)
        }
        globals_ref['frames']()
        d[0].interact(globals_ref, locals_ref)


if __name__ == '__main__':
    _main()
