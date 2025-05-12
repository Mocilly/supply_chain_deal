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




def execute_conversation(message):
    url, payload, headers = talk_initialize()  # 初始化API参数
    content_list = []
    is_finished = False


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

    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")

    return content_list, is_finished


with open(r'.\调用文件\用于行业分类分析的可视化表\output.jsonl', 'r', encoding='utf-8') as f:
    lines = ""
    for line in f:
        data = json.loads(line.strip())
        industry_id = data.get("INDUSTRY_ID", "")
        description = data.get("DESCRIPTION", "")
        lines += f"{industry_id}：{description}；\n"

messages=[
    {"role": "user", "content": "请参照国民经济行业分类（GBT+4754_2017）2019修订进行判断，记住其中的行业代码(四位数)和行业描述用于判断我后续发给你的信息，\
     接下来是命令：\n"
     "我将发一组供应链关系的起始公司名称和相关的关键词，\
     请通过联网查询相关信息来跟上述行业描述的内容相匹配来看所发信息属于哪一个行业，给出四位码，并给出判断依据，\
     参考网址同步显示出来,判断中可将source_company_keyword权重调高,\n"
     "等待我的下一个指令"
     "\n"
     },
    
    {"role": "user", "content":"参照国民经济行业分类表输出可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依照行业分类表数字），判断依据：xxxxxx，参考网址:列出参考信息的来源网址   \n "
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：National Cement Company of California\
    ,keyword：oil and gas royalties,rock and aggregate royalties，royalties from a cement operation"},
    {"role": "user", "content":"参照国民经济行业分类表输出可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依照行业分类表数字），判断依据：xxxxxx，参考网址:列出参考信息的来源网址   \n "
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：Calpine generating\
    ,keyword：lease,electric power plant"},
    {"role": "user", "content":"参照国民经济行业分类表输出可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依照行业分类表数字），判断依据：xxxxxx，参考网址:列出参考信息的来源网址   \n "
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：Pastoria Energy Facility, L.L.C\
    ,keyword：tenant"},
]

content_list = []
# 返回是否结束的状态
content,is_finished = execute_conversation(messages[0])

# 逐条执行对话，返回是否结束的状态
content,is_finished = execute_conversation(messages[1])
content_list.append(content)
content,is_finished = execute_conversation(messages[2])
content_list.append(content)
content,is_finished = execute_conversation(messages[3])
content_list.append(content[3])

# 将content_list写入JSON文件
output_path = r'.\调用文件\用于行业分类分析的可视化表\conversation_output.json'
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(content_list, json_file, ensure_ascii=False, indent=4)

print(f"内容已成功写入到 {output_path}")








