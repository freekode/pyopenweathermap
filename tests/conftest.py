"""Keep tests without the network marker completely offline."""

import socket

import pytest


@pytest.fixture(autouse=True)
def block_unmarked_network(request, monkeypatch):
    if request.node.get_closest_marker("network") is not None:
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Network access requires @pytest.mark.network")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
