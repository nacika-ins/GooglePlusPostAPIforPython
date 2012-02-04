# -*- coding: utf-8 -*-
'''
Google+ API for Python ver.0.6
'''
import re
import urllib
import urllib2
import cookielib
import time
import datetime
import random
import simplejson as json  # Djangoの場合は # from django.utils import simplejson as json
import os
import socket
import urlparse

#JSON修
def _fixjson(_jsonstr):
    _jsonstr = _jsonstr.replace("\"null\"", "null")
    _jsonstr = _jsonstr.replace("\"false\"", "false")
    _jsonstr = _jsonstr.replace("\"true\"", "true")
    return _jsonstr
    
#JSON
def _jd(*args):
    jsonstr = json.dumps(args, separators=(",", ":"))
    jsonstr = _fixjson(jsonstr)
    return jsonstr

#JSON
def _jd2(*args):
    jsonstr = json.dumps(args, separators=(",", ":"))
    return jsonstr

#JSONの読み込み
def _jsonload(_jsonstr):
    #先頭の2行を削除
    try:
        _jsonstr = r"" + _jsonstr[_jsonstr.index("\n\n"):len(_jsonstr)]
    except:
        pass

    #JSON調整
    strlmode = 0        #文字列リテラルモード
    c = 0
    
    while(1):
        
        #サイズを超えたら抜ける 
        if c >= len(_jsonstr):
            break
        
        #文字列リテラルかどうか
        if (_jsonstr[c - 1] != "\\" or _jsonstr[c - 2:c] == "\\\\") and _jsonstr[c] == "\"":
            strlmode = strlmode ^ 1
            c += 1
            continue

        #文字列リテラル以外
        if strlmode == 0:
            
            #null
            flag = 0
            
            #コンマが続く場合
            if _jsonstr[c:c + 2] == ",,":
                flag = 1
            
            #ブロックの始まり
            if _jsonstr[c:c + 2] == "[,":
                flag = 1

            #ブロックの終わり
            if _jsonstr[c:c + 2] == ",]":
                flag = 1
            
            #NULLを追加する
            if flag == 1:
                _jsonstr = _jsonstr[:c + 1] + "\"null\"" + _jsonstr[c + 1:]
                c += 2 + 4
                c += 1
                continue
            
            #true
            flag = 0
            
            #コンマが続く場合
            if _jsonstr[c:c + 6] == ",true,":
                flag = 1
            
            #ブロックの始まり
            if _jsonstr[c:c + 6] == "[true,":
                flag = 1

            #ブロックの終わり
            if _jsonstr[c:c + 6] == ",true]":
                flag = 1
                
            #両方ブロック
            if _jsonstr[c:c + 6] == "[true]":
                flag = 1
            
            #trueを追加する
            if flag == 1:
                _jsonstr = _jsonstr[:c + 1] + "\"true\"" + _jsonstr[c + 1 + 4:]
                c += 2 + 4
                c += 1
                continue

            #false
            flag = 0
            
            #コンマが続く場合
            if _jsonstr[c:c + 7] == ",false,":
                flag = 1
            
            #ブロックの始まり
            if _jsonstr[c:c + 7] == "[false,":
                flag = 1

            #ブロックの終わり
            if _jsonstr[c:c + 7] == ",false]":
                flag = 1
            
            #両方ブロック
            if _jsonstr[c:c + 7] == "[false]":
                flag = 1
            
            #falseを追加する
            if flag == 1:
                _jsonstr = _jsonstr[:c + 1] + "\"false\"" + _jsonstr[c + 1 + 5:]
                c += 2 + 5
                c += 1
                continue

        
        c += 1
    return json.loads(_jsonstr)

#RequestID
def _reqid():
    reqid = ""
    for i in range(7):
        reqid = reqid + str(random.randint(0, 9))
    return reqid

#funcurl
def _funcurl(_type, _func, _params, _urls, _ispage, _userid):

    if _ispage:
        return _urls["page"] % (_userid, _type, _func, _params, _reqid())
    else:
        return _urls["user"] % (_type, _func, _params, _reqid())

#gpulsfunc
def _gplusfunc(_type, _func, _params, _isflag, _login, _postdata=""):
    
    if _isflag:
        slash = "/"
    else:
        slash = ""
    
    if _postdata:
        #URLエンコード
        params = urllib.urlencode(_postdata)
    
        params = params.replace("%27", "'")
        #####print params
        
    #URLの設定
    sendurl = _funcurl(_type, _func + slash, _params, _login.urls, _login.ispage, _login.userid)
    #print "SendURL: " + sendurl

    #投稿する
    if _postdata:
        return _login.opener.open(sendurl, params).read()
    else:
        return _login.opener.open(sendurl).read()


