from io import StringIO
from unittest.mock import patch

import pytest

from lox.lox import Lox, run_file, run_prompt


def test_error_reporting():
    # Capture stderr output
    with patch("sys.stderr", new=StringIO()) as fake_stderr:
        Lox.error(1, "test error")
        assert fake_stderr.getvalue() == "[line 1] Error: test error\n"
        assert Lox.had_error


def test_report_with_context():
    with patch("sys.stderr", new=StringIO()) as fake_stderr:
        Lox.report(1, " in function 'foo'", "invalid syntax")
        assert (
            fake_stderr.getvalue()
            == "[line 1] Error in function 'foo': invalid syntax\n"
        )
        assert Lox.had_error


def test_run_file_nonexistent():
    with pytest.raises(FileNotFoundError):
        run_file("nonexistent.lox")


def test_run_file_invalid_encoding():
    mock_data = b"\x80invalid"  # Invalid UTF-8
    # mock = mock_open(read_data=mock_data)

    with patch(
        "pathlib.Path.read_text",
        side_effect=UnicodeDecodeError("utf-8", mock_data, 0, 1, "invalid"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            run_file("test.lox")
        assert exc_info.value.code == 66  # EX_NOINPUT


def test_run_file_with_error():
    mock_data = "invalid@token"  # This will cause a scanner error

    with patch("pathlib.Path.read_text", return_value=mock_data):
        with pytest.raises(SystemExit) as exc_info:
            run_file("test.lox")
        assert exc_info.value.code == 65  # EX_DATAERR
        assert Lox.had_error


def test_run_prompt():
    inputs = ["1 + 2", "var x = 10;", KeyboardInterrupt()]

    with patch("builtins.input", side_effect=inputs):
        with patch("sys.stdout", new=StringIO()):
            run_prompt()  # Should handle the KeyboardInterrupt gracefully

    # Verify error flag gets reset between inputs
    assert not Lox.had_error


def test_main_too_many_args():
    with patch("sys.argv", ["pylox", "script.lox", "extra"]):
        with pytest.raises(SystemExit) as exc_info:
            from lox.lox import main

            main()
        assert exc_info.value.code == 64  # EX_USAGE
