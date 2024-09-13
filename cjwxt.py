import datetime
import hashlib
import json
import re
import time
import configparser
import base64
import requests
import urllib3
import binascii

urllib3.disable_warnings()
import subprocess


# 创建一个新的 Popen 类，并继承自 subprocess.Popen
class MySubprocessPopen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        # 在调用父类（即 subprocess.Popen）的构造方法时，将 encoding 参数直接置为 UTF-8 编码格式
        super().__init__(encoding='UTF-8', *args, **kwargs)


# 必须要在导入 PyExecJS 模块前，就将 subprocess.Popen 类重置为新的类
subprocess.Popen = MySubprocessPopen
import execjs


# =================================================ini课程设置===============================================================
def initialize_config_file():
    with open('config.ini', 'w', encoding='utf-8'):
        pass
    # 创建 ConfigParser 对象
    config = configparser.ConfigParser()

    # 添加 [Cookie] section
    config['Cookie'] = {
        'cookie': '"Cookie-Editor插件导出的Header String格式Cookie"'
    }

    # 添加 [General Setting] section
    config['General Setting'] = {
        'username': '"学号"',
        'password': '"密码"',
        'time_sleep': '0.6',
        'timeout': '2.0'
    }

    # 添加 [Term Setting] section
    config['Term Setting'] = {
        'open_date': '"2024-01-01 09:00:00"',
        'profileId': '""',
        'semesterId': '""'

    }
    # 添加 [User Setting] section
    config['User Setting'] = {
        'user_class_list': '["课程序号1","课程序号2","课程序号3","课程序号4","课程序号5"]',
        'user_class_group_dict': '{"课程序号1":"1","课程序号2":"1"}',
        'user_class_backup_dict': '{"课程序号1":"课程1备选课程序号","课程序号2":"课程2备选课程序号"}'
    }

    config['Waiting Setting'] = {
        'target_class_no': '',
        'drop_class_no': ''
    }

    # 添加 [data] section
    config['data'] = {
        'status': 'False',
        'update_time': '2024-01-01 09:00:00',
        'class_list': 'WyJ4eHh4eHgiXQ==',
        'class_name_dict': 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ==',
        'class_group_dict': 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ==',
        'class_backup_dict': 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ=='
    }

    # 将内容写入 config.ini 文件
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    print(f"[INFO]{datetime.datetime.now().strftime('%H:%M:%S')} 初始化配置文件完成")


# 创建 ConfigParser 对象
config = configparser.ConfigParser()