#ログインする
class Login(object):

    #urls
    urls = {
        "login":        "https://accounts.google.com/login",
        "loginAuth":    "https://accounts.google.com/ServiceLoginAuth",
        "plus":         "https://plus.google.com/",
        "page":         "https://plus.google.com/b/" + "%s" + "/_/" + "%s" + "/" + "%s" + "?" + "%s" + "&_reqid=" + "%s" + "&rt=j",
        "user":         "https://plus.google.com/_/" + "%s" + "/" + "%s" + "?" + "%s" + "&_reqid=" + "%s" + "&rt=j",
        "activity":     "https://plus.google.com/_/stream/getactivities/?sp=%%5B1%%2C2%%2C%%22" + "%s" + "%%22%%2Cnull%%2Cnull%%2C" + "%d" + "%%2Cnull%%2C%%22social%%2Egoogle%%2Ecom%%22%%2C%%5B%%5D%%5D&hl=ja&_reqid=" + "%s" + "&rt=j",
        "activitynode": "https://plus.google.com/_/stream/getactivities/?ct=" + "%s" + "&sp=%%5B1%%2C2%%2C%%22" + "%s" + "%%22%%2Cnull%%2Cnull%%2C" + "%d" + "%%2Cnull%%2C%%22social%%2Egoogle%%2Ecom%%22%%2C%%5B%%5D%%5D&hl=ja&_reqid=" + "%s" + "&rt=j",
        "music":        "https://music.google.com/music/listen?#all_pl",
        "upload1":      "https://plus.google.com/_/upload/photos/resumable?authuser=0",
        "upload2":      "https://plus.google.com/_/upload/photos/resumable?upload_id=" + "%s" + "&file_id=" + "%s",
        "pagenotify":   "https://plus.google.com/b/" + "%s" + "/_/notifications/getnotificationsdata",
        "usernotify":   "https://plus.google.com/_/notifications/getnotificationsdata",
        "hot":          "https://plus.google.com/_/stream/getactivities/?sp=[16,2,null,null,null," + "%s" + ",null,\"social.google.com\",[],null,null,null,null,null,null,[]]&hl=ja&_reqid=" + "%s" + "&rt=j",
        "hotnode":      "https://plus.google.com/_/stream/getactivities/?ct=" + "%s" + "&sp=[16,2,null,null,null," + "%s" + ",null,\"social.google.com\",[],null,null,null,null,null,null,[]]&hl=ja&_reqid=" + "%s" + "&rt=j",
        "comment":      "https://plus.google.com/_/stream/getactivity/?updateId=" + "%s" + "&_reqid=" + "%s" + "&rt=j",
        "stream":       "https://plus.google.com/_/stream/getactivities/?sp=[1,2,null,null,null," + "%s" + ",null,\"social.google.com\",[],null,null,null,null,null,null,[]]&hl=ja&_reqid=" + "%s" + "&rt=j",
        "streamnode":   "https://plus.google.com/_/stream/getactivities/?ct=" + "%s" + "&sp=[1,2,null,null,null," + "%s" + ",null,\"social.google.com\",[],null,null,null,null,null,null,[]]&hl=ja&_reqid=" + "%s" + "&rt=j",
        "search":       "https://plus.google.com/_/s/query?_reqid=" + "%s"
    }
    
    #パラメータ
    params = {
        "login":        "dsh=" + "%s" + "&GALX=" + "%s" + "&pstMsg=1&dnConn=https%%3A%%2F%%2Faccounts.youtube.com&timeStmp=&secTok=&Email=" + "%s" + "&Passwd=" + "%s" + "&signIn=%%E3%%83%%AD%%E3%%82%%B0%%E3%%82%%A4%%E3%%83%%B3&PersistentCookie=yes&rmShown=1",
        "linkurl":        "c=" + "%s" + "&t=1&slpf=0&ml=1"
        }
    
    #正規表現オブジェクト
    d = datetime.datetime.today()
    reg = {
        "sendid":           re.compile(r"\"(AObGSA.*:[0-9]*)\""),
        "userid":           re.compile(r"key: '2', data:[ ]\[.([0-9]*)"),
        "dsh":              re.compile(r"name=\"dsh\" id=\"dsh\" value=\"([-0-9]+)\""),
        "GALX":             re.compile(r"name=\"GALX\"[ \t\n]+value=\"([-_a-zA-Z0-9]+)\""),
        "postid":           re.compile(r"\"(.*)\",\"\",\"s:updates:esshare\""),
        "domain":           re.compile(r"//(.[^/]*)/?"),
        "urlfix":           re.compile(r"^http:(//.*)"),
        "thumbnailtype":    re.compile(r".*\.(.*)$"),
        "comlen":           re.compile(r"\"\d+-\d+-\d+\",([0-9]+),"),
        "notifyuserid":     re.compile(r"\./(.*)"),
        "jsone15":          re.compile(r"(\d+\.\d+)E\d+")
    }
    
    def __init__(self, _mailaddress, _password):
        
        #Cookie
        self.cj = cookielib.LWPCookieJar()
        
        #OpenDirector
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        
        #UserAgent
        self.opener.addheaders = [("User-Agent", "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)")]

        #HTMLの取得
        html = r"" + self.opener.open(Login.urls["login"]).read()
        
        #dsh値の取得
        self.dsh = Login.reg["dsh"].search(html).group(1)
        #####print "dsh: " + self.dsh
        
        #GALX値の取得
        self.GALX = Login.reg["GALX"].search(html).group(1)
        #####print "GALX: " + self.GALX
        
        #ログイン
        self.opener.open(Login.urls["loginAuth"], Login.params["login"] % (self.dsh, self.GALX, _mailaddress, _password)).read()

    #Google+を使用できるようにするオブジェクトを返す
    def plus(self, _pageid):
        
        #HTMLの取得
        try:
            html = r"" + self.opener.open(Login.urls["plus"]).read()
        except:
            print "Login error"
            return 0
        
        #sendidの取得
        self.sendid = Login.reg["sendid"].search(html).group(1)
        #####print "sendid: " + self.sendid
        
        #ページの場合
        if _pageid:
        
            #useridをpageidにする
            self.userid = _pageid
            self.ispage = 1
            
        else:
        
            #useridの取得
            self.userid = Login.reg["userid"].search(html).group(1)
            self.ispage = 0
            
        #####print "userid: " + self.userid
        
        #plusオブジェクトを返す
        return _Plus(self)
        
    #GoogleMusicオブジェクト
    def music(self):
        
        #HTMLの取得
        html = r"" + self.opener.open(Login.urls["music"]).read()
        #####print html
        return _Music(self)

#Google+を使えるようにする
class _Plus(object):
    
    def __init__(self, _login):
        self.login = _login
        self.circleid = ""
        self.iscircle = 0
        self.iscomment = "false"
        self.isshare = "false"
    
    #circleidを設定する
    def circle(self, _circleid):
        
        self.iscircleid = _circleid
        
        if _circleid == "":
            self.iscircle = 0
        else:
            self.iscircle = 1
        
    #コメントをロックする
    def comment(self, _islock):
        if _islock:
            self.iscomment = "true"
        else:
            self.iscomment = "false"
    
    #再共有をロックする
    def share(self, _islock):
        if _islock:
            self.isshare = "true"
        else:
            self.isshare = "false"
    
    #Google+に投稿する
    def post(self):
        return _Post(self.login, self)
        
    #最後にポストしたPOSTIDを取得する
    def activepost(self):
        html = r"" + self.login.opener.open(self.login.urls["activity"] % (self.login.userid, 1, _reqid())).read()
        return self.login.reg["postid"].search(html).group(1)
        
    #最後にポストしたポストのポスト数を取得する
    def comlen(self):
        html = r"" + self.login.opener.open(self.login.urls["activity"] % (self.login.userid, 1, _reqid())).read()
        return int(self.login.reg["comlen"].search(html).group(1))

    #現在の通知数を取得する
    def notifycheck(self):
        try:
            html = _gplusfunc("n", "guc", "poll=false&pid=119", False, self.login, "")
            jsonstr = _jsonload(html)
            ###############print json.dumps(jsonstr, sort_keys=True,indent=4)
            for i in jsonstr[0]:
                if i[0] == "on.uc":
                    num = i[1]
                    break
            return num
        except:
            return 0

    #通知を取得する
    def notify(self):
        return _Notify(self.login)

    #人気の投稿を取得
    def hot(self, _num=20):
        return _Hot(self.login, _num)

    #他の人のポストを取得する
    def activity(self, _userid="", _num=20):
        return _Activity(self.login, _num, "", _userid)
    
    #ストリームを取得する
    def stream(self, _num=20):
        return _Stream(self.login, _num)
    
    #検索結果を取得する
    def search(self, _query, _mode="all", _range="all", _type="new"):
        
        #すべて
        if _mode == "all":
            mode = 1
        #ユーザーとページ
        elif _mode == "peopleandpages":
            mode = 2
        #Google+のポスト
        elif _mode == "posts":
            mode = 3
        #Sparks
        elif _mode == "sparks":
            mode = 4
        #ハングアウト
        elif _mode == "hangouts":
            mode = 5
        
        #全てのユーザー
        if _range == "all":
            ranges = 1
            
        #サークル内
        elif _range == "circles":
            ranges = 2
        
        #自分のみ
        elif _range == "you":
            ranges = 5
        
        #新着順
        if _type == "new":
            types = 2
        
        #関連度順
        elif _type == "best":
            types = 1

        return _Search(self.login, 0, "", "", _query, mode, ranges, types)
    
