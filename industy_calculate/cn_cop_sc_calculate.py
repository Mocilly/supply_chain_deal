
from datetime import datetime
import os
import re
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
    path_dic)
from component.company_supplyChain import SupplyRelation, Company
from datetime import timedelta


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


print("\n 依照状态查找供应链条：")


# 	# 4. 查找特定状态模式的路径  (专指Transfer和recover对象，不包括permanent_break，因为后者要考虑最终状态)
def find_by_status(relations,pattern):
    count=0
    find_path = []
    for chains in relations:
        chain = chains[:-1]
        final_status = chains[-1]
        for rel in chain:
            if rel.status == pattern:
                find_path.append(rel)
                count+=1
    print(f'找到对应 {pattern} 关系数量:{count}')
    return find_path



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

pattern_paths = []
for i in range(1,7):
    #将文件名和路径合并起来 加载供应链数据
    loaded_data = load_supply_chain_data(os.path.join(path_dic["complete_sc"],f'complete_supply_chains_{i}.json'))

    # 重建供应链关系
    relations = rebuild_relations(loaded_data=loaded_data, companies=companies)

    print(f"供应链关系总数：{len(relations)}")
    for complete_rel in relations:
        sc_chain = complete_rel[:-1]
        for rel in sc_chain:
            if rel.status == 'transfer':
                pattern_paths.append(complete_rel)
                break

    print(f"处理完第{i}个文件中，转移关系当前数量：{len(pattern_paths)}")


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
        print(f"进度：{i}/{len(restored_relations)}")
    return supply_chains_contains_cn_node



restoired_relations = []
for i in range(1,7):
    #将文件名和路径合并起来 加载供应链数据
    loaded_data = load_supply_chain_data(os.path.join(path_dic["complete_sc"],f'complete_supply_chains_{i}.json'))

    # 重建供应链关系
    relations = rebuild_relations(loaded_data=loaded_data, companies=companies)
    for complete_rel in relations:
        restoired_relations.append(complete_rel)
    print(f'解决{i}')


# region 将全部供应链中的公司id去重保留在集合中
supply_chains_contains_cn_node = filter_supply_chains_contains_cn_node(restoired_relations, company_to_country)

#将上述供应链中的公司的id去重保留在集合中
unique_company_ids = set()
for chain in supply_chains_contains_cn_node:
    chain = chain[:-1]
    for rel in chain:
        unique_company_ids.add(rel.from_co.id)
        unique_company_ids.add(rel.to_co.id)
print(f"包含中国节点的供应链所涉及的所有公司总数：{len(unique_company_ids)}")


import pandas as pd


df_sc = pd.read_csv(r'.\调用文件\用于行业分类分析的可视化表\8.新算法_添加所属国家后的供应链关系表.csv') #供应链df
# df_cop = pd.read_stata(r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data\时间趋势分析数据\时间趋势分析数据cop表.dta') #cop表

# df_cop.columns

df_sc.columns
df_sc
#创造方法 来 获取df_sc中的 source_compan_name，target_company_name，source_company_keyword，target_company_keyword，keyword
df_sc = df_sc[['source_company_id','target_company_id','SOURCE_name','TARGET_name','source_company_keyword','target_company_keyword',
               'keyword1','keyword2','keyword3','keyword4','keyword5','keyword6','keyword7','keyword8','keyword9','keyword10']]

df_sc.columns
#将df_sc中的source_company_id和target_company_id转成字符串格式
df_sc['source_company_id'] = df_sc['source_company_id'].astype(str)
df_sc['target_company_id'] = df_sc['target_company_id'].astype(str)


# 将unique_company_ids中每个公司id在 df_sc的'source_company_id','target_company_id'查询，如果有查询结果则将该行索引加入列表中
matched_indices = set()
for i,company_id in enumerate(unique_company_ids):
    source_matches = df_sc.index[df_sc['source_company_id'] == company_id].tolist()
    target_matches = df_sc.index[df_sc['target_company_id'] == company_id].tolist()
    matched_indices.update(source_matches)
    matched_indices.update(target_matches)
    print(f"进度：{i}/{len(unique_company_ids)}")
# 将集合转换为列表并打印匹配到的行索引数量
matched_indices = list(matched_indices)
print(f"匹配到的行索引数量：{len(matched_indices)}")

#将储存的列表保存起来
with open(os.path.join(path_dic['complete_sc'],'matched_indices.txt'), 'w') as f:
    for index in matched_indices:
        f.write(f"{index}\n")

