
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



# 建立转移的时间月份字典，从2013年1月份到2024年12月份每个月份创建一个年份+月份的键
transfer_month_count = dict()
start_date = datetime(2013, 1, 1)
end_date = datetime(2024, 12, 31)
current_date = start_date
 
while current_date <= end_date:
    # 直接使用 datetime 对象作为键（精确到月初）
    key = current_date.replace(day=1)
    transfer_month_count[key] = 0
    # 使用 dateutil 的 relativedelta 安全增加1个月
    current_date += relativedelta(months=1)

# 计数函数
def increment_transfer_month_count(event_time: datetime,transfer_dict:dict) -> None:
    month_key = event_time.replace(day=1)
    transfer_dict[month_key] += 1





# 建立转移的时间年度字典，从2013年到2024年每年创建一个年份键（每年1月1日）
transfer_year_count = dict()
start_date = datetime(2013, 1, 1)
end_date = datetime(2024, 12, 31)
current_date = start_date
 
# 初始化字典，键为每年1月1日的datetime对象
while current_date <= end_date:
    transfer_year_count[current_date] = 0  # 直接以每年1月1日作为键
    current_date += relativedelta(years=1)  # 安全递增年份
 
# 计数函数
def increment_transfer_year_count(event_time: datetime) -> None:
    """当出现符合时间点时，对应年份的计数+1"""
    # 生成年度键（每年1月1日）
    year_key = datetime(event_time.year, 1, 1)
    # 检查键是否存在（防止意外输入）
    if year_key in transfer_year_count:
        transfer_year_count[year_key] += 1
    else:
        print(f"警告：时间 {event_time} 超出统计范围（2013-2024）")




for i, rel in enumerate(pattern_paths):
    #中国本土公司间建立转移供应链关系 时间计数
    cn_mainland__SAR = ['CN','HK','MO']
    if (any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR) or
        any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
        ):
        if 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]:
            continue
        else:    
            increment_transfer_year_count(rel.start)


for time, value in transfer_year_count.items():
    print(f"年份：{time.year}, 转移数量：{value}")



#region---------------年度时间趋势图可视化
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter
import numpy as np
from datetime import datetime

# 设置中文字体和行业报告风格
plt.rcParams['font.sans-serif'] = ['SimHei']  # 适用于Windows系统
plt.rcParams['axes.unicode_minus'] = False·
plt.style.use('ggplot')

# 准备数据（示例数据，需替换实际数据）
years = sorted(transfer_year_count.keys())
values = [transfer_year_count[year] for year in years]

# 计算增长率
growth_rates = [(values[i] - values[i-1])/values[i-1] if i>0 else 0 for i in range(len(values))]
growth_rates[0] = np.nan  # 首年无增长率

# 创建画布和坐标轴
fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()

# 绘制柱状图（左侧轴）
bars = ax1.bar(
    [y.strftime('%Y') for y in years],
    values,
    color='#1F77B4',
    edgecolor='black',
    alpha=0.8,
    hatch='////',
    label='转移数量'
)
# 添加柱状图阴影效果
for bar in bars:
    bar.set_alpha(0.8)
    bar.set_edgecolor('black')

# 绘制折线图（右侧轴）
line, = ax2.plot(
    [y.strftime('%Y') for y in years],
    growth_rates,
    color='#2CA02C',
    linestyle='--',
    marker='o',
    markersize=8,
    linewidth=2,
    markerfacecolor='white',
    markeredgewidth=2,
    label='增长率'
)

# 设置坐标轴格式
ax1.set_xlabel('年份', fontsize=12)
ax1.set_ylabel('数量', fontsize=12)
ax2.set_ylabel('增长率', fontsize=12)
ax2.yaxis.set_major_formatter(PercentFormatter(1.0))  # 转换为百分比格式

# 设置双轴刻度范围
ax1.set_ylim(0, max(values)*1.2)
ax2.set_ylim(min(growth_rates)*1.1 if not np.isnan(min(growth_rates)) else 0, 
            max(growth_rates)*1.1 if not np.isnan(max(growth_rates)) else 1)

# 设置图表标题
plt.title('供应链转移趋势分析（2013-2024）', fontsize=14, pad=20)

# 合并图例
lines = [bars[0], line]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', frameon=True)

# 添加数据标签
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}',
             ha='center', va='bottom')

# 设置网格线
ax1.grid(axis='y', linestyle='--', alpha=0.7)
ax2.grid(visible=False)

# 调整布局
plt.tight_layout()
plt.show()
#endregion 年度时间趋势图可视化