#投稿取得クラス
class _PostData(object):
    
    #使用するパラメータのみ渡す
    def __init__(self, _postjson, _login=0, _num=0, _node="", _userid="", _query="", _mode="", _range="", _type=""):
        
        self.login = _login
        self.postjson = _postjson
        self.node = _node
        self.num = _num
        self.userid = _userid
        self.query = _query
        self.type = _type
        self.range = _range
        self.mode = _mode
    
    #次のアクティビティを取得
    def nextactivity(self):
        try:
            #nodeを使用する場合は派生クラスにこのパラメータを使用すること
            return self.__class__(self.login, self.num, self.node, self.userid, self.query, self.mode, self.range, self.type)
        except:
            return 0
    
    #ポストの数を取得
    def length(self):
        try:
            return len(self.postjson)
        except:
            return 0

    #投稿者名
    def postusername(self, _num=0):
        try:
            return self.postjson[_num][3].encode("utf-8")
        except:
            return ""
        
    #本文
    def postbody(self, _num=0):
        try:
            #Sparks時の本文があるか調べる
            body = self.postjson[_num][47].encode("utf-8")
            if not body == "null":
                #Sparks
                return body
            else:
                #それ以外
                return self.postjson[_num][4].encode("utf-8")
        except:
            return ""

    #ポストID
    def postid(self, _num=0):
        try:
            return self.postjson[_num][8].encode("utf-8")
        except:
            return ""

    #投稿者ID
    def postuserid(self, _num=0):
        try:
            return self.postjson[_num][16].encode("utf-8")
        except:
            return ""

    #再共有されたポストのIDを取得
    def resharepostid(self, _num=0):
        try:
            postid = self.postjson[_num][39].encode("utf-8")
            if postid != "null" or postid == "":
                return self.postjson[_num][39].encode("utf-8")
            else:
                return ""
        except:
            return ""

    #ポストのパーマリンクURLの取得
    def permalink(self, _num=0):
        try:
            return "https://plus.google.com/" + self.postjson[_num][21].encode("utf-8")
        except:
            return ""
        
    #全体のポストのコメント数を取得(コメント○○ 件と表示されている数値です)
    def commenttotal(self, _num=0):
        try:
            return self.postjson[_num][93]
        except:
            return ""
        
    #表示されているコメント数を取得
    def commentlength(self, _num=0):
        try:
            return len(self.postjson[_num][7])
        except:
            return 0

    #ポストの再共有数を取得
    def sharelength(self, _num=0):
        try:
            return self.postjson[_num][96]
        except:
            return 0

    #ポストの+1の数を取得
    def plusonelength(self, _num=0):
        try:
            plusone = self.postjson[_num][73][16]
            if plusone == "null":
                return 0
            else:
                return plusone
        except:
            return 0

    #通知のコメントの投稿者
    def commentusername(self, _num=0, _comnum=0):
        try:
            return self.postjson[_num][7][_comnum][1].encode("utf-8")
        except:
            return ""

    #通知のコメントの投稿者のID
    def commentuserid(self, _num=0, _comnum=0):
        try:
            return self.postjson[_num][7][_comnum][6].encode("utf-8")
        except:
            return ""
        
    #通知のコメントID
    def commentid(self, _num=0, _comnum=0):
        try:
            return self.postjson[_num][7][_comnum][4].encode("utf-8")
        except:
            return ""

    #通知のコメントの本文
    def commentbody(self, _num=0, _comnum=0):
        try:
            return self.postjson[_num][7][_comnum][2].encode("utf-8")
        except:
            return ""
        
    #コメントの続きを取得
    def comment(self, _postid):
        return _Comment(self.login, _postid)
    
    #SparksIDを取得
    def sparksid(self, _num=0):
        try:
            sparksid = self.postjson[_num][88].encode("utf-8")
            if sparksid:
                return sparksid
            else:
                return ""
        except:
            return ""
    
    #Sparksの見出しを取得
    def sparkstitle(self, _num=0):
        try:
            return self.postjson[_num][11][0][3].encode("utf-8")
        except:
            return ""

    #Sparksの記事の投稿者名を取得
    def sparksauther(self, _num=0):
        try:
            return self.postjson[_num][82][2][3][0].encode("utf-8")
        except:
            return ""

    #Sparksの説明文を取得
    def sparksdescription(self, _num=0):
        try:
            return self.postjson[_num][11][0][21].encode("utf-8")
        except:
            return ""

    #Sparksのリンクを取得
    def sparkslink(self, _num=0):
        try:
            return self.postjson[_num][13].encode("utf-8")
        except:
            return ""

