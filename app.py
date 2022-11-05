import csv
import logging
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

class StanScrapper:
    def __init__(self):
        """Start up the browser driver instance."""

        logging.basicConfig(level=logging.INFO)

        options = Options()
        options.headless = True

        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=options)
        logging.info("Browser driver is opened.")

        self.no_email = []
        self.output_data = []
        self.running = False
        
    def get_page(self, uid: int) -> None:
        """
        Direct `driver` to a page based on id (example id: `001`).
        Grab element of interest as `body`.
        """
        url = "https://sejm.gov.pl/Sejm9.nsf/posel.xsp?id={:03d}".format(uid)
        self.driver.get(url)
        self.body = self.driver.find_element(By.ID, "title_content")
        logging.info(f"Browser driver skipped to {uid} page.")


    def get_details(self) -> tuple:
        """Get name, district, party and email of a politician"""
        
        name = self.body.find_element(By.TAG_NAME, "h1").text
        if not name:
            # there are template blank pages at the end, catch it to finish
            self.running = False
            return ()
        
        if self.check_if_rip():
            name = '✝ ' + name
        
        district = self.body.find_element(By.ID, "okreg").text
        
        try:
            party = self.body.find_element(By.CSS_SELECTOR, "a[href*='klub']").text
        except NoSuchElementException:
            party = self.body.find_element(By.XPATH, "//p[@id = 'lblKlub']/following-sibling::p[1]").text

        birth = self.body.find_element(By.ID, "urodzony").text
        age = self.get_age(birth)
        
        try:
            email_link = self.body.find_element(By.PARTIAL_LINK_TEXT, "adres email")
        except NoSuchElementException:
            email = None
            self.no_email.append(name)
        else:
            # email is uncovered after a click
            email_link.click()
            email = email_link.text

        return name, district, party, age, email
    
    def get_age(self, birth_info: str) -> int:
        """Compute politician's age."""
        try:
            bdate, _ = birth_info.split(",")
        except ValueError:
            # There is no birth place given
            bdate = birth_info
        bday, bmonth, byear = [int(x) for x in bdate.split('-')]
        today = date.today()
        age = today.year - byear - ((today.month, today.day) < (bmonth, bday))
        return age

    def check_if_rip(self) -> bool:
        """Check if politician passed away."""
        try:
            self.driver.find_element(By.XPATH, '//*[contains(text(), "Zmarł")]')
        except NoSuchElementException:
            return False
        else:
            return True

    def write_to_csv(self, data: list) -> None:
        """Write gathered output to csv file."""
        header = ["name", "district", "party", "age", "email"]

        try:
            # Create data.csv file if it doesn't exist
            open('data/data.csv', 'x')
        except FileExistsError:
            pass

        with open('data/data.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            for row in data:
                writer.writerow(row)
        logging.info("Data saved successfully to `data/data.csv`.")


    def tear_down(self) -> None:
        """Close a browser driver instance."""
        logging.info("Fetched all, closing browser.")
        self.driver.quit()
        
    def run(self):
        """Loop to run the scrapper and save output."""
        i = 0
        self.running = True

        while self.running:
            i += 1
            self.get_page(i)
            self.output_data.append(self.get_details())

        self.tear_down()
        self.write_to_csv(self.output_data)


if __name__ == '__main__':
    s = StanScrapper()
    s.run()
