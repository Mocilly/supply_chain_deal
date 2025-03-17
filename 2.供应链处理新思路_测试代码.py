# region ######################################################  开始必备执行代码   
import os

import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict
from collections import defaultdict


# pd.options.display.max_rows = 10000  # 终端显示10000行


def Save(fileName,path,df):
    #.将上面的df保存为xlsx表格
    fileName = fileName+'.xlsx'
    savePath = ''.join([path,fileName])
    wr = pd.ExcelWriter(savePath)#输入即将导出数据所在的路径并指定好Excel工作簿的名称
    df.to_excel(wr, index = False)

    wr._save()



# 路径集合#
path_dic = {'foreign_data':r"C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data",
            'cop_data':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\上市公司数据',
            'middle':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\中间文件',
            'save':r'C:/Users/Mocilly/Desktop/研创平台课题项目/数据//',
            }

#endregion 




# region  -----7.1 将新建的断裂指标添加到上市公司数据中_ 新计算方法(关联产业链破裂也算作break计入上市公司)
'''新计算方法说明:
    考虑到上市公司的安全性资金较为充裕，因此在贸易战期间其产业链不太可能会发生断裂。
    因此我们采用一种新的方法来计算成上市公司的产业链断裂。
    我们将非上市公司与上市公司的关联产业链纳入计算，如果关联产业链发生断裂，那么即意味着上市公司受到了贸易战冲击导致的间接产业链断裂效应
'''


#endregion -----7.1 将新建的断裂指标添加到上市公司数据中_ 新计算方法(关联产业链破裂也算作break计入上市公司)


from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from weakref import WeakValueDictionary

class Company:
    """使用单例模式确保公司对象唯一性"""
    _instances = WeakValueDictionary()
    
    def __new__(cls, cid: str, country: str, listed: bool,company_status = ['active']):
        if cid in cls._instances:
            return cls._instances[cid]

        instance = super().__new__(cls)
        instance.id = cid
        instance.country = country
        instance.listed = listed
        instance.status = company_status
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
            print(f'sorted_rels:{sorted_rels}')

            for i in range(len(sorted_rels)-1):
                for r in range(i+1,(len(sorted_rels))):
                        
                    prev = sorted_rels[i]
                    curr = sorted_rels[r]
    
                    gap = curr.start - prev.end
                    pre_transfer_check = prev.from_co.id == curr.from_co.id
                    recover_check = (prev.from_co.id,prev.to_co.id) == (curr.from_co.id,curr.to_co.id)

                    print(f"{prev}:{curr}")
                    print(f'(prev.from_co.id,prev.to_co.id):{(prev.from_co.id,prev.to_co.id)}')
                    print(f'(curr.from_co.id,curr.to_co.id):{(curr.from_co.id,curr.to_co.id)}')
                    print(f'recover_check:{recover_check}')
                    print(f'i:{i}')


                    if recover_check:
                        if gap > self.recovery_period :
                            print(1)
                            
                            prev.status = "permanent_break"
                            print(f'prev.status:{prev.status}')
                            curr.status = "active"  # curr.status remains as active
                            print(f'curr.status:{curr.status}')
                        elif (gap > timedelta(0)) :
                            curr.status = "recovered"
                    elif pre_transfer_check:
                        if gap > timedelta(0):
                            prev.status = "permanent_break"
                            curr.status = 'transfer'

                    print('----------------------------------------')



#深度优先算法无法查找到成圈层状的供应链关系，这是该算法的缺陷所在
    def find_supply_chains(self, 
                        min_length: int = 3,
                        max_depth: int = 20,
        ) -> List[List['SupplyRelation']]:
        
        valid_chains = []
        
        def dfs(current_company: 'Company',
                path: List['SupplyRelation'],
                visited_companies: set['Company'],
                last_end: Optional[datetime] = None):
            
            # 记录所有有效路径（不限制状态）
            if len(path) >= min_length:
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
        for start_company in self.graph:
            # 生成所有初始路径分支
            for initial_rel in self.graph.get(start_company, []):
                dfs(initial_rel.to_co,
                    [initial_rel],
                    {start_company, initial_rel.to_co},
                    initial_rel.end)
        
        return valid_chains


        
    def detect_transfers(self) -> List[Dict]:
        """优化后的产业转移检测"""
        transfers = []
        
        for supplier in self.graph.values():
            sorted_rels = sorted(supplier, key=lambda x: x.start)
            
            for i in range(1, len(sorted_rels)):
                prev = sorted_rels[i-1]
                curr = sorted_rels[i]
                
                # 转移成立条件
                time_condition = curr.start - prev.end > self.recovery_period
                client_change = prev.to_co != curr.to_co
                status_condition = prev.status in ("permanent_break","recovered",'active') #如果前一状态是recovered，那下一节点也可以转移
                print('转移检测')
                print(f"转移检测情况：time_condition:{time_condition} + client_change:{client_change} + status_condition:{status_condition}")
                print(f'间隔时间：{curr.start - prev.end}')
                print(f'前一节点的状态：{prev.status}')
                print(f'现在节点的状态：{curr.status}')
                if time_condition and client_change and status_condition:
                    print('转移成立')
                    prev.status = 'permanent_break'
                    curr.status = 'transfer'
                    transfers.append({
                        'supplier': prev.from_co.id,
                        'from_client': prev.to_co.id,
                        'to_client': curr.to_co.id,
                        'transfer_date': curr.start,
                        'gap_days': (curr.start - prev.end).days
                    })
                    
        return transfers
    


