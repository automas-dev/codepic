from unittest.mock import patch

from codepic import cli


@patch('codepic.cli.print')
def test_first(mock_print):
    cli()

    mock_print.assert_called_once_with('Hello CLI')
