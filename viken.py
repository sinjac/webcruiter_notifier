#!/usr/bin/env python3
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import enum
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class JobAdOverview:
    webcruiter_id: str
    href: str
    heading: str
    city: str
    published: str
    deadline: str


class FilterByDiscipline(enum.Enum):
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

    def __wait_until_loaded(self):
        try:
            loading_modal = self.__browser.find_element(By.ID, 'loadingModal')
            self.wait.until(EC.invisibility_of_element(loading_modal))
        except NoSuchElementException:
            pass

    def __wait_until_clickable(self, find_element: str):
        clickable_element = self.__browser.find_element(By.XPATH, find_element)
        self.wait.until(EC.element_to_be_clickable(clickable_element))

    def login(self, email: str, password: str):
        try:
            self.__wait_until_loaded()

            login_webcruiter = self.__browser.find_element(By.LINK_TEXT, "Logg inn")
            login_webcruiter.click()

            self.__wait_until_loaded()

            email_field = self.__browser.find_element("id", "Start_Email")
            email_field.send_keys(email)

            start_next_button = self.__browser.find_element(By.ID, 'start-next-button')
            start_next_button.click()

            self.__wait_until_loaded()

            password_field = self.__browser.find_element("id", "Login_Password_show")
            password_field.send_keys(password)

            login_next_button = self.__browser.find_element(By.ID, 'login-next-button')
            login_next_button.click()

            self.__wait_until_loaded()

        except TimeoutException as e:
            print(e)

    def filter_by(self, filter_by_discipline: FilterByDiscipline):
        if not isinstance(filter_by_discipline, FilterByDiscipline):
            raise ValueError

        self.__wait_until_loaded()
        show_fields = self.__browser.find_element(By.XPATH, f'//span[starts-with(@aria-label, "Vis Fagfelt")]')
        if show_fields.is_displayed():
            show_fields.click()

        element_to_find = f'//input[starts-with(@aria-label, "{filter_by_discipline.value}")]'
        selected_fields = self.__browser.find_element(By.XPATH, element_to_find)
        self.__wait_until_clickable(element_to_find)

        if not selected_fields.is_selected():
            selected_fields.click()
            self.__wait_until_loaded()

    def show_all_jobs(self):
        element_to_find =  f'//button[starts-with(@data-bind, "click:loadMore")]'
        while True:
            try:
                show_more_field = self.__browser.find_element(By.XPATH, element_to_find)
                show_more_field.click()
                self.__wait_until_loaded()
            except  ElementNotInteractableException:
                break

    def get_all_ad_overviews(self):
        job_advertisements = []
        job_elements = self.__browser.find_elements(By.XPATH, '//a[starts-with(@id, "item")]')
        self.__wait_until_loaded()

        for job_element in job_elements:
            job_advertisements.append(self.__get_job_advertisement(job_element))

        return job_advertisements

    def __get_job_advertisement(self, job_element):
        ad_id = job_element.get_attribute("id")
        ad_href = job_element.get_attribute("href")
        ad_title = self.__get_ad_title(job_element)
        city = self.__get_city_name(job_element)
        published_date = self.__get_published_date(job_element)
        deadline = self.__get_deadline(job_element)

        return JobAdOverview(ad_id, ad_href, ad_title, city, published_date, deadline)

    
    def __get_ad_title(self, job_element):
        title_element = job_element.find_element(By.XPATH, './/div[starts-with(@data-bind, "text:Heading")]')
        return title_element.text

    def __get_city_name(self, job_element):
        city_element = job_element.find_element(By.XPATH, './/span[starts-with(@data-bind, "text:Workplace")]')
        return city_element.text

    def __get_published_date(self, job_element):
        published_element = job_element.find_element(By.XPATH, './/span[starts-with(@data-bind, "shortDate:PublishedDate")]')
        return published_element.text

    def __get_deadline(self, job_element):
        deadline_group = job_element.find_element(By.XPATH, './/div[starts-with(@data-template, "advert-status")]')
        deadline_options = ["ThreeDaysLeft", "TwoDaysLeft", "LastChance", "HourLeft", "Deadline"]
        for deadline_option in deadline_options:
            deadline_element = deadline_group.find_element(By.XPATH, f'.//div[starts-with(@data-bind, "visible:{deadline_option}")]')
            if deadline_element.is_displayed():
                return deadline_element.text

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
    parser.add_argument("email", help="Enter an email", type=str)
    parser.add_argument("password", help="Enter a password", type=str)
    parser.add_argument("--url", default="https://candidate.webcruiter.com/nb-no/home/companyadverts?companylock=906050#search", help="Enter a url to webcruiter", type=str)

    args = parser.parse_args()

    with WebCruiterAutomation(args.url) as webcruiter_bot:
        webcruiter_bot.login(args.email, args.password)
        webcruiter_bot.filter_by(FilterByDiscipline.teaching_and_training)
        webcruiter_bot.show_all_jobs()
        advertisements = webcruiter_bot.get_all_ad_overviews()
        for ad in advertisements:
            print(ad, "\n")
