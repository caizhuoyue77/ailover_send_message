import json
import random
import datetime
import time
import requests
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

# 全局变量
DATA_DIR = "data"  # 存储随机时间点的文件夹
API_BASE_URL = "http://127.0.0.1:9099"  # FastAPI 服务的地址
NICKNAME = "努力毕业的cookie"  # 目标好友昵称

# 调度器
scheduler = BackgroundScheduler()

# 创建数据文件夹（如果不存在）
os.makedirs(DATA_DIR, exist_ok=True)

def get_date_filename(target_date):
    """
    获取存储随机时间点的 JSON 文件名
    """
    return os.path.join(DATA_DIR, f"{target_date.strftime('%Y-%m-%d')}.json")

def random_time_in_range(start_hour, end_hour):
    """
    在指定时间范围内生成随机时间
    """
    hour = random.randint(start_hour, end_hour - 1)
    minute = random.randint(0, 59)
    return datetime.time(hour, minute)

def generate_random_times(target_date):
    """
    为指定日期生成随机时间点，并存储到 JSON 文件
    """
    random_times = {
        "morning": random_time_in_range(6, 8),  # 6:00 - 8:59
        "midday": random_time_in_range(8, 12),  # 8:00 - 11:59
        "afternoon": random_time_in_range(12, 17),  # 12:00 - 16:59
        "evening": random_time_in_range(17, 20),  # 17:00 - 19:59
        "night": random_time_in_range(22, 23),  # 22:00 - 22:59
        "test_1": random_time_in_range(18, 19),
        "test_2": random_time_in_range(18, 19),
        "test_3": random_time_in_range(19, 20),
    }

    # 将时间点序列化为字符串
    random_times_str = {k: v.strftime("%H:%M:%S") for k, v in random_times.items()}

    # 保存到 JSON 文件
    json_filename = get_date_filename(target_date)
    with open(json_filename, "w") as f:
        json.dump(random_times_str, f)
    print(f"[生成时间点] 随机时间点生成: {random_times_str}，存储为 {json_filename}")

    # 为生成的时间点添加任务
    schedule_messages_for_times(target_date, random_times_str)

def send_message_to_api(nickname, message):
    """
    通过 FastAPI 的 send_text 接口发送消息
    """
    url = f"{API_BASE_URL}/send_text/"
    payload = {
        "nickname": nickname,
        "message": message
    }
    try:
        print(f"[API 调用] 准备发送消息: {payload}")
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[API 调用成功] 消息发送成功: {message}")
        else:
            print(f"[API 调用失败] 错误信息: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[API 调用异常] 调用失败: {e}")


import requests
import json

def get_msg(user_message):
    api_key = "sk-eb93b1c0ba2542239ac5a7ae8aba98ac"
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a role-play specialist and talks like a bad-ass loving boyfriend. Use short sentences."},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx
        msg = response.json()["choices"][0]["message"]["content"]
        return msg
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}



def schedule_messages_for_times(target_date, time_points):
    """
    为指定日期和时间点添加定时消息任务
    """
    for label, time_str in time_points.items():
        # 解析字符串为时间对象
        time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S").time()
        run_date = datetime.datetime.combine(target_date, time_obj)
        if run_date > datetime.datetime.now():  # 确保时间在未来
            
            prompts = ["你想分享你刚遇到的事情", "你想表达一下你想我了", "你想搞笑一下，抽象一下", "告诉我你刚到家", "你想告诉我你准备带点东西回家"]
            prompt = random.choice(prompts)
            msg_content = get_msg(f"It's now {run_date}. {prompt}. So you said:")
            print(f"[添加任务] 添加任务 {label}，运行时间: {run_date} 发送:{msg_content}")
                        
            scheduler.add_job(
                send_message_to_api,
                DateTrigger(run_date=run_date),
                args=[NICKNAME, msg_content]
            )
        else:
            print(f"[忽略任务] 时间点 {label} 已经过期: {run_date}")

# 启动时检查当天的 JSON 文件是否存在，如果不存在则生成
today = datetime.date.today()
if not os.path.exists(get_date_filename(today)):
    print(f"[初始化] 检测到 {get_date_filename(today)} 不存在，开始生成随机时间点")
    generate_random_times(today)
else:
    print(f"[初始化] 随机时间点文件已存在，跳过生成步骤")

# 启动调度器
scheduler.start()

if __name__ == "__main__":
    print("[启动系统] 消息调度系统已启动")
    try:
        while True:
            pass  # 保持程序运行
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("[系统停止] 消息调度系统已停止")