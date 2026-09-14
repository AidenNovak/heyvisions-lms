"""Construction of the ``From`` header for outbound mail.

**Only the display name is configurable. The address never is.**

Every email leaves as ``<display name> <mailing.system_email_address>``. The
address is the one domain that holds the verified SPF/DKIM records, so letting
an organization point ``From`` at an address of its own would break DKIM
alignment on every message and drag down the reputation of a sending domain
shared by every tenant. A display name changes nothing a receiving MTA
authenticates, which is exactly why it is the part we hand out.

The display name is attacker-controllable: an org admin types it into a
settings form and it lands verbatim in an RFC 5322 header. A bare CR or LF in a
header value is header injection — enough to append a ``Bcc:`` of the
attacker's choosing or to end the header block early and take over the body.
``email.utils.formataddr`` quotes specials and RFC 2047-encodes non-ASCII, but
it will carry a newline straight through, so sanitizing has to happen *before*
it, and it happens here so that it happens exactly once.
"""

import re
from email.utils import formataddr
from typing import Optional

# Fallback used when neither the org nor the deployment names a sender. The
# deployment's own name comes from config (``site_name``); this is only the
# last resort when config is unreadable, and upstream's brand name is
# deliberately not used for it.
_FALLBACK_SENDER_NAME = "Notifications"


def default_sender_name() -> str:
    """The deployment's own From display name, or a neutral fallback.

    Read from config rather than hardcoded: the display name is user-facing
    copy naming the platform, so it must follow ``LEARNHOUSE_SITE_NAME``.
    """
    try:
        from config.config import get_learnhouse_config

        return (get_learnhouse_config().site_name or "").strip() or _FALLBACK_SENDER_NAME
    except Exception:  # pragma: no cover - config is always present in practice
        return _FALLBACK_SENDER_NAME

# Long enough for a real organization name, short enough that the header stays
# readable in every client's inbox list. Mirrored by the dashboard's character
# counter and enforced again server-side on write.
MAX_SENDER_NAME_LENGTH = 64

# C0 controls (CR, LF, NUL, TAB…), DEL, and the C1 block. TAB is included
# deliberately: it is a header *folding* character, not content.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Unicode line/paragraph separators — not C0 controls, but still line breaks to
# anything that later re-encodes the header.
_UNICODE_BREAKS = re.compile(r"[\u2028\u2029]")

_WHITESPACE_RUN = re.compile(r"\s+")


def sanitize_sender_name(raw: Optional[str]) -> str:
    """Return ``raw`` reduced to something safe to place in a header value.

    Control characters and line separators are **removed**, not replaced: a
    ``"Evil\\r\\nBcc: x@y"`` that became ``"Evil  Bcc: x@y"`` would still be a
    header the sender never intended. Runs of whitespace then collapse to a
    single space, the result is trimmed, and anything past
    ``MAX_SENDER_NAME_LENGTH`` is dropped.

    Returns ``""`` for anything that sanitizes down to nothing, which callers
    read as "no name configured".
    """
    if not raw:
        return ""

    name = _CONTROL_CHARS.sub("", str(raw))
    name = _UNICODE_BREAKS.sub("", name)
    name = _WHITESPACE_RUN.sub(" ", name).strip()

    if len(name) > MAX_SENDER_NAME_LENGTH:
        # Trim again: truncation can leave a trailing space.
        name = name[:MAX_SENDER_NAME_LENGTH].strip()

    return name


def format_sender(
    display_name: Optional[str],
    address: str,
    default_name: Optional[str] = None,
) -> str:
    """Build the ``From`` value for ``address``, displayed as ``display_name``.

    ``address`` is the platform's system email address and is never derived
    from user input (see the module docstring). ``default_name`` is the
    platform-level fallback — ``None`` means "use the deployment's own name"
    (``default_sender_name()``), while an explicit empty string means the
    deployment cleared it on purpose, in which case the bare address is emitted
    with no display name at all.

    Quoting of specials (``,`` ``;`` ``<`` ``>`` ``"`` ``:``) and RFC 2047
    encoding of non-ASCII are left to ``formataddr`` rather than hand-rolled,
    so a name in any script arrives intact instead of being stripped.
    """
    # The address is not user input, but a malformed value in config should not
    # be able to smuggle a header break either.
    addr = _CONTROL_CHARS.sub("", str(address or "")).strip()

    name = sanitize_sender_name(display_name)
    if not name:
        fallback = default_sender_name() if default_name is None else default_name
        name = sanitize_sender_name(fallback)

    if not name:
        return addr

    return formataddr((name, addr))
