import requests
from bs4 import BeautifulSoup

url = 'https://ead.unieuro.edu.br/'
response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')
text = soup.get_text(separator='\n', strip=True)
print(text)
