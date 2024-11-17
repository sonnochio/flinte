import arxiv
import requests

def fetch_crossref_citations(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code} for DOI {doi}")
        return []
    data = response.json()
    references = data.get("message", {}).get("reference", [])
    citations = [{"doi": ref.get("DOI")} for ref in references if ref.get("DOI")]
    return citations


def fetch_arxiv_papers(keyword, max_results=50):
    search = arxiv.Search(
        query=keyword,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers = []
    for result in search.results():
        papers.append({
            "id": result.entry_id,
            "title": result.title,
            "doi": result.doi,
            "authors": [author.name for author in result.authors],
            "abstract": result.summary,
            "published": result.published
        })
    return papers

# Fetch papers related to "AI architecture"
papers = fetch_arxiv_papers("AI architecture", max_results=50)
for paper in papers:
    print(paper["doi"])
    if paper["doi"]!= None:
        info=fetch_crossref_citations(paper["doi"])
        print(info)





