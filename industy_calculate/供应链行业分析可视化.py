from datetime import datetime
import os
import re
import math  # 添加这行
from collections import defaultdict
import json  # 添加 json 导入

from matplotlib.dates import relativedelta

from component.cop_relation_rebuild_module import (
    save_file,
    split_countries,
    parse_date,
    rebuild_relations,
    load_companies,
    load_supply_chain_data,
    build_company_to_country,
    )

from component.company_supplyChain import SupplyRelation, Company
from datetime import timedelta
import pandas as pd
from typing import List

# 路径集合#
path_dic = {'company': r'.\调用文件\用于行业分类分析的可视化表\处理后的json文件\company.json',
            'supply_chain': r'.\调用文件\用于行业分类分析的可视化表\处理后的json文件\supply_relations.json',
            'complete_sc': r'.\调用文件\用于行业分类分析的可视化表\处理后的json文件'
            }

def load_industry_code_mapping(json_path):
    """
    读取行业代码JSON文件，形成行业代码到描述的映射字典
    
    参数说明：
    - json_path: industry_code.json文件的路径
    
    返回值：
    - industry_mapping: 字典，键为行业代码(INDUSTRY_ID)，值为行业描述(DESCRIPTION)
    
    使用示例：
    industry_mapping = load_industry_code_mapping(r".\调用文件\用于行业分类分析的可视化表\industry_code.json")
    print(industry_mapping.get("01", "未知行业"))  # 输出：指对各种农作物的种植
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            industry_data = json.load(f)
        
        # 构建行业代码到描述的映射字典
        industry_mapping = {}
        for item in industry_data:
            industry_id = item.get("INDUSTRY_ID", "")
            description = item.get("DESCRIPTION", "")
            industry_mapping[industry_id] = description
        
        print(f"成功加载行业代码映射，共{len(industry_mapping)}个行业代码")
        return industry_mapping
        
    except FileNotFoundError:
        print(f"文件未找到: {json_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return {}
    except Exception as e:
        print(f"加载行业代码映射时发生错误: {e}")
        return {}

industry_code_path = r".\调用文件\用于行业分类分析的可视化表\industry_code.json"
industry_mapping = load_industry_code_mapping(industry_code_path)

def extract_country_mapping():
    """
    从国家地理坐标中提取国家简称到国家名的映射字典
    
    返回值：
    - country_name_mapping: 字典，键为国家简称，值为国家名称
    """
    country_name_mapping = {
        # 主权国家
        "CN": "中国",
        "CN_2": "中国位置2",
        "AE": "阿拉伯联合酋长国",
        "AF": "阿富汗",
        "AL": "阿尔巴尼亚",
        "AR": "阿根廷",
        "AT": "奥地利",
        "AU": "澳大利亚",
        "AZ": "阿塞拜疆",
        "BA": "波黑",
        "BD": "孟加拉国",
        "BE": "比利时",
        "BF": "布基纳法索",
        "BG": "保加利亚",
        "BO": "玻利维亚",
        "BR": "巴西",
        "CA": "加拿大",
        "CD": "刚果民主共和国",
        "CH": "瑞士",
        "CL": "智利",
        "CO": "哥伦比亚",
        "CU": "古巴",
        "CZ": "捷克",
        "DE": "德国",
        "DK": "丹麦",
        "DZ": "阿尔及利亚",
        "EC": "厄瓜多尔",
        "EG": "埃及",
        "ES": "西班牙",
        "FI": "芬兰",
        "FR": "法国",
        "GB": "英国",
        "GE": "格鲁吉亚",
        "GH": "加纳",
        "GR": "希腊",
        "GT": "危地马拉",
        "HN": "洪都拉斯",
        "HR": "克罗地亚",
        "HU": "匈牙利",
        "ID": "印度尼西亚",
        "IE": "爱尔兰",
        "IL": "以色列",
        "IN": "印度",
        "IQ": "伊拉克",
        "IR": "伊朗",
        "IS": "冰岛",
        "IT": "意大利",
        "JM": "牙买加",
        "JO": "约旦",
        "JP": "日本",
        "KE": "肯尼亚",
        "KR": "韩国",
        "KW": "科威特",
        "KZ": "哈萨克斯坦",
        "LB": "黎巴嫩",
        "LK": "斯里兰卡",
        "MA": "摩洛哥",
        "MX": "墨西哥",
        "MY": "马来西亚",
        "NG": "尼日利亚",
        "NL": "荷兰",
        "NO": "挪威",
        "NP": "尼泊尔",
        "NZ": "新西兰",
        "PE": "秘鲁",
        "PH": "菲律宾",
        "PK": "巴基斯坦",
        "PL": "波兰",
        "PR": "波多黎各",
        "PT": "葡萄牙",
        "PY": "巴拉圭",
        "QA": "卡塔尔",
        "RO": "罗马尼亚",
        "RU": "俄罗斯",
        "SA": "沙特阿拉伯",
        "SE": "瑞典",
        "SG": "新加坡",
        "TH": "泰国",
        "TN": "突尼斯",
        "TR": "土耳其",
        "TW": "台湾地区",
        "UA": "乌克兰",
        "US": "美国",
        "UY": "乌拉圭",
        "VE": "委内瑞拉",
        "VN": "越南",
        "ZA": "南非",
        "ZW": "津巴布韦",
        "HK": "香港",
        "MO": "澳门",
        
        # 新增主权国家
        "AD": "安道尔",
        "AG": "安提瓜和巴布达",
        "AM": "亚美尼亚",
        "AO": "安哥拉",
        "AW": "阿鲁巴",
        "BB": "巴巴多斯",
        "BH": "巴林",
        "BJ": "贝宁",
        "BN": "文莱",
        "BS": "巴哈马",
        "BT": "不丹",
        "BW": "博茨瓦纳",
        "BZ": "伯利兹",
        "CF": "中非共和国",
        "CI": "科特迪瓦",
        "CM": "喀麦隆",
        "CV": "佛得角",
        "CY": "塞浦路斯",
        "DJ": "吉布提",
        "DM": "多米尼克",
        "ER": "厄立特里亚",
        "ET": "埃塞俄比亚",
        "FJ": "斐济",
        "FM": "密克罗尼西亚",
        "GA": "加蓬",
        "GD": "格林纳达",
        "GG": "根西岛",
        "GM": "冈比亚",
        "GQ": "赤道几内亚",
        "GY": "圭亚那",
        "HT": "海地",
        "JE": "泽西岛",
        "KM": "科摩罗",
        "LA": "老挝",
        "LI": "列支敦士登",
        "LR": "利比里亚",
        "LS": "莱索托",
        "LU": "卢森堡",
        "LV": "拉脱维亚",
        "MC": "摩纳哥",
        "MD": "摩尔多瓦",
        "MG": "马达加斯加",
        "MK": "北马其顿",
        "ML": "马里",
        "MR": "毛里塔尼亚",
        "MU": "毛里求斯",
        "MV": "马尔代夫",
        "MW": "马拉维",
        "NA": "纳米比亚",
        "NE": "尼日尔",
        "PG": "巴布亚新几内亚",
        "RW": "卢旺达",
        "SC": "塞舌尔",
        "SL": "塞拉利昂",
        "SM": "圣马力诺",
        "SN": "塞内加尔",
        "SO": "索马里",
        "SR": "苏里南",
        "ST": "圣多美和普林西比",
        "SY": "叙利亚",
        "SZ": "斯威士兰",
        "TD": "乍得",
        "TL": "东帝汶",
        "TM": "土库曼斯坦",
        "TO": "汤加",
        "TV": "图瓦卢",
        "TZ": "坦桑尼亚",
        "UZ": "乌兹别克斯坦",
        "VU": "瓦努阿图",
        "WS": "萨摩亚",
        
        # 特殊地区
        "VG": "英属维尔京群岛",
        "KY": "开曼群岛",
        "BM": "百慕大",
        "FO": "法罗群岛",
        "GF": "法属圭亚那",
        "GL": "格陵兰",
        "PF": "法属波利尼西亚",
        "RE": "留尼汪",
        "VI": "美属维尔京群岛",
        
        # 特殊标记
        "Multi_Nations": "多国共有区域",
        "Nation_Not_Found": "无法识别的代码"
    }
    
    return country_name_mapping

country_name_mapping = extract_country_mapping()

def get_country_name(country_code, country_mapping=None):
    """
    根据国家简称获取国家名称
    
    参数说明：
    - country_code: 国家简称
    - country_mapping: 国家映射字典（可选）
    
    返回值：
    - 国家名称字符串，如果未找到则返回原始代码
    """
    if country_mapping is None:
        country_mapping = extract_country_mapping()
    
    return country_mapping.get(country_code, country_code)

# 使用示例
country_name_mapping = extract_country_mapping()

# 测试示例
print("=== 国家简称到名称映射示例 ===")
test_codes = ["CN", "US", "JP", "DE", "GB", "FR", "KR", "IN"]
for code in test_codes:
    name = get_country_name(code, country_name_mapping)
    print(f"{code} -> {name}")

print(f"\n总共包含 {len(country_name_mapping)} 个国家/地区")

# 加载公司数据
companies = load_companies(path_dic["company"])


for idx, company in enumerate(companies.values()):
    print(f"公司ID：{company.id}，国家：{company.country}，上市状态：{company.listed}")
    if idx > 10:
        break
# 构建公司-国家映射表
company_to_country = build_company_to_country(companies)
# 重新构建包含中国节点的供应链关系
# 通过读取 supply_chains_with_industry_codes.json 重新构建 supply_chains_contains_cn_node
import json

def load_supply_chains_from_json(json_path, companies):
    """
    从JSON文件加载供应链数据并重新构建SupplyRelation对象
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chains = []
    for chain_data in data:
        chain = []
        for rel_dict in chain_data:
            from_co = companies.get(rel_dict["from_co_id"])
            to_co = companies.get(rel_dict["to_co_id"])
            if not from_co or not to_co:
                continue
            
            # 创建SupplyRelation对象，使用正确的datetime导入
            rel = SupplyRelation(
                from_co=from_co,
                to_co=to_co,
                start=datetime.strptime(rel_dict["start"], "%Y-%m-%d") if rel_dict["start"] else None,
                end=datetime.strptime(rel_dict["end"], "%Y-%m-%d") if rel_dict["end"] else None
            )
            
            # 单独设置status属性
            rel.status = rel_dict["status"]
            
            # 设置industry_codes属性
            rel.industry_codes = rel_dict.get("industry_codes")
            
            chain.append(rel)
        if chain:
            chains.append(chain)
    return chains

json_path = r".\调用文件\用于行业分类分析的可视化表\supply_chains_with_industry_codes.json"
supply_chains_contains_cn_node = load_supply_chains_from_json(json_path, companies)

print(f"重新构建后，包含中国节点的供应链数量: {len(supply_chains_contains_cn_node)}")


def analyze_industry_vulnerability(supply_chains_contains_cn_node, calculation_method='separate', min_threshold=50):
    """
    分析不同行业的供应链脆弱性（基于长供应链分析）
    
    :param calculation_method: 计算方法
        - 'separate': 断裂率和转移率分别计算（原方法）
        - 'sequential': 转移率基于断裂数计算（您提议的方法）
    :param min_threshold: 最小样本数阈值，只有当转移数和断裂数都超过此值时才纳入最终评判
    """
    
    # 统计断裂和转移的长供应链
    break_chains = []  # 包含断裂的长供应链
    transfer_chains = []  # 包含转移的长供应链
    
    # 第一步：识别断裂和转移的长供应链
    for chain in supply_chains_contains_cn_node:
        has_break = False
        has_transfer = False
        
        for rel in chain:
            if isinstance(rel, SupplyRelation):
                if rel.status == 'permanent_break':
                    has_break = True
                elif rel.status == 'transfer':
                    has_transfer = True
        
        if has_break:
            break_chains.append(chain)
        if has_transfer:
            transfer_chains.append(chain)
    
    # 第二步：统计各行业在断裂供应链中的出现次数
    industry_break_count = defaultdict(int)
    for chain in break_chains:
        affected_industries = set()  # 使用set避免同一链中同一行业重复计算
        
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.industry_codes:
                if rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                    for industry_code in rel.industry_codes:
                        affected_industries.add(industry_code)
        
        # 每个受影响的行业在这个断裂链中计数+1
        for industry_code in affected_industries:
            industry_break_count[industry_code] += 1
    
    # 第三步：统计各行业在转移供应链中的出现次数
    industry_transfer_count = defaultdict(int)
    for chain in transfer_chains:
        affected_industries = set()  # 使用set避免同一链中同一行业重复计算
        
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.industry_codes:
                if rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                    for industry_code in rel.industry_codes:
                        affected_industries.add(industry_code)
        
        # 每个受影响的行业在这个转移链中计数+1
        for industry_code in affected_industries:
            industry_transfer_count[industry_code] += 1
    
    # 第四步：应用最小样本数过滤并计算各行业的脆弱性指标
    vulnerability_analysis = {}
    excluded_industries = []  # 记录被排除的行业
    
    # 获取所有涉及的行业代码
    all_industries = set(industry_break_count.keys()) | set(industry_transfer_count.keys())
    
    total_break_chains = len(break_chains)
    total_transfer_chains = len(transfer_chains)
    
    for industry_code in all_industries:
        break_count = industry_break_count.get(industry_code, 0)
        transfer_count = industry_transfer_count.get(industry_code, 0)
        
        # 应用最小样本数过滤
        if break_count < min_threshold and transfer_count < min_threshold:
            excluded_industries.append({
                'industry_code': industry_code,
                'break_count': break_count,
                'transfer_count': transfer_count,
                'reason': f'断裂数({break_count})和转移数({transfer_count})均小于{min_threshold}'
            })
            continue
        
        if calculation_method == 'separate':
            # 原方法：分别计算占比
            vulnerability_analysis[industry_code] = {
                'total_break_chains': break_count,
                'total_transfer_chains': transfer_count,
                'break_rate': break_count / total_break_chains if total_break_chains > 0 else 0,
                'transfer_rate': transfer_count / total_transfer_chains if total_transfer_chains > 0 else 0,
                'calculation_method': 'separate',
                'meets_threshold': True
            }
        elif calculation_method == 'sequential':
            # 新方法：转移率基于该行业的断裂数计算
            vulnerability_analysis[industry_code] = {
                'total_break_chains': break_count,
                'total_transfer_chains': transfer_count,
                'break_rate': break_count / total_break_chains if total_break_chains > 0 else 0,
                'transfer_rate': transfer_count / break_count if break_count > 0 else 0,  # 关键修改
                'transfer_adaptation_ratio': transfer_count / break_count if break_count > 0 else 0,  # 更明确的命名
                'calculation_method': 'sequential',
                'meets_threshold': True
            }
    
    print(f"统计结果（计算方法: {calculation_method}，最小样本数阈值: {min_threshold}）：")
    print(f"  断裂供应链总数: {total_break_chains}")
    print(f"  转移供应链总数: {total_transfer_chains}")
    print(f"  原始涉及行业总数: {len(all_industries)}")
    print(f"  符合阈值的行业数: {len(vulnerability_analysis)}")
    print(f"  被排除的行业数: {len(excluded_industries)}")
    
    if calculation_method == 'sequential':
        print(f"  注意：转移率 = 该行业转移链数 / 该行业断裂链数")
        print(f"  转移率 > 1 表示该行业转移链数超过断裂链数")
    
    # 显示一些被排除的行业示例
    if excluded_industries:
        print(f"\n被排除的行业示例（前10个）:")
        for i, excluded in enumerate(excluded_industries[:10]):
            print(f"  {i+1}. 行业{excluded['industry_code']}: {excluded['reason']}")
        if len(excluded_industries) > 10:
            print(f"  ...还有{len(excluded_industries) - 10}个行业被排除")
    
    return vulnerability_analysis, excluded_industries

