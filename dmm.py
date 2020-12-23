# -*- coding: utf-8 -*-
import requests
import re
import json
import threading 
import time
from jinja2 import PackageLoader,Environment
from bs4 import BeautifulSoup
from queue import Queue
#from lxml import etree
from function_requests import get_html_jp
from function_requests import get_html_jp_html
from loadini import read_config
from selenium import webdriver

def findinfo(articleid):
    url = "https://www.dmm.co.jp/digital/videoa/-/list/=/article=actress/id=%s/" %articleid
    html = get_html_jp(url)
    page1 = re.findall(r'/digital/videoa/-/list/=/article=actress/id=\d+/page=(\d+)/',html)
    title = re.findall(r'<title>(.*) - エロ動画・アダルトビデオ - FANZA動画</title>',html)
    if page1 == []:
        page1 = 1
    else:
        page3 = []
        for i in page1:
            if i not in page3:
                page3.append(int(i))
        page4 = max(page3)
        page1 = page4
    title1 = title[0]
    return (page1,title1)
def producer(in_q,articleid, page):
    for i in range(1, int(page)+1):
        url = "https://www.dmm.co.jp/digital/videoa/-/list/=/article=actress/id={}/page={}/".format(articleid,i)
        #print(url)
        in_q.put(url)
def dmmcid(in_q, out_q):
    while in_q.empty() is not True:
        url = in_q.get()
        html = get_html_jp(url)
        list = re.findall(r'https://www\.dmm\.co\.jp/digital/videoa/-/detail/=/cid=([_0-9a-z]+)/',html)
        #print(list)
        out_q.append(list)
        in_q.task_done()
def dmm_thread(articleid):
    start = time.time()
    page, title = findinfo(articleid)
    #print(page,title)
    queue = Queue()  
    result_queue = []
    #page = 9
    producer_thread = threading.Thread(target=producer, args=(queue, articleid, page))
    #producer_thread.daemon = True
    producer_thread.start()
    
    for index in range(int(page)+1):
        consumer_thread = threading.Thread(target=dmmcid, args=(queue, result_queue))
        consumer_thread.daemon = True
        consumer_thread.start()
    #print('开启线程数:' + str(threading.active_count()))
    queue.join()
    
    resetlist = []
    for i in result_queue:
        try:
            for n in i:
                if n not in resetlist:
                    resetlist.append(n)
        except TypeError: 
            if i not in resetlist:
                resetlist.append(i)
    
    
    #print(resetlist)
    leng = len(resetlist)
    alllist = ','.join(resetlist)
    end = time.time()
    usetime = str(end - start)
    result = '%s - エロ動画・アダルトビデオ - FANZA動画\npage(%s)(%s),cid list  =>\n%s' % (title,page,leng,alllist)
    return (result,usetime)
    
