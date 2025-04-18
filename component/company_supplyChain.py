
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
            
            # 记录所有有效路径（不限制状态），添加中国公司检验
            if len(path) >= min_length:
                country_check = False
                for rel in path:
                    contains_cn = ('CN' in rel.from_co.country ) or ('CN' in rel.to_co.country )
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
