from pathlib import Path
import pandas as pd
import json

df = pd.read_excel(r'.\调用文件\用于行业分类分析的可视化表\GB_T 4754-2017 国民经济行业分类（一维表）.xlsx')

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

# 如果DESCRIPTION栏是空的，则将NAME的内容添加到DESCRIPTION栏目中
df.loc[df['DESCRIPTION'].isnull(), 'DESCRIPTION'] = df.loc[df['DESCRIPTION'].isnull(), 'NAME']

df.drop(columns=['NAME'], inplace=True)

# 删除INDUSTRY_ID全为字母的行
df = df[~df['INDUSTRY_ID'].str.isalpha()].reset_index(drop=True)

	# 输出路径，文件扩展名更改为 .json
output_file = Path(r'.\调用文件\用于行业分类分析的可视化表\industry_code.json')
output_file.parent.mkdir(parents=True, exist_ok=True)
 
def clean_data(x):
    """数据清洗函数"""
    if pd.isna(x):
        return None
    if isinstance(x, str):
        # 清理换行符和反斜杠
        return x.replace('\n', ' ').replace('\\', '')
    return x

# 将整个DataFrame进行清洗，然后转换为记录列表
cleaned_df = df.applymap(clean_data)
records_list = cleaned_df.to_dict(orient='records')
 
# 将整个列表写入一个JSON文件
with open(output_file, 'w', encoding='utf-8') as f:
    # 使用 json.dump 将列表写入文件
    # indent=4 使JSON文件格式美观，易于阅读
    json.dump(records_list, f, ensure_ascii=False, indent=4)
 
# 验证文件
with open(output_file, 'r', encoding='utf-8') as f:
    # 读取并解析整个JSON文件
    data = json.load(f)
    print(f"成功将 {len(data)} 条记录写入 {output_file}")
    if data:
        print("文件中的第一条记录:")
        print(data[0])





