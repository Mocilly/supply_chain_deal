
# 函数：处理missing_codes并批量保存结果
import json
from pathlib import Path
import re
import sys
import time
from tqdm import tqdm
# 将系统路径添加到Python搜索路径
import sys
sys.path.append(r'c:\Users\Mocilly\Desktop\Githook\supply_chain_deal-3')  # 添加根目录

sys.path.append(r'.\industy_calculate')  # 添加相对路径
from siliconflow_qa_record import talk_initialize, execute_conversation, process_lines_to_dict

misssing_code_file_revise = Path('.\调用文件\用于行业分类分析的可视化表\data_need_to_revised.json')


# 读取未匹配的行业代码信息
print(f"\n正在读取未匹配的行业代码信息: {misssing_code_file_revise}")
try:
    with open(misssing_code_file_revise, 'r', encoding='utf-8') as f:
        loaded_missing_codes = json.load(f)
    
    print(f"成功加载未匹配的行业代码信息，共 {len(loaded_missing_codes)} 个条目")
    
except Exception as e:
    print(f"读取未匹配的行业代码信息时出错: {e}")


def process_missing_codes_in_batches(loaded_missing_codes, data, num):
    """
    处理未匹配的行业代码并保存结果
    
    参数:
    loaded_missing_codes - 加载的未匹配行业代码字典
    data - 原始数据字典
    """
    # 创建输出目录
    output_dir = Path(r".\调用文件\用于行业分类分析的可视化表\中间修正文件存储")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化LLM通信
    print("初始化LLM通信...")
    url, payload, headers = talk_initialize()
    
    # 提示消息
    message_need_to_add = [
        "我接下来将发一组供应链关系的起始公司名称和相关的关键词，\
         请通过联网查询相关信息来跟中国国民经济行业分类标准（2017）2019修订版相匹配来看所发的供应链信息属于哪一个行业，给出行业四位码，并给出判断依据，\
         参考信息网址同步显示出来,判断中可将source_company_keyword中的查询所得信息和keyword中的查询所得信息的权重调高(如果没有该字段则正常搜索),\n",

        "参照中国国民经济行业分类标准的行业代码和行业描述来输出下列信息中可能性最高的单个分类\n"
         "显示格式：行业分类代码：xxxx（依据中国国民经济行业分类），判断依据：xxxxxx，参考网址:xxxx（列出下方供应链信息联网搜索后得到的信息参考的网址，诸如查询该公司所得的业务信息）\n",
    ]
    
    # 发送初始化消息
    _, _ = execute_conversation(url, payload, headers, {
        "role": "user", "content": message_need_to_add[0]
    })
    
    # 处理缺失的代码
    batch_size = 100
    processed_count = 0
    batch_number = 1
    batch_data = {}
    
    print(f"开始处理未匹配的行业代码，总计 {len(loaded_missing_codes)} 个条目...")
    
    # 使用tqdm显示进度条
    for idx, key_value in tqdm(loaded_missing_codes.items(), desc="处理中"):
        idx = int(idx)  # 确保索引是整数
        
        # 获取对应的数据项
        key_idx = 0
        target_key = None
        for k in data.keys():
            if key_idx == idx:
                target_key = k
                break
            key_idx += 1
        
        if not target_key:
            print(f"未找到索引 {idx} 对应的键")
            continue
        
        # 解析键以构造消息
        parts = target_key.split('|')
        extracted = {}
        for part in parts:
            if ':' in part:
                k, v = part.split(':', 1)
                extracted[k.strip()] = v.strip()
        
        # 构造消息字符串
        fields = [
            ("source_compan_name", extracted.get("SOURCE_name", "")),
            ("target_company_name", extracted.get("TARGET_name", "")),
            ("source_company_keyword", extracted.get("source_company_keyword", "")),
            ("target_company_keyword", extracted.get("target_company_keyword", "")),
            ("keyword", extracted.get("keywords", "")),
        ]
        
        # 过滤掉值为空的字段
        filtered_fields = [f"{name}:{value}" for name, value in fields if value]
        message = ", ".join(filtered_fields)
        message_send = message_need_to_add[1] + message
        
        # 请求LLM回答
        try:
            content, _ = execute_conversation(url, payload, headers, 
                                           {"role": "user", "content": message_send})
            
            # 保存到当前批次
            if content:
                # 按原始数据格式存储，保持原格式 [indices, [[content]]]
                batch_data[target_key] = [data[target_key][0], [[content]]]
                processed_count += 1
            
            # 每处理batch_size个条目保存一次
            if processed_count % batch_size == 0:
                # 保存当前批次
                batch_file = output_dir / f"batch_{num}_{batch_number}.json"
                with open(batch_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, ensure_ascii=False, indent=2)
                
                print(f"已完成批次 {batch_number}，保存到 {batch_file}")
                batch_number += 1
                batch_data = {}  # 重置批次数据
            
            # 添加适当的延时，避免API限制
            time.sleep(1)
        
        except Exception as e:
            print(f"处理索引 {idx} 时出错: {e}")
    
    # 保存最后不足batch_size的批次
    if batch_data:
        batch_file = output_dir / f"batch_{num}_{batch_number}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        
        print(f"已完成最后批次 {batch_number}，保存到 {batch_file}")
    
    print(f"处理完成，总共处理了 {processed_count} 个条目，分为 {batch_number} 个批次")
    return True


