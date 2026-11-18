from unittest.mock import patch, MagicMock
from decimal import Decimal
from presentation.user.wallet.transfer_menu import run_transfer_menu
from core.result import Result


@patch("presentation.user.wallet.transfer_menu.clear_console")
@patch("builtins.input")
def test_transfer_menu_empty_username(mock_input, mock_clear):
    mock_input.side_effect = [""]
    with patch("presentation.user.wallet.transfer_menu.console.print") as mock_print:
        run_transfer_menu(1)
        mock_print.assert_called_with("[red]Username არ შეიძლება იყოს ცარიელი.[/red]")


@patch("presentation.user.wallet.transfer_menu.clear_console")
@patch("builtins.input")
def test_transfer_menu_empty_asset(mock_input, mock_clear):
    mock_input.side_effect = ["alice", ""]
    with patch("presentation.user.wallet.transfer_menu.console.print") as mock_print:
        run_transfer_menu(1)
        mock_print.assert_called_with("[red]აქტივი არ შეიძლება იყოს ცარიელი.[/red]")


@patch("presentation.user.wallet.transfer_menu.clear_console")
@patch("builtins.input")
def test_transfer_menu_invalid_amount(mock_input, mock_clear):
    mock_input.side_effect = ["alice", "BTC", "abc"]
    with patch("presentation.user.wallet.transfer_menu.console.print") as mock_print:
        run_transfer_menu(1)
        assert any("არასწორი რაოდენობის ფორმატი" in str(c) for c in mock_print.call_args_list)


@patch("presentation.user.wallet.transfer_menu.clear_console")
@patch("builtins.input")
@patch("presentation.user.wallet.transfer_menu.get_db")
@patch("presentation.user.wallet.transfer_menu.WalletService")
def test_transfer_menu_success(mock_wallet_service, mock_get_db, mock_input, mock_clear):
    mock_input.side_effect = ["alice", "BTC", "1.5", ""]
    mock_service_inst = MagicMock()
    mock_service_inst.transfer.return_value = Result.success({})
    mock_wallet_service.return_value = mock_service_inst

    with patch("presentation.user.wallet.transfer_menu.console.print") as mock_print:
        run_transfer_menu(1)
        assert any("წარმატებით გადაირიცხა" in str(c) for c in mock_print.call_args_list)


@patch("presentation.user.wallet.transfer_menu.clear_console")
@patch("builtins.input")
@patch("presentation.user.wallet.transfer_menu.get_db")
@patch("presentation.user.wallet.transfer_menu.WalletService")
def test_transfer_menu_failure(mock_wallet_service, mock_get_db, mock_input, mock_clear):
    mock_input.side_effect = ["alice", "BTC", "1.5", ""]
    mock_service_inst = MagicMock()
    mock_service_inst.transfer.return_value = Result.failure("არასაკმარისი ბალანსი")
    mock_wallet_service.return_value = mock_service_inst

    with patch("presentation.user.wallet.transfer_menu.console.print") as mock_print:
        run_transfer_menu(1)
        assert any("არასაკმარისი ბალანსი" in str(c) for c in mock_print.call_args_list)
