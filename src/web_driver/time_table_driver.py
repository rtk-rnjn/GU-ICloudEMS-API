from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .driver import WebDriver


class TimeTableDriver(WebDriver):
    def click_button(self) -> None:
        self._click_timetable_icon()

    def _click_timetable_icon(self):
        self.wait_for_preloader()
        href = "schedulerand/tt_report_view.php"
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{href}']")))
        element = self.driver.find_element(By.XPATH, f"//a[@href='{href}']")

        element.click()
