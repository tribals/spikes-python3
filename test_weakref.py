import weakref


def test_lifespan_of_weak_referenced_object():
    context = Context()

    place_foo_in(context)

    assert context[0] is not None

    # now make ref to be weak
    context = WeakContext()

    place_foo_in(context)

    # assert context[0] is not None # oops!
    assert context[0] is None


class Context(object):
    def __init__(self):
        self._context = list()

    def append(self, object_):
        self._context.append(object_)

    def __getitem__(self, index):
        return self._context[index]


def place_foo_in(context):
    # create ref
    foo = Foo()

    context.append(foo)

    # returning from function, there is another ref to `foo`,
    # and it can not be freed yet
    pass


class Foo(object):
    pass


class WeakContext(object):
    def __init__(self):
        self._context = list()

    def append(self, object_):
        self._context.append(weakref.ref(object_))

    def __getitem__(self, index):
        return self._context[index]()
