
# region ######################################################  开始必备执行代码   
import os
import re

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
# region 数据读取与加载
import json
import plotly.graph_objects as go

with open(path_dic['middle'] + '\\' + 'company.json', 'r') as f:
    loaded_company_data = json.load(f)
# with open(r'C:\Users\32915\Desktop\研创文件\company.json', 'r') as f:
#     loaded_company_data = json.load(f)

#重建company对象
companies = dict()
count = 0
for cop in loaded_company_data:
    companies[cop['id']] = Company(cop['id'],cop['country'],cop['listed'])
    # print(f'已解决{count+1}')
    count+=1

# 公司-国家映射表（用于后续路径分析）
company_to_country = dict()
for company,info in companies.items():
    company_to_country[company] = info.country
    


# # 读取数据（需要替换为实际路径）
# with open(r'C:\Users\32915\Desktop\研创文件\complete_supply_chains.json', 'r', encoding='utf-8') as f:
#     loaded_data = json.load(f)

with open(path_dic['middle'] + '\\' + 'complete_supply_chains.json', 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)

path_lines = []

# 遍历每个初始节点（如 S1）
for initial_node, chains in loaded_data.items():
    # 遍历该初始节点下的所有链条
    for chain in chains:
        path_segments = []
        nodes = chain.get('path', [])
        final_status = chain.get('final_status', '')
        
        # 生成初始节点到第一个节点的边（核心新增逻辑）
        if nodes:
            first_node = nodes[0]
            initial_segment = f"{initial_node}→{first_node['name']}"
            # 添加第一个节点的状态
            if first_node.get('status') and str(first_node['status']).lower() != 'none':
                initial_segment += f"({first_node['status']})"
            path_segments.append(initial_segment)
            
            # 生成后续节点间的边
            for i in range(len(nodes)-1):
                source = nodes[i]['name']
                target = nodes[i+1]['name']
                status = nodes[i+1].get('status')
                
                if source == target:  # 过滤自循环边
                    continue
                
                # 构建边描述
                segment = f"{source}→{target}"
                if status and str(status).lower() != 'none':
                    segment += f"({status})"
                path_segments.append(segment)
        
        # 拼接完整路径
        if path_segments:
            full_path = " → ".join(path_segments)
            # 添加最终状态
            if final_status:
                full_path += f"[{final_status}]"
            path_lines.append(full_path)

# 示例输出
for path in path_lines[:10]:
    print(path)

#endregion 数据读取与加载



