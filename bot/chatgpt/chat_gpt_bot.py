# encoding:utf-8

import time


import openai
import openai.error
import requests
from lxml import etree
from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, load_config
import requests
import random

import QWeatherAPI
from myKey import KEY
ddl_list = []
''' official website  https://www.qweather.com '''
'''      dev website  https://dev.qweather.com'''
mykey = '&key=' + KEY # EDIT HERE!

url_api_weather = 'https://devapi.qweather.com/v7/weather/'
url_api_geo = 'https://geoapi.qweather.com/v2/city/'
url_api_rain = 'https://devapi.qweather.com/v7/minutely/5m'
url_api_air = 'https://devapi.qweather.com/v7/air/now'

def get(api_type):
    url = url_api_weather + api_type + '?location=' + '101280601' + mykey
    return requests.get(url).json()

def rain(lat, lon):
    url = url_api_rain  + '?location=' + lon + ',' + lat + mykey
    return requests.get(url).json()

def air(city_id):
    url = url_api_air + '?location=' + '101280601' + mykey
    return requests.get(url).json()

def getfirsttext(list):
    """
    返回列表中第一个元素
    :return:
    """
    try:
        return list[0].strip()
    except:
        return ""

def get_random_pic_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                random_index = random.randint(0, len(data) - 1)
                return data[random_index]
            else:
                print("返回的数据格式不正确或为空列表")
        else:
            print(f"请求失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"发生异常：{e}")
    return None

# OpenAI对话模型API (可用)
class ChatGPTBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        # set the default api_key
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))

        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[CHATGPT] session query={}".format(session.messages))

            api_key = context.get("openai_api_key")
            model = context.get("gpt_model")
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)


            reply_content = self.reply_text(session, api_key, args=new_args)

            logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                if "还是" in query:
                    a = query.split("还是")[0]
                    b = query.split("还是")[1]
                    c = random.randint(0, 100)
                    if c>=50:
                        reply_content["content"] = a
                    else:
                        reply_content["content"] = b
                elif "lyc" in query:
                    reply_content["content"]= "lyc别装逼"
                elif "sp" in query:
                    reply_content["content"] = "sp傻逼"
                elif "cxsj" in query:
                    reply_content["content"] = "彭嘉新"
                elif "历史版本" in query:
                    reply_content["content"] = "5月7日bot更新(版本0.2.0)\n更新内容：\n【增加功能】查看天气\n【增加功能】查看微博热搜\n【增加功能】骂人功能"
                elif "版本" in query:
                    reply_content["content"] = "5月8日bot更新(版本0.2.1)\n更新内容：\n【修复】稳定了bot的骂人功力\n【修复】修复了sp和lyc在判断中的优先级\n【增加功能】帮忙选择 句内有“还是”两个字时 我会帮你做选择\n【增加功能】支持版本/历史版本查询\n\n每日0:00-10:00准时维护更新 无法使用"
                elif "下次顺序" in query:
                    reply_content["content"] = "lh1 lyc2 jhl3 sp4"
                elif "顺序" in query:
                    reply_content["content"] = "lyc1 jhl2 sp3 lh4"
                elif "mmw" in query:
                    reply_content["content"] = "妹妹婉婉嘞"
                elif "天气" in query:
                    reply_content["content"] = QWeatherAPI.aaa()
                elif "图" in query:
                    random_pic_link_url = "https://api.yimian.xyz/img?type=moe"
                    random_pic_url = get_random_pic_url(random_pic_link_url)
                    reply_content["content"] = random_pic_url
                elif "热搜" in query:
                    if "前" in query:
                        num = query.split("前")[1]
                        try:
                            number = int(num)
                            print("转换成功:", number)
                            url = "https://tophub.today/n/KqndgxeLl9"
                            headers = {
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.69'
                            }
                            res = requests.get(
                                url=url,
                                headers=headers
                            )

                            html = etree.HTML(res.text)
                            trs = html.xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/table/tbody/tr')

                            sb = ''
                            a = 0
                            for tr in trs:
                                sb += getfirsttext(tr.xpath('./td[1]/text()'))
                                sb += getfirsttext(tr.xpath('./td[2]/a/text()'))
                                sb += getfirsttext(tr.xpath('./td[3]/text()'))
                                sb += "\n"
                                a += 1
                                if a == number:
                                    break
                            reply_content["content"] = sb
                        except ValueError:
                            reply_content["content"] = "‘前xx’后面不能加其他汉字"
                    else:
                        url = "https://tophub.today/n/KqndgxeLl9"
                        headers = {
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.69'
                        }
                        res = requests.get(
                            url=url,
                            headers=headers
                        )

                        html = etree.HTML(res.text)
                        trs = html.xpath('/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[1]/table/tbody/tr')

                        sb = ''
                        a=0
                        for tr in trs:
                            sb += getfirsttext(tr.xpath('./td[1]/text()'))
                            sb += getfirsttext(tr.xpath('./td[2]/a/text()'))
                            sb += getfirsttext(tr.xpath('./td[3]/text()'))
                            sb += "\n"
                            a += 1
                            if a == 15:
                                break
                        reply_content["content"] = sb
                elif "操" or "妈" or "死" or "傻" or "b" or "c" or "草" or "逼" in query:
                    try:
                        response = requests.get("https://act.jiawei.xin:10086/lib/api/maren.php?catalog=yang")
                        #common qiu yang
                        if response.status_code == 200:
                            reply_content["content"] = response.text.strip()  # 返回去除首尾空白字符的文本
                        else:
                            print(f"请求失败，状态码：{response.status_code}")
                    except Exception as e:
                        print(f"发生异常：{e}")

                reply = Reply(ReplyType.TEXT, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, retstring)
            else:
                reply = Reply(ReplyType.ERROR, retstring)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, api_key=None, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        result = {"completion_tokens": 0, "content": "如果你有其他问题或需要帮助，请随时告诉我，我会尽力提供帮助。"}
        # try:
        #     if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
        #         raise openai.error.RateLimitError("RateLimitError: rate limit exceeded")
        #     # if api_key == None, the default openai.api_key will be used
        #     if args is None:
        #         args = self.args
        #     response = openai.ChatCompletion.create(api_key=api_key, messages=session.messages, **args)
        #     # logger.debug("[CHATGPT] response={}".format(response))
        #     # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
        #     return {
        #         "total_tokens": response["usage"]["total_tokens"],
        #         "completion_tokens": response["usage"]["completion_tokens"],
        #         "content": response.choices[0]["message"]["content"],
        #     }
        # except Exception as e:
        #     need_retry = retry_count < 2
        #     result = {"completion_tokens": 0, "content": "???"}
        #     if isinstance(e, openai.error.RateLimitError):
        #         logger.warn("[CHATGPT] RateLimitError: {}".format(e))
        #         result["content"] = "提问太快啦，请休息一下再问我吧"
        #         if need_retry:
        #             time.sleep(20)
        #     elif isinstance(e, openai.error.Timeout):
        #         logger.warn("[CHATGPT] Timeout: {}".format(e))
        #         result["content"] = "我没有收到你的消息"
        #         if need_retry:
        #             time.sleep(5)
        #     elif isinstance(e, openai.error.APIError):
        #         logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
        #         result["content"] = "请再问我一次"
        #         if need_retry:
        #             time.sleep(10)
        #     elif isinstance(e, openai.error.APIConnectionError):
        #         logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
        #         result["content"] = "我连接不到你的网络"
        #         if need_retry:
        #             time.sleep(5)
        #     else:
        #         logger.exception("[CHATGPT] Exception: {}".format(e))
        #         need_retry = False
        #         self.sessions.clear_session(session.session_id)
        #
        #     if need_retry:
        #         logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
        #         return self.reply_text(session, api_key, args, retry_count + 1)
        #     else:
        #         return result
        return result


