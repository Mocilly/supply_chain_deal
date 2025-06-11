import json
from pathlib import Path
import re
import sys
import time
from tqdm import tqdm
# 定义输入输出路径
input_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data.json")
misssing_code_file_revise = Path(r'.\调用文件\用于行业分类分析的可视化表\data_need_to_revised.json')
output_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data_clean.json")


# 读取JSON文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"加载了 {len(data)} 个键值对")


def clean_data(data):
    """
    清理字典数据，删除所有星号（单星号和双星号）和空格
    """
    processed_items = 0

    for key, value in data.items():
        if isinstance(value, list) and len(value) >= 2:
            for i, data_list in enumerate(value[1]):
                for j, text in enumerate(data_list):
                    cleaned_text = text.replace('*', '').replace(' ', '')
                    value[1][i][j] = cleaned_text
        processed_items += 1

        if processed_items % 10 == 0:
            print(f"已处理 {processed_items} 个项目")

# 调用方法
clean_data(data)

# 查看前50项目
print("前50个项目:")
for i, (key, value) in enumerate(data.items()):
    if i >= 50:
        break
    print(f"键: {key}, 值: {value}")

def extract_industry_codes(data):
    """
    提取行业代码，返回 industry_codes, missing_codes, pattern1_matches, pattern2_matches
    支持在同一文本中提取多个行业代码
    """
    industry_codes = {}  # 改为存储{key_idx: [code1, code2, ...]}格式
    missing_codes = {}
    pattern1_matches = 0
    pattern2_matches = 0

    # 第一种匹配模式: 字母+数字格式 (如C1512)
    pattern1 = re.compile(r'(?:行业(?:分类)?代码：?\s*)?([A-Z]\d{4,5}|[A-Z]\d{3,4}|[A-Z]\d{2})')
    # 第二种匹配模式: 纯数字格式 (如48)
    pattern2 = re.compile(r'(?:行业(?:分类)?代码：?\s*)(\d{1,4})(?:\s*（[^）]*）)?')

    for key_idx, (key, value) in enumerate(data.items()):
        try:
            if isinstance(value, list) and len(value) >= 2:
                found_codes = []  # 存储当前项找到的所有代码
                
                # 遍历所有文本块寻找所有可能的行业代码
                for data_list in value[1]:
                    for text in data_list:
                        # 模式1匹配 - 查找所有匹配项，不再提前退出
                        matches1 = pattern1.findall(text)
                        if matches1:
                            for code in matches1:
                                if code not in found_codes:  # 避免重复
                                    found_codes.append(code)
                                    print(f"键 {key_idx}: 使用模式1找到行业代码 {code}")
                                    pattern1_matches += 1
                        
                        # 模式2匹配 - 同样查找所有匹配项
                        matches2 = pattern2.findall(text)
                        if matches2:
                            for code in matches2:
                                if code not in found_codes:  # 避免重复
                                    found_codes.append(code)
                                    print(f"键 {key_idx}: 使用模式2找到行业代码 {code}")
                                    pattern2_matches += 1
                
                # 根据找到的代码情况处理
                if found_codes:
                    industry_codes[key_idx] = found_codes
                    if len(found_codes) > 1:
                        print(f"键 {key_idx}: 找到多个行业代码: {', '.join(found_codes)}")
                else:
                    # 未找到任何代码
                    missing_codes[key_idx] = key
                    print(f"键 {key_idx}: 未找到行业代码")
                    
        except Exception as e:
            print(f"处理键 '{key}' 时出错: {e}")
            missing_codes[key_idx] = f"{key} (处理出错: {str(e)})"

    # 计算找到多个代码的项目数量
    multi_code_count = sum(1 for codes in industry_codes.values() if len(codes) > 1)
    
    print(f"完成处理，总共提取了 {len(industry_codes)} 个项目的行业代码")
    print(f"其中有 {multi_code_count} 个项目包含多个行业代码")
    print(f"模式1匹配了 {pattern1_matches} 个代码，模式2匹配了 {pattern2_matches} 个代码")
    print(f"有 {len(missing_codes)} 个项目未能提取到行业代码")
    
    return industry_codes, missing_codes, pattern1_matches, pattern2_matches

# 调用方法
industry_codes, missing_codes, pattern1_matches, pattern2_matches = extract_industry_codes(data)



# 将未匹配的行业代码信息保存到文件
with open(misssing_code_file_revise, 'w', encoding='utf-8') as f:
    json.dump(missing_codes, f, ensure_ascii=False, indent=2)

print(f"已将未匹配的行业代码信息写入到 {misssing_code_file_revise.absolute()}")


# 从revise_data_qa_llm_request.py生成的结果来进行读取并进行下列对原data的修正











#打印前50个未找到行业代码的项目
print("前50个未找到行业代码的项目:")
for i, (key, value) in enumerate(missing_codes.items()):
    if i >= 50:
        break
    print(f"键: {key}, 值: {value}")

print(f"未找到行业代码的项目数量: {len(missing_codes)}")
#查看data第962020行的内容
check_id = 0
# 遍历字典中的每个键值对
for key, value in data.items():
    if check_id == 952336:
        print(f"第 {check_id} 行的内容: 键: {key}, 值: {value}")
    check_id += 1


# 将清理后的数据写入新文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已将清理后的JSON数据写入到 {output_file.absolute()}")


if __name__ == "__main__":
    clean_json_file()