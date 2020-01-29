"""
Example of how to test `Commands`_ in async-style code.

.. _`Commands`: https://martinfowler.com/bliki/CQRS.html

"""

import asyncio
from unittest import mock

import pytest


async def foo(awaitable, *args, **kwargs):
    await awaitable(*args, **kwargs)


# NOTE: all three options are working. Which is better - I don't know...


@pytest.mark.asyncio
async def test_foo():
    dep = mock.AsyncMock()

    await foo(dep, 'spam', 42, a='eggs', b=4242)

    assert dep.called
    assert dep.call_args == mock.call('spam', 42, a='eggs', b=4242)
    assert dep.awaited


def test_foo1():
    dep = mock.AsyncMock()

    asyncio.run(foo(dep, 'spam', 42, a='eggs', b=4242), debug=True)

    assert dep.called
    assert dep.call_args == mock.call('spam', 42, a='eggs', b=4242)
    assert dep.awaited


def test_foo2(event_loop):
    dep = mock.AsyncMock()

    event_loop.run_until_complete(foo(dep, 'spam', 42, a='eggs', b=4242))

    assert dep.called
    assert dep.call_args == mock.call('spam', 42, a='eggs', b=4242)
    assert dep.awaited

