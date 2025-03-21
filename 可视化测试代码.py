
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



import json
import plotly.graph_objects as go

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

# 转换数据结构：生成类似 path_lines 的供应链路径描述
path_lines = []
 
# 遍历每个初始节点（例如 S1, S2, S3）
for initial_node, chains in loaded_data.items():
    # 遍历该初始节点下的所有供应链链条
    for chain in chains:
        path_segments = []
        nodes = chain.get('path', [])
        final_status = chain.get('final_status', '')
        # 遍历节点，生成连续的边（source→target）
        for i in range(len(nodes) - 1):
            source = nodes[i]['name']
            target = nodes[i + 1]['name']
            status = nodes[i + 1]['status']  # 使用目标节点的状态作为边的状态
            # 关键改进：过滤 source == target 的边
            if source == target:
                continue  # 跳过两端相同的边
            # 处理状态显示逻辑
            if status and status.lower() != 'none':
                segment = f"{source}→{target}({status})"
            else:
                segment = f"{source}→{target}"
            
            path_segments.append(segment)
        # 添加最终状态（可选）
        # if final_status:
        #     path_segments.append(f"[最终状态: {final_status}]")
        
        # 拼接完整路径
        if path_segments:
            full_path = " → ".join(path_segments)
            path_lines.append(full_path)




# 公司-国家映射表（所有S开头公司属于中国）
company_to_country = {
    **{f"S{i}": "China" for i in range(1,4)},  # S1-S3均来自中国
    "C1": "USA", "C2": "Germany", "C3": "Japan",
    "C4": "India", "C5": "France", "C6": "UK"
}

# 国家地理坐标（经度，纬度）
country_coords = {
    "China": [104.1954, 35.8617],
    "USA": [-95.7129, 37.0902],
    "Germany": [10.4515, 51.1657],
    "Japan": [138.2529, 36.2048],
    "India": [78.9629, 20.5937],
    "France": [2.2137, 46.2276],
    "UK": [-3.43597, 55.3781],

}

# region ###################################################### 统计逻辑实现
def analyze_paths(path_lines):
    """
    供应链状态分析函数
    
    功能：
    1. 永久断裂(permanent_break)处理逻辑：
       - 跟踪从中国开始的连续断裂链条
       - 按层级加权（第1层x1，第2层x0.5，第3层x0.1）
    2. 转移(transfer)/恢复(recovered)处理逻辑：
       - 仅统计中国直接发起的单个状态变化
    """
    status_records = {
        'permanent_break': defaultdict(float),
        'transfer': defaultdict(float),
        'recovered': defaultdict(float)
    }

    for path in path_lines:
        # 分解路径为独立段（忽略时间标记）
        segments = []
        for seg in path.split(' → '):
            if match := re.match(r'(\w+)→(\w+)\((\w+)\)', seg.split('[')[0]):
                segments.append(match.groups())

        current_chain = None  # 跟踪当前断裂链条状态

        for start_comp, end_comp, status in segments:
            start_country = company_to_country.get(start_comp)
            end_country = company_to_country.get(end_comp)
            
            # 处理永久断裂状态
            if status == 'permanent_break':
                if current_chain:  # 延续现有链条
                    layer = current_chain['layer'] + 1
                    weight = 1.0 if layer == 1 else 0.5 if layer == 2 else 0.1
                    current_chain['layer'] = layer
                else:  # 新链条必须起始于中国
                    if start_country == 'China':
                        layer = 1
                        weight = 1.0
                        current_chain = {'layer': layer}
                    else:
                        continue  # 非中国起始的断裂不统计
                
                # 记录国家间断裂关系及加权值
                status_records['permanent_break'][(start_country, end_country)] += weight
            
            # 处理转移/恢复状态（仅中国直接发起）
            elif start_country == 'China':
                if status == 'transfer':
                    status_records['transfer'][(start_country, end_country)] += 1.0
                elif status == 'recovered':
                    status_records['recovered'][(start_country, end_country)] += 1.0
                
                # 状态变化中断永久断裂链条
                current_chain = None
            
            # 非永久断裂状态中断链条
            else:
                current_chain = None

    return status_records

status_data = analyze_paths(path_lines)
# endregion

