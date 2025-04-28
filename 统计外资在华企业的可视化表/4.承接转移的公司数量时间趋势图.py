
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
path_dic = {'company': r'.\调用文件\时间趋势分析\company.json',
            'supply_chain': r'.\调用文件\时间趋势分析\supply_relations.json',
            'complete_sc': r'.\调用文件\时间趋势分析'
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

    path_lines = find_by_status(relations,pattern='transfer')
    print(f"第{i}个文件中，转移关系数量：{len(path_lines)}")
    #将找到的节点数据一个个全部添加到一个列表中
    for path in path_lines:
        pattern_paths.append(path)

print(f"所有文件中，转移关系数量：{len(pattern_paths)}")

#endregion 数据读取与加载



#region ----------------------------------------两任期数据切换 （重要）----------------------

# path_lines_all = relation_direct_delete_NO_lines(relations=relations,
#                                        filter_start=datetime(2015,1,1),
#                                        filter_end=datetime(2024,12,31))
# path_lines = path_lines_all
# len(path_lines)
## 涉及国家对数：permanent_break,transfer，recover = 68,56,20

# path_lines_Trump = relation_direct_delete_NO_lines(relations=relations,
#                                        filter_start=datetime(2016,11,9),
#                                        filter_end=datetime(2020,12,14))
# path_lines = path_lines_Trump
# len(path_lines)
# # 涉及国家对数：permanent_break,transfer，recover = 57,36,7

# path_lines_Biden = relation_direct_delete_NO_lines(relations=relations,
#                                        filter_start=datetime(2020,12,14),
#                                        filter_end=datetime(2024,12,31))
# path_lines = path_lines_Biden
# len(path_lines)
## 涉及国家对数：permanent_break,transfer，recover = 59,53,19

# len(path_lines_Trump)

# for rel in path_lines_Trump[:1000]:
#     print(rel)





#endregion -------------------------------------两任期数据切换 （重要）--------------------------







# region 字典创造和计数函数
def create_time_keyed_dict(start_date: datetime, end_date: datetime, increment: str = 'year') -> dict:
    """
    创建一个以时间为键的字典，键为指定时间间隔的datetime对象，值初始化为0。

    :param start_date: 起始日期，datetime对象
    :param end_date: 结束日期，datetime对象
    :param increment: 时间间隔类型，'year'表示按年递增，'month'表示按月递增
    :return: 初始化的字典
    """
    time_keyed_dict = dict()
    current_date = start_date

    while current_date <= end_date:
        time_keyed_dict[current_date] = 0
        if increment == 'year':
            current_date += relativedelta(years=1)
        elif increment == 'month':
            current_date += relativedelta(months=1)
        else:
            raise ValueError("Unsupported increment type. Use 'year' or 'month'.")
    
    return time_keyed_dict


# 计数函数
def increment_transfer_count(event_time: datetime, transfer_dict: dict, increment: str = 'year') -> None:
    """
    根据时间点和指定的时间间隔类型（年或月），对对应的计数字典进行计数+1。

    :param event_time: 事件发生时间，datetime对象
    :param transfer_dict: 计数字典
    :param increment: 时间间隔类型，'year'表示按年计数，'month'表示按月计数
    """
    if increment == 'year':
        key = datetime(event_time.year, 1, 1)
    elif increment == 'month':
        key = event_time.replace(day=1)
    else:
        raise ValueError("Unsupported increment type. Use 'year' or 'month'.")

    if key in transfer_dict:
        transfer_dict[key] += 1
    else:
        print(f"警告：时间 {event_time} 超出统计范围或键不存在")



# endregion 字典创造和计数函数


# 创建一个以月份为键的字典，键为指定时间间隔的datetime对象（精确到月初），值初始化为0
transfer_count_by_month = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='month'
    )

# 创建一个以年份为键的字典，键为指定时间间隔的datetime对象（精确到年初），值初始化为0
native_transfer_count_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)


# region转移到中国的供应链数量和 本土企业建立转移关系数量
cn_transfer_rel_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
    )
