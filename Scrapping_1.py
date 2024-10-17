import socket
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from functools import reduce
import ssl
import re
from pprint import pprint

# Conversion rates
MDL_TO_EUR = 1 / 19.5
EUR_TO_MDL = 19.5


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

# New function for JSON serialization
def to_json(data):
    def serialize(obj):
        if isinstance(obj, dict):
            return "{" + ",".join(f'"{k}":{serialize(v)}' for k, v in obj.items()) + "}"
        elif isinstance(obj, list):
            return "[" + ",".join(serialize(item) for item in obj) + "]"
        elif isinstance(obj, str):
            return f'"{obj}"'
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif obj is None:
            return "null"
        else:
            return f'"{str(obj)}"'

    return serialize(data)


# New function for XML serialization
def to_xml(data, root_name="root"):
    def serialize(obj, name):
        if isinstance(obj, dict):
            return f"<{name}>" + "".join(serialize(v, k) for k, v in obj.items()) + f"</{name}>"
        elif isinstance(obj, list):
            return "".join(serialize(item, "item") for item in obj)
        elif obj is None:
            return f"<{name}/>"
        else:
            return f"<{name}>{str(obj)}</{name}>"

    return f'<?xml version="1.0" encoding="UTF-8"?>\n{serialize(data, root_name)}'

# Custom serialization function with boolean handling
def custom_serialize(obj):
    if isinstance(obj, dict):
        return "D{" + ",".join(f"{custom_serialize(k)}:{custom_serialize(v)}" for k, v in obj.items()) + "}"
    elif isinstance(obj, list):
        return "L[" + ",".join(custom_serialize(item) for item in obj) + "]"
    elif isinstance(obj, str):
        return f"S|{obj}|"
    elif isinstance(obj, int):
        return f"I|{obj}|"
    elif isinstance(obj, float):
        return f"F|{obj}|"
    elif obj is None:
        return "N|None|"
    else:
        raise ValueError("Unsupported data type")


def deserialize_list(data):
    result = []
    item_start = 0
    nesting_level = 0

    for i, char in enumerate(data):
        if char in '{[':
            nesting_level += 1
        elif char in ']}':
            nesting_level -= 1

        if nesting_level == 0 and (char == ',' or i == len(data) - 1):
            item = data[item_start:i + 1] if i == len(data) - 1 else data[item_start:i]
            result.append(custom_deserialize(item.strip()))
            item_start = i + 1

    #print(f"Deserialized list: {result}")  # Debug print
    return result


def deserialize_dict(data):
    result = {}
    key = None
    value_start = 0
    nesting_level = 0

    for i, char in enumerate(data):
        if char in '{[':
            nesting_level += 1
        elif char in ']}':
            nesting_level -= 1

        if nesting_level == 0:
            if char == ':' and key is None:
                key = data[value_start:i].strip()
                value_start = i + 1
            elif char == ',' or i == len(data) - 1:
                value = data[value_start:i + 1] if i == len(data) - 1 else data[value_start:i]
                if key is not None:
                    result[custom_deserialize(key)] = custom_deserialize(value.strip())
                key = None
                value_start = i + 1

    #print(f"Deserialized dict: {result}")  # Debug print
    return result


def custom_deserialize(data):
    def safe_slice(obj, length=100):
        if isinstance(obj, (str, list, tuple)):
            return str(obj[:length])
        else:
            return str(obj)[:length]

    #print(f"Deserializing: {safe_slice(data)}...")  # Print first 100 chars of data safely

    # If data is already a dict or list, return it as is
    if isinstance(data, (dict, list)):
        print("Data is already deserialized.")
        return data

    # If data is not a string, convert it to a string
    if not isinstance(data, str):
        data = str(data)

    data = data.strip()  # Remove leading/trailing whitespace

    if data.startswith("D{"):  # Deserialize dict
        return deserialize_dict(data[2:-1])  # Remove 'D{' and '}'
    elif data.startswith("L["):  # Deserialize list
        return deserialize_list(data[2:-1])  # Remove 'L[' and ']'
    elif data.startswith("S|"):  # Deserialize string
        return data[2:-1]  # Remove 'S|' and '|' from both sides
    elif data.startswith("I|"):  # Deserialize integer
        return int(data[2:-1])  # Remove 'I|' and '|' and convert to int
    elif data.startswith("F|"):  # Deserialize float
        return float(data[2:-1])  # Remove 'F|' and '|' and convert to float
    elif data.startswith("N|"):  # Deserialize None
        return None  # Return None
    else:
        raise ValueError(f"Unsupported data format: {safe_slice(data, 50)}...")

# Generate JSON and XML representations
json_result = to_json(result)
xml_result = to_xml(result, "scraping_result")

# Print JSON and XML results
print("JSON Representation:")
print(json_result)
print("\nXML Representation:")
print(xml_result)

# Serialize the data
serialized_data = custom_serialize(result)
print("\nSerialized:")
print(serialized_data,"\n")

# Deserialize the serialized string
deserialized_data = custom_deserialize(serialized_data)

# Verify the deserialization by comparing with the original data
print("\nDeserialization successful:", result == deserialized_data)

# Optional: Print the entire deserialized data structure in a formatted way
print("\nFull deserialized data structure:")
pprint(deserialized_data, width=120, compact=True)