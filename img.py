import imgkit
from bs4 import BeautifulSoup
import requests

url = "https://logs.tf/2924272"

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

player_table = soup.select_one("#log-section-players").select_one("#players")

table_height = 0

for row in player_table.select_one("tbody").find_all("tr"):
    name = row.select_one(".log-player-name a.dropdown-toggle").text
    nclasses = len(row.select(".log-classes i"))

    if len(name) > 25 or nclasses > 4:
        table_height += 48
    else:
        table_height += 29

options = {
    "xvfb": "",
    'crop-h': table_height + 28 + 30 + 66 + 15 + 28,
    'crop-w': '980',
    'crop-x': '178',
    'crop-y': '201',
}

imgkit.from_url(url, "out.png", options=options)



# css_link = soup.find('link', rel='stylesheet')
# css = requests.get(f"https://logs.tf/{css_link['href']}")
# css = css.text

# with open("/home/tf2maps/bot_zeus/temp.css", "w") as file:
#     file.write(css)

# page = f"""
# <html>
#     <head>
#         <meta name="imgkit-format" content="png"/>
#         <meta name="imgkit-width" content="920"/>
#         <meta name="imgkit-height" content="500"/>
#     </head>
#     <body>
#         {soup.select_one(".content")}
#     </body>
# </html>
# """

# imgkit.from_string(page, "out.png", css="temp.css", options=options)