for i, rel in enumerate(pattern_paths):
    #home_region一栏里存在长度不为1的列表，由于可视化是用home_region + country，所以这里要用home_region+country从transfer中找到转向中国的供应链关系
    cn_mainland__SAR = ['CN','HK','MO']
    if (any(area in company_to_country[rel.to_co.id][0] for area in cn_mainland__SAR) or
        any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
        ):
        if 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]:
            continue
        else:    
            increment_transfer_count(rel.start,cn_transfer_rel_by_year,increment='year')

for time, value in cn_transfer_rel_by_year.items():
    print(f"年份：{time.year}, 转移数量：{value}")




for i, rel in enumerate(pattern_paths):
    #中国本土公司间建立转移供应链关系 时间计数
    cn_mainland__SAR = ['CN','HK','MO']
    #下面为cn公司数量计数
    # if (any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR) or
    #     any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
    #     ):
    if (any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR) and
        any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
        ):
        if 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]:
            continue
        else:    
            increment_transfer_count(rel.start,native_transfer_count_by_year,increment='year')


for time, value in native_transfer_count_by_year.items():
    print(f"年份：{time.year}, 转移数量：{value}")
#endregion 转移到中国的供应链数量和 本土企业建立转移关系数量


#region 统计转移到中国的供应链中本土供应商数量和本土公司平均本土供应关系数量占比

# 统计转移到中国的供应链中本土供应商数量和单个公司平均本土供应关系数量占比
def calculate_average_ratio(relations, company_to_country):
    """
    计算转移到中国的供应链中本土供应商数量和单个公司平均本土供应商数量占比。

    :param relations: 供应链关系列表
    :param company_to_country: 公司到国家的映射字典
    :return: 本土供应商数量和单个公司平均外资供应关系数量占比
    """
    local_supplier_count = 0
    foreign_supplier_count = 0

    for rel in relations:
        nation_not_found_from = 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]
        nation_not_found_to = 'Nation_Not_Found' in company_to_country[rel.to_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.to_co.id][1]
        if nation_not_found_from or nation_not_found_to:
            # 如果起始公司或目标公司在国家映射中未找到，则跳过该关系
            continue
        else:
            if any(area in company_to_country[rel.to_co.id][1] for area in ['CN', 'HK', 'MO']):
                local_supplier_count += 1
            else:
                foreign_supplier_count += 1

    average_ratio = local_supplier_count / (local_supplier_count + foreign_supplier_count) if (local_supplier_count + foreign_supplier_count) > 0 else 0

    return local_supplier_count,foreign_supplier_count, average_ratio

# 统计转移到中国的供应链中外资在华供应商数量和单个公司平均本土供应关系数量占比
def calculate_average_ratio_2(relations, company_to_country):

    local_supplier_count = 0
    foreign_supplier_count = 0

    for rel in relations:
        nation_not_found_from = 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]
        nation_not_found_to = 'Nation_Not_Found' in company_to_country[rel.to_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.to_co.id][1]
        if nation_not_found_from or nation_not_found_to:
            # 如果起始公司或目标公司在国家映射中未找到，则跳过该关系
            continue
        else:
            if any(area not in company_to_country[rel.to_co.id][1] for area in ['CN', 'HK', 'MO']) and \
                any(area  in company_to_country[rel.to_co.id][0] for area in ['CN', 'HK', 'MO']):
                local_supplier_count += 1
            else:
                foreign_supplier_count += 1

    average_ratio = local_supplier_count / (local_supplier_count + foreign_supplier_count) if (local_supplier_count + foreign_supplier_count) > 0 else 0

    return local_supplier_count,foreign_supplier_count, average_ratio

def get_native_company_set(pattern_paths, company_to_country):
    """
    获取中国本土公司集合，这些公司与其他本土公司建立了供应链关系。
    
    :param pattern_paths: 供应链关系路径列表
    :param company_to_country: 公司到国家的映射字典
    :return: 本土公司集合
    """
    native_cop_set = set()
    cn_mainland__SAR = ['CN', 'HK', 'MO']

    for rel in pattern_paths:
        native_cop_check_from = any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR)
        native_cop_check_to = any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)

        if native_cop_check_from or native_cop_check_to:
            if native_cop_check_from:
                if 'Nation_Not_Found' not in company_to_country[rel.from_co.id][0] and \
                    'Nation_Not_Found' not in company_to_country[rel.from_co.id][1]:
                    native_cop_set.add(rel.from_co.id)

            if native_cop_check_to:
                if 'Nation_Not_Found' not in company_to_country[rel.to_co.id][0] and \
                    'Nation_Not_Found' not in company_to_country[rel.to_co.id][1]:
                    native_cop_set.add(rel.to_co.id)

    return native_cop_set

