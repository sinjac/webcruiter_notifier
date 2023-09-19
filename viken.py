#!/usr/bin/env python3
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import enum
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass, InitVar, field


@dataclass
class JobAdOverview:
    job_element: InitVar[WebElement]
    webcruiter_id: str = field(init=False)
    href: str = field(init=False)
    heading: str = field(init=False)
    city: str = field(init=False)
    published: str = field(init=False)
    deadline: str = field(init=False)

    def __post_init__(self, job_element: WebElement):
        self.webcruiter_id = job_element.get_attribute("id")
        self.href = job_element.get_attribute("href")
        self.heading = self.__get_ad_title(job_element)
        self.city = self.__get_city_name(job_element)
        self.published = self.__get_published_date(job_element)
        self.deadline = self.__get_deadline(job_element)

    def __get_ad_title(self, job_element: WebElement):
        title_element = job_element.find_element(By.XPATH, './/div[starts-with(@data-bind, "text:Heading")]')
        return title_element.text

    def __get_city_name(self, job_element: WebElement):
        city_element = job_element.find_element(By.XPATH, './/span[starts-with(@data-bind, "text:Workplace")]')
        return city_element.text

    def __get_published_date(self, job_element: WebElement):
        published_element = job_element.find_element(By.XPATH, './/span[starts-with(@data-bind, "shortDate:PublishedDate")]')
        return published_element.text

    def __get_deadline(self, job_element: WebElement):
        deadline_group = job_element.find_element(By.XPATH, './/div[starts-with(@data-template, "advert-status")]')
        return self.__find_visible_deadline_option(deadline_group).text

    def __find_visible_deadline_option(self, deadline_group: WebElement):
        deadline_options = ["ThreeDaysLeft", "TwoDaysLeft", "LastChance", "HourLeft", "Deadline"]
        deadline_elements = [deadline_group.find_element(By.XPATH, f'.//div[starts-with(@data-bind, "visible:{deadline_option}")]') for deadline_option in deadline_options]
        return list(filter(lambda deadline_element: deadline_element.is_displayed(), deadline_elements))[0]

class Discipline(enum.Enum):
    administration = "Administrasjon"
    other_health = "Andre helsefagselt"
    other_engineering = "Andre ingeniørfag"
    customer_service_ict = "Brukerstøtte, IKT"
    human_resources = "HR"
    customer_and_client_care = "Kunde- og klientbehandling"
    customer_care = "Kundebehandling"
    leadership = "Ledelse"
    networking_and_systems_engineering_ict = "Nettverks- og systemtekniske fag, IKT"
    finance = "Regnskap"
    cleaning = "Renhold"
    restaurant = "Restaurant"
    teaching_and_training = "Undervisning og opplæring"

class WebCruiterAutomation:

    def __init__(self, webcruiter_url: str, firefox_path: str = "/usr/bin/firefox", timeout: float=10.0):
        self.__options = Options()
        self.__options.binary_location = firefox_path
        self.__options.add_argument("--headless")
        self.__timeout = timeout
        self.__webcruiter_url = webcruiter_url

    def load_page(function_candidate: callable):
        def wait_until_loaded(self, *args, **kwargs):
            try:
                loading_modal = self.__browser.find_element(By.ID, 'loadingModal')
                self.wait.until(EC.invisibility_of_element(loading_modal))
            except NoSuchElementException:
                pass

            return function_candidate(self, *args, **kwargs)

        return wait_until_loaded

    @load_page
    def __press_button(self, search_type: str, button_name: str):
        button_field = self.__browser.find_element(search_type, button_name)
        button_field.click()

    @load_page
    def __write_field(self, search_type: str, field_name: str, field_value: str):
        writeable_field = self.__browser.find_element(search_type, field_name)
        writeable_field.send_keys(field_value)

    @load_page
    def __select_field(self, search_type: str, field_name: str):
        select_field = self.__browser.find_element(search_type, field_name)
        self.__browser.execute_script("arguments[0].scrollIntoView();", select_field)
        if not select_field.is_selected():
            select_field.click()

    def login(self, email: str, password: str):
        try:
            self.__press_button(By.LINK_TEXT, "Logg inn")
            self.__write_field(By.ID, "Start_Email", email)
            self.__press_button(By.ID, "start-next-button")
            self.__write_field(By.ID, "Login_Password_show", password)
            self.__press_button(By.ID, "login-next-button")
        except TimeoutException as e:
            print(e)

    def filter_by(self, discipline: Discipline):
        if not isinstance(discipline, Discipline):
            raise ValueError

        try:
            self.__press_button(By.XPATH, f'//span[starts-with(@aria-label, "Vis Fagfelt")]')
        except ElementNotInteractableException:
            pass
        finally:
            self.__select_field(By.XPATH, f'//input[starts-with(@aria-label, "{discipline.value}")]')

    def show_all_jobs(self):
        element_to_find =  f'button[data-bind="click:loadMore,enter:loadMore,space:loadMore"]'
        while True:
            try:
                self.__press_button(By.CSS_SELECTOR, element_to_find)
            except  ElementNotInteractableException:
                break

    @load_page
    def get_all_ad_overviews(self):
        job_elements = self.__browser.find_elements(By.XPATH, '//a[starts-with(@id, "item")]')
        return [JobAdOverview(job_element) for job_element in job_elements]

    def __enter__(self):
        self.__browser = webdriver.Firefox(options=self.__options)
        self.__browser.maximize_window()
        self.__browser.get(self.__webcruiter_url)
        self.wait = WebDriverWait(self.__browser, self.__timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__browser.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically retrieves all jobs from within a certain category on webcruiter.")
    parser.add_argument("--email", help="Enter an email", type=str)
    parser.add_argument("--password", help="Enter a password", type=str)
    parser.add_argument("--url", default="https://candidate.webcruiter.com/nb-no/home/companyadverts?companylock=906050#search", help="Enter a url to webcruiter", type=str)

    args = parser.parse_args()

    with WebCruiterAutomation(args.url) as webcruiter_bot:
        if args.email and args.password:
            webcruiter_bot.login(args.email, args.password)

        webcruiter_bot.filter_by(Discipline.teaching_and_training)
        webcruiter_bot.filter_by(Discipline.leadership)
        webcruiter_bot.show_all_jobs()
        advertisements = webcruiter_bot.get_all_ad_overviews()
        for ad in advertisements:
            print(ad, "\n")
