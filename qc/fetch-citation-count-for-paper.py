import requests
import sys

def main():
    pmid = sys.argv[1] if len(sys.argv) > 1 else input("Please enter the PMID of the paper you want to fetch the citation count for: ")
    
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/citations?format=json"
    response = requests.get(url)

    if response.status_code == 200:
        response_dict = response.json()
        hit_count = response_dict.get('hitCount', 0)
        print(f"{hit_count} papers have cited the paper with PMID {pmid}.")
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

if __name__ == "__main__":
    main()