# 加载原始数据
input_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data.json")
print(f"正在加载原始数据文件: {input_file}")
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"成功加载原始数据，共 {len(data)} 个键值对")
except Exception as e:
    print(f"读取原始数据时出错: {e}")
    sys.exit(1)

# 读取loaded_missing_codes的前1000行储存为新的字典变量，用于分批执行方法
sample_1000_missing_codes = dict(list(loaded_missing_codes.items())[2900:3000]) #每个num对应1000条数据

# 显示部分读取的内容\
print("未匹配行业代码的前5个条目:")
for i, (key, value) in enumerate(sample_1000_missing_codes.items()):
    if i >= 5:
        break
    print(f"索引 {key}: {value}")

process_missing_codes_in_batches(sample_1000_missing_codes, data,num= 1) #num分批次是为了多终端运行脚本



def merge_json_files(source_dir_path: Path, output_file_path: Path):
    """
    合并指定目录中的所有JSON文件到一个文件中。

    参数:
    source_dir_path (Path): 包含JSON文件的源目录路径。
    output_file_path (Path): 合并后输出的JSON文件路径。
    """
    merged_data = {}
    
    print(f"开始合并目录 '{source_dir_path}' 中的JSON文件...")
    
    # 确保源目录存在
    if not source_dir_path.is_dir():
        print(f"错误: 源目录 '{source_dir_path}' 不存在或不是一个目录。")
        return

    json_files = list(source_dir_path.glob('*.json')) # 假设所有批处理文件都是.json格式
    
    if not json_files:
        print(f"在目录 '{source_dir_path}' 中没有找到JSON文件。")
        return

    for file_path in tqdm(json_files, desc="合并文件中"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_to_merge = json.load(f)
                merged_data.update(data_to_merge) # 合并字典
            print(f"已合并文件: {file_path.name}")
        except json.JSONDecodeError:
            print(f"警告: 文件 '{file_path.name}' 不是有效的JSON格式，已跳过。")
        except Exception as e:
            print(f"读取或合并文件 '{file_path.name}' 时出错: {e}")
            
    # 确保输出目录存在
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"\n所有JSON文件已成功合并到: {output_file_path}")
        print(f"合并后的文件包含 {len(merged_data)} 个条目。")
    except Exception as e:
        print(f"写入合并后的文件 '{output_file_path}' 时出错: {e}")


# 定义源目录和目标文件路径
source_directory = Path(r".\调用文件\用于行业分类分析的可视化表\中间修正文件存储") # 注意这里我假设中间文件在子目录 "2" 中，根据您的process_missing_codes_in_batches函数
target_output_file = Path(r".\调用文件\用于行业分类分析的可视化表\second_round_llm_revised.json")

# 执行合并操作
merge_json_files(source_directory, target_output_file)



