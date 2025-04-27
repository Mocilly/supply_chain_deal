import requests
import json

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

messages=[
    {"role": "system", "content": "你是一个著名的诗人"},
    {"role": "user", "content": "请说hello"}
]
response = requests.post(url, json=payload, headers=headers, stream=True)
# 检查请求是否成功
if response.status_code == 200:
    content_list = []
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
    content_list.append(final_result.replace('\n', ''))
else:
    print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")

# 返回是否结束的状态
is_finished
content_list