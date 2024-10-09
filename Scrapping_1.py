import requests
from bs4 import BeautifulSoup

url = "https://999.md/ro/list/animals-and-plants/dogs"

# Make an HTTP GET request
response = requests.get(url)

# Check if the request was successful (status code 200 means OK)
if response.status_code == 200:
    print("Request Successful!")
    html_content = response.text  # The HTML content of the webpage
    print(html_content)  # Print a snippet of the HTML content
else:
    print(f"Failed to retrieve the webpage. Status Code: {response.status_code}")

# Assuming `html_content` is the HTML we fetched earlier
soup = BeautifulSoup(html_content, 'html.parser')

# List to store product information
products = []

# Find all product containers (update with the actual HTML structure)
product_containers = soup.find_all('li', class_='ads-list-photo-item')

# Loop through products and extract name and price
for product in product_containers:
    # Extract product name
    product_name_element = product.find('div', class_='ads-list-photo-item-title')
    product_price_element = product.find('div', class_='ads-list-photo-item-price')

    # Check if product name is found
    if product_name_element:
        product_name = product_name_element.text.strip()
    else:
        print("Product name not found.")
        product_name = "N/A"  # or continue to the next product

    # Check if product price is found
    if product_price_element:
        product_price = product_price_element.text.strip()
    else:
        print("Product price not found.")
        product_price = "N/A"  # or continue to the next product

    # Add the product info to the list as a dictionary
    products.append({
        "name": product_name,
        "price": product_price
    })

# Print all products
for p in products:
    print(f"Product Name: {p['name']}, Product Price: {p['price']}")