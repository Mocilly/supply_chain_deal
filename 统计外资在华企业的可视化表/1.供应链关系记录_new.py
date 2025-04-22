# region ######################################################  开始必备执行代码   
import os

import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
from component.company_supplyChain import SupplyRelation, Company, SupplyChainAnalyzer

# pd.options.display.max_rows = 10000  # 终端显示10000行


def Save(fileName,file_type,path,df):
    if file_type == 'xlsx':
        #.将上面的df保存为xlsx表格
        fileName = fileName +'.xlsx'
        savePath = ''.join([path,fileName])
        wr = pd.ExcelWriter(savePath)#输入即将导出数据所在的路径并指定好Excel工作簿的名称
        df.to_excel(wr, index = False)

        wr._save()
    if file_type == 'dta':
        fileName = fileName +'.dta'
        savePath = ''.join([path,fileName])
        df.to_stata(savePath,
                        write_index=False,
                        version=118)


# 路径集合#
path_dic = {'foreign_data':r"C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data",
            'cop_data':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\上市公司数据',
            'middle':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\中间文件',
            'save':r'C:/Users/Mocilly/Desktop/研创平台课题项目/数据//',
            }

#endregion 

# 7.1 将新建的断裂指标添加到上市公司数据中_ 新计算方法(关联产业链破裂也算作break计入上市公司)
'''新计算方法说明:
    考虑到上市公司的安全性资金较为充裕，因此在贸易战期间其产业链不太可能会发生断裂。
    因此我们采用一种新的方法来计算成上市公司的产业链断裂。
    我们将非上市公司与上市公司的关联产业链纳入计算，如果关联产业链发生断裂，那么即意味着上市公司受到了贸易战冲击导致的间接产业链断裂效应
'''



# region 中间处理过程
#获取供应链表
base_dir = path_dic['foreign_data']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[6]
df_cop = pd.read_stata(files[7]) #公司df 
df_sc = pd.read_stata(files[6]) #供应链df


# 得到供应链所有公司集合
df_sc.dtypes
df_cop.dtypes


df_cop = df_cop[['start_','end_','id','home_region','country']]
df_cop


all_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_sc.index:
    all_cop_set.add(df_sc.loc[i,'source_company_id'])
    print(f'已解决{i+1}')

# 记录country 和 home_region 到country_belong里面

df_sc['source_company_belong'] = None
df_sc.columns
df_cop.columns
for i,cop in enumerate(all_cop_set):
    
    condition_cop = (df_cop['id'] == cop)
    condition_sc = (df_sc['source_company_id'] == cop)
    df = df_cop[condition_cop]
    df_sc_index_list = df_sc[condition_sc].index

    column_set_1 = set(df["home_region"].dropna())
    column_set_2 = set(df["country"].dropna())
    column_set = column_set_1 | column_set_2
    sc_status = None
    #更改逻辑 ,记录country和home_region到country_belong里面
    if len(column_set) == 1:
        temp_str = column_set.pop()
        sc_status = f'home_region:{temp_str}&country:{temp_str}'
    elif len(column_set) > 1:
        if len(column_set_1) == 1 : #如果home_region不为空，则取出home_region
            temp_str = column_set_1.pop()
            sc_status = f'home_region:{temp_str}&'
        elif len(column_set_1) > 1:
            temp_str = '|'.join([country for country in list(column_set_1)])
            sc_status = f'home_region:{temp_str}&'
        if len(column_set_2) == 1: #如果country不为空，则取出country
            temp_str = column_set_2.pop()
            sc_status += f'country:{temp_str}'
        elif len(column_set_2) > 1:
            temp_str = '|'.join([country for country in list(column_set_2)])
            sc_status += f'country:{temp_str}'
    else:
        sc_status = 'Nation_Not_Found'

    for r in df_sc_index_list:
        df_sc.loc[r,'source_company_belong'] = sc_status
    
    print(f'已解决{i+1}/{len(all_cop_set)}')


df_sc['target_company_belong'] = None
df_sc.columns
df_cop.columns
target_cop_set = set()  # 供应链中的target公司集合  ,
for i in df_sc.index:
    target_cop_set.add(df_sc.loc[i,'target_company_id'])
    print(f'已解决{i+1}')
