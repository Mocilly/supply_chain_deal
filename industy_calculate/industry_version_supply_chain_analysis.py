from datetime import datetime
import os
import re
import math  # 添加这行
from collections import defaultdict

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

# 加载公司数据
companies = load_companies(path_dic["company"])


for idx, company in enumerate(companies.values()):
    print(f"公司ID：{company.id}，国家：{company.country}，上市状态：{company.listed}")
    if idx > 10:
        break
# 构建公司-国家映射表
company_to_country = build_company_to_country(companies)


def relation_direct_delete_NO_lines(relations, filter_start, filter_end):
    result_indices = []
    for chain in relations:
        # 分离供应链关系数据 和 供应链状态数据
        supply_chain = chain[:-1]
        chain_status = chain[-1]
        
        if not supply_chain or not chain_status:
            continue
            
        
        # 第一阶段：标记所有有效节点
        valid_indices = [
            rel for i, rel in enumerate(supply_chain)
            if rel.start >= filter_start and rel.end <= filter_end
        ]
        if valid_indices:
            valid_indices.append(chain_status)
            result_indices.append(valid_indices)
            continue
        
        
    return result_indices



def filter_supply_chains_contains_cn_node(restored_relations, company_to_country):
    """
    保留包含中国节点的供应链关系
    :param restored_relations: 供应链关系列表
    :param company_to_country: 公司ID到国家的映射
    :return: 包含中国节点的供应链关系列表
    """
    supply_chains_contains_cn_node = []
    for i, complete_rel in enumerate(restored_relations):
        chain = complete_rel[:-1]
        for rel in chain:
            from_co_country_belong = company_to_country[rel.from_co.id]
            to_co_country_belong = company_to_country[rel.to_co.id]
            if 'CN' in from_co_country_belong[0] or 'CN' in from_co_country_belong[1]:
                supply_chains_contains_cn_node.append(chain)
                break
            if 'CN' in to_co_country_belong[0] or 'CN' in to_co_country_belong[1]:
                supply_chains_contains_cn_node.append(chain)
                break
        # print(f"进度：{i}/{len(restored_relations)}")
    return supply_chains_contains_cn_node


