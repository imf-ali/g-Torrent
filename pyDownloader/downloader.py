from tkinter import *
import requests

from multiprocessing.pool import Pool
from multiprocessing import Manager
from concurrent.futures import ThreadPoolExecutor
import time
import aiohttp
import asyncio
import math
import json

import os

os.environ['NO_PROXY'] = 'localhost'



DOWNLOAD_LINK='http://localhost:8000/api/download/'

DOWNLOAD_API_LINK='http://localhost:8000/api/downloadAPI/'

G_DOWN_LINK = 'https://drive.google.com/uc?export=download&id='

class AsyncioDownloader():
  def __init__(self,url):
    self.url = url
    self.dict = {}

  async def fetch(self,i,chunk):
    if chunk: 
      self.dict[i]=chunk

  async def main(self):
    async with aiohttp.ClientSession() as session:
      response = await session.request(method='GET', url=self.url)
      response_json = await response.read()
      chunk_size=1024
      i = 0
      response_json[1024*i:min(1024*(i+1),len(response_json))]
      tasks = [self.fetch(i,response_json[1024*i:min(1024*(i+1),len(response_json))]) for i in range(math.ceil(len(response_json)/chunk_size))]
      await asyncio.gather(*tasks)

  def func(self):
    asyncio.run(self.main())




class MultithreadingDownloader():
  def __init__(self,name,hashes):
    self.urls = []
    self.name = name
    self.hashes = hashes
    self.async_ref ={}


  def func(self,index):
    asyncio.run(self.async_ref[index].func())

  def getLinkFromhash(self):
    for lH in self.hashes:
      som = requests.get(DOWNLOAD_LINK+lH).text
      resp_d = json.loads(som)['link']
      self.urls.append(G_DOWN_LINK+resp_d)
    for i,som in enumerate(self.urls):
      self.async_ref[i] = AsyncioDownloader(som)
  def main(self):
    self.getLinkFromhash()
    print(self.urls)
    with ThreadPoolExecutor() as executor:
      paramter1 = []
      paramter2 = []
      for i,som in enumerate(self.urls):
        paramter1.append(i)
      executor.map(self.func,paramter1)
    with open(self.name,"wb") as fi:
      for i in range(len(self.async_ref)):
        for som in range(len(self.async_ref[i].dict)):
          fi.write(self.async_ref[i].dict[som])


class MultiprocessingDownloader():
  def __init__(self,url,name):
    self.url = url
    self.name = name
    self.dict = {}

  def fetch(self,i,row,chunk):
    if chunk:
      row[i]=chunk

  def main(self):
    with Manager() as mgr:
      row = mgr.dict({})
      with Pool() as pool:
        with requests.Session() as session:
          r = session.get(self.url, stream = True)
          pool.starmap(self.fetch,[(i,row,chunk) for i,chunk in enumerate(r.iter_content(chunk_size=100))])

      with open(self.name,"wb") as fi:
        for i in range(len(row)):
          fi.write(row[i])   


class SynchronousDownloader():
  def __init__(self,url,name):
    self.url = url
    self.name = name
    self.dict = {}

  def fetch(self,fi,chunk):
    if chunk: 
      fi.write(chunk)

  def main(self):
    with requests.Session() as session:
      r = session.get(self.url, stream = True)
      with open(self.name,"wb") as fi: 
        for chunk in r.iter_content(chunk_size=100): 
          self.fetch(fi,chunk)



def downloadFile(downloadUrl):
  hash_arr=[]
  som = requests.get(downloadUrl).text
  resp_d = json.loads(som)
  print(resp_d)
  outFile = resp_d['filename']
  hash_arr = resp_d['hash']
  print("yes")
  MultithreadingDownloader(outFile,hash_arr).main()

from tkinter import filedialog


class Downloader:
  def __init__(self,root):
    self.root = root
    self.root.title("Downloader Application")
    self.root.geometry("600x100+200+200")
    self.fileName = StringVar()
    self.downloadName = StringVar()
    self.status = StringVar()
    self.status.set("--/--")
    download_frame = Frame(self.root,background="grey",width=600,height=100).place(x=0,y=0)
    url_lbl = Label(download_frame,text="downaloded file name",compound=LEFT,font=("times new roman",15,"bold"),bg="grey",fg="gold").grid(row=1,column=0,padx=10,pady=10)
    url_txt = Entry(download_frame,bd=2,width=25,textvariable=self.downloadName,relief=SUNKEN,font=("times new roman",15)).grid(row=1,column=1,padx=10,pady=10)
    dwn_btn = Button(download_frame,text="Download",command=self.download,width=10,font=("times new roman",14,"bold"),bg="gold",fg="navyblue").grid(row=1,column=2,padx=10,pady=10)
    status_lbl = Label(download_frame,textvariable=self.status,font=("times new roman",14,"bold"),bg="grey",fg="white").grid(row=2,column=1)
    dwn_btn = Button(download_frame,text="select torrent File",command=self.browseFiles,width=10,font=("times new roman",14,"bold"),bg="gold",fg="navyblue").grid(row=2,column=2,padx=10,pady=10)
  def browseFiles(self):
    filename = filedialog.askopenfilename(initialdir = ".",title = "Select a File",filetypes = (("Text files","*.txt*"),("all files","*.*")))
    self.fileName = filename
  def download(self):
    if self.downloadName =="":
      self.status.set("file NOT SPECIFIED")
    else:
      try:
        self.status.set("Downloading...")
        self.root.update()
        downloadFile(self.downloadName.get())
        self.status.set("Downloaded Successfully")
      except:
        self.status.set("Error in Downloading")
root = Tk()
Downloader(root)
root.mainloop()