for i,cop in enumerate(target_cop_set):
    condition_cop = (df_cop['id'] == cop)
    condition_sc = (df_sc['target_company_id'] == cop)
    df = df_cop[condition_cop]
    df_sc_index_list = df_sc[condition_sc].index

    column_set_1 = set(df["home_region"].dropna())
    column_set_2 = set(df["country"].dropna())
    column_set = column_set_1 | column_set_2
    sc_status = None
    #更改逻辑 ,记录country和home_region到country_belong里面
    if len(column_set) == 1:
        temp_str = column_set.pop()
        sc_status = f'home_region:{temp_str}&country:{temp_str}'
    elif len(column_set) > 1:
        if len(column_set_1) == 1 : #如果home_region不为空，则取出home_region
            temp_str = column_set_1.pop()
            sc_status = f'home_region:{temp_str}&'
        elif len(column_set_1) > 1:
            temp_str = '|'.join([country for country in list(column_set_1)])
            sc_status = f'home_region:{temp_str}&'
        if len(column_set_2) == 1: #如果country不为空，则取出country
            temp_str = column_set_2.pop()
            sc_status += f'country:{temp_str}'
        elif len(column_set_2) > 1:
            temp_str = '|'.join([country for country in list(column_set_2)])
            sc_status += f'country:{temp_str}'
    else:
        sc_status = 'Nation_Not_Found'

    for r in df_sc_index_list:
        df_sc.loc[r,'target_company_belong'] = sc_status
    
    print(f'已解决{i+1}/{len(target_cop_set)}')



df_sc[df_sc['target_company_belong'].isna()] #查看是否有空值
#有空值说明上面的代码在处理国家所属的逻辑上还是有点问题的，但source_company_belong处理后并未出现空值，
# 因此此处可能是supply_chain的target_company_id在company.dta中并不存在所致，所以我们将281个空值设为nation_not_found
na_index = df_sc[df_sc['target_company_belong'].isna()].index
len(na_index) #查看空值数量
for i in na_index:
    df_sc.loc[i,'target_company_belong'] = 'Nation_Not_Found'
    print(f'已解决{i+1}')

for i in df_sc.index:
    c_belong = df_sc.loc[i,'target_company_belong']
    if c_belong.startswith('|'):
        c_belong = c_belong[1:]
    if c_belong.endswith('|'):
        c_belong = c_belong[:-1]
        
    df_sc.loc[i,'target_company_belong'] = c_belong
    print(f'已解决{i+1}')

# region 中间处理过程_1.2，删掉开头结尾的 | ，就不在中间处理过程_1上的原代码上作修改了
for i in df_sc.index:
    c_belong = df_sc.loc[i,'source_company_belong']
    home_region = c_belong[:c_belong.find('&')]
    hr_c = home_region[home_region.find(':')+1:]
    country = c_belong[c_belong.find('&')+1:]
    c = country[country.find(':')+1:]
    if hr_c.startswith('|'):
        hr_c = hr_c[1:]
    if hr_c.endswith('|'):
        hr_c = hr_c[:-1]
    if c.startswith('|'):
        c = c[1:]
    if c.endswith('|'):
        c = c[:-1]

    df_sc.loc[i,'source_company_belong'] = f"home_region:{hr_c}&country:{c}"
    print(f'已解决{i+1}')

#endregion


df_sc[df_sc['target_company_belong'].isna()]
df_sc[df_sc['source_company_belong'].isna()]
print(df_sc['end_'].head())  # 查看前几行数据
print(df_sc['end_'].apply(type).value_counts())  # 统计元素类型
df_sc[df_sc['end_'].isna()]
df_sc.to_csv(path_dic['middle']+'\\' + '8.新算法_添加所属国家后的供应链关系表.csv', index=False)
# Save('8.新算法_添加所属国家后的供应链关系表','xlsx',path_dic['middle'] + '\\',df_sc)

#endregion 中间处理过程 



# region 中间处理过程_2
#获取供应链表
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[7]
# df_sc = pd.read_excel(files[7],dtype={'source_company_id':str,'target_company_id':str,
#                                               'SOURCE_ticker':str,'TARGET_ticker':str}) 
df_sc = pd.read_csv(
    files[7],
    dtype={
        'source_company_id': str,
        'target_company_id': str,
        'SOURCE_ticker': str,
        'TARGET_ticker': str
    }
)

