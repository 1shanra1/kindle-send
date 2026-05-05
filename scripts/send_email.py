#!/usr/bin/env python3
"""SMTP email backend for kindle-send.

Sends a single email with one or more attachments. Reads SMTP credentials
from environment variables.

Usage:
    send_email.py --to <addr> --subject <s> --body <b> --attach <file> [--attach <file2> ...]

Required env vars:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

Optional env vars:
    SMTP_USE_SSL  — '1' for SMTP_SSL (default for port 465), '0' for STARTTLS

The From address is always SMTP_USER. For Send-to-Kindle, this address must
be on the user's Amazon Approved Personal Document E-mail List.
"""
import argparse
import mimetypes
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path


def env(name: str, required: bool = True) -> str | None:
    v = os.environ.get(name)
    if required and not v:
        print(f"ERROR: {name} env var must be set", file=sys.stderr)
        sys.exit(2)
    return v


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--to", required=True, help="Recipient address")
    p.add_argument("--subject", required=True)
    p.add_argument("--body", default="")
    p.add_argument("--attach", action="append", default=[],
                   help="Path to a file to attach (repeatable)")
    args = p.parse_args()

    host = env("SMTP_HOST")
    port = int(env("SMTP_PORT"))
    user = env("SMTP_USER")
    password = env("SMTP_PASS")
    use_ssl = os.environ.get("SMTP_USE_SSL", "1" if port == 465 else "0") == "1"

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = args.to
    msg["Subject"] = args.subject
    msg.set_content(args.body or "Sent via kindle-send.")

    for path_str in args.attach:
        path = Path(path_str)
        if not path.exists():
            print(f"ERROR: attachment not found: {path}", file=sys.stderr)
            return 2
        ctype, _ = mimetypes.guess_type(path.name)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(path.read_bytes(), maintype=maintype,
                           subtype=subtype or "octet-stream", filename=path.name)

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)

    print(f"sent to={args.to} subject={args.subject!r} attach={len(args.attach)}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
