# coding: utf-8
import pymysql
import socket
import time
import sys,os,subprocess
import ctypes
import random
import datetime
from winreg import OpenKey, HKEY_LOCAL_MACHINE, QueryInfoKey, EnumKey, CloseKey, QueryValueEx, SetValueEx, REG_SZ, \
    KEY_ALL_ACCESS, KEY_WOW64_64KEY

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

import requests
from bs4 import BeautifulSoup
import pyautogui
pyautogui.FAILSAFE = False
import re

import fake_useragent
import settings
from setmac import SetMac
import win32api, win32con
import jieba


# 7天以前
def getLastweek():
    today = datetime.date.today()
    sevenday = datetime.timedelta(days=1)
    lastweek = today - sevenday
    return lastweek

# 删除log文件
def delete_log():
    lastweek = getLastweek()
    lastweek_log = "{}_log.txt".format(lastweek)
    if (os.path.exists(lastweek_log)):
        os.remove(lastweek_log)
        print("删除上周的log文件")


class BasicClick(object):
    def __init__(self):
        super(BasicClick, self).__init__()

    customtime = 0  # 自定义总时间
    persleeptime = 0  # 自定义每次进入内页的时间（inclick方法中处理）
    rlx = 0  # 偏移量x
    rly = 0  # 偏移量y
    grlx = 0  # 元素宽度
    grly = 0  # 元素高度
    rooturl = ''  # 目标网站url
    disurl = ''  # 排除项网站url
    keywordlist = []  # 关键词列表
    keyword = ''  # 关键词
    # 百度网站入口tn参数
    RelKeyword_list = []  # 相关搜索词列表
    HotKeyword_list = []  # 热点搜索词列表
    cookies_list = []  # 百度cookies列表
    acnum = 0  # 任务成功数f
    FBL = []
    tn_list = []



    # 读配置文件
    def readINI(self, engine):
        """读取配置文件"""
        # self.FBL = settings.FBL
        self.log = ''
        self.net = settings.SPQ_NAME
        self.connectSQL()
        self.engine = engine
        sql = "select show_threshold,click_threshold, ifchangefbl, ifchangemac, ifgetip, username, get_ip_sleep, get_task_sleep, sleep_time, customtime_min, customtime_max from taskparams where engine='{}'".format(self.engine)
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            random.shuffle(alist)
            self.show_threshold = alist[0][0]
            self.click_threshold = alist[0][1]
            self.ifchangefbl = alist[0][2]
            self.ifchangemac = alist[0][3]
            self.ifgetip = alist[0][4]
            self.username = alist[0][5]
            self.get_ip_sleep = alist[0][6]
            self.get_task_sleep = alist[0][7]
            self.sleep_time = alist[0][8]
            self.customtime_min = alist[0][9]
            self.customtime_max = alist[0][10]
            self.customtime = random.choice(range(self.customtime_min, self.customtime_max))
        except:
            self.show_threshold = 0.5
            self.click_threshold = 0.2
            self.ifchangefbl = 'false'
            self.ifchangemac = 'false'
            self.ifgetip = 'false'
            self.username = 'user1'
            self.get_ip_sleep = 15
            self.get_task_sleep = 5
            self.sleep_time = 240
            customtime = random.choice(range(180, 300))
            self.customtime = customtime
        self.disconnectSQL()

        self.connectSQL()
        sql = "select width,height from fbl"
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            random.shuffle(alist)  # 洗牌，随机选择一个任务
            for vo in alist:
                width = vo[0]
                height = vo[1]
                self.FBL.append({"width": width, "height": height})
        except Exception as err:
            self.writelog('读取分辨率失败')
        self.disconnectSQL()

        self.connectSQL()
        sql = "select tn_list from tnlist where engine='{}'".format(self.engine)
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            random.shuffle(alist)  # 洗牌，随机选择一个任务
            for tn in alist:
                self.tn_list.append(tn[0])
        except Exception as err:
            self.writelog('读取tnlist失败')
        self.disconnectSQL()


    def connectSQL(self):
        """连接数据库"""
        try:
            self.db = pymysql.connect(host=settings.SQL_HOST, user=settings.SQL_USER, password=settings.SQL_PASS,
                                      db=settings.SQL_DB, connect_timeout=20)
            self.cursor = self.db.cursor()
        except Exception as err:
            print('连接数据库出错:{}'.format(err))


    def disconnectSQL(self):
        """关闭数据库连接"""
        self.db.close()

    # ==========================各种点击=====================================================
    def doRoll(self):
        """如果目标元素被导航条覆盖，那么执行此程序将滚动条移动到最上面"""
        self.driver.execute_script("window.scrollTo(0,0);")
        time.sleep(3)


    def doRandRoll(self):
        """滚动条随机滚动"""
        pos = random.choice(range(60, 200))
        self.driver.execute_script("window.scrollTo(0," + str(pos) + ");")
        time.sleep(3)


    def toNewWeb(self):
        """句柄转到最后页面"""
        # time.sleep(3)
        for handle in self.driver.window_handles:
            newhandle = handle

        self.driver.switch_to.window(newhandle)


    def ClickCom(self, element):
        """点击通用方法***不退出***"""
        self.comElementIn(element)
        self.curx = element.location_once_scrolled_into_view['x'] + self.rlx
        self.cury = element.location_once_scrolled_into_view['y'] + self.rly
        if self.cury < self.rly + self.baidunavzxy:
            self.cury = self.cury + self.baidunavzxy
            self.driver.execute_script('window.scrollBy(0,-{})'.format(self.baidunavzxy))
        self.grlx = element.size['width']
        self.grly = element.size['height']
        grlp = self.randElementPosition()
        handlenum1 = len(self.driver.window_handles)
        # print(self.curx,self.curx+ grlp['x'], self.cury, self.cury+ grlp['y'])
        self.mouseMoveClick(self.curx+ grlp['x'], self.cury+ grlp['y'])
        time.sleep(5)
        self.toNewWeb()
        handlenum2 = len(self.driver.window_handles)
        if handlenum1 != handlenum2:
            time.sleep(3)
            self.driver.close()
            time.sleep(3)
            self.toNewWeb()


    # ==========================点击页面的功能函数=====================================================
    # 随机ua 一次搞定
    def randUa(self):
        headers = {}
        headers['User-Agent'] = self.get_UserAaent()
        return headers  # 返回随机UA


    def mouseMoveRand(self):
        """随机移动几次鼠标"""
        randmovetimes = random.choice(range(0,4))
        for i in range(0, randmovetimes):
            randx = random.choice(range(0, self.winWidth)) + self.rlx
            randy = random.choice(range(0, self.winHeight)) + self.rly
            randmovespeed = random.choice(range(1, 3))
            pyautogui.moveTo(randx, randy, duration=randmovespeed)
            time.sleep(self.randSleep())


    def mouseMoveClick(self, x, y):
        """随机移动几次然后再点击目标"""
        randmovetimes = random.choice(range(0, 3))
        for i in range(0, randmovetimes):
            randx = random.choice(range(0, self.winWidth)) + self.rlx
            randy = random.choice(range(0, self.winHeight)) + self.rly
            randmovespeed = random.choice(range(1, 3))
            pyautogui.moveTo(randx, randy, duration=randmovespeed)
            time.sleep(self.randSleep())
        randmovespeed = random.choice(range(1, 3))
        pyautogui.click(x, y, duration=randmovespeed)


    def mouseMove_without_Click(self, x, y):
        """随机移动几次然后再点击目标"""
        randmovetimes = random.choice(range(0, 3))
        for i in range(0, randmovetimes):
            randx = random.choice(range(0, self.winWidth)) + self.rlx
            randy = random.choice(range(0, self.winHeight)) + self.rly
            randmovespeed = random.choice(range(1, 3))
            pyautogui.moveTo(randx, randy, duration=randmovespeed)
            time.sleep(self.randSleep())
        randmovespeed = random.choice(range(1, 3))
        pyautogui.moveTo(x, y, duration=randmovespeed)


    def randElementPosition(self):
        """获取元素大小并随机元素内部坐标"""
        x = random.choice(range(1, self.grlx))
        y = random.choice(range(1, self.grly))
        return {'x': x, 'y': y}


    def randDriverSize(self):
        """随机驱动大小，随机浏览器大小"""
        size = self.driver.get_window_size()
        width = size['width']
        height = size['height']
        widthrand = random.choice(range(800, width + 1))
        heightrand = random.choice(range(600, height + 1))
        self.driver.set_window_size(widthrand, heightrand)
        time.sleep(5)
        print(self.driver.get_window_size())

    #==========================操作流程=====================================================
    # 更换分辨率
    def changeFBL(self):
        a = random.choice(self.FBL)
        dm = win32api.EnumDisplaySettings(None,0)
        dm.PelsHeight = a['height']
        dm.PelsWidth = a['width']
        log = "本次任务屏幕分辨率,宽:" + str(a['width']) + " 高:" + str(a['height'])
        self.writelog(log)
        #
        ## 增加品目色彩位数随机
        f = random.choice(range(0,3))
        if f>0:
            dm.BitsPerPel = 32
        else:
            dm.BitsPerPel = 24
        #
        dm.DisplayFixedOutput = 0
        win32api.ChangeDisplaySettings(dm, 0)


    # 设置ua
    def get_UserAaent(self):
        """设置ua"""
        # ua = fake_useragent.UserAgent()
        # return ua.random
        location = os.getcwd() + '/fake_useragent.json'
        ua = fake_useragent.UserAgent(path=location)
        return ua.random


    # 检查网络
    def check_network(self):
        """检查网络"""
        exit_code1 = subprocess.call('ping www.taobao.com')
        if exit_code1:
            exit_code2 = subprocess.call('ping www.douban.com')
            if exit_code2:
                exit_code3 = subprocess.call('ping www.zhihu.com')
                if exit_code3:
                    return False
        return True


    def check_network_new(self, cur_ip):
        pattern = re.compile(r"[\d\.]+:[\d]+")
        m = pattern.match(cur_ip)
        if m != None:
            """检查网络"""
            exit_code1 = subprocess.call('ping www.taobao.com')
            if exit_code1:
                exit_code2 = subprocess.call('ping www.douban.com')
                if exit_code2:
                    exit_code3 = subprocess.call('ping www.zhihu.com')
                    if exit_code3:
                        return False
            return True
        else:
            print("代理IP无效！")
            return False


    # def check_network_new(self, cur_ip):
    #     pattern = re.compile(r"[\d\.]+:[\d]+")
    #     m = pattern.match(cur_ip)
    #     if m != None:
    #         try:
    #             requests.adapters.DEFAULT_RETRIES = 3
    #             # print("本次的ip为:{}".format(cur_ip))
    #             thisProxy = "http://" + cur_ip
    #             thisIP = "".join(cur_ip.split(":")[0:1])
    #             # print('thisIP:{}'.format(thisIP))
    #             res = requests.get(url="http://icanhazip.com/",timeout=6,proxies={"http":thisProxy})
    #             proxyIP = res.text
    #             # print('proxyIP:{}'.format(proxyIP))
    #             if(proxyIP.strip() == thisIP.strip()):
    #                 print("代理IP:'"+ cur_ip + "'有效！")
    #                 return True
    #             else:
    #                 print("代理IP无效！")
    #                 return False
    #         except:
    #             print("代理IP无效！")
    #             return False
    #     else:
    #         print("代理IP无效！")
    #         return False


    # 清除cookie
    def clearCookies(self):
        """清除cookies"""
        try:
            self.driver.delete_all_cookies()
        except Exception as err:
            print(err)


    def quitexe(self):
        """退出处理程序"""
        try:
            self.clearCookies()
            self.driver.quit()
        except Exception as err:
            print(err)

    # ======================点击流程=====================================================
    def getTask(self):
        flag = False
        # 读取数据库
        self.connectSQL()

        sql = "select id,keyword,text,rooturl,disurl,mode,clicknum,clickreadynum from taskeveryday where username = '{}' and engine = '{}' and clickreadynum < clicknum".format(self.username, self.engine)
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            random.shuffle(alist)  # 洗牌，随机选择一个任务
            if len(alist) != 0:
                for vo in alist:
                    id = vo[0]
                    keyword = vo[1]
                    text = vo[2]
                    rooturl = vo[3]
                    disurl = vo[4]
                    mode = vo[5]
                    clicknum = vo[6]
                    clickreadynum = vo[7]
                    self.loadTask(id, keyword, text, rooturl, disurl, mode, clickreadynum)
                    print(id, keyword, text, rooturl, disurl, mode, clickreadynum)
                    try:
                        sqlalter = "update taskeveryday set clickreadynum = %d where id = %d" % (clickreadynum + 1, id)
                        n = self.cursor.execute(sqlalter)
                        self.db.commit()
                        flag = True
                        break
                    except Exception as err:
                        print("更新数据库任务失败 err:{}".format(err))
            else:
                print("{}的任务已经跑完了".format(self.username))
                self.writelog("{}的任务已经跑完了".format(self.username))
        except Exception as err:
            print("读取数据库任务失败 err:{}".format(err))

        self.disconnectSQL()

        if flag == False:
            return False
        elif flag == True:
            return True


    def Tasktimeout_minus1(self):
        self.connectSQL()

        sql = "select id,clickreadynum from taskeveryday where id = %d " % self.id
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            id = alist[0][0]
            clickreadynum = alist[0][1]
            try:
                sqlalter = "update taskeveryday set clickreadynum = %d where id = %d" % (clickreadynum - 1, id)
                n = self.cursor.execute(sqlalter)
                self.db.commit()
            except Exception as err:
                print("更新数据库任务失败 err:{}".format(err))
        except Exception as err:
            print("读取数据库任务失败 err:{}".format(err))

        self.disconnectSQL()




    def loadTask(self, id, keyword, text, rooturl, disurl, mode, clickreadynum):
        """加载任务"""
        self.id = id
        self.keyword = keyword
        self.text = text
        self.rooturl = rooturl
        self.disurl = disurl
        self.mode = mode
        self.clickreadynum = clickreadynum


    #======================功能函数=====================================================
    # def loadCookies(self):
    #     self.printDivide()
    #     print("正在加载本地百度Cookies")
    #     self.printDivide()
    #     f = open("cookies.txt", "r")
    #     cookies = f.readlines()
    #     f.close()
    #     for cook in cookies:
    #         cook = cook.replace(";","")
    #         cook = cook.strip()
    #         cooktuple = cook.split("=")
    #         self.cookies_list.append({"name": cooktuple[0], "value": cooktuple[1]})
    #     # print(self.cookies_list)
    #     print("加载本地百度Cookies成功")


    def addCookies(self):
        """添加百度cookies"""
        cook = random.choice(self.cookies_list)
        name = cook['name']
        value = cook['value']
        print("当前使用的cookie:")
        print(cook)
        self.driver.add_cookie({"name": name, "value": value})
        # print("加载cookie完成")


    def get_mac_address(self):
        """获取当前mac地址"""
        try:
            import netifaces
        except ImportError:
            try:
                command_to_execute = "pip install netifaces"
                subprocess.call(command_to_execute)
            except OSError:
                print("Can NOT install netifaces, Aborted!")
                sys.exit(1)
            import netifaces
        routingGateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
        routingNicName = netifaces.gateways()['default'][netifaces.AF_INET][1]
        for interface in netifaces.interfaces():
            if interface == routingNicName:
                # print netifaces.ifaddresses(interface)
                routingNicMacAddr = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
                try:
                    routingIPAddr = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                    # TODO(Guodong Ding) Note: On Windows, netmask maybe give a wrong result in 'netifaces' module.
                    routingIPNetmask = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['netmask']
                except KeyError:
                    pass
        return routingNicMacAddr.upper()



    def printDivide(self):
        """打印分割线"""
        print("="*70)


    def randSleep(self):
        """随机睡眠时间"""
        return random.choice(range(0,3))


    def customSleep(self):
        """自定义睡眠时间"""
        time.sleep(self.persleeptime)

    # # 写日志文件
    # def writelog(self, text):
    #     """写日志"""
    #     td = datetime.datetime.now().strftime('%Y-%m-%d')
    #     with open('{}_log.txt'.format(td), 'a') as f:
    #         f.write(text)
    #         f.write('\n')


    def writelog(self, text):
        self.log = r"{}\n{}".format(self.log, text)

    # 往数据库写log文件
    def pushlog(self, text, engine):
        td = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.db.open == True:
            try:
                sqlalter = 'INSERT INTO tasklog(log_time, engine, log_message) VALUES("{}", "{}", "{}");'.format(td, engine, text)
                n = self.cursor.execute(sqlalter)
                self.db.commit()
                print("log日志写入数据库成功")
            except Exception as err:
                print("log日志写入数据库失败 err:{}".format(err))
        else:
            self.connectSQL()
            try:
                sqlalter = 'INSERT INTO tasklog(log_time, engine, log_message) VALUES("{}", "{}", "{}");'.format(td, engine, text)
                n = self.cursor.execute(sqlalter)
                self.db.commit()
                print("log日志写入数据库成功")
            except Exception as err:
                print("log日志写入数据库失败 err:{}".format(err))
            self.disconnectSQL()


    # def get_ip(self):
    #     try:
    #         import xmlrpc.client
    #         with xmlrpc.client.ServerProxy("http://106.53.193.72:5000/") as proxy:
    #             ip = proxy.get_ip()
    #         self.writelog("获取新ip;")
    #         return ip
    #     except Exception as err:
    #         self.writelog("获取ip出错;")
    #         return ""

    def get_ip(self):
        try:
            url = 'http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId=48d2907c917542078f572e3f2d75cab2&orderno=YZ20211121125eWbiZw&returnType=1&count=1'
            f = requests.get(url, timeout=60)
            if f.status_code != 200:
                self.writelog("获取ip出错，status_code!=200:;")
                return ""
            else:
                self.writelog("获取新ip;")
                return f.text
        except Exception as err:
            self.writelog("获取ip出错;")
            return ""




    def if_run(self, engine):
        self.readINI(engine=engine)
        flag = False
        ramdom_num = random.random()
        locat_hour = time.localtime().tm_hour
        key = 'hour{}'.format(locat_hour)
        self.connectSQL()
        sql = "select {} from taskparams where engine = '{}'".format(key, engine)
        try:
            m = self.cursor.execute(sql)
            alist = self.cursor.fetchall()
            alist = list(alist)
            threshold = alist[0][0]
            if ramdom_num < threshold:
                print("随机数：{}， 阈值：{},运行".format(ramdom_num, threshold))
                self.printDivide()
                self.writelog("时间：{}".format(datetime.datetime.now()))
                self.writelog("随机数：{}， 阈值：{},运行".format(ramdom_num, threshold))
                self.printDivide()
                flag = True
            else:
                print("随机数：{}， 阈值：{},不运行".format(ramdom_num, threshold))
                self.printDivide()
                self.writelog("时间：{}".format(datetime.datetime.now()))
                self.writelog("随机数：{}， 阈值：{},不运行".format(ramdom_num, threshold))
                self.printDivide()
                flag = False
        except:
            print("if_run报错")
            self.writelog("if_run报错")
            flag = False
        self.disconnectSQL()
        self.pushlog(self.log, self.engine)
        return flag


if __name__ == "__main__":
    engine = "baidu_pc"
    basic = BasicClick()
    basic.readINI(engine=engine)