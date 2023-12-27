from __future__ import annotations

import json
import pathlib
from typing import TYPE_CHECKING, Final

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver as FireFoxWebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

    from .typehints import SeleniumConfig

config_path = pathlib.Path(__file__).parent / "config.json"

with open(config_path, "r") as config_file:
    config: SeleniumConfig = json.load(config_file)

js_path = pathlib.Path(__file__).parent / config["external_javascript"]
js = js_path.read_text(encoding="utf-8", errors="strict")


SELENIUM_ARGS: Final = config["selenium_args"]
GU_ICLOUD_EMS_LOGIN: Final = config["login_page_endpoint"]


class WebDriver:
    def __init__(self, admission_number: str, password: str) -> None:
        options = Options()
        for arg in SELENIUM_ARGS:
            options.add_argument(arg)

        self.__admission_number = admission_number
        self.__password = password

        self.driver = webdriver.Firefox(options=options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(3)

        self.__login_success = False

    def _wait_for(self, cls_name: str, *, timeout: int = 10):
        try:
            element = self.driver.find_element(By.CLASS_NAME, cls_name)
        except NoSuchElementException:
            return

        wait = WebDriverWait(self.driver, timeout)

        def is_display_none(_) -> bool:
            maybe_none = element.value_of_css_property("display")
            return maybe_none == "none"

        wait.until(is_display_none)

    def wait_for_preloader(self) -> None:
        class_name = "preloader-backdrop"
        self._wait_for(class_name)

    def wait_for_swal(self) -> None:
        class_name = "swal2-buttonswrapper swal2-loading"
        self._wait_for(class_name)

    def login(self) -> FireFoxWebDriver:
        self.driver.get(GU_ICLOUD_EMS_LOGIN)

        self._input_and_click(
            self.driver.find_element(By.ID, config["input_username_id"]),
            self.__admission_number,
        )

        self._input_and_click(
            self.driver.find_element(By.ID, config["input_password_id"]),
            self.__password,
        )

        self.driver.execute_script(f"""verify_branch({self.__admission_number!r})""")

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.ID, config["login_button_id"])))

        self.wait_for_preloader()

        submit = self.driver.find_element(By.ID, config["login_button_id"])
        submit.click()

        self.click_button()
        self.driver.execute_script(js)

        self._wait_for("ONE MORE STUPID WAIT", timeout=30)

        self.__login_success = True
        return self.driver

    def download_page_source(self) -> str:
        if not self.__login_success:
            raise RuntimeError("You must login first.")
        else:
            return self.driver.page_source

    def download_page_source_to(self, path: str | pathlib.Path) -> str:
        self.login()

        with open(path, "w") as file:
            file.write(self.download_page_source())

        return str(path)

    def _input_and_click(
        self, element: WebElement, text: str, *, click_enter: bool = False
    ) -> None:
        element.send_keys(text)
        if click_enter:
            element.send_keys(Keys.ENTER)

    def click_button(self) -> None:
        raise NotImplementedError('You must implement "click_button" method.')

    def close(self) -> None:
        self.driver.close()
