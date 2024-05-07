# encoding: utf-8
'''
 @author: 我不是大佬
 @contact: 2869210303@qq.com
 @wx; safeseaa
 @qq; 2869210303
 @file: 微博热搜爬虫.py
 @time: 2023/1/29 9:16
  '''
import requests
from lxml import etree

url="https://tophub.today/n/KqndgxeLl9"
headers={
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.69'
}
res=requests.get(
    url=url,
    headers=headers
)

html=etree.HTML(res.text)
trs=html.xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/table/tbody/tr')

def getfirsttext(list):
    """
    返回列表中第一个元素
    :return:
    """
    try:
        return list[0].strip()
    except:
        return ""

file=open("微博热搜top50.txt",mode="w",encoding="utf-8")
for tr in trs:
    id=getfirsttext(tr.xpath('./td[1]/text()'))
    title=getfirsttext(tr.xpath('./td[2]/a/text()'))
    play=getfirsttext(tr.xpath('./td[3]/text()'))
    print(id,title,play)
    file.write(str(id)+","+title+","+str(play)+"\n")
file.close()