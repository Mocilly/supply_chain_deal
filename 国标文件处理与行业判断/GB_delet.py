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



# 输出到JSONL文件（每行一个JSON对象）
output_file = r'C:\Users\Mocilly\Desktop\output.jsonl'

with open(output_file, 'w', encoding='utf-8') as f:
    for i in df.index:
        # 将每行数据转为字典格式
        record = {col: df.loc[i, col] for col in df.columns}
        
        # 写入JSON行格式（ensure_ascii=False保持中文可读）
        f.write(json.dumps(record, ensure_ascii=False) + '\n')



