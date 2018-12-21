# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
app = Flask(__name__)
def Substr(str, start, stop):
    return str[start:stop + 1]
slack_token = 'xoxb-504131970294-507397687075-1NAlBROQ6ABkFONf90adlcXT'
slack_client_id = '504131970294.507500237986'
slack_client_secret = '67f30dcad5cd896e444d6992a80d748c'
slack_verification = 'FeoFULJS0qmuRISleEtAnVFb'
sc = SlackClient(slack_token)
# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    lisT = []
    lisT = text.split('/')
    if lisT[1] == '구미강동':
        cinemacode = '451'
    elif lisT[1] == '구미공단':
        cinemacode = '167'
    elif lisT[1] == '구미센트럴':
        cinemacode = '705'
    elif lisT[1] == '구미프리미엄':
        cinemacode = '168'
    else:
        cinemacode = '451'
    # URL 데이터를 가져올 사이트 url 입력
    url = "https://movie.naver.com/movie/bi/ti/running.nhn?code=" + cinemacode + "&sdate=" + lisT[2]
    # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
    movie_list = []
    movie_time = []
    pthe_count = 0
    keywords =[]
    for tbody in soup.find_all("tbody"):
        # list.append(trs.get_text())
        for th in tbody.find_all("th"):
            movie_list.append(th.get_text().strip().replace("\n", "").replace("\t", ""))
        for td in tbody.find_all("td"):
            atag = []
            for a in td.find_all("a"):
                atag.append(a.get_text().strip().replace("\n", "").replace("\t", ""))
            movie_time.append(atag)
    if '영화' in lisT[0]:
        for x in range(len(movie_list)):
            keywords.append(movie_list[x] + '\n' + str(movie_time[x]))
    elif Substr(lisT[0],13,len(lisT[0])) in movie_list:
        indexNo = movie_list.index(Substr(lisT[0],13,len(lisT[0])))
        keywords.append(movie_list[indexNo] + '\n' + str(movie_time[indexNo]))
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)
# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])
    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]
        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )
        return make_response("App mention message has been sent", 200, )
    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})
@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })
    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"
if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
