import jieba
from collections import Counter
import matplotlib.pyplot as plt
import re  # 导入正则表达式模块

# 示例文本（实际使用时可替换为任意中文文本）
sample_text = """
近年来，人工智能（AI）技术以惊人的速度发展，深刻改变着人类社会的方方面面。从智能手机的语音助手到自动驾驶汽车，从医疗影像诊断到金融风险评估，AI算法正在渗透到各行各业。深度学习、神经网络和自然语言处理等技术突破，使得计算机能够处理海量数据并模拟人类认知能力。

在核心技术领域，机器学习始终是人工智能的基石。通过监督学习、无监督学习和强化学习等范式，算法可以从标注数据或交互经验中不断优化自身性能。例如，谷歌的AlphaGo通过数百万次自我对弈，最终战胜了人类顶尖围棋选手；特斯拉的自动驾驶系统则通过实时分析道路摄像头和传感器数据，实现了复杂路况下的决策能力。

数据作为AI的燃料，其重要性不言而喻。互联网每天产生的数万亿字节数据——包括文本、图像、视频和用户行为记录——为模型训练提供了丰富素材。但与此同时，数据隐私和伦理问题也引发广泛讨论。欧盟的《通用数据保护条例》（GDPR）正是为了平衡技术创新与个人权利而诞生的代表性法规。

行业应用方面，AI已在多个领域取得突破：

医疗健康：IBM Watson能辅助医生分析病历和医学论文，提供个性化诊疗建议
金融科技：蚂蚁金服的风控系统利用机器学习识别欺诈交易，准确率超过99%
制造业：工业机器人通过计算机视觉实现精密零件质检，效率比人工提升20倍
尽管前景广阔，AI仍面临诸多挑战。算法偏见、算力消耗和可解释性不足等问题制约着技术落地。例如，人脸识别系统在不同肤色群体中的准确率差异，暴露了训练数据多样性的缺失；而大型语言模型（如GPT-3）生成虚假信息的风险，则突显了伦理规范的重要性。

未来十年，人工智能将与量子计算、脑机接口等前沿技术深度融合。中国科技企业如百度和阿里巴巴已投入数十亿美元研发AI芯片，试图突破硬件瓶颈。学术界则致力于开发更接近人类思维的通用人工智能（AGI），尽管这一目标可能仍需数十年时间。
"""

'''
一、基本定义
典型中文停用词：
"的"、"是"、"在"、"了"、"和"、"我们"、"这个"、"可以"、"年"、"月"

典型英文停用词：
"the", "a", "an", "in", "on", "of", "and", "is", "are"

二、为何需要停用词？
提升分析效率：
减少无意义词汇的计算量（高频词可能占文本30%以上）

增强结果准确性：
避免低价值词汇影响关键词提取（如："然后"在报告中重复出现但无实际意义）

改善可视化效果：
词云中突出真正重要的词汇（否则可能被"的"等词占据视觉焦点）
'''
# 自定义停用词表（可根据需求扩展）
stopwords = set([
    '的', '在', '和', '了', '是', '较', '达到', '包括', '背景', '下', '元', 
    '同比', '年度', '每', '股', '建议', '持续', '加大', '实现'
])

def word_frequency_analysis(text):
    # 文本预处理
    text = re.sub(r'\d+', '', text)  # 去除数字
    text = re.sub(r'[^\u4e00-\u9fa5]', ' ', text)  # 只保留中文
    
    # 精确模式分词
    words = jieba.lcut(text)
    
    # 过滤停用词和单字
    filtered = [
        word for word in words if len(word) > 1 and word not in stopwords
    ]
    
    # 词频统计
    return Counter(filtered)


# 执行分析
word_counts = word_frequency_analysis(sample_text)

# 打印前10高频词
print("Top 10 高频词汇:")
for word, count in word_counts.most_common(10):
    print(f"{word}: {count}次")

# 可视化设置
# plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置全局字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# # 生成词云
from wordcloud import WordCloud
wc = WordCloud(
    font_path='C:\Windows\Fonts\simhei.ttf',  # 替换为你的中文字体路径
    width=800, 
    height=600,
    background_color='white'
).generate_from_frequencies(word_counts)


plt.figure(figsize=(12,6))

# 词云图
plt.subplot(121)
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.title("词云分析")

# 条形图
plt.subplot(122)
top_words = word_counts.most_common(10)
words = [w[0] for w in top_words]
counts = [w[1] for w in top_words]
plt.barh(words[::-1], counts[::-1])  # 降序显示
plt.title("词频TOP10")
plt.xlabel("出现次数")

plt.tight_layout()
plt.show()