def ciddata(html):
    notitle = 0
    soup = BeautifulSoup(html,'lxml')
    try:
        ifresult = re.findall(r'(指定されたページが見つかりません)', html)
        noresult = '指定されたページが見つかりません'
    except:
        pass
    try:
        if noresult in ifresult:
            notitle = 1
            return (noresult, notitle)
    except Exception:
        pass


    ciddata = {}
    allper = soup.find_all(name='span', id='performer')
    sortper = re.findall(r'<a href="/digital/videoa/-/list/=/article=actress/id=(\d+)/">(.*?)</a>', str(allper))
    perfordata = {}
    for i in sortper:
        perfordata[i[0]] = i[1]
    if perfordata != None:
        ciddata['performers'] = perfordata
    else:
        ciddata['performers'] = '---'
    allkey = soup.find('table', attrs = {'class':'mg-b20'}).find_all('a', href = re.compile('article=keyword'))
    sortkey = re.findall(r'<a href="/digital/videoa/-/list/=/article=keyword/id=(\d+)/">(.*?)</a>', str(allkey))
    keyworddata = {}
    for i in sortkey:
        keyworddata[i[0]] = i[1]
    if perfordata != None:
        ciddata['keyword'] = keyworddata
    else:
        ciddata['keyword'] = '---'
    
    scoregif = soup.find('table', attrs = {'class':'mg-b20'}).find_all('img')
    try:
        score = re.findall(r'https://.*/(\d)_?(\d)?.gif',str(scoregif))[0]
        ciddata['score'] = score
    except:
        ciddata['score'] = '0-0'
    try:
        redkey = re.findall(r'<span class="red">(.*)</span>',html)[0]
        titlebig = re.findall(r'<title>(.*)</title>',html)[0]
        ciddata['title'] = redkey + '  ' + titlebig
    except:
        ciddata['title'] = '---'
        notitle =  1
    try:
        ciddata['fanart_img'] = re.findall(r'<a href=\"(.*)\" target=\"_package\" name=\"package-image\"',html)[0]
    except:
        ciddata['fanart_img'] = '---'
    try:
        ciddata['distribute'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">配信開始日：</td>\n?<td>\n?(.*)</td>',html)[0]
    except:
        ciddata['distribute'] = '---'
    try:
        ciddata['release'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">商品発売日：</td>\n?<td>\n?(.*)</td>',html)[0]
    except:   
        ciddata['release'] = '---'
    try:
        ciddata['time'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">収録時間：</td>\n?<td>(.*\n?.*)',html)[0]
    except:   
        ciddata['time'] = '---'
    try:   
        ciddata['directorid'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">監督：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=director/id=(\d+)/\">.*</a></td>',html)[0]
    except:   
        ciddata['directorid'] = '---'
    try:     
        ciddata['director'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">監督：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=director/id=\d+/\">(.*)</a></td>',html)[0]
    except:   
        ciddata['director'] = '---'
    try:     
        ciddata['series'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">シリーズ：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=series/id=\d+/\">(.*)</a></td>',html)[0]
    except:   
        ciddata['series'] = '---'
    try:     
        ciddata['seriesid'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">シリーズ：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=series/id=(\d+)/\">.*</a></td>',html)[0]
    except:   
        ciddata['seriesid'] = '---'
    try:     
        ciddata['maker'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">メーカー：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=maker/id=\d+/\">(.*)</a></td>',html)[0]
    except:   
        ciddata['maker'] = '---'
    try:     
        ciddata['makerid'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">メーカー：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=maker/id=(\d+)/\">.*</a></td>',html)[0]
    except:   
        ciddata['makerid'] = '---'
    try:     
        ciddata['label'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">レーベル：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=label/id=\d+/\">(.*)</a></td>',html)[0]
    except:   
        ciddata['label'] = '---'
    try:     
        ciddata['labelid'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">レーベル：</td>\n?<td><a href=\"/digital/videoa/-/list/=/article=label/id=(\d+)/\">.*</a></td>',html)[0]
    except: 
        ciddata['labelid'] = '---'
    try:     
        ciddata['cid'] = re.findall(r'<td align=\"right\" valign=\"top\" class=\"nw\">品番：</td>[\s\S]*?<td>(.*?)</td>',html)[0]
    except: 
        ciddata['cid'] = '---'
    return (ciddata,notitle)
def prevideo(searchcid):
    video1 = searchcid[0]
    video3 = searchcid[0:3]
    videobase = 'https://cc3001.dmm.co.jp/litevideo/freepv/{}/{}/{}/{}_dmb_w.mp4'.format(video1,video3,searchcid,searchcid)
    return videobase
def prevideolow(searchcid):
    video1 = searchcid[0]
    video3 = searchcid[0:3]
    videobase = 'https://cc3001.dmm.co.jp/litevideo/freepv/{}/{}/{}/{}_sm_w.mp4'.format(video1,video3,searchcid,searchcid)
    return videobase
def prephotos(searchcid):
    searchurl = 'https://www.dmm.co.jp/digital/videoa/-/detail/=/cid={}/'.format(searchcid)
    html = get_html_jp(searchurl)
    soup = BeautifulSoup(html,'lxml')
    photourlss = soup.find_all('img', attrs = {'class':'mg-b6'})
    photourls = re.findall(r'(https://pics.dmm.co.jp/digital/video/.*?/.*?.jpg)', str(photourlss))
    photolist = list(photourls)
    #print(photolist)
    jpg = []
    for i in photolist:
        ii = list(i)
        ii.insert(-6,'jp')
        iii = ''.join(ii)
        iii = iii.replace('-jp','jp-',1)
        jpg.append(iii)
        

    return (jpg)
def template_cid(ciddataa):
    ciddataa_performers = ciddataa.get('performers')
    ciddataa_keyword = ciddataa.get('keyword')
    #print(ciddataa_performers)
    env = Environment(loader=PackageLoader('dmm','templates'))    # 创建一个包加载器对象
    template = env.get_template('base.md')    # 获取一个模板文件
    temp_out = template.render(ciddata = ciddataa, ciddata_performers = ciddataa_performers, ciddata_keyword = ciddataa_keyword) 
    #print(temp_out)  # 渲染
    return (temp_out)
        
    #print(Substitute)
def dmmonecid(searchcid):
    searchcid = searchcid.replace('-','00')
    searchurl = 'https://www.dmm.co.jp/digital/videoa/-/detail/=/cid={}/'.format(searchcid)
    html = get_html_jp(searchurl)
    ciddataa,notitle = ciddata(html)
    if ciddataa == '指定されたページが見つかりません':
        return ciddataa,notitle
    temp_out = template_cid(ciddataa)
    return temp_out, notitle


def dmmsearch_data(searchstr):
    #url = 'https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr=乙白さやか'
    url = 'https://www.dmm.co.jp/digital/videoa/-/list/search/=/limit=30/?searchstr={}'.format(searchstr)
    html = get_html_jp(url)
    #判断有无结果
    try:
        result = re.findall(r'(選択した条件で商品は存在しませんでした)',html)
        noresult = '選択した条件で商品は存在しませんでした'
    except:
        pass
    try:
        if noresult in result:
            stitle = 1
            return (noresult,stitle)
    except Exception:
        pass
    
    soup = BeautifulSoup(html,'lxml')
    searchbody = soup.find('div',attrs = {'class' : 'd-area'})
    try:
        stitle = re.findall(r'<title>(.*?)</title>',html)[0]
    except Exception:
        stitle = '検索結果'
    boxall = searchbody.find_all('li',attrs = {'style' : 'width: 130px;'})
    onebox = str(boxall).split('</div></li>')
    boxlist = []
    for box in onebox:
        boxdict = {}
        notitle = 0
        if box:
            try:
                litetitle = re.findall(r'<span class=\"txt\">(.*?)</span>',box)[0]
                #print(litetitle)
                if litetitle == None:
                    notitle = 1
            except:
                notitle = 1
            try:
                cid = re.findall(r'<a href=\"https://www\.dmm\.co\.jp/digital/videoa/-/detail/=/cid=(\w+)/\?.*?\">',box)[0]
                boxdict['cid'] = cid
            except:
                boxdict['cid'] = '-'
            try:
                keywords = re.findall(r'<span class=\"ico-st-\w+\"><span>(.*?)</span></span>',box)
                keyword = ','.join(keywords)
                boxdict['keyword'] = keyword
            except:
                boxdict['keyword'] = '-'
            try:
                links = re.findall(r'<a href=\"(https://www\.dmm\.co\.jp/digital/videoa/-/detail/=/cid=\w+/\?.*?)\">',box)[0]
                boxdict['links'] = links
            except:
                boxdict['links'] = '-'
            try:
                img = re.findall(r'<span class=\"img\"><img alt=\".*?\" src=\"(https://pics.dmm.co.jp/digital/video/\w+/\w+.jpg)\"/></span>',box)
                boxdict['img'] = img[0]
            except:
                boxdict['img'] = '-'
            try:   
                title = re.findall(r'<span class=\"img\"><img alt=\"(.*?)\" src=\"https://pics.dmm.co.jp/digital/video/\w+/\w+.jpg\"/></span>',box)
                boxdict['title'] = title[0]
            except:
                boxdict['title'] = '-'
            try:   
                sublinks = re.findall(r'<span><a href=\"(/digital/videoa/-/list/search/=/limit=30/.*?)/\">.*?</a></span>',box)
                sublink = 'https://www.dmm.co.jp' + sublinks[0]
                boxdict['sublinks'] = sublink
            except:
                boxdict['sublinks'] = '-'
            try:    
                subtexts = re.findall(r'<span><a href=\"/digital/videoa/-/list/search/=/limit=30/.*?/\">(.*?)</a></span>',box)
                boxdict['subtexts'] = subtexts[0]
            except:
                boxdict['subtexts'] = '-'
            
            if notitle == 0:
                #print(boxdict)
                boxlist.append(boxdict)
    return (boxlist,stitle)
def template_search(resultdataa,stitlee):
    
    env = Environment(loader=PackageLoader('dmm','templates'))    # 创建一个包加载器对象
    template = env.get_template('search.md')    # 获取一个模板文件
    temp_out = template.render(resultdata = resultdataa,stitle = stitlee) 
    #print(temp_out)  # 渲染
    return (temp_out)
def dmmsearch(searchstr,mode='temp'):
    
    result, stitle = dmmsearch_data(searchstr)
    if mode == 'onlysearch':
        return result, stitle
    noresult = '選択した条件で商品は存在しませんでした'
    if result == noresult:
        return noresult
    
    temp_out = template_search(result, stitle)
    return temp_out


def dmmlinks_data(links):
    #url = 'https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr=乙白さやか'
    url = links
    html = get_html_jp(url)
    #判断有无结果
    soup = BeautifulSoup(html,'lxml')
    searchbody = soup.find('div',attrs = {'class' : 'd-area'})
    try:
        stitle = re.findall(r'<title>(.*?)</title>',html)[0]
        #print(stitle)
    except Exception:
        stitle = '検索結果'
    boxall = searchbody.find_all('li',attrs = {'style' : 'width: 130px;'})
    onebox = str(boxall).split('</div></li>')
    boxlist = []
    for box in onebox:
        boxdict = {}
        notitle = 0
        if box:
            try:
                litetitle = re.findall(r'<span class=\"txt\">(.*?)</span>',box)[0]
                #print(litetitle)
                if litetitle == None:
                    notitle = 1
            except:
                notitle = 1
            try:    
                cid = re.findall(r'<a href=\"https://www\.dmm\.co\.jp/digital/videoa/-/detail/=/cid=(\w+)/\?.*?\">',box)[0]
                #print(cid)
                boxdict['cid'] = cid
            except:
                boxdict['cid'] = '-'
            try:
                keywords = re.findall(r'<span class=\"ico-st-\w+\"><span>(.*?)</span></span>',box)
                keyword = ','.join(keywords)
                boxdict['keyword'] = keyword
            except:
                boxdict['keyword'] = '-'
            try:
                links = re.findall(r'<a href=\"(https://www\.dmm\.co\.jp/digital/videoa/-/detail/=/cid=\w+/\?.*?)\">',box)[0]
                boxdict['links'] = links
            except:
                boxdict['links'] = '-'
            try:
                img = re.findall(r'<span class=\"img\"><img alt=\".*?\" src=\"(https://pics.dmm.co.jp/digital/video/\w+/\w+.jpg)\"/></span>',box)
                boxdict['img'] = img[0]
            except:
                boxdict['img'] = '-'
            try:   
                title = re.findall(r'<span class=\"img\"><img alt=\"(.*?)\" src=\"https://pics.dmm.co.jp/digital/video/\w+/\w+.jpg\"/></span>',box)
                boxdict['title'] = title[0]
            except:
                boxdict['title'] = '-'
            try:   
                souplink = BeautifulSoup(box,'lxml')
                slink = souplink.find('p',attrs = {'class' : 'sublink'})
                #print(slink)
                #sublinks = re.findall(r'',box)
            except:
                pass
            try:
                sslink = slink.find('a').get('href')
                sublink = 'https://www.dmm.co.jp' + sslink
                boxdict['sublinks'] = sublink
            except:
                boxdict['sublinks'] = '-'
            try: 
                sstext = slink.find('a').string
                #subtexts = re.findall(r'',box)
                boxdict['subtexts'] = sstext
            except:
                boxdict['subtexts'] = '-'
            
            if notitle == 0:
                #print(boxdict)
                boxlist.append(boxdict)
    return (boxlist,stitle)
def template_links(resultdataa,stitlee):
    
    env = Environment(loader=PackageLoader('dmm','templates'))    # 创建一个包加载器对象
    template = env.get_template('search.md')    # 获取一个模板文件
    temp_out = template.render(resultdata = resultdataa,stitle = stitlee) 
    #print(temp_out)  # 渲染
    return (temp_out)
def dmmlinks(links):
    result, stitle = dmmlinks_data(links)
    #print(result, stitle)
    temp_out = template_links(result, stitle)
    return temp_out

def truevideo(searchcid):
    url = 'https://www.dmm.co.jp/digital/videoa/-/detail/ajax-movie/=/cid={}'.format(searchcid)
    #coding=utf-8

    allconfig = read_config()
    ifproxy = allconfig['ifproxy'] 
    proxy = allconfig['proxy'] 
    system = allconfig['system'] 
    

    # 进入浏览器设置
    options = webdriver.ChromeOptions()
    #谷歌无头模式
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # options.add_argument('window-size=1200x600')
    # 设置语言
    options.add_argument('lang=ja_JP.UTF-8')
    # 更换头部
    options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"')
    #设置代理
    if ifproxy == 'true':
        options.add_argument('proxy-server=' + proxy)

    if system == 'linux':
        browser = webdriver.Chrome(executable_path=r'./chromedriver',options=options)
    elif system == 'windows':
        browser = webdriver.Chrome(executable_path=r'./chromedriver.exe',options=options)
    #browser.set_page_load_timeout(5)    
    
    browser.get(url)
    #print(browser.page_source)
    browser.switch_to.default_content()
    browser.switch_to.frame('DMMSample_player_now')
    video = browser.find_element_by_xpath('//*[contains(@id,"video-video")]')
    
    # 返回播放文件地址
    videourl = browser.execute_script("return arguments[0].currentSrc;",video)
    browser.quit()
    return videourl


def dmmsearchall_data(searchstr):
    #url = 'https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr=乙白さやか'
    url = 'https://www.dmm.co.jp/search/=/searchstr={}/sort=rankprofile/'.format(searchstr)
    html = get_html_jp(url)
    #判断有无结果
    result = re.findall(r'(に一致する商品は見つかりませんでした。)',html)
    noresult = 'に一致する商品は見つかりませんでした。'
    try:
        if noresult in result:
            stitle = 1
            return (noresult,stitle)
    except Exception:
        pass
    
    soup = BeautifulSoup(html,'lxml')
    searchbody = soup.find('div',attrs = {'class' : 'd-area'})
    try:
        stitle = re.findall(r'<title>(.*?)</title>',html)[0]
    except Exception:
        stitle = '検索結果'
    boxall = searchbody.find('div',attrs = {'class' : 'd-sect'})
    onebox = str(boxall).split('<div>')
    
    boxlist = []
    for box in onebox:
        boxdict = {}
        notitle = 0
        if box:
            try:
                litetitle = re.findall(r'<span class=\"txt\">(.*?)</span>',box)[0]
                #print(litetitle)
                if litetitle == None:
                    notitle = 1
            except:
                notitle = 1
            try:
                cid = re.findall(r'<a href=\"https://www\.dmm\.co\.jp/.*?/cid=(\w+)/\?.*?\">',box)[0]
                boxdict['cid'] = cid
            except:
                boxdict['cid'] = '-'
            try:
                keywords = re.findall(r'<span class=\"ico-\w+-\w+\"><span>(.*?)</span></span>',box)
                keyword = ','.join(keywords)
                boxdict['keyword'] = keyword
            except:
                boxdict['keyword'] = '-'
            try:
                links = re.findall(r'<a href=\"(https://www\.dmm\.co\.jp/.*?-/detail/=/cid=\w+/\?.*?)\">',box)[0]
                boxdict['links'] = links
            except:
                boxdict['links'] = '-'
            try:
                img = re.findall(r'(pics\.dmm\.co\.jp/.*?/\w+/\w+.jpg)',box)[0]
                boxdict['img'] = img
            except Exception as e:
                
                boxdict['img'] = '-'
            try:   
                title = re.findall(r'alt=\"(.*)\" src',box)[0]
                boxdict['title'] = title
            except Exception as e:
                
                boxdict['title'] = '-'
            try:   
                sublinks = re.findall(r'<span><a href=\"(.*?)\">.*?</a></span>',box)
                boxdict['sublinks'] = sublinks[0]
            except Exception as e:
                
                boxdict['sublinks'] = '-'
            try:    
                subtexts = re.findall(r'<span><a href=\".*?\">(.*?)</a></span>',box)[0]
                boxdict['subtexts'] = subtexts
            except:
                boxdict['subtexts'] = '-'
            
            if notitle == 0:
                #print(boxdict)
                boxlist.append(boxdict)
    return (boxlist,stitle)
def template_searchall(resultdataa,stitlee):
    
    env = Environment(loader=PackageLoader('dmm','templates'))    # 创建一个包加载器对象
    template = env.get_template('searchall.md')    # 获取一个模板文件
    temp_out = template.render(resultdata = resultdataa,stitle = stitlee) 
    #print(temp_out)  # 渲染
    return (temp_out)
def dmmsearchall(searchstr,mode='temp'):
    
    result, stitle = dmmsearchall_data(searchstr)
    if mode == 'onlysearch':
        return result, stitle
    noresult = 'に一致する商品は見つかりませんでした。'
    if result == noresult:
        return noresult
    
    temp_out = template_searchall(result, stitle)
    return temp_out


       

    
    
    
if __name__ == "__main__":
    print(dmmonecid('ssni00973'))
    #print('1')
    
    
    
