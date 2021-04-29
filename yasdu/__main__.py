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
            suffix = ' <=='

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
        globals_ref.update(globals_ref['_global_functions'])

    if 'sources' in globals_ref:
        globals_ref['sources']()
        print('\n')

    if 'frames' in globals_ref:
        globals_ref['frames']()

    if 'get_ipython' in globals_ref:
        _update_ipython_prompt(globals_ref['get_ipython'](), frame)
    else:
        _update_sys_prompt(frame)


def _show_sources(d, globals_ref, args_ref: ArgumentsNamespace, count_lines):
    """Implementation of sources() function in REPL"""
    if args_ref.no_sources:
        print('Sources are disabled.')
        return
    frame = globals_ref.get('_lframe')
    if not frame:
        print('Unable to get frame')
        return
    start_display = frame.f_line - count_lines
    stop_display = frame.f_line + count_lines
    other_frame_lines = {fr.f_line: num for num, fr in enumerate(d) if fr.file == frame.file}

    line_number_bar_color = '\033[48;5;236m'
    current_indicator_color = '\033[92m'
    other_indicator_color = '\033[32m'
    sgr_reset = '\033[0;97m'
    line_fill = '\033[0K'

    current_line_color = '\033[48;5;234m'
    other_lines_color = '\033[40m'
    try:
        with open(frame.file) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f'{frame.file}: File not found')
    max_frame_number_length = max([len(str(i)) for i in other_frame_lines.keys()])
    max_line_number_length = len(str(len(lines)))
    align_size = max(max_frame_number_length + 1, max_line_number_length, 3)
    for num, line in enumerate(lines):
        if stop_display > num > start_display:
            if num == frame.f_line - 1:
                print(
                    line_number_bar_color, current_indicator_color,
                    f'{"==>": >{align_size}} ',
                    sgr_reset,
                    current_line_color,
                    line.rstrip('\r\n'),
                    sgr_reset,
                    line_fill,
                    sep=''
                )
            elif num + 1 in other_frame_lines:
                print(
                    line_number_bar_color, other_indicator_color,
                    f'{other_frame_lines[num + 1]: >{align_size - 1}}> ',
                    sgr_reset,
                    other_lines_color,
                    line.rstrip('\r\n'),
                    sgr_reset,
                    line_fill,
                    sep=''
                )
            else:
                print(
                    line_number_bar_color,
                    f'{num + 1: >{align_size}} ',
                    sgr_reset,
                    other_lines_color,
                    line.rstrip('\r\n'),
                    sgr_reset,
                    line_fill,
                    sep=''
                )


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
        global_functions = {
            'frames': lambda: _show_frames(d, globals_ref, no_sources=args.no_sources),
            'dump': d,
            'up': lambda count=1: _update_frame(d, globals_ref, -count),
            'down': lambda count=1: _update_frame(d, globals_ref, count),
            'sources': lambda c=15: _show_sources(d, globals_ref, args, c)
        }
        globals_ref: typing.Dict[str, typing.Union[types.LambdaType, typing.List[LoadedFrame], LoadedFrame]] = {}
        globals_ref.update(global_functions)
        globals_ref['_global_functions'] = global_functions
        globals_ref['frames']()
        d[0].interact(globals_ref, no_ipython=args.no_ipython)


if __name__ == '__main__':
    _main()
