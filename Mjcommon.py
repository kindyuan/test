#-*- coding:utf-8 -*-
import datetime,ConfigParser,MySQLdb,os,arcpy
import json
import urllib
import urllib2
import shutil
import logging

#获取服务器令牌
def gentoken(url, username, password, expiration=60):
    query_dict = {'username': username,
                  'password': password,
                  'expiration': str(expiration),
                  'client': 'requestip'}
    query_string = urllib.urlencode(query_dict)
    print query_string
    return json.loads(urllib.urlopen(url + "?f=json", query_string).read())['token']

#删除服务器文件夹
def deleteFolder(server,folder, username, password, token=None, port=6080):
    if token is None:
        token_url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)
        token = gentoken(token_url, username, password)
    delete_service_url = "http://{}:{}/arcgis/admin/services/{}/deleteFolder?token={}".format(server, port, folder ,token)
    print delete_service_url
    urllib2.urlopen(delete_service_url, ' ').read()

#删除地图服务
def deleteService(server, servicename, username, password, token=None, port=6080):
    if token is None:
        token_url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)
        token = gentoken(token_url, username, password)
    servicename=servicename+".MapServer"
    delete_service_url = "http://{}:{}/arcgis/admin/services/{}/delete?token={}".format(server, port, servicename, token)
    print delete_service_url
    urllib2.urlopen(delete_service_url, ' ').read()

#读取配置文件函数
def readConfig():
    configfile = ConfigParser.ConfigParser()
    configfile.readfp(open("../config.ini"), "rb")
    config={}
    config["workPath"]=configfile.get("global", "workPath")
    config["server_username"]=configfile.get("server","username")
    config["server_password"]=configfile.get("server","password")
    config["server_ip"] = configfile.get("server", "ip")
    config["server_port"] = configfile.get("server", "port")
    config["database_username"]=configfile.get("database","username")
    config["database_password"] = configfile.get("database", "password")
    config["dbname"] = configfile.get("database", "dbname")
    config["database_ip"] = configfile.get("database", "ip")
    config["database_port"] = configfile.get("database", "port")
    return config

#如将"2016-11-23 10:00:00"转换为"2016112310"
def convertTime(timeString):
    return timeString[0:4]+timeString[5:7]+timeString[8:10]+timeString[11:13]

#如将"2016112310"转换为"2016-11-23 10:00:00"
def timeConvert(timeString):
    date=timeString[0:4]+"-"+timeString[4:6]+"-"+timeString[6:8]
    time=timeString[8:10]+":00:00"
    datetimeString=date+" "+time
    return datetimeString

#计算时间推移,如传入参数（2016020512，1）得到2016020513
def timeShift(timeString,deltahours):
    year=int(timeString[0:4])
    month=int(timeString[4:6])
    day=int(timeString[6:8])
    hour=int(timeString[8:10])
    dt=datetime.datetime(year,month,day,hour)
    addhours=datetime.timedelta(hours=deltahours)#计算时间推移
    dt=dt+addhours
    dtString=dt.strftime("%Y%m%d%H")
    return dtString

#计算时间推移，返回[2017/02/28 10:00:00,2017022810]
def timeShiftConvert(stringTime,deltahours):#将按小时推移时间转换为字符串.
    year=int(stringTime[0:4])
    month=int(stringTime[4:6])
    day=int(stringTime[6:8])
    dt=datetime.datetime(year,month,day,0)
    addhours=datetime.timedelta(hours=deltahours)#计算时间推移
    dt=dt+addhours
    timeFiledString=dt.strftime("%Y/%m/%d %H"+":00:00")
    timeLayerString=dt.strftime("%Y%m%d%H")
    timeString=[timeFiledString,timeLayerString]
    return timeString

#获得arcgis for server的ags连接文件
def GetAGSConnectionFile(outdir,config):
    out_folder_path=outdir+"/workspace/ags"
    out_name="magusServerLink.ags"#ags文件名
    server_url="http://"+config["server_ip"]+":"+config["server_port"]+"/arcgis/admin"
    use_arcgis_desktop_staging_folder = False
    staging_folder_path= outdir+"/workspace"
    user_name = config["server_username"]
    password = config["server_password"]
    arcpy.mapping.CreateGISServerConnectionFile("ADMINISTER_GIS_SERVICES",
                                                out_folder_path,
                                                out_name,
                                                server_url,
                                                "ARCGIS_SERVER",
                                                use_arcgis_desktop_staging_folder,
                                                staging_folder_path,
                                                user_name,
                                                password,
                                                "SAVE_USERNAME"
                                                )
    return os.path.join(out_folder_path,out_name)

#传入时间字符串型如"2017-04-12 22:00:00",返回datetime时间对象
def string2datetime(stringTime):
    year=int(stringTime[0:4])
    month=int(stringTime[5:7])
    day=int(stringTime[8:10])
    hour=int(stringTime[11:13])
    dt=datetime.datetime(year,month,day,hour)
    return dt

#计算两个时间之间所有到小时的整点时间，返回数组时间，不包括最小时间。时间格式型如"2017-04-12 22:00:00“
def min2maxTime(minTime,maxTime):
    minDt=string2datetime(minTime)
    maxDt=string2datetime(maxTime)
    dt=maxDt - minDt
    Hs=int(dt.days*24)+int(dt.seconds/3600)
    timeStrings=[]
    for i in range(0,Hs):
        addhours = datetime.timedelta(hours=1)
        minDt=minDt+addhours
        timeString = minDt.strftime("%Y/%m/%d %H" + ":00:00")
        timeStrings.append(timeString)
    return timeStrings

def clearProcessData(workPath):
    processRasterPath=os.path.join(workPath,"workspace","monitor","processraster")
    sdPath = os.path.join(workPath, "workspace", "monitor", "sd")
    paths=[processRasterPath,sdPath]
    for path in paths:
        for clearPath in os.listdir(path):
            shutil.rmtree(clearPath)

#如果文件夹不存在则创建文件夹
def createFolder(path):
    identifyPath = os.path.exists(path)
    if not identifyPath:
        os.mkdir(path)