#検索
class _Search(_PostData):
    
    #クラスパラメータは_PostDataと一律でなければいけない(デフォルト値は新規インスタンス作成時に使用しないパラメータに付加)
    def __init__(self, _login, _num=0, _node="", _userid="", _query="", _mode=1, _range=1, _type=2):
        self.login = _login

        jsonstr = _jd(
                        [
                            _query,
                            _mode,
                            _type,
                            [
                                _range
                            ]
                        ],
                        "null",
                        (lambda prm:(
                            [
                                _node
                             ]
                        if prm else
                            []
                        ))(_node)
                    )


        params = {
               "srchrp":    jsonstr,
               "at":        self.login.sendid
               }
        
        
        
        #URLエンコード
        params = urllib.urlencode(params)
    
        #print params
        #print self.login.urls["search"] % _reqid()
        
        html = r"" + self.login.opener.open(self.login.urls["search"] % _reqid(), params).read()

        jsonstr = _jsonload(html)
        ##########print json.dumps(jsonstr, sort_keys=True,indent=4)
        
        for i in jsonstr:
            if i[0].encode("utf-8") == "sp.sqr":
                postjson = i[1][1][0][0]
                try:
                    node = i[1][1][2]
                except:
                    node = ""
                _PostData.__init__(self, postjson, _login, 0, node, "", _query, _mode, _range, _type)
                break
    

#コメントの続きを取得する
class _Comment(_PostData):
    
    def __init__(self, _login, _postid):
        self.login = _login
        html = r"" + self.login.opener.open(self.login.urls["comment"] % (_postid, _reqid())).read()

        #jsonを調整
        try:
            jsonstr = _jsonload(html)
        except:
            jsonstr = []
        
        ####print json.dumps(jsonstr, sort_keys=True,indent=4)
        
        for i in jsonstr[0]:
            if i[0].encode("utf-8") == "os.u":
                postjson = [i[1]]
                _PostData.__init__(self, postjson)
                break

#通知を取得する
class _Notify(_PostData):
    
    #ノードを使用しないためパラメータ制限はない
    def __init__(self, _login):
        self.login = _login
       
        #通知を取得する
        if self.login.ispage:
            html = r"" + self.login.opener.open(self.login.urls["pagenotify"] % self.login.userid).read()
        else:
            html = r"" + self.login.opener.open(self.login.urls["usernotify"]).read()
            
        #通知を既読完了にする
        postdata = {
                    "time":     str(int(time.time())) + str(datetime.datetime.now().microsecond),
                    "at":       self.login.sendid
                    }
        _gplusfunc("notifications", "updatelastreadtime", "", False, self.login, postdata)
        
        #jsonを調整
        try:
            jsonstr = _jsonload(html)
        except:
            jsonstr = []
            
        for i in jsonstr:
            if i[0].encode("utf-8") == "on.nr":
                postjson = []
                self.notifyjson = []
                self.postidjson = []
                for ii in i[1][0]:
                    try:
                        self.notifyjson.append(ii[2][0][1][0])
                    except:
                        self.notifyjson.append([])
                        
                    try:
                        self.postidjson.append(ii[10])
                    except:
                        self.postidjson.append("")
                        
                    try:
                        postjson.append(ii[18][0][0])
                    except:
                        postjson.append([])
                        
                _PostData.__init__(self, postjson)
                ####print json.dumps(self.postjson, sort_keys=True,indent=4)
                break
        #print json.dumps(self.notifyjson, sort_keys=True,indent=4)

    #通知の種類を取得
    def notifystat(self, _num=0):
        try:
            prm = self.notifyjson[_num][1]
            if prm == 2: 
                return "mycomment"
            elif prm == 16:
                return "mention"
            elif prm == 20:
                return "plusone"
            elif prm == 6:
                return "circlein"
            elif prm == 3:
                return "othercomment"
            elif prm == 15:
                return "mention"
            return str(type)
        except:
            return ""
    
    #通知の送信者を取得
    def notifyusername(self, _num=0):
        try:
            return self.notifyjson[_num][2][0].encode("utf-8")
        except:
            return ""

    #通知の送信者のIDを取得
    def notifyuserid(self, _num=0):
        try:
            return self.login.reg["notifyuserid"].search(self.notifyjson[_num][2][1].encode("utf-8")).group(1)
        except:
            return ""

    #通知のポストIDを取得
    def notifypostid(self, _num=0):
        try:
            postid = self.postidjson[_num].encode("utf-8")
            try:
                postid.index("g:")
                return ""
            except:
                return postid
        except:
            return ""
    
    #通知のアイコンを取得
    def notifyicon(self, _num=0):
        try:
            return "http:" + self.notifyjson[_num][2][2].encode("utf-8")
        except:
            return ""
    
    #性別を取得
    def notifysex(self, _num=0, _male="male", _female="female", _other="other"):
        try:
            sex = self.notifyjson[_num][2][4].encode("utf-8")
            if sex == "male":
                return _male
            elif sex == "female":
                return _female
            return _other
        except:
            return ""


#人気の投稿を取得する
class _Activity(_PostData):
    
    #クラスパラメータは_PostDataと一律でなければいけない(デフォルト値は新規インスタンス作成時に使用しないパラメータに付加)
    def __init__(self, _login, _num, _node, _userid, _query="", _mode="", _range="", _type=""):
        self.login = _login
        if _userid == "":
            userid = self.login.userid
        else:
            userid = _userid

        if _node == "":
            html = r"" + self.login.opener.open(self.login.urls["activity"] % (userid, _num, _reqid())).read()
        else:
            html = r"" + self.login.opener.open(self.login.urls["activitynode"] % (_node, userid, _num, _reqid())).read()
        
        jsonstr = _jsonload(html)
        #######print json.dumps(jsonstr, sort_keys=True,indent=4)
        
        for i in jsonstr[0]:
            if i[0].encode("utf-8") == "os.nu":
                postjson = i[1][0]
                try:
                    node = i[1][1]
                except:
                    node = ""
                _PostData.__init__(self, postjson, _login, _num, node, _userid)
                break

#人気の投稿を取得する
class _Hot(_PostData):
    
    #クラスパラメータは_PostDataと一律でなければいけない(デフォルト値は新規インスタンス作成時に使用しないパラメータに付加)
    def __init__(self, _login, _num, _node="", _userid="", _query="", _mode="", _range="", _type=""):
        self.login = _login
        if _node == "":
            html = r"" + self.login.opener.open(self.login.urls["hot"] % (_num, _reqid())).read()
        else:
            html = r"" + self.login.opener.open(self.login.urls["hotnode"] % (_node, _num, _reqid())).read()
        
        jsonstr = _jsonload(html)
        #####print json.dumps(jsonstr, sort_keys=True,indent=4)
        
        for i in jsonstr[0]:
            if i[0].encode("utf-8") == "os.nu":
                postjson = i[1][0]
                try:
                    node = i[1][1]
                except:
                    node = ""
                _PostData.__init__(self, postjson, _login, _num, node)
                break
        
        
