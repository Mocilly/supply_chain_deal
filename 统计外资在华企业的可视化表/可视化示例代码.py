import plotly.graph_objects as go
import pandas as pd

# 示例数据（需替换为真实数据）
df = pd.DataFrame({
    "Year": [2018, 2018, 2019, 2019, 2020, 2020],
    "Type": ["迁出", "迁入", "迁出", "迁入", "迁出", "迁入"],
    "Country": ["越南", "德国", "印度", "韩国", "墨西哥", "日本"],
    "Value": [5, 3, 8, 4, 6, 2],
    "Start_Lat": [35.8617, 51.1657, 35.8617, 35.9078, 35.8617, 36.2048],
    "Start_Lon": [104.1954, 10.4515, 104.1954, 127.7669, 104.1954, 138.2529],
    "End_Lat": [14.0583, 35.8617, 20.5937, 35.8617, 23.6345, 35.8617],
    "End_Lon": [108.2772, 104.1954, 78.9629, 104.1954, -102.5528, 104.1954],
})

# 创建动态帧
years = df['Year'].unique()
frames = []
for year in years:
    df_year = df[df['Year'] == year]
    lines = []
    for _, row in df_year.iterrows():
        line = go.Scattergeo(
            lon=[row['Start_Lon'], row['End_Lon']],
            lat=[row['Start_Lat'], row['End_Lat']],
            mode='lines',
            line=dict(
                width=row['Value'] * 2,  # 线宽反映规模
                color='red' if row['Type'] == '迁出' else 'green'
            ),
            hoverinfo='text',
            text=f"{row['Country']}<br>{row['Type']}金额: {row['Value']}亿美元",
            showlegend=False
        )
        lines.append(line)
    frames.append(go.Frame(data=lines, name=str(year)))

# 基础地图（中国高亮）
fig = go.Figure(
    data=[
        go.Scattergeo(
            lon=[104.1954], lat=[35.8617],
            mode='markers',
            marker=dict(size=12, color='blue'),
            text="中国",
            hoverinfo='text'
        )
    ],
    frames=frames
)

# 动画和时间轴设置
fig.update_layout(
    title_text="外资在华供应链转移趋势（2018-2020）",
    geo=dict(
        projection_type='natural earth',
        showcountries=True,
        countrycolor='gray',
        landcolor='lightgray'
    ),
    updatemenus=[dict(
        type='buttons',
        buttons=[dict(
            label='播放',
            method='animate',
            args=[None, dict(frame=dict(duration=1000, redraw=True))]
        )]
    )],
    sliders=[dict(
        steps=[dict(args=[[str(year)], dict(mode='immediate')], label=str(year)) for year in years]
    )]
)

fig.show()