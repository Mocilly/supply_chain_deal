# region ######################################################  开始必备执行代码   


from datetime import datetime
import re
from collections import defaultdict

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

# 路径集合#
path_dic = {'company': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\company.json',
            'supply_chain': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\supply_relations.json',
            'complete_sc': r'.\调用文件\统计在华外资企业的可视化表\处理后的json文件\complete_supply_chains.json'}

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

# endregion######################################################  开始必备执行代码





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

437641
176675
252487

#region ----------------------------------------两任期数据切换 （重要）----------------------
# path_lines_all = relation_direct_delete_NO_lines(relations=relations,
#                                        filter_start=datetime(2016,11,9),
#                                        filter_end=datetime(2024,12,31))
# path_lines = path_lines_all
# len(path_lines)
## 涉及国家对数：permanent_break,transfer，recover = 68,56,20

path_lines_Trump = relation_direct_delete_NO_lines(relations=relations,
                                       filter_start=datetime(2016,11,9),
                                       filter_end=datetime(2020,12,14))
path_lines = path_lines_Trump
len(path_lines)
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





# country一栏里都是数目为1的列表，所以相当于 ==
native_transfer_rel = []
for i, rel in enumerate(pattern_paths):
    #home_region一栏里存在长度不为1的列表，由于可视化是用home_region + country，所以这里要用home_region+country从transfer中找到转向中国的供应链关系
    cn_mainland__SAR = ['CN','HK','MO']
    if (any(area in company_to_country[rel.to_co.id][0] for area in cn_mainland__SAR) or
        any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
        ):
        if 'Nation_Not_Found' in company_to_country[rel.from_co.id][0] or 'Nation_Not_Found' in company_to_country[rel.from_co.id][1]:
            continue
        else:    
            native_transfer_rel.append(rel)

len(native_transfer_rel)
transfer_to_cn_ratio = len(native_transfer_rel) / len(pattern_paths) * 100
print(f'贸易战期间转移到中国的供应链关系在全球供应链转移中的占比：{transfer_to_cn_ratio:.2f}%')


# #中国本土公司与中国本土公司 供应链转移占比
native_to_native_rel = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    if (any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR) and
        any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
        ):
        native_to_native_rel.append(rel)
len(native_to_native_rel)
cn_native_ratio = len(native_to_native_rel) / len(native_transfer_rel) * 100
print(f"中国本土公司与中国本土公司 供应链转移占比：{cn_native_ratio:.2f}%")


#中国本土公司与中国本土公司 供应链转移 中  转移方具备多国背景的比例
multiply_background_cn_cop = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    native_cn_check = (any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR) and 
                       any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR))
    if len(company_to_country[rel.from_co.id][0]) > 1 and native_cn_check:
        multiply_background_cn_cop.append(rel)
len(multiply_background_cn_cop)
cn_cop_multiply_background_ratio = len(multiply_background_cn_cop) / len(native_to_native_rel) * 100
print(f"中国本土公司与中国本土公司 供应链转移 中  转移方具备多国背景的比例：{cn_cop_multiply_background_ratio:.2f}%")



#供应链向中国转移的公司中，纯粹外资比例
pure_foreign_cop = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    foreign_check = not any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR)
    if (foreign_check and 
        company_to_country[rel.from_co.id][0] == company_to_country[rel.from_co.id][1] ):         
        #如果该外资是纯粹外资企业，不是在华外资，前后的home_region和country一致
        pure_foreign_cop.append(rel)
len(pure_foreign_cop)
pure_foreign_ratio = len(pure_foreign_cop) / len(native_transfer_rel) * 100
print(f"供应链向中国转移的公司中，纯粹外资比例：{pure_foreign_ratio:.2f}%")


#在华外资公司 在外资供应链向中国转移中占比 （供应链转移的目标公司为外资的在华公司）
foreign_cop_in_cn = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    foreign_check = not any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR)
    if (foreign_check and 
        any(area in company_to_country[rel.to_co.id][0] for area in cn_mainland__SAR)
        ):         
        foreign_cop_in_cn.append(rel)
len(foreign_cop_in_cn)
foreign_cop_in_cn_ratio = len(foreign_cop_in_cn) / len(native_transfer_rel) * 100
print(f"在华外资公司 在外资供应链向中国转移中占比：{foreign_cop_in_cn_ratio:.2f}%")

#  ----------下面是其他的占比------------------在华外资公司相关的占比------------------