#region国家地理坐标（经度，纬度）
country_coords = {
    # 主權國家
    "AE": [54.3000, 23.4241],     # 阿联酋
    "AR": [-63.6167, -38.4161],   # 阿根廷
    "AT": [14.5500, 47.5162],     # 奥地利
    "AU": [133.7751, -25.2744],   # 澳大利亚
    "BA": [17.6790, 43.9159],     # 波黑
    "BD": [90.4125, 23.6850],     # 孟加拉国
    "BE": [4.4699, 50.5039],      # 比利时
    "BG": [25.4858, 42.7339],     # 保加利亚
    "BH": [50.5577, 26.0667],     # 巴林
    "BM": [-64.7500, 32.2948],    # 百慕大（英国海外领地）
    "BR": [-51.9253, -14.2350],   # 巴西
    "BS": [-77.3961, 25.0343],    # 巴哈马
    "BW": [24.0000, -22.0000],    # 博茨瓦纳
    "CA": [-106.3468, 56.1304],   # 加拿大
    "CH": [8.2275, 46.8182],      # 瑞士
    "CI": [-5.5471, 7.5400],      # 科特迪瓦
    "CL": [-71.5429, -35.6751],   # 智利
    "CM": [12.3547, 7.3697],      # 喀麦隆
    "CN": [104.1954, 35.8617],    # 中国
    "CO": [-74.2973, 4.5709],     # 哥伦比亚
    "CR": [-83.7534, 9.7489],     # 哥斯达黎加
    "CY": [33.4299, 35.1264],     # 塞浦路斯
    "CZ": [15.4729, 49.8175],     # 捷克
    "DE": [10.4515, 51.1657],     # 德国
    "DK": [9.5018, 56.2639],      # 丹麦
    "EE": [25.0136, 58.5953],     # 爱沙尼亚
    "EG": [30.8025, 26.8206],     # 埃及
    "ES": [-3.7492, 40.4637],     # 西班牙
    "FI": [25.7482, 61.9241],     # 芬兰
    "FO": [-6.9118, 61.8926],     # 法罗群岛（丹麦自治领）
    "FR": [2.2137, 46.2276],      # 法国
    "GA": [11.6094, -0.8037],     # 加蓬
    "GB": [-3.43597, 55.3781],    # 英国
    "GE": [43.3569, 42.3154],     # 格鲁吉亚
    "GH": [-1.0232, 7.9465],      # 加纳
    "GR": [21.8243, 39.0742],     # 希腊
    "HK": [114.1694, 22.3193],    # 中国香港特别行政区
    "HR": [15.2000, 45.1000],     # 克罗地亚
    "HU": [19.5033, 47.1625],     # 匈牙利
    "ID": [113.9213, -0.7893],    # 印度尼西亚
    "IE": [-8.2439, 53.4129],     # 爱尔兰
    "IL": [34.8516, 31.0461],     # 以色列
    "IN": [78.9629, 20.5937],     # 印度
    "IS": [-19.0208, 64.9631],    # 冰岛
    "IT": [12.5674, 41.8719],     # 意大利
    "JP": [138.2529, 36.2048],    # 日本
    "KE": [37.9062, -0.0236],     # 肯尼亚
    "KR": [127.7669, 35.9078],    # 韩国
    "KW": [47.4818, 29.3117],     # 科威特
    "KZ": [66.9237, 48.0196],     # 哈萨克斯坦
    "LB": [35.8623, 33.8547],     # 黎巴嫩
    "LK": [80.7718, 7.8731],      # 斯里兰卡
    "LT": [23.8813, 55.1694],     # 立陶宛
    "LU": [6.1296, 49.8153],      # 卢森堡
    "LV": [24.6032, 56.8796],     # 拉脱维亚
    "MA": [-7.0926, 31.7917],     # 摩洛哥
    "MX": [-102.5528, 23.6345],   # 墨西哥
    "MY": [109.6976, 3.1409],     # 马来西亚
    "NG": [8.6753, 9.0820],       # 尼日利亚
    "NL": [5.2913, 52.1326],      # 荷兰
    "NO": [8.4689, 60.4720],      # 挪威
    "NZ": [174.7762, -40.9006],   # 新西兰
    "OM": [55.9233, 21.4735],     # 阿曼
    "PE": [-75.0152, -9.1899],    # 秘鲁
    "PH": [121.7740, 12.8797],    # 菲律宾
    "PK": [69.3451, 30.3753],     # 巴基斯坦
    "PL": [19.1451, 51.9194],     # 波兰
    "PT": [-8.2245, 39.3999],     # 葡萄牙
    "QA": [51.1839, 25.3548],     # 卡塔尔
    "RO": [24.9668, 45.9432],     # 罗马尼亚
    "RU": [105.3188, 61.5240],    # 俄罗斯
    "SA": [45.0792, 23.8859],     # 沙特阿拉伯
    "SE": [18.6435, 60.1282],     # 瑞典
    "SG": [103.8198, 1.3521],     # 新加坡
    "TH": [100.9925, 15.8700],    # 泰国
    "TR": [35.2433, 38.9637],     # 土耳其
    "TW": [120.9605, 23.6978],    # 中国台湾地区
    "UA": [31.1656, 48.3794],     # 乌克兰
    "US": [-95.7129, 37.0902],    # 美国
    "ZA": [22.9375, -30.5595],    # 南非
    "ZW": [29.1549, -19.0154],    # 津巴布韦

    # 特殊地区
    "GI": [-5.3454, 36.1408],     # 直布罗陀（英国海外领地）
    "GG": [-2.5853, 49.4657],     # 根西岛（英国皇家属地）
    "JE": [-2.1312, 49.2144],     # 泽西岛（英国皇家属地）
    "MO": [113.5439, 22.1987],    # 中国澳门特别行政区
    "PR": [-66.5901, 18.2208],    # 波多黎各（美国自由邦）
    "PS": [35.2332, 31.9522],     # 巴勒斯坦（争议地区）
    "VI": [-64.8963, 18.3358],    # 美属维尔京群岛
    
    # 特殊标记
    "Multi_Nations": None,          # 多国共有区域（需根据具体案例定义）
    "Nation Not_Found": None      # 无法识别的代码
}
#endregion国家地理坐标（经度，纬度）