def load_industry_codes_and_assign(relations_list: List[List], industry_csv_path: str):
    """
    从CSV文件加载行业代码并分配给供应链关系
    :param relations_list: 供应链关系列表
    :param industry_csv_path: 行业代码CSV文件路径
    """
    try:
        # 读取CSV文件，添加 low_memory=False 避免警告
        df = pd.read_csv(industry_csv_path, encoding='utf-8', low_memory=False)
        print(f"CSV文件读取成功，共 {len(df)} 行")
        print(f"CSV列名: {list(df.columns)}")
        
        # 检查行业代码列是否存在
        industry_column = None
        possible_names = ['行业代码', 'industry_code', 'Industry_Code', '行业编码']
        for name in possible_names:
            if name in df.columns:
                industry_column = name
                break
        
        if industry_column is None:
            # 如果找不到，使用最后一列
            industry_column = df.columns[-1]
            print(f"未找到预期的行业代码列名，使用最后一列: {industry_column}")
        else:
            print(f"使用行业代码列: {industry_column}")
        
        # 检查行业代码列的空值情况
        industry_data = df[industry_column]
        total_rows = len(df)
        null_count = industry_data.isnull().sum()
        empty_count = (industry_data == '').sum()
        valid_count = total_rows - null_count - empty_count
        
        print(f"行业代码列统计:")
        print(f"  总行数: {total_rows}")
        print(f"  空值(NaN): {null_count}")
        print(f"  空字符串: {empty_count}")
        print(f"  有效值: {valid_count}")
        print(f"  有效值占比: {valid_count/total_rows*100:.2f}%")
        
        # 显示一些非空的行业代码示例
        non_empty_data = industry_data.dropna()
        non_empty_data = non_empty_data[non_empty_data != '']
        if len(non_empty_data) > 0:
            print(f"行业代码示例: {list(non_empty_data.head(5))}")
        else:
            print("警告：没有找到任何非空的行业代码！")
        
        # 检查CSV文件中的日期格式和其他列
        print(f"CSV前5行数据:")
        print(df.head())
        
        # 检查并使用正确的列名
        start_col = None
        end_col = None
        from_co_col = None
        to_co_col = None
        
        # 检查日期列
        for col in ['start_', 'start', 'Start', 'START']:
            if col in df.columns:
                start_col = col
                break
        
        for col in ['end_', 'end', 'End', 'END']:
            if col in df.columns:
                end_col = col
                break
        
        # 检查公司ID列
        for col in ['source_company_id', 'from_co_id', 'from_company_id']:
            if col in df.columns:
                from_co_col = col
                break
        
        for col in ['target_company_id', 'to_co_id', 'to_company_id']:
            if col in df.columns:
                to_co_col = col
                break
        
        if not all([start_col, end_col, from_co_col, to_co_col]):
            print(f"缺少必要的列: start_col={start_col}, end_col={end_col}, from_co_col={from_co_col}, to_co_col={to_co_col}")
            return
        
        print(f"使用列名: start={start_col}, end={end_col}, from_co={from_co_col}, to_co={to_co_col}")
        
        # 创建查询索引，基于from_co_id, to_co_id, start_month, end_month
        try:
            # 在日期解析前先替换异常日期
            df[start_col] = df[start_col].astype(str).replace('4000-01-01', '2025-01-01')
            df[end_col] = df[end_col].astype(str).replace('4000-01-01', '2025-01-01')
            
            # 解析日期并转换为月份周期
            df['start_month'] = pd.to_datetime(df[start_col], errors='coerce').dt.to_period('M')
            df['end_month'] = pd.to_datetime(df[end_col], errors='coerce').dt.to_period('M')
            
            # 检查日期解析结果
            start_null_count = df['start_month'].isnull().sum()
            end_null_count = df['end_month'].isnull().sum()
            print(f"日期解析结果: start_month空值={start_null_count}, end_month空值={end_null_count}")
            
        except Exception as e:
            print(f"日期解析错误: {e}")
            return
        
        # 创建查询字典以提高查询效率
        lookup_dict = {}
        for _, row in df.iterrows():
            key = (
                str(row[from_co_col]), 
                str(row[to_co_col]), 
                row['start_month'], 
                row['end_month']
            )
            industry_value = row[industry_column]
            
            # 处理行业代码：如果为空或NaN，设为None；如果有"|"分隔，转为列表
            if pd.isna(industry_value) or industry_value == '':
                lookup_dict[key] = None
            else:
                industry_codes = str(industry_value).split('|') if '|' in str(industry_value) else [str(industry_value)]
                lookup_dict[key] = industry_codes
        
        print(f"创建查询字典，共 {len(lookup_dict)} 个键值对")
        
        # 统计查询字典中的空值情况
        dict_none_count = sum(1 for v in lookup_dict.values() if v is None)
        dict_valid_count = len(lookup_dict) - dict_none_count
        print(f"查询字典中: 空值={dict_none_count}, 有效值={dict_valid_count}")
        
        # 显示几个有效的键值对示例
        valid_samples = [(k, v) for k, v in lookup_dict.items() if v is not None]
        if valid_samples:
            print("有效键值对示例:")
            for i, (key, value) in enumerate(valid_samples[:3]):
                print(f"  {key} -> {value}")
        else:
            print("警告：查询字典中没有任何有效的行业代码！")
        
        # 为每个供应链关系分配行业代码
        matched_count = 0
        not_found_count = 0
        none_count = 0
        
        for relation_chain in relations_list:
            # 跳过状态信息（最后一个元素）
            supply_chain = relation_chain[:-1] if len(relation_chain) > 0 else []
            
            for rel in supply_chain:
                if isinstance(rel, SupplyRelation):
                    # 创建查询键 - 修复datetime转换问题
                    start_month = None
                    end_month = None
                    
                    if rel.start:
                        # 将datetime转换为pandas Period
                        start_month = pd.Timestamp(rel.start).to_period('M')
                    
                    if rel.end:
                        # 将datetime转换为pandas Period
                        end_month = pd.Timestamp(rel.end).to_period('M')
                    
                    query_key = (
                        rel.from_co.id,
                        rel.to_co.id,
                        start_month,
                        end_month
                    )
                    
                    # 查找行业代码
                    if query_key in lookup_dict:
                        rel.industry_codes = lookup_dict[query_key]
                        if rel.industry_codes is None:
                            none_count += 1
                        else:
                            matched_count += 1
                    else:
                        rel.industry_codes = 'Line_Not_Found'
                        not_found_count += 1
                        
                        # 调试：显示前几个未找到的键
                        if not_found_count <= 5:
                            print(f"未找到的查询键: {query_key}")
        
        print(f"匹配统计: 成功匹配={matched_count}, 空值匹配={none_count}, 未找到={not_found_count}")
        print(f"成功加载行业代码，共处理 {len(lookup_dict)} 条记录")
        
    except Exception as e:
        print(f"加载行业代码时出错：{e}")
        import traceback

        traceback.print_exc()
        
        # 如果出错，为所有关系设置默认值
        for relation_chain in relations_list:
            supply_chain = relation_chain[:-1] if len(relation_chain) > 0 else []
            for rel in supply_chain:
                if isinstance(rel, SupplyRelation):
                    rel.industry_codes = 'Line_Not_Found'


