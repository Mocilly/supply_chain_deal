# supply_chain_module.py

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Tuple
from component.company_supplyChain import SupplyRelation, Company


# 路径集合#
path_dic = {'company': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\company.json',
            'supply_chain': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\supply_relations.json',
            'complete_sc': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\complete_supply_chains.json'}

# 保存文件函数
def save_file(file_name: str, file_type: str, path: str, df: pd.DataFrame):
    if file_type == 'xlsx':
        file_name = file_name + '.xlsx'
        save_path = ''.join([path, file_name])
        with pd.ExcelWriter(save_path) as writer:
            df.to_excel(writer, index=False)
    elif file_type == 'dta':
        file_name = file_name + '.dta'
        save_path = ''.join([path, file_name])
        df.to_stata(save_path, write_index=False, version=118)

# 智能分割国家字符串
def split_countries(country_str: str) -> Tuple[List[str], List[str]]:
    normalized = country_str.strip()
    if not normalized:
        return (), ()
    home_region = normalized[:normalized.find('&')]
    hr_c = home_region[home_region.find(':') + 1:]
    c = normalized[normalized.find('&') + 1:]
    country = c[c.find(':') + 1:]
    home_region_list = hr_c.split('|') if '|' in hr_c else [hr_c]
    country_list = country.split('|') if '|' in country else [country]
    return home_region_list, country_list

# 解析日期字符串
def parse_date(date_str: str) -> datetime:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

# 重建供应链关系对象
def rebuild_relations(loaded_data: Dict, companies: Dict[str, Company]) -> List[SupplyRelation]:
    relations = []
    for initial_node, chains in loaded_data.items():
        for chain in chains:
            nodes = chain.get('path', [])
            final_status = chain.get('final_status', '')
            start_time = parse_date(chain.get('start_time', None))
            end_time = parse_date(chain.get('end_time', None))
            rel = []

            if nodes:
                first_node = nodes[0]
                sr = SupplyRelation(
                    companies[initial_node],
                    companies[first_node['name']],
                    parse_date(first_node['start']),
                    parse_date(first_node['end']),
                )
                sr.status = first_node['status']
                rel.append(sr)

                for i in range(1, len(nodes) - 1, 2):
                    from_co = companies[nodes[i]['name']]
                    to_co = companies[nodes[i + 1]['name']]
                    start = parse_date(nodes[i + 1]['start'])
                    end = parse_date(nodes[i + 1]['end'])
                    status = nodes[i + 1].get('status')
                    supply_sc = SupplyRelation(from_co, to_co, start, end)
                    supply_sc.status = status
                    rel.append(supply_sc)

                rel.append([final_status, start_time, end_time])
                relations.append(rel)
    return relations

# 加载公司数据
def load_companies(path: str) -> Dict[str, Company]:
    with open(path, 'r') as f:
        loaded_company_data = json.load(f)
    companies = {cop['id']: Company(cop['id'], cop['country'], cop['listed']) for cop in loaded_company_data}
    return companies

# 加载供应链数据
def load_supply_chain_data(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 构建公司到国家的映射表
def build_company_to_country(companies: Dict[str, Company]) -> Dict[str, Tuple[List[str], List[str]]]:
    return {company: split_countries(info.country) for company, info in companies.items()}
