import csv
import os
import time
from httpcore import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

INPUT_FILENAME = "ga4gh_related_articles_citation_counts.csv"
OUTPUT_FILENAME = "ga4gh_related_articles_citation_counts_scraped.csv"
OUTPUT_HEADER = ["id","source", "hit_count", "scrape_url", "scrape_citation_count"]
URL_TEMPLATE = "https://europepmc.org/article/{source}/{id}"

def main():
    input_file = os.path.join("data", INPUT_FILENAME)
    output_file = os.path.join("data", OUTPUT_FILENAME)
    ifh = open(input_file, 'r')
    ofh = open(output_file, 'w')
    reader = csv.DictReader(ifh)
    writer = csv.DictWriter(ofh, fieldnames=OUTPUT_HEADER)

    writer.writeheader()

    driver = webdriver.Chrome() 
    
    row_n = 0
    for row in reader:
        row["scrape_url"] = URL_TEMPLATE.format(**row)
        row['scrape_citation_count'] = "NA"

        driver.get(row['scrape_url'])

        try:
            element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "impact")))
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()

            time.sleep(2)

            row["scrape_citation_count"] = driver.find_elements(By.CLASS_NAME, "feature-large")[0].text
        except TimeoutException:
            pass
        except Exception:
            pass
        finally:
            writer.writerow(row)
            print(f"Row {row_n} processed")
            row_n += 1
        
    driver.quit()
    ifh.close()
    ofh.close()

    print("Finished. All rows processed")

if __name__ == "__main__":
    main()