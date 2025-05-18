from time import sleep
import sys
sys.path.append('.\industy_calculate')
from siliconflow_qa_record import talk_initialize, execute_conversation, process_lines_to_dict
print("调试信息:开始运行")  # 终端会显示此内容

import json
import os
import re

# 存储下国民经济行业分类的字典文件 用于后续比对
file_path = r'.\调用文件\用于行业分类分析的可视化表\output.jsonl'
lines_dict = process_lines_to_dict(file_path)

# 查看行业代码是否在字典键里面
def check_industry_code_in_dict(industry_code, dictionary):
    """
    检查给定的行业代码是否存在于字典的键中

    Args:
        industry_code (str): 要检查的行业代码
        dictionary (dict): 包含行业代码的字典

    Returns:
        bool: 如果行业代码存在于字典键中返回True，否则返回False
    """
    return industry_code in dictionary

# 示例调用
industry_code_to_check = "1234"  # 替换为实际的行业代码
is_present = check_industry_code_in_dict(industry_code_to_check, lines_dict)
print(f"行业代码 {industry_code_to_check} 是否存在于字典中: {is_present}")

message_need_to_add = [
    "我接下来将发一组供应链关系的起始公司名称和相关的关键词，\
     请通过联网查询相关信息来跟中国国民经济行业分类标准（2017）2019修订版相匹配来看所发的供应链信息属于哪一个行业，给出行业四位码，并给出判断依据，\
     参考信息网址同步显示出来,判断中可将source_company_keyword中的查询所得信息和keyword中的查询所得信息的权重调高(如果没有该字段则正常搜索),\n",

    "参照中国国民经济行业分类标准的行业代码和行业描述来输出下列信息中可能性最高的单个分类\n"
     "显示格式：行业分类代码：xxxx（依据中国国民经济行业分类），判断依据：xxxxxx，参考网址:xxxx（列出下方供应链信息联网搜索后得到的信息参考的网址，诸如查询该公司所得的业务信息）\n",

]


def extract_relevant_data(data):
    """从嵌套字典结构中提取关键字段，重组为以元组为键的新字典
    
    Args:
        data: 原始数据字典，键为复合字符串，值为关联数据
        
    Returns:
        以(来源名称,目标名称,来源公司关键词,目标公司关键词)为键的新字典
    """
    result = {}
    for key, value in data.items():
        # 过滤包含特定标记的无效键
        if "info_not_found" in key:
            continue

        # 解析复合键结构：用竖线分割的多个键值对
        parts = key.split('|')
        extracted = {}
        for part in parts:
            # 提取冒号分隔的键值对（split次数限制为1次，防止值含冒号）
            if ':' in part:
                k, v = part.split(':', 1)  # 仅分割第一个冒号
                extracted[k.strip()] = v.strip()  # 去除两端空格

        # 构建四元组复合键：SOURCE_name, TARGET_name, 公司关键词组合
        key_tuple = (extracted.get("SOURCE_name", ""),       
            extracted.get("TARGET_name", ""),       
            extracted.get("source_company_keyword", ""),  
            extracted.get("target_company_keyword", ""),  
            extracted.get("keyword", "")   
        )
        
        # 保留原始值，用于后续关联分析
        result[key_tuple] = value
        
    return result

with open(r'.\调用文件\用于行业分类分析的可视化表\用于行业分类分析的可视化表info_dict.json', 'r', encoding='utf-8') as f:
    file_content_dict = extract_relevant_data(json.load(f))

#查看前10条数据
for key, value in file_content_dict.items():
    if list(file_content_dict.keys()).index(key) < 10:
        print(key)
        print(value)
        print("===================================")
    else:
        break

print(f"总共的条目数量为{len(file_content_dict)}")
def construct_message_from_key(key):
    """
    根据给定的键构造消息字符串

    Args:
        key (tuple): 包含多个字段的元组

    Returns:
        str: 拼接后的消息字符串
    """
    fields = [
        ("source_compan_name", key[0]),
        ("target_company_name", key[1]),
        ("source_company_keyword", key[2]),
        ("target_company_keyword", key[3]),
        ("keyword", key[4]),
    ]

    # 过滤掉值为空的字段
    filtered_fields = [f"{name}:{value}" for name, value in fields if value]

    # 拼接消息
    return ", ".join(filtered_fields)



# # 使用正则表达式提取行业代码
# def extract_industry_code(content):
#     """
#     从内容中提取行业代码

#     Args:
#         content (str): 包含行业代码的字符串

#     Returns:
#         str: 提取出的行业代码，如果未找到则返回空字符串
#     """
#     match = re.search(r"行业分类代码：(\d{4})", content)
#     return match.group(1) if match else ""

# # 提取并存储行业代码
# content_list = []
# for content in file_content_dict[key][1]:
#     industry_code = extract_industry_code(content)
#     content_list.append(industry_code)

def execute_conversation_with_range(url, payload, headers,start_line, end_line):
    """
    执行对话内容，支持指定起止行数范围，并输出修改的字典行

    Args:
        start_line (int): 起始行数（从0开始）
        end_line (int): 结束行数（包含）

    Returns:
        dict: 包含修改后的键值对的字典
    """
    
    modified_entries = {}
    _, _ = execute_conversation(url, payload, headers,{
        "role": "user", "content": message_need_to_add[0]})
    for i, (key, value) in enumerate(file_content_dict.items()):
        if i < start_line or i > end_line:
            # 跳过不在范围内的行
            continue
        message = construct_message_from_key(key)
        message_send = message_need_to_add[1] + message
        content, _ = execute_conversation(url, payload, headers,
                                          {"role": "user", "content": message_send})
        index_list = value
        # 转换 key 为字符串并按照顺序排列
        key_str = f"SOURCE_name:{key[0]}|TARGET_name:{key[1]}|source_company_keyword:{key[2]}|target_company_keyword:{key[3]}|keywords:{key[4]}"
        modified_entries[key_str] = [index_list,[content]]  # 保存修改的行


    return modified_entries


# 示例调用
def execute_and_save(start_line, end_line):
    url, payload, headers = talk_initialize()
    modified_entries = execute_conversation_with_range(url, payload, headers,start_line, end_line)
#存储修改行的字典
    execute_order = f"{start_line}-{end_line}"
    sleep(2)
    output_file_path = fr'.\调用文件\用于行业分类分析的可视化表\中间文件\industry_identify_{execute_order}.json'
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(modified_entries, f, ensure_ascii=False, indent=4)
    sleep(1)
    print(f"修改的行已保存到 {output_file_path}")


####################    接下来是分布执行对话（多开VScode客户端来实现），每个对话50个就将对话结果存入文件中（避免tokens过长 ds记不住上下文） ####################


#region vscode客户端5执行的代码片段：
def process_lines_with_skip(skip_until):
    for r in range(40, 50):

        for i in range(10000*r, 10000*(r+1), 100):
            start_line = i
            end_line = i + 99
            # 调用函数并保存结果
            if i in range(400000, skip_until, 100):
                continue
            print(f"正在处理行 {start_line} 到 {end_line}...")
            execute_and_save(start_line, end_line)
#endregion
process_lines_with_skip(414500)
