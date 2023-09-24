from viken.ad_overview import JobAdOverview, Discipline, WebcruiterHomepageParser
from dataclasses import dataclass, field, InitVar
from datetime import datetime
import enum
import requests
from bs4 import BeautifulSoup

class JobType(enum.Enum):
    none = ""
    part_time = "Deltid"
    full_time = "Heltid"

class EmploymentType(enum.Enum):
    none = ""
    substitute = "Vikariat"
    permanent = "Fast"
    hourly = "Timelønnet"
    engagement = "Engasjement"
    both = "Fast, Vikariat"

@dataclass
class JobDetails:
    overview: InitVar[JobAdOverview]

    id: int = field(init=False)
    deadline: datetime = field(init=False)

    job_title: str = field(init=False)
    job_type: JobType = field(init=False)
    employment_type: EmploymentType = field(init=False)
    employment_percentage: float = field(init=False)

    href: str = field(init=False)

    def __post_init__(self, overview: JobAdOverview):
        response = requests.get(overview.href)
        soup = BeautifulSoup(response.text, "html.parser")
        information = self.__get_key_information(soup)

        self.id = int(information["Webcruiter-ID:"])
        self.job_title = information["Stillingstittel:"]
        self.job_type = JobType(information["Heltid / Deltid:"])
        self.employment_type = EmploymentType(information["Ansettelsesform:"])
        self.employment_percentage = max([float(percentage) for percentage in information["Stillingsprosent:"].split(",")])
        self.href = overview.href
        self.deadline = datetime.strptime(information["Søknadsfrist:"], "%d.%m.%Y")

    def __get_key_information(self, soup: BeautifulSoup) -> dict:
        key_information = {}
        for row in soup.find_all('div', class_='row'):
            try:
                key = row.find('span').text.strip()
                value = row.find('div', class_='col-xs-8 col-sm-7 we-padding key-info-value').text.strip()
                key_information[key] = value
            except AttributeError:
                pass

        return key_information

def get_job_listings(ad_overviews: list[JobAdOverview]):
    job_details = []
    for ad_overview in ad_overviews:
        try:
            job_details.append(JobDetails(ad_overview))
        except KeyError:
            pass
    return job_details

if __name__ == "__main__":
    url="https://candidate.webcruiter.com/nb-no/home/companyadverts?companylock=906050#search"

    homepage_parser = WebcruiterHomepageParser(url)

    homepage_parser.filter_by(Discipline.teaching_and_training)
    homepage_parser.show_all_jobs()
    advertisements = homepage_parser.get_all_ad_overviews()
    job_details = get_job_listings(advertisements)

    for job_detail in job_details:
        print(job_detail, end="\n\n")
