import selenium
import requests
from lxml import html

main_page = requests.get("http://scoreboard.uscyberpatriot.org/")
print(main_page.content)
table = html.fromstring(main_page.content)
table = table.xpath('//table[@class="CSSTableGenerator"]/tbody')

# https://www.code-learner.com/python-parse-html-page-with-xpath-example/