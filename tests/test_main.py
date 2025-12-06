import pytest
from unittest.mock import patch, MagicMock
from moondock import main as main_module

def test_main_initialization():
    mock_client = MagicMock()
    mock_client.ping.return_value = True

    with patch("moondock.main.init_docker", return_value=mock_client), \
         patch("moondock.main.DockerEventWatcher") as MockWatcher, \
         patch("moondock.main.DiscordClient") as MockDiscord:

        mock_watcher_instance = MockWatcher.return_value
        mock_discord_instance = MockDiscord.return_value

        # Call the main() function
        main_module.main()

        # Assertions
        MockWatcher.assert_called_once()
        args, kwargs = MockWatcher.call_args

        # Positional arguments
        assert args[0] == mock_client
        assert callable(args[1])  # the callback lambda
        MockDiscord.assert_called_once()