# region ###################################################### 统计逻辑实现  （更改统计规则从此处入手，或者从数据加载层面入手）
def analyze_paths(path_lines):
    """
    修复版数据分析函数
        供应链状态分析函数（最终版）
    1. 解析路径末尾的final_status
    2. 当final_status为limit_day_break时：
       - 启用新的层级权重系数（1, 0.7, 0.4）
       - 最终权重 = 层级权重 × 0.1
    
    新增规则：
    1. 当且仅当以下两个条件同时满足时应用limit_day_break权重：
       - final_status == 'limit_day_break'
       - 路径最后一个节点状态 != 'permanent_break'
    """
    status_records = {
        'permanent_break': defaultdict(float),
        'transfer': defaultdict(float),
        'recovered': defaultdict(float)
    }

    # 增强正则表达式
    seg_pattern = re.compile(r'(\w+)→(\w+)(?:\((\w+)\))?(?:\[(\w+)\])?')

    for path in path_lines:
        segments = []
        final_status = None
        
        # 分离路径段
        for seg in path.split(' → '):
            if match := seg_pattern.match(seg):
                start, end, status, f_status = match.groups()
                if f_status:
                    final_status = f_status
                segments.append((start, end, status))
        
        # 状态处理逻辑
        current_chain = None
        for idx, (start_comp, end_comp, status) in enumerate(segments):
            start_country = company_to_country.get(start_comp)
            end_country = company_to_country.get(end_comp)
            
            # 必须存在国家映射
            if not all([start_country, end_country]):
                continue
                
            if status == 'permanent_break':
                # 处理CN起始的段，强制创建新层级
                if start_country == 'CN':
                    layer = 1
                    current_chain = {'layer': layer, 'origin': 'CN'}
                elif current_chain and current_chain['origin'] == 'CN':
                    # 非CN段，仅在现有链条中递增层级
                    layer = current_chain['layer'] + 1
                    current_chain['layer'] = layer
                else:
                    continue  # 忽略非CN且无链条的段
                
                # 计算权重
                if start_country == 'CN':
                    is_limit_break = (
                        final_status == 'limit_day_break' and 
                        (idx == len(segments)-1 and segments[-1][2] != 'permanent_break')
                    )
                    layer_weights = {1: 1.0, 2: 0.7, 3: 0.4} if is_limit_break else {1: 1.0, 2: 0.5, 3: 0.1}
                    weight = layer_weights.get(layer, 0) * (0.1 if is_limit_break else 1)
                    
                    key = (start_country, end_country)
                    status_records['permanent_break'][key] += weight
            
            # 处理其他状态
            elif status in ('transfer', 'recovered'):
                if start_country == 'CN':
                    status_records[status][(start_country, end_country)] += 1.0
                current_chain = None

    return status_records

status_data = analyze_paths(path_lines)
count = 0
# 调试：打印前5条记录
for key,value in status_data.items():
    print(key,value)
    count+=1
    if count > 3:
        break


print("\n原始状态数据样本：")
for status in ['permanent_break', 'transfer', 'recovered']:
    print(f"{status}: {list(status_data[status].items())[:3]}")
# endregion



