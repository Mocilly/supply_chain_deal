import os
import requests
import json
import time



def talk_initialize(sk='sk-mqxdbrnlwcmdflpjmkoekrefarzcuyvwgszwhfltcjodzxyr',model='Qwen/Qwen3-14B'):
    # 这里可以添加初始化代码，例如设置API密钥等
    url = "https://api.siliconflow.cn/v1/chat/completions"


    payload = {
        "model": model,
        "messages": messages,
        "stream": True,  # 启用流式处理
        "max_tokens": 8192,#max_tokens必须小于等于16384
        "stop": ["null"],
        "temperature": 0.3,
        "top_p": 0.3,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
        # 注意：根据API文档，你可能需要移除或适当地填充tools字段
    }

    headers = {
        "Authorization": f"Bearer {sk}",
        "Content-Type": "application/json"
    }
    return url, payload, headers




def execute_conversation(url, payload, headers, message, max_retries=10, retry_delay=5):
    content_list = []
    is_finished = False
    payload["messages"] = [message]

    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=15)
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
                                chunk_str = chunk_str[6:].strip()
                            if chunk_str == "[DONE]":
                                is_finished = True
                                break

                            chunk_json = json.loads(chunk_str)
                            if 'choices' in chunk_json and isinstance(chunk_json['choices'], list) and len(chunk_json['choices']) > 0:
                                choice = chunk_json['choices'][0]
                                delta = choice.get('delta', {})
                                content = delta.get('content')
                                if content is not None:
                                    final_result += content
                                    if first_content_output:
                                        print("\n\n==============================\n结果:")
                                        first_content_output = False
                                    print(content, end='', flush=True)
                        except json.JSONDecodeError as e:
                            print(f"JSON解码错误: {e}", flush=True)

                content_list.append(final_result.replace('\n', '').strip())
                break  # 成功则跳出重试循环
            else:
                print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
                break  # 非超时错误不重试
        except requests.exceptions.Timeout:
            attempt += 1
            print(f"请求超时，正在重试({attempt}/{max_retries})...")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，放弃请求。")
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            break

    return content_list, is_finished


def process_lines_to_dict(file_path):
    result_dict = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            industry_id = data.get("INDUSTRY_ID", "")
            description = data.get("DESCRIPTION", "")
            if industry_id and description:
                result_dict[industry_id] = description
    return result_dict

# Example usage
file_path = r'.\调用文件\用于行业分类分析的可视化表\output.jsonl'
lines_dict = process_lines_to_dict(file_path)



# 示例测试代码  如下
messages=[

    {"role": "user", "content": 
    "我接下来将发一组供应链关系的起始公司名称和相关的关键词，\
     请通过联网查询相关信息来跟中国国民经济行业分类标准（2017）2019修订版相匹配来看所发的供应链信息属于哪一个行业，给出行业四位码，并给出判断依据，\
     参考信息网址同步显示出来,判断中可将source_company_keyword中的查询所得信息和keyword中的查询所得信息的权重调高,\n"
    
    },
    {"role": "user", "content":
      "参照中国国民经济行业分类标准的行业代码和行业描述来输出下列信息中可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依据中国国民经济行业分类），判断依据：xxxxxx，参考网址:xxxx（列出下方供应链信息联网搜索后得到的信息参考的网址，诸如查询该公司所得的业务信息）\n"
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：National Cement Company of California\
    ,keyword：oil and gas royalties,rock and aggregate royalties，royalties from a cement operation"},
    
    {"role": "user", "content":   "参照中国国民经济行业分类标准的行业代码和行业描述来输出下列信息中可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依据中国国民经济行业分类），判断依据：xxxxxx，参考网址:xxxx（列出下方供应链信息联网搜索后得到的信息参考的网址，诸如查询该公司所得的业务信息）\n"
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：Calpine generating\
    ,keyword：lease,electric power plant"},

    {"role": "user", "content":   "参照中国国民经济行业分类标准的行业代码和行业描述来输出下列信息中可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依据中国国民经济行业分类），判断依据：xxxxxx，参考网址:xxxx（列出下方供应链信息联网搜索后得到的信息参考的网址，诸如查询该公司所得的业务信息）\n"
    "source_compan_name:Tejon Ranch Co.,target_company_name:Calpine Corp.,source_company_keyword：Tejon,target_company_keyword：Pastoria Energy Facility, L.L.C\
    ,keyword：tenant"},
]

# content_list = []
# # 返回是否结束的状态
# content,is_finished = execute_conversation(messages[0])

# # 逐条执行对话，返回是否结束的状态
# content,is_finished = execute_conversation(messages[1])
# content_list.append(content)
# content,is_finished = execute_conversation(messages[2])
# content_list.append(content)
# content,is_finished = execute_conversation(messages[3])
# content_list.append(content[3])


# # 将content_list写入JSON文件
# output_path = r'.\调用文件\用于行业分类分析的可视化表\conversation_output.json'
# with open(output_path, 'w', encoding='utf-8') as json_file:
#     json.dump(content_list, json_file, ensure_ascii=False, indent=4)

# print(f"内容已成功写入到 {output_path}")








