from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def moviecontentcrawler(url):

    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(options=op)
    time.sleep(3)
    driver.get(url)


    python_button = driver.find_element(By.ID ,"play-now")
    python_button.click()

    sourceiframe = driver.find_element(By.ID ,"playit") 
    time.sleep(3)
    return sourceiframe.get_attribute("src")
    
    
def findall(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)

def getmovienamehtml(url):
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(options=op)
    time.sleep(3)
    driver.get(url)
    wholehtmlstr=(driver.find_element(By.TAG_NAME,"body")).get_attribute("innerHTML")
    moviename=[]

    htmllst=list(findall(wholehtmlstr,"https://ww9.0123movie.net/movie"))
    if len(htmllst)==0:
        return []
    
    for i in htmllst:
        j=i
        while 1:
            if wholehtmlstr[j]=="\"":
                moviename.append([wholehtmlstr[i:j]])

                break
            j=j+1

    k=0
    for i in list(findall(wholehtmlstr,"=\"card-title text-light fs-6 m-0\">")):
        j=i+34
        while 1:
            if wholehtmlstr[j]=="<":
                moviename[k].append(wholehtmlstr[i+34:j])
                k=k+1
                break
            j=j+1
    return moviename
    

file1 = open("movielist.html","w")
file1.writelines([])
file1.close()

for i in range(1,10000):
    tocrawl=list(getmovienamehtml("https://ww9.0123movie.net/list/movies/"+str(i)+".html"))
    if tocrawl==[]:
        print("end")
        break
    for str1,moviename in tocrawl:
        moviehtml=moviecontentcrawler(str1)
        file1 = open("movielist.html","a")
        file1.writelines(["<a href='",moviehtml,"'>",moviename,"</a>","<br>","</br>"])
        file1.close()
    
    
    