#ストリームの投稿を取得する
class _Stream(_PostData):
    
    #クラスパラメータは_PostDataと一律でなければいけない(デフォルト値は新規インスタンス作成時に使用しないパラメータに付加)
    def __init__(self, _login, _num, _node="", _userid="", _query="", _mode="", _range="", _type=""):
        self.login = _login
        if _node == "":
            html = r"" + self.login.opener.open(self.login.urls["stream"] % (_num, _reqid())).read()
        else:
            html = r"" + self.login.opener.open(self.login.urls["streamnode"] % (_node, _num, _reqid())).read()
        
        jsonstr = _jsonload(html)
        #print json.dumps(jsonstr, sort_keys=True,indent=4)
        
        for i in jsonstr[0]:
            if i[0].encode("utf-8") == "os.nu":
                postjson = i[1][0]
                try:
                    node = i[1][1]
                except:
                    node = ""
                _PostData.__init__(self, postjson, _login, _num, node)
                break

    

#Google+に投稿する
class _Post(object):
    
    def __init__(self, _login, _plus):
        self.login = _login
        self.plus = _plus
        self.postcount = 0
    
    #通常投稿
    def _post(self, **kwargs):
    
        #キーが無い場合NULLを代入
        kwargs.setdefault("message", "")
        kwargs.setdefault("reshare", "null")
        kwargs.setdefault("linkurl", "")
        kwargs.setdefault("linkdescription", "")
        kwargs.setdefault("linktitle", "")
        kwargs.setdefault("linktype", "text/html")
        kwargs.setdefault("linkthumbnail", "")
        kwargs.setdefault("linktx", 200)
        kwargs.setdefault("linkty", 200)
        kwargs.setdefault("circleid", "")
        kwargs.setdefault("iscomment", "null")
        kwargs.setdefault("isshare", "null")
        kwargs.setdefault("linkthumbnailtype", "")
        kwargs.setdefault("linkimage", "")
        kwargs.setdefault("uploadimage", "")
        kwargs.setdefault("linkfavicon", "")
        kwargs.setdefault("linknofavicon", False)
        kwargs.setdefault("sparksid", "null")
        
        #限定公開かどうか
        if kwargs["circleid"]:
            scopetype = "focusGroup"
            kwargs.setdefault("circlename", "Limited")
            me = "false"
            groupType = "p"
            
            #circleidの先頭にpが含まれていた場合削除
            if kwargs["circleid"][0] == "p":
                kwargs["circleid"] = kwargs["circleid"][1:len(kwargs["circleid"])]
            
            #circleidにuseridを付加
            kwargs["circleid"] = self.login.userid + "." + kwargs["circleid"]
                
        else:
            #一般公開
            scopetype = "anyone"
            kwargs.setdefault("circlename", "anyone")
            me = "true"
            groupType = "null"
        
        #ファビコン処理
        if not kwargs["linknofavicon"]:
            if kwargs["linkfavicon"]:
                domain = "?domain=" + self.login.reg["domain"].search(kwargs["linkfavicon"]).group(1)
            else:
                if kwargs["linktitle"]:
                    try:
                        domain = "?domain=" + self.login.reg["domain"].search(kwargs["linkurl"]).group(1)
                    except:
                        domain = ""
                        
            
        #コメント可否
        if kwargs["iscomment"] != "null":
            if kwargs["iscomment"]:
                iscomment = "True"
            else:
                iscomment = "False"
        else:
            iscomment = self.plus.iscomment
                
        
        #再共有の可否
        if kwargs["isshare"] != "null":
            if kwargs["isshare"]:
                isshare = "True"
            else:
                isshare = "False"
        else:
            isshare = self.plus.isshare
            
        #サムネイルタイプ
        if kwargs["linktitle"]:
            if kwargs["linkthumbnail"]:
                if kwargs["linkthumbnailtype"]:
                    imagemime = kwargs["linkthumbnailtype"]
                else:
                    imagetype = self.login.reg["thumbnailtype"].search(kwargs["linkthumbnail"]).group(1)
                    if imagetype == "jpg":
                        imagemime = "image/jpeg"
                    elif imagetype == "jpeg":
                        imagemime = "image/jpeg"
                    elif imagetype == "png":
                        imagemime = "image/png"
                    elif imagetype == "bmp":
                        imagemime = "image/bmp"
                    elif imagetype == "gif":
                        imagemime = "image/gif"
                    else:
                        imagemime = "image/jpeg"
        
        #画像の投稿
        if kwargs["uploadimage"]:
            print kwargs["uploadimage"][0]
            
            #json
            uploaddata = _jd2({
                "createSessionRequest": {
                    "fields": [
                        {
                            "external": {
                                "filename": os.path.basename(kwargs["uploadimage"][0]),
                                "formPost": {},
                                "name": "file",
                                "size": os.path.getsize(kwargs["uploadimage"][0])
                            }
                        },
                        {
                            "inlined": {
                                "content": str(int(time.time())) + str(datetime.datetime.now().microsecond / 1000),
                                "contentType": "text/plain",
                                "name": "batchid"
                            }
                        },
                        {
                            "inlined": {
                                "content": "sharebox",
                                "contentType": "text/plain",
                                "name": "client"
                            }
                        },
                        {
                            "inlined": {
                                "content": "true",
                                "contentType": "text/plain",
                                "name": "disable_asbe_notification"
                            }
                        },
                        {
                            "inlined": {
                                "content": "updates",
                                "contentType": "text/plain",
                                "name": "streamid"
                            }
                        },
                        {
                            "inlined": {
                                "content": "true",
                                "contentType": "text/plain",
                                "name": "use_upload_size_pref"
                            }
                        },
                        {
                            "inlined": {
                                "content": self.login.userid,
                                "contentType": "text/plain",
                                "name": "effective_id"
                            }
                        },
                        {
                            "inlined": {
                                "content": self.login.userid,
                                "contentType": "text/plain",
                                "name": "owner_name"
                            }
                        }
                    ]
                },
                "protocolVersion": "0.8"
            })[1:-1]
            
            print "---"
            print uploaddata
            print "---"
            
            #HTMLの取得
            uploaddata = self.login.opener.open(self.login.urls["upload1"], uploaddata).read()
            print uploaddata
            print "---"
            
            #JSONを読み込む
            uploaddata = json.loads(uploaddata)
            
            #JSON一覧
            print json.dumps(uploaddata, sort_keys=True, indent=4)
            
            #アップロードURLの取得
            uploadurl = uploaddata["sessionStatus"]["externalFieldTransfers"][0]["formPostInfo"]["url"]
            print "uploadurl: " + uploadurl
            print "---"
            
            #アップロード開始
            print "ソケットを作成しています"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print "ソケットに接続しています"
            
            print "urlprmを生成しています"
            urlprm = urlparse.urlparse(uploadurl)
            print urlprm
            
            s.connect(urlprm[1], 443)
            
            print "サイズを取得しています"
            size = os.path.getsize(kwargs["uploadimage"][0])
            print size
            totalsent = 0
            print "ファイルを開いています"
            f = open(kwargs["uploadimage"][0], "rb")
            print "ファイルを読み込んでいます"
            data = f.read();
            f.close()
            print "prmを生成します"
            prm = urlprm[2]+"?"+urlprm[4]
            print prm
            print "送信します"
            sent = self.sock.send("POST "+prm+" HTTP/1.0\nContent-Length:"+size+"\n\n")
            totalsent = totalsent + sent
            while totalsent < size:
                print "送信しています"
                sent = self.sock.send(data[totalsent:])
                print sent
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent
            
            
            print uploaddata
            print "---end---"
            
        #投稿する範囲
        scopedata = _jd(
            {
                "aclEntries": [
                    {
                        "scope": {
                            "scopeType":    scopetype, #focusGroup
                            "name":            kwargs["circlename"],
                            "id":            kwargs["circleid"],
                            "me":            me,
                            "requiresKey":    "false",
                            "groupType":    groupType
                        },
                        "role":20
                    },
                    {
                        "scope":{
                            "scopeType":    scopetype,
                            "name":            kwargs["circlename"],
                            "id":            kwargs["circleid"],
                            "me":            me,
                            "requiresKey":    "false",
                            "groupType":    groupType
                        },
                        "role":60
                        
                    }
                ]                                    
            }
            )[1:-1]
        
        #リンク
        if kwargs["linkurl"]:
            linkdata = _jd(_jd(
                "null", "null", "null", kwargs["linktitle"], "null",
                #通常の画像リンク
                (lambda prm:(
                    (
                        (
                            [
                                "null", kwargs["linkimage"], kwargs["linktx"], kwargs["linkty"]
                            ]
                        ) 
                    if prm else
                        (
                            "null"
                        )
                    )
                ))(kwargs["linkimage"]),
                "null", "null", "null",
                [],
                "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", kwargs["linkdescription"], "null", "null",
                [
                    "null", kwargs["linkurl"], "null", kwargs["linktype"], "document"
                ],
                "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null",
                (lambda prm:(
                    (
                        (
                            [
                                [
                                    "null", kwargs["linkimage"], 120, 96.14035087719297
                                ],
                                [
                                    "null", kwargs["linkimage"], 120, 96.14035087719297
                                ]
                            ]

                        ) 
                    if prm else
                        (
                            #ファビコン
                            (lambda prm:(
                                (
                                    (
                                        "null"
                                    ) 
                                if prm else
                                    (
                                        (lambda prm:(
                                            (
                                                (
                                                    [
                                                        [
                                                            "null", "//s2.googleusercontent.com/s2/favicons" + domain, "null", "null"
                                                        ],
                                                        [
                                                            "null", "//s2.googleusercontent.com/s2/favicons" + domain, "null", "null"
                                                        ]
                                                    ]
                                                ) 
                                            if prm else
                                                (
                                                    "null"
                                                )
                                            )
                                        ))(kwargs["linktitle"])
                                    )
                                )
                            ))(kwargs["linknofavicon"])
                        )
                    )
                ))(kwargs["linkimage"]),
                "null", "null", "null", "null", "null",
                [
                    [
                        "null", "", "http://google.com/profiles/media/provider", ""
                    ]
                ]

                ),
                _jd(
    
                "null", "null", "null", "null", "null",
                #サムネイル
                (lambda prm:(
                    (
                        (
                            [
                                "null", kwargs["linkthumbnail"]
                            ]
                        ) 
                    if prm else
                        (
                            "null"
                        )
                    )
                ))(kwargs["linkthumbnail"]),
                "null", "null", "null",
                [],
                "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null",
                (lambda prm:(
                    (
                        (
                            [
                                "null", kwargs["linkurl"], "null", imagemime, "photo", "null", "null", "null", "null", "null", "null", "null", kwargs["linktx"], kwargs["linkty"]
                            ]
                        ) 
                    if prm else
                        (
                            "null"
                        )
                    )
                ))(kwargs["linkthumbnail"]),
                "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null", "null",
                (lambda prm:(
                    (
                        (
                            [
                                [
                                    "null", kwargs["linkthumbnail"], "null", "null"
                                ],
                                [
                                    "null", kwargs["linkthumbnail"], "null", "null"
                                ]
                            ]
                        )
                    if prm else
                        (
                            "null"
                        )
                    )
                ))(kwargs["linkthumbnail"]),
                "null", "null", "null", "null", "null",
                [
                    [
                        "null", "images", "http://google.com/profiles/media/provider", ""
                    ]
                ]
            ))
        else:
            linkdata = "null"

        #spar
        spar = _jd(
                kwargs["message"],
                "oz:%s.%x.%x" % (self.login.userid, int(time.time()), self.postcount),
                kwargs["reshare"],
                "null",
                "null",
                "null",
                linkdata,
                "null",
                scopedata,
                "true",
                [],
                "false",
                "false",
                "null",
                [],
                "false",
                "false",
                "null",
                kwargs["sparksid"],
                "null",
                "null",
                "null",
                "null",
                "null",
                "null",
                "null",
                "null",
                iscomment,
                isshare,
                "false"
            )
            

        #pastdataを設定
        postdata = {
            "spar":        spar,
            "at":        self.login.sendid
        }

        
        #送信
        _gplusfunc("sharebox", "post", "spam=20", True, self.login, postdata)
        self.postcount += 1
        
    #ポストを編集する
    def edit(self, _postid, _message):
    
        #pastdataを設定
        postdata = {
            "spt":        _message,
            "sei":        _postid,
            "sml":        "[]",
            "madl":        "true",
            "at":        self.login.sendid
        }
        
        #送信
        _gplusfunc("stream", "edit", "spam=20", True, self.login, postdata)

    #コメントする
    def comment(self, _postid, _message):
    
        #pastdataを設定
        postdata = {
            "itemId":                _postid,
            "clientId":                "os:" + _postid + ":" + str(int(time.time())) + str(datetime.datetime.now().microsecond / 1000),
            "text":                    _message,
            "timestamp_msec":        str(int(time.time())) + str(datetime.datetime.now().microsecond / 1000),
            "at":                    self.login.sendid
        }

        #送信
        _gplusfunc("stream", "comment", "spam=20", True, self.login, postdata)
        
    #再共有
    def reshare(self, _message="", _postid="", _circleid=""):
        self._post(message=_message, reshare=_postid, circleid=_circleid)
    
    #カスタムリンク
    def customlink(self, _message="", _linkurl="//plus.google.com", _linktitle="", _linkdescription="", _linkthumbnail="", _linkthumbnailtype="", _imagesizex=200, _imagesizey=200):
        self._post(message=_message, linkurl=_linkurl, linktitle=_linktitle, linkdescription=_linkdescription, linkthumbnail=_linkthumbnail, linkthumbnailtype=_linkthumbnailtype, linktx=_imagesizex, linkty=_imagesizey)
        
    #リンク
    def link(self, _message="", _linkurl="", _thumbnailnumber=0):
        
        #URLの設定
        sendurl = _funcurl("sharebox", "linkpreview/", self.login.params["linkurl"] % (_linkurl), self.login.urls, self.login.ispage, self.login.userid)
        
        #パラメータの設定
        params = {
            "susp":        "false",
            "at":        self.login.sendid
        }
        
        #URLエンコード
        params = urllib.urlencode(params)
        
        #HTMLの取得
        html = r"" + self.login.opener.open(sendurl, params).read()
        
        
        try:
            js = _jsonload(html)
        except:
            js = []
        
        #lpdリストを取得
        size = len(js[0])
        for i in range(size):
            if js[0][i][0] == "lpd":
                js = js[0][i]
                break

        #JSON一覧
        ####print json.dumps(js, sort_keys=True, indent=4)
        
        #サムネイルURL一覧を取得
        size = len(js[2])
        linkthumbnaillist = []
        for i in range(size):
            try:
                linkthumbnailurl = js[2][i][5][1].encode("utf-8")
                linkthumbnailtype = js[2][i][24][3].encode("utf-8")
                linkthumbnailsizex = int(js[2][i][24][12])
                linkthumbnailsizey = int(js[2][i][24][13])
            except:
                linkthumbnailurl = ""
                linkthumbnailtype = ""
                linkthumbnailsizex = ""
                linkthumbnailsizey = ""

            linkthumbnaillist.append([linkthumbnailurl, linkthumbnailtype, linkthumbnailsizex, linkthumbnailsizey])
        
        #タイトルを取得        
        try:
            linktitle = js[4][0][3].encode("utf-8")
        except:
            return 0
        
        #descriptionを取得
        try:
            linkdescription = js[4][0][7].encode("utf-8")
        except:
            linkdescription = ""
        
        #Link投稿
        self.customlink(_message, _linkurl, linktitle, linkdescription, linkthumbnaillist[_thumbnailnumber][0], linkthumbnaillist[_thumbnailnumber][1], linkthumbnaillist[_thumbnailnumber][2], linkthumbnaillist[_thumbnailnumber][3])
        return 1


    #通常投稿
    def message(self, _message="", _circleid=""):
        self._post(message=_message, circleid=_circleid)
    
    #画像投稿
    def image(self, _message, *args):
        self._post(message=_message, uploadimage=args)
    
    #ポストのコメントをロックする
    def commentlock(self, _postid):
    
        #pastdataを設定
        postdata = {
            "itemId":        _postid,
            "disable":        "true",
            "at":            self.login.sendid
        }
        
        #送信
        _gplusfunc("stream", "disablecomments", "", True, self.login, postdata)
        
    #ポストのコメントをロックを解除する
    def commentunlock(self, _postid):
    
        #pastdataを設定
        postdata = {
            "itemId":        _postid,
            "disable":        "false",
            "at":            self.login.sendid
        }
        #送信
        _gplusfunc("stream", "disablecomments", "", True, self.login, postdata)

    #sparksを共有する
    def sparks(self, _message, _sparksid):
        self._post(message=_message, sparksid=_sparksid)

