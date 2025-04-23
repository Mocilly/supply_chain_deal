
from datetime import datetime
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
path_dic = {'company': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\company.json',
            'supply_chain': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\supply_relations.json',
            'complete_sc': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\complete_supply_chains.json'
            }

# 加载公司数据
companies = load_companies(path_dic["company"])

for idx, company in enumerate(companies.values()):
    print(f"公司ID：{company.id}，国家：{company.country}，上市状态：{company.listed}")
    if idx > 10:
        break
# 构建公司-国家映射表
company_to_country = build_company_to_country(companies)

# 加载供应链数据
loaded_data = load_supply_chain_data(path_dic["complete_sc"])

# 重建供应链关系
relations = rebuild_relations(loaded_data=loaded_data, companies=companies)

# 打印部分数据用于验证
for rel in relations[:10]:
    print(rel)
    for r in rel[:-1]:
        print(f"起始公司：{r.from_co.id}，目标公司：{r.to_co.id}，开始时间：{r.start}，结束时间：{r.end}，状态：{r.status}")

print(f"供应链关系总数：{len(relations)}")


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

#endregion 数据读取与加载



#region ----------------------------------------两任期数据切换 （重要）----------------------
path_lines_all = relation_direct_delete_NO_lines(relations=relations,
                                       filter_start=datetime(2016,11,9),
                                       filter_end=datetime(2024,12,31))
path_lines = path_lines_all
len(path_lines)
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



len(path_lines)
for rel in path_lines[3000:4000]:
    print(rel)

#endregion -------------------------------------两任期数据切换 （重要）--------------------------




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

pattern_paths = find_by_status(path_lines,'transfer')

len(pattern_paths)



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

# 创建一个以月份为键的字典，键为指定时间间隔的datetime对象（精确到月初），值初始化为0
transfer_count_by_month = create_time_keyed_dict(
    start_date=datetime(2013, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='month'
    )







# country一栏里都是数目为1的列表，所以相当于 ==
cn_transfer_rel_by_year = create_time_keyed_dict(
    start_date=datetime(2013, 1, 1),
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



    # 使用方法创建年度字典
native_transfer_count_by_year = create_time_keyed_dict(
    start_date=datetime(2013, 1, 1),
    end_date=datetime(2024, 12, 31),
    increment='year'
    )
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

def plot_supply_chain_trend(values, values_2, bars_label, line_label, x_label, y_label_left, y_label_right, title):
    """
    绘制供应链转移趋势分析图。

    :param values: 柱状图数据
    :param values_2: 折线图数据
    :param bars_label: 柱状图图例标签
    :param line_label: 折线图图例标签
    :param x_label: 横轴标签
    :param y_label_left: 左侧纵轴标签
    :param y_label_right: 右侧纵轴标签
    :param title: 图表标题
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
    # 添加柱状图阴影效果
    for bar in bars:
        bar.set_alpha(0.8)
        bar.set_edgecolor('black')

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
    ax2.set_ylim(
        min(line_values) * 1.1 if not np.isnan(min(line_values)) else 0,
        max(line_values) * 1.1 if not np.isnan(max(line_values)) else 1
    )

    # 设置图表标题
    plt.title(title, fontsize=14, pad=20)
    lines_for_legend = [
        plt.Rectangle((0,0), 1, 1, fc='#1F77B4', alpha=0.8, hatch='////', edgecolor='black'),  # 柱状图代理句柄
        line  # 折线图句柄
    ]
    labels_for_legend = [bars_label, line_label]
 
    ax1.legend(lines_for_legend, labels_for_legend, loc='upper left', frameon=True)

    # 添加数据标签
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
    bars_label="转向中国的供应链数量",
    line_label="中国本土供应链数量",
    x_label="年份",
    y_label_left="转向中国的供应链数量",
    y_label_right="中国本土供应链数量",
    title="供应链转移趋势分析"
)

#endregion 年度时间趋势图可视化

