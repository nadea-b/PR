import requests

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