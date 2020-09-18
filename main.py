# coding=utf-8
import re, asyncio, traceback
from common import *

# 检查session
def check_session(session):
    res = requests.head(info.platform_url+"api/v1/tokens", cookies={"session":session})
    # {"success": true, "data": [{"id": 7, "expiration": "2020-04-19T00:00:00+00:00", "type": "user"}]}
    return res.status_code == 200

# 账号登录获取session
def login_get_session():
    login_url = info.platform_url+"login"
    r = requests.get(login_url)
    # 取 nonce
    reg = r'<input id="nonce" name="nonce" type="hidden" value="(.*)">'
    res = r.content.decode('utf-8')
    pattern = re.compile(reg)
    result = pattern.findall(res)
    nonce = result[0]
    # 取 cookie
    cookie = r.headers.get("Set-Cookie")
    cookie = cookie[cookie.index("=")+1:cookie.index(";")]
    # 登录取 session
    res = requests.post(login_url,data={
        "name":info.username,
        "password":info.password,
        "nonce":nonce
    },headers={"Cookie":"session="+cookie}, allow_redirects=False)
    session = res.headers.get("Set-Cookie")
    return session[session.index("=")+1:session.index(";")]

# 取用户列表
def get_user_list(page=1):
    global session
    jsonInfo = get_response_json(info.platform_url + "api/v1/users?page=" + str(page), session)
    if not jsonInfo['success']:
        logging.error("error to get userlist")
        return 0,1,0,[]
    pagination = jsonInfo['meta']['pagination']
    return pagination['total'],pagination['page'],pagination['pages'],jsonInfo['data']

def get_challenge_rank(challenge_id,user_id):
    global session
    jsonInfo = get_response_json(info.platform_url + "api/v1/submissions?type=correct&challenge_id=" + str(challenge_id), session)
    idx = 0
    if not jsonInfo['success']:
        logging.error("error to get attemptlist")
        return idx

    for user in jsonInfo['data']:
        idx += 1
        if user['user_id'] == user_id:
            return idx
    return -1

def get_attempt_list(page=1):
    global session
    jsonInfo = get_response_json(info.platform_url + "api/v1/submissions?type=correct&page=" + str(page), session)
    if not jsonInfo['success']:
        logging.error("error to get attemptlist")
        return 0,1,0,[]
    pagination = jsonInfo['meta']['pagination']
    return pagination['total'],pagination['page'],pagination['pages'],jsonInfo['data']

# 更新并返回session
def update_session():
    global KEY_SESSION
    session = redis_get(KEY_SESSION)
    if not session or not check_session(session):
        session = login_get_session()
        if not session:
            return None
        redis_set(KEY_SESSION, session)
    logging.info("ctfd session: %s",session)
    return session

# 缓存所有用户名到redis，返回总用户数
def update_user_list():
    global KEY_USERNAME
    pre_page_user = 50
    total = redis_hlen(KEY_USERNAME)
    page = pages = int((total - 1)/pre_page_user) + 1
    total_user = 0
    while page <= pages:
        total_user,page,pages,userList = get_user_list(page)
        idname = {}
        for user in userList:
            idname[user['id']] = user['name']
        if len(idname) > 0:
            redis_hmset(KEY_USERNAME, idname)
        page += 1
    return total_user

# 监听新注册用户
async def deal_user_list():
    global SLEEP_SECOND,session,total_user
    while True:
        try:
            session = update_session()
            if not session:
                await asyncio.sleep(SLEEP_SECOND*5)
                continue
            total = get_user_list()[0]
            if total == 0:# 异常
                await asyncio.sleep(SLEEP_SECOND)
                continue
            if total_user < total:# 有新用户注册
                update_user_list()
                total_user = total
            await asyncio.sleep(SLEEP_SECOND)
        except:
            logging.error('[error1]fail to get api info,continue.\n' + traceback.format_exc())
            await asyncio.sleep(SLEEP_SECOND)

# 监听新正确提交
async def deal_attemp_list():
    global SLEEP_SECOND,session,total_correct,sub_page,sub_pages,KEY_USERNAME
    per_page_submit = 20
    page = sub_pages
    while True:
        try:
            session = update_session()
            if not session:
                await asyncio.sleep(SLEEP_SECOND*5)
                continue
            total,page,pages,aList = get_attempt_list(page)
            if total == 0:# 异常
                await asyncio.sleep(SLEEP_SECOND)
                continue
            if total_correct < total:
                # page=1  total_correct=10  total=15    10,15
                # page=1  total_correct=10  total=39    10,20
                # page=2  total_correct=10  total=39    0,19
                # page=1  total_correct=16  total=17
                start = total_correct - (page - 1) * per_page_submit
                if start < 0:
                    start = 0 # 3.跨页重置为0
                for i in range(start,len(aList)):
                    # sub_id = aList[i]['id']
                    user_id = aList[i]['user_id']
                    user_name = redis_hmget(KEY_USERNAME,user_id)[0]
                    challenge_id = aList[i]['challenge_id']
                    challenge = aList[i]['challenge']
                    challenge_name = challenge['name']
                    challenge_category = challenge['category']
                    # 查提交顺序
                    solves = get_challenge_rank(challenge_id,user_id)
                    msg = None
                    if solves == 1:
                        msg = f'恭喜师傅 {user_name} 获得【{challenge_category}】{challenge_name} 一血！'
                    elif solves == 2:
                        msg = f'恭喜师傅 {user_name} 获得【{challenge_category}】{challenge_name} 二血！'
                    elif solves == 3:
                        msg = f'恭喜师傅 {user_name} 获得【{challenge_category}】{challenge_name} 三血！'
                    # else:
                    #     msg = f'恭喜师傅 {user_name} 解出【{challenge_category}】{challenge_name}！'
                    # 报喜
                    if msg:
                        # print(msg)
                        logging.info("send_group_msg: " + msg)
                        send_group_msg(msg)
                if pages == page:
                    # 到最后一页才改变total_correct
                    total_correct = total
                else:
                    page += 1
                logging.info("total_correct: %s, page: %s",total_correct,page)
            await asyncio.sleep(SLEEP_SECOND)
        except:
            logging.error('[error2]fail to get api info,continue.\n' + traceback.format_exc())
            await asyncio.sleep(SLEEP_SECOND)
    pass

if __name__ == '__main__':
    KEY_SESSION = "ctfd_session"
    KEY_USERNAME = "ctfd_user_list"
    SLEEP_SECOND = 3

    session = update_session()
    total_user = update_user_list()
    logging.info("总注册用户数: %s", total_user)
    total_correct,sub_page,sub_pages = get_attempt_list()[:3]
    logging.info("总正确提交数: %s", total_correct)

    loop = asyncio.get_event_loop()
    tasks = [deal_user_list(),deal_attemp_list()]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