def get_all_company_set(pattern_paths, company_to_country):
    """
    获取所有公司集合
    
    :param pattern_paths: 供应链关系路径列表
    :param company_to_country: 公司到国家的映射字典
    :return: 本土公司集合
    """
    all_cop_set = set()
    # cn_mainland__SAR = ['CN', 'HK', 'MO']

    for rel in pattern_paths:

        if 'Nation_Not_Found' not in company_to_country[rel.from_co.id][0] and \
            'Nation_Not_Found' not in company_to_country[rel.from_co.id][1]:
            all_cop_set.add(rel.from_co.id)

        if 'Nation_Not_Found' not in company_to_country[rel.to_co.id][0] and \
            'Nation_Not_Found' not in company_to_country[rel.to_co.id][1]:
            all_cop_set.add(rel.to_co.id)

    return all_cop_set


# 本土转移供应链中新增中国本土公司数量（年份）
cop_native_count_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)
for year in range(2015, 2025):  # 从2015年到2024年
    yearly_relations = [
        rel for rel in pattern_paths if rel.start.year == year
    ]
    yearly_native_cop_set = get_native_company_set(yearly_relations, company_to_country)
    cop_native_count_by_year[datetime(year, 1, 1)] = len(yearly_native_cop_set)


# 本土新增转移供应链中中国外资公司数量（年份）
cop_foreign_count_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)
for year in range(2015, 2025):  # 从2013年到2024年
    yearly_relations = [
        rel for rel in pattern_paths if rel.start.year == year
    ]
    yearly_native_cop_set = get_all_company_set(yearly_relations, company_to_country) - get_native_company_set(yearly_relations, company_to_country)
    cop_foreign_count_by_year[datetime(year, 1, 1)] = len(yearly_native_cop_set)



all_native_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去
for i,rel in enumerate(pattern_paths):
    cn_mainland__SAR = ['CN','HK','MO']
    if 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]:
            continue
    else:    
        if  any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR):
                all_native_cop_set.add(rel.from_co.id)  # 添加起始公司ID
        if  any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR):
                all_native_cop_set.add(rel.to_co.id)  # 添加目标公司ID

    print(f'已解决{i+1}')

# 本土公司 平均新建转移供应链的本土公司供应关系占比
cop_native_ratio_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)



for year in range(2015, 2025):  # 从2013年到2024年
    yearly_relations = [
        rel for rel in pattern_paths if rel.start.year == year
    ] #固定特定年份的供应链关系
    yearly_native_cop_set = get_native_company_set(yearly_relations, company_to_country)  # 获取本土公司集合
    ratio_list = []  # 存储每个本土公司的 本土供应商平均比例
    for i,cop in enumerate(yearly_native_cop_set):
        local_supplier_count,foreign_supplier_count,average_ratio = calculate_average_ratio(yearly_relations, company_to_country)
        # if local_supplier_count != 0:
        #     print(f"公司ID：{cop}，本土供应商数量：{local_supplier_count}，平均比例：{average_ratio:.2%}")
        ratio_list.append(average_ratio)  # 将每个本土公司的平均比例添加到列表中
        # print(f'已经处理{i+1}/{len(yearly_native_cop_set)}个本土公司')
    # 计算 本土公司 的 本土供应商比例 的 平均比例
    if not ratio_list:
        print(f"年份：{year} 没有本土公司数据，无法计算平均比例。")
        list_average_ratio = 0.0  # 或其他默认值
    else:
        list_average_ratio = sum(ratio_list) / len(ratio_list)

    cop_native_ratio_by_year[datetime(year, 1, 1)] = round(list_average_ratio, 2)  # 将平均比例保留两位小数并存入字典中
    print(f"年份：{year}, 本土公司新增供应商 平均本土供应商比例：{list_average_ratio:.2%}") 

