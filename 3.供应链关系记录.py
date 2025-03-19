# region ######################################################  开始必备执行代码   
import os

import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict
from collections import defaultdict


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




# region 方法，类合集
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from weakref import WeakValueDictionary

class Company:
    """使用单例模式确保公司对象唯一性"""
    _instances = WeakValueDictionary()
    
    def __new__(cls, cid: str, country: str, listed: bool):
        if cid in cls._instances:
            return cls._instances[cid]

        instance = super().__new__(cls)
        instance.id = cid
        instance.country = country
        instance.listed = listed
        cls._instances[cid] = instance
        return instance


class SupplyRelation:
    """增强型供应链关系对象"""
    __slots__ = ['from_co', 'to_co', 'start', 'end', 'status']
    
    def __init__(self, 
                 from_co: Company, 
                 to_co: Company,
                 start: datetime, 
                 end: datetime):
        self.from_co = from_co
        self.to_co = to_co
        self.start = start
        self.end = end
        self.status = "active"  # active/recovered/permanent_break/break/transfer

    def __repr__(self):
        return f"<Relation {self.from_co.id}→{self.to_co.id} ({self.status})>"

class SupplyChainAnalyzer:
    """增强型供应链分析器"""
    def __init__(self, 
                 relations: List[SupplyRelation],
                 recovery_period: int = 90,
                 end_date=datetime(2021,1,20)):
        
        self.end_date = end_date
        self.recovery_period = timedelta(days=recovery_period)
        self.relations = relations
        self.graph = self._build_graph()
        self._analyze_relations()
    
    def _build_graph(self) -> Dict[Company, List[SupplyRelation]]:
        """构建带状态的时序关系图"""
        graph = defaultdict(list)
        for rel in self.relations:
            graph[rel.from_co].append(rel)
        return graph

    def _analyze_relations(self,end_date:datetime = datetime(2021,1,20)):
        """分析关系状态（核心逻辑优化）"""
        # 按供应商分组分析
        supplier_groups = defaultdict(list)
        for rel in self.relations:
            key = rel.from_co.id
            supplier_groups[key].append(rel)
             # 分析每组关系
        # print(f'supplier_groups:{supplier_groups}')
        for fid, relations in supplier_groups.items():
            sorted_rels = sorted(relations, key=lambda x: x.start)
            # print(f'sorted_rels:{sorted_rels}')

            for i in range(len(sorted_rels)-1):
                for r in range(i+1,(len(sorted_rels))):
                        
                    prev = sorted_rels[i]
                    curr = sorted_rels[r]
    
                    gap = curr.start - prev.end
                    pre_transfer_check = prev.from_co.id == curr.from_co.id
                    recover_check = (prev.from_co.id,prev.to_co.id) == (curr.from_co.id,curr.to_co.id)

                    # print(f"{prev}:{curr}")
                    # print(f'(prev.from_co.id,prev.to_co.id):{(prev.from_co.id,prev.to_co.id)}')
                    # print(f'(curr.from_co.id,curr.to_co.id):{(curr.from_co.id,curr.to_co.id)}')
                    # print(f'recover_check:{recover_check}')
                    # print(f'i:{i}')


                    if recover_check:
                        if gap > self.recovery_period :
                            # print(1)
                            
                            prev.status = "permanent_break"
                            # print(f'prev.status:{prev.status}')
                            curr.status = "active"  # curr.status remains as active
                            # print(f'curr.status:{curr.status}')
                        elif (gap > timedelta(0)) :
                            curr.status = "recovered"
                    elif pre_transfer_check:
                        if gap > timedelta(0):
                            prev.status = "permanent_break"
                            curr.status = 'transfer'

                    # print('----------------------------------------')



