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

# Assuming `html_content` is the HTML we fetched earlier
soup = BeautifulSoup(html_content, 'html.parser')

# List to store product information
products = []

# Find all product containers (this is based on the provided HTML structure)
product_containers = soup.find_all('div', class_='anyproduct-card')

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
        product_name = "N/A"

    # Check if product price is found
    if product_price_element:
        product_price = product_price_element.text.strip()
    else:
        print("Product price not found.")
        product_price = "N/A"

    # Check if product link is found
    if product_link_element:
        product_link = product_link_element['href']
    else:
        print("Product link not found.")
        product_link = "N/A"

    # Add the product info to the list as a dictionary
    products.append({
        "name": product_name,
        "price": product_price,
        "link": product_link
    })

# Print all products
for p in products:
    print(f"Product Name: {p['name']}, Product Price: {p['price']}, Product Link: {p['link']}")
