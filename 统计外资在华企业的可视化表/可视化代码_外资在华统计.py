# region ######################################################  开始必备执行代码   
import os
import re

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
path_dic ={'company':r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\company.json',
           'supply_chain': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\supply_relations.json',
           'complete_sc':r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\complete_supply_chains.json',

           }

#endregion 


# region数据结构片段解释：

'''
	{
  "S1": [
    {
      "path": [
        {
          "name": "C4", 
          "status": "permanent_break",
          "start": "2023-01-01",
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


with open(path_dic["company"], 'r') as f:
    loaded_company_data = json.load(f)

#重建company对象
companies = dict()
count = 0
for cop in loaded_company_data:
    companies[cop['id']] = Company(cop['id'],cop['country'],cop['listed'])
    # print(f'已解决{count+1}')
    count+=1

for idx,company in enumerate(companies.values()):
    if idx>= 100:
        break
    print(f'公司ID：{company.id}，国家：{company.country}，上市公司：{company.listed}')


# 公司-国家映射表（用于后续路径分析）
      #新增多国家背景公司计量，将多国家背景公司的所属国家处理为列表

# 用于处理多国家背景公司的国家字符串
def split_countries(country_str: str) -> tuple:
    """智能分割国家字符串，自动检测分隔符"""
    

    # 标准化字符串（去除前后空格）
    normalized = country_str.strip()

    # 空字符串直接返回空元组
    if not normalized:
        return ()
    # 标准化字符串（去除前后空格）
    # 检测分隔符
    home_region = normalized[:normalized.find('&')]
    hr_c = home_region[home_region.find(':')+1:]
    c = normalized[normalized.find('&')+1:]
    country = c[c.find(':')+1:]
    home_region_list = None
    country_list = None
    if '|' in hr_c:
        # 分割并清理元素
        home_region_list = [hr for hr in hr_c.split('|')]

    else:
        # 返回单个国家列表
        home_region_list = [hr_c]
    
    if '|' in country:
        # 分割并清理元素
        country_list = [c for c in country.split('|')]
    else:
        # 返回单个国家列表
        country_list = [country]

    return (home_region_list,country_list)

company_to_country = dict()
for company,info in companies.items():
    company_to_country[company] = split_countries(info.country)
    

for idx,com_country in enumerate(company_to_country.items()):
    if idx>= 100:
        break
    print(f'公司ID：国家 "{com_country}')

# # 读取数据（需要替换为实际路径）
with open(path_dic["complete_sc"], 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)


def parse_date(date_str):
    """解析日期字符串为datetime对象，时间强制为00:00:00，空值返回None"""
    if not date_str:
        return None
    try:
        # 直接解析为datetime，时间部分自动为0
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None



def rebuild_relations(loaded_data:dict)->List[SupplyRelation]:

    """重建供应链关系对象"""
    relations = []
    for initial_node, chains in loaded_data.items():
        #  遍历该初始节点下的所有链条
        for chain in chains:
            nodes = chain.get('path', [])
            final_status = chain.get('final_status', '')
            start_time = parse_date(chain.get('start_time', None))
            end_time = parse_date(chain.get('end_time', None))
            rel = []
  
            #  生成初始节点到第一个节点的边（核心逻辑）
            if nodes:
                first_node = nodes[0]
                # 构建初始关系
                sr =SupplyRelation(companies[initial_node],
                                   companies[first_node['name']],
                                   parse_date(first_node['start']), 
                                   parse_date(first_node['end']),
                                   )
                sr.status = first_node['status']
                rel.append(sr)
                 # 生成后续节点间的供应关系
                for i in range(1,len(nodes)-1,2):
                    from_co = companies[nodes[i]['name']]
                    to_co = companies[nodes[i+1]['name']]
                    start = parse_date(nodes[i+1]['start'])
                    end = parse_date(nodes[i+1]['end'])
                    status = nodes[i+1].get('status')
                    supply_sc = SupplyRelation(from_co, to_co, start, end)
                    supply_sc.status = status
                    rel.append(supply_sc)
                rel.append([final_status,start_time,end_time])
                relations.append(rel)
    return relations

relations = rebuild_relations(loaded_data=loaded_data)

for rel in relations[:10]:
    print(rel)
    rel[:-1]
    for r in rel[:-1]:
        print(f"起始公司：{r.from_co.id}，目标公司：{r.to_co.id}，开始时间：{r.start}，结束时间：{r.end}，状态：{r.status}")
    

len(relations)






def is_relation_valid(relation: SupplyRelation) -> bool:
    """关系有效性验证函数（新增）"""
    def validate_company(company: Company) -> bool:
        """验证单个公司是否符合要求"""
        home_regions, countries = company_to_country.get(company.id, ([], []))
        
        # 条件1：home_region必须包含CN（不区分大小写）
        home_valid = 'CN' in home_regions
        
        # 条件2：countries不能全为CN
        country_valid =  'CN' not in countries or set(countries) != {'CN'}
        
        return home_valid and country_valid

    # 双向验证：起始公司或目标公司任意一方符合条件即可
    return validate_company(relation.from_co) or validate_company(relation.to_co)

def delete_relation(relations: List[List]) -> List[List]:
    """
    增强版供应链关系过滤方法
    逻辑说明：
    1. 遍历每个供应链链条
    2. 对每个链条中的每个supplyrelation进行双向验证：
       - 验证方向：from_co和to_co公司
       - 必须满足：home_region包含CN 且 country不全为CN
    3. 保留条件：链条中存在至少一个有效关系
    4. 删除条件：整条链所有关系均无效
    """
    filtered_chains = []
    
    for chain in relations:
        # 分离关系对象和其他元数据
        relations_in_chain = chain[:-1]
        metadata = chain[-1]
        
        # 有效性验证（至少有一个有效关系）
        keep_chain = any([is_relation_valid(rel) for rel in relations_in_chain])
        
        if keep_chain:
            # 重构链条时保留原始结构
            filtered_chains.append(chain)

    
    return filtered_chains



437641


# 执行过滤
filtered_rel = delete_relation(relations)
print(f"过滤后剩余链条数：{len(filtered_rel)}")

for idx, rel in enumerate(filtered_rel[:10]):
    print(f"链条{idx+1}:")
    print(rel)


def count_chains_with_node(relations, node_code):
    """
    统计链条中带有指定节点的供应链数量
    :param relations: 供应链关系列表
    :param node_code: 指定节点代码（如'HK', 'CN'等）
    :return: 带有指定节点的供应链数量
    """
    count = 0
    for rel in relations:
        for r in rel[:-1]:
            source_country = company_to_country.get(r.from_co.id, [])
            target_country = company_to_country.get(r.to_co.id, [])
            if (node_code in source_country[1] or node_code in target_country[1]):
                count += 1
                break
    return count

# 示例调用
node_code = 'CN'
node_code = 'HK'
count = count_chains_with_node(filtered_rel, node_code)
print(f"链条中带有节点 {node_code} 的供应链数量：{count}")


def generate_path_lines(relations, filter_start, filter_end):
    result = []
    for chain in relations:
        # 分离供应链关系数据 和 供应链状态数据
        supply_chain = [r for r in chain if isinstance(r, SupplyRelation)]
        chain_status = chain[-1]
        
        if not supply_chain or not chain_status:
            continue
            
        final_status = chain_status[0]
        
        # 第一阶段：标记所有有效节点
        valid_indices = [
            i for i, rel in enumerate(supply_chain)
            if rel.start >= filter_start and rel.end <= filter_end
        ]
        
        # 第三阶段：构建输出路径
        if valid_indices:
            rels = []
            for i in valid_indices:
                sc = supply_chain[i]
                single_rel = '→'.join([sc.from_co.id,sc.to_co.id,]) + f'({sc.status})'
                rels.append(single_rel)

            path_str = " → ".join(r for r in rels)
    
            # 判断是否为原链末尾
            if valid_indices[-1] == len(supply_chain) - 1:
                path_str += f"[{final_status}]"
                
            result.append(path_str)
            
    return result

#endregion 数据读取与加载



#region ----------------------------------------两任期数据切换 （重要）----------------------
path_lines_all = generate_path_lines(relations=filtered_rel,
                                       filter_start=datetime(2016,11,9),
                                       filter_end=datetime(2024,12,31))
path_lines = path_lines_all
## 涉及国家对数：permanent_break,transfer，recover = 68,56,20

# path_lines_Trump = generate_path_lines(relations=relations,
#                                        filter_start=datetime(2016,11,9),
#                                        filter_end=datetime(2020,12,14))
# path_lines = path_lines_Trump
## 涉及国家对数：permanent_break,transfer，recover = 57,36,7

# path_lines_Biden = generate_path_lines(relations=relations,
#                                        filter_start=datetime(2020,12,14),
#                                        filter_end=datetime(2024,12,31))
# path_lines = path_lines_Biden
# 涉及国家对数：permanent_break,transfer，recover = 59,53,19


# len(path_lines_Trump)

# for rel in path_lines_Trump[:1000]:
#     print(rel)



len(path_lines)
for rel in path_lines[3000:4000]:
    print(rel)

#endregion -------------------------------------两任期数据切换 （重要）--------------------------




#region国家地理坐标（经度，纬度）
country_coords = {
    # 主權國家
    "CN": [116.4074, 39.9042],    # 中国
    'CN_2':[100.2653, 30.6041], #（中国位置2）
    "AE": [54.3667, 24.4667],     # 阿拉伯联合酋长国
    "AF": [69.2075, 34.5553],     # 阿富汗
    "AL": [19.8190, 41.3275],     # 阿尔巴尼亚
    "AR": [-58.3816, -34.6037],   # 阿根廷
    "AT": [16.3738, 48.2082],     # 奥地利
    "AU": [149.1300, -35.2809],   # 澳大利亚
    "AZ": [49.8920, 40.4093],     # 阿塞拜疆
    "BA": [18.4131, 43.8563],     # 波黑
    "BD": [90.4125, 23.6850],     # 孟加拉国
    "BE": [4.3517, 50.8503],      # 比利时
    "BF": [-1.5197, 12.3681],     # 布基纳法索
    "BG": [23.3241, 42.6977],     # 保加利亚
    "BO": [-68.1193, -16.4897],   # 玻利维亚
    "BR": [-47.9297, -15.7801],   # 巴西
    "CA": [-75.6972, 45.4215],    # 加拿大
    "CD": [15.2662, -4.3224],     # 刚果民主共和国（刚果金）
    "CH": [7.4474, 46.9480],      # 瑞士
    "CL": [-70.6483, -33.4489],   # 智利

    "CO": [-74.0721, 4.7110],     # 哥伦比亚
    "CU": [-82.3666, 23.1136],    # 古巴
    "CZ": [14.4378, 50.0755],     # 捷克
    "DE": [13.4049, 52.5200],     # 德国
    "DK": [12.5683, 55.6761],     # 丹麦
    "DZ": [3.0588, 36.7538],      # 阿尔及利亚
    "EC": [-78.4678, -0.1807],    # 厄瓜多尔
    "EG": [31.2357, 30.0444],     # 埃及
    "ES": [-3.7038, 40.4168],     # 西班牙
    "FI": [24.9384, 60.1699],     # 芬兰
    "FR": [2.3522, 48.8566],      # 法国
    "GB": [-0.1276, 51.5072],     # 英国
    "GE": [44.8271, 41.7151],     # 格鲁吉亚
    "GH": [-0.1866, 5.6037], 
    
         # 加纳
    "GR": [23.7275, 37.9838],     # 希腊
    "GT": [-90.5150, 14.6349],    # 危地马拉
    "HN": [-87.2044, 14.0818],    # 洪都拉斯
    "HR": [16.0015, 45.8150],     # 克罗地亚
    "HU": [19.0402, 47.4979],     # 匈牙利
    "ID": [106.8650, -6.1751],    # 印度尼西亚
    "IE": [-6.2603, 53.3498],     # 爱尔兰
    "IL": [34.7818, 32.0853],     # 以色列
    "IN": [77.2090, 28.6139],     # 印度
    "IQ": [44.3615, 33.3152],     # 伊拉克
    "IR": [51.3890, 35.6892],     # 伊朗
    "IS": [-21.9426, 64.1466],    # 冰岛
    "IT": [12.4964, 41.9028],     # 意大利
    "JM": [-76.7930, 17.9714],    # 牙买加
    "JO": [35.9106, 31.9539],     # 约旦
    "JP": [139.6917, 35.6895],    # 日本
    "KE": [36.8219, -1.2864],     # 肯尼亚
    "KR": [126.9780, 37.5665],    # 韩国
    "KW": [47.9783, 29.3759],     # 科威特
    "KZ": [71.4491, 51.1605],     # 哈萨克斯坦
    "LB": [35.4955, 33.8886],     # 黎巴嫩
    "LK": [79.8612, 6.9271],      # 斯里兰卡
    "MA": [-6.8326, 34.0133],     # 摩洛哥
    "MX": [-99.1332, 19.4326],    # 墨西哥
    "MY": [101.6869, 3.1390],     # 马来西亚
    "NG": [7.4891, 9.0579],       # 尼日利亚
    "NL": [4.8952, 52.3702],      # 荷兰
    "NO": [10.7522, 59.9139],     # 挪威
    "NP": [85.3240, 27.7172],     # 尼泊尔
    "NZ": [174.7772, -41.2865],   # 新西兰
    "PE": [-77.0428, -12.0464],   # 秘鲁
    "PH": [120.9842, 14.5995],    # 菲律宾
    "PK": [73.0479, 33.6844],     # 巴基斯坦
    "PL": [21.0175, 52.2297],     # 波兰
    "PR": [-66.1057, 18.4663],    # 波多黎各（美国自由邦）
    "PT": [-9.1393, 38.7223],     # 葡萄牙
    "PY": [-57.5759, -25.2637],   # 巴拉圭
    "QA": [51.5310, 25.2854],     # 卡塔尔
    "RO": [26.1025, 44.4268],     # 罗马尼亚
    "RU": [37.6173, 55.7558],     # 俄罗斯
    "SA": [46.7219, 24.7136],     # 沙特阿拉伯
    "SE": [18.0686, 59.3293],     # 瑞典
    "SG": [103.8198, 1.3521],     # 新加坡
    "TH": [100.5018, 13.7563],    # 泰国
    "TN": [10.1815, 36.8065],     # 突尼斯
    "TR": [32.8597, 39.9334],     # 土耳其
    "TW": [121.5654, 25.0330],    # 台湾地区（中国的省份）
    "UA": [30.5234, 50.4501],     # 乌克兰
    "US": [-77.0369, 38.9072],    # 美国
    "UY": [-56.1645, -34.9011],   # 乌拉圭
    "VE": [-66.9036, 10.4806],    # 委内瑞拉
    "VN": [105.8342, 21.0278],    # 越南
    "ZA": [28.1871, -25.7460],    # 南非
    "ZW": [31.0522, -17.8249],    # 津巴布韦
    "HK": [114.1694, 22.3193],    # 香港（中国特别行政区）
    "MO": [113.5439, 22.1987],    # 澳门（中国特别行政区）
    # 主權國家（新增）
    "AD": [1.5218, 42.5063],      # 安道尔
    "AG": [-61.7968, 17.0770],    # 安提瓜和巴布达
    "AM": [44.5035, 40.1776],     # 亚美尼亚
    "AO": [13.2345, -8.8390],     # 安哥拉
    "AW": [-69.9772, 12.5211],    # 阿鲁巴（荷兰海外领地）
    "AZ": [49.8920, 40.4093],     # 阿塞拜疆
    "BB": [-59.5988, 13.1132],    # 巴巴多斯
    "BH": [50.5577, 26.2285],     # 巴林
    "BJ": [2.6323, 6.4969],       # 贝宁
    "BN": [114.9422, 4.9031],     # 文莱
    "BS": [-77.3500, 25.0343],    # 巴哈马
    "BT": [89.6380, 27.4728],     # 不丹
    "BW": [25.9201, -24.6533],    # 博茨瓦纳
    "BZ": [-88.7667, 17.2510],    # 伯利兹
    "CF": [18.5582, 4.3947],      # 中非共和国
    "CI": [-5.5471, 7.5390],      # 科特迪瓦
    "CM": [11.5150, 3.8480],      # 喀麦隆
    "CV": [-23.5088, 14.9330],    # 佛得角
    "CY": [33.3823, 35.1856],     # 塞浦路斯
    "DJ": [42.5903, 11.5720],     # 吉布提
    "DM": [-61.3700, 15.2976],    # 多米尼克
    "ER": [38.9318, 15.3229],     # 厄立特里亚
    "ET": [38.7578, 8.9806],      # 埃塞俄比亚
    "FJ": [178.4419, -18.1416],   # 斐济
    "FM": [158.1623, 6.8875],     # 密克罗尼西亚
    "GA": [9.4673, 0.4162],       # 加蓬
    "GD": [-61.6900, 12.0500],    # 格林纳达
    "GG": [-2.5853, 49.4667],     # 根西岛（英国皇家属地）
    "GM": [-16.5778, 13.4557],    # 冈比亚
    "GQ": [8.7833, 3.7500],       # 赤道几内亚
    "GY": [-58.1551, 6.8013],     # 圭亚那
    "HT": [-72.3381, 18.5944],    # 海地
    "JE": [-2.1310, 49.2144],     # 泽西岛（英国皇家属地）
    "KM": [43.2551, -11.7022],    # 科摩罗
    "LA": [102.6300, 17.9628],    # 老挝
    "LB": [35.4955, 33.8886],     # 黎巴嫩
    "LI": [9.5557, 47.1410],      # 列支敦士登
    "LR": [-10.7972, 6.3008],     # 利比里亚
    "LS": [27.4869, -29.3100],    # 莱索托
    "LU": [6.1319, 49.6116],      # 卢森堡
    "LV": [24.0934, 56.9496],     # 拉脱维亚
    "MC": [7.4246, 43.7384],      # 摩纳哥
    "MD": [28.8614, 47.0105],     # 摩尔多瓦
    "MG": [47.5136, -18.9141],    # 马达加斯加
    "MK": [21.4314, 41.9973],     # 北马其顿
    "ML": [-8.0029, 12.6392],     # 马里
    "MR": [-15.9780, 18.0735],    # 毛里塔尼亚
    "MU": [57.5000, -20.3480],    # 毛里求斯
    "MV": [73.5109, 4.1755],      # 马尔代夫
    "MW": [33.7878, -13.9669],    # 马拉维
    "NA": [17.0934, -22.5609],    # 纳米比亚
    "NE": [2.1098, 13.5136],      # 尼日尔
    "PG": [147.1803, -9.4438],    # 巴布亚新几内亚
    "RW": [30.0619, -1.9500],     # 卢旺达
    "SC": [55.4540, -4.6221],     # 塞舌尔
    "SL": [-13.2317, 8.4840],     # 塞拉利昂
    "SM": [12.4473, 43.9356],     # 圣马力诺
    "SN": [-17.4467, 14.7167],    # 塞内加尔
    "SO": [45.3182, 2.0469],      # 索马里
    "SR": [-55.1699, 5.8520],     # 苏里南
    "ST": [6.7333, 0.3365],       # 圣多美和普林西比
    "SY": [36.2765, 33.5131],     # 叙利亚
    "SZ": [31.1461, -26.3200],    # 斯威士兰
    "TD": [15.0444, 12.1347],     # 乍得
    "TL": [125.5617, -8.5537],    # 东帝汶
    "TM": [58.3833, 37.9500],     # 土库曼斯坦
    "TO": [-175.2018, -21.1393],  # 汤加
    "TV": [179.1945, -8.5212],    # 图瓦卢
    "TZ": [35.7384, -6.1629],     # 坦桑尼亚
    "UZ": [69.2401, 41.2995],     # 乌兹别克斯坦
    "VU": [168.3228, -17.7333],   # 瓦努阿图
    "WS": [-171.7516, -13.8333],  # 萨摩亚
 
    # 特殊地区（新增）


    # 部分特殊地区

    "VG": [-64.6208, 18.4286],    # 英属维尔京群岛（英国海外领土）
    "KY": [-81.3744, 19.3133],    # 开曼群岛（英国海外领土）
    "BM": [-64.7500, 32.2948],    # 百慕大（英国海外领地）
    "FO": [-6.7710, 61.8926],     # 法罗群岛（丹麦自治领）
    "GF": [-52.3333, 4.9333],     # 法属圭亚那（法国海外省）
    "GL": [-51.6941, 64.1814],    # 格陵兰（丹麦自治领）
    "PF": [-149.5667, -17.5333],  # 法属波利尼西亚（法国海外集体）
    "RE": [55.4542, -20.8784],    # 留尼汪（法国海外省）
    "VI": [-64.9344, 18.3417],    # 美属维尔京群岛

    # 特殊标记
    "Multi_Nations": None,          # 多国共有区域（需根据具体案例定义）
    "Nation Not_Found": None      # 无法识别的代码
}

#endregion国家地理坐标（经度，纬度）

# region ###################################################### 统计逻辑实现  （更改统计规则从此处入手，或者从数据加载层面入手）
def analyze_paths(path_lines,):
    
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
            start_country = company_to_country.get(start_comp)[1]
            end_country = company_to_country.get(end_comp)[1]
            
            # 必须存在国家映射 会检查两个变量是否均为“真值”（即非空、非None、非False等）
            if not all([start_country, end_country]):
                continue
                
            if status == 'permanent_break':
                # 处理CN起始的段，强制创建新层级
                
                layer = 1
                current_chain = {'layer': layer}
                if current_chain:
                    
                    layer = current_chain['layer'] + 1
                    current_chain['layer'] = layer
                
                # 计算权重

                is_limit_break = (
                    final_status == 'limit_day_break' and 
                    (idx == len(segments)-1 and segments[-1][2] != 'permanent_break')
                )
                layer_weights = {1: 1.0, 2: 0.7, 3: 0.4} if is_limit_break else {1: 1.0, 2: 0.5, 3: 0.1}
                weight = layer_weights.get(layer, 0) * (0.1 if is_limit_break else 1)
                
                for start in start_country:
                    for target in end_country:
                        key = (start, target)
                        status_records['permanent_break'][key] += weight
                
            # 处理其他状态
            elif status in ('transfer', 'recovered'):
                for start in start_country:
                    for target in end_country:
                        status_records[status][(start, target)] += 1.0
                current_chain = None

    return status_records

status_data = analyze_paths(path_lines)

print("\n原始状态数据样本：")
# 调试：打印前5条记录

#比较位置不同的元组是否相等
country_set = set()

for i, (key, value) in enumerate(status_data['permanent_break'].items()):
    country_set.add(key)
country_set
need_count = 0
for country_pair in country_set:
    if 'CN' in country_pair and set(country_pair) != {'CN'}:
        need_count += 1
print('中国内陆 涉及地区对数：',need_count)


need_count = 0
for country_pair in country_set:
    if 'HK' in country_pair and set(country_pair) != {'HK'}:
        need_count += 1
print('中国香港 涉及地区对数：',need_count)

for key,value in status_data.items():
    print(key,value)





# endregion


# region创建地图图形

def create_map_figure(status_data,country:str, line_width_list=[],country_show_list:list=['CN','HK','TW','MO']):
    traces = []
    color_mapping = {
        'permanent_break': 'rgb(230,50,50)',  # 红色
        'transfer': 'rgb(50,180,50)',         # 绿色
        'recovered': 'rgb(255,200,0)'         # 黄色
    }
    valid_countries = {
        k: v for k, v in country_coords.items()
        if k not in ['Nation Not_Found'] and v is not None
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
        sum_weights = sum([weight for (start, end), weight in data.items()])
        for i, ((start, end), weight) in enumerate(data.items()):
            # 国家节点过滤（添加调试）
            if start not in valid_countries or end not in valid_countries:
                print(f"过滤无效节点：{start}→{end}")
                continue
             # 新增：国家过滤测试
            if (start not in country_show_list) and (end not in country_show_list):  # 检测元组是否包含中心国家
                print(f"过滤非中心国家节点：{start}→{end}")
                continue
            # 调试：打印前5条记录
            if i < 5:
                print(f'总权重为：{sum_weights}')
                print(f"  {start}→{end} 权重：{weight}")
                print(f'分位数为：{weight/sum_weights*100}')


            
            # 处理CN→CN的情况，使用CN_2作为终点坐标
            original_end = end
            if start == 'CN' and end == 'CN' and country in valid_countries:
                end = country  # 替换为CN_2
                # 确保替换后的国家有效
                if end not in valid_countries:
                    end = original_end  # 回退到原始国家
            # 坐标获取
            start_coord = valid_countries[start]
            end_coord = valid_countries[end]
            
            p1 = sum_weights*0.10
            p2 = sum_weights*0.20
            p3 = sum_weights*0.30
            # 线宽计算
            if weight < p1:
                line_width = line_width_list[0]
            elif weight < p2:
                line_width = line_width_list[1]
            elif weight < p3:
                line_width = line_width_list[2]
            else:
                line_width = line_width_list[3]

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
fig = create_map_figure(status_data,'CN_2', line_width_list=[1,6,10,15],country_show_list=['CN','HK','MO'])


fig.show()


# endregion创建地图图形

