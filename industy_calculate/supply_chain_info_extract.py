import pandas as pd
import os
import json

df_sc = pd.read_csv(r'.\调用文件\用于行业分类分析的可视化表\8.新算法_添加所属国家后的供应链关系表.csv') #供应链df
# df_cop = pd.read_stata(r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data\时间趋势分析数据\时间趋势分析数据cop表.dta') #cop表

# df_cop.columns

df_sc.columns

#创造方法 来 获取df_sc中的 source_compan_name，target_company_name，source_company_keyword，target_company_keyword，keyword
df_sc = df_sc[['source_company_id','target_company_id','SOURCE_name','TARGET_name','source_company_keyword','target_company_keyword',
               'keyword1','keyword2','keyword3','keyword4','keyword5','keyword6','keyword7','keyword8','keyword9','keyword10']]

df_sc.columns
# 创造方法 来 获取df_sc其中一行的 'SOURCE_name','TARGET_name'，source_company_keyword，target_company_keyword，keyword
def extract_row_info(row):
    return {
        'SOURCE_name': row['SOURCE_name'] if pd.notna(row['SOURCE_name']) else '',
        'TARGET_name': row['TARGET_name'] if pd.notna(row['TARGET_name']) else '',
        'source_company_keyword': row['source_company_keyword'] if pd.notna(row['source_company_keyword']) else '',
        'target_company_keyword': row['target_company_keyword'] if pd.notna(row['target_company_keyword']) else '',
        'keywords': ','.join([row[f'keyword{i}'] for i in range(1, 11) if pd.notna(row[f'keyword{i}'])])
    }

#将字典内容输出成完整字符串
def dict_to_string(info_dict):
    return '|'.join([f"{key}:{value}" for key, value in info_dict.items()])


# 示例：获取df_sc第一行的信息
row_info = extract_row_info(df_sc.iloc[0])
print(row_info)
print(dict_to_string(row_info))

length_df_sc = len(df_sc.index)
# 遍历df_sc将提取的信息作为键，所有索引作为列表作为值
info_dict = {}
for index, row in df_sc.iterrows():
    row_info = extract_row_info(row)
    if row_info['SOURCE_name'] == '' or row_info['TARGET_name'] == '':
        row_info_str = 'info_not_found'
    else:
        row_info_str = dict_to_string(row_info)
    if row_info_str not in info_dict:
        info_dict[row_info_str] = []
    info_dict[row_info_str].append(index)
    print(f'已解决{index+1}/{length_df_sc}')


len(info_dict.items()) #查看字典的长度
# 查看字典的前10个键值对
for i, (key, value) in enumerate(info_dict.items()):
    if i < 10:
        print(f"Key: {key}, Value: {value}")
    else:
        break

# 将字典输出到json文件予以存储

output_file = r'.\调用文件\用于行业分类分析的可视化表\用于行业分类分析的可视化表info_dict.json'
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(info_dict, f, ensure_ascii=False, indent=4)

print(f"字典已成功存储到文件路径: {output_file}")