#endregion 将全部供应链中的公司id去重保留在集合中


# region 将转移供应链中的公司id去重保留在集合中
# 将unique_transfer_company_ids中每个公司id在 df_sc的'source_company_id','target_company_id'查询，如果有查询结果则将该行索引加入列表中
transfer_sc_contains_cn_node = filter_supply_chains_contains_cn_node(pattern_paths, company_to_country)

transfer_sc_contains_cn_node[:50]
import pandas as pd


df_sc = pd.read_csv(r'.\调用文件\用于行业分类分析的可视化表\8.新算法_添加所属国家后的供应链关系表.csv') #供应链df
# df_cop = pd.read_stata(r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data\时间趋势分析数据\时间趋势分析数据cop表.dta') #cop表

# df_cop.columns

df_sc.columns
df_sc
#创造方法 来 获取df_sc中的 source_compan_name，target_company_name，source_company_keyword，target_company_keyword，keyword
df_sc = df_sc[['source_company_id','target_company_id','SOURCE_name','TARGET_name','source_company_keyword','target_company_keyword',
               'keyword1','keyword2','keyword3','keyword4','keyword5','keyword6','keyword7','keyword8','keyword9','keyword10']]

df_sc.columns
#将df_sc中的source_company_id和target_company_id转成字符串格式
df_sc['source_company_id'] = df_sc['source_company_id'].astype(str)
df_sc['target_company_id'] = df_sc['target_company_id'].astype(str)


#将上述供应链中的公司的id去重保留在集合中
unique_company_ids = set()
for chain in transfer_sc_contains_cn_node:
    chain = chain[:-1]
    for rel in chain:
        unique_company_ids.add(rel.from_co.id)
        unique_company_ids.add(rel.to_co.id)
print(f"包含中国节点的供应链所涉及的所有公司总数：{len(unique_company_ids)}")



# 将unique_company_ids中每个公司id在 df_sc的'source_company_id','target_company_id'查询，如果有查询结果则将该行索引加入列表中
matched_indices = set()
for i,company_id in enumerate(unique_company_ids):
    source_matches = df_sc.index[df_sc['source_company_id'] == company_id].tolist()
    target_matches = df_sc.index[df_sc['target_company_id'] == company_id].tolist()
    matched_indices.update(source_matches)
    matched_indices.update(target_matches)
    print(f"进度：{i}/{len(unique_company_ids)}")
# 将集合转换为列表并打印匹配到的行索引数量
matched_indices = list(matched_indices)
print(f"匹配到的行索引数量：{len(matched_indices)}")

#将储存的列表保存起来
with open(os.path.join(path_dic['complete_sc'],'transfer_matched_indices.txt'), 'w') as f:
    for index in matched_indices:
        f.write(f"{index}\n")
#endregion 将转移供应链中的公司id去重保留在集合中


# region 读取transfer_matched_indices.txt文件
with open(os.path.join(path_dic['complete_sc'],'transfer_matched_indices.txt'), 'r') as f:
    transfer_matched_indices = [int(line.strip()) for line in f.readlines()]
transfer_matched_indices[:50]
transfer_matched_indices[6] in range(0,52055)
len(transfer_matched_indices)
max_num_every_one_hundred_thousand  = [(0,52055),
                                       (161795,214610),
                                       (332478,388420),
                                       (519817,571715),
                                       (687912,741170),
                                       (862550,922030),
                                       (1041162,1093738),
                                       (1209475,1265213),
                                       (1400976,1453515),
                                       (1569524,1617025)]

# 查询不在max_num_every_one_hundred_thousand的十个范围内的索引
not_in_any_range = []
for idx in transfer_matched_indices:
    in_range = False
    for rng in max_num_every_one_hundred_thousand:
        if rng[0] <= idx <= rng[1]:
            in_range = True
            break
    if not in_range:
        not_in_any_range.append(idx)

print(f"不在任何max_num_every_one_hundred_thousand范围内的索引数量：{len(not_in_any_range)}")
print("部分不在范围内的索引示例：", not_in_any_range[:20])

len(not_in_any_range)

# 将index_not_included中每十万个索引下的最小最大输出
for i in range(0, 17):
    min_index = min([index for index in not_in_any_range if index > i*100000 and index < (i+1)*100000], default=None)
    max_index = max([index for index in not_in_any_range if index > i*100000 and index < (i+1)*100000], default=None)
    print(f"在{i*100000}到{(i+1)*100000}范围内未包含的索引最小值：{min_index}，最大值：{max_index}")

