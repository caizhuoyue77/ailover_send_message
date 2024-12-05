import json
import random
import datetime
import time
import requests
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from concurrent.futures import ThreadPoolExecutor

# 配置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 全局变量
DATA_DIR = "data"  # 存储随机时间点的文件夹
API_BASE_URL = "http://127.0.0.1:9099"  # FastAPI 服务的地址
NICKNAME = "Linda"  # 目标好友昵称
ROLEPLAY_PROMPT = """请你扮演我的男友：秦彻。
# 说话特征：1.说话直接 2.很自信，霸道 3.有Dom的感觉 4.撩人，喜欢反问
# 示例：1.大晚上找我，想我了？ 2.刚刚出去，看见了你最爱的点心，给你带了一份。我是不是对你特别好？ 3.刚醒，好困。"""

MODE_PROMPTS = {
    "default": [
        "你想分享你刚遇到的事情",
        "你想表达一下你想我了",
        "你想搞笑一下，抽象一下",
        "告诉我你刚到家",
        "你想告诉我你准备带点东西回家",
        "现在的时间",
        "分享你刚刚遇到的日常，比如看到的东西或者有趣的事",
        "表达你的情绪，比如觉得累、想我了",
        "直接告诉我你很想我",
        "问问我在干什么",
        "聊聊其他事引发的联想，比如提到某件事让你想到过去的我",
        "表达你伤心或者失望，比如觉得我忽略你了",
        "生我的气",
        "觉得被冷落了，可以用点小抱怨的语气",
        "突然感慨一下，带点深情和撩人的感觉",
        "色诱我一下",
        "提醒我天气"
    ],
    "morning": "说早安",
    "night": "说一下这一天干的事，然后表示要睡了"
}

# 创建数据文件夹（如果不存在）
os.makedirs(DATA_DIR, exist_ok=True)

# 配置调度器
scheduler = BackgroundScheduler()
scheduler.configure(job_defaults={'max_instances': 3})

# 使用线程池优化并发
executor = ThreadPoolExecutor(max_workers=5)


def get_weather_forecast(location_id="101210102", key="66a68b69b6434b56b09a68983aa71a72"):
    """
    获取天气预报信息
    :param location_id: 地区ID (默认杭州地区)
    :param key: API密钥
    :param days: 查询天数
    :return: 天气信息字符串
    """
    # 构建请求的URL
    base_url = "https://devapi.qweather.com/v7/weather/3d"
    params = {
        "location": location_id,
        "key": key,
    }

    try:
        # 发送GET请求
        response = requests.get(base_url, params=params)

        # 检查响应状态码
        if response.status_code == 200:
            # 请求成功，解析JSON数据
            data = response.json()

            # 构建天气信息字符串
            weather_info_str = ""
            for i, day in enumerate(data.get("daily", []), start=1):
                day_name = "今日" if i == 1 else "明日" if i == 2 else "后日"
                weather_info_str += "{}天气：{}度～{}度，{}\n".format(
                    day_name, 
                    day.get("tempMax"), 
                    day.get("tempMin"), 
                    day.get("textDay"), 
                )
            return weather_info_str
        else:
            logging.error(f"获取天气信息失败，状态码: {response.status_code}, 响应: {response.text}")
            return "获取天气信息失败，请稍后再试"
    except Exception as e:
        logging.exception(f"获取天气信息时发生错误: {e}")
        return "天气信息获取失败，请检查网络连接"
    
    
def get_date_filename(target_date):
    """获取存储随机时间点的 JSON 文件名"""
    return os.path.join(DATA_DIR, f"{target_date.strftime('%Y-%m-%d')}.json")

def random_time_in_range(start_hour, end_hour):
    """在指定时间范围内生成随机时间"""
    hour = random.randint(start_hour, end_hour - 1)
    minute = random.randint(15, 30)
    return datetime.time(hour, minute)