#在华外资公司将供应链向中国转移的占比  （占全部向中国转移供应链的比例）
foreign_cop_in_cn_source = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    foreign_check = not any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR)
    if (foreign_check and 
        any(area in company_to_country[rel.from_co.id][0] for area in cn_mainland__SAR)
        ):         
        foreign_cop_in_cn_source.append(rel)
len(foreign_cop_in_cn_source)
foreign_cop_in_cn_source_ratio = len(foreign_cop_in_cn_source) / len(native_transfer_rel) * 100
print(f"在华外资公司将供应链向中国转移的占比  （占全部向中国转移供应链的比例）：{foreign_cop_in_cn_source_ratio:.2f}%")

# 在华外资公司将供应链转移给在华外资公司的占比  （占全部向中国转移供应链的比例）
foreign_cop_in_cn_source_to = []
for i, rel in enumerate(native_transfer_rel):
    cn_mainland__SAR = ['CN','HK','MO']
    foreign_check_from = not any(area in company_to_country[rel.from_co.id][1] for area in cn_mainland__SAR)
    foreign_check_to = not any(area in company_to_country[rel.to_co.id][1] for area in cn_mainland__SAR)
    if (foreign_check_from and foreign_check_to and 
        any(area in company_to_country[rel.from_co.id][0] for area in cn_mainland__SAR) and
        any(area in company_to_country[rel.to_co.id][0] for area in cn_mainland__SAR)
        ):         
        foreign_cop_in_cn_source_to.append(rel)
len(foreign_cop_in_cn_source_to)
foreign_cop_in_cn_source_to_ratio = len(foreign_cop_in_cn_source_to) / len(native_transfer_rel) * 100
print(f"在华外资公司将供应链转向在华外资公司的占比  （占全部向中国转移供应链的比例）：{foreign_cop_in_cn_source_to_ratio:.2f}%")

trump_data_num  = [ 1119,   681,   225,   407,  342,    0,    0]
trump_data_list = [ 9.80, 60.86, 33.04, 36.37, 30.56, 0.00, 0.00]
biden_data_num  = [ 8268,  3201,   316,  4848,  2497,   30,    4]
biden_data_list = [13.41, 38.72,  9.87, 58.64, 30.20, 0.36, 0.05]


# endregion


#region 可视化
import matplotlib.pyplot as plt
import numpy as np

def plot_supply_chain_analysis(title, label_ratio_name, categories, num_data, percent_data,num_max,percent_max):
    # 设置中文字体和图表风格
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 替换为系统中存在的支持中文的字体
    plt.rcParams['axes.unicode_minus'] = False

    # 创建画布和轴
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    # 固定左轴范围（数量轴）
    ax1.set_ylim(0, num_max)  # 根据数据最大值1200，设置上限为1400
    # 固定右轴范围（比例轴）
    ax2.set_ylim(0, percent_max)  # 原范围0.1-0.18，调整为0.08-0.18保持对称

    # 设置柱状图位置和宽度
    n_bars = 2                  # 每组柱数
    total_width = 0.1           # 每组总宽度占位
    bar_width = total_width / n_bars  # 单柱宽度
    group_spacing = 0.1         # 组间间距（关键参数）

    x = np.arange(len(categories)) * (n_bars * bar_width + group_spacing)  # 组中心坐标生成公式

    # 绘制柱状图
    bars1 = ax1.bar(x - bar_width / 2, num_data, bar_width, label='供应链数量', color='#1f77b4')
    bars2 = ax2.bar(x + bar_width / 2, percent_data, bar_width, label=label_ratio_name, color='#ff7f0e')

    # 坐标轴精确定位设置
    def setup_axis(ax, spine_color, label_text, label_coords):
        """统一设置坐标轴样式"""
        ax.spines[['top']].set_visible(False)  # 隐藏顶部边框
        ax.spines[['left', 'right']].set_visible(True)  # 确保左右边框可见

        # 设置指定边框
        if 'left' in ax.spines:
            ax.spines['left'].set_position(('outward', 10))
            ax.spines['left'].set_color(spine_color)
        if 'right' in ax.spines:
            ax.spines['right'].set_position(('outward', 10))
            ax.spines['right'].set_color(spine_color)

        ax.tick_params(axis='y', colors=spine_color, direction='out')
        ax.set_ylabel(label_text,
                      rotation=0,
                      fontsize=10,
                      color=spine_color,
                      labelpad=25)
        ax.yaxis.set_label_coords(*label_coords)  # 坐标轴标签定位

    # 设置左侧主坐标轴
    setup_axis(ax1, '#1f77b4', '供应链数量', (-0.03, 1.06))

    # 设置右侧次坐标轴
    setup_axis(ax2, '#ff7f0e', '比重', (1.03, 1.1))

    # 通用设置
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.tick_params(axis='x', length=0)  # 隐藏x轴刻度线
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)

    # 添加图例
    lines = [bars1, bars2]
    ax1.legend(lines, [l.get_label() for l in lines],
               loc='upper center',
               bbox_to_anchor=(0.5, -0.12),
               ncol=2,
               frameon=False)

    # 设置图表标题
    plt.title(title,
              pad=25,
              fontsize=12,
              fontweight='bold')

    # 调整布局
    plt.tight_layout()
    plt.show()

