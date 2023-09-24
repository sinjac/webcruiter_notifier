#!/usr/bin/env python3
import viken.ad_overview as overview
import viken.ad_details as details
import datetime
import time
import enum
import argparse
import requests

class JobNotifier:
    def __init__(self, apikey: str):
        self.apikey = apikey
        self.jobs = {}

    def run(self, course_filters: list[str], employment_percentage: float=50.0):
        while True:
            all_jobs = {ad.id: ad for ad in self.__get_viken_overviews()}
            new_ads = [ad_overview for ad_id, ad_overview in all_jobs.items() if not ad_id in self.jobs]
            existing_ads = {ad_id: ad_details for ad_id, ad_details in self.jobs.items() if ad_id in all_jobs}

            new_ads_details = details.get_job_listings(new_ads)
            filtered_new_ads = self.__filter_new_ads(new_ads_details, course_filters, employment_percentage)

            self.__send_ad_notifications(filtered_new_ads)

            print("\n\nExisting Ads:")
            for id in self.jobs:
                print(id)

            self.jobs = {**existing_ads, **filtered_new_ads}
            self.__sleep_until_next_datetime()

    def __get_viken_overviews(self, url: str = "https://candidate.webcruiter.com/nb-no/home/companyadverts?companylock=906050#search"
 ):
        homepage_parser = overview.WebcruiterHomepageParser(url)
        homepage_parser.filter_by(overview.Discipline.teaching_and_training)
        homepage_parser.show_all_jobs()
        ads = homepage_parser.get_all_ad_overviews()
        del homepage_parser
        return ads

    def __filter_new_ads(self, new_ads: list[details.JobDetails], course_filters: list[str], employment_percentage_limit: float):
        ad_details = {}
        for ad in new_ads:
            if any(course in ad.job_title.lower() for course in course_filters) and employment_percentage_limit <= ad.employment_percentage:
                ad_details[ad.id] = ad

        return ad_details

    def __send_ad_notifications(self, new_ads: dict[int, details.JobDetails]):
        print("\n\nNew Ads:")
        for new_ad in new_ads.values():
            print(new_ad.id)
            self.__send_notification(new_ad)
            time.sleep(1)

    def __send_notification(self, ad: details.JobDetails):
        requests.post("https://api.mynotifier.app", {
            "apiKey": self.apikey,
            "message": f"New Job: {ad.id}",
            "description": f"Title: {ad.job_title}\nPercentage: {ad.employment_percentage}\nJob Type: {ad.job_type}\nEmployment Type: {ad.employment_type}\nDeadline: {ad.deadline}\nLink: {ad.href}",
            "type": "info"
        })

    def __slep_until_next_datetime(self):
        sleep_duration = self.__get_sleepduration()
        time.sleep(sleep_duration)

    def __get_sleepduration(self, startup_time: datetime.time = datetime.time(hour=18,minute=0), frequency: datetime.timedelta = datetime.timedelta(days=1)):
        next_date = datetime.date.today() + frequency
        target_datetime = datetime.datetime.combine(next_date, startup_time)
        return (target_datetime - datetime.datetime.now()).total_seconds()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notify about jobs in webcruiter")
    parser.add_argument("apikey", help="Enter an api key for mynotifier ", type=str)
    args = parser.parse_args()

    job_notifier = JobNotifier(args.apikey)
    course_filter = ["engelsk", "samfunnsfag", "samfunnskunnskap", "sosiologi", "sosialantropologi", "sosialkunnskap"]
    job_notifier.run(course_filter)
