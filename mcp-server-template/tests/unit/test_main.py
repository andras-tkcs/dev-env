"""__PACKAGE__.__main__: argument handling, without starting a real transport."""

from __future__ import annotations

import pytest

from __PACKAGE__ import __main__ as entry
from __PACKAGE__ import __version__

pytestmark = pytest.mark.unit


class TestMain:
    def test_version_flag_prints_version_and_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            entry.main(["--version"])
        assert exc.value.code == 0
        assert __version__ in capsys.readouterr().out

    def test_runs_the_server_over_stdio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        transports: list[str] = []

        class FakeServer:
            def run(self, transport: str) -> None:
                transports.append(transport)

        monkeypatch.setattr(entry, "build_server", FakeServer)
        assert entry.main([]) == 0
        assert transports == ["stdio"]