# region 测试数据生成
"""生成包含三种状态场景的测试数据"""
    # 创建公司实例（使用单例模式）
companies = {
    'S1': Company('S1', '中国', listed=True),
    'S2': Company('S2', '美国', listed=False),
    'S3': Company('S3', '美国', listed=False),
    'S4': Company('S4', '美国', listed=False),
    'S5': Company('S5', '美国', listed=False),
    'C1': Company('C1', '日本', listed=True),
    'C2': Company('C2', '德国', listed=False),
    'C3': Company('C3', '韩国', listed=True),
    'C4': Company('C4', '韩国', listed=True),
    'C5': Company('C5', '法国', listed=True),
    'C6': Company('C6', '法国', listed=True),
    'C7': Company('C7', '法国', listed=True),
    'C8': Company('C8', '法国', listed=True),
    'C9': Company('C9', '法国', listed=True),
    'C10': Company('C10', '法国', listed=True),
    'C11': Company('C11', '法国', listed=True),
    'C12': Company('C12', '法国', listed=True),
    'C13': Company('C13', '法国', listed=True),
    'C14': Company('C14', '法国', listed=True),

}



test_relations = [
# 场景1：永久断裂 (间隔120天) - 原有
(companies['S1'], companies['C1'], datetime(2019,1,1), datetime(2019,6,30)),
(companies['S1'], companies['C1'], datetime(2020,1,1), datetime(2020,12,31)),

# 场景2：自动恢复 (间隔30天) - 原有
(companies['S2'], companies['C2'], datetime(2020,3,1), datetime(2020,5,31)),
(companies['S2'], companies['C2'], datetime(2020,7,1), datetime(2020,9,30)),

# 场景3：产业转移 (间隔92天更换客户) - 原有
(companies['S1'], companies['C2'], datetime(2021,1,1), datetime(2021,3,31)),
(companies['S1'], companies['C3'], datetime(2021,7,1), datetime(2021,12,31)),

# 新增场景4：四层供应链断裂（跨3个层级）
# S3→C4→C5→C6 链条断裂
(companies['S3'], companies['C4'], datetime(2020,1,1), datetime(2020,3,31)),
(companies['C4'], companies['C5'], datetime(2020,4,1), datetime(2020,6,30)), 
(companies['C5'], companies['C6'], datetime(2020,9,1), datetime(2020,12,31)),  # 中间层断裂95天

# 新增场景5：五层供应链部分恢复
# S4→C7→C8→C9→C10 混合断裂
(companies['S4'], companies['C7'], datetime(2021,1,1), datetime(2021,4,30)),
(companies['C7'], companies['C8'], datetime(2021,5,1), datetime(2021,7,31)),
(companies['C8'], companies['C9'], datetime(2021,9,1), datetime(2021,11,30)),  # 断裂31天
(companies['C9'], companies['C10'], datetime(2022,1,1), datetime(2022,6,30)),   # 跨年断裂

# 新增场景6：多路径供应链网络
# 同时存在 S5→C11 和 S5→C12 两条支线
(companies['S5'], companies['C11'], datetime(2022,1,1), datetime(2022,3,31)),
(companies['S5'], companies['C12'], datetime(2022,4,1), datetime(2022,6,30)),
(companies['C11'], companies['C13'], datetime(2022,7,1), datetime(2022,9,30)),  # 更换下游客户
(companies['C12'], companies['C14'], datetime(2022,8,1), datetime(2022,12,31))  # 重叠时间测试
]
relations = []
for from_co, to_co, start, end in test_relations:
    relations.append(SupplyRelation(from_co, to_co, start, end))
relations

 # 初始化分析器
analyzer = SupplyChainAnalyzer(relations, recovery_period=90,end_date=datetime(2021,1,1))

# analyzer.graph
for cop, cop_relation in analyzer.graph.items():
        print(f"公司名字：{cop.id}")
        for rel in cop_relation:
            print(f"供应链关系：{rel}")
# transfers = analyzer.detect_transfers()
# transfers = analyzer.detect_transfers()
# transfers
# for t in transfers:
#     print(f"{t['supplier']} 从 {t['from_client']} 转移到 {t['to_client']} "
#             f"(间隔 {t['gap_days']} 天)")


# 查找长度≥2的供应链
chains = analyzer.find_supply_chains(min_length=2)
chains
for chain in chains:
    print([f"{rel.from_co.id}→{rel.to_co.id}" for rel in chain])
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
print("\n【完全供应链路径】")

for i, chain in enumerate(chains):
    print(chain)
    for rel in chain:
        print(type(rel))




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