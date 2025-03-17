# region ######################################################  开始必备执行代码   
import os

import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict
from collections import defaultdict


# pd.options.display.max_rows = 10000  # 终端显示10000行


def Save(fileName,path,df):
    #.将上面的df保存为xlsx表格
    fileName = fileName+'.xlsx'
    savePath = ''.join([path,fileName])
    wr = pd.ExcelWriter(savePath)#输入即将导出数据所在的路径并指定好Excel工作簿的名称
    df.to_excel(wr, index = False)

    wr._save()



# 路径集合#
path_dic = {'foreign_data':r"C:\Users\Mocilly\Desktop\研创平台课题项目\数据\factset\data",
            'cop_data':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\上市公司数据',
            'middle':r'C:\Users\Mocilly\Desktop\研创平台课题项目\数据\中间文件',
            'save':r'C:/Users/Mocilly/Desktop/研创平台课题项目/数据//',
            }

#endregion 


# 示例数据输入
path_lines = [
    "S1→C1(permanent_break)[limit_day_break]",
    "S1→C1(permanent_break)[limit_day_break]",
    "S1→C2(permanent_break)[beyond_day_continue]",
    "S1→C3(transfer)[beyond_day_continue]",
    "S2→C2(active)[limit_day_break]",
    "S2→C2(recovered)[limit_day_break]",
    "S3→C4(active)[limit_day_break]",
    "S3→C4(active) → C4→C5(active)[limit_day_break]",
    "S3→C4(active) → C4→C5(active) → C5→C6(active)[limit_day_break]",
    "C4→C5(active)[limit_day_break]",
    "C4→C5(active) → C5→C6(active)[limit_day_break]",
    "C5→C6(active)[limit_day_break]",
    # 其他路径...
]
# 公司到国家的映射（需根据实际数据补充）
company_to_country = {
    "S1": "China", "C1": "USA",
    "S2": "Germany", "C2": "France",
    "S3": "Japan", "C3": "South Korea",
    "C4": "India", "C5": "Italy", "C6": "UK"
}

import re
import plotly.graph_objects as go

# 预设国家坐标（示例数据，实际需要更精确）
country_coords = {
    "China": [104.1954, 35.8617],
    "USA": [-95.7129, 37.0902],
    "Germany": [10.4515, 51.1657],
    "France": [2.2137, 46.2276],
    "Japan": [138.2529, 36.2048],
    "South Korea": [127.7669, 35.9078],
    "India": [78.9629, 20.5937],
    "Italy": [12.5674, 41.8719],
    "UK": [-3.43597, 55.3781]
}

# 解析产业链数据
connections = []
for line in path_lines:
    segments = line.split(' → ')
    current_color = 'blue'  # 默认颜色
    for seg in segments:
        match = re.match(r'(\w+)→(\w+)\((.*?)\)', seg)
        if not match: continue
        
        start_comp, end_comp, status = match.groups()
        start_country = company_to_country.get(start_comp)
        end_country = company_to_country.get(end_comp)
        
        if not start_country or not end_country: continue

        # 确定线条样式
        line_style = 'solid'
        color = current_color
        
        if 'permanent_break' in status:
            line_style = 'dash'
        if 'transfer' in status:
            color = 'red'
            current_color = 'red'  # 影响后续链条
        
        connections.append({
            'start': start_country,
            'end': end_country,
            'color': color,
            'style': line_style
        })



# 创建可视化轨迹
traces = []

# 先添加虚线轨迹（保证绘制顺序）
for line_style in ['dash', 'solid']:
    for color in ['blue', 'red']:
        line_segments = [
            c for c in connections 
            if c['style'] == line_style and c['color'] == color
        ]
        
        if not line_segments: continue
        
        lons, lats = [], []
        for conn in line_segments:
            start = country_coords[conn['start']]
            end = country_coords[conn['end']]
            lons += [start[0], end[0], None]
            lats += [start[1], end[1], None]
        
        traces.append(go.Scattergeo(
            lon = lons,
            lat = lats,
            mode = 'lines',
            line = dict(width=1.5, color=color, dash=line_style),
            hoverinfo='none',
            showlegend=False
        ))

# 添加国家节点
country_trace = go.Scattergeo(
    lon = [c[0] for c in country_coords.values()],
    lat = [c[1] for c in country_coords.values()],
    mode = 'markers+text',
    marker = dict(size=12, color='black'),
    text = list(country_coords.keys()),
    textposition = 'top center',
    hoverinfo='text',
    showlegend=False
)
traces.append(country_trace)

# 配置地图
fig = go.Figure(data=traces)
# 修改地理参数部分为：
fig.update_geo(
    resolution=50,  # 提高地图分辨率
    visible=True,  # 确保地理图层可见
    countrycolor="Black",  # 使用高对比度的红色
    countrywidth=3,  # 加粗边界线
    landcolor="rgb(245,245,220)",  # 米色陆地
    oceancolor="rgb(173,216,230)",  # 浅蓝色海洋
    coastlinewidth=2,  # 加粗海岸线
    coastlinecolor="navy"  # 蓝色海岸线
)

fig.update_layout(
    geo=dict(
        showcountries=True,  # 强制显示国家边界
        projection_type="natural earth",
        scope="world",  # 明确指定显示范围
        bgcolor="rgba(255,255,255,0.9)"  # 设置画布背景
    )
)

fig.show()