import os
import json
import glob
from pathlib import Path

# 定义目录路径
json_dir = Path(r".\调用文件\用于行业分类分析的可视化表\中间文件")
output_file = Path(r".\调用文件\用于行业分类分析的可视化表\merged_data.json")

# 确保目录路径存在
if not json_dir.exists():
    print(f"目录 {json_dir} 不存在")
    exit(1)

# 获取所有JSON文件
json_files = list(json_dir.glob("*.json"))

if not json_files:
    print(f"在 {json_dir} 中没有找到JSON文件")
    exit(1)

print(f"找到 {len(json_files)} 个JSON文件")

# 合并JSON数据为一个大字典
merged_data = {}

for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 根据JSON结构决定如何合并
        if isinstance(data, dict):
            # 直接合并字典的键值对
            merged_data.update(data)
        elif isinstance(data, list):
            # 如果是列表，则遍历其中的每个字典并合并
            for item in data:
                if isinstance(item, dict):
                    merged_data.update(item)
        
        print(f"已合并: {json_file}")
    except Exception as e:
        print(f"处理 {json_file} 时出错: {e}")

# 清理所有文本中的星号（*）
for key, value in merged_data.items():
    for i, data_list in enumerate(value[1]):
        for j, text in enumerate(data_list):
            # 删除所有星号
            cleaned_text = text.replace('*', '')
            merged_data[key][1][i][j] = cleaned_text

# 将合并后的数据写入新文件
output_path = Path(output_file)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

print(f"已将合并的JSON数据写入到 {output_path.absolute()}")