def create_map_figure(status_data, max_line_width=15):
    traces = []
    color_mapping = {
        'permanent_break': 'rgb(230,50,50)',  # 红色
        'transfer': 'rgb(50,180,50)',         # 绿色
        'recovered': 'rgb(255,200,0)'         # 黄色
    }
    valid_countries = {
        k: v for k, v in country_coords.items()
        if k not in ['Multi_Nations', 'Nation Not_Found'] and v is not None
    }
    # 调试：打印有效国家列表
    print(f"有效国家数量：{len(valid_countries)}")
    print("示例国家：", list(valid_countries.keys())[:5])

    # 国家标签层（调整文本尺寸）
    country_trace = go.Scattergeo(
        lon=[c[0] for c in valid_countries.values()],
        lat=[c[1] for c in valid_countries.values()],
        mode='text',
        text=[f"<b>{k}</b>" for k in valid_countries],
        textfont=dict(color='#FFA500', family="Arial Black", size=14),  # 调大字号
        textposition='middle center',
        hoverinfo='none',
        showlegend=False,
        meta={'status': 'base'}
    )
    traces.append(country_trace)

    # 调试：打印状态数据统计
    print("\n状态数据统计：")
    for status in ['permanent_break', 'transfer', 'recovered']:
        print(f"{status}: {len(status_data[status])}条记录")

    # 状态轨迹生成（添加调试信息）
    for status in ['permanent_break', 'transfer', 'recovered']:
        data = status_data[status]
        if not data:
            print(f"{status}无数据")
            continue
            
        max_weight = max(data.values()) if data else 1
        print(f"\n处理{status}，最大权重：{max_weight}")
        
        for i, ((start, end), weight) in enumerate(data.items()):
            # 调试：打印前5条记录
            if i < 5:
                print(f"  {start}→{end} 权重：{weight}")

            # 国家节点过滤（添加调试）
            if start not in valid_countries or end not in valid_countries:
                print(f"过滤无效节点：{start}→{end}")
                continue
                
            # 坐标获取
            start_coord = valid_countries[start]
            end_coord = valid_countries[end]
            
            # 线宽计算（确保最小可见性）
            line_width = (weight / max_weight) * max_line_width
            line_width = max(min(line_width, max_line_width), 2)  # 最小2px
            
            traces.append(go.Scattergeo(
                lon=[start_coord[0], end_coord[0]],
                lat=[start_coord[1], end_coord[1]],
                mode='lines',
                line=dict(width=line_width, color=color_mapping[status], dash='solid'),
                opacity=0.9 if status == 'permanent_break' else 0.7,
                hoverinfo='text',
                hovertext=f"{start}→{end} | 状态：{status} | 权重：{weight:.2f}",
                visible=True,  # 默认全部可见
                meta={'status': status}
            ))

    # # 可视化控制（简化配置）
    geo_config = dict(
        resolution=110,
        showcountries=True,
        countrycolor='rgb(150,150,150)',
        countrywidth=0.5,
        showframe=False,
        projection_type="natural earth",
        projection=dict(
            scale=1.5,  # 放大初始显示比例
        )
    )

    #     # 修改地理参数配置
    # geo_config = dict(
    #     resolution=110,
    #     showcountries=True,
    #     countrycolor='rgb(150,150,150)',
    #     countrywidth=0.5,
    #     showframe=False,
    #     # projection_type="orthographic",  # 改用正交投影
    #     projection_type="natural earth",  # 改用自然地球投影
    #     projection=dict(
    #         scale=1.5,  # 放大初始显示比例
    #         rotation=dict(lon=104, lat=35, roll=0)  # 中心点对准中国
    #     ),
    #     bgcolor='rgba(255,255,255,0.2)',  # 可选：背景透明化
    #     landcolor='rgb(240,240,240)',      # 陆地颜色
    #     lataxis_showgrid=True,             # 显示经纬网格
    #     lonaxis_showgrid=True
    # )
    
    fig = go.Figure(data=traces)
    fig.update_layout(
        geo=geo_config,
        # 标题设置（关键修改）
        title_text='全球供应链状态监控系统',
        title_font=dict(size=24, family='SimHei'),  # 设置字体
        title_x=0.5,  # 水平居中
        title_y=0.95,  # 垂直位置（0-1范围）
        title_xanchor='center',

        updatemenus=[{
            'buttons': [
                dict(label='全部显示', method='update', args=[{"visible": [True]*len(traces)}]),
                *[dict(label=f"仅显示：{status}",
                      method='update',
                      args=[{"visible": [t.meta['status'] == status or t.meta['status'] == 'base' for t in traces]}])
                  for status in color_mapping]
            ],
            'direction': 'down',
            'x': 0.1,
            'y': 1
        }],
        height=1000,  # 调高画布
        width=1600,   # 调宽画布
        margin=dict(l=0, r=0, b=0, t=40),  # 边距最小化
        # 禁用缩放回调（关键！）
        # uirevision='fixed-view'
    )
    return fig

def get_layer(w):
    """权重值转中文层级"""
    if w >= 0.9: return 'Ⅰ级（直接辐射）'
    elif w >= 0.4: return 'Ⅱ级（次级影响）'
    else: return 'Ⅲ级（远端传导）'


# 生成可视化图表
fig = create_map_figure(status_data, max_line_width=15)
fig.show()