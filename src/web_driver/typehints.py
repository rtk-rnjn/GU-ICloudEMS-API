from __future__ import annotations

from typing import TypedDict


class SeleniumConfig(TypedDict):
    selenium_args: list[str]
    login_page_endpoint: str
    input_username_id: str
    input_password_id: str
    login_button_id: str
    external_javascript: str
