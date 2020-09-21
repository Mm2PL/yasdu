import os

from .shell import spawn_shell


class LoadedFrame:
    f_globals: dict
    f_locals: dict
    f_line: int
    file: str
    frame_number: int  # represents the index into the dump list (returned by load())

    def __repr__(self):
        return f'<{self.__class__.__name__} at {self.file}:{self.f_line}>'

    @classmethod
    def from_dict(cls, d: dict):
        new = cls()
        new.f_globals = d['globals']
        new.f_locals = d['locals']
        new.f_line = d['line']
        new.file = d['file']
        return new

    def interact(self, globals_ref=None, no_ipython=False):
        """
        Interact with the frame

        :param globals_ref: A reference to a dict that will store the globals.
        :param locals_ref: A reference to a dict that will store the locals.
        :param no_ipython: Disabled IPython support.
        :return: Nothing
        """
        if globals_ref:
            globals_ = globals_ref
        else:
            globals_ = {}

        globals_.update(self.f_globals)
        globals_.update(self.f_locals)
        globals_['_lframe'] = self

        print('LoadedFrame object is available through the `_lframe` global variable\n')
        spawn_shell(globals_, self.interactive_prompt_prefix, no_ipython)

    @property
    def interactive_prompt_prefix(self):
        return f'[{os.path.split(self.file)[-1]}:{self.f_line} ({self.frame_number})] '