#深度优先算法无法查找到成圈层状的供应链关系，这是该算法的缺陷所在
    def find_supply_chains(self, 
                        min_length: int = 3,
                        max_depth: int = 20,
                        start_index:int = 0,
                        end_index: int = 100,
        ) -> List[List['SupplyRelation']]:
        
        valid_chains = []
        
        def dfs(current_company: 'Company',
                path: List['SupplyRelation'],
                visited_companies: set['Company'],
                last_end: Optional[datetime] = None):
            
            # 记录所有有效路径（不限制状态）
            if len(path) >= min_length:
                country_check = False
                for rel in path:
                    contains_cn = (rel.from_co.country == 'CN') or (rel.to_co.country == 'CN')
                    if  contains_cn:
                        country_check = True
                if country_check:
                    valid_chains.append(path.copy())
            
            if len(path) >= max_depth:
                return
            
            for rel in self.graph.get(current_company, []):
                # 时间连续性验证（允许当天接续）
                #举例：现已计入链条长度为2的初始公司下的第一个节点，时间连续性检验的是依照第一个节点公司的relation里面的开始时间是否在初始
                #该改良后的dfs算法旨在列出尽可能多的供应链关系已提供给后续检验供应链是否存在其中存在断裂
                time_valid = last_end is None or rel.start >= last_end 
                
                # 循环检测（防止同一公司重复出现）
                cycle_detected = rel.to_co in visited_companies
                
                if time_valid and not cycle_detected:
                    # 优化时间传递逻辑
                    new_last_end = max(last_end, rel.end) if last_end else rel.end
                    
                    dfs(rel.to_co,
                        path + [rel],
                        visited_companies | {rel.to_co},  # 使用集合合并避免修改原集合
                        new_last_end)
        # 遍历所有可能的起始点
        count = 0
        for start_company in self.graph:
            internal_check = (count>= start_index) and (count < end_index)
            #增加初始节点为中国公司的检验
            is_cn = start_company.country == 'CN'
            if not internal_check or not is_cn:
                count+=1
                print(f'已跳过第{count+1}个')
                continue
            # 生成所有初始路径分支
            for initial_rel in self.graph.get(start_company, []):
                dfs(initial_rel.to_co,
                    [initial_rel],
                    {start_company, initial_rel.to_co},
                    initial_rel.end)
            print(f'已解决第{count+1}个')
            count+=1
        return valid_chains 




    # def detect_transfers(self) -> List[Dict]:
    #     """优化后的产业转移检测"""
    #     transfers = []
        
    #     for supplier in self.graph.values():
    #         sorted_rels = sorted(supplier, key=lambda x: x.start)
            
    #         for i in range(1, len(sorted_rels)):
    #             prev = sorted_rels[i-1]
    #             curr = sorted_rels[i]
                
    #             # 转移成立条件
    #             time_condition = curr.start - prev.end > self.recovery_period
    #             client_change = prev.to_co != curr.to_co
    #             status_condition = prev.status in ("permanent_break","recovered",'active') #如果前一状态是recovered，那下一节点也可以转移
    #             # print('转移检测')
    #             # print(f"转移检测情况：time_condition:{time_condition} + client_change:{client_change} + status_condition:{status_condition}")
    #             # print(f'间隔时间：{curr.start - prev.end}')
    #             # print(f'前一节点的状态：{prev.status}')
    #             # print(f'现在节点的状态：{curr.status}')
    #             if time_condition and client_change and status_condition:
    #                 # print('转移成立')
    #                 prev.status = 'permanent_break'
    #                 curr.status = 'transfer'
    #                 transfers.append({
    #                     'supplier': prev.from_co.id,
    #                     'from_client': prev.to_co.id,
    #                     'to_client': curr.to_co.id,
    #                     'transfer_date': curr.start,
    #                     'gap_days': (curr.start - prev.end).days
    #                 })
                    
    #     return transfers
    
#endregion 方法，类合集

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


source_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_sc.index:
    source_cop_set.add(df_sc.loc[i,'source_company_id'])
    print(f'已解决{i+1}')

#这里还是要记录一下home_region和country不一样的公司，记为Multi_Nations

df_sc['source_company_belong'] = None
df_sc.columns
df_cop.columns
for i,cop in enumerate(source_cop_set):
    
    condition_cop = (df_cop['id'] == cop)
    condition_sc = (df_sc['source_company_id'] == cop)
    df = df_cop[condition_cop]
    df_sc_index_list = df_sc[condition_sc].index

    column_set_1 = set(df["home_region"].dropna())
    column_set_2 = set(df["country"].dropna())
    column_set = column_set_1 | column_set_2
    sc_status = []
    if len(column_set) == 1:
        sc_status.append(column_set.pop())
    elif len(column_set) > 1:
        sc_status.append('Multi_Nations')
    elif len(column_set) < 1:
        sc_status.append('Nation_Not_Found')

    for r in df_sc_index_list:
        df_sc.loc[r,'source_company_belong'] = sc_status[0]
    
    print(f'已解决{i+1}/{len(source_cop_set)}')

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
    sc_status = []
    if len(column_set) == 1:
        sc_status.append(column_set.pop())
    elif len(column_set) > 1:
        sc_status.append('Multi_Nations')
    elif len(column_set) < 1:
        sc_status.append('Nation_Not_Found')

    for r in df_sc_index_list:
        df_sc.loc[r,'target_company_belong'] = sc_status[0]
    
    print(f'已解决{i+1}/{len(target_cop_set)}')