cop_native_ratio_by_year

cop_foreign_ratio_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)
for year in range(2015, 2025):  # 从2015年到2024年
    yearly_relations = [
        rel for rel in pattern_paths if rel.start.year == year
    ] #固定特定年份的供应链关系
    ratio_list = []  # 存储每个本土公司的 本土供应商平均比例
    for i,cop in enumerate(yearly_native_cop_set):
        local_supplier_count,foreign_supplier_count, average_ratio = calculate_average_ratio(yearly_relations, company_to_country)
        # if foreign_supplier_count != 0:
        #     print(f"公司ID：{cop}，外资供应商数量：{local_supplier_count}，平均比例：{average_ratio:.2%}")
        ratio_list.append(1-average_ratio)  # 将每个本土公司的平均比例添加到列表中
        # print(f'已经处理{i+1}/{len(yearly_native_cop_set)}个本土公司')
    # 计算 本土公司 的 本土供应商比例 的 平均比例
    if not ratio_list:
        print(f"年份：{year} 没有本土公司数据，无法计算平均比例。")
        list_average_ratio = 0.0  # 或其他默认值
    else:
        list_average_ratio = sum(ratio_list) / len(ratio_list)

    cop_foreign_ratio_by_year[datetime(year, 1, 1)] = round(list_average_ratio, 2)  # 将平均比例保留两位小数并存入字典中
    print(f"年份：{year}, 本土公司新增供应商 平均外资供应商比例：{list_average_ratio:.2%}") 


cop_foreign_in_cn_ratio_by_year = create_time_keyed_dict(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
)
for year in range(2015, 2025):  # 从2015年到2024年
    yearly_relations = [
        rel for rel in pattern_paths if rel.start.year == year
    ] #固定特定年份的供应链关系
    ratio_list = []  # 存储每个本土公司的 本土供应商平均比例
    for i,cop in enumerate(yearly_native_cop_set):
        foreign_in_cn_supplier_count,foreign_supplier_count, average_ratio = calculate_average_ratio(yearly_relations, company_to_country)
        # if foreign_supplier_count != 0:
        #     print(f"公司ID：{cop}，外资供应商数量：{local_supplier_count}，平均比例：{average_ratio:.2%}")
        ratio_list.append(1-average_ratio)  # 将每个本土公司的平均比例添加到列表中
        # print(f'已经处理{i+1}/{len(yearly_native_cop_set)}个本土公司')
    # 计算 本土公司 的 本土供应商比例 的 平均比例
    if not ratio_list:
        print(f"年份：{year} 没有本土公司数据，无法计算平均比例。")
        list_average_ratio = 0.0  # 或其他默认值
    else:
        list_average_ratio = sum(ratio_list) / len(ratio_list)

    cop_foreign_ratio_by_year[datetime(year, 1, 1)] = round(list_average_ratio, 2)  # 将平均比例保留两位小数并存入字典中
    print(f"年份：{year}, 本土公司新增供应商 平均外资在华供应商比例：{list_average_ratio:.2%}") 



#region 年度数据趋势图可视化


