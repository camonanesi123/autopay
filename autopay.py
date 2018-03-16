#--coding:utf-8
#author:hexiao
#
#设计一个类去模拟打开电信网站并且充值
#

from urllib.request import urlopen
from urllib.request import Request
import urllib.request
import urllib.parse
import re
import shutil
import http.cookiejar
import json
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
import time
import os
import threading
from selenium.webdriver.common.action_chains import ActionChains
#解析包
from bs4 import BeautifulSoup



# 定义一个自己的头类, 继承HTTPRedirectHandler
# 重写 http_error_302, 直接返回 fp(reponse);
class MyRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, hdrs):
        return fp

#爬虫类
class Crawler():
#构造函数传入必要的登录地址
    def __init__(self,url,header):
        self.url=url
        self.header=header
        self.opener=1
        return

#创建opener，包含header信息和cookie
    def CreateOpener(self):
        #实例化cookie对象，需要一直维护在内存中
        cookie=http.cookiejar.CookieJar()
        #创建一个cookie处理器
        CookieHandle=urllib.request.HTTPCookieProcessor(cookie)
        myHandler = MyRedirectHandler()
        #创建带有cookie，和识别302跳转的opener
        opener=urllib.request.build_opener(CookieHandle,myHandler)
        #传入header
        head=[]
        for key,value in self.header.items():
            elem=(key,value)
            head.append(elem)
        opener.open(self.url)
        self.opener = opener
        return opener
#第二次请求,输入手机号和充值金额之后点下一步
    def getOrderId(self,phoneNum,amount):
        phoneNumber=phoneNum
        payAmount=amount
        shopid="20001"
        formdata = {"headerInfo": { "functionCode": "recharge"},"requestContent":{"shopid":"20001","phoneNumber":"17777784957","payAmount":1,"type":1}}
        data_encoded = urllib.parse.urlencode(formdata).encode(encoding='UTF8')
        #json封装
        formdata = json.dumps(formdata).encode(encoding='UTF8')
        url = 'http://cservice.client.189.cn:9092/common/recharge.do'
        self.opener.addheaders = [('X-Requested-With', 'XMLHttpRequest'),
                     ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'),
                     ('Accept','application/json, text/javascript, */*; q=0.01'),
                     ('Accept-Encoding','gzip, deflate')]
        response = self.opener.open(url, formdata)
        jsonText = response.read().decode()
        a = json.loads(jsonText)
        #print(a)
        orderid=a["responseContent"]['orderId']
        print(orderid)
        return orderid

#第三部请求获取sessionId
    def getSessionId(self,orderId):
        url = "http://pay.a.189.cn/pay/onlinePay.do?userid=FSD88888&type=3000701&id=%s"%orderId
        print(url)
        res =self.opener.open(url)
        print(res.getcode())
        #从头部中拿取Location 因为里面有session
        a = res.getheaders()
        #a是一个头部的元组数组，遍历数组，找到元组第一个元素为location
        url=""
        for i in range(0,len(a)):
            if(a[i][0] == "Location"):
                url = a[i][1]
        print(url)
        #把url中sessionid的内容抠出来 找到? 找到 &
        start = url.find('?')
        end = url.find('&')
        session = url[start+1:end]
        print(session)
        return session		
#第四次请求直接把sessionId拿到，请求百度付款 http://pay.a.189.cn/pay/onlinePay.html?sessionid=f68f864ae3ef4ade8ac87ed123c8228c&trkProducts=41;1898888888850
    #获得https百度钱包的支付链接
    def getBaifubaoPage(self,sessionId):
        url = 'http://pay.a.189.cn/pay/toPay.do?bankCode=baidupay&%s&state='%sessionId	
        res =self.opener.open(url)
        s= res.read().decode()
        #name='request_params' value='{"base":{"service":"create_order_direct","version":1.0,"merchant_id":"01","sign":"Yv7SeZJOAT0jq0xn7n4NMZGTjDcbyHo3JNKC97E5Bic=","platform":"132"},"biz":{"order_id":"1000000083420180314224722714","transaction_id":"201803140059000000000100268544","create_time":"2018-03-14 23:13:23","over_time":"2018-03-15 11:13:23","product_name":"银行卡直充-50元","total_price":4975,"return_url":"http://pay.a.189.cn/pay/toPayQuery.do?boId=5d26e53d047148a1b99f7eaa144c63a5","notify_url":"","client_ip":"114.248.198.80","bank":"baidupay","ledger_infos":null}}'
        #解析表单中的name 和 value 然后打包post过去
        #第六次请求
        #print(s)
        soup = BeautifulSoup(s)
        value = soup.find('input', {'name': 'request_params'}).get('value')
        formdata = {'request_params':value}
        data_encoded = urllib.parse.urlencode(formdata).encode(encoding='UTF8')
        url = 'http://paygo.189.cn:9778/189pay/service'
        #print(url)
        response = self.opener.open(url, data_encoded)
        s= response.read().decode()
        #print(s)
        soup = BeautifulSoup(s)
        link = soup.find('a').get('href')
        #打开支付（第七次） 模拟 浏览器打开
        print(link)
        return link		


	
