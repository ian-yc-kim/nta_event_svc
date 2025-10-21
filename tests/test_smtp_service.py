import smtplib
from unittest.mock import patch, MagicMock
import pytest

from event_service.services.smtp import SMTPService, EmailSendError


def make_mock_smtp_instance(host, port):
    inst = MagicMock()
    # ensure methods exist
    inst.connect = MagicMock()
    inst.ehlo = MagicMock()
    inst.starttls = MagicMock()
    inst.login = MagicMock()
    inst.send_message = MagicMock()
    inst.quit = MagicMock()
    # add host/port attributes for tests that simulate connect behavior
    inst.host = host
    inst.port = port
    return inst


def test_ssl_success_single_recipient_message_and_calls():
    host = "smtp.example.com"
    port = 465
    username = "sender@example.com"
    password = "s3cr3t"
    recipient = "recipient@example.com"
    subject = "Greetings"
    body = "Body text goes here."

    mock_instance = make_mock_smtp_instance(host, port)

    # Patch SMTP_SSL so its __enter__ returns our mock instance
    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_ctx = mock_smtp_ssl_cls.return_value
        mock_ctx.__enter__.return_value = mock_instance

        service = SMTPService(host=host, port=port, username=username, password=password)
        service.send_email([recipient], subject, body)

    # Verify login called with credentials
    mock_instance.login.assert_called_once_with(username, password)
    # Verify send_message called once
    assert mock_instance.send_message.call_count == 1
    # Verify context manager __exit__ was invoked on exit
    assert mock_ctx.__exit__.called

    # Inspect the EmailMessage object passed to send_message
    sent_msg = mock_instance.send_message.call_args[0][0]
    assert sent_msg["From"] == username
    assert sent_msg["To"] == recipient
    assert sent_msg["Subject"] == subject
    assert body in sent_msg.get_content()


def test_starttls_success_flow():
    host = "smtp.example.com"
    port = 587
    username = "user@example.com"
    password = "pwd"
    recipient = "rcpt@example.com"
    subject = "TLS mail"
    body = "TLS body"

    mock_instance = make_mock_smtp_instance(host, port)

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_ctx = mock_smtp_cls.return_value
        mock_ctx.__enter__.return_value = mock_instance

        service = SMTPService(host=host, port=port, username=username, password=password)
        service.send_email([recipient], subject, body)

    # STARTTLS handshake expected: service should call ehlo twice and starttls once
    assert mock_instance.ehlo.call_count >= 2
    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_once_with(username, password)
    mock_instance.send_message.assert_called_once()
    # Ensure context manager exit called
    assert mock_ctx.__exit__.called


def test_connection_failure_raises_emailsenderror_and_hides_password():
    host = "bad.smtp"
    port = 465
    username = "user@bad"
    password = "shouldnotappear"
    recipient = "x@x.com"

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_ctx = mock_smtp_ssl_cls.return_value
        mock_ctx.__enter__.side_effect = smtplib.SMTPConnectError(421, "Connection refused")

        service = SMTPService(host=host, port=port, username=username, password=password)

        with pytest.raises(EmailSendError) as excinfo:
            service.send_email([recipient], "subj", "body")

    msg = str(excinfo.value)
    # Ensure safe context in message: contains host:port and username and recipient
    assert f"{host}:{port}" in msg
    assert username in msg
    assert str([recipient]) in msg
    # Ensure password is not leaked
    assert password not in msg


def test_authentication_failure_raises_emailsenderror_and_context_exit_called():
    host = "smtp.auth"
    port = 465
    username = "auth_user"
    password = "p@ssw0rd"
    recipient = "r@e.com"

    mock_instance = make_mock_smtp_instance(host, port)
    mock_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_ctx = mock_smtp_ssl_cls.return_value
        mock_ctx.__enter__.return_value = mock_instance

        service = SMTPService(host=host, port=port, username=username, password=password)

        with pytest.raises(EmailSendError) as excinfo:
            service.send_email([recipient], "s", "b")

    msg = str(excinfo.value)
    assert username in msg
    assert password not in msg
    # Ensure context manager __exit__ was invoked
    assert mock_ctx.__exit__.called


def test_multiple_recipients_formatting():
    host = "smtp.multi"
    port = 465
    username = "multi@ex"
    password = "pw"
    recipients = ["a@example.com", "b@example.com"]
    subject = "Multi"
    body = "multi body"

    mock_instance = make_mock_smtp_instance(host, port)

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_ctx = mock_smtp_ssl_cls.return_value
        mock_ctx.__enter__.return_value = mock_instance

        service = SMTPService(host=host, port=port, username=username, password=password)
        service.send_email(recipients, subject, body)

    sent_msg = mock_instance.send_message.call_args[0][0]
    assert sent_msg["To"] == ", ".join(recipients)
    assert mock_instance.send_message.call_count == 1
    assert mock_ctx.__exit__.called


def test_html_subtype_content():
    host = "smtp.html"
    port = 465
    username = "html@ex"
    password = "pw"
    recipient = "r@ex"
    subject = "HTML"
    html_body = "<h1>Hello</h1>"

    mock_instance = make_mock_smtp_instance(host, port)

    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_cls:
        mock_ctx = mock_smtp_ssl_cls.return_value
        mock_ctx.__enter__.return_value = mock_instance

        service = SMTPService(host=host, port=port, username=username, password=password)
        service.send_email([recipient], subject, html_body, subtype="html")

    sent_msg = mock_instance.send_message.call_args[0][0]
    assert sent_msg.get_content_type() == "text/html"
    assert html_body in sent_msg.get_content()
    assert mock_ctx.__exit__.called


def test_empty_recipient_list_raises_value_error():
    service = SMTPService(host="h", port=465, username="u", password="p")
    with pytest.raises(ValueError):
        service.send_email([], "s", "b")
