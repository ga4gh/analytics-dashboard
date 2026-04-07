import requests
import xmltodict
import json

SEARCH_QUERY = '''(("GA4GH" OR "Global Alliance for Genomics and Health") NOT (PUB_TYPE:("published erratum")))'''

def get_next_page_url(response_dict):
    if 'responseWrapper' in response_dict.keys() and 'nextPageUrl' in response_dict['responseWrapper'].keys():
        return response_dict['responseWrapper']['nextPageUrl']
    return None

def main():
    ga4gh_related_articles_count = 0
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" + SEARCH_QUERY
    
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = xmltodict.parse(response.content)
            url = get_next_page_url(response_dict)
            
            if response_dict['responseWrapper']['resultList']:
                ga4gh_related_articles_count += len(response_dict['responseWrapper']['resultList']['result'])

        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")

        print(f"Running total of GA4GH related articles: {ga4gh_related_articles_count}")
    
    print(f"Total number of GA4GH related articles: {ga4gh_related_articles_count}")

if __name__ == "__main__":
    main()