# region 赋值行业代码并重建供应链关系

restored_relations = []
for i in range(1,7):
    #将文件名和路径合并起来 加载供应链数据
    loaded_data = load_supply_chain_data(os.path.join(path_dic["complete_sc"],f'complete_supply_chains_{i}.json'))

    # 重建供应链关系
    relations = rebuild_relations(loaded_data=loaded_data, companies=companies)
    for complete_rel in relations:
        restored_relations.append(complete_rel)
    print(f'解决{i}')

# 加载并分配行业代码
industry_csv_path = r".\调用文件\用于行业分类分析的可视化表\9.新算法_添加所属国家后的供应链关系表_带行业代码.csv"
load_industry_codes_and_assign(restored_relations, industry_csv_path)

# 将全部供应链中的公司id去重保留在集合中
supply_chains_contains_cn_node = filter_supply_chains_contains_cn_node(restored_relations, company_to_country)


# 统计包含 Line_Not_Found 的供应链关系数量及占比
line_not_found_count = 0
for chain in supply_chains_contains_cn_node:
    for rel in chain:
        if isinstance(rel, SupplyRelation) and getattr(rel, "industry_codes", None) == "Line_Not_Found":
            line_not_found_count += 1
            break  # 只统计一次该链

total_chains = len(supply_chains_contains_cn_node)
percentage = (line_not_found_count / total_chains) * 100 if total_chains > 0 else 0

print(f"包含 Line_Not_Found 的供应链关系数量: {line_not_found_count}")
print(f"占比: {percentage:.2f}%")


# 打印供应链关系，展示行业代码
ccc = 0
for chain in supply_chains_contains_cn_node:
    print(f"供应链包含中国节点：{chain}")
    for rel in chain:
        if isinstance(rel, SupplyRelation):
            print(f"  供应关系：{rel.from_co.id} -> {rel.to_co.id}, 状态：{rel.status}, 行业代码：{rel.industry_codes}")
    ccc += 1
    if ccc > 15:
        break



import json

# 将包含中国节点的供应链关系保存为JSON文件
def supply_chain_to_dict(chain):
    # 将SupplyRelation对象转换为可序列化的字典
    result = []
    for rel in chain:
        if isinstance(rel, SupplyRelation):
            result.append({
                "from_co_id": rel.from_co.id,
                "to_co_id": rel.to_co.id,
                "status": rel.status,
                "start": rel.start.strftime("%Y-%m-%d") if rel.start else None,
                "end": rel.end.strftime("%Y-%m-%d") if rel.end else None,
                "industry_codes": rel.industry_codes
            })
    return result

output_list = [supply_chain_to_dict(chain) for chain in supply_chains_contains_cn_node]

output_path = r".\调用文件\用于行业分类分析的可视化表\supply_chains_with_industry_codes.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_list, f, ensure_ascii=False, indent=2)
print(f"已保存包含中国节点的供应链关系到: {output_path}")

# endregion 赋值行业代码并重建供应链关系


