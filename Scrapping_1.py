import requests
from bs4 import BeautifulSoup

url = "https://librarius.md/ro/catalog/tops"

# Make an HTTP GET request
response = requests.get(url)

# Check if the request was successful (status code 200 means OK)
if response.status_code == 200:
    print("Request Successful!")
    html_content = response.text  # The HTML content of the webpage
else:
    print(f"Failed to retrieve the webpage. Status Code: {response.status_code}")
    html_content = ""

soup = BeautifulSoup(html_content, 'html.parser')

products = []

# Find all product containers
product_containers = soup.find_all('div', class_='anyproduct-card')

# Helper function to validate price
def is_valid_price(price):
    try:
        # Remove non-numeric characters (e.g., "lei" currency) and convert to float
        price_value = float(price.replace("lei", "").strip())
        return price_value > 0  # Only valid if price is greater than 0
    except ValueError:
        return False

# Loop through products and extract name, price, and link
for product in product_containers:
    # Extract product name
    product_name_element = product.find('div', class_='card-title')
    product_price_element = product.find('div', class_='card-price')
    product_link_element = product.find('a', href=True)

    # Check if product name is found
    if product_name_element:
        product_name = product_name_element.text.strip()
    else:
        print("Product name not found.")
        product_name = ""

    # Check if product price is found
    if product_price_element:
        product_price = product_price_element.text.strip()
    else:
        print("Product price not found.")
        product_price = ""

    # Check if product link is found
    if product_link_element:
        product_link = product_link_element['href']
    else:
        print("Product link not found.")
        product_link = ""

    # --- Validation 1: Ensure product name is not empty ---
    if not product_name:
        print("Invalid product: Product name is empty.")
        continue  # Skip storing this product

    # --- Validation 2: Ensure price is valid (number and greater than 0) ---
    if not is_valid_price(product_price):
        print(f"Invalid product: Price '{product_price}' is not valid.")
        continue  # Skip storing this product

    # Scrape the product link to get the author's info
    if product_link:
        # Make a second request to the product link
        product_response = requests.get(product_link)
        if product_response.status_code == 200:
            product_soup = BeautifulSoup(product_response.text, 'html.parser')

            # Extract the author's information from the meta tag
            author_meta = product_soup.find('meta', property='book:author')
            author_name = author_meta['content'] if author_meta else "Author not found."
        else:
            author_name = "Failed to load product page."

    # If all validations pass, add the product info to the list as a dictionary
    products.append({
        "name": product_name,
        "price": product_price,
        "link": product_link,
        "author": author_name  # New additional data
    })

# Print all valid products
for p in products:
    print(f"Product Name: {p['name']}, Product Price: {p['price']}, Product Link: {p['link']}, Author: {p['author']}")
