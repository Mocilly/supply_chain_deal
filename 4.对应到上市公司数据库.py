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
    # 重写相等性判断
    def __eq__(self, other):
        return (self.from_co == other.from_co and 
                self.to_co == other.to_co and
                self.status == other.status)
    
    # 生成哈希值用于集合去重
    def __hash__(self):
        return hash((self.from_co, self.to_co,self.start,self.end,self.status))

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

    def filter_duplicate_chains(self,chains: List[List[SupplyRelation]]) -> List[List[SupplyRelation]]:
    # 按路径长度降序排列
        sorted_chains = sorted(chains, key=lambda x: len(x), reverse=True)
        
        seen_relations = set()
        filtered_chains = []
        
        for chain in sorted_chains:
            # 提取路径中的所有关系
            relations_in_chain = set(chain)
            
            # 检查是否存在新关系
            if not relations_in_chain.issubset(seen_relations):
                filtered_chains.append(chain)
                seen_relations.update(relations_in_chain)
        
        return filtered_chains



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
            #增加初始节点为中国公司的检验  （为限制关系数量，避免内存超载） (删除测试)
            # is_cn = start_company.country == 'CN'
            # if not internal_check or not is_cn:
            if not internal_check :
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
        return self.filter_duplicate_chains(valid_chains) 

    
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


base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[7]
df_sc = pd.read_excel(files[7],dtype={'source_company_id':str,'target_company_id':str,
                                              'SOURCE_ticker':str,'TARGET_ticker':str}) 

df = df_sc[['source_company_id','target_company_id','SOURCE_ticker','TARGET_ticker']]

# region 存储数据的读取和后续查询操作原理
import json
################################################## 读取JSON文件

with open(path_dic['middle'] + '\\' + 'company.json', 'r') as f:
    loaded_company_data = json.load(f)

#重建company对象
companies = dict()
count = 0
for cop in loaded_company_data:
    companies[cop['id']] = Company(cop['id'],cop['country'],cop['listed'])
    # print(f'已解决{count+1}')
    count+=1


# 读取数据
with open(path_dic['middle'] + '\\' +'complete_supply_chains.json', encoding='utf-8') as f:
    loaded_data = json.load(f)

# 数据结构测试
count = 0
for key,value in loaded_data.items():
    print(key)
    for rel in value:
        # print(f"链条情况: {rel}")
        print(f'具体链条情况：{rel}')
    if count>1:
        break
    count+=1




# 1. 获取所有初始节点
initial_nodes = list(loaded_data.keys())

initial_nodes
len(initial_nodes)
count=0
for node in initial_nodes:
    if companies[node].country == 'CN':
        continue
    else:
        initial_nodes.pop()
len(initial_nodes)

# print("所有初始节点:", initial_nodes)  #警告 此处有着 列表浅引用的陷阱，用dict.fromkeys会导致所有引用转向同一列表
initial_nodes_dict = {key: [False, None] for key in initial_nodes} #第一个参数检验是否断裂，第二个参数检验将股票代码涵盖进去
len(initial_nodes_dict)
# 2. 获取指定初始节点的所有路径
def get_paths_by_initial(initial_node):
    return loaded_data.get(initial_node, [])
s = get_paths_by_initial('3554')
s[23]
#先统计初始节点以外的节点断裂情况
cn_cop = []
for initial_node in initial_nodes:
    chains = get_paths_by_initial(initial_node)
    for chain in chains:
        final_status = chain['final_status']
        path = chain['path']
        
        flag = False
        for i,node in enumerate(path):
            name = node['name']
            if name in initial_nodes_dict:
                cn_cop.append(name)
                flag = True
                if node['status'] == 'permanent_break':  #如果当天节点就是中国公司且状态为断裂，则无需进行后续检查处理，直接下一节点
                    flag = False
                continue
            if flag:
                if node['status'] == 'permanent_break' or final_status == 'limit_day_break':
                    flag = False
                    continue
                elif i == len(path)-1:
                    cn_cop.pop()
cn_cop_break_set = set(cn_cop)

#再统计初始节点断裂情况
for initial_node in initial_nodes:  #逻辑： 有一个产业链断裂就判定为初始节点断裂
    chains = get_paths_by_initial(initial_node)
    for chain in chains:
        final_status = chain['final_status']
        path = chain['path']

        for i,node in enumerate(path):
            if node['status'] == 'permanent_break':
                cn_cop_break_set.add(initial_node)
                break

len(cn_cop_break_set)
for node in list(cn_cop_break_set):
    if node in initial_nodes_dict:
        initial_nodes_dict[node][0] = True

df.columns
initial_nodes_dict
count = 0
len_initial_nodes_dict = len(initial_nodes_dict)
multi_ticker = []
for key,value in initial_nodes_dict.items():
    ticker_set = set()
    # 收集 TARGET_ticker
    target_mask = df['target_company_id'] == key
    if target_mask.any():
        target_tickers = df.loc[target_mask, 'TARGET_ticker'].unique()
        ticker_set.update(target_tickers)
    
    # 收集 SOURCE_ticker
    source_mask = df['source_company_id'] == key
    if source_mask.any():
        source_tickers = df.loc[source_mask, 'SOURCE_ticker'].unique()
        ticker_set.update(source_tickers)
    if len(ticker_set) == 1:
        value[1] = ticker_set.pop()
    else:
        multi_ticker.append([key,list(ticker_set)])
    print(f"已解决{count+1}/{len_initial_nodes_dict}")
    count+=1

initial_nodes_dict

count=0
for key,value in initial_nodes_dict.items():
    # print(value)
    if initial_nodes_dict[key][0] ==False:
        print(key)
        count+=1
        
print(count) 
    









#输出结果演示，如何读取相应的内容
for path in s3_paths:
    print(path['path'])
    print([dic['name'] for dic in path['path']])
    print(f"路径长度：{len(path['path'])}，最终状态：{path['final_status']}")

# 3. 查找包含特定节点的路径
def find_paths_containing_node(target_node):
    results = []
    for initial, paths in loaded_data.items():
        for chain in paths:
            nodes_in_chain = [node['name'] for node in chain['path']]
            if target_node in nodes_in_chain:
                results.append({
                    "initial": initial,
                    "path": chain['path'],
                    "final_status": chain['final_status']
                })
    return results
 
c4_paths = find_paths_containing_node('117591775')
c4_paths
print(f"找到 {len(c4_paths)} 条包含 117591775 的路径")




	# 4. 查找特定状态模式的路径

def find_by_status(data,pattern):
    count=0
    find_path = []
    for initial_node,chains in data.items():
        initial_list = []
        initial_list.append(initial_node)
        for chain in chains:
            flag = False
        
            path = chain['path'] 
            for node in path:
                if node['status'] == pattern:
                    initial_list.append(chain)
                    flag = True 
                    count+=1
                    break
            if flag:
                count-=1
                break

        find_path.append(initial_list)
    print(f'count:{count}')
    return find_path

len(loaded_data)
limit_paths = find_by_status(loaded_data,'permanent_break')

count=0
for path in limit_paths:
    print(path)
    if count>50:
        break
    count+=1

print(f"找到 {len(limit_paths)} 条包含路径")
 
#endregion 存储数据的读取和后续查询操作原理