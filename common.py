# coding=utf-8
import requests,json
import redis
from config import serverinfo as info
import logging

logging.basicConfig(filename='/tmp/ctfdbot.log',level=logging.INFO,format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %X')
redisClent = redis.Redis(host=info.redis["host"],port=info.redis["port"],password=info.redis["password"],decode_responses=True)

# 调用机器人发送消息
def send_group_msg(msg):
    r = requests.post(info.bot_api + "group?id=" + info.group_id,data=msg.encode("utf8"))
    logging.info("send_group_msg res: " + r.text)

def send_user_msg(msg):
    r = requests.post(info.bot_api + "user?id=909712710",data=msg.encode("utf8"))
    logging.info("send_user_msg res: " + r.text)

# redis操作
def redis_get(key):
    return redisClent.get(key)

def redis_set(key,value):
    redisClent.set(key,value)

def redis_hmget(key,id):
    return redisClent.hmget(key,id)

def redis_hmset(key,arr):
    redisClent.hmset(key,arr)

def redis_hlen(key):
    return redisClent.hlen(key)

def json_res(text):
    return json.loads(text)

def get_response_json(url,session):
    res = requests.get(url, cookies={"session":session})
    return json_res(res.text)
