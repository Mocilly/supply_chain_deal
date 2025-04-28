import os
import requests
import json



def talk_initialize():
    # 这里可以添加初始化代码，例如设置API密钥等
    url = "https://api.siliconflow.cn/v1/chat/completions"
    model="deepseek-ai/DeepSeek-R1"


    payload = {
        "model": model,
        "messages": messages,
        "stream": True,  # 启用流式处理
        "max_tokens": 16384,#max_tokens必须小于等于16384
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
        # 注意：根据API文档，你可能需要移除或适当地填充tools字段
    }

    headers = {
        "Authorization": "Bearer sk-mqxdbrnlwcmdflpjmkoekrefarzcuyvwgszwhfltcjodzxyr",
        "Content-Type": "application/json"
    }
    return url, payload, headers




def execute_conversation(messages):
    url, payload, headers = talk_initialize()  # 初始化API参数
    content_list = []
    is_finished = False

    for message in messages:
        payload["messages"] = [message]
        response = requests.post(url, json=payload, headers=headers, stream=True)

        # 检查请求是否成功
        if response.status_code == 200:
            is_finished = False
            first_content_output = True
            final_result = ""

            for chunk in response.iter_lines():
                if chunk:  # 过滤掉keep-alive新行
                    chunk_str = chunk.decode('utf-8').strip()
                    try:
                        if chunk_str.startswith('data:'):
                            chunk_str = chunk_str[6:].strip()  # 去除"data:"前缀和之后的首位空格
                        if chunk_str == "[DONE]":  # 完成了
                            is_finished = True
                            break

                        # 解析JSON
                        chunk_json = json.loads(chunk_str)
                        if 'choices' in chunk_json and isinstance(chunk_json['choices'], list) and len(chunk_json['choices']) > 0:
                            choice = chunk_json['choices'][0]
                            delta = choice.get('delta', {})
                            # 获取结果信息
                            content = delta.get('content')

                            # 打印结果内容：content（如果有）
                            if content is not None:
                                final_result += content
                                if first_content_output:
                                    print("\n\n==============================\n结果:")
                                    first_content_output = False
                                print(content, end='', flush=True)

                    except json.JSONDecodeError as e:
                        print(f"JSON解码错误: {e}", flush=True)

            # 将最终结果存入content_list，去掉其中的换行符
            content_list.append(final_result.replace('\n', '').strip())

            # 如果对话完成，继续下一轮
            if not is_finished:
                print("\n对话未完成，无法继续下一轮。")
                break
        else:
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            break

    return content_list, is_finished


messages=[
    {"role": "user", "content": "请简短的说一下hello"}
]


# 返回是否结束的状态
content_list,is_finished = execute_conversation(messages)
content_list







def file_talk_initialize():
    
    # 配置参数
    api_key = "sk-mqxdbrnlwcmdflpjmkoekrefarzcuyvwgszwhfltcjodzxyr"  # 替换为你的API Key
    url = "https://api.siliconflow.cn/v1/files"  # 以文档实际地址为准

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    return url, headers


url,headers = file_talk_initialize()  # 初始化API参数
# 要上传的文件路径
file_path = r'.\调用文件\时间趋势分析\company.json'



# 读取文件内容
try:
    with open(file_path, "rb") as file:
        files = {
            "file": (file_path.split("/")[-1], file, "application/octet-stream")
        }

        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data={"purpose": "batch"},  # 关键修复点：添加purpose参数
            timeout=30  # 根据文件大小调整超时时间
        )

        # 处理响应
        if response.status_code == 200:
            print("文件上传成功！")
            print("响应数据：", response.json())
        else:
            print(f"上传失败，状态码：{response.status_code}")
            print("错误信息：", response.text)

except FileNotFoundError:
    print(f"文件不存在：{file_path}")
except Exception as e:
    print(f"发生异常：{str(e)}")

