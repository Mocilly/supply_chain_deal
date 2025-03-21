# region ###################################################### 核心代码 
import re
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

# 生成测试数据（包含多层级永久断裂案例）
path_lines = [
    # 三级永久断裂链条（中国→印度→法国→英国）
    "S1→C4(permanent_break) → C4→C5(permanent_break) → C5→C6(permanent_break)",
    # 二级永久断裂链条（中国→美国→德国）
    "S2→C1(permanent_break) → C1→C2(permanent_break)",
    # 单层转移案例
    "S3→C3(transfer)",
    # 混合状态案例
    "S1→C2(permanent_break) → C2→C5(transfer) → C5→C6(recovered)",
    # 恢复案例
    "S2→C5(recovered)",
]

# 公司-国家映射表（所有S开头公司属于中国）
company_to_country = {
    **{f"S{i}": "China" for i in range(1,4)},  # S1-S3均来自中国
    "C1": "USA", "C2": "Germany", "C3": "Japan",
    "C4": "India", "C5": "France", "C6": "UK"
}

# 国家地理坐标（经度，纬度）
country_coords = {
    "China": [104.1954, 35.8617],
    "USA": [-95.7129, 37.0902],
    "Germany": [10.4515, 51.1657],
    "Japan": [138.2529, 36.2048],
    "India": [78.9629, 20.5937],
    "France": [2.2137, 46.2276],
    "UK": [-3.43597, 55.3781]
}

# region ###################################################### 统计逻辑实现
def analyze_paths(path_lines):
    """
    供应链状态分析函数
    
    功能：
    1. 永久断裂(permanent_break)处理逻辑：
       - 跟踪从中国开始的连续断裂链条
       - 按层级加权（第1层x1，第2层x0.5，第3层x0.1）
    2. 转移(transfer)/恢复(recovered)处理逻辑：
       - 仅统计中国直接发起的单个状态变化
    """
    status_records = {
        'permanent_break': defaultdict(float),
        'transfer': defaultdict(float),
        'recovered': defaultdict(float)
    }

    for path in path_lines:
        # 分解路径为独立段（忽略时间标记）
        segments = []
        for seg in path.split(' → '):
            if match := re.match(r'(\w+)→(\w+)\((\w+)\)', seg.split('[')[0]):
                segments.append(match.groups())

        current_chain = None  # 跟踪当前断裂链条状态

        for start_comp, end_comp, status in segments:
            start_country = company_to_country.get(start_comp)
            end_country = company_to_country.get(end_comp)
            
            # 处理永久断裂状态
            if status == 'permanent_break':
                if current_chain:  # 延续现有链条
                    layer = current_chain['layer'] + 1
                    weight = 1.0 if layer == 1 else 0.5 if layer == 2 else 0.1
                    current_chain['layer'] = layer
                else:  # 新链条必须起始于中国
                    if start_country == 'China':
                        layer = 1
                        weight = 1.0
                        current_chain = {'layer': layer}
                    else:
                        continue  # 非中国起始的断裂不统计
                
                # 记录国家间断裂关系及加权值
                status_records['permanent_break'][(start_country, end_country)] += weight
            
            # 处理转移/恢复状态（仅中国直接发起）
            elif start_country == 'China':
                if status == 'transfer':
                    status_records['transfer'][(start_country, end_country)] += 1.0
                elif status == 'recovered':
                    status_records['recovered'][(start_country, end_country)] += 1.0
                
                # 状态变化中断永久断裂链条
                current_chain = None
            
            # 非永久断裂状态中断链条
            else:
                current_chain = None

    return status_records

status_data = analyze_paths(path_lines)
# endregion

# endregion
# endregion
def create_map_figure(status_data):
    traces = []
    max_line_width = 15
    color_mapping = {
        'permanent_break': 'rgb(230,50,50)',
        'transfer': 'rgb(50,180,50)',
        'recovered': 'rgb(50,50,230)'
    }

    # 国家节点增强显示
    country_trace = go.Scattergeo(
        lon=[c[0] for c in country_coords.values()],
        lat=[c[1] for c in country_coords.values()],
        mode='markers+text',
        marker=dict(
            size=18,
            color='rgba(30,30,30,0.9)',
            line=dict(width=1, color='white')
        ),
        text=[f"<b>{k}</b>" for k in country_coords],
        textfont=dict(
            color='rgba(255,255,255,0.9)',
            family='Arial Black',
            size=11
        ),
        textposition='top center',
        hoverinfo='text',
        showlegend=False,
        meta={'status': 'base'}
    )
    traces.append(country_trace)

    # 生成状态轨迹
    for status in ['permanent_break', 'transfer', 'recovered']:
        data = status_data[status]
        if not data:
            continue
            
        max_weight = max(data.values(), default=1)
        
        for (start, end), weight in data.items():
            # 坐标验证
            start_coord = country_coords.get(start, [None, None])
            end_coord = country_coords.get(end, [None, None])
            if None in start_coord + end_coord:
                continue
                
            # 动态线宽
            line_width = (weight / max_weight) * max_line_width
            line_width = max(min(line_width, 15), 1.5)
            
            traces.append(go.Scattergeo(
                lon=[start_coord[0], end_coord[0], None],
                lat=[start_coord[1], end_coord[1], None],
                mode='lines',
                line=dict(
                    width=line_width,
                    color=color_mapping[status],
                    dash='dash' if status == 'permanent_break' else 'solid'
                ),
                opacity=0.85,
                hoverinfo='text',
                hovertext=f"{start}→{end}<br>辐射层级：{get_layer(weight)}<br>权重：{weight:.2f}",
                visible=(status == 'permanent_break'),
                meta={'status': status}
            ))

    # 交互控件优化
    buttons = []
    visible_states = ['permanent_break', 'transfer', 'recovered']
    for status in visible_states:
        visible = [
            (t.meta.get('status') == status) if 'meta' in t 
            else (status == 'permanent_break')  # 默认显示第一个状态
            for t in traces
        ]
        buttons.append(dict(
            label=f"{status.capitalize()}状态",
            method='update',
            args=[{'visible': visible}],
            execute=True
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title_text='全球供应链状态分析系统',
        updatemenus=[dict(
            type='dropdown',
            direction='down',
            active=0,
            buttons=buttons,
            x=0.12,
            xanchor='left',
            y=1.15
        )],
        geo=dict(
            resolution=110,
            showframe=True,
            showcoastlines=True,
            coastlinecolor='rgb(100,100,100)',
            landcolor='rgb(245,245,240)',
            oceancolor='rgb(220,240,255)'
        ),
        height=750,
        margin=dict(l=0, r=0, t=90, b=0)
    )
    return fig

def get_layer(w):
    """权重值转中文层级"""
    if w >= 0.9: return 'Ⅰ级（直接辐射）'
    elif w >= 0.4: return 'Ⅱ级（次级影响）'
    else: return 'Ⅲ级（远端传导）'

    
# 生成可视化图表
fig = create_map_figure(status_data)
fig.show()