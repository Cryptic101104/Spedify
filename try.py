import requests as r
import bs4 as bs4

product_name = input("Enter the product name: ")
url = "https://www.flipkart.com/search?q=" + product_name
print("URL:", url)

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
}

try:
    product_response = r.get(url, headers=headers)
    # Check if the response is successful
    if product_response.status_code == 200:
        soup = bs4.BeautifulSoup(product_response.text, features='lxml')
        names = soup.find_all('div', class_='KzDlHZ')
        prices = soup.find_all('div', class_='Nx9bqj _4b5DiR')

        if names and prices:
            # Print the first product name and price
            print("Product Name:", names[0].text.strip())
            print("Price:", prices[0].text.strip())
        else:
            print("Product or price not found.")
    else:
        print("Failed to retrieve data. Status code:", product_response.status_code)

except Exception as e:
    print("An error occurred:", e)
