import requests
import xmltodict
import csv
import os

SEARCH_TERM="GA4GH"
OUTPUT_HEADER=["id","source", "hit_count"]
OUTPUT_FILENAME="ga4gh_related_articles_citation_counts.csv"

def get_next_page_url(response_dict):
    if 'responseWrapper' in response_dict.keys() and 'nextPageUrl' in response_dict['responseWrapper'].keys():
        return response_dict['responseWrapper']['nextPageUrl']
    return None

def process_single_result(result):
    id = result['id']
    source = result['source']
    hit_count = 0

    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{id}/citations?format=json"
    response = requests.get(url)
    if response.status_code == 200:
        hit_count = response.json().get('hitCount', 0)

    return {
        "id": id,
        "source": source,
        "hit_count": hit_count
    }

if __name__ == "__main__":
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={SEARCH_TERM}"
    response = requests.get(url)
    page = 1
    output_file = os.path.join("data", OUTPUT_FILENAME)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_HEADER)
        writer.writeheader()

        while url:
            response = requests.get(url)
            if response.status_code == 200:
                response_dict = xmltodict.parse(response.content)
                url = get_next_page_url(response_dict)
                
                if response_dict['responseWrapper']['resultList']:
                    for result in response_dict['responseWrapper']['resultList']['result']:
                        row = process_single_result(result)
                        writer.writerow(row)
                        
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
            
            print(f"Running. Page {page} processed")
            page += 1
        
        print(f"Finished. All pages processed")
