import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import time

def crawl_website(start_url):
    """
    Recursively crawls a website starting from a given URL to find all unique links
    within the same domain.

    Args:
        start_url (str): The URL to begin crawling from.

    Returns:
        list: A sorted list of unique URLs found on the website.
    """
    # Use a set to store URLs to visit to avoid duplicates and for efficient lookups.
    urls_to_visit = {start_url}
    # Use a set to keep track of visited URLs to prevent re-crawling and infinite loops.
    visited_urls = set()
    
    # Get the base domain to ensure we only crawl links within the same website.
    # e.g., for 'https://docs.example.com/page/1', the domain is 'docs.example.com'
    domain_name = urlparse(start_url).netloc
    
    print(f"Starting crawl at: {start_url}")
    print(f"Restricting to domain: {domain_name}\n")

    while urls_to_visit:
        # Get the next URL to process.
        current_url = urls_to_visit.pop()
        
        # Skip if we have already visited this URL.
        if current_url in visited_urls:
            continue
            
        print(f"Crawling: {current_url}")
        visited_urls.add(current_url)

        try:
            # Set a timeout to avoid hanging on unresponsive pages.
            response = requests.get(current_url, timeout=5)
            # Raise an exception for bad status codes (4xx or 5xx).
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Could not retrieve {current_url}. Reason: {e}")
            continue

        # Parse the HTML content of the page.
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags with an 'href' attribute.
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Use urljoin to handle relative URLs (e.g., '/page.html').
            # This will correctly combine the base URL with the relative link.
            full_url = urljoin(current_url, href)

            # Clean the URL by removing fragments (#) and query parameters (?).
            parsed_full_url = urlparse(full_url)
            full_url = parsed_full_url._replace(query="", fragment="").geturl()

            # Check four conditions:
            # 1. The link belongs to the same domain.
            # 2. The link starts with the original start_url (same path hierarchy).
            # 3. The link has not been visited yet.
            # 4. The link is not already in our queue to visit.
            if (domain_name in full_url and 
                full_url.startswith(start_url) and 
                full_url not in visited_urls and 
                full_url not in urls_to_visit):
                urls_to_visit.add(full_url)
                
        # A small delay to be polite to the server and avoid getting blocked.
        time.sleep(0.1)

    print("\nCrawl complete!")
    return sorted(list(visited_urls))

if __name__ == "__main__":
    # Ensure a starting URL is provided as a command-line argument.
    if len(sys.argv) > 1:
        root_url = sys.argv[1]
    else:
        # If no argument is given, prompt the user for input.
        root_url = input("Please enter the root URL to start parsing: ")

    if not root_url.startswith('http'):
        print("Error: Please provide a valid URL (e.g., 'https://example.com').")
    else:
        all_links = crawl_website(root_url)
        
        # Save the collected links to a text file.
        output_filename = f"{urlparse(root_url).netloc}_links.txt"
        with open(output_filename, 'w') as f:
            for link in all_links:
                f.write(f"{link}\n")
        
        print(f"\nFound {len(all_links)} unique links.")
        print(f"Results saved to: {output_filename}")
