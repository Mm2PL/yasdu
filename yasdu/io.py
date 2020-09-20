from .frame import LoadedFrame

import json
import os
import traceback
import types
import typing

import dill as pickle
from dill import PicklingError


class FakeObject:
    representation: str
    more_info: str

    def __repr__(self):
        return '[unavailable] ' + self.representation

    def __init__(self, representation):
        self.representation = representation
        self.more_info = 'No info'


def _prepare_variables(variables, ref_table):
    """Adds variables to the ref_table and uses saves them via the id and returns that."""
    o = {}
    for k, v in variables.items():
        o[k] = id(v)

        try:
            ref_table[id(v)] = pickle.dumps(v).hex()
        except (TypeError, AttributeError, PicklingError):
            ref_table[id(v)] = '[pickle failed] ' + repr(v)
    return o


def get_info(tb=None):
    data = []

    if tb:
        stack = list(tb)
    else:
        stack = list(traceback.walk_stack(None))

    ref_table = {}
    for num, f in enumerate(stack):
        frame: types.FrameType
        if isinstance(f, (tuple, list)):
            frame, _ = f
        else:
            frame = f

        data.append({
            'locals': _prepare_variables(frame.f_locals, ref_table),
            'globals': _prepare_variables(frame.f_globals, ref_table),
            'line': frame.f_lineno,
            'file': frame.f_code.co_filename
        })
    return {
        'data': data,
        'refs': ref_table
    }


def dump(filename: str, comment: typing.Optional[str] = None, tb=None):
    info = get_info(tb)
    # don't move down, otherwise the open file will be saved :-)

    orig_filename = filename
    counter = 0

    while 1:
        if os.path.exists(filename):
            counter += 1
            filename = orig_filename + '.' + str(counter)
        else:
            break

    with open(filename, 'w') as f:
        info['comment'] = comment
        json.dump(info, f, indent=4)
    print(f'*** Created stack dump in {filename!r} ***')
    return filename


def load(filename: str):
    with open(filename, 'r') as f:
        jdata = json.load(f)
    data = jdata['data']
    ref_t = _load_ref_table(jdata['refs'])
    print(f'Unpickled {len(ref_t)} objects...')
    frames = []
    for num, f in enumerate(data):
        f['globals'] = _resolve_refs(f['globals'], ref_t)
        f['locals'] = _resolve_refs(f['locals'], ref_t)
        frames.append(LoadedFrame.from_dict(f))
    print('Done loading data.')
    if 'comment' in jdata:
        c = jdata['comment']
        if c is not None:
            print()
            print()
            print(c)
    for num, frame in enumerate(frames):
        frame: LoadedFrame
        frame.frame_number = num
    return frames


def _resolve_refs(variables: dict, ref_table: dict) -> dict:
    """Replaces `ref_table` refs while copying `variables` to the output."""
    new_vars = {}
    for num, kvpair in enumerate(variables.items()):
        k, v = kvpair
        new_vars[k] = ref_table[str(v)]
    return new_vars


def _load_ref_table(variables: dict) -> dict:
    o = {}
    for k, v in variables.items():
        v: str
        if v.startswith('[pickle failed] '):
            o[k] = FakeObject(v.replace('[pickle failed] ', '', 1))
        else:
            try:
                o[k] = pickle.loads(bytes.fromhex(v))
            except BaseException as e:  # pickle can execute anything, let's not let that crash the program.
                o[k] = FakeObject('[load failed]')
                o[k].more_info = (f'Loading from pickle failed: {e}\n'
                                  f'Hex pickled data: {v}')
    return o
