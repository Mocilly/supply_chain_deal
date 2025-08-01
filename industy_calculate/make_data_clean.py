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
    修正版本：使用原始键保持与data的一致性
    """
    industry_codes = {}  # 改为存储{original_key: [code1, code2, ...]}格式
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
                                    print(f"键 {key_idx} (原始键): 使用模式1找到行业代码 {code}")
                                    pattern1_matches += 1
                        
                        # 模式2匹配 - 同样查找所有匹配项
                        matches2 = pattern2.findall(text)
                        if matches2:
                            for code in matches2:
                                if code not in found_codes:  # 避免重复
                                    found_codes.append(code)
                                    print(f"键 {key_idx} (原始键): 使用模式2找到行业代码 {code}")
                                    pattern2_matches += 1
                
                # 根据找到的代码情况处理 - 使用原始键而不是key_idx
                if found_codes:
                    industry_codes[key] = found_codes  # 使用原始key
                    if len(found_codes) > 1:
                        print(f"原始键 '{key}': 找到多个行业代码: {', '.join(found_codes)}")
                else:
                    # 未找到任何代码 - 使用原始键
                    missing_codes[key] = key  # 使用原始key
                    print(f"原始键 '{key}': 未找到行业代码")
                    
        except Exception as e:
            print(f"处理键 '{key}' 时出错: {e}")
            missing_codes[key] = f"{key} (处理出错: {str(e)})"  # 使用原始key

    # 计算找到多个代码的项目数量
    multi_code_count = sum(1 for codes in industry_codes.values() if len(codes) > 1)
    
    print(f"完成处理，总共提取了 {len(industry_codes)} 个项目的行业代码")
    print(f"其中有 {multi_code_count} 个项目包含多个行业代码")
    print(f"模式1匹配了 {pattern1_matches} 个代码，模式2匹配了 {pattern2_matches} 个代码")
    print(f"有 {len(missing_codes)} 个项目未能提取到行业代码")
    
    # 验证键的一致性
    all_processed_keys = set(industry_codes.keys()) | set(missing_codes.keys())
    original_keys = set(data.keys())
    if all_processed_keys == original_keys:
        print("✓ 键一致性验证通过：所有data键都已正确处理")
    else:
        print("✗ 键一致性验证失败")
        missing_keys = original_keys - all_processed_keys
        extra_keys = all_processed_keys - original_keys
        if missing_keys:
            print(f"  缺失的键数量: {len(missing_keys)}")
        if extra_keys:
            print(f"  多余的键数量: {len(extra_keys)}")
    
    return industry_codes, missing_codes, pattern1_matches, pattern2_matches

# 重新运行修正后的函数
print("=== 使用修正后的extract_industry_codes函数 ===")
industry_codes, missing_codes, pattern1_matches, pattern2_matches = extract_industry_codes(data)

# 验证键的一致性
print(f"\n=== 键一致性最终验证 ===")
print(f"data键数量: {len(data)}")
print(f"industry_codes键数量: {len(industry_codes)}")
print(f"missing_codes键数量: {len(missing_codes)}")
print(f"总计: {len(industry_codes) + len(missing_codes)}")

# 检查几个示例键
sample_keys = list(data.keys())[:3]
for key in sample_keys:
    print(f"\n键一致性检查 - '{key[:50]}...':")
    print(f"  在data中: {key in data}")
    print(f"  在industry_codes中: {key in industry_codes}")
    print(f"  在missing_codes中: {key in missing_codes}")
    if key in industry_codes:
        print(f"  提取到的代码: {industry_codes[key]}")
# 调用方法
industry_codes, missing_codes, pattern1_matches, pattern2_matches = extract_industry_codes(data)



# 将未匹配的行业代码信息保存到文件
with open(misssing_code_file_revise, 'w', encoding='utf-8') as f:
    json.dump(missing_codes, f, ensure_ascii=False, indent=2)

print(f"已将未匹配的行业代码信息写入到 {misssing_code_file_revise.absolute()}")


# 从revise_data_qa_llm_request.py生成的结果second_round_lllm_revised.json
# 来进行读取并进行下列对原data的修正
with open(Path(r".\调用文件\用于行业分类分析的可视化表\second_round_llm_revised.json"), 'r', encoding='utf-8') as f:
    revised_data = json.load(f)

# 对原始数据进行修正
count = 0
for key, value in revised_data.items():
    if key in data:
        data[key][1] = value[1][0]  #此处是由于second_round_llm_revised.json多嵌套了个列表，合并数据的脚本就懒得再修改了
        count += 1
print(f"已将 {count} 个项目的行业代码从修正数据中更新到原始数据中")


# 第二次调用方法，读取已经修改过的data
industry_codes, missing_codes, pattern1_matches, pattern2_matches = extract_industry_codes(data)


    
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


def load_json_to_dict(file_path):
    """
    读取包含行业代码的 JSON 文件，并将其解析为一个字典。
    该函数期望 JSON 文件是一个包含对象的列表，且每个对象都应有 'INDUSTRY_ID' 和 'DESCRIPTION' 键。
    例如: [{"INDUSTRY_ID": "01", "DESCRIPTION": "农业", ...}, ...]
    它会将这些对象转换成一个以行业代码为键，行业描述为值的字典。

    参数:
    file_path (str): JSON 文件的路径。

    返回:
    dict: 一个以行业代码为键，行业描述为值的字典。
          如果文件不存在或处理过程中发生错误，则可能返回一个空字典。
    """
    industry_data_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if isinstance(data, list):
                for item_number, item in enumerate(data, 1):
                    # 使用正确的键名: INDUSTRY_ID 和 DESCRIPTION
                    if isinstance(item, dict) and 'INDUSTRY_ID' in item and 'DESCRIPTION' in item:
                        code = item.get('INDUSTRY_ID')
                        description = item.get('DESCRIPTION')
                        if code:
                            industry_data_dict[code] = description
                        else:
                            print(f"警告: 文件 '{file_path}' 的第 {item_number} 个项目代码为空，已跳过: {item}")
                    else:
                        print(f"警告: 文件 '{file_path}' 的第 {item_number} 个项目缺少必需的键，已跳过: {item}")
            elif isinstance(data, dict):
                 # 如果文件本身就是一个 INDUSTRY_ID:DESCRIPTION 格式的字典
                 industry_data_dict = data
            else:
                print(f"警告: 文件 '{file_path}' 的内容不是预期的列表或字典格式。")

        print(f"成功从 '{file_path}' 加载了 {len(industry_data_dict)} 条行业代码数据。")

    except FileNotFoundError:
        print(f"错误: 文件 '{file_path}' 未找到。")
    except json.JSONDecodeError as e:
        print(f"警告: 解析文件 '{file_path}' 时出错: {e}.")
    except Exception as e:
        print(f"读取文件 '{file_path}' 时发生错误: {e}")
        
    return industry_data_dict

# 文件路径
file_path = r".\调用文件\用于行业分类分析的可视化表\industry_code.json"

# 读取并存储为字典
industry_data_dict = load_json_to_dict(file_path)

# 打印结果字典中的条目数量，以及前5个条目（如果存在）以供验证
print(f"\n合并后的字典中共有 {len(industry_data_dict)} 个条目。")
if industry_data_dict:
    print("字典中的前50个条目（或全部，如果少于50个）:")
    count = 0
    for key, value in industry_data_dict.items():
        if count < 50:
            print(f"  '{key}': {value}")
            count += 1
        else:
            break
else:
    print("合并后的字典为空。")



def process_industry_codes_with_alphabet_removal(industry_codes):
    """
    处理行业代码字典，将值从代码列表转换为包含原始代码和去除字母后代码的格式
    
    参数:
    industry_codes (dict): 原始行业代码字典，格式为 {key_idx: [code1, code2, ...]}
    
    返回:
    dict: 处理后的行业代码字典，格式为 {key_idx: [[original_code, cleaned_code], ...]}
          每个代码变成一个列表，索引0是原始代码，索引1是去除字母后的代码
          如果原始代码不含字母，则索引0和1都是原值
    """
    import re
    
    processed_industry_codes = {}
    
    for key_idx, codes_list in industry_codes.items():
        processed_codes = []
        
        for code in codes_list:
            original_code = str(code)
            # 去除代码中的字母，只保留数字
            cleaned_code = re.sub(r'[A-Za-z]', '', original_code)
            
            # 如果原始代码不含字母，或者清理后为空，则索引0和1都是原值
            if cleaned_code == original_code or not cleaned_code:
                processed_codes.append([original_code, original_code])
            else:
                # 如果含有字母且清理后不为空，索引0是原值，索引1是清理后的值
                processed_codes.append([original_code, cleaned_code])
        
        processed_industry_codes[key_idx] = processed_codes
    
    print(f"处理了 {len(industry_codes)} 个项目的行业代码")
    
    # 统计含有字母的代码数量
    total_codes = 0
    codes_with_letters = 0
    
    for codes_list in industry_codes.values():
        for code in codes_list:
            total_codes += 1
            if re.search(r'[A-Za-z]', str(code)):
                codes_with_letters += 1
    
    print(f"总代码数: {total_codes}")
    print(f"含有字母的代码数: {codes_with_letters}")
    print(f"不含字母的代码数: {total_codes - codes_with_letters}")
    
    return processed_industry_codes

# 在提取行业代码后调用此方法
processed_industry_codes = process_industry_codes_with_alphabet_removal(industry_codes)

# 打印前10个项目的处理结果
print("\n前10个项目的代码处理结果:")
count = 0
for key_idx, processed_codes in processed_industry_codes.items():
    if count >= 10:
        break
    
    print(f"项目 {key_idx}:")
    for i, (original, cleaned) in enumerate(processed_codes):
        if original == cleaned:
            print(f"  代码 {i+1}: '{original}' (无字母)")
        else:
            print(f"  代码 {i+1}: '{original}' -> '{cleaned}' (去除字母)")
    print()
    
    count += 1

# 显示一些统计信息
print("处理结果统计:")
items_with_letter_codes = 0
items_without_letter_codes = 0

for key_idx, processed_codes in processed_industry_codes.items():
    has_letter_codes = False
    for original, cleaned in processed_codes:
        if original != cleaned:
            has_letter_codes = True
            break
    
    if has_letter_codes:
        items_with_letter_codes += 1
    else:
        items_without_letter_codes += 1

print(f"包含字母代码的项目数: {items_with_letter_codes}")
print(f"不包含字母代码的项目数: {items_without_letter_codes}")

# 读取前50个包含多个代码的项目
count = 0
for key_idx, processed_codes in processed_industry_codes.items():
    
    print(f"{key_idx} : {processed_codes}")
    count += 1
    if count >= 50:
        break


def match_industry_codes_with_dict(processed_industry_codes, industry_data_dict):
    """
    将处理过的行业代码与行业字典进行匹配，返回包含三个值的列表
    
    参数:
    processed_industry_codes (dict): 格式为 {key_idx: [[original_code, cleaned_code], ...]}
    industry_data_dict (dict): 行业代码字典，格式为 {code: description}
    
    返回:
    tuple: (matched_codes, codes_not_found)
        - matched_codes (dict): 格式为 {key_idx: [[original_code, cleaned_code, matched_code], ...]}
        - codes_not_found (dict): 格式为 {key_idx: [[original_code, cleaned_code], ...]} - 无法匹配的代码
    """
    matched_codes = {}
    codes_not_found = {}
    
    total_codes = 0
    matched_count = 0
    not_found_count = 0
    
    for key_idx, code_pairs in processed_industry_codes.items():
        matched_codes[key_idx] = []
        temp_not_found = []
        
        for original_code, cleaned_code in code_pairs:
            total_codes += 1
            found_match = False
            final_matched_code = None
            
            # 处理清理后的代码
            code_to_search = str(cleaned_code)
            
            # 1. 如果是1位数，前面补0
            if len(code_to_search) == 1:
                code_to_search = '0' + code_to_search
            
            # 开始匹配逻辑
            if len(code_to_search) == 2:
                # 2位代码直接查找
                if code_to_search in industry_data_dict:
                    final_matched_code = code_to_search
                    found_match = True
                    
            elif len(code_to_search) == 3:
                # 3位代码：先查3位，再查前2位
                if code_to_search in industry_data_dict:
                    final_matched_code = code_to_search
                    found_match = True
                else:
                    # 截取前2位
                    code_2digit = code_to_search[:2]
                    if code_2digit in industry_data_dict:
                        final_matched_code = code_2digit
                        found_match = True
                        
            elif len(code_to_search) == 4:
                # 4位代码：先查4位，再查前3位，最后查前2位
                if code_to_search in industry_data_dict:
                    final_matched_code = code_to_search
                    found_match = True
                else:
                    # 截取前3位
                    code_3digit = code_to_search[:3]
                    if code_3digit in industry_data_dict:
                        final_matched_code = code_3digit
                        found_match = True
                    else:
                        # 截取前2位
                        code_2digit = code_to_search[:2]
                        if code_2digit in industry_data_dict:
                            final_matched_code = code_2digit
                            found_match = True
                            
            elif len(code_to_search) > 4:
                # 超过4位的代码：依次尝试4位、3位、2位
                code_4digit = code_to_search[:4]
                if code_4digit in industry_data_dict:
                    final_matched_code = code_4digit
                    found_match = True
                else:
                    code_3digit = code_to_search[:3]
                    if code_3digit in industry_data_dict:
                        final_matched_code = code_3digit
                        found_match = True
                    else:
                        code_2digit = code_to_search[:2]
                        if code_2digit in industry_data_dict:
                            final_matched_code = code_2digit
                            found_match = True
            
            # 记录结果
            if found_match:
                matched_codes[key_idx].append([original_code, cleaned_code, final_matched_code])
                matched_count += 1
            else:
                temp_not_found.append([original_code, cleaned_code])
                not_found_count += 1
        
        # 如果有无法匹配的代码，记录到codes_not_found中
        if temp_not_found:
            codes_not_found[key_idx] = temp_not_found
    
    print(f"代码匹配统计:")
    print(f"总代码数: {total_codes}")
    print(f"成功匹配: {matched_count}")
    print(f"无法匹配: {not_found_count}")
    print(f"匹配成功率: {matched_count/total_codes*100:.2f}%")
    
    return matched_codes, codes_not_found

# 调用函数进行匹配
matched_codes, codes_not_found = match_industry_codes_with_dict(processed_industry_codes, industry_data_dict)

# 打印前10个匹配结果
print("\n前10个项目的匹配结果:")
count = 0
for key_idx, matched_list in matched_codes.items():
    if count >= 10:
        break
    
    print(f"项目 {key_idx}:")
    for original, cleaned, matched in matched_list:
        print(f"  原始: '{original}' -> 清理: '{cleaned}' -> 匹配: '{matched}' ({industry_data_dict.get(matched, '未找到描述')})")
    
    # 如果该项目有无法匹配的代码，也显示出来
    if key_idx in codes_not_found:
        print("  无法匹配的代码:")
        for original, cleaned in codes_not_found[key_idx]:
            print(f"    原始: '{original}' -> 清理: '{cleaned}' (无匹配)")
    print()
    
    count += 1

# 显示无法匹配的代码统计
if codes_not_found:
    print(f"\n有 {len(codes_not_found)} 个项目包含无法匹配的代码")
    total_unmatched = sum(len(codes) for codes in codes_not_found.values())
    print(f"总共有 {total_unmatched} 个代码无法匹配")
    
    # 显示前5个无法匹配的示例
    print("\n前5个无法匹配代码的示例:")
    count = 0
    for key_idx, unmatched_list in codes_not_found.items():
        if count >= 5:
            break
        print(f"项目 {key_idx}: {unmatched_list}")
        count += 1
else:
    print("\n所有代码都成功匹配!")


# 显示前50个matched_codes
print("\n前50个项目的matched_codes:")
count = 0
for key_idx, matched_list in matched_codes.items():
    if count >= 953600:
        print(f"项目 {key_idx}: {matched_list}")
    count += 1


def check_key_consistency(data, industry_codes, processed_industry_codes, matched_codes):
    """
    检查各个阶段键的含义是否保持一致
    """
    print("=== 键含义一致性检查 ===")
    
    # 检查data的键
    print(f"原始data的键类型和数量:")
    print(f"  data键的数量: {len(data)}")
    print(f"  data的前5个键: {list(data.keys())[:5]}")
    print(f"  data键的类型: {type(list(data.keys())[0]) if data else 'N/A'}")
    
    # 检查industry_codes的键
    print(f"\nindustry_codes的键类型和数量:")
    print(f"  industry_codes键的数量: {len(industry_codes)}")
    print(f"  industry_codes的前5个键: {list(industry_codes.keys())[:5]}")
    print(f"  industry_codes键的类型: {type(list(industry_codes.keys())[0]) if industry_codes else 'N/A'}")
    
    # 检查processed_industry_codes的键
    print(f"\nprocessed_industry_codes的键类型和数量:")
    print(f"  processed_industry_codes键的数量: {len(processed_industry_codes)}")
    print(f"  processed_industry_codes的前5个键: {list(processed_industry_codes.keys())[:5]}")
    print(f"  processed_industry_codes键的类型: {type(list(processed_industry_codes.keys())[0]) if processed_industry_codes else 'N/A'}")
    
    # 检查matched_codes的键
    print(f"\nmatched_codes的键类型和数量:")
    print(f"  matched_codes键的数量: {len(matched_codes)}")
    print(f"  matched_codes的前5个键: {list(matched_codes.keys())[:5]}")
    print(f"  matched_codes键的类型: {type(list(matched_codes.keys())[0]) if matched_codes else 'N/A'}")
    
    # 检查键的一致性
    print(f"\n=== 键一致性验证 ===")
    
    # 检查industry_codes的键是否都存在于data中
    industry_keys_in_data = set(industry_codes.keys()) & set(data.keys())
    print(f"industry_codes中有 {len(industry_keys_in_data)} 个键存在于原始data中")
    print(f"industry_codes总键数: {len(industry_codes)}")
    
    # 检查processed_industry_codes的键是否与industry_codes一致
    processed_keys_match = set(processed_industry_codes.keys()) == set(industry_codes.keys())
    print(f"processed_industry_codes的键与industry_codes一致: {processed_keys_match}")
    
    # 检查matched_codes的键是否与processed_industry_codes一致
    matched_keys_match = set(matched_codes.keys()) <= set(processed_industry_codes.keys())
    print(f"matched_codes的键是processed_industry_codes的子集: {matched_keys_match}")
    
    # 显示键的对应关系示例
    print(f"\n=== 键对应关系示例 ===")
    sample_keys = list(data.keys())[:3]
    for key in sample_keys:
        print(f"键 '{key}':")
        print(f"  在data中存在: {key in data}")
        print(f"  在industry_codes中存在: {key in industry_codes}")
        print(f"  在processed_industry_codes中存在: {key in processed_industry_codes}")
        print(f"  在matched_codes中存在: {key in matched_codes}")
        
        if key in data:
            data_sample = str(data[key])[:100] + "..." if len(str(data[key])) > 100 else str(data[key])
            print(f"  data[{key}]: {data_sample}")
        
        if key in industry_codes:
            print(f"  industry_codes[{key}]: {industry_codes[key]}")
        
        if key in processed_industry_codes:
            print(f"  processed_industry_codes[{key}]: {processed_industry_codes[key]}")
            
        if key in matched_codes:
            print(f"  matched_codes[{key}]: {matched_codes[key]}")
        print()

# 执行一致性检查
check_key_consistency(data, industry_codes, processed_industry_codes, matched_codes)



# 执行一致性检查
check_key_consistency(data, industry_codes, processed_industry_codes, matched_codes)

def process_matched_codes_gb2017_fix(matched_codes):
    """
    处理matched_codes中的GB2017代号问题和去重
    
    处理逻辑：
    1. 如果一个项目有多个代码且包含'47'和其他代码，则去除'47'保留其他代码
    2. 如果代码中只有'47'则维持原样
    3. 在有多个代码的情况下，去除所有'8610'代码但保留其他代码（由于政治因素导致的新闻业大规模公司变动不计入此次供应链考量）
    4. 如果项目只包含'8610'代码，则保留该项目
    5. 对处理后的结果进行去重，基于第三个值（matched_code）
    
    参数:
    matched_codes (dict): 格式为 {key: [[original_code, cleaned_code, matched_code], ...]}
    
    返回:
    dict: 处理后的matched_codes
    """
    processed_matched_codes = {}
    
    # 统计变量
    items_processed = 0
    items_with_47_removed = 0
    items_with_8610_removed = 0
    items_only_8610_kept = 0
    items_deduplicated = 0
    
    for key, matched_list in matched_codes.items():
        items_processed += 1
        
        # 第一步：处理8610代码 - 由于政治因素导致的新闻业大规模公司变动不计入此次供应链考量
        # 检查是否只包含8610代码
        only_8610 = all(matched_code == '8610' for _, _, matched_code in matched_list)
        
        if only_8610:
            # 如果项目只包含8610代码，保留该项目
            items_only_8610_kept += 1
            print(f"8610保留: 键 '{key[:50]}...' 只包含8610代码，予以保留")
            filtered_8610_list = matched_list.copy()  # 保留原始数据
        else:
            # 在有多个代码的情况下，去除所有8610代码但保留其他代码
            filtered_8610_list = []
            had_8610 = False
            for original_code, cleaned_code, matched_code in matched_list:
                if matched_code == '8610':
                    had_8610 = True
                    # 跳过8610代码，不添加到filtered_8610_list中
                else:
                    filtered_8610_list.append([original_code, cleaned_code, matched_code])
            
            if had_8610 and len(filtered_8610_list) > 0:
                items_with_8610_removed += 1
                print(f"8610处理: 键 '{key[:50]}...' 去除了代码'8610'，保留其他代码")
        
        # 第二步：处理GB2017代号问题 - 去除'47'（如果有其他代码的话）
        filtered_list = []
        has_47 = False
        has_others = False
        
        # 检查是否包含'47'和其他代码
        for original_code, cleaned_code, matched_code in filtered_8610_list:
            if matched_code == '47':
                has_47 = True
            else:
                has_others = True
        
        # 应用过滤逻辑
        if has_47 and has_others and len(filtered_8610_list) >= 2:
            # 有多个代码且包含'47'和其他代码，去除'47'保留其他代码
            for original_code, cleaned_code, matched_code in filtered_8610_list:
                if matched_code != '47':  # 去除'47'保留其他代码
                    filtered_list.append([original_code, cleaned_code, matched_code])
            items_with_47_removed += 1
            print(f"GB2017处理: 键 '{key[:50]}...' 去除了代码'47'，保留其他代码")
        else:
            # 其他情况：只有'47'或没有'47'或只有一个代码，维持原样
            filtered_list = filtered_8610_list.copy()
        
        # 第三步：去重处理 - 基于第三个值（matched_code）
        seen_matched_codes = set()
        deduplicated_list = []
        original_count = len(filtered_list)
        
        for original_code, cleaned_code, matched_code in filtered_list:
            if matched_code not in seen_matched_codes:
                seen_matched_codes.add(matched_code)
                deduplicated_list.append([original_code, cleaned_code, matched_code])
        
        # 如果去重后数量减少，记录统计信息
        if len(deduplicated_list) < original_count:
            items_deduplicated += 1
            print(f"去重处理: 键 '{key[:50]}...' 从{original_count}个代码去重到{len(deduplicated_list)}个")
        
        # 最终列表添加到结果中（即使为空也添加，保持键的完整性）
        processed_matched_codes[key] = deduplicated_list
    
    # 输出处理统计
    print(f"\n=== matched_codes处理统计 ===")
    print(f"总处理项目数: {items_processed}")
    print(f"保留的纯8610项目数: {items_only_8610_kept}")
    print(f"应用8610代码去除的项目数: {items_with_8610_removed}")
    print(f"应用GB2017修正（去除'47'）的项目数: {items_with_47_removed}")
    print(f"应用去重处理的项目数: {items_deduplicated}")
    
    # 验证处理前后的总体统计
    original_total_codes = sum(len(codes) for codes in matched_codes.values())
    processed_total_codes = sum(len(codes) for codes in processed_matched_codes.values())
    original_total_items = len(matched_codes)
    processed_total_items = len(processed_matched_codes)
    
    print(f"处理前总项目数: {original_total_items}")
    print(f"处理后总项目数: {processed_total_items}")
    print(f"保持的项目数: {processed_total_items}")  # 现在应该是相等的
    print(f"处理前总代码数: {original_total_codes}")
    print(f"处理后总代码数: {processed_total_codes}")
    print(f"减少的代码数: {original_total_codes - processed_total_codes}")
    
    # 显示一些处理示例
    print(f"\n=== 处理示例 ===")
    example_count = 0
    for key in matched_codes.keys():
        if key in processed_matched_codes:
            original = matched_codes[key]
            processed = processed_matched_codes[key]
            
            # 只显示有变化的示例
            if original != processed:
                print(f"键: {key[:50]}...")
                print(f"  处理前: {original}")
                print(f"  处理后: {processed}")
                print()
                
                example_count += 1
                if example_count >= 5:  # 只显示前5个变化的示例
                    break
    
    if example_count == 0:
        print("没有发现需要处理的项目")
    
    return processed_matched_codes

# 调用新的处理方法
print("\n=== 开始处理matched_codes中的GB2017代号问题和去除 ===")
processed_matched_codes = process_matched_codes_gb2017_fix(matched_codes)

c = 0
for key, matched_list in processed_matched_codes.items():
    print(f"键: {key[:50]}...")
    print(f"  处理后: {matched_list}")
    c += 1
    if c >= 50:
        break

# 更新matched_codes变量，使用处理后的版本
matched_codes = processed_matched_codes


'''
根据所得到的matched_codes将其添加到原始数据data中，应该采用matched_codes中的每个子列表的第三个值予以添加。
'''

def add_matched_codes_to_data(data, matched_codes):
    """
    将matched_codes中的行业代码添加到原始数据data中
    按照代码位数从多到少的顺序排列
    
    参数:
    data (dict): 原始数据字典
    matched_codes (dict): 匹配的行业代码字典，格式为 {key: [[original_code, cleaned_code, matched_code], ...]}
    
    返回:
    int: 成功添加行业代码的项目数量
    """
    added_count = 0
    
    for key, matched_list in matched_codes.items():
        if key in data:
            # 提取所有匹配到的行业代码（第三个值）
            industry_codes = []
            for original_code, cleaned_code, matched_code in matched_list:
                industry_codes.append(matched_code)
            
            # 按照代码位数从多到少排序
            # 先按位数降序，位数相同时按字母数字顺序升序
            industry_codes.sort(key=lambda x: (-len(str(x)), str(x)))
            
            # 在data[key][1]中添加新的子列表
            if isinstance(data[key], list) and len(data[key]) >= 2:
                if isinstance(data[key][1], list):
                    # 检查是否已经添加过行业代码（避免重复添加）
                    # 通过检查最后一个子列表是否与要添加的代码相同
                    last_item = data[key][1][-1] if data[key][1] else None
                    
                    if last_item != industry_codes:
                        # 只有当最后一个子列表不等于要添加的代码时才添加
                        data[key][1].append(industry_codes)
                        added_count += 1
                        print(f"为键 '{key[:50]}...' 添加排序后的行业代码: {industry_codes}")
                    else:
                        print(f"跳过键 '{key[:50]}...' - 行业代码已存在: {industry_codes}")
                else:
                    print(f"警告: 键 '{key}' 的data[key][1]不是列表格式")
            else:
                print(f"警告: 键 '{key}' 的数据结构不符合预期")
        else:
            print(f"警告: matched_codes中的键 '{key}' 在原始data中不存在")
    
    print(f"成功为 {added_count} 个项目添加了行业代码")
    return added_count

# 调用函数将matched_codes添加到原始数据中（只调用一次）
print("\n=== 将匹配的行业代码添加到原始数据中 ===")
added_count = add_matched_codes_to_data(data, matched_codes)

# 删除重复的调用
# 注释掉或删除以下重复的调用：
# print("\n=== 将匹配的行业代码添加到原始数据中 ===")
# added_count = add_matched_codes_to_data(data, matched_codes)

# 验证添加结果 - 检查前5个添加了行业代码的项目
print("\n=== 验证添加结果 ===")
count = 0
for key, value in data.items():
    if key in matched_codes:
        print(f"键: {key[:100]}...")
        print(f"原始数据结构: {len(value[1])} 个子列表")
        
        # 显示最后一个子列表（应该是新添加的行业代码）
        if len(value[1]) > 0:
            last_sublist = value[1][-1]
            print(f"最后一个子列表（行业代码）: {last_sublist}")
            
            # 显示对应的matched_codes内容进行比较
            matched_info = matched_codes[key]
            expected_codes = [item[2] for item in matched_info]
            print(f"期望的行业代码: {expected_codes}")
            print(f"匹配成功: {last_sublist == expected_codes}")
        print("-" * 50)
        
        count += 1
        if count >= 5:
            break

# 将更新后的数据重新写入文件
updated_output_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data_with_industry_codes.json")
with open(updated_output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n已将添加行业代码后的数据写入到 {updated_output_file.absolute()}")

# 统计最终结果
total_items = len(data)
items_with_codes = len(matched_codes)
print(f"\n=== 最终统计 ===")
print(f"总项目数: {total_items}")
print(f"成功提取并添加行业代码的项目数: {items_with_codes}")
print(f"添加行业代码的成功率: {items_with_codes/total_items*100:.2f}%")




import pandas as pd

print(f"\n=== 重新读取merged_data_with_industry_codes.json ===")
updated_output_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data_with_industry_codes.json")
with open(updated_output_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"重新加载了 {len(data)} 个键值对")
# 读取CSV文件
csv_file_path = Path(r".\调用文件\用于行业分类分析的可视化表\8.新算法_添加所属国家后的供应链关系表.csv")
print(f"\n=== 读取CSV文件并添加行业代码列 ===")

try:
    # 读取CSV文件，第一行作为表头
    df = pd.read_csv(csv_file_path, encoding='utf-8')
    print(f"成功读取CSV文件，共有 {len(df)} 行数据，{len(df.columns)} 列")
    print(f"CSV文件的列名: {list(df.columns)}")
    
    # 在DataFrame末尾添加新列'行业代码'
    df['行业代码'] = ''
    
    # 统计变量
    total_json_entries = len(data)
    matched_entries = 0
    assigned_rows = 0
    
    print(f"\n开始处理 {total_json_entries} 个JSON条目...")
    
    # 遍历merged_data_with_industry_codes.json的内容
    for json_key, json_value in data.items():
        if isinstance(json_value, list) and len(json_value) >= 1:
            # 获取行索引列表（第一个元素）
            if isinstance(json_value[0], list):
                row_indices = json_value[0]
            else:
                continue
            
            # 获取行业代码（如果存在）
            industry_codes_str = ""
            if len(json_value) >= 2 and isinstance(json_value[1], list):
                # 查找行业代码列表（最后一个非文本的子列表）
                for sublist in reversed(json_value[1]):
                    if isinstance(sublist, list) and len(sublist) > 0:
                        # 检查是否是行业代码列表（短字符串组成的列表）
                        if all(isinstance(code, str) and len(code) <= 6 for code in sublist):
                            industry_codes_str = "|".join(sublist)
                            break
            
            # 如果找到了行业代码，对指定的行索引进行赋值
            if industry_codes_str:
                matched_entries += 1
                for row_idx in row_indices:
                    if isinstance(row_idx, int) and 0 <= row_idx < len(df):
                        df.loc[row_idx, '行业代码'] = industry_codes_str
                        assigned_rows += 1
                        if assigned_rows <= 10:  # 只显示前10个赋值示例
                            print(f"为第 {row_idx} 行赋值行业代码: {industry_codes_str}")
                
                if matched_entries <= 5:  # 只显示前5个条目的详细信息
                    print(f"JSON键: {json_key[:80]}...")
                    print(f"  行索引: {row_indices}")
                    print(f"  行业代码: {industry_codes_str}")
                    print()
    
    print(f"\n=== 处理统计 ===")
    print(f"JSON总条目数: {total_json_entries}")
    print(f"包含行业代码的条目数: {matched_entries}")
    print(f"成功赋值的行数: {assigned_rows}")
    
    # 检查行业代码列的填充情况
    filled_rows = df['行业代码'].ne('').sum()
    print(f"CSV中有行业代码的行数: {filled_rows}")
    print(f"CSV总行数: {len(df)}")
    print(f"行业代码填充率: {filled_rows/len(df)*100:.2f}%")
    
    # 显示一些带行业代码的行的示例
    print(f"\n=== 前10行带行业代码的数据示例 ===")
    rows_with_codes = df[df['行业代码'] != ''].head(10)
    if len(rows_with_codes) > 0:
        for idx, row in rows_with_codes.iterrows():
            print(f"行 {idx}: 行业代码 = '{row['行业代码']}'")
    else:
        print("没有找到带行业代码的行")
    
    # 保存更新后的CSV文件
    output_csv_path = Path(r".\调用文件\用于行业分类分析的可视化表\9.新算法_添加所属国家后的供应链关系表_带行业代码.csv")
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n已将添加行业代码后的CSV保存到: {output_csv_path.absolute()}")
    
    # 显示行业代码的分布统计
    print(f"\n=== 行业代码分布统计 ===")
    industry_code_counts = df['行业代码'].value_counts()
    print(f"不同行业代码的数量: {len(industry_code_counts)}")
    if len(industry_code_counts) > 0:
        print("前10个最常见的行业代码:")
        for code, count in industry_code_counts.head(10).items():
            if code != '':  # 跳过空值
                print(f"  {code}: {count} 次")

except FileNotFoundError:
    print(f"错误: 找不到CSV文件 {csv_file_path}")
except Exception as e:
    print(f"处理CSV文件时发生错误: {e}")
    import traceback
    traceback.print_exc()

print(f"\n=== 所有处理完成 ===")