def crawlingpage():

	# 需要post的网址的URL
    url = "http://cservice.client.189.cn:9092/recharge/recharge_index.html?shopid=20001"
    #header
    header=\
        {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
        "Connection":"keep-alive",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate",
        "Accept-Language":"zh-CN,zh;q=0.8",
        "Upgrade-Insecure-Requests":"1",
        "Cache-Control":"max-age=0",
        }	
#实例化爬虫
    lj=Crawler(url,header)
#获得opener
    opener=lj.CreateOpener()
#输入手机，金额获取订单号
    orderId = lj.getOrderId("17777784957",1)
#获取sessionId
    sessionId = lj.getSessionId(orderId)
#获取百度支付的https链接
    link = lj.getBaifubaoPage(sessionId)
    ''' 获得支付链接之后模拟用浏览器打开按步骤操作 '''
    chromedriver = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"
    os.environ["webdriver.chrome.driver"] = chromedriver
#获取chrome driver 对象
    driver = webdriver.Chrome(chromedriver)
    driver.get(link)
#打开之后选用户名登陆
    time.sleep(5)
    a = driver.find_element_by_id("TANGRAM__PSP_3__footerULoginBtn")
    time.sleep(5)
    a.click()

#进入输入用户名登陆界面
    elem_user = driver.find_element_by_name("userName")
    time.sleep(10)
    elem_user.send_keys("wakawakafrica")
#输入密码

    b = driver.find_element_by_name("password")
    time.sleep(10)
    b.send_keys("000424")
#点击登陆
    a = driver.find_element_by_id('TANGRAM__PSP_3__submit')
    a.click()
    time.sleep(10)
#点确认支付
    a = driver.find_element_by_class_name('buttonwrap')
    print(a)
    a.click()
    time.sleep(10)
#模拟输入密码
#ActionChains(driver).move_to_element(driver.find_element_by_id('pwdinput').click().sendKeys("000424")).perfrom()
    a = driver.find_element_by_id('pwdinput')
    print(a)
#百度钱包支付密码自己写
    a.send_keys("xxxxxx")
    time.sleep(10)
#关闭浏览器
    driver.quit()

	
	

# 创建两个线程

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("Starting " + self.name)
       # 获得锁，成功获得锁定后返回True
       # 可选的timeout参数不填时将一直阻塞直到获得锁定
       # 否则超时后将返回False
        #threadLock.acquire()
        #print_time(self.name, self.counter, 10)
        crawlingpage()       
		#threadLock.release()
 
def print_time(threadName, delay, counter):
    while counter:
        time.sleep(delay)
        print("%s: %s" % (threadName, time.ctime(time.time())))
        counter -= 1
 
threadLock = threading.Lock()
threads = []
 
# 创建新线程10个
for i in range(0,10):
    t = myThread(i, "Thread-%s"%i, i)
    t.start()
    threads.append(t)

# 等待所有线程完成
for t in threads:
    t.join()
print("Exiting Main Thread")


#t = threading.Thread(target=crawlingpage)
#t.start()
#t.join()
   
#a = driver.find_element_by_class_name('business-widget-ani')
#time.sleep(5)
#a.send_keys("000424")

#a = driver.find_element_by_class_name('business-widget-ani').send_keys(Keys.ENTER)

