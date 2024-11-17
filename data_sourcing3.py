import requests
import csv
import os
import time
import feedparser
from tqdm import tqdm

# Constants
ARXIV_API_URL = 'http://export.arxiv.org/api/query'
CROSSREF_API_URL = 'https://api.crossref.org/works/'
PDF_DIR = 'pdfs'  # Directory to save PDFs
REQUEST_DELAY = 1  # Seconds to wait between API requests (to respect rate limits)

# Parameters
ARXIV_MAX_RESULTS = 300  # Number of initial papers to fetch from arXiv
TOTAL_MAX_PAPERS = 1000  # Total number of unique papers desired
ARXIV_SEARCH_QUERY = 'all:machine learning'  # Adjust as needed

def get_arxiv_papers(search_query, start=0, max_results=100):
    """Fetch papers from arXiv based on a search query."""
    print("Fetching initial arXiv papers based on the search query...")
    papers = []
    base_url = f"{ARXIV_API_URL}?search_query={search_query}&start={start}&max_results={max_results}"

    response = requests.get(base_url)
    if response.status_code != 200:
        print("Error fetching data from arXiv API.")
        return papers

    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        paper = {
            'id': entry.get('id', ''),
            'doi': '',  # Will be filled later if available
            'title': entry.get('title', '').replace('\n', ' ').strip(),
            'abstract': entry.get('summary', '').replace('\n', ' ').strip(),
            'authors': ', '.join([author.name for author in entry.get('authors', [])]),
            'published': entry.get('published', ''),
            'categories': entry.get('arxiv_primary_category', {}).get('term', ''),
            'all_categories': ', '.join(t['term'] for t in entry.get('tags', [])),
            'pdf_url': entry.get('id', '').replace('abs', 'pdf') + '.pdf',
            'source': 'arXiv'
        }
        # Check for DOI
        doi = ''
        for link in entry.get('links', []):
            if link.rel == 'related' and 'doi.org' in link.href:
                doi = link.href.split('doi.org/')[1]
                break
        if doi:
            paper['doi'] = doi.lower()
        else:
            paper['doi'] = paper['id'].split('/abs/')[-1]  # Use arXiv ID if DOI not available
        papers.append(paper)
    return papers

def get_crossref_metadata(doi):
    """Fetch metadata and citations for a paper using Crossref API."""
    url = f"{CROSSREF_API_URL}{doi}"
    headers = {'User-Agent': 'YourAppName (mailto:your.email@example.com)'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, []

    data = response.json()
    message = data.get('message', {})
    metadata = {
        'id': message.get('URL', ''),
        'doi': message.get('DOI', '').lower(),
        'title': ' '.join(message.get('title', [])),
        'abstract': message.get('abstract', '').replace('\n', ' ').strip(),
        'authors': ', '.join([' '.join([name.get('given', ''), name.get('family', '')]).strip() for name in message.get('author', [])]),
        'published': '-'.join(map(str, message.get('issued', {}).get('date-parts', [[0, 0, 0]])[0])),
        'categories': ', '.join(message.get('subject', [])),
        'all_categories': ', '.join(message.get('subject', [])),
        'pdf_url': '',
        'source': 'Crossref',
        'publisher': message.get('publisher', '')
    }
    # References (citations)
    references = message.get('reference', [])
    citations = []
    for ref in references:
        ref_doi = ref.get('DOI', '')
        if ref_doi:
            citations.append(ref_doi.lower())
    return metadata, citations

def download_pdf(paper):
    """Download the PDF of a paper from arXiv."""
    if paper['source'] != 'arXiv' or not paper['pdf_url']:
        return False
    pdf_url = paper['pdf_url']
    doi = paper['doi'].replace('/', '_')  # Replace '/' in DOI to avoid file path issues
    pdf_path = os.path.join(PDF_DIR, f"{doi}.pdf")
    if not os.path.exists(pdf_path):
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200:
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            return True
    return False

def main():
    # Step 1: Fetch initial arXiv papers
    initial_papers = get_arxiv_papers(search_query=ARXIV_SEARCH_QUERY, max_results=ARXIV_MAX_RESULTS)
    print(f"Initial arXiv papers fetched: {len(initial_papers)}")

    # Initialize data structures
    papers = {}
    edges = []
    queue = []

    # Add initial papers to the data structures
    for paper in initial_papers:
        doi = paper['doi']
        if doi not in papers:
            papers[doi] = paper
            queue.append(doi)

    # Process papers to collect citations and metadata
    print("Processing papers to collect citations and metadata...")
    with tqdm(total=TOTAL_MAX_PAPERS) as pbar:
        pbar.update(len(papers))
        idx = 0
        while idx < len(queue) and len(papers) < TOTAL_MAX_PAPERS:
            current_doi = queue[idx]
            current_paper = papers[current_doi]
            idx += 1  # Move to the next paper
            # Skip if already processed citations
            if 'citations_fetched' in current_paper:
                continue
            # Fetch citations
            if current_paper['doi']:
                metadata, citations = get_crossref_metadata(current_paper['doi'])
                time.sleep(REQUEST_DELAY)
                if metadata:
                    # Update metadata
                    for key, value in metadata.items():
                        if not current_paper.get(key):
                            current_paper[key] = value
                    # Add citations
                    for cited_doi in citations:
                        edges.append({'source': current_doi, 'target': cited_doi})
                        if cited_doi not in papers and len(papers) < TOTAL_MAX_PAPERS:
                            # Prepare a placeholder for the cited paper
                            cited_paper = {'doi': cited_doi, 'source': 'Crossref'}
                            papers[cited_doi] = cited_paper
                            queue.append(cited_doi)
                            pbar.update(1)
                else:
                    current_paper['citations_fetched'] = True
                    continue
            current_paper['citations_fetched'] = True
            time.sleep(REQUEST_DELAY)

    print(f"Total unique papers collected: {len(papers)}")
    print(f"Total edges (citations) collected: {len(edges)}")

    # Step 2: Write papers and edges to CSV files before downloading PDFs
    print("Writing papers and edges to CSV files...")
    fieldnames = set()
    for paper in papers.values():
        fieldnames.update(paper.keys())
    fieldnames = list(fieldnames)

    with open('papers2.csv', 'w', newline='', encoding='utf-8') as paper_file:
        writer = csv.DictWriter(paper_file, fieldnames=fieldnames)
        writer.writeheader()
        for paper in papers.values():
            writer.writerow(paper)

    with open('citations2.csv', 'w', newline='', encoding='utf-8') as edge_file:
        fieldnames = ['source', 'target']
        writer = csv.DictWriter(edge_file, fieldnames=fieldnames)
        writer.writeheader()
        for edge in edges:
            writer.writerow(edge)

    print("CSV files generated successfully.")

    # Step 3: After CSV files are completed, proceed to download PDFs
    print("Downloading PDFs from arXiv...")
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
    for doi, paper in tqdm(papers.items()):
        if paper['source'] == 'arXiv':
            success = download_pdf(paper)
            if not success:
                print(f"Failed to download PDF for DOI: {paper['doi']}")
            time.sleep(REQUEST_DELAY)

    print("PDF downloads completed.")

if __name__ == '__main__':
    main()
