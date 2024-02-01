import csv
import logging
import requests
from datetime import date

URL = "https://api.sejm.gov.pl/sejm/term10/MP"


class StanScrapper:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.output_data = []

    def get_data(self) -> None:
        """Use API to get all"""
        data = requests.get(URL).json()
        for mp in data:
            name = mp["firstLastName"]
            district = f"{mp['districtNum']} {mp['districtName']}"
            party = mp["club"]
            age = self.get_age(mp["birthDate"])
            email = mp["email"]
            self.output_data.append((name, district, party, age, email))

    def get_age(self, birth_date: str) -> int:
        """Compute politician's age."""
        bday, bmonth, byear = [int(x) for x in birth_date.split("-")]
        today = date.today()
        age = today.year - byear - ((today.month, today.day) < (bmonth, bday))
        return age

    def write_to_csv(self) -> None:
        """Write gathered output to csv file."""
        header = ["name", "district", "party", "age", "email"]

        try:
            # Create data.csv file if it doesn't exist
            open("data/data.csv", "x")
        except FileExistsError:
            pass

        with open("data/data.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for row in self.output_data:
                writer.writerow(row)
        logging.info("Data saved successfully to `data/data.csv`.")


def drop_column(column: str) -> None:
    """I had to do it."""
    try:
        f = open("data/data.csv", "r")
    except FileExistsError:
        return
    else:
        data = csv.DictReader(f)
        headers = [f for f in data.fieldnames]

    if column not in headers:
        logging.warn(f"{column} not found in csv file.")
        logging.debug(f"Headers found: {headers}")
        return

    d = []
    for row in data:
        row.pop(column)
        d.append(row)

    headers.pop(headers.index(column))
    f.close()

    with open("data/data.csv", "w") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(d)


if __name__ == "__main__":
    s = StanScrapper()
    s.get_data()
    s.write_to_csv()