# 转换 start_ 列（兼容纯日期或含时间的字符串）
df_sc["start_"] = pd.to_datetime(df_sc["start_"], errors="coerce")
# 截断 start_ 列的时间部分（保留日期）
df_sc["start_"] = df_sc["start_"].dt.floor("D")


# Pandas 的 Timestamp 使用 64 位整数 存储纳秒级时间戳（从 1970 年 1 月 1 日起算），
# 其最大日期范围约为 公元 1677 年到 2262 年。
# 当代码中使用了超出此范围的日期（如 4000-01-01），尝试将其转换为纳秒时会触发整数溢出（OverflowError），
# 最终导致 OutOfBoundsDatetime 错误。


# 2. 转换日期（自动推断格式）
df_sc["end_"] = pd.to_datetime(df_sc["end_"], errors="coerce").dt.floor("D")

	# 步骤3：填充缺失值(其实质为4000-01-01 00:00:00)为 2025-01-01
df_sc["end_"] = df_sc["end_"].fillna(pd.to_datetime("2025-01-01"))
 

df_sc.head(50)
df_sc.info()

print("end_ 缺失值数量:", df_sc['end_'].isna().sum())
print("start_ 缺失值数量:", df_sc['start_'].isna().sum())







all_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_sc.index:
    all_cop_set.add(df_sc.loc[i,'source_company_id'])
    all_cop_set.add(df_sc.loc[i,'target_company_id'])
    print(f'已解决{i+1}')

len(all_cop_set)    # 供应链中的公司数量

companies = dict()
company_set_record = set()
for i,cop in enumerate(all_cop_set):
    company_in_set = cop in company_set_record
    if not company_in_set:
        condition = (df_sc["source_company_id"] == cop)
        subset = df_sc.loc[condition]
        if subset.empty:
            # 如果没有找到对应的行，跳过
            continue
        #此处没有做公司可能退市的处理，如果上市则将其标记为上市公司，记为True
        is_all_na = subset["SOURCE_ticker"].isna().all()
        #国家去重后检测是否应该添加到Companies字典中
        source_country_set = set(subset["source_company_belong"].dropna())
        if source_country_set != set():
            companies[cop] = Company(cop,source_country_set.pop(),not is_all_na)
            company_set_record.add(cop)

    print(f'已解决{i+1}/{len(all_cop_set)}')

for i in df_sc.index:
    cop = df_sc.loc[i,'target_company_id']
    company_in_set = cop in company_set_record
    if not company_in_set:
        target_country = df_sc.loc[i,'target_company_belong']
        has_ticker = not pd.isna(df_sc.loc[i, 'TARGET_ticker'])
        if companies.get(cop, None) == None:
            # 如果没有找到对应的行，跳过
            continue
        companies[cop] = Company(cop,target_country,has_ticker)
        company_set_record.add(cop)
    print(f'已解决{i+1}/{len(df_sc.index)}')

len(company_set_record)
len(companies)
sample_relations = []
len_df_sc = len(df_sc.index)
for i in df_sc.index:
    source_cop =  df_sc.loc[i,'source_company_id']
    target_cop = df_sc.loc[i,'target_company_id']
    start_time = df_sc.loc[i,'start_']
    end_time = df_sc.loc[i,'end_']
    if companies.get(source_cop,None) == None or companies.get(target_cop,None) == None: ## 如果公司不存在于字典中，则跳过
        continue
    sample_relations.append((companies[source_cop],companies[target_cop],start_time,end_time))
    print(f'已解决{i+1}/{len_df_sc}')





relations = []
count = 0
len_sample_relations = len(sample_relations)
for from_co, to_co, start, end in sample_relations:
    relations.append(SupplyRelation(from_co, to_co, start, end))
    print(f'已解决{count+1}/{len_sample_relations}')
    count+=1

len(relations)
import json

##################################################存储company变量
# 将公司对象转换为字典列表
companies_to_save = []
count = 0
total = len(companies)
for key,cop in companies.items():
    companies_to_save.append({
        'id': cop.id,
        'country': cop.country, 
        'listed': cop.listed
    })
    print(f'已转换并保存 {count+1}/{total}')
    count += 1

################################################### 写入JSON文件
with open(path_dic['middle'] + '\\' +'company.json', 'w') as f:
    json.dump(companies_to_save, f, indent=4)
print("数据已保存至 company.json")

