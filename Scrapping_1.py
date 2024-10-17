import socket
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from functools import reduce
import ssl

# Conversion rates
MDL_TO_EUR = 1 / 19.5  # Example rate: 1 MDL/lei = 0.051 EUR
EUR_TO_MDL = 19.5  # Example rate: 1 EUR = 19.5 MDL/lei


# Helper function to clean the price string
def clean_price(price):
    cleaned_price = ''.join(filter(lambda x: x.isdigit() or x in ['.', ' '], price))
    return cleaned_price.replace(" ", "")  # Remove spaces for float conversion


# Updated is_valid_price function
def is_valid_price(price):
    cleaned_price = clean_price(price)
    try:
        price_value = float(cleaned_price)
        return price_value > 0  # Only valid if price is greater than 0
    except ValueError:
        return False


# Updated convert_price function
def convert_price(price, target_currency="EUR"):
    price_value = 0
    cleaned_price = clean_price(price)

    if "EUR" in price:
        price_value = float(cleaned_price.replace("EUR", "").strip())
        if target_currency in ["MDL", "lei"]:
            return price_value * EUR_TO_MDL  # Convert EUR to MDL/lei
    elif "lei" in price or "MDL" in price:
        price_value = float(cleaned_price.replace("lei", "").replace("MDL", "").strip())
        if target_currency == "EUR":
            return price_value * MDL_TO_EUR  # Convert lei to EUR
    return price_value  # Return the price value


# Function to filter products based on price range
def filter_by_price(product, min_price, max_price, currency="MDL"):
    price_in_mdl = convert_price(product['price'], currency)
    return min_price <= price_in_mdl <= max_price


# Function to send HTTP request and get response using a TCP socket
def get_http_response(host, path, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as secure_sock:
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            secure_sock.sendall(request.encode())

            response = b""
            while True:
                chunk = secure_sock.recv(4096)
                if not chunk:
                    break
                response += chunk

    # Split the response into headers and body
    headers, body = response.split(b'\r\n\r\n', 1)
    return body.decode('utf-8')


# Scrape the webpage and get product data
url = "https://librarius.md/ro/catalog/tops"
host = "librarius.md"
path = "/ro/catalog/tops"

html_content = get_http_response(host, path)

soup = BeautifulSoup(html_content, 'html.parser')
products = []

# Find all product containers
product_containers = soup.find_all('div', class_='anyproduct-card')

# Loop through products and extract name, price, and link
for product in product_containers:
    product_name_element = product.find('div', class_='card-title')
    product_price_element = product.find('div', class_='card-price')
    product_link_element = product.find('a', href=True)

    product_name = product_name_element.text.strip() if product_name_element else ""
    product_price = product_price_element.text.strip() if product_price_element else ""
    product_link = product_link_element['href'] if product_link_element else ""

    # Scrape product page for author
    author_name = "Author not found."
    if product_link:
        product_html = get_http_response(host, product_link)
        product_soup = BeautifulSoup(product_html, 'html.parser')
        author_meta = product_soup.find('meta', property='book:author')
        author_name = author_meta['content'] if author_meta else "Author not found."

    # Validate and add product if the price is valid
    if is_valid_price(product_price):
        products.append({
            "name": product_name,
            "price": product_price,
            "link": product_link,
            "author": author_name
        })

# Map prices to EUR
mapped_products = list(map(lambda p: {**p, 'price_EUR': convert_price(p['price'], "EUR")}, products))

# Filter products by price range
filtered_products = list(filter(lambda p: filter_by_price(p, 50, 500, currency="lei"), mapped_products))

# Use reduce to sum the prices of the filtered products
total_price = reduce(lambda acc, p: acc + convert_price(p['price'], "lei"), filtered_products, 0)

# Attach the sum and UTC timestamp to the data structure
result = {
    "products": filtered_products,
    "total_price": total_price,
    "timestamp": datetime.now(pytz.utc).isoformat()
}

print(result)