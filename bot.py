from bs4 import BeautifulSoup
import re

file = "video.html"
with open(file,'r') as f:
    source = f.read()

soup = BeautifulSoup(source,'html.parser')

paras = soup.find_all("p")

title = paras[0].string

vids = paras[2]
links = [link.extract().text for link in vids.findAll('a')]
name = re.compile('\d+\..*?(?=<br/>)')
names = name.findall(str(vids))

vids_dict = dict(zip(names, links))

print(title)
print()
print()
for vid in vids_dict:
    print('Name: ', vid)
    print('Link: ', vids_dict[vid])
    print()