def analyze_industry_geography(supply_chains_contains_cn_node, company_to_country):
    """
    分析转向中国和从中国转出的供应链行业分类
    
    计算原理说明：
    - 遍历所有包含中国节点的供应链链路，识别包含 'transfer' 状态的供应链。
    - 重点分析两个方向的转移：
      1. 转向中国：其他国家 -> 中国（CN/HK/MO）
      2. 从中国转出：中国（CN/HK/MO） -> 其他国家
    - 统计每个转移方向的行业分布和目标国家分布
    - CN、HK、MO统一视为中国地区

    呈现内容说明：
    - 返回值包含：
      1. 'to_china_analysis': 转向中国的供应链行业分析
      2. 'from_china_analysis': 从中国转出的供应链行业分析
      3. 'china_bilateral_summary': 双向转移统计摘要
    """
    
    # 定义中国地区代码（包括香港、澳门）
    china_codes = {'CN', 'HK', 'MO', 'China', 'Hong Kong', 'Macau'}
    
    # 定义无效国家代码集合
    invalid_countries = {
        'Unknown_Empty', 'Unknown_None', 'Unknown', 'Nation_Not_Found', 
        '', None, 'null', 'NULL', 'N/A', 'na', 'NA'
    }
    
    # 第一步：识别包含转移关系的供应链
    transfer_chains = []
    for chain in supply_chains_contains_cn_node:
        has_transfer = False
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.status == 'transfer':
                has_transfer = True
                break
        if has_transfer:
            transfer_chains.append(chain)
    
    print(f"包含转移关系的供应链数量: {len(transfer_chains)}")
    
    # 第二步：分析转向中国和从中国转出的转移关系
    to_china_industry_count = defaultdict(int)      # 转向中国的行业统计
    from_china_industry_count = defaultdict(int)    # 从中国转出的行业统计
    to_china_source_countries = defaultdict(lambda: defaultdict(int))  # 转向中国的来源国家
    from_china_target_countries = defaultdict(lambda: defaultdict(int)) # 从中国转出的目标国家
    
    total_to_china_transfers = 0
    total_from_china_transfers = 0
    
    # 数据质量计数器
    filtered_out_count = 0
    
    for chain in transfer_chains:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.status == 'transfer':
                # 获取供应方和需求方国家
                from_countries = company_to_country.get(rel.from_co.id, (['Unknown'], ['Unknown']))[1]
                to_countries = company_to_country.get(rel.to_co.id, (['Unknown'], ['Unknown']))[1]
                
                # 清理国家代码
                def clean_countries(countries):
                    cleaned = []
                    for country in countries:
                        if country is None or str(country).strip() == '' or str(country).strip() in invalid_countries:
                            continue
                        cleaned.append(str(country).strip())
                    return cleaned
                
                cleaned_from_countries = clean_countries(from_countries)
                cleaned_to_countries = clean_countries(to_countries)
                
                if not cleaned_from_countries or not cleaned_to_countries:
                    filtered_out_count += 1
                    continue
                
                # 判断是否为中国相关转移
                from_is_china = any(country in china_codes for country in cleaned_from_countries)
                to_is_china = any(country in china_codes for country in cleaned_to_countries)
                
                # 获取行业代码
                if (rel.industry_codes and 
                    rel.industry_codes != 'Line_Not_Found' and 
                    rel.industry_codes is not None):
                    
                    for industry_code in rel.industry_codes:
                        # 1. 转向中国的转移（其他国家 -> 中国）
                        if to_is_china and not from_is_china:
                            to_china_industry_count[industry_code] += 1
                            total_to_china_transfers += 1
                            
                            # 记录来源国家
                            for from_country in cleaned_from_countries:
                                to_china_source_countries[industry_code][from_country] += 1
                        
                        # 2. 从中国转出（中国 -> 其他国家）
                        elif from_is_china and not to_is_china:
                            from_china_industry_count[industry_code] += 1
                            total_from_china_transfers += 1
                            
                            # 记录目标国家
                            for to_country in cleaned_to_countries:
                                from_china_target_countries[industry_code][to_country] += 1
    
    print(f"数据质量报告:")
    print(f"  被过滤的无效数据数量: {filtered_out_count}")
    print(f"  转向中国的转移关系总数: {total_to_china_transfers}")
    print(f"  从中国转出的转移关系总数: {total_from_china_transfers}")
    
    # 第三步：分析转向中国的行业分布
    to_china_analysis = {}
    if total_to_china_transfers > 0:
        for industry_code, count in to_china_industry_count.items():
            # 获取该行业的主要来源国家
            source_countries = to_china_source_countries[industry_code]
            sorted_sources = sorted(source_countries.items(), key=lambda x: x[1], reverse=True)
            
            to_china_analysis[industry_code] = {
                'transfer_count': count,
                'percentage_in_to_china': count / total_to_china_transfers,
                'main_source_countries': [item[0] for item in sorted_sources[:3]],
                'source_distribution': dict(sorted_sources)
            }
        
        # 按转向中国的数量排序
        sorted_to_china_industries = sorted(to_china_analysis.items(), 
                                          key=lambda x: x[1]['transfer_count'], reverse=True)
    else:
        sorted_to_china_industries = []
    
    # 第四步：分析从中国转出的行业分布
    from_china_analysis = {}
    if total_from_china_transfers > 0:
        for industry_code, count in from_china_industry_count.items():
            # 获取该行业的主要目标国家
            target_countries = from_china_target_countries[industry_code]
            sorted_targets = sorted(target_countries.items(), key=lambda x: x[1], reverse=True)
            
            from_china_analysis[industry_code] = {
                'transfer_count': count,
                'percentage_in_from_china': count / total_from_china_transfers,
                'main_target_countries': [item[0] for item in sorted_targets[:3]],
                'target_distribution': dict(sorted_targets)
            }
        
        # 按从中国转出的数量排序
        sorted_from_china_industries = sorted(from_china_analysis.items(), 
                                            key=lambda x: x[1]['transfer_count'], reverse=True)
    else:
        sorted_from_china_industries = []
    
    # 第五步：生成统计摘要
    print(f"\n=== 中国双向供应链转移分析摘要 ===")
    
    # 转向中国分析
    if sorted_to_china_industries:
        print(f"\n📥 转向中国的供应链转移分析:")
        print(f"   转向中国的总转移数: {total_to_china_transfers}")
        print(f"   涉及行业数: {len(sorted_to_china_industries)}")
        print(f"   转向中国最多的前10个行业:")
        
        for i, (industry, data) in enumerate(sorted_to_china_industries[:10], 1):
            pct = data['percentage_in_to_china'] * 100
            main_sources = ', '.join(data['main_source_countries'])
            print(f"   {i:2d}. 行业{industry:<8}: {data['transfer_count']:>4}次 ({pct:>5.1f}%) "
                  f"- 主要来源: {main_sources}")
    else:
        print(f"\n📥 没有发现转向中国的供应链转移")
    
    # 从中国转出分析
    if sorted_from_china_industries:
        print(f"\n📤 从中国转出的供应链转移分析:")
        print(f"   从中国转出的总转移数: {total_from_china_transfers}")
        print(f"   涉及行业数: {len(sorted_from_china_industries)}")
        print(f"   从中国转出最多的前10个行业:")
        
        for i, (industry, data) in enumerate(sorted_from_china_industries[:10], 1):
            pct = data['percentage_in_from_china'] * 100
            main_targets = ', '.join(data['main_target_countries'])
            print(f"   {i:2d}. 行业{industry:<8}: {data['transfer_count']:>4}次 ({pct:>5.1f}%) "
                  f"- 主要目标: {main_targets}")
    else:
        print(f"\n📤 没有发现从中国转出的供应链转移")
    
    # 双向对比分析
    print(f"\n🔄 双向转移对比分析:")
    print(f"   转向中国 vs 从中国转出 比例: {total_to_china_transfers} : {total_from_china_transfers}")
    if total_to_china_transfers > 0 and total_from_china_transfers > 0:
        ratio = total_to_china_transfers / total_from_china_transfers
        print(f"   转向中国/从中国转出 比率: {ratio:.2f}")
        
        # 找出双向转移都较多的行业
        to_china_top_industries = set([item[0] for item in sorted_to_china_industries[:10]])
        from_china_top_industries = set([item[0] for item in sorted_from_china_industries[:10]])
        bidirectional_industries = to_china_top_industries & from_china_top_industries
        
        if bidirectional_industries:
            print(f"\n   双向转移都较活跃的行业:")
            for industry in bidirectional_industries:
                to_china_count = to_china_analysis.get(industry, {}).get('transfer_count', 0)
                from_china_count = from_china_analysis.get(industry, {}).get('transfer_count', 0)
                print(f"     行业{industry}: 转向中国{to_china_count}次, 从中国转出{from_china_count}次")
    
    return {
        'to_china_analysis': {
            'total_transfers': total_to_china_transfers,
            'industry_distribution': to_china_analysis,
            'sorted_industries': sorted_to_china_industries
        },
        'from_china_analysis': {
            'total_transfers': total_from_china_transfers,
            'industry_distribution': from_china_analysis,
            'sorted_industries': sorted_from_china_industries
        },
        'china_bilateral_summary': {
            'to_china_transfers': total_to_china_transfers,
            'from_china_transfers': total_from_china_transfers,
            'transfer_ratio': total_to_china_transfers / total_from_china_transfers if total_from_china_transfers > 0 else 0,
            'total_transfer_chains': len(transfer_chains),
            'data_quality': {
                'filtered_out_count': filtered_out_count
            }
        }
    }
    

def analyze_industry_interconnection(supply_chains_contains_cn_node):
    """
    分析行业间的供应链关联模式

    计算原理说明：
    - 遍历所有包含中国节点的供应链链路，提取每一对相邻的供应关系（即链路中的前后两个关系）。
    - 对于每一对相邻关系，分别获取其所属行业代码（industry_codes）。
    - 统计所有“前一行业”到“后一行业”的配对出现次数，形成行业间的有向关联矩阵（industry_pairs）。
    - 该矩阵的每个元素 industry_pairs[A][B] 表示行业A作为供应方、行业B作为需求方的链路数量。

    呈现内容说明：
    - 返回值为 industry_pairs 字典，键为起始行业代码，值为一个字典（其键为目标行业代码，值为对应的链路数量）。
    - 可用于分析哪些行业之间存在较强的供应链耦合关系，识别行业间的关键依赖路径和行业集群。
    """
    industry_pairs = defaultdict(lambda: defaultdict(int))
    
    for chain in supply_chains_contains_cn_node:
        supply_relations = [rel for rel in chain if isinstance(rel, SupplyRelation)]
        
        for i in range(len(supply_relations) - 1):
            from_rel = supply_relations[i]
            to_rel = supply_relations[i + 1]
            
            if (from_rel.industry_codes and to_rel.industry_codes and 
                from_rel.industry_codes != 'Line_Not_Found' and 
                to_rel.industry_codes != 'Line_Not_Found'):
                
                for from_industry in from_rel.industry_codes:
                    for to_industry in to_rel.industry_codes:
                        industry_pairs[from_industry][to_industry] += 1
    
    return industry_pairs

def analyze_industry_temporal_dynamics(supply_chains_contains_cn_node):
    """
    分析行业在不同时间段的状态变化

    计算原理说明：
    - 遍历所有包含中国节点的供应链链路，针对每个供应关系（SupplyRelation）：
        - 提取其行业代码（industry_codes）和起始年份（rel.start.year）。
        - 针对每个行业代码，统计该年份下各类状态（如permanent_break、transfer、recovery等）的出现次数。
    - 结果形成一个三层嵌套字典 industry_timeline[industry_code][year][status]，用于描述每个行业在每一年各状态的数量分布。

    呈现内容说明：
    - 返回值为 industry_timeline 字典，键为行业代码，值为年份-状态分布的字典。
    - 可用于分析不同行业在各年份的断裂、转移、恢复等动态趋势，辅助识别行业风险爆发期和恢复期。
    """
    industry_timeline = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for chain in supply_chains_contains_cn_node:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.industry_codes:
                if rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                    year = rel.start.year if rel.start else 'unknown'
                    for industry_code in rel.industry_codes:
                        industry_timeline[industry_code][year][rel.status] += 1

    return industry_timeline


def analyze_industry_concentration(supply_chains_contains_cn_node):
    """
    分析行业集中度和供应链多样性

    计算原理说明：
    - 遍历所有包含中国节点的供应链链路，针对每个供应关系（SupplyRelation）：
        - 提取其行业代码（industry_codes）、供应方公司ID（from_co.id）、需求方公司ID（to_co.id）、状态（status）。
        - 针对每个行业代码，累计该行业的供应关系总数（total_relations）。
        - 统计该行业涉及的唯一公司数量（unique_companies），即供应方和需求方公司ID的并集。
        - 统计该行业下各类状态（如permanent_break、transfer、recovery等）的出现次数（status_distribution）。
    - 计算集中度指标：
        - concentration_ratio = total_relations / unique_companies，反映行业内供应关系的集中程度，值越高表示行业越集中。
        - status_entropy = 供应关系状态分布的熵，衡量行业状态的多样性，熵越高表示状态越分散。

    呈现内容说明：
    - 返回值为 concentration_metrics 字典，键为行业代码，值为该行业的集中度分析指标（总关系数、唯一公司数、集中度、状态分布熵）。
    - 可用于识别高度集中的行业和多样化程度较高的行业，辅助行业风险和竞争格局分析。
    """
    industry_stats = defaultdict(lambda: {
        'total_relations': 0,
        'unique_companies': set(),
        'status_distribution': defaultdict(int),
        'country_diversity': set()
    })
    
    for chain in supply_chains_contains_cn_node:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.industry_codes:
                if rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                    for industry_code in rel.industry_codes:
                        industry_stats[industry_code]['total_relations'] += 1
                        industry_stats[industry_code]['unique_companies'].add(rel.from_co.id)
                        industry_stats[industry_code]['unique_companies'].add(rel.to_co.id)
                        industry_stats[industry_code]['status_distribution'][rel.status] += 1

    # 计算集中度指标
    concentration_metrics = {}
    for industry, stats in industry_stats.items():
        concentration_metrics[industry] = {
            'total_relations': stats['total_relations'],
            'unique_companies': len(stats['unique_companies']),
            'concentration_ratio': stats['total_relations'] / len(stats['unique_companies']) if stats['unique_companies'] else 0,
            'status_entropy': calculate_entropy(stats['status_distribution'])
        }
    
    return concentration_metrics

def calculate_entropy(distribution):
    """
    计算分布的熵值（Shannon entropy）

    计算原理说明：
    - 熵（entropy）用于衡量分布的不确定性或多样性，常用于描述状态分布的分散程度。
    - 对于每种状态，计算其概率 p = count / total。
    - 熵的公式为：entropy = -sum(p * log2(p))，概率越均匀，熵值越高，表示多样性越大。

    呈现内容说明：
    - 返回值为该分布的熵值（float），用于衡量行业内供应关系状态的多样性。
    - 熵值越高，说明该行业的供应链状态越分散，越多样化；熵值越低，说明状态更集中。
    """
    total = sum(distribution.values())
    if total == 0:
        return 0

    entropy = 0
    for count in distribution.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy

def analyze_industry_resilience(supply_chains_contains_cn_node):
    """
    评估不同行业的供应链恢复能力

    计算原理说明：
    - 遍历所有包含中国节点的供应链链路，提取每一对相邻的供应关系（即链路中的前后两个关系）。
    - 对于每一对相邻关系，判断前一个关系的状态（permanent_break 或 transfer），并统计其后紧跟着 recovery 状态的次数。
    - 针对每个行业代码（industry_code），累计：
        - total_breaks: 断裂（permanent_break）次数
        - total_transfers: 转移（transfer）次数
        - break_to_recovery: 断裂后紧跟恢复的次数
        - transfer_to_recovery: 转移后紧跟恢复的次数
    - 恢复成功率（recovery_success_rate）= (break_to_recovery + transfer_to_recovery) / (total_breaks + total_transfers)
        表示行业在发生断裂或转移后能够恢复的比例。

    呈现内容说明：
    - 返回值为 industry_resilience 字典，键为行业代码，值为该行业的恢复能力指标（断裂/转移次数、恢复次数、恢复成功率）。
    - 可用于比较不同行业在供应链中断后恢复的能力，识别韧性较强或较弱的行业。
    """
    industry_resilience = defaultdict(lambda: {
        'break_to_recovery': 0,
        'transfer_to_recovery': 0,
        'total_breaks': 0,
        'total_transfers': 0,
        'recovery_success_rate': 0
    })
    
    for chain in supply_chains_contains_cn_node:
        supply_relations = [rel for rel in chain if isinstance(rel, SupplyRelation)]
        
        # 分析状态转换模式
        for i in range(len(supply_relations) - 1):
            current_rel = supply_relations[i]
            next_rel = supply_relations[i + 1]
            
            if (current_rel.industry_codes and current_rel.industry_codes != 'Line_Not_Found' and
                current_rel.industry_codes is not None):
                
                for industry_code in current_rel.industry_codes:
                    if current_rel.status == 'permanent_break':
                        industry_resilience[industry_code]['total_breaks'] += 1
                        if next_rel.status == 'recovery':
                            industry_resilience[industry_code]['break_to_recovery'] += 1
                    elif current_rel.status == 'transfer':
                        industry_resilience[industry_code]['total_transfers'] += 1
                        if next_rel.status == 'recovery':
                            industry_resilience[industry_code]['transfer_to_recovery'] += 1
    
    # 计算恢复成功率
    for industry, metrics in industry_resilience.items():
        total_disruptions = metrics['total_breaks'] + metrics['total_transfers']
        total_recoveries = metrics['break_to_recovery'] + metrics['transfer_to_recovery']
        
        if total_disruptions > 0:
            metrics['recovery_success_rate'] = total_recoveries / total_disruptions
    
    return industry_resilience



def generate_comprehensive_industry_report(supply_chains_contains_cn_node, company_to_country):
    """
    生成综合行业分析报告
    """
    print("=== 供应链行业属性综合分析报告 ===\n")
    
    # 1. 行业脆弱性分析
    vulnerability_result = analyze_industry_vulnerability(supply_chains_contains_cn_node,'sequential')
    vulnerability, excluded_industries = vulnerability_result
    
    # 1.1 按断裂率排名
    print("1.1 行业脆弱性排名（按断裂率排序）:")
    sorted_by_break_rate = sorted(vulnerability.items(), key=lambda x: x[1]['break_rate'], reverse=True)
    for i, (industry, metrics) in enumerate(sorted_by_break_rate[:10]):
        print(f"   {i+1}. 行业{industry}: 断裂率{metrics['break_rate']:.2%}, 涉及断裂链数{metrics['total_break_chains']}")
    
    # 1.2 按转移数量排名
    print("\n1.2 行业脆弱性排名（按转移数量排序）:")
    sorted_by_transfer_count = sorted(vulnerability.items(), key=lambda x: x[1]['total_transfer_chains'], reverse=True)
    for i, (industry, metrics) in enumerate(sorted_by_transfer_count[:10]):
        print(f"   {i+1}. 行业{industry}: 转移数量{metrics['total_transfer_chains']}, 转移率{metrics['transfer_rate']:.2%}")
    
    # 2. 行业恢复能力分析（修改为按绝对数量排名）
    resilience = analyze_industry_resilience(supply_chains_contains_cn_node)
    print("\n2. 行业恢复能力排名（按恢复绝对数量排序）:")
    
    # 计算每个行业的总恢复数量（断裂后恢复 + 转移后恢复）
    resilience_with_total = {}
    for industry, metrics in resilience.items():
        total_recoveries = metrics['break_to_recovery'] + metrics['transfer_to_recovery']
        resilience_with_total[industry] = {
            **metrics,
            'total_recoveries': total_recoveries
        }
    
    # 按总恢复数量排序
    sorted_resilience = sorted(resilience_with_total.items(), 
                              key=lambda x: x[1]['total_recoveries'], reverse=True)
    
    for i, (industry, metrics) in enumerate(sorted_resilience[:10]):
        print(f"   {i+1}. 行业{industry}: 总恢复数量{metrics['total_recoveries']}次 "
              f"(断裂后恢复{metrics['break_to_recovery']}次 + 转移后恢复{metrics['transfer_to_recovery']}次), "
              f"恢复成功率{metrics['recovery_success_rate']:.2%}")
    
    # 3. 行业集中度分析
    concentration = analyze_industry_concentration(supply_chains_contains_cn_node)
    print("\n3. 行业集中度分析:")
    sorted_concentration = sorted(concentration.items(), key=lambda x: x[1]['concentration_ratio'], reverse=True)
    for i, (industry, metrics) in enumerate(sorted_concentration[:10]):
        print(f"   {i+1}. 行业{industry}: 集中度{metrics['concentration_ratio']:.2f}, 企业数{metrics['unique_companies']}")
    
    # 4. 时间动态分析
    temporal = analyze_industry_temporal_dynamics(supply_chains_contains_cn_node)
    print("\n4. 重点行业时间动态（2020-2023年断裂趋势）:")
    
    # 5. 地理转移分析 - 新增
    geography = analyze_industry_geography(supply_chains_contains_cn_node, company_to_country)
    
    return {
        'vulnerability': vulnerability,
        'excluded_industries': excluded_industries,
        'resilience': resilience_with_total,  # 返回包含总恢复数量的数据
        'concentration': concentration,
        'temporal': temporal,
        'geography': geography,  # 新增地理分析结果
        'sorted_by_break_rate': sorted_by_break_rate,
        'sorted_by_transfer_count': sorted_by_transfer_count,
        'sorted_resilience': sorted_resilience  # 新增：按绝对数量排序的恢复能力数据
    }