#GoogleMusicを使えるようにする
class _Music(object):
    
    def __init__(self, _login):
        self.login = _login
        

#main
#if __name__ == '__main__':

    
    #Googleアカウントにログインす
    print "ログインしています"
    g = Login("メールアドレス", "パスワード")
    
    #Google+を使えるようにする
    print "Google+を使えるようにしています"
    plus = g.plus("ページID")

    

    '''
    #人気の投稿を取得する
    print "検索しています"
    search = plus.search("あ", "sparks", "all", "new")
    #search = plus.activity("", 20)
    count = 0
    
    
    l = search.length()
    
    for i in range(l):
        count += 1
        print "ユーザー名: "+search.postusername(i)
        print "ユーザーID: "+search.postuserid(i)
        print "本文: "+search.postbody(i)
        print "コメント数: "+str(search.commentlength(i))
        print "再共有数: "+str(search.sharelength(i))
        print "+1数: "+str(search.plusonelength(i))
        print "ポストID: "+search.postid(i)
        print "再共有ポストID: "+search.resharepostid(i)
        print "SparksID: "+search.sparksid(i)
        print "SparksTitle: "+search.sparkstitle(i)
        print "SparksDesc: "+search.sparksdescription(i)
        print "SparksAuther: "+search.sparksauther(i)
        print "SparksLink: "+search.sparkslink(i)
        print "カウント: "+str(count)
        print "----------------------------------------"
    '''

    #投稿できるようにする
    #print "投稿できるようにしています"
    post = plus.post()


    #Google Musicを使えるようにする(まだ動かない)
    #music = g.music()

    #コメント禁止
    #plus.comment(True)
    
    #共有禁止
    #plus.share(True)
    
    #投稿オブジェクト
    #post = plus.post()
    
    #Sparksを共有
    #post.sparks("hoge", "ChQxNDcxMDE0ODY5NTY5MDQ4NjI2MxI0WjJodHRwOi8vZ3JlZS5qcC9zaGliYWhhcmFfcmlzYS9ibG9nL2VudHJ5LzYxOTUzNjM2NyIyaHR0cDovL2dyZWUuanAvc2hpYmFoYXJhX3Jpc2EvYmxvZy9lbnRyeS82MTk1MzYzNjc4gPmvutDJrQJqInBlcmZlY3RzdHJlYW06MTQ3MTAxNDg2OTU2OTA0ODYyNjNyTwpC5p+05Y6fIOmHjOe0lyDlhazlvI/jg5bjg63jgrAv5YmN6auq44GC44G/44GT44G/KCrCtNCU772AKikgLSBHUkVFEgl0ZXh0L2h0bWyrAbIBzQIaQuaftOWOnyDph4zntJcg5YWs5byP44OW44Ot44KwL+WJjemrquOBguOBv+OBk+OBvygqwrTQlO+9gCopIC0gR1JFRaoBtQHmn7Tljp8g6YeM57SXIOWFrOW8j+ODluODreOCsC/liY3pq6rjgYLjgb/jgZPjgb8oKsK00JTvvYAqKTog5YmN6auq44GC44G/44GT44G/44GX44Gm44KC44KJ44Gj44Gf4piG5b2hKCrCtNCU772AKikg44Gq44KT44GLIOWkieOBquODneODvOOCuuOBqOOCieOCjOOBnyjnrJEpIOaYvOS8keOBv+alveOBl+OBhCjnrJEpwwHKATJodHRwOi8vZ3JlZS5qcC9zaGliYWhhcmFfcmlzYS9ibG9nL2VudHJ5LzYxOTUzNjM2N9oBCXRleHQvaHRtbOIBCGRvY3VtZW50xAGsAasBsgHWAcMBygEyaHR0cDovL2dyZWUuanAvc2hpYmFoYXJhX3Jpc2EvYmxvZy9lbnRyeS82MTk1MzYzNjfaAQppbWFnZS9qcGVn4gEFcGhvdG/EAcsC0gJCaHR0cDovL3N0MTEyLnN0b3JhZ2UuZ3JlZS5qcC9hbGJ1bS8zNS81OS80NDA0MzU1OS9hNzQzN2Y3MF82NDAuanBn2AJk4AJLzAL7AoIDBmltYWdlc4oDKWh0dHA6Ly9nb29nbGUuY29tL3Byb2ZpbGVzL21lZGlhL3Byb3ZpZGVy/AKsAcoDMmh0dHA6Ly9ncmVlLmpwL3NoaWJhaGFyYV9yaXNhL2Jsb2cvZW50cnkvNjE5NTM2MzY30gUrMAWyASYLEMHbuwkaHQgDGhkiFwoER1JFRRIPaHR0cDovL2dyZWUuanAvDIgGBQ==")
    
    #投稿
    #post._post(message = "", linkurl = "https://lh6.googleusercontent.com/-koN3zNVjPmQ/TtLd--zETTI/AAAAAAAAAAo/sLFReYW56_c/w288-h288/%25E3%2582%25B9%25E3%2582%25AF%25E3%2583%25AA%25E3%2583%25BC%25E3%2583%25B3%25E3%2582%25B7%25E3%2583%25A7%25E3%2583%2583%25E3%2583%2588%25EF%25BC%25882011-11-24%2B9.22.56%25EF%25BC%2589.png", linkimage = "https://lh6.googleusercontent.com/-koN3zNVjPmQ/TtLd--zETTI/AAAAAAAAAAo/sLFReYW56_c/w288-h288/%25E3%2582%25B9%25E3%2582%25AF%25E3%2583%25AA%25E3%2583%25BC%25E3%2583%25B3%25E3%2582%25B7%25E3%2583%25A7%25E3%2583%2583%25E3%2583%2588%25EF%25BC%25882011-11-24%2B9.22.56%25EF%25BC%2589.png")

    #最後にポストした投稿を取得する
    #postid =  post.activepost()
    
    #編集
    #post.edit(postid, "テスト")
    
    #コメントする
    #post.comment("z12kwlrw3ra5d5lwy04ch3vrimayyveqojs", "こんにちは！こんにちは！")

    #再共有
    #post.reshare("test", postid)
    
    #カスタムリンク共有
    post.customlink("test", "http://yahoo.com", "", '<iframe width="560" height="315" src="http://www.youtube.com/embed/BeMZP-oyOII" frameborder="0" allowfullscreen></iframe><iframe width="420" height="315" src="http://www.youtube.com/embed/i7SOhHV3vQ8" frameborder="0" allowfullscreen></iframe><iframe width="560" height="315" src="http://www.youtube.com/embed/bcnT6iYNRqA" frameborder="0" allowfullscreen></iframe><iframe width="560" height="315" src="http://www.youtube.com/embed/yzC4hFK5P3g" frameborder="0" allowfullscreen></iframe><iframe width="560" height="315" src="http://www.youtube.com/embed/MGt25mv4-2Q" frameborder="0" allowfullscreen></iframe>', "", "", 100, 100)
    
    #リンク共有
    #if not post.link("テスト", "http://sample.com/"):
    #    print "ポストに失敗しました"

    
    #画像投稿 (まだ動かない)
    #post.image("test", "/Volumes/Users/Dropbox/nacika/Desktop/a.png")
    
    #通常投稿
    #post.message("テスト")
    #print "投稿しました"
    
    
    ##post._post(message = "メッセージ", linktitle = "タイトル", linkurl = "https://plus.google.com/103944597090770978886/posts/Zjkgg8k2nYV", linkdescription ="ぽ", linknofavicon = True)

    #通知取得
    '''
    print "notifycheck: " + str(plus.notifycheck())
    notify = plus.notify()
    size = notify.length()
    for i in range(size):
        print "username: " + notify.notifyusername(i)
        print "postid: " + notify.notifypostid(i)
        print "status: " + notify.notifystat(i)
        print "icon: " + notify.notifyicon(i)
        print "sex: " + notify.notifysex(i, "男", "女", "その他")
        print "postusername: "+notify.postusername(i)
        print "postuserid: "+notify.postuserid(i)
        print "postbody: "+notify.postbody(i)
        print "commenttotal: "+str(notify.commenttotal(i))
        print "commentlength: "+str(notify.commentlength(i))
        print "    ---------------------------------------"
        for ii in range(notify.commentlength(i)):
            print "    commentusername: "+notify.commentusername(i, ii)
            print "    commentuserid: "+notify.commentuserid(i, ii)
            print "    commentbody: "+notify.commentbody(i, ii)
            print "    commentid: "+notify.commentid(i, ii)
            print "    ---------------------------------------"
        #コメント欄を全取得する    
        ####if notify.postid(i) != "":
            ####comment = notify.comment(notify.postid(i))
            ####for ii in range(comment.commentlength()):
                ####print "    commentusername: "+comment.commentusername(0, ii)
                ####print "    commentuserid: "+comment.commentuserid(0, ii)
                ####print "    commentbody: "+comment.commentbody(0, ii)
                ####print "    ---------------------------------------"
            
        print "-----------------------------------"
    '''
