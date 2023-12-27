from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .driver import WebDriver


class ProfileDriver(WebDriver):
    def click_button(self) -> None:
        self._click_profile()

    def _click_profile(self):
        self.wait_for_preloader()
        href = "/corecampus/student/myprofile/myprofile_nw.php"

        img = self.driver.find_element(By.CLASS_NAME, "rounded-circle")
        img.click()

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{href}']")))
        element = self.driver.find_element(By.XPATH, f"//a[@href='{href}']")

        element.click()