##################################################存储relation变量
# 将对象转换为字典列表
data_to_save = []
count = 0
total = len(relations)
for relation in relations:
    data_to_save.append({
        'from_co': relation.from_co.id,
        'to_co': relation.to_co.id,
        'start': relation.start.strftime("%Y-%m-%d"),  # 格式化为字符串
        'end': relation.end.strftime("%Y-%m-%d"),  # 含时分秒
        'status' :relation.status
    })
    print(f'已转换并保存 {count+1}/{total}')
    count += 1
 

################################################### 写入JSON文件
with open(path_dic['middle'] + '\\' + 'supply_relations.json', 'w') as f:
    json.dump(data_to_save, f, indent=4)
print("数据已保存至 supply_relations.json")


c = 0
for i in relations:
    print(i)
    print(f'{type(i.end)}:{i.end}')
    c+=1
    if c>50:
        break
#endregion 中间处理过程_2

# region 供应链长链建立
import json
################################################## 读取JSON文件

with open(path_dic['middle'] + '\\' + 'company.json', 'r') as f:
    loaded_company_data = json.load(f)

with open(path_dic['middle'] + '\\' + 'supply_relations.json', 'r') as f:
    loaded_relation_data = json.load(f)

#重建company对象
companies = dict()
count = 0
for cop in loaded_company_data:
    companies[cop['id']] = Company(cop['id'],cop['country'],cop['listed'])
    # print(f'已解决{count+1}')
    count+=1

#重建relation对象
count = 0
restored_relations = []
for rel in loaded_relation_data:
    # 假设Company对象需要通过name或id重建
    from_co = companies[rel['from_co']]  
    to_co = companies[rel['to_co']]
    
    # 时间字符串转回datetime对象
    start = datetime.strptime(rel['start'], "%Y-%m-%d")
    end = datetime.strptime(rel['end'], "%Y-%m-%d")
    
    restored_relations.append(
        SupplyRelation(from_co, to_co, start, end)
    )
    # print(f'已解决{count+1}')
    count+=1

restored_relations

 # 初始化分析器
analyzer = SupplyChainAnalyzer(restored_relations, recovery_period=90,end_date=datetime(2024,12,31))
len(analyzer.graph)
# # analyzer.graph
# for cop, cop_relation in analyzer.graph.items():
#         print(f"公司名字：{cop.id}")
#         for rel in cop_relation:
#             print(f"供应链关系：{rel}")
# transfers = analyzer.detect_transfers()
# transfers = analyzer.detect_transfers()
# transfers
# for t in transfers:
#     print(f"{t['supplier']} 从 {t['from_client']} 转移到 {t['to_client']} "
#             f"(间隔 {t['gap_days']} 天)")


# 查找长度≥1  <=10的供应链,先查找100个  （修改dfs算法，增加一层供应链含中量检测）
chains = analyzer.find_supply_chains(min_length=1,max_depth=4,start_index=0,end_index=len(analyzer.graph)+1)
# chains = analyzer.find_supply_chains(min_length=1,max_depth=4,start_index=0,end_index=math.floor(len(analyzer.graph)/3))
# chains = analyzer.find_supply_chains(min_length=1,max_depth=4,start_index=math.floor(len(analyzer.graph)/3),end_index=math.floor(len(analyzer.graph)/3*2))
# chains = analyzer.find_supply_chains(min_length=1,max_depth=4,start_index=math.floor(len(analyzer.graph)/3*2),end_index=len(analyzer.graph)+1)
count = 0 
for chain in chains:
    print(chain)
    if count >50:
        break
    count+=1
len(chains)

# region 以下是需要执行两遍的代码，两个chains分别执行一遍，并记得更改最终形成的json文件名
# for chain in chains:
#     print([f"{rel.from_co.id}→{rel.to_co.id}" for rel in chain])

 

# 验证供应链路径 -------------------------------------------------

 #接下来的步骤：
'''
解析路径字符串：

1.提取初始节点、后续节点链和最终状态。
使用正则表达式分离节点状态和最终状态。
数据清洗与处理：

2.去除多余空格，统一箭头格式。
分割节点链并解析每个节点的名称和状态。
存储到数据结构：

3.按初始节点分类，将路径信息添加到对应的列表中。 
'''

print("\n【完全供应链路径】")