def generate_random_times(target_date):
    """为指定日期生成随机时间点，并存储到 JSON 文件"""
    random_times = {
        "morning": random_time_in_range(6, 8),  # 6:00 - 8:59
        "midday": random_time_in_range(8, 12),  # 8:00 - 11:59
        "afternoon": random_time_in_range(12, 17),  # 12:00 - 16:59
        "sunset": random_time_in_range(17, 19), # 17:00 - 18:59
        "evening": random_time_in_range(20, 21),  # 19:00 - 21:59
        "evening2": random_time_in_range(20, 21),  # 19:00 - 21:59
        "evening3": random_time_in_range(20, 21),  # 19:00 - 21:59
        "night": random_time_in_range(22, 23)   # 22:00 - 22:59
    }

    random_times_str = {k: v.strftime("%H:%M:%S") for k, v in random_times.items()}

    json_filename = get_date_filename(target_date)
    with open(json_filename, "w") as f:
        json.dump(random_times_str, f)
    logging.info(f"[生成时间点] 随机时间点生成: {random_times_str}，存储为 {json_filename}")

    # 添加任务
    schedule_messages_for_times(target_date, random_times_str)

def send_message_to_api(nickname, message):
    """通过 FastAPI 的 send_text 接口发送消息"""
    url = f"{API_BASE_URL}/send_text/"
    payload = {"nickname": nickname, "message": message}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info(f"[API 调用成功] 消息发送成功: {message}")
        else:
            logging.error(f"[API 调用失败] 错误信息: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[API 调用异常] 调用失败: {e}")

def get_msg(user_message):
    """通过外部 API 获取消息内容"""
    # api_key = os.getenv("DEEPSEEK_API_KEY")
    api_key = "sk-eb93b1c0ba2542239ac5a7ae8aba98ac"
    if not api_key:
        raise ValueError("API Key not found. Set DEEPSEEK_API_KEY environment variable.")

    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": ROLEPLAY_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "tempeature": 0.9
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logging.error(f"[API 错误] {e}")
        return None

def schedule_messages_for_times(target_date, time_points):
    """为指定日期和时间点添加定时消息任务"""
    for label, time_str in time_points.items():
        time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S").time()
        run_date = datetime.datetime.combine(target_date, time_obj)
        
        
        if run_date > datetime.datetime.now():
            # 获取特定时间段的提示语
            if label == "morning":
                prompt = MODE_PROMPTS["morning"]
            elif label == "night":
                prompt = MODE_PROMPTS["night"]
            else:
                prompt = random.choice(MODE_PROMPTS["default"])
                if "天气" in prompt:
                    weather = get_weather_forecast()
                    prompt = f"{prompt} 天气信息：{weather}"
                    
            msg_content = get_msg(f"现在是 {run_date}. {prompt}. 你会说：")
            if not msg_content:
                continue
            messages = split_into_sentences(msg_content)
            for index, sentence in enumerate(messages):
                delayed_run_date = run_date + datetime.timedelta(seconds=index)
                logging.info(f"[添加任务] 添加任务 {label}-{index + 1}，运行时间: {delayed_run_date} 发送: {sentence}")
                scheduler.add_job(
                    send_message_to_api,
                    DateTrigger(run_date=delayed_run_date),
                    args=[NICKNAME, sentence]
                )
        else:
            logging.info(f"[忽略任务] 时间点 {label} 已经过期: {run_date}")

def split_into_sentences(text):
    """
    按标点符号分割消息为多句，并保留标点符号
    """
    import re
    # 匹配句子并保留标点符号
    sentences = re.split(r'([。！？!?.])', text)
    
    # 合并句子和标点符号
    combined_sentences = [
        sentences[i] + sentences[i + 1] if i + 1 < len(sentences) else sentences[i]
        for i in range(0, len(sentences), 2)
    ]
    return [s.strip() for s in combined_sentences if s.strip()]

def cleanup_old_files(data_dir, days_to_keep=7):
    """清理过期的 JSON 文件"""
    now = datetime.datetime.now()
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path):
            try:
                file_date = datetime.datetime.strptime(filename.split(".")[0], "%Y-%m-%d")
                if (now - file_date).days > days_to_keep:
                    os.remove(file_path)
                    logging.info(f"[清理文件] 删除过期文件: {file_path}")
            except ValueError:
                continue

# 启动时检查当天的 JSON 文件是否存在
today = datetime.date.today()
if not os.path.exists(get_date_filename(today)):
    logging.info(f"[初始化] 检测到 {get_date_filename(today)} 不存在，开始生成随机时间点")
    generate_random_times(today)
else:
    logging.info(f"[初始化] 随机时间点文件已存在，跳过生成步骤")

# 定期清理旧文件
cleanup_old_files(DATA_DIR)

# 启动调度器
scheduler.start()

if __name__ == "__main__":
    logging.info("[启动系统] 消息调度系统已启动")
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("[系统停止] 消息调度系统已停止")