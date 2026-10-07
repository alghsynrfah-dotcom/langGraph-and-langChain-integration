import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain.tools import tool


ARTICLE_TIMEOUT = 10
MAX_CONTENT_LENGTH = 6000


def _is_safe_url(url: str) -> bool:
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"}:
        return False

    hostname = parsed_url.hostname

    if not hostname:
        return False

    hostname = hostname.lower()

    blocked_hosts = {
        "localhost",
        "localhost.localdomain",
    }

    if hostname in blocked_hosts:
        return False

    try:
        ip = ipaddress.ip_address(hostname)

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return False

    except ValueError:

        try:
            resolved_ips = socket.getaddrinfo(
                hostname,
                None,
            )

            for result in resolved_ips:

                resolved_ip = result[4][0]

                ip = ipaddress.ip_address(
                    resolved_ip
                )

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                ):
                    return False

        except socket.gaierror:
            return False

    return True


@tool
def fetch_article(url: str) -> str:
    """
    Fetch readable text from a news article URL.

    Use this tool when the agent needs to inspect
    the content of a specific news article.

    Input:
        url: The URL of the article.

    Output:
        Clean article text or an error message.
    """

    if not url or not url.strip():
        return "Error: URL cannot be empty."

    url = url.strip()

    if not _is_safe_url(url):
        return (
            "Error: URL is not allowed "
            "for security reasons."
        )

    try:

        response = requests.get(
            url,
            timeout=ARTICLE_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "AI-News-Research-Agent"
                )
            },
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for element in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        if not text:
            return (
                "Error: No readable article "
                "content found."
            )

        text = text[:MAX_CONTENT_LENGTH]

        return text

    except requests.Timeout:
        return (
            "Error: Article request timed out. "
            "Please try again later."
        )

    except requests.RequestException as error:
        return (
            f"Error: Article request failed: "
            f"{str(error)}"
        )

    except Exception as error:
        return (
            f"Error: Unexpected article tool failure: "
            f"{str(error)}"
        )