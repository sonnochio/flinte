import arxiv
import csv

# Fetch papers from ArXiv
def fetch_arxiv_papers(keyword, max_results=100):
    search = arxiv.Search(
        query=keyword,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    return [
        {
            "id": result.entry_id,
            "title": result.title,
            "summary": result.summary,
            "authors": [author.name for author in result.authors],
            "published": result.published
        }
        for result in search.results()
    ]

# Save data to CSV
def save_to_csv(data, filename, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

# Main logic
if __name__ == "__main__":
    print("Fetching papers...")
    papers = fetch_arxiv_papers("AI architecture", max_results=50)
    print(f"Fetched {len(papers)} papers.")
    
    # Save papers to CSV
    save_to_csv(
        papers,
        "arxiv_papers.csv",
        fieldnames=["id", "title", "summary", "authors", "published"]
    )
