import requests

def fetch_publications(keyword, limit=10000):
    sparql_endpoint = "https://opencitations.net/sparql"
    query = f"""
    PREFIX dcterms: <http://purl.org/dc/terms/>
    SELECT ?work ?title
    WHERE {{
        ?work dcterms:title ?title .
        FILTER(CONTAINS(LCASE(?title), "{keyword.lower()}"))
    }}
    LIMIT {limit}
    """
    response = requests.get(sparql_endpoint, params={'query': query, 'format': 'json'})
    
    # Debugging: Print the status code and response text
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    # Check if response is successful
    if response.status_code != 200:
        raise Exception(f"SPARQL query failed with status code {response.status_code}")
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON. Response content:")
        print(response.text)
        return None

# Call the function
fetch_publications("AI architecture")
