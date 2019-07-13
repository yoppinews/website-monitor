# -*- coding: utf-8 -*-
from __future__ import annotations

import dataclasses

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


@dataclasses.dataclass(frozen=True)
class WebDriverWrapperFindElementResult:
    url: str
    title: str
    selector: str
    selected_text: str


class WebDriverWrapper:
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument("--log-level=0")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-gpu')
        options.add_argument("--disable-application-cache")
        options.add_argument('--disable-popup-blocking')
        options.add_argument("--disable-infobars")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--enable-logging")
        options.add_argument("--v=99")
        options.add_argument("--single-process")
        options.add_argument("--ignore-certificate-errors")
        options.binary_location = "/opt/bin/headless-chromium"
        self._web_driver = Chrome(executable_path="/opt/bin/chromedriver", chrome_options=options)

    def find_element(self, url: str, selector: str) -> WebDriverWrapperFindElementResult:
        self._web_driver.get(url)
        WebDriverWait(self._web_driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'body')))
        WebDriverWait(self._web_driver, 10).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, selector)))
        return WebDriverWrapperFindElementResult(
            url=self._web_driver.current_url,
            title=self._web_driver.title,
            selector=selector,
            selected_text=self._web_driver.find_element_by_css_selector(selector).text,
        )