class AzureChatGPTBot(ChatGPTBot):
    def __init__(self):
        super().__init__()
        openai.api_type = "azure"
        openai.api_version = conf().get("azure_api_version", "2023-06-01-preview")
        self.args["deployment_id"] = conf().get("azure_deployment_id")

    def create_img(self, query, retry_count=0, api_key=None):
        api_version = "2022-08-03-preview"
        url = "{}dalle/text-to-image?api-version={}".format(openai.api_base, api_version)
        api_key = api_key or openai.api_key
        headers = {"api-key": api_key, "Content-Type": "application/json"}
        try:
            body = {"caption": query, "resolution": conf().get("image_create_size", "256x256")}
            submission = requests.post(url, headers=headers, json=body)
            operation_location = submission.headers["Operation-Location"]
            retry_after = submission.headers["Retry-after"]
            status = ""
            image_url = ""
            while status != "Succeeded":
                logger.info("waiting for image create..., " + status + ",retry after " + retry_after + " seconds")
                time.sleep(int(retry_after))
                response = requests.get(operation_location, headers=headers)
                status = response.json()["status"]
            image_url = response.json()["result"]["contentUrl"]
            return True, image_url
        except Exception as e:
            logger.error("create image error: {}".format(e))
            return False, "图片生成失败"


if __name__ == '__main__':
    getfirsttext(list)