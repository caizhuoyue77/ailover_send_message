from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import itchat
import requests
import io
import os

# 创建 FastAPI 应用
app = FastAPI()

# 微信登录
itchat.auto_login(hotReload=True)

# 定义请求数据模型
class TextRequest(BaseModel):
    nickname: str  # 好友昵称
    message: str   # 要发送的文本消息

class PhotoRequest(BaseModel):
    nickname: str  # 好友昵称
    url: str       # 网络图片的 URL 或本地文件路径

class VoiceRequest(BaseModel):
    nickname: str  # 好友昵称
    url: str       # 网络语音的 URL 或本地文件路径

@app.post("/send_text/")
def send_text(request: TextRequest):
    """
    根据昵称发送文本消息
    :param request: 包含好友昵称和文本内容
    :return: 成功或失败信息
    """
    # 获取好友列表
    friends = itchat.get_friends()
    # 查找指定昵称的好友
    friend = next((f for f in friends if f['NickName'] == request.nickname), None)

    if not friend:
        raise HTTPException(status_code=404, detail=f"未找到昵称为 '{request.nickname}' 的好友")

    try:
        # 发送文本消息
        itchat.send(request.message, toUserName=friend['UserName'])
        return {"status": "success", "message": f"消息已发送给 '{request.nickname}'", "content": request.message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {e}")

@app.post("/send_photo/")
def send_photo(request: PhotoRequest):
    """
    根据昵称发送照片
    :param request: 包含好友昵称和图片URL或本地路径
    :return: 成功或失败信息
    """
    # 获取好友列表
    friends = itchat.get_friends()
    # 查找指定昵称的好友
    friend = next((f for f in friends if f['NickName'] == request.nickname), None)

    if not friend:
        raise HTTPException(status_code=404, detail=f"未找到昵称为 '{request.nickname}' 的好友")

    try:
        # 判断是否是本地文件路径
        if os.path.isfile(request.url):
            # 发送本地图片
            itchat.send_image(request.url, toUserName=friend['UserName'])
            return {"status": "success", "message": f"本地图片已发送给 '{request.nickname}'", "path": request.url}
        else:
            # 下载网络图片
            response = requests.get(request.url, stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="无法下载图片，请检查图片 URL 是否有效")

            # 将图片加载到内存
            image_storage = io.BytesIO(response.content)
            image_storage.seek(0)

            # 发送图片
            itchat.send_image(image_storage, toUserName=friend['UserName'])
            return {"status": "success", "message": f"网络图片已发送给 '{request.nickname}'", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送图片失败: {e}")

@app.post("/send_voice/")
def send_voice(request: VoiceRequest):
    """
    根据昵称发送语音消息
    :param request: 包含好友昵称和语音URL或本地路径
    :return: 成功或失败信息
    """
    # 获取好友列表
    friends = itchat.get_friends()
    # 查找指定昵称的好友
    friend = next((f for f in friends if f['NickName'] == request.nickname), None)

    if not friend:
        raise HTTPException(status_code=404, detail=f"未找到昵称为 '{request.nickname}' 的好友")

    try:
        # 判断是否是本地文件路径
        if os.path.isfile(request.url):
            # 发送本地语音
            itchat.send_file(request.url, toUserName=friend['UserName'])
            return {"status": "success", "message": f"本地语音已发送给 '{request.nickname}'", "path": request.url}
        else:
            # 下载网络语音文件
            response = requests.get(request.url, stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="无法下载语音文件，请检查语音 URL 是否有效")

            # 将语音加载到内存
            voice_storage = io.BytesIO(response.content)
            voice_storage.seek(0)

            # 发送语音
            itchat.send_file(voice_storage, toUserName=friend['UserName'])
            return {"status": "success", "message": f"网络语音已发送给 '{request.nickname}'", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送语音消息失败: {e}")

@app.get("/")
def read_root():
    return {"message": "欢迎使用微信消息发送API！"}