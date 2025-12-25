from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from astrbot.core.message.components import Plain, Reply

import dashscope
from dashscope import Generation

global max_text_line

dashscope_api = "please fill your api_key"


@register("forwardMessageAnalysis", "orchidsziyou", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        global max_text_line
        max_text_line = 200

    @filter.command("fenxi")
    async def fenxi(self, event: AstrMessageEvent):
        global max_text_line
        linecount = 0
        try:
            message_chain = event.get_messages()
            reply_id = -1
            is_pure_text = False  # 是否为纯文本
            for msg in message_chain:
                if msg.type == 'Reply':
                    # 处理回复消息
                    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                    assert isinstance(event, AiocqhttpMessageEvent)
                    client = event.bot
                    payload = {
                        "message_id": msg.id
                    }
                    response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
                    reply_msg = response['message'][0]
                    # print(response)
                    # print(reply_msg)

                    reply_id = msg.id

                    if reply_msg['type'] == "text":
                        is_pure_text = True

            raw_text_line = ""  # 记录提取出来的文字的line

            if is_pure_text == True:
                # print(reply_msg)
                raw_text_line = reply_msg['data']['text']
                # print(raw_text_line)

            else:

                if reply_id == -1:
                    yield event.plain_result("未找到回复聊天记录，请重试")
                    return

                """分析获取到的信息的情况"""
                data = event.get_messages()
                # print(data)
                # forward_msg_id = data[0].chain[0].id
                # print(forward_msg_id)
                forward_msg_id = reply_id

                # 获取合并消息的详细信息

                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                    AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads2 = {
                    "message_id": forward_msg_id
                }
                response = await client.api.call_action('get_forward_msg', **payloads2)  # 调用 协议端  API
                # print(response)

                messagelist = response["messages"]
                # print(messagelist)

                for message in messagelist:
                    # print(message)
                    curmessage = message
                    if curmessage["message"][0]["type"] == "text":
                        linecount += 1
                        if linecount >= max_text_line:
                            break
                        else:
                            # print(curmessage["message"][0]["data"]["text"])
                            raw_text_line = raw_text_line + curmessage["message"][0]["data"]["text"] + "\n"
                    if curmessage["message"][0]["type"] == "forward":
                        innerMessageList = curmessage["message"][0]["data"]["content"]
                        # print(innerMessageList)
                        for innermessage in innerMessageList:
                            if innermessage["message"][0]["type"] == "text":
                                linecount += 1
                                if linecount >= max_text_line:
                                    break
                                else:
                                    raw_text_line = raw_text_line + innermessage["message"][0]["data"]["text"] + "\n"

            print(raw_text_line)

            dashscope.api_key = dashscope_api

            response = Generation.call(
                model="qwen-max",  # 或者使用 qwen-turbo, qwen-plus 等
                messages=[
                    {"role": "system", "content": "你是一个专业的文本分析助手"},
                    {"role": "user",
                     "content": f"请详细分析以下文本内容,分析有无关于性转，开挂，骂人，暴力，政治,抑郁，恶心人，原神，引战等可以被称作“屎”的内容，如果有，就分析返回来“是”，否则就返回来“不是”，只需要回答是或者不是,不要回答其他的东西。如果发送的内容为空，就返回“提供的内容为空”：{raw_text_line}"}
                ]
            )

            # 输出分析结果
            if response.status_code == 200:
                result = response.output.text
                print(result)
                if result == "是":
                    message_chain = [
                        Reply(id=reply_id),
                        Plain("这就是屎")
                    ]

                elif result == "提供的内容为空":
                    message_chain = [
                        Reply(id=reply_id),
                        Plain("没有成功提取到内容，搜索失败")
                    ]
                else:
                    message_chain = [
                        Reply(id=reply_id),
                        Plain("我不觉得这是屎")
                    ]
                yield event.chain_result(message_chain)
        except Exception as e:
            print(e)
            yield event.plain_result("搜索失败")
            return