# endregion
# endregion
def create_map_figure(status_data):
    traces = []
    max_line_width = 15
    color_mapping = {
        'permanent_break': 'rgb(230,50,50)',
        'transfer': 'rgb(50,180,50)',
        'recovered': 'rgb(50,50,230)'
    }
	  # 修正后的国家标签配置
    country_trace = go.Scattergeo(
        lon=[c[0] for c in country_coords.values()],
        lat=[c[1] for c in country_coords.values()],
        mode='text',
        text=[f"<b>{k}</b>" for k in country_coords],
        textfont=dict(
            color='#FFA500',
            family="Arial Black",
            size=17
        ),
        textposition=[
            # 使用Plotly官方支持的参数值
            'middle right' if country == "China" else      # 中国
            'bottom left' if country == "USA" else       # 美国
            'bottom center' if country == "Germany" else # 德国
            'middle center' if country == "Japan" else        # 日本
            'middle center' if country == "India" else    # 印度（修正这里）
            'middle right' if country == "France" else     # 法国（修正这里）
            'bottom center'                                # 英国
            for country in country_coords
        ],
        hoverinfo='none',
        showlegend=False,
        meta={'status': 'base'}
    )
    traces.append(country_trace)


    # 生成状态轨迹
    for status in ['permanent_break', 'transfer', 'recovered']:
        data = status_data[status]
        if not data:
            continue
            
        max_weight = max(data.values(), default=1)
        
        for (start, end), weight in data.items():
            # 坐标验证
            start_coord = country_coords.get(start, [None, None])
            end_coord = country_coords.get(end, [None, None])
            if None in start_coord + end_coord:
                continue
                
            # 动态线宽
            line_width = (weight / max_weight) * max_line_width
            line_width = max(min(line_width, 15), 1.5)
            
            traces.append(go.Scattergeo(
                lon=[start_coord[0], end_coord[0], None],
                lat=[start_coord[1], end_coord[1], None],
                mode='lines',
                line=dict(
                    width=line_width,
                    color=color_mapping[status],
                    dash='dash' if status == 'permanent_break' else 'solid'
                ),
                opacity=0.85,
                hoverinfo='text',
                hovertext=f"{start}→{end}<br>辐射层级：{get_layer(weight)}<br>权重：{weight:.2f}",
                visible=(status == 'permanent_break'),
                meta={'status': status}
            ))

     # 修正可见性控制逻辑
    buttons = []
    visible_states = ['permanent_break', 'transfer', 'recovered']
    for status in visible_states:
        visible = [
            (t.meta.get('status') == status) if 'meta' in t and t.meta.get('status') != 'base' 
            else True  # 确保国家标签始终可见
            for t in traces
        ]
        buttons.append(dict(
            label=f"{status.capitalize()}状态",
            method='update',
            args=[{'visible': visible}]
        ))
    
    geo_config = dict(
        resolution=50,  # 降低地图分辨率
        showcountries=True,
        countrycolor='rgb(100,100,100)',  # 使用灰色替代纯黑
        countrywidth=0.8,  # 更细的国家边界
        showcoastlines=True,
        coastlinecolor='rgb(80,80,80)',  # 更柔和的颜色
        coastlinewidth=0.1,  # 更细的海岸线
        showlakes=False,  # 隐藏湖泊
        showrivers=False,  # 隐藏河流
        showframe=False,  # 隐藏地图边框
        showsubunits=False, # 关键参数：隐藏次级行政区划（包括小岛）❗
        subunitwidth=0,     # 彻底隐藏次级边界
        landcolor="rgb(245,245,220)",  # 米色陆地
        oceancolor="rgb(173,216,230)",  # 浅蓝色海洋
        projection_type="natural earth"  # 使用简化投影

    )
    
    fig = go.Figure(data=traces)
    fig.update_layout(
        title_text='全球供应链状态分析系统',
        updatemenus=[dict(
            type='dropdown',
            direction='down',
            active=0,
            buttons=buttons,
            x=0.12,
            xanchor='left',
            y=1.15
        )],
        geo=geo_config,
        plot_bgcolor='rgba(255,255,255,0.9)',  # 画布背景色
        height=750,
        margin=dict(l=0, r=0, t=90, b=0)
    )

    return fig


def get_layer(w):
    """权重值转中文层级"""
    if w >= 0.9: return 'Ⅰ级（直接辐射）'
    elif w >= 0.4: return 'Ⅱ级（次级影响）'
    else: return 'Ⅲ级（远端传导）'

    
# 生成可视化图表
fig = create_map_figure(status_data)
fig.show()