plot_supply_chain_analysis()

#endregion 可视化

import matplotlib.pyplot as plt
import numpy as np



 
def plot_combined_supply_chain_1():
    # 设置中文字体和图表风格
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
 
    # 数据配置
    main_categories = ['特朗普任期', '拜登任期']
    sub_categories = [
        '全球供应链转移分析',
        '本土企业间转移强度分析',
        '本土企业转移中跨国背景分析'
    ]
    label_ratio_names = [
        '贸易战期间中国在全球供应链转移中的承接比例（占全球供应链转移总量）',
        '中国本土企业间供应链转移在整体对华转移中的比重（含港澳地区关联企业）',
        '本土企业间转移中多国家背景企业的参与程度（跨国企业主导的境内转移比重）'
    ]
    
    # 数据集 (特朗普数据, 拜登数据)
    num_data = [
        [1119, 681, 225],
        [8268, 3201, 316]
    ]
    percent_data = [
        [9.80, 60.86, 33.04],
        [13.41, 38.72, 9.87]
    ]
    # 专业配色方案 + 阴影效果（修正版）
    num_color = '#2A5C8B'  # 主色调
    num_edge = '#1A3C5B'   # 边框色
    num_hatch = '////'     # 斜线纹理
 
    percent_colors = [
        ('#E69138', '#B5712C', '....'),  # 全球供应链
        ('#6B8E23', '#557817', 'xxxx'),  # 本土企业
        ('#9370DB', '#6A5ACD', '++++')   # 跨国背景
    ]
 
    # 创建画布和轴
    fig, ax1 = plt.subplots(figsize=(16, 8))
    ax2 = ax1.twinx()
 
    # 坐标轴范围
    num_max = 10000
    percent_max = 70
    ax1.set_ylim(0, num_max)
    ax2.set_ylim(0, percent_max)
 
    # 柱状图参数
    bar_width = 0.15
    group_spacing = 1.5  # 主分类间距
    sub_group_spacing = 0.1  # 子分类间距
 
    # 计算x轴位置
    base_positions = np.array([0, group_spacing])  # 两大分类基础位置
    x_ticks = []
    
    # 绘制柱状图
    for main_idx in range(2):  # 遍历主分类
        for sub_idx in range(3):  # 遍历子分类
            x = base_positions[main_idx] + sub_idx * (bar_width*2 + sub_group_spacing)
            
            # 绘制数量柱（带阴影效果）
            ax1.bar(x - bar_width/2, 
                    num_data[main_idx][sub_idx], 
                    width=bar_width,
                    facecolor=num_color,
                    edgecolor=num_edge,
                    linewidth=1.2,
                    hatch=num_hatch)
        
            # 绘制比例柱（带阴影效果）
            ax2.bar(x + bar_width/2,
                    percent_data[main_idx][sub_idx],
                    width=bar_width,
                    facecolor=percent_colors[sub_idx][0],
                    edgecolor=percent_colors[sub_idx][1],
                    linewidth=1.2,
                    hatch=percent_colors[sub_idx][2])
 
 
    # 设置坐标轴样式
    def setup_axis(ax, spine_color, label_text, label_coords):
        ax.spines[['top']].set_visible(False)
        ax.spines[['left', 'right']].set_visible(True)
        if 'left' in ax.spines:
            ax.spines['left'].set_position(('outward', 10))
            ax.spines['left'].set_color(spine_color)
        if 'right' in ax.spines:
            ax.spines['right'].set_position(('outward', 10))
            ax.spines['right'].set_color(spine_color)
        ax.tick_params(axis='y', colors=spine_color, direction='out')
        ax.set_ylabel(label_text,
                      rotation=0,
                      fontsize=10,
                      color=spine_color,
                      labelpad=25)
        ax.yaxis.set_label_coords(*label_coords)
 
    setup_axis(ax1, 'gray', '供应链数量', (-0.03, 1.03))
    setup_axis(ax2, 'gray', '百分比', (1.03, 1.05))
 
    # 设置分类标签系统
    ax1.set_xticks([])  # 清空默认x轴标签
    
    # 添加主分类标签（特朗普/拜登）
    for main_idx, pos in enumerate(base_positions):
        ax1.text(pos + (3*(bar_width*2 + sub_group_spacing))/2 - bar_width, 
                -0.05 * num_max, 
                main_categories[main_idx],
                ha='center', va='top',
                fontsize=11,
                fontweight='bold')
    
    # 修改后的子分类标签（三个分析类型）
    for sub_idx in range(3):
        # 计算每个小组的起始x坐标（数量柱左边缘）
        # 特朗普任期
        x_start_trump = base_positions[0] + sub_idx*(bar_width*2 + sub_group_spacing) - bar_width*1
        ax1.text(x_start_trump, -0.01 * num_max,
                sub_categories[sub_idx],
                ha='left',  # 左对齐确保文字起始位置匹配
                va='top',
                fontsize=8)
        
        # 拜登任期
        x_start_biden = base_positions[1] + sub_idx*(bar_width*2 + sub_group_spacing) - bar_width*1
        ax1.text(x_start_biden, -0.01 * num_max,
                sub_categories[sub_idx],
                ha='left',
                va='top',
                fontsize=8)
 
    # 修正后的图例创建部分
    legend_elements = [
        plt.Rectangle((0,0),1,1, 
                     facecolor=num_color,
                     edgecolor=num_edge,
                     hatch=num_hatch,
                     label="供应链数量"),
        *[plt.Rectangle((0,0),1,1,
                       facecolor=percent_colors[i][0],
                       edgecolor=percent_colors[i][1],
                       hatch=percent_colors[i][2],
                       label=label_ratio_names[i]) 
         for i in range(3)]
    ]
    
    ax1.legend(handles=legend_elements, 
              loc='upper left',
              bbox_to_anchor=(0.5, 1),
              frameon=False,
              fontsize=8)
 
        # 设置图表标题
    plt.title('本土企业供应链转移分析',
              pad=25,
              fontsize=18,
              fontweight='bold')
    # 添加网格和调整布局
        # 添加PDF矢量格式输出
    plt.savefig('本土企业转移情况分析.pdf', 
               format='pdf',
               bbox_inches='tight')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.subplots_adjust(right=0.8)
    plt.show()
 