# for i, chain in enumerate(chains):
#     # print(chain)
#     for rel in chain:
#         # print(type(rel))
#region 废弃部分 下方代码二合一了
# def find_path (chains):
#     all_paths = []
#     count = 0
#     for i, chain in enumerate(chains, 1):
#         path = []
#         end_str = []
#         if chain[-1].end <= analyzer.end_date:
#             #产业链最后结束时间在贸易战冲击以内，记为限定日期内断裂
#             end_str.append('limit_day_break')
#         else:
#             #产业链最后结束时间在贸易战冲击以外，记为超限定日期持续性产业链 ，标记为该状态后需要进一步检验该产业链内部状态
#             end_str.append('beyond_day_continue' )
#         for r,rel in enumerate(chain):
#             path.append(f"{rel.from_co.id}→"f"{rel.to_co.id}({rel.status})")
#         all_paths.append(f"{" → ".join(path)}[{end_str[0]}]")
#         # print(f'已解决{count+1}')
#         count+=1
#     return all_paths
# all_chains = find_path(chains)

# len(all_chains)
# # all_chains


# import re

# def parse_paths(path_lines):
#     data = {}
#     for line in path_lines:
#         # 分离最终状态和节点链
#         final_status_match = re.search(r'\[([^\]]+)\]$', line)
#         final_status = final_status_match.group(1) if final_status_match else None
#         nodes_part = line[:final_status_match.start()].strip() if final_status_match else line.strip()
        
#         # 清洗节点链：统一箭头格式
#         nodes_part = re.sub(r'\s*→\s*', '→', nodes_part)
#         nodes = nodes_part.split('→')
#         if not nodes:
#             continue
        
#         initial_node = nodes[0].strip()
#         subsequent_nodes = []
#         for node_str in nodes[1:]:
#             node_str = node_str.strip()
#             # 解析节点名称、状态和时间参数
#             match = re.match(r'^([^(]+)\(([^)]+)\)$', node_str)
#             if match:
#                 name, status = match.groups()
#             else:
#                 name, status = node_str, None
#             subsequent_nodes.append({"name": name, "status": status})
        
#         # 存入数据结构
#         if initial_node not in data:
#             data[initial_node] = []
#         data[initial_node].append({
#             "path": subsequent_nodes,
#             "final_status": final_status
#         })
#     return data
#endregion 废弃部分 下方代码二合一了

def find_path(chains, end_date):
    data = {}
    for chain in chains:
        path_nodes = []
        initial_node = None
        path_start_dt = None  # 保留datetime用于初始时间记录
        path_end_dt = None    # 保留datetime用于最终状态判断
        
        for rel in chain:
            # 初始化起始节点（仅在第一次循环执行）
            if not initial_node:
                initial_node = rel.from_co.id
                path_start_dt = rel.start  # 保持datetime类型用于后续格式转换
            
            # 构建带字符串时间戳的节点信息
            node = {
                "name": rel.to_co.id,
                "status": rel.status,
                "start": rel.start.isoformat() if rel.start else None,  # 转换为ISO字符串
                "end": rel.end.isoformat() if rel.end else None         # 转换为ISO字符串
            }
            path_nodes.append(node)
            path_end_dt = rel.end  # 持续更新为datetime类型
            
        # 最终状态判断（使用未转换的datetime进行比较）
        final_status = 'limit_day_break' if path_end_dt <= end_date else 'beyond_day_continue'
        
        # 组装带字符串时间戳的路径信息
        if initial_node not in data:
            data[initial_node] = []
            
        data[initial_node].append({
            "path": path_nodes,
            "final_status": final_status,
            "start_time": path_start_dt.isoformat() if path_start_dt else None,  # 转换初始时间
            "end_time": path_end_dt.isoformat() if path_end_dt else None         # 转换结束时间
        })
    
    return data

# 解析并存储数据

parsed_data = find_path(chains,analyzer.end_date)
len(parsed_data)
# 示例输出查看

# # 数据结构测试
# count = 0
# for key,value in parsed_data.items():
#     print(key)
#     # print(value)
#     for rel in value:
#     #     # print(f"链条情况: {rel}")
#         print(f'{rel}')
    
#     if count>1:
#         break
#     count+=1

