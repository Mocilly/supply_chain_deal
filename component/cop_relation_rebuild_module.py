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
def rebuild_relations(loaded_data: Dict, companies: Dict[str, Company]) -> List[List[SupplyRelation]]:
    """
    重建供应链关系对象，确保构建完整的链条
    """
    relations = []
    
    for initial_node, chains in loaded_data.items():
        for chain_data in chains:
            path = chain_data.get('path', [])
            final_status = chain_data.get('final_status', 'unknown')
            
            if len(path) < 2:  # 至少需要两个节点才能形成关系
                continue
            
            # 构建完整的供应链关系列表
            chain_relations = []
            
            # 从初始节点开始，构建每一段关系
            current_from_id = initial_node
            
            for i, node_info in enumerate(path):
                to_id = node_info['name']
                status = node_info['status']
                start_time = parse_date(node_info['start'])
                end_time = parse_date(node_info['end'])
                
                # 确保公司存在
                if current_from_id not in companies or to_id not in companies:
                    print(f"警告：公司ID {current_from_id} 或 {to_id} 不存在于公司数据中")
                    current_from_id = to_id  # 继续处理下一个关系
                    continue
                
                # 创建供应关系
                from_company = companies[current_from_id]
                to_company = companies[to_id]
                
                relation = SupplyRelation(
                    from_co=from_company,
                    to_co=to_company,
                    start=start_time,
                    end=end_time
                )
                relation.status = status
                
                chain_relations.append(relation)
                
                # 更新下一段关系的起始公司
                current_from_id = to_id
            
            # 如果成功构建了关系，添加到结果中
            if chain_relations:
                # 添加最终状态信息
                chain_relations.append(final_status)
                relations.append(chain_relations)
    
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


import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Tuple
from component.company_supplyChain import SupplyRelation, Company