df_sc[df_sc['source_company_belong'].isna()]
print(df_sc['end_'].head())  # 查看前几行数据
print(df_sc['end_'].apply(type).value_counts())  # 统计元素类型
df_sc[df_sc['end_'].isna()]
Save('8.新算法_添加所属国家后的供应链关系表','xlsx',path_dic['save'],df_sc)

#获取供应链表
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[7]
df_sc = pd.read_excel(files[7],dtype={'source_company_id':str,'target_company_id':str,
                                              'SOURCE_ticker':str,'TARGET_ticker':str}) 
# df_sc = pd.read_excel(r'C:\Users\32915\Desktop\8.新算法_添加所属国家后的供应链关系表.xlsx',
#                       dtype={'source_company_id':str,'target_company_id':str,
#                                               'SOURCE_ticker':str,'TARGET_ticker':str}) 



# Pandas 的 Timestamp 使用 64 位整数 存储纳秒级时间戳（从 1970 年 1 月 1 日起算），
# 其最大日期范围约为 公元 1677 年到 2262 年。
# 当代码中使用了超出此范围的日期（如 4000-01-01），尝试将其转换为纳秒时会触发整数溢出（OverflowError），
# 最终导致 OutOfBoundsDatetime 错误。
MAX_PANDAS_DATE = pd.Timestamp.max  # This is 2262-04-11
for i in df_sc.index:
    end_time = df_sc.loc[i,'end_']
    if end_time > datetime(2025,1,1):
        df_sc.loc[i,'end_'] = datetime(2025,1,1)
    print(f'已解决{i+1}/{len(df_sc.index)}')

df_sc[df_sc['end_'] >= datetime(2025,1,1)]



source_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_sc.index:
    source_cop_set.add(df_sc.loc[i,'source_company_id'])
    print(f'已解决{i+1}')

companies = dict()
company_set = set()
for i,cop in enumerate(source_cop_set):
    company_in_set = cop in company_set
    if not company_in_set:
        condition = (df_sc["source_company_id"] == cop)
        subset = df_sc.loc[condition]
        #此处没有做公司可能退市的处理，如果上市则将其标记为上市公司，记为True
        is_all_na = subset["SOURCE_ticker"].isna().all() 
        source_country = set(subset["source_company_belong"].dropna()).pop()
        companies[cop] = Company(cop,source_country,not is_all_na)
    print(f'已解决{i+1}/{len(source_cop_set)}')

for i in df_sc.index:
    cop = df_sc.loc[i,'target_company_id']
    company_in_set = cop in company_set
    if not company_in_set:
        target_country = df_sc.loc[i,'target_company_belong']
        has_ticker = not pd.isna(df_sc.loc[i, 'TARGET_ticker'])
        companies[cop] = Company(cop,target_country,has_ticker)
    print(f'已解决{i+1}/{len(df_sc.index)}')


sample_relations = []
for i in df_sc.index:
    source_cop =  df_sc.loc[i,'source_company_id']
    target_cop = df_sc.loc[i,'target_company_id']
    start_time = df_sc.loc[i,'start_']
    end_time = df_sc.loc[i,'end_']
    sample_relations.append((companies[source_cop],companies[target_cop],start_time,end_time))
    print(f'已解决{i+1}/{len(df_sc.index)}')






relations = []
count = 0
len_sample_relations = len(sample_relations)
for from_co, to_co, start, end in sample_relations:
    relations.append(SupplyRelation(from_co, to_co, start, end))
    print(f'已解决{count+1}/{len_sample_relations}')
    count+=1





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
with open(path_dic['save'] + 'company.json', 'w') as f:
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
with open(path_dic['save'] + 'supply_relations.json', 'w') as f:
    json.dump(data_to_save, f, indent=4)
print("数据已保存至 supply_relations.json")





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



 # 初始化分析器
analyzer = SupplyChainAnalyzer(restored_relations, recovery_period=90,end_date=datetime(2021,1,1))
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
chains = analyzer.find_supply_chains(min_length=1,max_depth=6,start_index=0,end_index=len(analyzer.graph))
chains
len(chains)
# for chain in chains:
#     print([f"{rel.from_co.id}→{rel.to_co.id}" for rel in chain])
# endregion
 



# for rel in relations:
#     status_map = {rel: rel.status}
#     for rel, status in status_map.items():
#         print(f"{rel.from_co.id}→{rel.to_co.id} {rel.start.date()}--{rel.end.date()}: {status}")
#     print("\n【产业转移检测】")
#     transfers = analyzer.detect_transfers()
#     for t in transfers:
#         print(f"{t['supplier']} 从 {t['from_client']} 转移到 {t['to_client']} "
#               f"(间隔 {t['gap_days']} 天)")

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