# 保存文件
with open(path_dic['middle'] + '\\' +'complete_supply_chains.json', 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, indent=2, ensure_ascii=False)
# with open(path_dic['middle'] + '\\' +'complete_supply_chains_1.json', 'w', encoding='utf-8') as f:
#     json.dump(parsed_data, f, indent=2, ensure_ascii=False)
# with open(path_dic['middle'] + '\\' +'complete_supply_chains_2.json', 'w', encoding='utf-8') as f:
#     json.dump(parsed_data, f, indent=2, ensure_ascii=False)
# with open(path_dic['middle'] + '\\' +'complete_supply_chains_3.json', 'w', encoding='utf-8') as f:
#     json.dump(parsed_data, f, indent=2, ensure_ascii=False)


# region数据结构片段解释：
'''
	{
  "S1": [
    {
      "path": [
        {
          "name": "C4", 
          "status": "permanent_break",
          "start_time": "2023-01-01",
          "end": "2023-12-31"
        },
        {
          "name": "C5",
          "status": None,
          "start": None,
          "end": None
        },
        {
          "name": "C6",
          "status": "transfer",
          "start": "2024-01-01",
          "end": "2024-12-31"
        }
      ],
      "final_status": "limit_day_break",
      "start_time": "2023-01-01",
      "end_time": "2025-01-01"
    }
  ]
}
'''

#endregion数据结构片段解释


#endregion 以下是需要执行两遍的代码，两个chains分别执行一遍，并记得更改最终形成的json文件名

#endregion 供应链长链建立

# # region 存储数据的读取和后续查询操作原理
# import json
# ################################################## 读取JSON文件

# with open(path_dic['middle'] + '\\' + 'company.json', 'r') as f:
#     loaded_company_data = json.load(f)

# #重建company对象
# companies = dict()
# count = 0
# for cop in loaded_company_data:
#     companies[cop['id']] = Company(cop['id'],cop['country'],cop['listed'])
#     # print(f'已解决{count+1}')
#     count+=1


# # 读取数据
# with open(path_dic['middle'] + '\\' +'complete_supply_chains.json', encoding='utf-8') as f:
#     loaded_data = json.load(f)

# # 数据结构测试
# count = 0
# for key,value in loaded_data.items():
#     print(key)
#     for rel in value:
#         # print(f"链条情况: {rel}")
#         print(f'具体链条情况：{rel}')
#     if count>1:
#         break
#     count+=1




# # 1. 获取所有初始节点
# initial_nodes = list(loaded_data.keys())
# # print("所有初始节点:", initial_nodes)
 
# # 2. 获取指定初始节点的所有路径
# def get_paths_by_initial(initial_node):
#     return loaded_data.get(initial_node, [])
 
# s3_paths = get_paths_by_initial('117591775')
# s3_paths
# len(s3_paths)
# #输出结果演示，如何读取相应的内容
# for path in s3_paths:
#     print(path['path'])
#     print([dic['name'] for dic in path['path']])
#     print(f"路径长度：{len(path['path'])}，最终状态：{path['final_status']}")

# # 3. 查找包含特定节点的路径
# def find_paths_containing_node(target_node):
#     results = []
#     for initial, paths in loaded_data.items():
#         for chain in paths:
#             nodes_in_chain = [node['name'] for node in chain['path']]
#             if target_node in nodes_in_chain:
#                 results.append({
#                     "initial": initial,
#                     "path": chain['path'],
#                     "final_status": chain['final_status']
#                 })
#     return results
 
# c4_paths = find_paths_containing_node('117591775')
# c4_paths
# print(f"找到 {len(c4_paths)} 条包含 117591775 的路径")


# 	# 4. 查找特定状态模式的路径

# def find_by_status(data,pattern):
#     count=0
#     find_path = []
#     for initial_node,chains in data.items():
#         initial_list = []
#         initial_list.append(initial_node)
#         for chain in chains:
#             flag = False
        
#             path = chain['path'] 
#             for node in path:
#                 if node['status'] == pattern:
#                     initial_list.append(chain)
#                     flag = True 
#                     count+=1
#                     break
#             if flag:
#                 count-=1
#                 break

#         find_path.append(initial_list)
#     print(f'count:{count}')
#     return find_path

# len(loaded_data)
# limit_paths = find_by_status(loaded_data,'permanent_break')

# count=0
# for path in limit_paths:
#     print(path)
#     if count>50:
#         break
#     count+=1

# print(f"找到 {len(limit_paths)} 条包含路径")
 
# #endregion 存储数据的读取和后续查询操作原理