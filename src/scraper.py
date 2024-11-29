# %%
# Import necessary libraries
import tldextract
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import csv
import time

# %%
# Download NLTK data files (run once)
nltk.download("punkt")
nltk.download("stopwords")

# %%
def retrieve_domains(url):
    """
    Extract the domain from a URL using tldextract.
    """
    url_parts = tldextract.extract(url)
    domain = f"{url_parts.domain}.{url_parts.suffix}"
    return domain

def search_scrape(keyword, headers, unwanted_domains):
    """
    Scrape Google search results for a given keyword, ensuring 10 URLs are collected.
    """
    query_str = keyword
    queries_dict = {}
    collected_count = 0
    start = 0

    while collected_count < 10:
        search_q_url = f"https://www.google.com/search?q={query_str}&num=10&start={start}"
        try:
            response = requests.get(search_q_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Find search result blocks
            queries = soup.find_all("div", class_="tF2Cxc")
            for query in queries:
                if collected_count >= 10:
                    break

                try:
                    search_url = query.find("a")["href"]
                    domain = retrieve_domains(search_url)

                    # Exclude unwanted domains and image results
                    if (
                        "imgres" in search_url or
                        any(unwanted_domain in domain for unwanted_domain in unwanted_domains)
                    ):
                        continue

                    search_title = query.find("h3").text.strip()
                    queries_dict[search_url] = search_title
                    collected_count += 1

                except Exception as e:
                    print(f"Error processing a query: {e}")

            start += 10  # Move to the next page
            time.sleep(2)  # Add a delay to avoid being blocked

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {search_q_url}: {e}")
            break

    return queries_dict

def extract_all_text(url, headers):
    """
    Extract all visible text from the header, description, and main content of a webpage.
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract text content from relevant sections
        header_text = " ".join([h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4"])])
        description_text = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
        main_content_text = soup.get_text(separator=" ", strip=True)

        # Combine all text
        combined_text = f"{header_text} {description_text} {main_content_text}".lower()
        combined_text = re.sub(r"[^\w\s]", "", combined_text)  # Remove punctuation
        return combined_text

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_keywords(text):
    """
    Extract frequently occurring words/phrases from the given text.
    """
    try:
        # Tokenize and remove stopwords
        words = word_tokenize(text)
        stop_words = set(stopwords.words("english"))
        custom_stop_words = {"page", "home", "click", "website", "read", "please", "visit"}
        stop_words.update(custom_stop_words)

        filtered_words = [word for word in words if word not in stop_words]

        # Count word frequencies
        word_freq = Counter(filtered_words)
        return [word for word, freq in word_freq.most_common(10)]  # Return top 10 keywords

    except Exception as e:
        print(f"Error processing text: {e}")
        return []

def save_to_csv(data, filename):
    """
    Save the data to a CSV file.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Website URL", "All Text", "Keywords"])  # Updated header
        for row in data:
            writer.writerow(row)

# %%
# Parameters
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
unwanted_domains = [
    "amazon.com", "ebay.com", "etsy.com", "alibaba.com", "madeinchina.com", "marketplace"
]
keywords = ["Sublimated Ribbons", "Running Medals"]

# %%
# Main execution
output_data = []

for keyword in keywords:
    print(f"Processing keyword: {keyword}")
    search_results = search_scrape(keyword, headers, unwanted_domains)

    for url, title in search_results.items():
        print(f"\nURL: {url}")
        print(f"Title: {title}")
        
        # Extract all text from the webpage
        full_text = extract_all_text(url, headers)
        
        # Extract keywords from the text
        top_keywords = extract_keywords(full_text)
        print("Top Keywords:", top_keywords)
        
        # Prepare row for CSV
        output_data.append([url, full_text, ", ".join(top_keywords)])  # Include all text and keywords

# %%
# Save the results to a CSV file
csv_filename = "web_scraping_results_full_text.csv"
save_to_csv(output_data, csv_filename)
print(f"Results saved to {csv_filename}")