def plot_supply_chain_trend(values, values_2, bars_label, line_label, x_label, y_label_left, y_label_right, title,accuracy=0.1):
    """
    绘制供应链转移趋势分析图（增强版）

    绘制供应链转移趋势分析图。

    :param values: 柱状图数据
    :param values_2: 折线图数据
    :param bars_label: 柱状图图例标签
    :param line_label: 折线图图例标签
    :param x_label: 横轴标签
    :param y_label_left: 左侧纵轴标签
    :param y_label_right: 右侧纵轴标签
    :param title: 图表标题

    改进说明：
    1. 折线图y轴范围扩大20%实现视觉上移
    2. 折线点添加数值标签
    """
    import matplotlib.pyplot as plt
    import numpy as np

    # 设置中文字体和行业报告风格
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 适用于Windows系统
    plt.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

    # 准备年份数据
    years = sorted(values.keys())
    bar_values = [values[year] for year in years]
    line_values = [values_2[year] for year in years]

    # 创建画布和坐标轴
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # 绘制柱状图（左侧轴）
    bars = ax1.bar(
        [y.strftime('%Y') for y in years],
        bar_values,
        color='#1F77B4',
        edgecolor='black',
        alpha=0.8,
        hatch='////',
        label=bars_label
    )

    # 绘制折线图（右侧轴）
    line, = ax2.plot(
        [y.strftime('%Y') for y in years],
        line_values,
        color='#2CA02C',
        linestyle='--',
        marker='o',
        markersize=8,
        linewidth=2,
        markerfacecolor='white',
        markeredgewidth=2,
        label=line_label
    )

    # 设置坐标轴格式
    ax1.set_xlabel(x_label, fontsize=12)
    ax1.set_ylabel(y_label_left, fontsize=12)
    ax2.set_ylabel(y_label_right, fontsize=12)

    # 设置双轴刻度范围
    ax1.set_ylim(0, max(bar_values) * 1.5)
    
    # 调整折线图y轴范围（上移关键修改）
    y_min = min(line_values) * 0.1 if not np.isnan(min(line_values)) else 0
    y_max = max(line_values) * 1.1 if not np.isnan(max(line_values)) else 1
    ax2.set_ylim(y_min, y_max)

    # 添加折线图数据标签（关键新增代码）
    for i, (x, y) in enumerate(zip(line.get_xdata(), line.get_ydata())):
        ax2.annotate(f'{y:.{accuracy}f}',
                     xy=(x, y),
                     xytext=(0, 10),  # 标签向上偏移10像素
                     textcoords='offset points',
                     ha='center',
                     va='bottom',
                     color='#2CA02C',
                     fontsize=10,
                     fontweight='bold')

    # 设置图表标题
    plt.title(title, fontsize=14, pad=20)
    
    # 合并图例
    lines_for_legend = [
        plt.Rectangle((0,0), 1, 1, fc='#1F77B4', alpha=0.8, hatch='////', edgecolor='black'),
        line
    ]
    ax1.legend(lines_for_legend, [bars_label, line_label], loc='upper left')

    # 添加柱状图数据标签
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')

    # 设置网格线
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax2.grid(visible=False)

    # 调整布局
    plt.tight_layout()
    plt.show()


plot_supply_chain_trend(
    values=cn_transfer_rel_by_year,
    values_2=native_transfer_count_by_year,
    bars_label="新增供应链转向中国的数量",
    line_label="中国本土公司间新增供应链数量",
    x_label="年份",
    y_label_left="新增供应链转向中国的数量",
    y_label_right="中国本土公司间新增供应链数量",
    title="供应链转移趋势分析",
    accuracy=0
)

plot_supply_chain_trend(
    values=cop_native_count_by_year,
    values_2=cop_native_ratio_by_year,
    bars_label="本土新增供应关系中——本土公司数量",
    line_label="本土公司新增供应商——本土公司占比",
    x_label="年份",
    y_label_left="本土新增供应关系中——本土公司数量",
    y_label_right="本土公司新增供应商——本土公司占比",
    title="供应商转移趋势分析",
    accuracy=2
)

plot_supply_chain_trend(
    values=cop_foreign_count_by_year,
    values_2=cop_foreign_ratio_by_year,
    bars_label="本土新增供应关系中——本土公司数量",
    line_label="本土公司新增供应商——外资公司占比",
    x_label="年份",
    y_label_left="本土新增供应关系中——本土公司数量",
    y_label_right="本土公司新增供应商——外资公司占比",
    title="供应商转移趋势分析",
    accuracy=2
)

plot_supply_chain_trend(
    values=cop_foreign_count_by_year,
    values_2=cop_foreign_ratio_by_year,
    bars_label="本土新增供应关系中——本土公司数量",
    line_label="本土公司新增供应商——外资在华公司占比",
    x_label="年份",
    y_label_left="本土新增供应关系中——本土公司数量",
    y_label_right="本土公司新增供应商——外资在华公司占比",
    title="供应商转移趋势分析",
    accuracy=2
)

#endregion 年度时间趋势图可视化

