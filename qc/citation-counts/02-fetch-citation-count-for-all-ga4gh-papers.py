import requests
import xmltodict
import csv
import os
import time

SEARCH_TERM='''(("GA4GH" OR "Global Alliance for Genomics and Health") NOT (PUB_TYPE:("published erratum")))'''
OUTPUT_HEADER=["id", "source", "pub_year", "api_url", "hit_count", "citation_count_qc"]
OUTPUT_FILENAME="ga4gh_related_articles_citation_counts.csv"
CITATION_YEAR_COUNTS = {}

def retry_loop(url):
    retry_count = 0
    while retry_count < 3:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            else:
                print(f"Request failed with status code {response.status_code}. Retrying...")
        except Exception as e:
            print(f"Request failed with exception: {e}. Retrying...")

        retry_count += 1
        time.sleep(2)  # Wait for 2 seconds before retrying

    raise Exception("Request failed after 3 retries.")

def get_next_page_url(response_dict):
    if 'responseWrapper' in response_dict.keys() and 'nextPageUrl' in response_dict['responseWrapper'].keys():
        return response_dict['responseWrapper']['nextPageUrl']
    return None

def process_single_result(result):
    id = result['id']
    source = result['source']
    pub_year = str(result.get('pubYear', 'NA'))
    api_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{id}/citations?format=json"
    hit_count = 0
    citation_count_qc = 0

    response = retry_loop(api_url)
    if response.status_code == 200:
        response_json = response.json()
        hit_count = response_json.get('hitCount', 0)

        if hit_count > 0:
            page = 1
            citation_list = response_json.get('citationList', {}).get('citation', [])

            while len(citation_list) > 0:
                for citation in citation_list:
                    citation_pub_year = str(citation.get('pubYear', 'NA'))
                    if citation_pub_year not in CITATION_YEAR_COUNTS.keys():
                        CITATION_YEAR_COUNTS[citation_pub_year] = 0
                    CITATION_YEAR_COUNTS[citation_pub_year] += 1
                    citation_count_qc += 1

                print(f"\tprocessed {citation_count_qc} of {hit_count} total citations")

                page += 1
                new_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{id}/citations?format=json&page={page}"
                response = retry_loop(new_url)
                response_json = response.json()
                citation_list = response_json.get('citationList', {}).get('citation', [])

    return {
        "id": id,
        "source": source,
        "pub_year": pub_year,
        "api_url": api_url,
        "hit_count": hit_count,
        "citation_count_qc": citation_count_qc
    }

def main():
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={SEARCH_TERM}"
    record_num = 1
    output_file = os.path.join("data", OUTPUT_FILENAME)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_HEADER)
        writer.writeheader()

        while url:
            response = retry_loop(url)
            if response.status_code == 200:
                response_dict = xmltodict.parse(response.content)
                url = get_next_page_url(response_dict)
                
                if response_dict['responseWrapper']['resultList']:
                    for result in response_dict['responseWrapper']['resultList']['result']:
                        print(f"Processing record {record_num}. ID: {result['id']} | Source: {result['source']}")
                        row = process_single_result(result)
                        writer.writerow(row)
                        print(f"Finished record {record_num}. ID: {result['id']} | Source: {result['source']} | Hit Count: {row['hit_count']} | Citation Count QC: {row['citation_count_qc']}")
                        record_num += 1
                        
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
        
        print(f"Finished. All pages processed")
        print(CITATION_YEAR_COUNTS)

if __name__ == "__main__":
    main()