for i, chain in enumerate(chains):
    print(chain)
    for rel in chain:
        print(type(rel))

def find_path (chains):
    all_paths = []
    for i, chain in enumerate(chains, 1):
        path = []
        end_str = []
        if chain[-1].end <= analyzer.end_date:
            #产业链最后结束时间在贸易战冲击以内，记为限定日期内断裂
            end_str.append('limit_day_break')
        else:
            #产业链最后结束时间在贸易战冲击以外，记为超限定日期持续性产业链 ，标记为该状态后需要进一步检验该产业链内部状态
            end_str.append('beyond_day_continue' )
        for r,rel in enumerate(chain):
            path.append(f"{rel.from_co.id}→"f"{rel.to_co.id}({rel.status})")
        all_paths.append(f"{" → ".join(path)}[{end_str[0]}]")

    return all_paths
all_chains = find_path(chains)
all_chains


import re

def parse_paths(path_lines):
    data = {}
    for line in path_lines:
        
        # 分离最终状态和节点链
        final_status_match = re.search(r'\[([^\]]+)\]$', line)
        final_status = final_status_match.group(1) if final_status_match else None
        nodes_part = line[:final_status_match.start()].strip() if final_status_match else line.strip()
        
        # 清洗节点链：统一箭头格式
        nodes_part = re.sub(r'\s*→\s*', '→', nodes_part)
        nodes = nodes_part.split('→')
        if not nodes:
            continue
        
        initial_node = nodes[0].strip()
        subsequent_nodes = []
        for node_str in nodes[1:]:
            node_str = node_str.strip()
            # 解析节点名称和状态
            match = re.match(r'^([^(]+)\(([^)]+)\)$', node_str)
            if match:
                name, status = match.groups()
            else:
                name, status = node_str, None
            subsequent_nodes.append({"name": name, "status": status})
        
        # 存入数据结构
        if initial_node not in data:
            data[initial_node] = []
        data[initial_node].append({
            "path": subsequent_nodes,
            "final_status": final_status
        })
    return data


# 解析并存储数据
parsed_data = parse_paths(all_chains)

# 示例输出查看
import json
print(json.dumps(parsed_data, indent=2, ensure_ascii=False))


# 保存文件
with open(path_dic['save'] + 'supply_chains.json', 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, indent=2, ensure_ascii=False)
 
# 读取数据
with open(path_dic['save'] + 'supply_chains.json', encoding='utf-8') as f:
    loaded_data = json.load(f)


# 1. 获取所有初始节点
initial_nodes = list(loaded_data.keys())
print("所有初始节点:", initial_nodes)
 
# 2. 获取指定初始节点的所有路径
def get_paths_by_initial(initial_node):
    return loaded_data.get(initial_node, [])
 
s3_paths = get_paths_by_initial('S3')

#输出结果演示，如何读取相应的内容
for path in s3_paths:
    print(path['path'])
    print([dic['name'] for dic in path['path']])
    print(f"路径长度：{len(path['path'])}，最终状态：{path['final_status']}")

# 3. 查找包含特定节点的路径
def find_paths_containing_node(target_node):
    results = []
    for initial, paths in loaded_data.items():
        for path in paths:
            nodes_in_path = [node['name'] for node in path['path']]
            if target_node in nodes_in_path:
                results.append({
                    "initial": initial,
                    "path": path['path'],
                    "final_status": path['final_status']
                })
    return results
 
c4_paths = find_paths_containing_node('C4')
c4_paths
print(f"找到 {len(c4_paths)} 条包含 C4 的路径")


	# 4. 查找特定状态模式的路径
def find_by_status(pattern):
    return [path for paths in loaded_data.values() for path in paths 
            if re.search(pattern, path['final_status'])]
 
limit_paths = find_by_status(r'limit_day')
print(f"找到 {len(limit_paths)} 条限制类路径")
 
# 5. 可视化路径关系
import networkx as nx
import matplotlib.pyplot as plt
 
def visualize_paths(initial_node):
    G = nx.DiGraph()
    paths = get_paths_by_initial(initial_node)
    
    for path in paths:
        nodes = [initial_node] + [n['name'] for n in path['path']]
        for i in range(len(nodes)-1):
            G.add_edge(nodes[i], nodes[i+1])
    
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue')
    plt.title(f"{initial_node} 的产业链关系")
    plt.show()
 
visualize_paths('S3')