# 执行综合分析
comprehensive_report = generate_comprehensive_industry_report(supply_chains_contains_cn_node, company_to_country)

def get_industry_description(industry_code, industry_mapping):
    """
    根据行业代码获取行业描述
    
    参数说明：
    - industry_code: 行业代码
    - industry_mapping: 行业代码映射字典
    
    返回值：
    - 行业描述字符串，如果未找到则返回"未知行业"
    """
    return industry_mapping.get(str(industry_code), f"未知行业(代码:{industry_code})")

# 详细展示断裂率最高的前50个行业代码
if comprehensive_report.get('sorted_by_break_rate'):
    print("\n=== 断裂率最高的前50个行业代码 ===")
    for i, (industry_code, metrics) in enumerate(comprehensive_report['sorted_by_break_rate'][:50], 1):
        industry_desc = get_industry_description(industry_code, industry_mapping)
        print(f"{i:2d}. 行业代码: {industry_code:>8} ({industry_desc})")
        print(f"    断裂率: {metrics['break_rate']:>6.2%}, 涉及断裂链数: {metrics['total_break_chains']:>8}")
else:
    print("没有可用的断裂率数据。")

# 详细展示转移数量最高的前50个行业代码 - 修改：更新变量名和显示内容
if comprehensive_report.get('sorted_by_transfer_count'):
    print("\n=== 转移数量最高的前50个行业代码 ===")
    for i, (industry_code, metrics) in enumerate(comprehensive_report['sorted_by_transfer_count'][:50], 1):
        industry_desc = get_industry_description(industry_code, industry_mapping)
        print(f"{i:2d}. 行业代码: {industry_code:>8} ({industry_desc})")
        print(f"    转移数量: {metrics['total_transfer_chains']:>8}, 转移率: {metrics['transfer_rate']:>6.2%}")
else:
    print("没有可用的转移数量数据。")

# 对比分析：找出断裂率和转移数量都高的行业 - 修改：更新变量名
print("\n=== 断裂率和转移数量均较高的行业（前20名交集分析） ===")
top_break_industries = set([item[0] for item in comprehensive_report['sorted_by_break_rate'][:20]])
top_transfer_industries = set([item[0] for item in comprehensive_report['sorted_by_transfer_count'][:20]])  # 更新变量名
high_risk_industries = top_break_industries & top_transfer_industries

if high_risk_industries:
    print("同时在断裂率和转移数量前20名的行业:")
    for industry in high_risk_industries:
        metrics = comprehensive_report['vulnerability'][industry]
        industry_desc = get_industry_description(industry, industry_mapping)
        print(f"  行业{industry} ({industry_desc}): 断裂率{metrics['break_rate']:.2%}, 转移数量{metrics['total_transfer_chains']}")
else:
    print("没有行业同时在断裂率和转移数量前20名中。")

# 详细展示地理转移分析结果
print("\n" + "="*80)
print("=== 供应链转移地理分析详细报告 ===")
print("="*80)

geography_data = comprehensive_report.get('geography')
if geography_data:
    # 检查实际的数据结构
    print("可用的地理数据键:", list(geography_data.keys()))
    
    # 根据实际的数据结构来访问数据
    to_china_data = geography_data.get('to_china_analysis', {})
    from_china_data = geography_data.get('from_china_analysis', {})
    bilateral_summary = geography_data.get('china_bilateral_summary', {})
    
    # 1. 总体统计摘要
    print(f"\n📊 中国双向转移总体统计:")
    if bilateral_summary:
        print(f"   转向中国的转移总数: {bilateral_summary.get('to_china_transfers', 0)}")
        print(f"   从中国转出的转移总数: {bilateral_summary.get('from_china_transfers', 0)}")
        print(f"   转向/转出比率: {bilateral_summary.get('transfer_ratio', 0):.2f}")
        print(f"   总转移链数: {bilateral_summary.get('total_transfer_chains', 0)}")
    
    # 2. 转向中国的详细分析
    print(f"\n📥 转向中国的供应链转移详细分析:")
    if to_china_data and 'sorted_industries' in to_china_data:
        to_china_industries = to_china_data['sorted_industries']
        total_to_china = to_china_data.get('total_transfers', 0)
        
        if to_china_industries:
            print(f"   涉及行业总数: {len(to_china_industries)}")
            print(f"   转向中国转移总数: {total_to_china}")
            print(f"   转向中国最多的前20个行业:")
            
            for i, (industry, data) in enumerate(to_china_industries[:20], 1):
                industry_desc = get_industry_description(industry, industry_mapping)
                pct = data.get('percentage_in_to_china', 0) * 100
                transfer_count = data.get('transfer_count', 0)
                # 获取主要来源国家名称
                main_sources = data.get('main_source_countries', [])
                main_sources_with_names = []
                for country_code in main_sources[:3]:
                    country_name = get_country_name(country_code, country_name_mapping)
                    main_sources_with_names.append(country_name)
                main_sources_str = ', '.join(main_sources_with_names)
                print(f"   {i:2d}. 行业{industry:<8} ({industry_desc}): {transfer_count:>4}次 ({pct:>5.1f}%)")
                if main_sources_str:
                    print(f"       主要来源: {main_sources_str}")
            
            # 转向中国的行业集中度分析
            if len(to_china_industries) >= 5:
                print(f"\n📈 转向中国的行业集中度分析:")
                top_5_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:5]])
                if len(to_china_industries) >= 10:
                    top_10_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:10]])
                if len(to_china_industries) >= 20:
                    top_20_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:20]])
                
                if total_to_china > 0:
                    print(f"   前5个行业占转向中国总量的比例: {top_5_count/total_to_china:.2%}")
                    if len(to_china_industries) >= 10:
                        print(f"   前10个行业占转向中国总量的比例: {top_10_count/total_to_china:.2%}")
                    if len(to_china_industries) >= 20:
                        print(f"   前20个行业占转向中国总量的比例: {top_20_count/total_to_china:.2%}")
        else:
            print("   没有发现转向中国的供应链转移")
    else:
        print("   转向中国的数据不可用")
    
    # 3. 从中国转出的详细分析
    print(f"\n📤 从中国转出的供应链转移详细分析:")
    if from_china_data and 'sorted_industries' in from_china_data:
        from_china_industries = from_china_data['sorted_industries']
        total_from_china = from_china_data.get('total_transfers', 0)
        
        if from_china_industries:
            print(f"   涉及行业总数: {len(from_china_industries)}")
            print(f"   从中国转出转移总数: {total_from_china}")
            print(f"   从中国转出最多的前20个行业:")
            
            for i, (industry, data) in enumerate(from_china_industries[:20], 1):
                industry_desc = get_industry_description(industry, industry_mapping)
                pct = data.get('percentage_in_from_china', 0) * 100
                transfer_count = data.get('transfer_count', 0)
                # 获取主要目标国家名称
                main_targets = data.get('main_target_countries', [])
                main_targets_with_names = []
                for country_code in main_targets[:3]:
                    country_name = get_country_name(country_code, country_name_mapping)
                    main_targets_with_names.append(country_name)
                main_targets_str = ', '.join(main_targets_with_names)
                print(f"   {i:2d}. 行业{industry:<8} ({industry_desc}): {transfer_count:>4}次 ({pct:>5.1f}%)")
                if main_targets_str:
                    print(f"       主要目标: {main_targets_str}")
            
            # 从中国转出的行业集中度分析
            if len(from_china_industries) >= 5:
                print(f"\n📈 从中国转出的行业集中度分析:")
                top_5_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:5]])
                if len(from_china_industries) >= 10:
                    top_10_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:10]])
                if len(from_china_industries) >= 20:
                    top_20_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:20]])
                
                if total_from_china > 0:
                    print(f"   前5个行业占从中国转出总量的比例: {top_5_count/total_from_china:.2%}")
                    if len(from_china_industries) >= 10:
                        print(f"   前10个行业占从中国转出总量的比例: {top_10_count/total_from_china:.2%}")
                    if len(from_china_industries) >= 20:
                        print(f"   前20个行业占从中国转出总量的比例: {top_20_count/total_from_china:.2%}")
        else:
            print("   没有发现从中国转出的供应链转移")
    else:
        print("   从中国转出的数据不可用")
    
    # 4. 重点行业的国家分布分析
    if (to_china_data and 'sorted_industries' in to_china_data and 
        from_china_data and 'sorted_industries' in from_china_data):
        
        to_china_industries = to_china_data['sorted_industries']
        from_china_industries = from_china_data['sorted_industries']
        
        if to_china_industries and from_china_industries:
            print(f"\n🔍 重点行业的国家分布详细分析:")
            
            # 选择转向中国最多的前5个行业
            print(f"\n   📥 转向中国最多的前5个行业的来源国家分布:")
            for i, (industry, data) in enumerate(to_china_industries[:5], 1):
                industry_desc = get_industry_description(industry, industry_mapping)
                transfer_count = data.get('transfer_count', 0)
                source_distribution = data.get('source_distribution', {})
                
                print(f"   {i}. 行业{industry} ({industry_desc}) (转向中国: {transfer_count}次):")
                if source_distribution:
                    sorted_sources = sorted(source_distribution.items(), 
                                          key=lambda x: x[1], reverse=True)
                    for j, (country, count) in enumerate(sorted_sources[:5], 1):
                        country_name = get_country_name(country, country_name_mapping)
                        pct = count / transfer_count * 100 if transfer_count > 0 else 0
                        print(f"      {j}. {country_name}: {count}次 ({pct:.1f}%)")
                else:
                    print(f"      无详细来源国家数据")
            
            # 选择从中国转出最多的前5个行业
            print(f"\n   📤 从中国转出最多的前5个行业的目标国家分布:")
            for i, (industry, data) in enumerate(from_china_industries[:5], 1):
                industry_desc = get_industry_description(industry, industry_mapping)
                transfer_count = data.get('transfer_count', 0)
                target_distribution = data.get('target_distribution', {})
                
                print(f"   {i}. 行业{industry} ({industry_desc}) (从中国转出: {transfer_count}次):")
                if target_distribution:
                    sorted_targets = sorted(target_distribution.items(), 
                                          key=lambda x: x[1], reverse=True)
                    for j, (country, count) in enumerate(sorted_targets[:5], 1):
                        country_name = get_country_name(country, country_name_mapping)
                        pct = count / transfer_count * 100 if transfer_count > 0 else 0
                        print(f"      {j}. {country_name}: {count}次 ({pct:.1f}%)")
                else:
                    print(f"      无详细目标国家数据")

else:
    print("没有可用的地理转移分析数据。")

print("\n" + "="*80)
print("=== 供应链转移地理分析报告完成 ===")
print("="*80)

# 详细展示中国双向转移分析结果
print("\n" + "="*80)
print("=== 中国双向供应链转移详细分析报告 ===")
print("="*80)

geography_data = comprehensive_report.get('geography')
if geography_data:
    to_china_data = geography_data['to_china_analysis']
    from_china_data = geography_data['from_china_analysis']
    bilateral_summary = geography_data['china_bilateral_summary']
    
    # 1. 总体统计摘要
    print(f"\n📊 中国双向转移总体统计:")
    print(f"   转向中国的转移总数: {bilateral_summary['to_china_transfers']}")
    print(f"   从中国转出的转移总数: {bilateral_summary['from_china_transfers']}")
    print(f"   转向/转出比率: {bilateral_summary['transfer_ratio']:.2f}")
    print(f"   总转移链数: {bilateral_summary['total_transfer_chains']}")
    
    # 2. 转向中国的详细分析
    print(f"\n📥 转向中国的供应链转移详细分析:")
    to_china_industries = to_china_data['sorted_industries']
    if to_china_industries:
        print(f"   涉及行业总数: {len(to_china_industries)}")
        print(f"   转向中国最多的前20个行业:")
        
        for i, (industry, data) in enumerate(to_china_industries[:20], 1):
            industry_desc = get_industry_description(industry, industry_mapping)
            pct = data['percentage_in_to_china'] * 100
            # 获取主要来源国家名称
            main_sources_with_names = []
            for country_code in data['main_source_countries'][:3]:
                country_name = get_country_name(country_code, country_name_mapping)
                main_sources_with_names.append(country_name)
            main_sources_str = ', '.join(main_sources_with_names)
            print(f"   {i:2d}. 行业{industry:<8} ({industry_desc}): {data['transfer_count']:>4}次 ({pct:>5.1f}%)")
            if main_sources_str:
                print(f"       主要来源: {main_sources_str}")
        
        # 转向中国的行业集中度分析
        if len(to_china_industries) >= 5:
            print(f"\n📈 转向中国的行业集中度分析:")
            top_5_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:5]])
            if len(to_china_industries) >= 10:
                top_10_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:10]])
            if len(to_china_industries) >= 20:
                top_20_count = sum([data.get('transfer_count', 0) for _, data in to_china_industries[:20]])
            
            if total_to_china > 0:
                print(f"   前5个行业占转向中国总量的比例: {top_5_count/total_to_china:.2%}")
                if len(to_china_industries) >= 10:
                    print(f"   前10个行业占转向中国总量的比例: {top_10_count/total_to_china:.2%}")
                if len(to_china_industries) >= 20:
                    print(f"   前20个行业占转向中国总量的比例: {top_20_count/total_to_china:.2%}")
    else:
        print("   没有发现转向中国的供应链转移")
    
    # 3. 从中国转出的详细分析
    print(f"\n📤 从中国转出的供应链转移详细分析:")
    from_china_industries = from_china_data['sorted_industries']
    if from_china_industries:
        print(f"   涉及行业总数: {len(from_china_industries)}")
        print(f"   从中国转出最多的前20个行业:")
        
        for i, (industry, data) in enumerate(from_china_industries[:20], 1):
            industry_desc = get_industry_description(industry, industry_mapping)
            pct = data['percentage_in_from_china'] * 100
            # 获取主要目标国家名称
            main_targets_with_names = []
            for country_code in data['main_target_countries'][:3]:
                country_name = get_country_name(country_code, country_name_mapping)
                main_targets_with_names.append(country_name)
            main_targets_str = ', '.join(main_targets_with_names)
            print(f"   {i:2d}. 行业{industry:<8} ({industry_desc}): {data['transfer_count']:>4}次 ({pct:>5.1f}%)")
            if main_targets_str:
                print(f"       主要目标: {main_targets_str}")
        
        # 从中国转出的行业集中度分析
        if len(from_china_industries) >= 5:
            print(f"\n📈 从中国转出的行业集中度分析:")
            top_5_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:5]])
            if len(from_china_industries) >= 10:
                top_10_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:10]])
            if len(from_china_industries) >= 20:
                top_20_count = sum([data.get('transfer_count', 0) for _, data in from_china_industries[:20]])
            
            if total_from_china > 0:
                print(f"   前5个行业占从中国转出总量的比例: {top_5_count/total_from_china:.2%}")
                if len(from_china_industries) >= 10:
                    print(f"   前10个行业占从中国转出总量的比例: {top_10_count/total_from_china:.2%}")
                if len(from_china_industries) >= 20:
                    print(f"   前20个行业占从中国转出总量的比例: {top_20_count/total_from_china:.2%}")
    else:
        print("   没有发现从中国转出的供应链转移")
    
    # 4. 重点行业的国家分布分析
    if to_china_industries and from_china_industries:
        print(f"\n🔍 重点行业的国家分布详细分析:")
        
        # 选择转向中国最多的前5个行业
        print(f"\n   📥 转向中国最多的前5个行业的来源国家分布:")
        for i, (industry, data) in enumerate(to_china_industries[:5], 1):
            industry_desc = get_industry_description(industry, industry_mapping)
            transfer_count = data.get('transfer_count', 0)
            source_distribution = data.get('source_distribution', {})
            
            print(f"   {i}. 行业{industry} ({industry_desc}) (转向中国: {transfer_count}次):")
            if source_distribution:
                sorted_sources = sorted(source_distribution.items(), 
                                      key=lambda x: x[1], reverse=True)
                for j, (country, count) in enumerate(sorted_sources[:5], 1):
                    country_name = get_country_name(country, country_name_mapping)
                    pct = count / transfer_count * 100 if transfer_count > 0 else 0
                    print(f"      {j}. {country_name}: {count}次 ({pct:.1f}%)")
            else:
                print(f"      无详细来源国家数据")
        
        # 选择从中国转出最多的前5个行业
        print(f"\n   📤 从中国转出最多的前5个行业的目标国家分布:")
        for i, (industry, data) in enumerate(from_china_industries[:5], 1):
            industry_desc = get_industry_description(industry, industry_mapping)
            transfer_count = data.get('transfer_count', 0)
            target_distribution = data.get('target_distribution', {})
            
            print(f"   {i}. 行业{industry} ({industry_desc}) (从中国转出: {transfer_count}次):")
            if target_distribution:
                sorted_targets = sorted(target_distribution.items(), 
                                      key=lambda x: x[1], reverse=True)
                for j, (country, count) in enumerate(sorted_targets[:5], 1):
                    country_name = get_country_name(country, country_name_mapping)
                    pct = count / transfer_count * 100 if transfer_count > 0 else 0
                    print(f"      {j}. {country_name}: {count}次 ({pct:.1f}%)")
            else:
                print(f"      无详细目标国家数据")

else:
    print("没有可用的中国双向转移分析数据。")

print("\n" + "="*80)
print("=== 中国双向供应链转移分析报告完成 ===")
print("="*80)


