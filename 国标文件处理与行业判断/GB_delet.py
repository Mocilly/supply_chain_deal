from pathlib import Path
import pandas as pd
import json

df = pd.read_excel(r'C:\Users\Mocilly\Desktop\GB_T 4754-2017 国民经济行业分类（一维表）.xlsx')

df.columns
df.drop(columns=['ID','PARENT_ID', 'LEVEL_TYPE'], inplace=True)
df.drop(index=[0], inplace=True)
df.reset_index(drop=True, inplace=True)
df
type(df.loc[25,'INDUSTRY_ID'])

#查看df某一列中缺失项
df['DESCRIPTION'].isnull().sum()
#查看df某一列中缺失项的索引
null_list = df[df['DESCRIPTION'].isnull()].index.tolist()
null_list
df.loc[null_list]

#查看两列都是缺失值的行
df[df['DESCRIPTION'].isnull() & df['NAME'].isnull()]

#将DESCRIPTION列全部转化为str格式
df['INDUSTRY_ID'] = df['INDUSTRY_ID'].astype(str)



for i in df.index:
    id = df.loc[i,'INDUSTRY_ID']
    if len(id) == 4:
        if pd.isnull(df.loc[i,'DESCRIPTION']):
            df.loc[i,'DESCRIPTION'] = df.loc[i,'NAME']
sub_count = 0
for i in df.index:
    id = df.loc[i,'INDUSTRY_ID']
    if len(id) == 4:
        sub_count += 1

print(f'Sub count: {sub_count}')


#查看df某一列中缺失项的索引                                               

null_list = df[df['DESCRIPTION'].isnull()].index.tolist()
null_list
df.loc[null_list]
for i in df.index:

    id = df.loc[i,'INDUSTRY_ID']
    if len(id) != 4:
        null_list.append(i)
df.drop(index=null_list, inplace=True)

df.drop(columns=['NAME'], inplace=True)

	# 输出路径
output_file = Path(r'.\调用文件\用于行业分类分析的可视化表\output.jsonl')
output_file.parent.mkdir(parents=True, exist_ok=True)
 
def clean_data(x):
    """数据清洗函数"""
    if pd.isna(x):
        return None
    if isinstance(x, str):
        # 清理换行符和反斜杠
        return x.replace('\n', ' ').replace('\\', '')
    return x
 
with open(output_file, 'w', encoding='utf-8') as f:
    for i in df.index:
        cleaned_record = df.loc[i].apply(clean_data).to_dict()
        json_line = json.dumps(
            cleaned_record,
            ensure_ascii=False,
            separators=(',', ':')
        ) + '\n'  # 正确添加换行符
        f.write(json_line)
 
# 验证文件
with open(output_file, 'r', encoding='utf-8') as f:
    first_line = f.readline()
    print(repr(first_line))  # 应输出：'{"INDUSTRY_ID":"0111","DESCRIPTION":"稻谷种植"}\n'