plot_combined_supply_chain_1()




def plot_combined_supply_chain_2():
    # 设置中文字体和图表风格
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 数据配置（扩展为4组）
    main_categories = ['特朗普任期', '拜登任期']
    sub_categories = [
        '纯粹外资企业供应链转移分析',
        '外资在华企业承接供应链转移分析',
        '外资在华企业本土化转移分析',
        '在华外资体系内部调整分析'
    ]
    label_ratio_names = [
        '外资企业直接参与对华供应链转移中的参与比例（外资直接转移供应链至中国的比重）',
        '外资企业供应链对华转移中在华分支机构的承接比例（目标端为外资中国子公司）',
        '在华外资企业作为转移来源方在整体对华转移中的比重（发起方为外资中国子公司）',
        '在华外资企业间供应链转移在整体对华转移中的占比（外资体系内部资源调配）'
    ]
    
    # 数据集 (特朗普数据, 拜登数据)
    num_data = [
        [407,  342,    0,    0],
        [4848,  2497,   30,    4]
    ]
    percent_data = [
        [36.37, 30.56, 0.00, 0.00],
        [58.64, 30.20, 0.36, 0.05]
    ]

    # 配色方案扩展
    num_color = '#2A5C8B'  # 主色调保持
    num_edge = '#1A3C5B'   
    num_hatch = '////'     

    # 新增第四组配色（青色系）
    percent_colors = [
        ('#E69138', '#B5712C', '....'),  # 全球供应链
        ('#6B8E23', '#557817', 'xxxx'),  # 本土企业
        ('#9370DB', '#6A5ACD', '++++'),  # 跨国背景
        ('#4ECDC4', '#3A9A94', '||||')   # 新增技术合作
    ]

    # 创建画布和轴
    fig, ax1 = plt.subplots(figsize=(18, 8))  # 加宽画布
    ax2 = ax1.twinx()

    # 坐标轴范围调整
    num_max = 10000  # 提升上限
    percent_max = 70
    ax1.set_ylim(0, num_max)
    ax2.set_ylim(0, percent_max)

    # 柱状图参数优化
    bar_width = 0.12  # 缩窄柱宽
    group_spacing = 1.5  
    sub_group_spacing = 0.08  # 增加子组间距

    # 计算x轴位置（适应4组）
    base_positions = np.array([0, group_spacing])  
    
    # 绘制柱状图（改为4组）
    for main_idx in range(2):  
        for sub_idx in range(4):  # 修改为4
            x = base_positions[main_idx] + sub_idx * (bar_width*2 + sub_group_spacing)
            
            # 数量柱
            ax1.bar(x - bar_width/2, 
                    num_data[main_idx][sub_idx], 
                    width=bar_width,
                    facecolor=num_color,
                    edgecolor=num_edge,
                    linewidth=1.2,
                    hatch=num_hatch)
            
            # 比例柱
            ax2.bar(x + bar_width/2,
                    percent_data[main_idx][sub_idx],
                    width=bar_width,
                    facecolor=percent_colors[sub_idx][0],
                    edgecolor=percent_colors[sub_idx][1],
                    linewidth=1.2,
                    hatch=percent_colors[sub_idx][2])

    # 设置坐标轴样式
    def setup_axis(ax, spine_color, label_text, label_coords):
        ax.spines[['top']].set_visible(False)
        ax.spines[['left', 'right']].set_visible(True)
        if 'left' in ax.spines:
            ax.spines['left'].set_position(('outward', 10))
            ax.spines['left'].set_color(spine_color)
        if 'right' in ax.spines:
            ax.spines['right'].set_position(('outward', 10))
            ax.spines['right'].set_color(spine_color)
        ax.tick_params(axis='y', colors=spine_color, direction='out')
        ax.set_ylabel(label_text,
                      rotation=0,
                      fontsize=10,
                      color=spine_color,
                      labelpad=25)
        ax.yaxis.set_label_coords(*label_coords)
 
    setup_axis(ax1, 'gray', '供应链数量', (-0.03, 1.03))
    setup_axis(ax2, 'gray', '百分比', (1.03, 1.05))
 
    # 设置分类标签系统
    ax1.set_xticks([])  # 清空默认x轴标签
    
    # 分类标签系统调整
    # 主分类标签
    for main_idx, pos in enumerate(base_positions):
        ax1.text(pos + (3*(bar_width*2 + sub_group_spacing))/2 - bar_width*1,  # 改为4组
                -0.1 * num_max, 
                main_categories[main_idx],
                ha='center', 
                va='top',
                fontsize=11,
                fontweight='bold')
    
    # 子分类标签定位（4组）
    for sub_idx in range(4):  # 改为4
        # 特朗普任期
        x_start_trump = base_positions[0] + sub_idx*(bar_width*2 + sub_group_spacing) - bar_width*1.2
        ax1.text(x_start_trump, -0.01 * num_max,
                sub_categories[sub_idx],
                rotation = -15,
                ha='left', 
                va='top',
                fontsize=8)
        
        # 拜登任期
        x_start_biden = base_positions[1] + sub_idx*(bar_width*2 + sub_group_spacing) - bar_width*1.2
        ax1.text(x_start_biden, -0.01 * num_max,
                sub_categories[sub_idx],
                rotation = -15,
                ha='left',
                va='top',
                fontsize=8)

    # 图例扩展
    legend_elements = [
        plt.Rectangle((0,0),1,1, 
                     facecolor=num_color,
                     edgecolor=num_edge,
                     hatch=num_hatch,
                     label="供应链数量"),
        *[plt.Rectangle((0,0),1,1,
                       facecolor=percent_colors[i][0],
                       edgecolor=percent_colors[i][1],
                       hatch=percent_colors[i][2],
                       label=label_ratio_names[i]) 
         for i in range(4)]  # 改为4
    ]
    
    ax1.legend(handles=legend_elements, 
              loc='upper left',
              bbox_to_anchor=(0.5, 1),  # 调整位置
              frameon=False,
              fontsize=8)
    # 标题
    plt.title('外资企业供应链转移分析',
              pad=25,
              fontsize=18,
              fontweight='bold')
    # 调整布局
    plt.savefig('外资企业转移情况分析.pdf', 
            format='pdf',
            bbox_inches='tight')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.subplots_adjust(right=0.8)  # 增加右侧空间
    plt.show()

plot_combined_supply_chain_2()