def read_config():
    global proxies, cookies, username, password, select_open_date, open_date, semesterId, profileId, time_sleep, timeout, data_status, data_update_time, target_class_no, drop_class_no, class_list, class_name_dict, class_group_dict, class_backup_dict

    try:
        with open('config.ini', 'r', encoding='utf-8') as configfile:
            config.read_file(configfile)
    except FileNotFoundError as e:
        initialize_config_file()
        with open('config.ini', 'r', encoding='utf-8') as configfile:
            config.read_file(configfile)

    try:
        proxies = eval(config.get('General Setting', 'proxy'))
        print(f"[PRO]{datetime.datetime.now().strftime('%H:%M:%S')} 正在使用代理服务器{proxies}")
    except Exception as e:
        proxies = {'http': None, 'https': None}

    # 应该往后放
    try:
        cookies = str(config.get('Cookie', 'cookie').strip('\n').strip('"').strip("'"))

        username = config.get('General Setting', 'username').strip('"').strip("'")
        password = config.get('General Setting', 'password').strip('"').strip("'")

        open_date = config.get('Term Setting', 'open_date').strip('"').strip("'")
        try:
            select_open_date = datetime.datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S')
        except:
            print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 选课开放时间格式错误，请检查config.ini")
        semesterId = config.get('Term Setting', 'semesterId').strip('"').strip("'")
        profileId = config.get('Term Setting', 'profileId').strip('"').strip("'")

        time_sleep = config.getfloat('General Setting', 'time_sleep')
        timeout = config.getfloat('General Setting', 'timeout')

        data_status = config.get('data', 'status').strip('"').strip("'")
        data_update_time = config.get('data', 'update_time').strip('"').strip("'")

        target_class_no = config.get('Waiting Setting', 'target_class_no').strip('"').strip("'")
        drop_class_no = config.get('Waiting Setting', 'drop_class_no').strip('"').strip("'")

        class_list = eval(base64.b64decode(config.get('data', 'class_list').encode('utf-8').decode('utf-8')))
        class_name_dict = eval(base64.b64decode(config.get('data', 'class_name_dict').encode('utf-8').decode('utf-8')))
        class_group_dict = eval(
            base64.b64decode(config.get('data', 'class_group_dict').encode('utf-8').decode('utf-8')))
        class_backup_dict = eval(
            base64.b64decode(config.get('data', 'class_backup_dict').encode('utf-8').decode('utf-8')))
    except binascii.Error as e:
        print(
            f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m配置文件[data]损坏,请备份配置文件后进行初始化\033[0m")
        if input("是否清空并初始化配置文件?(y/n):") == 'y':
            initialize_config_file()
        else:
            print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m配置文件初始化失败\033[0m")
            exit()


read_config()

# 预选课链接
pre_select_class_url = f'https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}'
# 剩余人数链接
keep_cookie_url = f'https://jwxt.sias.edu.cn/eams/stdElectCourse!queryStdCount.action?profileId={profileId}&projectId=1&semesterId={semesterId}&_={time.time()}'
# 选课链接
url_select_class = f'https://jwxt.sias.edu.cn/eams/stdElectCourse!batchOperator.action?profileId={profileId}'


# ======================================================================================================================

# 重构data数据
def update_ini_data(cookies_dict):

    if check_cookies():
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[42m\033[30m登录态正常\033[0m")
    else:
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m登录态异常\033[0m")
        return False
    if profileId == "":
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m配置文件profileId未指定!\033[0m")
        return False
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 开始更新配置文件数据")
    update_config_ini('data', 'status', 'False')
    update_config_ini('data', 'update_time', '2024-01-01 09:00:00')
    update_config_ini('data', 'class_list', 'WyJ4eHh4eHgiXQ==')
    update_config_ini('data', 'class_name_dict', 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ==')
    update_config_ini('data', 'class_group_dict', 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ==')
    update_config_ini('data', 'class_backup_dict', 'eyJ4eHh4eHgiOiJ4eHh4eHgifQ==')
    read_config()
    pre_select()
    config = configparser.ConfigParser()
    with open('config.ini', 'r', encoding='utf-8') as configfile:
        config.read_file(configfile)
    user_class_list = eval(config.get('User Setting', 'user_class_list'))
    user_class_group_dict = eval(config.get('User Setting', 'user_class_group_dict'))
    user_class_backup_dict = eval(config.get('User Setting', 'user_class_backup_dict'))
    if '课程序号' in (user_class_list or user_class_group_dict.keys() or user_class_backup_dict.keys()):
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 请先更新User Setting数据")
        return False
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 等待服务器响应")
    # 找课程列表
    session = requests.Session()
    paramsGet = {
        "profileId": profileId
    }
    headers = {
        "Host": "jwxt.sias.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
        "Accept": "*/*",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Referer": f"https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}",
        "Connection": "close", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "script", "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate", "Sec-Fetch-Mode": "no-cors", "Cache-Control": "no-cache",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", "Sec-Ch-Ua-Mobile": "?0"}

    response = session.get("https://jwxt.sias.edu.cn/eams/stdElectCourse!data.action", params=paramsGet,
                           headers=headers,
                           cookies=cookies_dict, proxies=proxies, verify=False)

    data = 'function getVariableA() {' + response.text.strip('\n') + 'return lessonJSONs;}'

    ctx = execjs.compile(data)
    try:
        # 将 JSON 字符串转换为 Python 字典
        js_result = ctx.call('getVariableA')
    except:
        print(
            f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m解析服务器请求失败，可能的原因是profileid不正确，当前profileid={profileId}\033[0m")
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m更新课程配置失败\033[0m")
        return False
    # 打印 Python 对象
    json_result = json.loads(json.dumps(js_result))
    print(
        f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 获取课程列表成功，用时{round(response.elapsed.total_seconds(), 2)}秒")

    # 检查备选课程是否有死循环
    _ = []
    for i, j in user_class_backup_dict.items():
        _.append(i)
        if j in _:
            print(
                f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m注意: user_class_backup_dict陷入死循环 发现{{'{i}':'{j}'}}，但是{i}已经出现过了\033[0m")
            return False

    # 收集所有课程no
    all_class_no = []
    for i in user_class_list:
        all_class_no.append(i)
    for i in user_class_backup_dict.values():
        all_class_no.append(i)
    all_class_group_dict = {}

    # 收集所有课程group
    for i in all_class_no:
        if user_class_group_dict.get(i, False):
            all_class_group_dict[i] = user_class_group_dict[i]
        else:
            all_class_group_dict[i] = None

    # 初始化字典和列表变量
    all_class_name_dict = {}
    all_id_class_dict = {}
    class_list = []
    class_group_dict = {}
    class_backup_dict = {}

    # 开始遍历json文件
    for i in json_result:
        if i['no'] in all_class_group_dict.keys():
            all_class_name_dict[i['id']] = i['name']
            all_id_class_dict[i['no']] = i['id']

            if i['no'] in user_class_list:
                class_list.append(i['id'])

            if i['no'] in user_class_group_dict.keys():
                group_id = str(user_class_group_dict[i['no']])
                for j in i['arrangeInfo']:
                    if group_id == str(j['schLessonGroupNo']):
                        class_group_dict[i['id']] = j['schLessonGroup']
                if not class_group_dict.get(i['id'], False):
                    print(
                        f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m{i['no']}({i['name']})没有找到组号为{group_id}的组\033[0m")
                    return False

    # 根据备份字典，将备份课程id替换为原课程id
    for i, j in user_class_backup_dict.items():
        class_backup_dict[all_id_class_dict[i]] = all_id_class_dict[j]
    update_config_ini('data', 'status', 'True')
    update_config_ini('data', 'update_time', f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    update_config_ini('data', 'class_list', base64.b64encode(str(class_list).encode('utf-8')).decode('utf-8'))
    update_config_ini('data', 'class_name_dict',
                      base64.b64encode(str(all_class_name_dict).encode('utf-8')).decode('utf-8'))
    update_config_ini('data', 'class_group_dict',
                      base64.b64encode(str(class_group_dict).encode('utf-8')).decode('utf-8'))
    update_config_ini('data', 'class_backup_dict',
                      base64.b64encode(str(class_backup_dict).encode('utf-8')).decode('utf-8'))
    read_config()
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 配置文件更新完成")


# 修改ini文件
def update_config_ini(section, key, value):
    try:
        # 修改某个值
        config.set(section, key, value)

        # 使用 utf-8 打开并写入 ini 文件
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

        return True
    except Exception as e:
        print(e)
        return False


def pre_select():
    headers_select_class = {
        "Host": "jwxt.sias.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "close",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://jwxt.sias.edu.cn/eams/loginExt.action"
    }
    cookies_dict = cookie_text_dict()
    # 创建Session对象
    session = requests.Session()

    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 准备进入选课页面")

    pre_num = 3
    while pre_num > 0:
        try:
            # 获取剩余人数
            pre_select_class_response = session.get(pre_select_class_url, headers=headers_select_class,
                                                    cookies=cookies_dict,
                                                    proxies=proxies, verify=False, allow_redirects=False,
                                                    timeout=5)
            if pre_select_class_response.status_code == 200:
                print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 成功进入选课页面")
                result = re.search(
                    r'/eams/stdElectCourse!queryStdCount\.action\?profileId=\d+&projectId=\d+&semesterId=(\d+)',
                    pre_select_class_response.text)
                try:
                    if result.group(1):
                        semesterid = result.group(1)
                        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 更新semesterid为{semesterid}")
                        update_config_ini('Term Setting', 'semesterid', str(semesterid))
                except AttributeError as e:
                    print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m进入选课页面失败,请检查profileid的值，当前为{profileId}\033[0m")
                    print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m更新semesterid失败\033[0m")
                break
            else:
                print(
                    f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 选课页面进入失败,状态码{pre_select_class_response.status_code},剩余重试次数{pre_num}")
                pre_num -= 1
                if pre_num == 0:
                    print(
                        f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 进入选课页面失败,请在浏览器同Cookie情况下手动进入,或手动终止程序后重新运行")
                    break
                time.sleep(time_sleep)
                continue
        except requests.exceptions.Timeout:
            print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 选课页面卡顿,剩余重试次数{pre_num}")
            pre_num -= 1
            if pre_num == 0:
                print(
                    f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 进入选课页面失败,请在浏览器同Cookie情况下手动进入,或手动终止程序后重新运行")
                break
            time.sleep(time_sleep)

            continue


# 抢课
def selectclass(classlist, classlist_name, cookies=''):
    if data_status != 'True':
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 请确保你已经更新过课程数据")
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 本轮选课开放于:{open_date}")
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 课程数据更新于:{data_update_time}")
    headers_select_class = {
        "Host": "jwxt.sias.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "close",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://jwxt.sias.edu.cn/eams/loginExt.action"
    }
    cookies_dict = cookie_text_dict()
    # 创建Session对象
    session = requests.Session()
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 准备进入选课页面")

    pre_num = 3
    while pre_num > 0:
        try:
            pre_select_class_response = session.get(pre_select_class_url, headers=headers_select_class,
                                                    cookies=cookies_dict,
                                                    proxies=proxies, verify=False, allow_redirects=False,
                                                    timeout=timeout)
            if pre_select_class_response.status_code == 200:
                print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 成功进入选课页面")
                break
            else:
                print(
                    f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 选课页面进入失败,状态码{pre_select_class_response.status_code},剩余重试次数{pre_num}")
                pre_num -= 1
                if pre_num == 0:
                    print(
                        f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 进入选课页面失败,请在浏览器同Cookie情况下手动进入,或手动终止程序后重新运行")
                    break
                time.sleep(time_sleep)
                continue
        except requests.exceptions.Timeout:
            print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 选课页面卡顿,剩余重试次数{pre_num}")
            pre_num -= 1
            if pre_num == 0:
                print(
                    f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 进入选课页面失败,请在浏览器同Cookie情况下手动进入,或手动终止程序后重新运行")
                break
            time.sleep(time_sleep)

            continue

    # 等待选课开放
    while datetime.datetime.now() < datetime.datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S'):
        dif_time = (datetime.datetime.strptime(open_date,
                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.now()).total_seconds()
        if dif_time > 120:
            print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 距离选课开放还有:%d 秒" % dif_time)
            keep_cookie(cookies_dict)
            time.sleep(30)
        elif 120 >= dif_time > 50:
            print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 距离选课开放还有:%d 秒" % dif_time)
            keep_cookie(cookies_dict)
            time.sleep(30)
        elif 60 >= dif_time > 20:
            print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 距离选课开放还有:%d 秒" % dif_time)
            keep_cookie(cookies_dict)
            time.sleep(15)
        elif 20 >= dif_time > 5:
            print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 距离选课开放还有:%d 秒" % dif_time)
            keep_cookie(cookies_dict)
            time.sleep(3)
        elif dif_time <= 5:
            # print("距离选课开放还有:%d 秒" % dif_time)
            time.sleep(0.1)

    code = 0
    class_success = []
    class_fail = []
    while code == 0:
        numa = len(classlist)
        numb = 0
        # 保证循环
        while numa > numb:
            # 仍然有课程没有选择完毕进入if
            if numa >= 1:
                cid = classlist[numb]
                classname = classlist_name.get(cid, '未命名课程')
                data_sc = {
                    "optype": 'true',
                    "operator0": str(cid) + ':true:0',
                    "lesson0": str(cid),
                    "schLessonGroup_" + str(cid): class_group_dict.get(int(cid), 'undefined')
                }
                # print("尝试选课:%s" % aa, end="")
                try:
                    # 发送 POST 请求并设置响应超时时间为timeout秒
                    response_class = session.post(url_select_class, headers=headers_select_class, data=data_sc,
                                                  cookies=cookies_dict,
                                                  proxies=proxies, verify=False, allow_redirects=False, timeout=timeout)
                    print(
                        f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 尝试选课:{classname} RT:{round(response_class.elapsed.total_seconds(), 2)}",
                        end="")
                    # 判断响应结果的内容是否包含特定的字符串（"选课成功" 或 "人数已满"）
                    if response_class.text.find("成功") != -1 or response_class.text.find("你已经选过") != -1:
                        print(" \033[42m\033[30m选课成功\033[0m")
                        class_success.append(classname)
                        classlist.remove(cid)
                        numa -= 1  # 进入下一节课
                        time.sleep(time_sleep)
                        continue
                    elif response_class.text.find("人数已满") != -1:
                        print(" \033[43m失败-人数已满！\033[0m")
                        if class_backup_dict.get(cid, '') != '':
                            print(
                                f"[INF]{classname}有备选课程:{classlist_name.get(class_backup_dict[cid], '未命名课程')}")
                            class_fail.append(classname)
                            classlist.remove(cid)
                            classlist.append(class_backup_dict[cid])  # 加入被选课
                            time.sleep(time_sleep)
                            continue
                        else:
                            class_fail.append(classname)
                            classlist.remove(cid)
                            numa -= 1  # 从列表删去该课，相当于进入下一节课
                            # keep_cookie(cookies_dict)
                            # time.sleep(2)
                            continue
                    elif response_class.text.find("冲突") != -1:
                        print(" \033[43m失败-课程发生冲突\033[0m")
                        if class_backup_dict.get(cid, '') != '':
                            print(
                                f"[INF]{classname}有备选课程:{classlist_name.get(class_backup_dict[cid], '未命名课程')}")
                            class_fail.append(classname)
                            classlist.remove(cid)
                            classlist.append(class_backup_dict[cid])  # 加入被选课
                            time.sleep(time_sleep)
                            continue
                        else:
                            class_fail.append(classname)
                            classlist.remove(cid)
                            numa -= 1  # 从列表删去该课，相当于进入下一节课
                            # keep_cookie(cookies_dict)
                            # time.sleep(2)
                            continue
                    elif response_class.text.find("不允许选该课程") != -1:
                        print(" \033[41m\033[30m失败-本轮不允许选该课程，请核对课程代码\033[0m")
                        class_fail.append(classname)
                        classlist.remove(cid)
                        numa -= 1  # 从列表删去该课，相当于进入下一节课
                        time.sleep(time_sleep)
                        continue
                    elif response_class.text.find("不开放") != -1:
                        print(" 失败-选课不开放")
                        numb += 1  # 跳过此课选下一节课
                        time.sleep(time_sleep)
                        continue
                    elif response_class.status_code == 302:
                        print(" \033[41m\033[30m失败-你未进入选课页面\033[0m")
                        class_fail.append(classname)
                        classlist.remove(cid)
                        numa -= 1  # 从列表删去该课，相当于进入下一节课
                        time.sleep(time_sleep)
                        continue
                    elif response_class.text.find("过快点击") != -1:
                        print(" \033[41m\033[30m失败-过快点击,如出现频繁请增加time_sleep参数的值\033[0m")
                        time.sleep(time_sleep)
                        continue
                    else:
                        print(" \033[41m\033[30m未知错误 1.3\033[0m")
                        numb += 1  # 跳过此课选下一节课
                        time.sleep(time_sleep)
                        continue

                except requests.exceptions.Timeout:
                    # 当响应超时时，跳过本次请求，将 numb 加1，等待一段时间后进行下一次循环。
                    print(
                        f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 尝试选课{classlist_name.get(cid, cid)}但服务器响应丢失")
                    numb += 1
                    time.sleep(time_sleep)
                    continue
        if len(classlist) == 0:
            code = 1
        else:
            pass

    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 正在处理结果...")
    print(f"[INF]选课成功:", class_success)
    print(f"[INF]选课失败:", class_fail)
    input(f"[INF]请在数维系统进行确认,此结果仅供参考,按任意键退出")


# 抢课的时候的保持登录模块
def keep_cookie(cookies_dict):
    session = requests.Session()
    paramsGet = {"semesterId": semesterId, "projectId": "1", "profileId": profileId}
    headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
               "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Platform": "\"Windows\"",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
               "Referer": f"https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}",
               "Connection": "close", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "empty",
               "Accept-Encoding": "gzip, deflate", "Sec-Fetch-Mode": "cors",
               "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", "Sec-Ch-Ua-Mobile": "?0"}
    response = session.get("https://jwxt.sias.edu.cn/eams/stdElectCourse!queryStdCount.action", params=paramsGet,
                           headers=headers, cookies=cookies_dict, proxies=proxies, verify=False)
    if response.status_code == 200:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[44m\033[30m正在保持会话\033[0m")
        return True
    else:
        print(
            f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m保持会话出现问题,可能是Cookie失效,状态码{response.status_code}\033[0m")
        return False

# 蹲课，仅支持一节课
def querystudent(target_id):
    """
    单独调用,传参为需要蹲的课的id
    querystudent(target_id)
    当课程有余位时返回True
    """

    cookies_dict = cookie_text_dict()
    target_id = str(target_id)
    while True:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 寻找 id:{target_id}", end='')
        session = requests.Session()
        paramsGet = {"semesterId": semesterId, "projectId": "1", "profileId": profileId}
        headers = {"Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
                   "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Platform": "\"Windows\"",
                   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
                   "Referer": f"https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}",
                   "Connection": "close", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "empty",
                   "Accept-Encoding": "gzip, deflate", "Sec-Fetch-Mode": "cors",
                   "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", "Sec-Ch-Ua-Mobile": "?0"}
        response = session.get("https://jwxt.sias.edu.cn/eams/stdElectCourse!queryStdCount.action", params=paramsGet,
                               headers=headers, cookies=cookies_dict, proxies=proxies, verify=False,
                               allow_redirects=False)
        if response.status_code == 200:
            matches = re.findall(r"'(\d+)':{sc:(\d+),lc:(\d+)}", response.text)
            # 构建字典
            data_dicts = [{'id': match[0], 'sc': match[1], 'lc': match[2]} for match in matches]
            found = False
            for course in data_dicts:
                if course['id'] == target_id:
                    found = True
                    # 找到匹配的课程，获取相应的 no
                    sc = course['sc']
                    lc = course['lc']
                    if sc < lc:
                        print(f" \033[42m\033[30m当前人数{sc}/{lc} 当前人数尚有空余!\033[0m")
                        return True
                    else:
                        print(f" 当前人数{sc}/{lc}")
                    break
            if not found:
                print(f' 未找到')
        elif response.status_code == 302:
            print(f" \033[41m\033[30m请求错误,状态码{response.status_code} 请检查登录状态!!!\033[0m")
        else:
            print(f" \033[41m\033[30m请求错误,状态码{response.status_code}\033[0m")
        time.sleep(5)


def drop_class(uid, cookies):
    session = requests.Session()

    paramsGet = {"profileId": profileId}
    paramsPost = {"lesson0": uid, "optype": "false", "operator0": f"{uid}:false"}
    headers = {"Origin": "https://jwxt.sias.edu.cn",
               "Sec-Ch-Ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Microsoft Edge\";v=\"128\"",
               "Accept": "text/html, */*; q=0.01", "X-Requested-With": "XMLHttpRequest",
               "Sec-Ch-Ua-Platform": "\"Windows\"", "Priority": "u=1, i",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
               "Referer": f"https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}",
               "Connection": "keep-alive", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "empty",
               "Accept-Encoding": "gzip, deflate, br", "Sec-Fetch-Mode": "cors",
               "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", "Sec-Ch-Ua-Mobile": "?0",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    response = session.post(url="https://jwxt.sias.edu.cn/eams/stdElectCourse!batchOperator.action", data=paramsPost,
                            params=paramsGet, headers=headers, cookies=cookies, proxies=proxies, verify=False)

    if response.text.find("退课 成功") != -1:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[42m\033[30m{uid}退课成功\033[0m")
        return True
    else:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m{uid}退课失败\033[0m")
        return False


def waiting_class():
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 请在配置文件中配置Waiting Setting配置")
    print(f"[INF]target_class_no为目标课程的课程序号")
    print(f"[INF]drop_class_no为当目标课程出现空缺，需要退选的课程序号")
    print(f"[INF]暂不支持带小组的课、多节课")
    print(f"[INF]当前配置 目标课程: {target_class_no}", end=' ')
    all_class_list = []
    all_class_list.append(target_class_no)
    if drop_class_no not in ['', 'null', 'None']:
        print(f"退选课程: {drop_class_no}")
        all_class_list.append(drop_class_no)
        drop_status = True
    else:
        print(f"没有退选课程")
        drop_status = False

    if input('是否开始蹲课(y/n)') != 'y':
        return False

    # 检查登录态
    if check_cookies():
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[42m\033[30m登录态正常\033[0m")
    else:
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m登录态异常\033[0m")
        return False
    if profileId == "":
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m配置文件profileId未指定!\033[0m")
        return False
    cookies_dict = cookie_text_dict()
    pre_select()

    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 等待服务器响应")
    # 找课程列表
    session = requests.Session()
    paramsGet = {
        "profileId": profileId
    }
    headers = {
        "Host": "jwxt.sias.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
        "Accept": "*/*",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Referer": f"https://jwxt.sias.edu.cn/eams/stdElectCourse!defaultPage.action?electionProfile.id={profileId}",
        "Connection": "close", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "script", "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate", "Sec-Fetch-Mode": "no-cors", "Cache-Control": "no-cache",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", "Sec-Ch-Ua-Mobile": "?0"}

    response = session.get("https://jwxt.sias.edu.cn/eams/stdElectCourse!data.action", params=paramsGet,
                           headers=headers,
                           cookies=cookies_dict, proxies=proxies, verify=False)

    data = 'function getVariableA() {' + response.text.strip('\n') + 'return lessonJSONs;}'

    ctx = execjs.compile(data)

    # 将 JSON 字符串转换为 Python 字典
    js_result = ctx.call('getVariableA')

    # 打印 Python 对象
    json_result = json.loads(json.dumps(js_result))
    print(
        f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 获取课程列表成功，用时{round(response.elapsed.total_seconds(), 2)}秒")

    all_class_name_dict = {}
    all_id_class_dict = {}

    for i in json_result:
        if i['no'] in all_class_list:
            all_class_name_dict[i['id']] = i['name']
            all_id_class_dict[i['no']] = i['id']

    target_class_id = all_id_class_dict[target_class_no]

    global class_list
    global class_name_dict
    global class_group_dict
    global class_backup_dict

    # 构造data
    class_list = [target_class_id]
    class_name_dict = all_class_name_dict
    class_group_dict = {}

    if drop_status:
        drop_class_id = all_id_class_dict[drop_class_no]
        class_backup_dict = {target_class_id: drop_class_id}
    else:
        drop_class_id = None
        class_backup_dict = {}
    if querystudent(target_class_id):

        if drop_status and len(str(drop_class_id)) == 6:
            print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 开始退课")
            drop_class(drop_class_id, cookie_text_dict())
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 开始选课")
        selectclass(class_list, class_name_dict, cookies)


# 处理cookie，Header String 转换为 dict
def cookie_text_dict():
    """
    登陆时处理预留Cookie,将其处理为在指定格式,转换为Dict格式
    """
    if cookies == '':
        text = ''
        print(f"[INF] 输入0使用账号密码获取cookie")
        print(f"[INF] 或输入导出的cookie数据,Header String格式,以两次回车为结束")
        while True:
            line = input()
            if line == '0':
                return login_jwxt(username, password)
            if line:
                text += line + '\n'
            else:
                break
    else:
        text = cookies
    try:
        cookies_dict = json.loads(text)
    except json.decoder.JSONDecodeError:
        cookies_dict = {cookie.split("=")[0]: cookie.split("=")[1].strip() for cookie in text.split(";")}
    except Exception:
        print(f"[ERR] \033[41m\033[30mCookie非Header String格式且非JSON格式,请检查后重试\033[0m")
        input()
        exit()
    # 当浏览器Cookie有两个JSESSIONID字段时，导出只会留下一个。进入选课系统检查的JSESSIONID应该是和GSESSIONID相等的，否则会报302。
    if 'JSESSIONID' in cookies_dict and 'GSESSIONID' in cookies_dict:
        if cookies_dict['JSESSIONID'] != cookies_dict['GSESSIONID']:
            cookies_dict['JSESSIONID'] = cookies_dict['GSESSIONID']
    elif 'JSESSIONID' in cookies_dict and 'GSESSIONID' not in cookies_dict:
        cookies_dict['GSESSIONID'] = cookies_dict['JSESSIONID']
    elif 'JSESSIONID' not in cookies_dict and 'GSESSIONID' in cookies_dict:
        cookies_dict['JSESSIONID'] = cookies_dict['GSESSIONID']
    else:
        print(f"[ERR]\033[41m\033[30m{datetime.datetime.now().strftime('%H:%M:%S')} Cookie出现问题\033[0m")
        input()
        exit()
    return cookies_dict


# 蹲课的时候用的登录模块，抢课的时候不用此函数获取cookie，因为谁都挤不进去。
def login_jwxt(username, password):
    """
    单独调用,使用账号密码
    """
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 准备登录")
    url = "http://jwxt.sias.edu.cn/eams/loginExt.action"
    headers = {
        "Host": "jwxt.sias.edu.cn",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close"
    }
    session = requests.Session()
    # Cookie请求
    response = session.get(url, headers=headers, proxies=proxies)
    body = response.text
    time.sleep(0.55)

    # IPS拦截判断(悲惨，要不是被拦过，谁知道还有IPS这东西)
    if body.find("An attack was detected") != -1:
        print(
            f"[ERR]\033[41m\033[30m{datetime.datetime.now().strftime('%H:%M:%S')} 请求被拦截，请切换网络环境重试！\033[0m")
        exit()
    elif body.find("账号密码登录") != -1:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 获取登录Cookie-成功  RT:",
              response.elapsed.total_seconds())
    else:
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 未知错误！1.1")
        exit()
    # 哈希加盐
    sha1key = re.search(r"CryptoJS\.SHA1\('(.*?)' \+ form\['password']\.value\)", body).group(1)
    password = sha1key + password
    password_sha = hashlib.sha1(password.encode("utf-8")).hexdigest()

    # 设置登录用Cookie和Header
    url_login = 'http://jwxt.sias.edu.cn/eams/loginExt.action'
    headers_login = {
        "Host": "jwxt.sias.edu.cn",
        "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://jwxt.sias.edu.cn/eams/loginExt.action"
    }

    # 账号密码—SHA1加盐
    data_login = {
        "username": username,
        "password": password_sha,
        "session_locale": "zh_CN"
    }

    # 登录请求
    session.get('http://jwxt.sias.edu.cn/favicon.ico', headers=headers)
    response_login = session.post(url_login, headers=headers_login, data=data_login, allow_redirects=False,
                                  proxies=proxies)
    cookie_dict = session.cookies.get_dict()  # 获取cookie为字典
    if response_login.status_code == 302:
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 登陆成功  RT:",
              response_login.elapsed.total_seconds())
    elif response_login.text.find("密码错误") != -1 or response_login.text.find("密码异常") != -1:
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 账号或密码错误，请重试  RT:",
              response_login.elapsed.total_seconds())
        exit()

    # 访问首页
    url_index = "http://jwxt.sias.edu.cn/eams/homeExt.action"
    requests_index = session.get(url_index, headers=headers_login, proxies=proxies)

    if requests_index.text.find("我的课表") != -1:
        uname = re.search('personal-name"> (.*?)\(\d+', requests_index.text).group(1)
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 学生姓名:%s  RT:" % uname,
              requests_index.elapsed.total_seconds())
        return cookie_dict
    else:
        print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} 访问首页-未知错误！1.2")
        exit()

def check_cookies():
    cookies_dict = cookie_text_dict()
    session = requests.Session()
    headers = {
        "Host": "jwxt.sias.edu.cn",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close"
    }
    # 访问首页
    url_index = "http://jwxt.sias.edu.cn/eams/homeExt.action"
    requests_index = session.get(url_index, headers=headers, proxies=proxies, cookies=cookies_dict)

    if requests_index.text.find("我的课表") != -1:
        uname = re.search('personal-name"> (.*?)\(\d+', requests_index.text).group(1)
        keep_cookie(cookies_dict)
        return True
    else:
        return False


def show_class():
    if 'xxxxxx' in class_list or 'xxxxxx' in class_backup_dict.keys() or 'xxxxxx' in class_group_dict.keys():
        print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 请先使用选项3更新数据库")
        return False

    for _ in class_list:
        print(f"{_}:{class_name_dict.get(_, '未知课程，请检查课程序号')}", end='')
        if _ in class_group_dict.keys():
            print(f" 组{class_group_dict[_]}", end='')

        i = _
        while i in class_backup_dict.keys():
            print(f" 备选课程{class_backup_dict[i]}", end='')
            if class_backup_dict[i] in class_group_dict.keys():
                print(f" 组{class_group_dict[class_backup_dict[i]]}")
            i = class_backup_dict.get(class_backup_dict[i], None)

        print()


def help_menu():
    print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} 菜单帮助")
    print(f"0.检查 Cookie登录态用于判断你的Cookie是否有效")
    print(f"1.选课 将会按照配置文件数据自动进行选课")
    print(f"2.查看当前课程 查看配置文件中的Data数据")
    print(f"3.更新课程数据 根据配置文件中User Setting更新Dara数据")
    print(f"4.蹲课 根据课程序号蹲课，当目标课程出现空余，可及时自动选课")
    print(f"5.初始化数据库 慎重！清空并初始化配置文件数据！")


def menu():
    print(f"[+]=================={datetime.datetime.now().strftime('%H:%M:%S')}==================")
    print(f"[|] 请输入序号选择功能")
    print(f"[|] 0.检查Cookie登录态")
    print(f"[|] 1.选课")
    print(f"[|] 2.查看当前课程")
    print(f"[|] 3.更新课程数据")
    print(f"[|] 4.蹲课")
    print(f"[|] 5.初始化数据库")
    print(f"[|] 6.帮助")
    print(f"[|] 单击回车键退出")
    print(f"[+]============================================")
    try:
        menu_select = input('请选择:')
        if len(menu_select) == 0:
            exit()
        menu_select = int(menu_select)
        if menu_select == 0:
            if check_cookies():
                print(f"[INF]{datetime.datetime.now().strftime('%H:%M:%S')} \033[42m\033[30m登录态正常\033[0m")
            else:
                print(f"[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} \033[41m\033[30m登录态异常\033[0m")
        elif menu_select == 1:
            selectclass(class_list, class_name_dict, cookies)
        elif menu_select == 2:
            show_class()
        elif menu_select == 3:
            update_ini_data(cookie_text_dict())
        elif menu_select == 4:
            waiting_class()
        elif menu_select == 5:
            print("慎重！清空并初始化配置文件数据！")
            if input("是否继续？(y/n):") == 'y':
                initialize_config_file()
        elif menu_select == 6:
            help_menu()
        else:
            print(f'不存在的选项')
        input("按任意键回到菜单...")
        return menu()
    except Exception as e:
        print(f"\033[41m\033[30m[ERR]{datetime.datetime.now().strftime('%H:%M:%S')} MENU\033[0m")
        print(e)
        input()
        exit()


if __name__ == '__main__':
    print("""\033[31m        _                  _        \033[0m
\033[32m       (_)                | |       \033[0m
\033[33m   ___  _ __      ____  __| |_      \033[0m
\033[34m  / __|| |\ \ /\ / /\ \/ /| __|     \033[0m
\033[35m | (__ | | \ V  V /  >  < | |_      \033[0m
\033[36m  \___|| |  \_/\_/  /_/\_\ \__|     \033[0m
\033[37m      _/ |                          \033[0m
\033[34m     |__/                v4.9.13 by sj\033[0m
    """)
    menu()

"""
version 4.9.13
Last modified at 2024-09-13
Copyright (C) 2024 sj

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
