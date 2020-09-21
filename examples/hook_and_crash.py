import yasdu

some_global_variable = 'testing123'


def happily_convert_some_values():
    v1 = int('deadbeef', 16)
    v2 = int('deadbeef')  # oh noes


if __name__ == '__main__':
    yasdu.hook()
    happily_convert_some_values()