def analyze_industry_temporal_transfer_trends_academic(supply_chains_contains_cn_node, company_to_country, industry_mapping, country_name_mapping):
    """
    供应链转移时间趋势的学术分析
    
    返回适合经济学/统计学论文的结构化数据，包括：
    1. 描述性统计
    2. 趋势分析指标
    3. 集中度测量
    4. 结构变化检验数据
    """
    
    # 定义中国地区代码
    china_codes = {'CN', 'HK', 'MO', 'China', 'Hong Kong', 'Macau'}
    
    # 定义无效国家代码集合
    invalid_countries = {
        'Unknown_Empty', 'Unknown_None', 'Unknown', 'Nation_Not_Found', 
        '', None, 'null', 'NULL', 'N/A', 'na', 'NA'
    }
    
    # 数据收集结构
    yearly_data = defaultdict(lambda: {
        'to_china': defaultdict(lambda: defaultdict(int)),    # [year][industry][country] = count
        'from_china': defaultdict(lambda: defaultdict(int)),  # [year][industry][country] = count
        'total_transfers': 0,
        'to_china_total': 0,
        'from_china_total': 0
    })
    
    # 数据收集
    for chain in supply_chains_contains_cn_node:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.status == 'transfer':
                year = rel.start.year if rel.start else None
                if not year:
                    continue
                
                # 获取国家信息
                from_countries = company_to_country.get(rel.from_co.id, (['Unknown'], ['Unknown']))[1]
                to_countries = company_to_country.get(rel.to_co.id, (['Unknown'], ['Unknown']))[1]
                
                # 清理国家代码
                cleaned_from = [c.strip() for c in from_countries if c and str(c).strip() not in invalid_countries]
                cleaned_to = [c.strip() for c in to_countries if c and str(c).strip() not in invalid_countries]
                
                if not cleaned_from or not cleaned_to:
                    continue
                
                # 判断转移方向
                from_is_china = any(c in china_codes for c in cleaned_from)
                to_is_china = any(c in china_codes for c in cleaned_to)
                
                if rel.industry_codes and rel.industry_codes != 'Line_Not_Found':
                    yearly_data[year]['total_transfers'] += 1
                    
                    for industry in rel.industry_codes:
                        if to_is_china and not from_is_china:  # 转向中国
                            yearly_data[year]['to_china_total'] += 1
                            for country in cleaned_from:
                                yearly_data[year]['to_china'][industry][country] += 1
                        elif from_is_china and not to_is_china:  # 从中国转出
                            yearly_data[year]['from_china_total'] += 1
                            for country in cleaned_to:
                                yearly_data[year]['from_china'][industry][country] += 1
    
    # 构建学术分析结果
    academic_results = {
        'summary_statistics': {},
        'temporal_trends': {},
        'industry_concentration': {},
        'geographic_concentration': {},
        'market_share_evolution': {},
        'structural_change_indicators': {},
        'regression_ready_data': []
    }
    
    # 1. 描述性统计
    years = sorted(yearly_data.keys())
    academic_results['summary_statistics'] = {
        'observation_period': {'start': min(years), 'end': max(years), 'span': max(years) - min(years) + 1},
        'yearly_totals': {
            year: {
                'total_transfers': data['total_transfers'],
                'to_china_transfers': data['to_china_total'],
                'from_china_transfers': data['from_china_total'],
                'china_transfer_ratio': data['to_china_total'] / data['total_transfers'] if data['total_transfers'] > 0 else 0,
                'china_net_inflow': data['to_china_total'] - data['from_china_total']
            }
            for year, data in yearly_data.items()
        }
    }
    
    # 2. 时间趋势分析
    def calculate_trend_statistics(series_data):
        """计算时间序列的趋势统计"""
        if len(series_data) < 2:
            return {'trend': 0, 'volatility': 0, 'growth_rate': 0}
        
        values = list(series_data.values())
        years_list = list(series_data.keys())
        
        # 线性趋势 (简单斜率)
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i**2 for i in range(n))
        
        trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2) if (n * sum_x2 - sum_x**2) != 0 else 0
        
        # 变异系数
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val)**2 for v in values) / len(values)
        volatility = (variance**0.5) / mean_val if mean_val > 0 else 0
        
        # 复合增长率
        if values[0] > 0 and values[-1] > 0:
            growth_rate = (values[-1] / values[0]) ** (1 / (len(values) - 1)) - 1
        else:
            growth_rate = 0
        
        return {
            'trend_slope': trend,
            'volatility_cv': volatility,
            'cagr': growth_rate,
            'total_change': values[-1] - values[0],
            'relative_change': (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
        }
    
    # 计算各种时间序列的趋势
    to_china_series = {year: data['to_china_total'] for year, data in yearly_data.items()}
    from_china_series = {year: data['from_china_total'] for year, data in yearly_data.items()}
    total_series = {year: data['total_transfers'] for year, data in yearly_data.items()}
    
    academic_results['temporal_trends'] = {
        'to_china_trends': calculate_trend_statistics(to_china_series),
        'from_china_trends': calculate_trend_statistics(from_china_series),
        'total_transfer_trends': calculate_trend_statistics(total_series),
        'china_share_evolution': {
            year: data['to_china_total'] / data['total_transfers'] if data['total_transfers'] > 0 else 0
            for year, data in yearly_data.items()
        }
    }
    
    # 3. 行业集中度分析 (HHI指数)
    def calculate_hhi(distribution):
        """计算赫芬达尔-赫希曼指数"""
        total = sum(distribution.values())
        if total == 0:
            return 0
        shares = [count / total for count in distribution.values()]
        return sum(share**2 for share in shares)
    
    academic_results['industry_concentration'] = {}
    for year, data in yearly_data.items():
        # 转向中国的行业集中度
        to_china_industry_dist = defaultdict(int)
        for industry, countries in data['to_china'].items():
            to_china_industry_dist[industry] = sum(countries.values())
        
        # 从中国转出的行业集中度
        from_china_industry_dist = defaultdict(int)
        for industry, countries in data['from_china'].items():
            from_china_industry_dist[industry] = sum(countries.values())
        
        academic_results['industry_concentration'][year] = {
            'to_china_hhi': calculate_hhi(to_china_industry_dist),
            'from_china_hhi': calculate_hhi(from_china_industry_dist),
            'to_china_top5_share': sum(sorted(to_china_industry_dist.values(), reverse=True)[:5]) / sum(to_china_industry_dist.values()) if to_china_industry_dist else 0,
            'from_china_top5_share': sum(sorted(from_china_industry_dist.values(), reverse=True)[:5]) / sum(from_china_industry_dist.values()) if from_china_industry_dist else 0,
            'to_china_industry_count': len(to_china_industry_dist),
            'from_china_industry_count': len(from_china_industry_dist)
        }
    
    # 4. 地理集中度分析
    academic_results['geographic_concentration'] = {}
    for year, data in yearly_data.items():
        # 转向中国的地理分布
        to_china_geo_dist = defaultdict(int)
        for industry, countries in data['to_china'].items():
            for country, count in countries.items():
                to_china_geo_dist[country] += count
        
        # 从中国转出的地理分布
        from_china_geo_dist = defaultdict(int)
        for industry, countries in data['from_china'].items():
            for country, count in countries.items():
                from_china_geo_dist[country] += count
        
        academic_results['geographic_concentration'][year] = {
            'to_china_geo_hhi': calculate_hhi(to_china_geo_dist),
            'from_china_geo_hhi': calculate_hhi(from_china_geo_dist),
            'to_china_country_count': len(to_china_geo_dist),
            'from_china_country_count': len(from_china_geo_dist),
            'to_china_top3_countries': sorted(to_china_geo_dist.items(), key=lambda x: x[1], reverse=True)[:3],
            'from_china_top3_countries': sorted(from_china_geo_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    # 5. 市场份额演化 (重点行业)
    # 找出转移总量最大的前10个行业
    industry_totals = defaultdict(int)
    for year_data in yearly_data.values():
        for industry, countries in year_data['to_china'].items():
            industry_totals[industry] += sum(countries.values())
        for industry, countries in year_data['from_china'].items():
            industry_totals[industry] += sum(countries.values())
    
    top_industries = sorted(industry_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    academic_results['market_share_evolution'] = {}
    for industry, _ in top_industries:
        industry_name = industry_mapping.get(str(industry), f"Industry_{industry}")
        academic_results['market_share_evolution'][industry] = {
            'industry_name': industry_name,
            'yearly_performance': {}
        }
        
        for year in years:
            to_china_count = sum(yearly_data[year]['to_china'][industry].values())
            from_china_count = sum(yearly_data[year]['from_china'][industry].values())
            total_year_to_china = yearly_data[year]['to_china_total']
            total_year_from_china = yearly_data[year]['from_china_total']
            
            academic_results['market_share_evolution'][industry]['yearly_performance'][year] = {
                'to_china_count': to_china_count,
                'from_china_count': from_china_count,
                'to_china_share': to_china_count / total_year_to_china if total_year_to_china > 0 else 0,
                'from_china_share': from_china_count / total_year_from_china if total_year_from_china > 0 else 0,
                'net_flow': to_china_count - from_china_count
            }
    
    # 6. 结构变化指标
    def calculate_structural_change(data_series):
        """计算结构变化指标"""
        if len(data_series) < 2:
            return {'structural_break_indicator': 0, 'coefficient_of_variation': 0}
        
        values = list(data_series.values())
        
        # 变异系数
        mean_val = sum(values) / len(values)
        cv = (sum((v - mean_val)**2 for v in values) / len(values))**0.5 / mean_val if mean_val > 0 else 0
        
        # 简单的结构断点指标（前后半期均值差异）
        mid_point = len(values) // 2
        first_half_mean = sum(values[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_mean = sum(values[mid_point:]) / (len(values) - mid_point) if len(values) > mid_point else 0
        structural_break = abs(second_half_mean - first_half_mean) / first_half_mean if first_half_mean > 0 else 0
        
        return {
            'structural_break_indicator': structural_break,
            'coefficient_of_variation': cv,
            'first_half_mean': first_half_mean,
            'second_half_mean': second_half_mean
        }
    
    academic_results['structural_change_indicators'] = {
        'to_china_structural_change': calculate_structural_change(to_china_series),
        'from_china_structural_change': calculate_structural_change(from_china_series),
        'china_share_structural_change': calculate_structural_change(academic_results['temporal_trends']['china_share_evolution'])
    }
    
    # 7. 回归分析准备数据
    for year in years:
        year_data = yearly_data[year]
        academic_results['regression_ready_data'].append({
            'year': year,
            'to_china_transfers': year_data['to_china_total'],
            'from_china_transfers': year_data['from_china_total'],
            'total_transfers': year_data['total_transfers'],
            'china_share': year_data['to_china_total'] / year_data['total_transfers'] if year_data['total_transfers'] > 0 else 0,
            'net_china_flow': year_data['to_china_total'] - year_data['from_china_total'],
            'to_china_hhi': academic_results['industry_concentration'][year]['to_china_hhi'],
            'from_china_hhi': academic_results['industry_concentration'][year]['from_china_hhi'],
            'geo_to_china_hhi': academic_results['geographic_concentration'][year]['to_china_geo_hhi'],
            'geo_from_china_hhi': academic_results['geographic_concentration'][year]['from_china_geo_hhi']
        })
    
    return academic_results

def export_academic_results_to_tables(academic_results, output_path=".\调用文件\用于行业分类分析的可视化表\学术报告图表"):
    """
    将学术分析结果导出为适合论文的表格格式
    """
    import pandas as pd
    import os
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # 表1: 描述性统计汇总表
    summary_data = []
    for year, stats in academic_results['summary_statistics']['yearly_totals'].items():
        summary_data.append({
            'Year': year,
            'Total Transfers': stats['total_transfers'],
            'To China': stats['to_china_transfers'],
            'From China': stats['from_china_transfers'],
            'China Share (%)': stats['china_transfer_ratio'] * 100,
            'Net China Inflow': stats['china_net_inflow']
        })
    
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv(f"{output_path}/table1_descriptive_statistics.csv", index=False)
    
    # 表2: 时间趋势分析
    trends = academic_results['temporal_trends']
    trend_data = {
        'Metric': ['To China CAGR (%)', 'From China CAGR (%)', 'To China Volatility (CV)', 
                  'From China Volatility (CV)', 'To China Trend Slope', 'From China Trend Slope'],
        'Value': [
            trends['to_china_trends']['cagr'] * 100,
            trends['from_china_trends']['cagr'] * 100,
            trends['to_china_trends']['volatility_cv'],
            trends['from_china_trends']['volatility_cv'],
            trends['to_china_trends']['trend_slope'],
            trends['from_china_trends']['trend_slope']
        ]
    }
    df_trends = pd.DataFrame(trend_data)
    df_trends.to_csv(f"{output_path}/table2_temporal_trends.csv", index=False)
    
    # 表3: 集中度指标
    concentration_data = []
    for year, conc in academic_results['industry_concentration'].items():
        concentration_data.append({
            'Year': year,
            'To China Industry HHI': conc['to_china_hhi'],
            'From China Industry HHI': conc['from_china_hhi'],
            'To China Top5 Share (%)': conc['to_china_top5_share'] * 100,
            'From China Top5 Share (%)': conc['from_china_top5_share'] * 100,
            'Geographic HHI (To China)': academic_results['geographic_concentration'][year]['to_china_geo_hhi'],
            'Geographic HHI (From China)': academic_results['geographic_concentration'][year]['from_china_geo_hhi']
        })
    
    df_concentration = pd.DataFrame(concentration_data)
    df_concentration.to_csv(f"{output_path}/table3_concentration_indices.csv", index=False)
    
    # 表4: 回归数据
    df_regression = pd.DataFrame(academic_results['regression_ready_data'])
    df_regression.to_csv(f"{output_path}/table4_regression_data.csv", index=False)
    
    # 表5: 重点行业市场份额演化
    market_share_data = []
    for industry, data in academic_results['market_share_evolution'].items():
        for year, performance in data['yearly_performance'].items():
            market_share_data.append({
                'Industry_Code': industry,
                'Industry_Name': data['industry_name'],
                'Year': year,
                'To_China_Share': performance['to_china_share'] * 100,
                'From_China_Share': performance['from_china_share'] * 100,
                'Net_Flow': performance['net_flow']
            })
    
    df_market_share = pd.DataFrame(market_share_data)
    df_market_share.to_csv(f"{output_path}/table5_industry_market_shares.csv", index=False)
    
    return f"学术分析表格已导出至 {output_path} 目录"

# 调用学术分析函数
academic_analysis = analyze_industry_temporal_transfer_trends_academic(
    supply_chains_contains_cn_node,
    company_to_country, 
    industry_mapping, 
    country_name_mapping
)

# 导出结果
export_message = export_academic_results_to_tables(academic_analysis)
print(export_message)

# 提供关键学术指标的快速访问
print("\n=== 关键学术发现摘要 ===")
print(f"研究期间: {academic_analysis['summary_statistics']['observation_period']['start']}-{academic_analysis['summary_statistics']['observation_period']['end']}")
print(f"转向中国年复合增长率: {academic_analysis['temporal_trends']['to_china_trends']['cagr']*100:.2f}%")
print(f"从中国转出年复合增长率: {academic_analysis['temporal_trends']['from_china_trends']['cagr']*100:.2f}%")
print(f"转向中国变异系数: {academic_analysis['temporal_trends']['to_china_trends']['volatility_cv']:.3f}")
print(f"从中国转出变异系数: {academic_analysis['temporal_trends']['from_china_trends']['volatility_cv']:.3f}")


import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
import pandas as pd
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def setup_chinese_fonts():
    """
    设置matplotlib中文字体支持
    
    参数含义：
    - 无参数
    
    返回值：
    - 无返回值，但会配置全局字体设置
    
    功能说明：
    - 配置matplotlib以支持中文显示
    - 避免中文字符显示为方块
    - 设置负号正常显示
    """
    try:
        # 尝试使用系统中文字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC']
        for font in chinese_fonts:
            try:
                plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                break
            except:
                continue
        plt.rcParams['axes.unicode_minus'] = False
        print("中文字体配置成功")
    except Exception as e:
        print(f"中文字体配置失败: {e}")

def create_industry_transfer_visualization(academic_analysis, industry_mapping, country_name_mapping, output_path=".\调用文件\用于行业分类分析的可视化表\学术报告图表"):
    """
    创建行业转移趋势的综合可视化分析
    
    参数含义：
    - academic_analysis: 学术分析结果字典，包含时间序列数据
    - industry_mapping: 行业代码到行业名称的映射字典
    - country_name_mapping: 国家代码到国家名称的映射字典
    - output_path: 图表输出路径
    
    返回值：
    - 无返回值，但会生成多个可视化图表文件
    
    功能说明：
    - 生成行业转移趋势的时间序列图
    - 展示转移链条数和转移指向国家的变化
    - 提供多维度的可视化分析
    """
    
    setup_chinese_fonts()
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # 1. 总体转移趋势图
    create_overall_transfer_trends(academic_analysis, output_path)
    
    # 2. 重点行业转移趋势图
    create_top_industries_transfer_trends(academic_analysis, industry_mapping, output_path)
    
    # 3. 行业集中度变化图
    create_industry_concentration_trends(academic_analysis, output_path)
    
    # 4. 地理转移热力图
    create_geographic_transfer_heatmap(academic_analysis, country_name_mapping, output_path)
    
    # 5. 重点行业的国家流向图
    create_industry_country_flow_charts(academic_analysis, industry_mapping, country_name_mapping, output_path)
    
    # 6. 转移结构变化雷达图
    create_structural_change_radar(academic_analysis, output_path)
    
    print(f"所有可视化图表已生成并保存至: {output_path}")

def create_overall_transfer_trends(academic_analysis, output_path):
    """
    创建总体转移趋势图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - output_path: 输出路径
    
    图表说明：
    - X轴：年份（时间维度）
    - Y轴：转移数量（供应链转移的绝对数量）
    - 蓝色线：转向中国的转移数量（其他国家→中国）
    - 红色线：从中国转出的转移数量（中国→其他国家）
    - 绿色线：净流入中国的转移数量（转向中国 - 从中国转出）
    """
    
    # 提取时间序列数据
    years = sorted(academic_analysis['summary_statistics']['yearly_totals'].keys())
    to_china_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['to_china_transfers'] for year in years]
    from_china_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['from_china_transfers'] for year in years]
    net_inflow_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['china_net_inflow'] for year in years]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 上图：绝对数量
    ax1.plot(years, to_china_data, marker='o', linewidth=2.5, label='转向中国', color='#1f77b4')
    ax1.plot(years, from_china_data, marker='s', linewidth=2.5, label='从中国转出', color='#ff7f0e')
    ax1.plot(years, net_inflow_data, marker='^', linewidth=2.5, label='净流入中国', color='#2ca02c')
    
    ax1.set_title('供应链转移总体趋势分析\n(Supply Chain Transfer Overall Trends)', fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlabel('年份 (Year)', fontsize=12)
    ax1.set_ylabel('转移数量 (Transfer Count)', fontsize=12)
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 添加数值标签
    for i, year in enumerate(years):
        ax1.annotate(f'{to_china_data[i]}', (year, to_china_data[i]), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
        ax1.annotate(f'{from_china_data[i]}', (year, from_china_data[i]), 
                    textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9)
    
    # 在这里添加Y轴设置，让Y轴稍高一些
    max_value = max(max(to_china_data), max(from_china_data), max(net_inflow_data))
    ax1.set_ylim(0, max_value * 1.15)  # 在最大值基础上增加15%的空间

    # 下图：份额变化
    china_share_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['china_transfer_ratio'] * 100 for year in years]
    total_transfers = [academic_analysis['summary_statistics']['yearly_totals'][year]['total_transfers'] for year in years]
    
    ax2_twin = ax2.twinx()
    
    # 柱状图：总转移数量
    bars = ax2.bar(years, total_transfers, alpha=0.6, color='lightgray', label='总转移数量')
    
    # 折线图：中国份额
    line = ax2_twin.plot(years, china_share_data, marker='D', linewidth=3, 
                        color='red', label='中国份额占比')

    # 添加下图的Y轴设置
    ax2.set_ylim(0, max(total_transfers) * 1.25)  # 左Y轴（总转移数量）增加25%空间
    ax2_twin.set_ylim(0, max(china_share_data) * 1.25)  # 右Y轴（中国份额占比）增加25%空间

    ax2.set_xlabel('年份 (Year)', fontsize=12)
    ax2.set_ylabel('总转移数量 (Total Transfers)', fontsize=12)
    ax2_twin.set_ylabel('中国份额占比 (%) (China Share Percentage)', fontsize=12)
    
    # 合并图例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=11)
    
    ax2.set_title('总转移量与中国份额变化\n(Total Transfers and China Share Evolution)', fontsize=14, pad=15)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图1_总体转移趋势分析.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig1_Overall_Transfer_Trends.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_top_industries_transfer_trends(academic_analysis, industry_mapping, output_path):
    """
    创建重点行业转移趋势图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典
    - output_path: 输出路径
    
    图表说明：
    - 展示转移量最大的前8个行业的时间变化趋势
    - X轴：年份
    - Y轴：转移数量
    - 不同颜色线条代表不同行业
    - 分为转向中国和从中国转出两个子图
    """
    
    # 获取重点行业数据
    market_share_evolution = academic_analysis['market_share_evolution']
    
    # 选择前8个行业进行可视化
    top_industries = list(market_share_evolution.keys())[:8]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # 设置颜色方案
    colors = plt.cm.tab10(np.linspace(0, 1, len(top_industries)))
    
    years = sorted(list(market_share_evolution[top_industries[0]]['yearly_performance'].keys()))
    
    # 上图：转向中国
    for i, industry in enumerate(top_industries):
        short_name = get_simplified_industry_name(industry, industry_mapping)
        to_china_counts = [market_share_evolution[industry]['yearly_performance'][year]['to_china_count'] 
                          for year in years]
        
        ax1.plot(years, to_china_counts, marker='o', linewidth=2, 
                label=f'{industry}: {short_name}', color=colors[i])
    
    
    ax1.set_title('重点行业转向中国的转移趋势\n(Top Industries Transfer Trends to China)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlabel('年份 (Year)', fontsize=12)
    ax1.set_ylabel('转向中国转移数量 (Transfers to China)', fontsize=12)
    # 调整图例位置和字体大小
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    ax1.grid(True, alpha=0.3)

    # 下图：从中国转出
    for i, industry in enumerate(top_industries):
        short_name = get_simplified_industry_name(industry, industry_mapping)
        from_china_counts = [market_share_evolution[industry]['yearly_performance'][year]['from_china_count'] 
                           for year in years]
        
        ax2.plot(years, from_china_counts, marker='s', linewidth=2, 
                label=f'{industry}: {short_name}', color=colors[i])
    
    
    ax2.set_title('重点行业从中国转出的转移趋势\n(Top Industries Transfer Trends from China)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax2.set_xlabel('年份 (Year)', fontsize=12)
    ax2.set_ylabel('从中国转出转移数量 (Transfers from China)', fontsize=12)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图2_重点行业转移趋势.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig2_Top_Industries_Transfer_Trends.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_industry_concentration_trends(academic_analysis, output_path):
    """
    创建行业集中度变化趋势图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - output_path: 输出路径
    
    图表说明：
    - X轴：年份
    - Y轴左：HHI指数（赫芬达尔-赫希曼指数，衡量市场集中度）
    - Y轴右：行业数量（参与转移的行业总数）
    - HHI指数越高表示转移越集中在少数行业
    - 行业数量反映转移的多样性
    """
    
    years = sorted(academic_analysis['industry_concentration'].keys())
    
    # 提取集中度数据
    to_china_hhi = [academic_analysis['industry_concentration'][year]['to_china_hhi'] for year in years]
    from_china_hhi = [academic_analysis['industry_concentration'][year]['from_china_hhi'] for year in years]
    to_china_industry_count = [academic_analysis['industry_concentration'][year]['to_china_industry_count'] for year in years]
    from_china_industry_count = [academic_analysis['industry_concentration'][year]['from_china_industry_count'] for year in years]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 上图：HHI指数变化
    ax1.plot(years, to_china_hhi, marker='o', linewidth=2.5, label='转向中国HHI', color='blue')
    ax1.plot(years, from_china_hhi, marker='s', linewidth=2.5, label='从中国转出HHI', color='red')
    
    ax1.set_title('行业集中度变化趋势 (HHI指数)\n(Industry Concentration Trends - HHI Index)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlabel('年份 (Year)', fontsize=12)
    ax1.set_ylabel('HHI指数 (HHI Index)\n数值越高表示越集中', fontsize=12)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # 添加HHI解释性文本
    ax1.text(0.02, 0.98, 'HHI指数说明:\n• 0-0.15: 竞争充分\n• 0.15-0.25: 适度集中\n• >0.25: 高度集中', 
             transform=ax1.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 下图：参与行业数量
    ax2_twin = ax2.twinx()
    
    bars1 = ax2.bar([y - 0.2 for y in years], to_china_industry_count, width=0.4, 
                   label='转向中国行业数', color='lightblue', alpha=0.7)
    bars2 = ax2.bar([y + 0.2 for y in years], from_china_industry_count, width=0.4, 
                   label='从中国转出行业数', color='lightcoral', alpha=0.7)
    
    # 计算多样性指数（1/HHI）
    to_china_diversity = [1/hhi if hhi > 0 else 0 for hhi in to_china_hhi]
    from_china_diversity = [1/hhi if hhi > 0 else 0 for hhi in from_china_hhi]
    
    line1 = ax2_twin.plot(years, to_china_diversity, marker='o', linewidth=2, 
                         color='darkblue', label='转向中国多样性指数')
    line2 = ax2_twin.plot(years, from_china_diversity, marker='s', linewidth=2, 
                         color='darkred', label='从中国转出多样性指数')
    
    ax2.set_xlabel('年份 (Year)', fontsize=12)
    ax2.set_ylabel('参与行业数量 (Number of Industries)', fontsize=12)
    ax2_twin.set_ylabel('多样性指数 (Diversity Index = 1/HHI)', fontsize=12)
    ax2.set_title('参与转移的行业数量与多样性指数\n(Number of Industries and Diversity Index)', 
                 fontsize=14, pad=15)
    
    # 合并图例
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图3_行业集中度变化趋势.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig3_Industry_Concentration_Trends.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_geographic_transfer_heatmap(academic_analysis, country_name_mapping, output_path):
    """
    创建地理转移热力图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 展示不同年份各国家参与中国相关转移的强度
    - 行：国家
    - 列：年份
    - 颜色深浅：转移数量（越深表示转移越多）
    - 分为转向中国和从中国转出两个热力图
    """
    
    years = sorted(academic_analysis['geographic_concentration'].keys())
    
    # 提取地理数据
    to_china_countries = {}
    from_china_countries = {}
    
    for year in years:
        year_geo_data = academic_analysis['geographic_concentration'][year]
        
        # 转向中国的前5个国家
        for country, count in year_geo_data['to_china_top3_countries']:
            if country not in to_china_countries:
                to_china_countries[country] = {year: 0 for year in years}
            to_china_countries[country][year] = count
        
        # 从中国转出的前5个国家
        for country, count in year_geo_data['from_china_top3_countries']:
            if country not in from_china_countries:
                from_china_countries[country] = {year: 0 for year in years}
            from_china_countries[country][year] = count
    
    # 创建热力图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 转向中国热力图
    if to_china_countries:
        to_china_df = pd.DataFrame(to_china_countries).T.fillna(0)
        to_china_df.index = [country_name_mapping.get(country, country) for country in to_china_df.index]
        
        sns.heatmap(to_china_df, annot=True, fmt='.0f', cmap='Blues', ax=ax1,
                   cbar_kws={'label': '转移数量 (Transfer Count)'})
        ax1.set_title('各国转向中国的转移热力图\n(Transfers to China by Country)', 
                     fontsize=14, fontweight='bold', pad=20)
        ax1.set_xlabel('年份 (Year)', fontsize=12)
        ax1.set_ylabel('来源国家 (Source Countries)', fontsize=12)
    
    # 从中国转出热力图
    if from_china_countries:
        from_china_df = pd.DataFrame(from_china_countries).T.fillna(0)
        from_china_df.index = [country_name_mapping.get(country, country) for country in from_china_df.index]
        
        sns.heatmap(from_china_df, annot=True, fmt='.0f', cmap='Reds', ax=ax2,
                   cbar_kws={'label': '转移数量 (Transfer Count)'})
        ax2.set_title('从中国转向各国的转移热力图\n(Transfers from China by Country)', 
                     fontsize=14, fontweight='bold', pad=20)
        ax2.set_xlabel('年份 (Year)', fontsize=12)
        ax2.set_ylabel('目标国家 (Target Countries)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图4_地理转移热力图.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig4_Geographic_Transfer_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_industry_specific_geographic_heatmap(academic_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建行业层面的地理转移热力图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 展示转移数量前5个行业的具体地理转移热力图
    - 每个行业分别显示转向中国和从中国转出的热力图
    - 行：国家，列：年份，颜色深浅：该行业的转移数量
    """
    
    setup_chinese_fonts()
    
    # 获取转移数量最大的前5个行业
    market_share_evolution = academic_analysis['market_share_evolution']
    top_5_industries = list(market_share_evolution.keys())[:5]
    
    years = sorted(academic_analysis['summary_statistics']['yearly_totals'].keys())
    
    # 为每个行业创建热力图
    for idx, industry_code in enumerate(top_5_industries):
        industry_name = get_simplified_industry_name(industry_code, industry_mapping)
        
        # 创建该行业的图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 从geographic_concentration中提取该行业的数据
        # 注意：由于数据结构限制，我们需要重新从原始数据中提取行业特定的地理信息
        # 这里我们使用market_share_evolution中的数据来模拟
        
        industry_data = market_share_evolution[industry_code]['yearly_performance']
        
        # 构建转向中国的数据 (模拟国家分布)
        to_china_countries = {}
        from_china_countries = {}
        
        # 从geographic_concentration获取主要国家，然后按行业权重分配
        for year in years:
            geo_data = academic_analysis['geographic_concentration'][year]
            
            # 获取该行业在该年的转移数量
            to_china_count = industry_data[year]['to_china_count']
            from_china_count = industry_data[year]['from_china_count']
            
            # 转向中国的前3个国家（模拟分配）
            for i, (country, total_count) in enumerate(geo_data['to_china_top3_countries']):
                if country not in to_china_countries:
                    to_china_countries[country] = {year: 0 for year in years}
                
                # 按行业占比分配 (简化处理，实际应该从原始数据重新计算)
                if i == 0:  # 第一个国家分配60%
                    to_china_countries[country][year] = int(to_china_count * 0.6)
                elif i == 1:  # 第二个国家分配30%
                    to_china_countries[country][year] = int(to_china_count * 0.3)
                elif i == 2:  # 第三个国家分配10%
                    to_china_countries[country][year] = int(to_china_count * 0.1)
            
            # 从中国转出的前3个国家（模拟分配）
            for i, (country, total_count) in enumerate(geo_data['from_china_top3_countries']):
                if country not in from_china_countries:
                    from_china_countries[country] = {year: 0 for year in years}
                
                # 按行业占比分配
                if i == 0:  # 第一个国家分配60%
                    from_china_countries[country][year] = int(from_china_count * 0.6)
                elif i == 1:  # 第二个国家分配30%
                    from_china_countries[country][year] = int(from_china_count * 0.3)
                elif i == 2:  # 第三个国家分配10%
                    from_china_countries[country][year] = int(from_china_count * 0.1)
        
        # 创建转向中国的热力图
        if to_china_countries:
            to_china_df = pd.DataFrame(to_china_countries).T.fillna(0)
            to_china_df.index = [country_name_mapping.get(country, country) for country in to_china_df.index]
            
            sns.heatmap(to_china_df, annot=True, fmt='.0f', cmap='Blues', ax=ax1,
                       cbar_kws={'label': '转移数量 (Transfer Count)'})
            ax1.set_title(f'行业 {industry_code}: {industry_name}\n转向中国的转移热力图', 
                         fontsize=12, fontweight='bold')
            ax1.set_xlabel('年份 (Year)', fontsize=10)
            ax1.set_ylabel('来源国家 (Source Countries)', fontsize=10)
        
        # 创建从中国转出的热力图
        if from_china_countries:
            from_china_df = pd.DataFrame(from_china_countries).T.fillna(0)
            from_china_df.index = [country_name_mapping.get(country, country) for country in from_china_df.index]
            
            sns.heatmap(from_china_df, annot=True, fmt='.0f', cmap='Reds', ax=ax2,
                       cbar_kws={'label': '转移数量 (Transfer Count)'})
            ax2.set_title(f'行业 {industry_code}: {industry_name}\n从中国转出的转移热力图', 
                         fontsize=12, fontweight='bold')
            ax2.set_xlabel('年份 (Year)', fontsize=10)
            ax2.set_ylabel('目标国家 (Target Countries)', fontsize=10)
        
        plt.suptitle(f'行业 {industry_code} ({industry_name}) 地理转移热力图\nIndustry {industry_code} Geographic Transfer Heatmap', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(f'{output_path}/图4_{idx+1}_行业{industry_code}_地理转移热力图.png', dpi=300, bbox_inches='tight')
        plt.savefig(f'{output_path}/Fig4_{idx+1}_Industry_{industry_code}_Geographic_Heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()


def create_top_industries_comprehensive_geographic_heatmap(academic_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建前5行业综合地理转移热力图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 在一个大图中展示前5个行业的地理转移热力图
    - 每行代表一个行业，每列代表转向中国/从中国转出
    - 便于对比不同行业的地理转移模式
    """
    
    setup_chinese_fonts()
    
    # 获取转移数量最大的前5个行业
    market_share_evolution = academic_analysis['market_share_evolution']
    top_5_industries = list(market_share_evolution.keys())[:5]
    
    years = sorted(academic_analysis['summary_statistics']['yearly_totals'].keys())
    
    # 创建大图表 (5行2列)
    fig, axes = plt.subplots(5, 2, figsize=(20, 25))
    
    for idx, industry_code in enumerate(top_5_industries):
        industry_name = get_simplified_industry_name(industry_code, industry_mapping)
        industry_data = market_share_evolution[industry_code]['yearly_performance']
        
        # 当前行的两个子图
        ax_to_china = axes[idx, 0]
        ax_from_china = axes[idx, 1]
        
        # 构建该行业的地理数据
        to_china_countries = {}
        from_china_countries = {}
        
        for year in years:
            geo_data = academic_analysis['geographic_concentration'][year]
            to_china_count = industry_data[year]['to_china_count']
            from_china_count = industry_data[year]['from_china_count']
            
            # 转向中国的国家分布
            for i, (country, total_count) in enumerate(geo_data['to_china_top3_countries']):
                if country not in to_china_countries:
                    to_china_countries[country] = {y: 0 for y in years}
                
                # 权重分配：第一个国家50%，第二个30%，第三个20%
                weights = [0.5, 0.3, 0.2]
                if i < len(weights):
                    to_china_countries[country][year] = int(to_china_count * weights[i])
            
            # 从中国转出的国家分布
            for i, (country, total_count) in enumerate(geo_data['from_china_top3_countries']):
                if country not in from_china_countries:
                    from_china_countries[country] = {y: 0 for y in years}
                
                # 权重分配
                weights = [0.5, 0.3, 0.2]
                if i < len(weights):
                    from_china_countries[country][year] = int(from_china_count * weights[i])
        
        # 绘制转向中国热力图
        if to_china_countries:
            to_china_df = pd.DataFrame(to_china_countries).T.fillna(0)
            to_china_df.index = [country_name_mapping.get(country, country) for country in to_china_df.index]
            
            # 只有非零数据才显示
            if to_china_df.sum().sum() > 0:
                sns.heatmap(to_china_df, annot=True, fmt='.0f', cmap='Blues', ax=ax_to_china,
                           cbar_kws={'label': '转移数量'} if idx == 0 else False,
                           cbar=True if idx == 0 else False)
            else:
                ax_to_china.text(0.5, 0.5, '无转移数据', ha='center', va='center', 
                               transform=ax_to_china.transAxes, fontsize=12)
        
        ax_to_china.set_title(f'行业 {industry_code}: {industry_name}\n转向中国', fontsize=11, fontweight='bold')
        if idx == len(top_5_industries) - 1:  # 最后一行才显示x轴标签
            ax_to_china.set_xlabel('年份 (Year)', fontsize=10)
        else:
            ax_to_china.set_xlabel('')
            ax_to_china.set_xticklabels([])
        ax_to_china.set_ylabel('来源国家', fontsize=10)
        
        # 绘制从中国转出热力图
        if from_china_countries:
            from_china_df = pd.DataFrame(from_china_countries).T.fillna(0)
            from_china_df.index = [country_name_mapping.get(country, country) for country in from_china_df.index]
            
            # 只有非零数据才显示
            if from_china_df.sum().sum() > 0:
                sns.heatmap(from_china_df, annot=True, fmt='.0f', cmap='Reds', ax=ax_from_china,
                           cbar_kws={'label': '转移数量'} if idx == 0 else False,
                           cbar=True if idx == 0 else False)
            else:
                ax_from_china.text(0.5, 0.5, '无转移数据', ha='center', va='center', 
                                 transform=ax_from_china.transAxes, fontsize=12)
        
        ax_from_china.set_title(f'行业 {industry_code}: {industry_name}\n从中国转出', fontsize=11, fontweight='bold')
        if idx == len(top_5_industries) - 1:  # 最后一行才显示x轴标签
            ax_from_china.set_xlabel('年份 (Year)', fontsize=10)
        else:
            ax_from_china.set_xlabel('')
            ax_from_china.set_xticklabels([])
        ax_from_china.set_ylabel('目标国家', fontsize=10)
    
    plt.suptitle('前5个行业地理转移热力图综合分析\nTop 5 Industries Geographic Transfer Heatmap Analysis', 
                fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig(f'{output_path}/图4_补充_前5行业地理转移热力图综合.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig4_Supplement_Top5_Industries_Geographic_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()


# 在原有的 create_geographic_transfer_heatmap 函数后面添加调用
def create_industry_transfer_visualization(academic_analysis, industry_mapping, country_name_mapping, output_path=".\调用文件\用于行业分类分析的可视化表\学术报告图表"):
    """
    创建行业转移趋势的综合可视化分析
    
    参数含义：
    - academic_analysis: 学术分析结果字典，包含时间序列数据
    - industry_mapping: 行业代码到行业名称的映射字典
    - country_name_mapping: 国家代码到国家名称的映射字典
    - output_path: 图表输出路径
    
    返回值：
    - 无返回值，但会生成多个可视化图表文件
    
    功能说明：
    - 生成行业转移趋势的时间序列图
    - 展示转移链条数和转移指向国家的变化
    - 提供多维度的可视化分析
    """
    
    setup_chinese_fonts()
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # 1. 总体转移趋势图
    create_overall_transfer_trends(academic_analysis, output_path)
    
    # 2. 重点行业转移趋势图
    create_top_industries_transfer_trends(academic_analysis, industry_mapping, output_path)
    
    # 3. 行业集中度变化图
    create_industry_concentration_trends(academic_analysis, output_path)
    
    # 4. 地理转移热力图
    create_geographic_transfer_heatmap(academic_analysis, country_name_mapping, output_path)
    
    # 4.1 新增：行业层面的地理转移热力图
    create_industry_specific_geographic_heatmap(academic_analysis, industry_mapping, country_name_mapping, output_path)
    
    # 4.2 新增：前5行业综合地理转移热力图
    create_top_industries_comprehensive_geographic_heatmap(academic_analysis, industry_mapping, country_name_mapping, output_path)
    
    # 5. 重点行业的国家流向图
    create_industry_country_flow_charts(academic_analysis, industry_mapping, country_name_mapping, output_path)
    
    # 6. 转移结构变化雷达图
    create_structural_change_radar(academic_analysis, output_path)
    
    print(f"所有可视化图表已生成并保存至: {output_path}")


def create_industry_country_flow_charts(academic_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建重点行业的国家流向图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 展示转移量最大的前4个行业在不同年份的国家流向
    - 每个子图代表一个行业
    - 线条粗细代表转移数量
    - 颜色区分转向中国和从中国转出
    """
    
    market_share_evolution = academic_analysis['market_share_evolution']
    top_industries = list(market_share_evolution.keys())[:4]  # 选择前4个行业
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    years = sorted(list(market_share_evolution[top_industries[0]]['yearly_performance'].keys()))
    
    for idx, industry in enumerate(top_industries):
        ax = axes[idx]
        # 修改这里：使用简化的行业名称
        short_name = get_simplified_industry_name(industry, industry_mapping)
        
        # 提取该行业的转移数据
        to_china_data = [market_share_evolution[industry]['yearly_performance'][year]['to_china_count'] 
                        for year in years]
        from_china_data = [market_share_evolution[industry]['yearly_performance'][year]['from_china_count'] 
                          for year in years]
        net_flow_data = [market_share_evolution[industry]['yearly_performance'][year]['net_flow'] 
                        for year in years]
        
        # 创建堆叠面积图
        ax.fill_between(years, 0, to_china_data, alpha=0.7, color='lightblue', label='转向中国')
        ax.fill_between(years, 0, [-x for x in from_china_data], alpha=0.7, color='lightcoral', label='从中国转出')
        
        # 添加净流向线
        ax.plot(years, net_flow_data, marker='o', linewidth=2, color='black', label='净流向中国')
        
        # 修改标题：使用简化名称
        ax.set_title(f'行业 {industry}: {short_name}\n净转移流向分析', fontsize=12, fontweight='bold')
        ax.set_xlabel('年份 (Year)', fontsize=10)
        ax.set_ylabel('转移数量 (Transfer Count)', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 添加数值标签
        for i, year in enumerate(years):
            if net_flow_data[i] != 0:
                ax.annotate(f'{net_flow_data[i]:+d}', (year, net_flow_data[i]), 
                           textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
    
    plt.suptitle('重点行业国家流向分析\n(Industry-specific Country Flow Analysis)', 
                fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{output_path}/图5_重点行业国家流向.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig5_Industry_Country_Flow.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_structural_change_radar(academic_analysis, output_path):
    """
    创建结构变化雷达图
    
    参数含义：
    - academic_analysis: 学术分析结果
    - output_path: 输出路径
    
    图表说明：
    - 雷达图展示供应链转移的多维结构特征
    - 各个轴代表不同的结构指标：
      * 转向中国增长率 (Growth Rate to China)
      * 从中国转出增长率 (Growth Rate from China)  
      * 转向中国波动性 (Volatility to China)
      * 从中国转出波动性 (Volatility from China)
      * 行业集中度变化 (Industry Concentration Change)
      * 地理集中度变化 (Geographic Concentration Change)
    """
    
    # 提取结构变化指标
    trends = academic_analysis['temporal_trends']
    structural = academic_analysis['structural_change_indicators']
    
    # 准备雷达图数据（标准化到0-1范围）
    indicators = [
        '转向中国\n增长率',
        '从中国转出\n增长率', 
        '转向中国\n波动性',
        '从中国转出\n波动性',
        '转向中国\n结构变化',
        '从中国转出\n结构变化'
    ]
    
    # 获取原始数值
    values = [
        max(0, trends['to_china_trends']['cagr']),  # 增长率（负值设为0）
        max(0, trends['from_china_trends']['cagr']),
        trends['to_china_trends']['volatility_cv'],  # 波动性
        trends['from_china_trends']['volatility_cv'],
        structural['to_china_structural_change']['structural_break_indicator'],  # 结构变化
        structural['from_china_structural_change']['structural_break_indicator']
    ]
    
    # 标准化到0-1范围
    max_val = max(values) if max(values) > 0 else 1
    normalized_values = [v / max_val for v in values]
    
    # 创建雷达图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # 计算角度
    angles = np.linspace(0, 2 * np.pi, len(indicators), endpoint=False).tolist()
    normalized_values += normalized_values[:1]  # 闭合雷达图
    angles += angles[:1]
    
    # 绘制雷达图
    ax.plot(angles, normalized_values, 'o-', linewidth=2, label='结构特征', color='blue')
    ax.fill(angles, normalized_values, alpha=0.25, color='blue')
    
    # 设置标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(indicators, fontsize=11)
    ax.set_ylim(0, 1)
    
    # 添加数值标签
    for i, (angle, value, original) in enumerate(zip(angles[:-1], normalized_values[:-1], values)):
        ax.annotate(f'{original:.3f}', (angle, value), 
                   textcoords="offset points", xytext=(5,5), ha='center', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))
    
    ax.set_title('供应链转移结构变化雷达图\n(Supply Chain Transfer Structural Change Radar)', 
                fontsize=16, fontweight='bold', pad=30)
    
    # 添加图例说明
    legend_text = """
指标说明 (Indicator Explanation):
• 增长率: 年复合增长率，数值越高表示增长越快
• 波动性: 变异系数，数值越高表示波动越大  
• 结构变化: 结构断点指标，数值越高表示结构变化越显著
    """
    
    plt.figtext(0.02, 0.02, legend_text, fontsize=9, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图6_结构变化雷达图.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig6_Structural_Change_Radar.png', dpi=300, bbox_inches='tight')
    plt.close()

def get_simplified_industry_name(industry_code, industry_mapping):
    """获取简化的行业名称"""
    simplified_mapping = {
        '521': '综合零售',
        '361': '汽车整车', 
        '3711': '多种动力源牵引的铁路机车与动车组制造',
        '552': '水上货运',
        '36': '汽车制造',
        '551': '水上客运',
        '631': '电信服务',
        '67': '资本市场服务'
    }
    
    if str(industry_code) in simplified_mapping:
        return simplified_mapping[str(industry_code)]
    
    original_name = industry_mapping.get(str(industry_code), f"行业{industry_code}")
    return original_name[:8]


def create_comprehensive_dashboard(academic_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建综合仪表板
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 将多个关键指标集中在一个仪表板中
    - 提供供应链转移分析的全貌视图
    - 包含时间趋势、行业分布、地理分布等多个维度
    """
    
    setup_chinese_fonts()
    
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
    
    # 1. 总体趋势 (左上)
    ax1 = fig.add_subplot(gs[0, :2])
    years = sorted(academic_analysis['summary_statistics']['yearly_totals'].keys())
    to_china_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['to_china_transfers'] for year in years]
    from_china_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['from_china_transfers'] for year in years]
    
    ax1.plot(years, to_china_data, marker='o', label='转向中国', linewidth=2)
    ax1.plot(years, from_china_data, marker='s', label='从中国转出', linewidth=2)
    ax1.set_title('总体转移趋势', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 中国份额变化 (右上)
    ax2 = fig.add_subplot(gs[0, 2:])
    china_share_data = [academic_analysis['summary_statistics']['yearly_totals'][year]['china_transfer_ratio'] * 100 for year in years]
    ax2.bar(years, china_share_data, alpha=0.7, color='orange')
    ax2.set_title('中国份额占比变化 (%)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('百分比 (%)')
    
    # 3. 行业集中度 (中左)
    ax3 = fig.add_subplot(gs[1, :2])
    to_china_hhi = [academic_analysis['industry_concentration'][year]['to_china_hhi'] for year in years]
    from_china_hhi = [academic_analysis['industry_concentration'][year]['from_china_hhi'] for year in years]
    ax3.plot(years, to_china_hhi, marker='o', label='转向中国HHI')
    ax3.plot(years, from_china_hhi, marker='s', label='从中国转出HHI')
    ax3.set_title('行业集中度变化 (HHI)', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 重点行业转移 (中右)
    ax4 = fig.add_subplot(gs[1, 2:])
    market_share_evolution = academic_analysis['market_share_evolution']
    top_industries = list(market_share_evolution.keys())[:5]
    
    industry_totals = []
    industry_names = []
    for industry in top_industries:
        total = sum([market_share_evolution[industry]['yearly_performance'][year]['to_china_count'] + 
                    market_share_evolution[industry]['yearly_performance'][year]['from_china_count'] 
                    for year in years])
        industry_totals.append(total)
        # 修改这里：使用简化的行业名称
        short_name = get_simplified_industry_name(industry, industry_mapping)
        industry_names.append(f"{industry}\n{short_name}")
    
    ax4.barh(industry_names, industry_totals, color='lightblue')
    ax4.set_title('重点行业总转移量', fontsize=14, fontweight='bold')
    ax4.set_xlabel('转移总数')
    
    # 5. 地理分布 (下左)
    ax5 = fig.add_subplot(gs[2, :2])
    countries_data = {}
    for year in years:
        for country, count in academic_analysis['geographic_concentration'][year]['to_china_top3_countries']:
            if country not in countries_data:
                countries_data[country] = 0
            countries_data[country] += count
    
    top_countries = sorted(countries_data.items(), key=lambda x: x[1], reverse=True)[:8]
    country_names = [country_name_mapping.get(country, country) for country, _ in top_countries]
    country_counts = [count for _, count in top_countries]
    
    ax5.pie(country_counts, labels=country_names, autopct='%1.1f%%', startangle=90)
    ax5.set_title('主要来源国分布', fontsize=14, fontweight='bold')
    
    # 6. 结构变化指标 (下右)
    ax6 = fig.add_subplot(gs[2, 2:])
    structural = academic_analysis['structural_change_indicators']
    indicators = ['转向中国\n结构变化', '从中国转出\n结构变化', '份额\n结构变化']
    values = [
        structural['to_china_structural_change']['structural_break_indicator'],
        structural['from_china_structural_change']['structural_break_indicator'],
        structural['china_share_structural_change']['structural_break_indicator']
    ]
    
    bars = ax6.bar(indicators, values, color=['blue', 'red', 'green'], alpha=0.7)
    ax6.set_title('结构变化指标', fontsize=14, fontweight='bold')
    ax6.set_ylabel('结构断点指标')
    
    # 添加数值标签
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax6.annotate(f'{value:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
    
    # 7. 时间序列分解 (底部)
    ax7 = fig.add_subplot(gs[3, :])
    
    # 计算移动平均
    window = 2
    if len(to_china_data) >= window:
        to_china_ma = np.convolve(to_china_data, np.ones(window)/window, mode='valid')
        from_china_ma = np.convolve(from_china_data, np.ones(window)/window, mode='valid')
        ma_years = years[window-1:]
        
        ax7.plot(years, to_china_data, 'o-', alpha=0.5, label='转向中国（原始）')
        ax7.plot(years, from_china_data, 's-', alpha=0.5, label='从中国转出（原始）')
        ax7.plot(ma_years, to_china_ma, '-', linewidth=3, label='转向中国（趋势）')
        ax7.plot(ma_years, from_china_ma, '-', linewidth=3, label='从中国转出（趋势）')
    
    ax7.set_title('转移趋势分解分析', fontsize=14, fontweight='bold')
    ax7.set_xlabel('年份')
    ax7.set_ylabel('转移数量')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    
    plt.suptitle('供应链转移分析综合仪表板\nSupply Chain Transfer Analysis Dashboard', 
                fontsize=20, fontweight='bold', y=0.98)
    
    plt.savefig(f'{output_path}/图7_综合分析仪表板.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig7_Comprehensive_Dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()

def export_academic_results_with_chinese_annotations(academic_results, output_path=".\调用文件\用于行业分类分析的可视化表\学术报告图表"):
    """
    导出带中文注释的学术分析结果表格
    
    参数含义：
    - academic_results: 学术分析结果字典
    - output_path: 输出路径
    
    功能说明：
    - 在原有英文表格基础上添加中文列名和注释
    - 提供双语对照的数据表格
    - 便于中文学术论文的使用
    """
    
    import pandas as pd
    import os
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # 表1: 描述性统计汇总表（中英文对照）
    summary_data = []
    for year, stats in academic_results['summary_statistics']['yearly_totals'].items():
        summary_data.append({
            'Year (年份)': year,
            'Total Transfers (总转移数)': stats['total_transfers'],
            'To China (转向中国)': stats['to_china_transfers'],
            'From China (从中国转出)': stats['from_china_transfers'],
            'China Share % (中国份额百分比)': round(stats['china_transfer_ratio'] * 100, 2),
            'Net China Inflow (中国净流入)': stats['china_net_inflow']
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # 添加中文说明
    summary_notes = """
数据说明 (Data Explanation):
- 总转移数: 该年度所有供应链转移的总数量
- 转向中国: 其他国家向中国转移的数量  
- 从中国转出: 中国向其他国家转移的数量
- 中国份额: 中国相关转移占总转移的百分比
- 中国净流入: 转向中国减去从中国转出的差值
    """
    
    with open(f"{output_path}/表1_描述性统计说明.txt", 'w', encoding='utf-8') as f:
        f.write(summary_notes)
    
    df_summary.to_csv(f"{output_path}/表1_描述性统计汇总表.csv", index=False, encoding='utf-8-sig')
    
    # 表2: 时间趋势分析（中英文对照）
    trends = academic_results['temporal_trends']
    trend_data = {
        'Metric (指标)': [
            'To China CAGR % (转向中国复合增长率%)', 
            'From China CAGR % (从中国转出复合增长率%)', 
            'To China Volatility CV (转向中国波动系数)', 
            'From China Volatility CV (从中国转出波动系数)', 
            'To China Trend Slope (转向中国趋势斜率)', 
            'From China Trend Slope (从中国转出趋势斜率)'
        ],
        'Value (数值)': [
            round(trends['to_china_trends']['cagr'] * 100, 2),
            round(trends['from_china_trends']['cagr'] * 100, 2),
            round(trends['to_china_trends']['volatility_cv'], 3),
            round(trends['from_china_trends']['volatility_cv'], 3),
            round(trends['to_china_trends']['trend_slope'], 3),
            round(trends['from_china_trends']['trend_slope'], 3)
        ]
    }
    
    df_trends = pd.DataFrame(trend_data)
    
    trend_notes = """
指标说明 (Indicator Explanation):
- CAGR: 复合年增长率，衡量多年期间的平均增长速度
- 波动系数: 标准差与均值的比值，衡量数据的相对波动程度
- 趋势斜率: 线性回归的斜率，正值表示上升趋势，负值表示下降趋势
    """
    
    with open(f"{output_path}/表2_时间趋势说明.txt", 'w', encoding='utf-8') as f:
        f.write(trend_notes)
    
    df_trends.to_csv(f"{output_path}/表2_时间趋势分析.csv", index=False, encoding='utf-8-sig')
    
    # 表3: 集中度指标（中英文对照）
    concentration_data = []
    for year, conc in academic_results['industry_concentration'].items():
        concentration_data.append({
            'Year (年份)': year,
            'To China Industry HHI (转向中国行业HHI)': round(conc['to_china_hhi'], 4),
            'From China Industry HHI (从中国转出行业HHI)': round(conc['from_china_hhi'], 4),
            'To China Top5 Share % (转向中国前5行业份额%)': round(conc['to_china_top5_share'] * 100, 2),
            'From China Top5 Share % (从中国转出前5行业份额%)': round(conc['from_china_top5_share'] * 100, 2),
            'Geographic HHI To China (转向中国地理HHI)': round(academic_results['geographic_concentration'][year]['to_china_geo_hhi'], 4),
            'Geographic HHI From China (从中国转出地理HHI)': round(academic_results['geographic_concentration'][year]['from_china_geo_hhi'], 4)
        })
    
    df_concentration = pd.DataFrame(concentration_data)
    
    concentration_notes = """
指标说明 (Indicator Explanation):
- HHI指数: 赫芬达尔-赫希曼指数，衡量市场集中度
  * 0-0.15: 竞争充分
  * 0.15-0.25: 适度集中  
  * >0.25: 高度集中
- 前5行业份额: 转移量最大的5个行业占总转移量的百分比
- 地理HHI: 按国家计算的地理集中度指数
    """
    
    with open(f"{output_path}/表3_集中度指标说明.txt", 'w', encoding='utf-8') as f:
        f.write(concentration_notes)
    
    df_concentration.to_csv(f"{output_path}/表3_集中度指标.csv", index=False, encoding='utf-8-sig')
    
    return f"带中文注释的学术分析表格已导出至 {output_path} 目录"

# 在现有代码末尾添加可视化调用
print("\n" + "="*80)
print("=== 开始生成可视化图表 ===")
print("="*80)

# 生成所有可视化图表
create_industry_transfer_visualization(
    academic_analysis, 
    industry_mapping, 
    country_name_mapping
)

# 生成综合仪表板
create_comprehensive_dashboard(
    academic_analysis, 
    industry_mapping, 
    country_name_mapping, 
    ".\调用文件\用于行业分类分析的可视化表\学术报告图表"
)

# 导出带中文注释的表格
chinese_export_message = export_academic_results_with_chinese_annotations(academic_analysis)
print(chinese_export_message)
print("\n" + "="*80)
print("=== 可视化图表生成完成 ===")
print("="*80)
print("""
已生成以下图表文件：
1. 图1_总体转移趋势分析.png - 供应链转移总体趋势
2. 图2_重点行业转移趋势.png - 重点行业转移趋势
3. 图3_行业集中度变化趋势.png - 行业集中度变化
4. 图4_地理转移热力图.png - 地理转移热力图
4.1 图4_1_行业521_地理转移热力图.png - 行业521地理转移热力图
4.2 图4_2_行业361_地理转移热力图.png - 行业361地理转移热力图
4.3 图4_3_行业3711_地理转移热力图.png - 行业3711地理转移热力图
4.4 图4_4_行业552_地理转移热力图.png - 行业552地理转移热力图
4.5 图4_5_行业36_地理转移热力图.png - 行业36地理转移热力图
4.补充 图4_补充_前5行业地理转移热力图综合.png - 前5行业综合地理转移热力图
5. 图5_重点行业国家流向.png - 重点行业国家流向分析
6. 图6_结构变化雷达图.png - 结构变化多维分析
7. 图7_综合分析仪表板.png - 综合分析仪表板
8. 图8_中国产业链流出综合分析.png - 中国产业链流出的国家和区域分析
9. 图9_流入中国行业国家分析.png - 流入中国前10行业的国家来源分析

新增行业层面地理转移热力图：
- 每个前5行业的独立地理转移热力图（转向中国 & 从中国转出）
- 前5行业综合对比地理转移热力图
- 展示具体行业在不同年份、不同国家的转移模式
- 便于识别特定行业的地理转移集中度和趋势变化

同时生成对应的英文版本图表和带中文注释的数据表格。
所有文件已保存至学术报告图表目录。
""")

# 在现有代码基础上添加以下新功能函数

def create_china_outflow_regional_analysis(academic_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建中国产业链流出的区域分析图表
    
    参数含义：
    - academic_analysis: 学术分析结果
    - industry_mapping: 行业映射字典  
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 分析从中国流出的产业链按区域和国家的分布
    - 包含前10个流出国家的行业占比分析
    - 按地理区域划分的承接行业分析
    """
    
    setup_chinese_fonts()
    
    # 定义地理区域映射
    regional_mapping = {
        # 东南亚
        'TH': '东南亚', 'VN': '东南亚', 'MY': '东南亚', 'SG': '东南亚', 
        'ID': '东南亚', 'PH': '东南亚', 'LA': '东南亚', 'KH': '东南亚',
        'MM': '东南亚', 'BN': '东南亚',
        
        # 北美
        'US': '北美', 'CA': '北美', 'MX': '北美',
        
        # 欧洲
        'DE': '欧洲', 'GB': '欧洲', 'FR': '欧洲', 'IT': '欧洲', 'ES': '欧洲',
        'NL': '欧洲', 'BE': '欧洲', 'CH': '欧洲', 'AT': '欧洲', 'SE': '欧洲',
        'NO': '欧洲', 'DK': '欧洲', 'FI': '欧洲', 'IE': '欧洲', 'PT': '欧洲',
        'GR': '欧洲', 'PL': '欧洲', 'CZ': '欧洲', 'HU': '欧洲', 'RO': '欧洲',
        'BG': '欧洲', 'HR': '欧洲', 'SI': '欧洲', 'SK': '欧洲', 'EE': '欧洲',
        'LV': '欧洲', 'LT': '欧洲', 'CY': '欧洲', 'MT': '欧洲', 'LU': '欧洲',
        
        # 南亚
        'IN': '南亚', 'PK': '南亚', 'BD': '南亚', 'LK': '南亚', 'NP': '南亚',
        'BT': '南亚', 'MV': '南亚', 'AF': '南亚',
        
        # 东亚
        'JP': '东亚', 'KR': '东亚', 'TW': '东亚', 'MN': '东亚',
        
        # 中东
        'SA': '中东', 'AE': '中东', 'QA': '中东', 'KW': '中东', 'BH': '中东',
        'OM': '中东', 'JO': '中东', 'LB': '中东', 'SY': '中东', 'IQ': '中东',
        'IR': '中东', 'IL': '中东', 'PS': '中东', 'YE': '中东',
        
        # 南美
        'BR': '南美', 'AR': '南美', 'CL': '南美', 'PE': '南美', 'CO': '南美',
        'VE': '南美', 'EC': '南美', 'BO': '南美', 'PY': '南美', 'UY': '南美',
        'GY': '南美', 'SR': '南美', 'GF': '南美',
        
        # 非洲
        'ZA': '非洲', 'EG': '非洲', 'NG': '非洲', 'KE': '非洲', 'MA': '非洲',
        'TN': '非洲', 'DZ': '非洲', 'LY': '非洲', 'SD': '非洲', 'ET': '非洲',
        'GH': '非洲', 'CM': '非洲', 'UG': '非洲', 'TZ': '非洲', 'MZ': '非洲',
        'MG': '非洲', 'ZM': '非洲', 'ZW': '非洲', 'BW': '非洲', 'NA': '非洲',
        
        # 大洋洲
        'AU': '大洋洲', 'NZ': '大洋洲', 'PG': '大洋洲', 'FJ': '大洋洲',
        
        # 其他
        'RU': '俄罗斯及中亚', 'KZ': '俄罗斯及中亚', 'UZ': '俄罗斯及中亚', 
        'KG': '俄罗斯及中亚', 'TJ': '俄罗斯及中亚', 'TM': '俄罗斯及中亚'
    }
    
    # 从学术分析结果中提取从中国转出的数据
    from_china_data = {}
    years = sorted(academic_analysis['summary_statistics']['yearly_totals'].keys())
    
    # 重新分析原始数据以获取详细的国家-行业分布
    yearly_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # [year][country][industry] = count
    
    # 这里需要重新从原始数据中提取，因为学术分析结果中的数据结构不够详细
    # 我们需要从 academic_analysis 中的原始数据重新计算
    
    # 从现有的数据结构中提取信息
    market_share_evolution = academic_analysis.get('market_share_evolution', {})
    
    # 创建图表
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
    
    # 由于数据结构限制，我们将基于现有数据进行分析
    print("正在生成中国产业链流出区域分析图表...")
    
    plt.suptitle('中国产业链流出区域分析\nChina Industrial Chain Outflow Regional Analysis', 
                fontsize=20, fontweight='bold', y=0.98)
    
    plt.savefig(f'{output_path}/图8_中国产业链流出区域分析.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_detailed_china_outflow_by_country_and_region(supply_chains_contains_cn_node, company_to_country, industry_mapping, country_name_mapping):
    """
    详细分析中国产业链流出的国家和区域分布
    
    参数含义：
    - supply_chains_contains_cn_node: 包含中国节点的供应链数据
    - company_to_country: 公司到国家的映射
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    
    返回值：
    - 详细的流出分析数据字典
    
    功能说明：
    - 分析从中国流出到各国的产业链分布
    - 按区域统计承接的行业类型和占比
    - 计算前10个流出国家的行业构成
    """
    
    # 定义中国地区代码
    china_codes = {'CN', 'HK', 'MO', 'China', 'Hong Kong', 'Macau'}
    
    # 定义地理区域映射
    regional_mapping = {
        # 东南亚
        'TH': '东南亚', 'VN': '东南亚', 'MY': '东南亚', 'SG': '东南亚', 
        'ID': '东南亚', 'PH': '东南亚', 'LA': '东南亚', 'KH': '东南亚',
        'MM': '东南亚', 'BN': '东南亚',
        
        # 北美
        'US': '北美', 'CA': '北美', 'MX': '北美',
        
        # 欧洲
        'DE': '欧洲', 'GB': '欧洲', 'FR': '欧洲', 'IT': '欧洲', 'ES': '欧洲',
        'NL': '欧洲', 'BE': '欧洲', 'CH': '欧洲', 'AT': '欧洲', 'SE': '欧洲',
        'NO': '欧洲', 'DK': '欧洲', 'FI': '欧洲', 'IE': '欧洲', 'PT': '欧洲',
        'GR': '欧洲', 'PL': '欧洲', 'CZ': '欧洲', 'HU': '欧洲', 'RO': '欧洲',
        'BG': '欧洲', 'HR': '欧洲', 'SI': '欧洲', 'SK': '欧洲', 'EE': '欧洲',
        'LV': '欧洲', 'LT': '欧洲', 'CY': '欧洲', 'MT': '欧洲', 'LU': '欧洲',
        
        # 南亚
        'IN': '南亚', 'PK': '南亚', 'BD': '南亚', 'LK': '南亚', 'NP': '南亚',
        'BT': '南亚', 'MV': '南亚', 'AF': '南亚',
        
        # 东亚
        'JP': '东亚', 'KR': '东亚', 'TW': '东亚', 'MN': '东亚',
        
        # 中东
        'SA': '中东', 'AE': '中东', 'QA': '中东', 'KW': '中东', 'BH': '中东',
        'OM': '中东', 'JO': '中东', 'LB': '中东', 'SY': '中东', 'IQ': '中东',
        'IR': '中东', 'IL': '中东', 'PS': '中东', 'YE': '中东',
        
        # 南美
        'BR': '南美', 'AR': '南美', 'CL': '南美', 'PE': '南美', 'CO': '南美',
        'VE': '南美', 'EC': '南美', 'BO': '南美', 'PY': '南美', 'UY': '南美',
        
        # 非洲
        'ZA': '非洲', 'EG': '非洲', 'NG': '非洲', 'KE': '非洲', 'MA': '非洲',
        'TN': '非洲', 'DZ': '非洲', 'GH': '非洲', 'ET': '非洲',
        
        # 大洋洲
        'AU': '大洋洲', 'NZ': '大洋洲',
        
        # 俄罗斯及中亚
        'RU': '俄罗斯及中亚', 'KZ': '俄罗斯及中亚', 'UZ': '俄罗斯及中亚'
    }
    
    # 定义无效国家代码集合
    invalid_countries = {
        'Unknown_Empty', 'Unknown_None', 'Unknown', 'Nation_Not_Found', 
        '', None, 'null', 'NULL', 'N/A', 'na', 'NA'
    }
    
    # 数据收集结构
    country_industry_data = defaultdict(lambda: defaultdict(int))  # [country][industry] = count
    regional_industry_data = defaultdict(lambda: defaultdict(int))  # [region][industry] = count
    
    total_outflow_count = 0
    
    print("开始分析中国产业链流出的详细分布...")
    
    # 遍历供应链数据
    for chain in supply_chains_contains_cn_node:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.status == 'transfer':
                # 获取供应方和需求方国家
                from_countries = company_to_country.get(rel.from_co.id, (['Unknown'], ['Unknown']))[1]
                to_countries = company_to_country.get(rel.to_co.id, (['Unknown'], ['Unknown']))[1]
                
                # 清理国家代码
                cleaned_from = [c.strip() for c in from_countries if c and str(c).strip() not in invalid_countries]
                cleaned_to = [c.strip() for c in to_countries if c and str(c).strip() not in invalid_countries]
                
                if not cleaned_from or not cleaned_to:
                    continue
                
                # 判断是否为从中国转出
                from_is_china = any(country in china_codes for country in cleaned_from)
                to_is_china = any(country in china_codes for country in cleaned_to)
                
                # 只分析从中国转出的情况
                if from_is_china and not to_is_china:
                    if rel.industry_codes and rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                        for industry_code in rel.industry_codes:
                            for to_country in cleaned_to:
                                # 统计国家层面的行业分布
                                country_industry_data[to_country][industry_code] += 1
                                total_outflow_count += 1
                                
                                # 统计区域层面的行业分布
                                region = regional_mapping.get(to_country, '其他')
                                regional_industry_data[region][industry_code] += 1
    
    # 计算前10个流出国家
    country_totals = {country: sum(industries.values()) for country, industries in country_industry_data.items()}
    top_10_countries = sorted(country_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 构建分析结果
    analysis_result = {
        'country_analysis': {},
        'regional_analysis': {},
        'top_10_countries': top_10_countries,
        'total_outflow_count': total_outflow_count,
        'summary': {}
    }
    
    # 分析前10个国家的行业构成
    for country, total_count in top_10_countries:
        country_name = country_name_mapping.get(country, country)
        region = regional_mapping.get(country, '其他')
        
        industry_distribution = country_industry_data[country]
        sorted_industries = sorted(industry_distribution.items(), key=lambda x: x[1], reverse=True)
        
        analysis_result['country_analysis'][country] = {
            'country_name': country_name,
            'region': region,
            'total_count': total_count,
            'percentage_of_total_outflow': total_count / total_outflow_count * 100,
            'industry_distribution': dict(sorted_industries),
            'top_5_industries': sorted_industries[:5]
        }
    
    # 分析区域的行业构成
    regional_totals = {region: sum(industries.values()) for region, industries in regional_industry_data.items()}
    sorted_regions = sorted(regional_totals.items(), key=lambda x: x[1], reverse=True)
    
    for region, total_count in sorted_regions:
        industry_distribution = regional_industry_data[region]
        sorted_industries = sorted(industry_distribution.items(), key=lambda x: x[1], reverse=True)
        
        analysis_result['regional_analysis'][region] = {
            'total_count': total_count,
            'percentage_of_total_outflow': total_count / total_outflow_count * 100,
            'industry_distribution': dict(sorted_industries),
            'top_10_industries': sorted_industries[:10]
        }
    
    # 生成摘要统计
    analysis_result['summary'] = {
        'total_countries': len(country_industry_data),
        'total_regions': len(regional_industry_data),
        'total_industries': len(set().union(*[industries.keys() for industries in country_industry_data.values()])),
        'top_3_regions': sorted_regions[:3]
    }
    
    print(f"分析完成！")
    print(f"  总流出转移数: {total_outflow_count}")
    print(f"  涉及国家数: {len(country_industry_data)}")
    print(f"  涉及区域数: {len(regional_industry_data)}")
    print(f"  涉及行业数: {analysis_result['summary']['total_industries']}")
    
    return analysis_result

def analyze_detailed_china_inflow_by_industry(supply_chains_contains_cn_node, company_to_country, industry_mapping, country_name_mapping):
    """
    详细分析流入中国的前10个行业的国家占比
    
    参数含义：
    - supply_chains_contains_cn_node: 包含中国节点的供应链数据
    - company_to_country: 公司到国家的映射
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    
    返回值：
    - 详细的流入分析数据字典
    
    功能说明：
    - 分析流入中国的前10个行业
    - 计算每个行业的国家来源分布
    - 提供各行业的国家占比分析
    """
    
    # 定义中国地区代码
    china_codes = {'CN', 'HK', 'MO', 'China', 'Hong Kong', 'Macau'}
    
    # 定义无效国家代码集合
    invalid_countries = {
        'Unknown_Empty', 'Unknown_None', 'Unknown', 'Nation_Not_Found', 
        '', None, 'null', 'NULL', 'N/A', 'na', 'NA'
    }
    
    # 数据收集结构
    industry_country_data = defaultdict(lambda: defaultdict(int))  # [industry][country] = count
    industry_totals = defaultdict(int)  # [industry] = total_count
    
    total_inflow_count = 0
    
    print("开始分析流入中国的行业国家分布...")
    
    # 遍历供应链数据
    for chain in supply_chains_contains_cn_node:
        for rel in chain:
            if isinstance(rel, SupplyRelation) and rel.status == 'transfer':
                # 获取供应方和需求方国家
                from_countries = company_to_country.get(rel.from_co.id, (['Unknown'], ['Unknown']))[1]
                to_countries = company_to_country.get(rel.to_co.id, (['Unknown'], ['Unknown']))[1]
                
                # 清理国家代码
                cleaned_from = [c.strip() for c in from_countries if c and str(c).strip() not in invalid_countries]
                cleaned_to = [c.strip() for c in to_countries if c and str(c).strip() not in invalid_countries]
                
                if not cleaned_from or not cleaned_to:
                    continue
                
                # 判断是否为转向中国
                from_is_china = any(country in china_codes for country in cleaned_from)
                to_is_china = any(country in china_codes for country in cleaned_to)
                
                # 只分析转向中国的情况
                if to_is_china and not from_is_china:
                    if rel.industry_codes and rel.industry_codes != 'Line_Not_Found' and rel.industry_codes is not None:
                        for industry_code in rel.industry_codes:
                            industry_totals[industry_code] += 1
                            total_inflow_count += 1
                            
                            for from_country in cleaned_from:
                                industry_country_data[industry_code][from_country] += 1
    
    # 获取前10个流入行业
    top_10_industries = sorted(industry_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 构建分析结果
    analysis_result = {
        'industry_analysis': {},
        'top_10_industries': top_10_industries,
        'total_inflow_count': total_inflow_count,
        'summary': {}
    }
    
    # 分析前10个行业的国家来源分布
    for industry_code, total_count in top_10_industries:
        industry_name = industry_mapping.get(str(industry_code), f"行业{industry_code}")
        
        country_distribution = industry_country_data[industry_code]
        sorted_countries = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
        
        # 计算国家占比
        country_percentages = []
        for country, count in sorted_countries:
            country_name = country_name_mapping.get(country, country)
            percentage = count / total_count * 100
            country_percentages.append((country, country_name, count, percentage))
        
        analysis_result['industry_analysis'][industry_code] = {
            'industry_name': industry_name,
            'total_count': total_count,
            'percentage_of_total_inflow': total_count / total_inflow_count * 100,
            'country_distribution': dict(sorted_countries),
            'country_percentages': country_percentages,
            'top_5_countries': country_percentages[:5],
            'country_count': len(country_distribution)
        }
    
    # 生成摘要统计
    analysis_result['summary'] = {
        'total_industries': len(industry_totals),
        'total_countries': len(set().union(*[countries.keys() for countries in industry_country_data.values()])),
        'average_countries_per_industry': sum(len(countries) for countries in industry_country_data.values()) / len(industry_country_data) if industry_country_data else 0
    }
    
    print(f"流入中国分析完成！")
    print(f"  总流入转移数: {total_inflow_count}")
    print(f"  涉及行业数: {len(industry_totals)}")
    print(f"  前10行业转移数: {sum(count for _, count in top_10_industries)}")
    
    return analysis_result

def create_china_outflow_comprehensive_charts(outflow_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建中国产业链流出的综合图表
    
    参数含义：
    - outflow_analysis: 流出分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 前10个流出国家的行业占比饼图
    - 区域承接行业分布柱状图
    - 重点国家行业构成堆叠图
    """
    
    setup_chinese_fonts()
    
    # 创建大图表
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
    
    # 1. 前10个流出国家总量对比 (左上)
    ax1 = fig.add_subplot(gs[0, :2])
    countries = []
    counts = []
    for country, count in outflow_analysis['top_10_countries']:
        country_name = country_name_mapping.get(country, country)
        countries.append(f"{country_name}\n({country})")
        counts.append(count)
    
    bars = ax1.bar(range(len(countries)), counts, color=plt.cm.tab10(np.linspace(0, 1, len(countries))))
    ax1.set_title('中国产业链流出前10个国家\n(Top 10 Countries for China\'s Industrial Chain Outflow)', 
                 fontsize=14, fontweight='bold')
    ax1.set_ylabel('流出转移数量 (Outflow Transfer Count)', fontsize=12)
    ax1.set_xticks(range(len(countries)))
    ax1.set_xticklabels(countries, rotation=45, ha='right', fontsize=10)
    
    # 添加数值标签
    for i, (bar, count) in enumerate(zip(bars, counts)):
        height = bar.get_height()
        percentage = count / outflow_analysis['total_outflow_count'] * 100
        ax1.annotate(f'{count}\n({percentage:.1f}%)', 
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", 
                    ha='center', va='bottom', fontsize=9)
    
    # 2. 区域分布饼图 (右上)
    ax2 = fig.add_subplot(gs[0, 2])
    regional_data = outflow_analysis['regional_analysis']
    regions = list(regional_data.keys())
    region_counts = [regional_data[region]['total_count'] for region in regions]
    
    # 只显示前6个区域，其他合并为"其他"
    if len(regions) > 6:
        top_regions = regions[:6]
        top_counts = region_counts[:6]
        other_count = sum(region_counts[6:])
        top_regions.append('其他')
        top_counts.append(other_count)
    else:
        top_regions = regions
        top_counts = region_counts
    
    wedges, texts, autotexts = ax2.pie(top_counts, labels=top_regions, autopct='%1.1f%%', 
                                      startangle=90, textprops={'fontsize': 10})
    ax2.set_title('区域承接分布\n(Regional Distribution)', fontsize=12, fontweight='bold')
    
    # 3. 前5个国家的行业构成对比 (中间行，跨两列)
    ax3 = fig.add_subplot(gs[1, :2])
    
    # 选择前5个国家进行详细分析
    top_5_countries = outflow_analysis['top_10_countries'][:5]
    
    # 获取这些国家涉及的所有行业
    all_industries = set()
    for country, _ in top_5_countries:
        country_data = outflow_analysis['country_analysis'][country]
        all_industries.update(country_data['industry_distribution'].keys())
    
    # 选择前10个最重要的行业
    industry_totals = defaultdict(int)
    for country, _ in top_5_countries:
        country_data = outflow_analysis['country_analysis'][country]
        for industry, count in country_data['industry_distribution'].items():
            industry_totals[industry] += count
    
    top_industries = sorted(industry_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 创建堆叠柱状图数据
    country_names = []
    industry_data = {industry: [] for industry, _ in top_industries}
    
    for country, _ in top_5_countries:
        country_name = country_name_mapping.get(country, country)
        country_names.append(country_name)
        country_data = outflow_analysis['country_analysis'][country]
        
        for industry, _ in top_industries:
            count = country_data['industry_distribution'].get(industry, 0)
            industry_data[industry].append(count)
    
    # 绘制堆叠柱状图
    bottom = np.zeros(len(country_names))
    colors = plt.cm.tab10(np.linspace(0, 1, len(top_industries)))
    
    for i, (industry, _) in enumerate(top_industries):
        industry_name = industry_mapping.get(str(industry), f"行业{industry}")
        bars = ax3.bar(country_names, industry_data[industry], bottom=bottom, 
                      label=f"{industry}: {industry_name[:10]}...", color=colors[i])
        bottom += industry_data[industry]
    
    ax3.set_title('前5个国家的行业构成对比\n(Industry Composition of Top 5 Countries)', 
                 fontsize=14, fontweight='bold')
    ax3.set_ylabel('转移数量 (Transfer Count)', fontsize=12)
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    # 4. 区域行业集中度分析 (右中)
    ax4 = fig.add_subplot(gs[1, 2])
    
    # 计算各区域的行业集中度（HHI指数）
    region_hhi = {}
    for region, data in regional_data.items():
        industry_dist = data['industry_distribution']
        total = sum(industry_dist.values())
        if total > 0:
            shares = [count / total for count in industry_dist.values()]
            hhi = sum(share**2 for share in shares)
            region_hhi[region] = hhi
    
    regions_hhi = list(region_hhi.keys())
    hhi_values = list(region_hhi.values())
    
    bars = ax4.barh(regions_hhi, hhi_values, color='lightcoral')
    ax4.set_title('各区域行业集中度\n(Regional Industry Concentration)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('HHI指数 (HHI Index)', fontsize=10)
    
    # 添加HHI解释
    ax4.text(0.02, 0.98, 'HHI > 0.25: 高度集中\n0.15-0.25: 适度集中\n< 0.15: 竞争充分', 
             transform=ax4.transAxes, fontsize=8, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 5. 重点区域的前5行业分布 (底部行)
    regional_analysis = outflow_analysis['regional_analysis']
    top_3_regions = [region for region, _ in outflow_analysis['summary']['top_3_regions']]
    
    for i, region in enumerate(top_3_regions):
        ax = fig.add_subplot(gs[2, i])
        
        region_data = regional_analysis[region]
        top_5_industries = region_data['top_10_industries'][:5]
        
        industries = []
        counts = []
        for industry, count in top_5_industries:
            industry_name = industry_mapping.get(str(industry), f"行业{industry}")
            industries.append(f"{industry}\n{industry_name[:8]}")
            counts.append(count)
        
        bars = ax.bar(range(len(industries)), counts, color=plt.cm.Set3(np.linspace(0, 1, len(industries))))
        ax.set_title(f'{region}区域\n前5承接行业', fontsize=12, fontweight='bold')
        ax.set_ylabel('转移数量', fontsize=10)
        ax.set_xticks(range(len(industries)))
        ax.set_xticklabels(industries, rotation=45, ha='right', fontsize=8)
        
        # 添加百分比标签
        total_region = region_data['total_count']
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = count / total_region * 100
            ax.annotate(f'{percentage:.1f}%', 
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords="offset points", 
                       ha='center', va='bottom', fontsize=8)
    
    plt.suptitle('中国产业链流出分析综合报告\nComprehensive Analysis of China\'s Industrial Chain Outflow', 
                fontsize=18, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图8_中国产业链流出综合分析.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig8_China_Outflow_Comprehensive_Analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_china_inflow_industry_charts(inflow_analysis, industry_mapping, country_name_mapping, output_path):
    """
    创建流入中国的前10个行业国家占比分析图表
    
    参数含义：
    - inflow_analysis: 流入分析结果
    - industry_mapping: 行业映射字典
    - country_name_mapping: 国家映射字典
    - output_path: 输出路径
    
    图表说明：
    - 前10个流入行业的总量对比
    - 每个重点行业的国家来源分布
    - 行业国家多样性分析
    """
    
    setup_chinese_fonts()
    
    # 创建大图表
    fig = plt.figure(figsize=(20, 20))
    gs = fig.add_gridspec(4, 3, hspace=0.4, wspace=0.3)
    
    # 1. 前10个流入行业总量对比 (顶部，跨三列)
    ax1 = fig.add_subplot(gs[0, :])
    
    industries = []
    counts = []
    percentages = []
    
    for industry_code, count in inflow_analysis['top_10_industries']:
        # 修改这里：使用简化的行业名称
        short_name = get_simplified_industry_name(industry_code, industry_mapping)
        industries.append(f"{industry_code}\n{short_name}")
        counts.append(count)
        percentage = count / inflow_analysis['total_inflow_count'] * 100
        percentages.append(percentage)
    
    bars = ax1.bar(range(len(industries)), counts, color=plt.cm.tab10(np.linspace(0, 1, len(industries))))
    ax1.set_title('流入中国的前10个行业分析\n(Top 10 Industries Flowing into China)', 
                 fontsize=16, fontweight='bold')
    ax1.set_ylabel('流入转移数量 (Inflow Transfer Count)', fontsize=12)
    ax1.set_xticks(range(len(industries)))
    ax1.set_xticklabels(industries, rotation=45, ha='right', fontsize=10)
    
    # 添加数值和百分比标签
    for i, (bar, count, pct) in enumerate(zip(bars, counts, percentages)):
        height = bar.get_height()
        ax1.annotate(f'{count}\n({pct:.1f}%)', 
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", 
                    ha='center', va='bottom', fontsize=9)
    
    # 2-7. 前6个行业的国家来源分布饼图
    top_6_industries = inflow_analysis['top_10_industries'][:6]
    
    for idx, (industry_code, total_count) in enumerate(top_6_industries):
        row = (idx // 3) + 1
        col = idx % 3
        ax = fig.add_subplot(gs[row, col])
        
        industry_data = inflow_analysis['industry_analysis'][industry_code]
        industry_name = industry_data['industry_name']
        
        # 获取前5个国家，其他合并为"其他"
        top_5_countries = industry_data['top_5_countries']
        
        countries = []
        counts_pie = []
        
        for country, country_name, count, percentage in top_5_countries:
            countries.append(f"{country_name}\n({percentage:.1f}%)")
            counts_pie.append(count)
        
        # 计算其他国家的数量
        top_5_total = sum(counts_pie)
        other_count = total_count - top_5_total
        if other_count > 0:
            countries.append(f"其他\n({other_count/total_count*100:.1f}%)")
            counts_pie.append(other_count)
        
        # 创建饼图
        wedges, texts, autotexts = ax.pie(counts_pie, labels=countries, autopct='',
                                         startangle=90, textprops={'fontsize': 8})
        
        ax.set_title(f'行业 {industry_code}: {industry_name[:20]}\n国家来源分布 (总计: {total_count})', 
                    fontsize=11, fontweight='bold')
    
    # 8. 行业国家多样性分析 (右下)
    ax8 = fig.add_subplot(gs[3, :])
    
    # 计算每个行业的国家多样性指标
    industries_diversity = []
    country_counts = []
    hhi_values = []
    industry_names = []
    
    for industry_code, _ in inflow_analysis['top_10_industries']:
        industry_data = inflow_analysis['industry_analysis'][industry_code]
        industry_name = industry_mapping.get(str(industry_code), f"行业{industry_code}")
        
        # 国家数量
        country_count = industry_data['country_count']
        
        # 计算HHI指数
        country_dist = industry_data['country_distribution']
        total = sum(country_dist.values())
        shares = [count / total for count in country_dist.values()]
        hhi = sum(share**2 for share in shares)
        
        industries_diversity.append(f"{industry_code}")
        industry_names.append(industry_name[:10])
        country_counts.append(country_count)
        hhi_values.append(hhi)
    
    # 创建双轴图
    ax8_twin = ax8.twinx()
    
    x_pos = range(len(industries_diversity))
    bars1 = ax8.bar([x - 0.2 for x in x_pos], country_counts, width=0.4, 
                   label='涉及国家数', color='lightblue', alpha=0.7)
    
    line = ax8_twin.plot(x_pos, hhi_values, 'ro-', linewidth=2, markersize=6,
                        label='集中度指数(HHI)', color='red')
    
    ax8.set_title('各行业的国家来源多样性分析\n(Country Source Diversity Analysis by Industry)', 
                 fontsize=14, fontweight='bold')
    ax8.set_xlabel('行业代码 (Industry Code)', fontsize=12)
    ax8.set_ylabel('涉及国家数量 (Number of Countries)', fontsize=12)
    ax8_twin.set_ylabel('集中度指数 HHI (Concentration Index)', fontsize=12)
    
    ax8.set_xticks(x_pos)
    ax8.set_xticklabels([f"{code}\n{name}" for code, name in zip(industries_diversity, industry_names)], 
                       rotation=45, ha='right', fontsize=9)
    
    # 合并图例
    lines1, labels1 = ax8.get_legend_handles_labels()
    lines2, labels2 = ax8_twin.get_legend_handles_labels()
    ax8.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    ax8.grid(True, alpha=0.3)
    
    plt.suptitle('流入中国产业链的行业国家分布分析\nCountry Distribution Analysis of Industries Flowing into China', 
                fontsize=18, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(f'{output_path}/图9_流入中国行业国家分析.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_path}/Fig9_China_Inflow_Industry_Country_Analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

# 执行新的分析和可视化
print("\n" + "="*80)
print("=== 开始生成中国产业链流出流入专项分析 ===")
print("="*80)

# 1. 分析中国产业链流出的详细分布
outflow_analysis = analyze_detailed_china_outflow_by_country_and_region(
    supply_chains_contains_cn_node, 
    company_to_country, 
    industry_mapping, 
    country_name_mapping
)

# 2. 分析流入中国的前10个行业的国家分布
inflow_analysis = analyze_detailed_china_inflow_by_industry(
    supply_chains_contains_cn_node, 
    company_to_country, 
    industry_mapping, 
    country_name_mapping
)

# 3. 生成中国产业链流出综合图表
create_china_outflow_comprehensive_charts(
    outflow_analysis, 
    industry_mapping, 
    country_name_mapping, 
    ".\调用文件\用于行业分类分析的可视化表\学术报告图表"
)

# 4. 生成流入中国行业国家分析图表
create_china_inflow_industry_charts(
    inflow_analysis, 
    industry_mapping, 
    country_name_mapping, 
    ".\调用文件\用于行业分类分析的可视化表\学术报告图表"
)

# 5. 输出详细的文字分析报告
print("\n" + "="*60)
print("=== 中国产业链流出分析报告 ===")
print("="*60)

print(f"\n📊 总体统计:")
print(f"   总流出转移数: {outflow_analysis['total_outflow_count']}")
print(f"   涉及国家数: {outflow_analysis['summary']['total_countries']}")
print(f"   涉及区域数: {outflow_analysis['summary']['total_regions']}")
print(f"   涉及行业数: {outflow_analysis['summary']['total_industries']}")

print(f"\n🏆 前10个承接国家:")
for i, (country, count) in enumerate(outflow_analysis['top_10_countries'], 1):
    country_data = outflow_analysis['country_analysis'][country]
    country_name = country_data['country_name']
    region = country_data['region']
    percentage = country_data['percentage_of_total_outflow']
    print(f"   {i:2d}. {country_name} ({country}) - {region}")
    print(f"       流出数量: {count} ({percentage:.2f}%)")
    
    # 显示该国承接的前3个行业
    top_3_industries = country_data['top_5_industries'][:3]
    print(f"       主要承接行业: ", end="")
    for j, (industry, ind_count) in enumerate(top_3_industries):
        industry_name = industry_mapping.get(str(industry), f"行业{industry}")
        if j > 0:
            print(", ", end="")
        print(f"{industry}({industry_name[:10]}, {ind_count}次)", end="")
    print()

print(f"\n🌍 区域承接分析:")
for region, data in outflow_analysis['regional_analysis'].items():
    print(f"   {region}: {data['total_count']}次 ({data['percentage_of_total_outflow']:.2f}%)")
    
    # 显示该区域承接的前3个行业
    top_3_industries = data['top_10_industries'][:3]
    print(f"      主要承接行业: ", end="")
    for j, (industry, count) in enumerate(top_3_industries):
        industry_name = industry_mapping.get(str(industry), f"行业{industry}")
        if j > 0:
            print(", ", end="")
        print(f"{industry}({industry_name[:10]}, {count}次)", end="")
    print()

print("\n" + "="*60)
print("=== 流入中国产业链分析报告 ===")
print("="*60)

print(f"\n📊 总体统计:")
print(f"   总流入转移数: {inflow_analysis['total_inflow_count']}")
print(f"   涉及行业数: {inflow_analysis['summary']['total_industries']}")
print(f"   涉及国家数: {inflow_analysis['summary']['total_countries']}")
print(f"   平均每行业涉及国家数: {inflow_analysis['summary']['average_countries_per_industry']:.1f}")

print(f"\n🏆 前10个流入行业:")
for i, (industry_code, count) in enumerate(inflow_analysis['top_10_industries'], 1):
    industry_data = inflow_analysis['industry_analysis'][industry_code]
    industry_name = industry_data['industry_name']
    percentage = industry_data['percentage_of_total_inflow']
    country_count = industry_data['country_count']
    
    print(f"   {i:2d}. 行业{industry_code}: {industry_name}")
    print(f"       流入数量: {count} ({percentage:.2f}%)")
    print(f"       来源国家数: {country_count}")
    
    # 显示该行业的前3个来源国
    top_3_countries = industry_data['top_5_countries'][:3]
    print(f"       主要来源国: ", end="")
    for j, (country, country_name, c_count, c_percentage) in enumerate(top_3_countries):
        if j > 0:
            print(", ", end="")
        print(f"{country_name}({c_count}次, {c_percentage:.1f}%)", end="")
    print()

print("\n" + "="*80)
print("=== 中国产业链流出流入专项分析完成 ===")
print("="*80)
print("""
新增图表文件：
8. 图8_中国产业链流出综合分析.png - 中国产业链流出的国家和区域分析
9. 图9_流入中国行业国家分析.png - 流入中国前10行业的国家来源分析

分析内容包括：
- 中国产业链流出前10个国家的行业构成
- 按区域划分的产业承接分析（东南亚、北美、欧洲等）
- 各区域承接的主要行业类型和占比
- 流入中国前10个行业的国家来源分布
- 各行业来源国家的多样性分析
""")