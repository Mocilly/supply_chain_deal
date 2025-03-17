# region ######################################################  开始必备执行代码   
import os
import numpy as np
import pandas as pd
import datetime as dt
#取消padas导出成excel时的默认表头格式（这会导致列单元格格式调整失败，）
pd.io.formats.excel.ExcelFormatter.header_style = None

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


month_dict = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,
              'oct':10,'nov':11,'dec':12}

#endregion 

#region -----1.公司 国家所属
base_dir = path_dic['foreign_data']

# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]

# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[0]

df_cop = pd.read_stata(files[0]) # 公司df
df_cop.columns
df_cop.index


cop_set = set()  # 公司 集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_cop.index:
    cop_set.add(df_cop.loc[i,'id'])
    print(f'已解决{i+1}')

# region 将公司的国家属地保存下来

cop_region = dict.fromkeys(list(cop_set),0)

all_items = len(cop_region)

count = 0 #计数变量
cop_change = [] #公司地址变更
for key,value in cop_region.items():

    df = df_cop[df_cop['id'] == key] #取出那些公司的信息存储在df中
    df.reset_index(drop = True,inplace = True)
    region_set = set() #用来看公司地址是否变动的集合
    for i in df.index:
        region_set.add(df.loc[i,'home_region'])
        cop_set.add(df_cop.loc[i,'id'])
    if len(region_set) > 1: #如果所属国家不止一个，则添加进cop_change
        cop_change.append(key)
    else: #否则就将所属国家添加进字典中
        cop_region[key] = df.loc[0,'home_region']
    print(f'已解决{count+1}/{all_items}')
    count+=1

cop_region
df = pd.DataFrame.from_dict(cop_region, orient='index', columns=['region'])
df.reset_index(inplace=True)
df.rename(columns={'index': 'id'},inplace=True)
df
Save('1.精简删减过后的id—region表',path_dic['save'],df)
df_change = pd.DataFrame()
df_change['id'] = cop_change
Save('2.迁移了国家的企业id',path_dic['save'],df_change)
#endregion

#endregion-----1.公司 国家所属

# region -----2.计算供应链数据中直接性供应关系的含中量，

# region -------获取供应链数据
base_dir = path_dic['foreign_data']
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[0]
df_sc = pd.read_stata(files[1]) #供应链df
df_sc.columns
#endregion

#获取公司属地表格
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[0]
df_cop_region = pd.read_excel(files[0],dtype={'id':str}) # 公司属地对应表
df_cop_region.columns

cop_region = dict()
all_cop = len(df_cop_region.index)
for i in df_cop_region.index:
    cop_region[df_cop_region.loc[i,'id']] = df_cop_region.loc[i,'region']
    print(f'已解决{i+1}/{all_cop}')

all_sc = len(df_sc.index)

df_sc.columns
# 删掉多余信息
df_sc.drop(columns=['subsidiaries', 'revenue_percent',       'percent_estimated', 'source_company_subsidiaries',    
       'target_company_subsidiaries', 'SOURCE_name', 'SOURCE_ticker',
       'SOURCE_cusip', 'SOURCE_isin', 'SOURCE_sedol', 'TARGET_name',
       'TARGET_ticker', 'TARGET_cusip', 'TARGET_isin', 'TARGET_sedol',
       'source_company_keyword', 'target_company_keyword', 'keyword1',
       'keyword2', 'keyword3', 'keyword4', 'keyword5', 'keyword6', 'keyword7',
       'keyword8', 'keyword9', 'keyword10'],inplace=True)
df_sc['source_contain'] = 999
df_sc['target_contain'] = 999

source_cop_set = set()  # 供应链中的source公司集合  ,此处创建空集合  ,集合中只有唯一值，将所有公司储存进去

for i in df_sc.index:
    source_cop_set.add(df_sc.loc[i,'id'])
    print(f'已解决{i+1}')


for i in df_sc.index: #是中国公司则在公司部门设为1
    source_cop_id = df_sc.loc[i,'source_company_id']
    target_cop_id = df_sc.loc[i,'target_company_id']
    if source_cop_id in cop_region.keys():
        if cop_region[source_cop_id] == 'CN':
            df_sc.loc[i,'source_contain'] = 1
    if target_cop_id in cop_region.keys():
        if cop_region[target_cop_id] == 'CN':
            df_sc.loc[i,'target_contain'] = 1
    print(f'已解决{i+1}/{all_sc}')

df_sc
cop_cn_count = {k: 0 for k in cop_region}
for i in df_sc.index:
    source_cop_id = df_sc.loc[i,'source_company_id']
    target_cop_id = df_sc.loc[i,'target_company_id']
    if source_cop_id in cop_region.keys():
        if df_sc.loc[i,'source_contain'] == 1 :
            cop_cn_count[source_cop_id] += 1
        if df_sc.loc[i,'target_contain'] == 1:
            cop_cn_count[source_cop_id] += 1
    else:
        cop_cn_count[source_cop_id] = 0

    print(f'已解决{i+1}/{all_sc}')

# endregion -----2.计算供应链数据中直接性供应关系的含中量，

# region -----3.删掉一点中国供应链含量都没有的数据
df_sc[df_sc['source_contain']==1]
cop_cn_count
c = 0
for key,value in cop_cn_count.items():
    if value > 0:
        c+=1
        print(f'含有CN的：{key}')

print(f'含量{c}/{len(cop_cn_count.items())}')


count = 0
cn_count = len(cop_cn_count)
cn_index = []
for key,value in cop_cn_count.items():
    if value > 0:
        for i in df_sc[df_sc['source_company_id']==key].index:
            cn_index.append(i)
    print(f'已完成{count}/{cn_count}')
    count+=1
df_sc_cn = df_sc.loc[cn_index]
df_sc_cn
Save('3.包含CN的供应链数据表',path_dic['save'],df_sc_cn)
# endregion -----3.删掉一点中国供应链含量都没有的数据

# region -----4.利用stata删掉部分类型的数据，保留客户——供应

# endregion -----4.利用stata删掉部分类型的数据，保留客户——供应

# region -----5.断裂指标复现
#获取删减掉完全不含中国企业的供应链数据
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
files[3]
df_sc_cn = pd.read_excel(files[3],dtype={'source_company_id':str,'target_company_id':str}) 
df_sc_cn.columns


df_sc_cn['break'] = None #供应链断裂标记

for i in df_sc_cn.index:
    if df_sc_cn.loc[i,'start_'] == df_sc_cn.loc[i,'end_']:
        df_sc_cn.loc[i,'break'] = 1
        print(f'已解决{i+1}')
        continue
    else:
        df_sc_cn.loc[i,'break'] = 0
        print(f'已解决{i+1}')

'''代码修改说明:
由于部分产业发生变化的时间较为滞后。因此，我们将原先的3月以内（包含3月不包含四月）产业链断裂  延长至6月内（包含6月不包含7月） 产业链断裂
为此添加break_4、break_5和break_6 三个变量
————修改时间为2025年。3月1日
'''
df_sc_cn['break_0'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_1'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_2'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_3'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_4'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_5'] = None #供应链当期断裂标记 ——指的是四份清单时间点
df_sc_cn['break_6'] = None #供应链当期断裂标记 ——指的是四份清单时间点

list_time = [pd.Timestamp(year=2018, month=4, day=4), #第一二份清单
pd.Timestamp(year=2018, month=7, day=10), #第三份清单
pd.Timestamp(year=2019, month=4, day=4) #第四份清单
]

for i in df_sc_cn.index:
    if df_sc_cn.loc[i,'break'] == 1 :
        for time in list_time:
            time_diff = df_sc_cn.loc[i,'start_'] - time            
            if time_diff > pd.Timedelta(0):
                time_diff_days = time_diff.days
                if time_diff_days<30:
                    df_sc_cn.loc[i,'break_0'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=30) and (time_diff_days<60):
                    df_sc_cn.loc[i,'break_1'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=60) and (time_diff_days<90):
                    df_sc_cn.loc[i,'break_2'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=90) and (time_diff_days<120):
                    df_sc_cn.loc[i,'break_3'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=120) and (time_diff_days<150):
                    df_sc_cn.loc[i,'break_4'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=150) and (time_diff_days<180):
                    df_sc_cn.loc[i,'break_5'] = 1
                    print(f'已解决{i+1}')
                    continue
                if (time_diff_days>=180) and (time_diff_days<210):
                    df_sc_cn.loc[i,'break_6'] = 1
                    print(f'已解决{i+1}')
                    continue
    else:
        print(f'已解决{i+1}')
        continue


for i in df_sc_cn.index:
    if df_sc_cn.loc[i,'break'] == 1 :
        if df_sc_cn.loc[i,'break_0'] != 1:
            df_sc_cn.loc[i,'break_0'] = 0
            print(f'已解决{i+1}')
        if df_sc_cn.loc[i,'break_1'] != 1:
            df_sc_cn.loc[i,'break_1'] = 0
            print(f'已解决{i+1}')
        if df_sc_cn.loc[i,'break_2'] != 1:
            df_sc_cn.loc[i,'break_2'] = 0
            print(f'已解决{i+1}')
        if df_sc_cn.loc[i,'break_3'] != 1:
            df_sc_cn.loc[i,'break_3'] = 0
            print(f'已解决{i+1}')
        # break_4版本
        if df_sc_cn.loc[i,'break_4'] != 1:
            df_sc_cn.loc[i,'break_4'] = 0
            print(f'已解决{i+1}')
 
        # break_5版本
        if df_sc_cn.loc[i,'break_5'] != 1:
            df_sc_cn.loc[i,'break_5'] = 0
            print(f'已解决{i+1}')
 
        #  break_6版本   
        if df_sc_cn.loc[i,'break_6'] != 1:
            df_sc_cn.loc[i,'break_6'] = 0
            print(f'已解决{i+1}')
    else:
        df_sc_cn.loc[i,'break_0'] = 0 
        df_sc_cn.loc[i,'break_1'] = 0 
        df_sc_cn.loc[i,'break_2'] = 0 
        df_sc_cn.loc[i,'break_3'] = 0
                # break_4版本
        df_sc_cn.loc[i,'break_4'] = 0

        # break_5版本
        df_sc_cn.loc[i,'break_5'] = 0

        # break_6版本
        df_sc_cn.loc[i,'break_6'] = 0
        print(f'已解决{i+1}')

#新建一个变量,其表示供应链受到关税清单冲击后是否断裂 （包含当期断裂和延后断裂，然后断裂时间范围扩展到大于6个月，小于7个月）
df_sc_cn['break_chain'] = None 
for i in df_sc_cn.index:
    if df_sc_cn.loc[i,'break'] == 1 :
        # 遍历所有break_0~6列
        trigger_flag = False
        for n in range(7):
            col = f'break_{n}'
            # 记录是否存在1
            if df_sc_cn.loc[i, col] == 1:
                trigger_flag = True
        
        # 根据标记设置break_chain
        if trigger_flag:
            df_sc_cn.loc[i, 'break_chain'] = 1
            print(f'链式标记已触发：{i+1}')
        else:
            df_sc_cn.loc[i, 'break_chain'] = 0
            print(f'链式标记已触发：{i+1}')
    else:
        df_sc_cn.loc[i, 'break_chain'] = 0
        print(f'链式标记已触发：{i+1}')


Save('5.建立断裂指标的供应链数据表',path_dic['save'],df_sc_cn)

# endregion -----5.断裂指标复现

# region -----6.添加上市公司股票代码
base_dir = path_dic['foreign_data']

# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]

# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[3]

df_cop = pd.read_stata(path) # 公司df
df_cop.columns
df_cop.index

#获取供应链数据
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[4]
df_sc_cn = pd.read_excel(path,dtype={'source_company_id':str,'target_company_id':str}) 
df_sc_cn.columns

df_cop.dtypes

df_sc_cn['source_ticker'] = None  #建立股票代码列
df_sc_cn['target_ticker'] = None

ticker_plenty_value = [] #容纳多个股票代码的特殊值
for i in df_sc_cn.index:
    source_id = df_sc_cn.loc[i,'source_company_id']
    target_id = df_sc_cn.loc[i,'target_company_id']
    source_ticker =  df_cop.index[ df_cop['id'] == source_id].tolist()
    target_ticker =  df_cop.index[ df_cop['id'] == target_id].tolist()
    if len(source_ticker) > 0 :
        ticker_set = set()
        for index in source_ticker:
            ticker_set.add(df_cop.loc[index,'ticker'])
        if len(ticker_set) > 1 :
            ticker_plenty_value.append(ticker_set)
        else:
            value = ticker_set.pop()
            df_sc_cn.loc[i,'source_ticker'] = value
        print(f'已解决{i+1}')
    if len(target_ticker) > 0 :
        ticker_set = set()
        for index in target_ticker:
            ticker_set.add(df_cop.loc[index,'ticker'])
        if len(ticker_set) > 1 :
            ticker_plenty_value.append(ticker_set)
        else:
            value = ticker_set.pop()
            df_sc_cn.loc[i,'target_ticker'] = value
        print(f'已解决{i+1}')
    print(f'已解决{i+1}')

Save('6.添加股票代码后的供应链数据表',path_dic['save'],df_sc_cn)
# endregion  -----6.添加上市公司股票代码

# region  -----7.将新建的断裂指标添加到上市公司数据中

#获取供应链数据
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[5]
df_sc_cn = pd.read_excel(path,dtype={'source_company_id':str,'target_company_id':str,
                            'source_ticker':str,'target_ticker':str}) 
df_sc_cn.columns


base_dir = path_dic['cop_data']

# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]

# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[0]

df_cop_all = pd.read_excel(path,dtype={'证券代码':str})  # 公司df
df_cop_all.columns

df_cop_all['break_0'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_1'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_2'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_3'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_4'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_5'] = None #上市公司当期断裂标记 ——指的是四份清单时间点
df_cop_all['break_6'] = None #上市公司当期断裂标记 ——指的是四份清单时间点


for i in df_sc_cn.index:
    source_ticker = df_sc_cn.loc[i,'source_ticker']
    target_ticker = df_sc_cn.loc[i,'target_ticker']
    break_0 = df_sc_cn.loc[i,'break_0']
    break_1 = df_sc_cn.loc[i,'break_1']
    break_2 = df_sc_cn.loc[i,'break_2']
    break_3 = df_sc_cn.loc[i,'break_3']
    if (break_0 == 1) or (break_1 == 1) or (break_2 == 1) or (break_3 == 1):
        if source_ticker is not np.nan :
            year = df_sc_cn.loc[i,'start_'].year
            condition = (df_cop_all['year'] == year) & (df_cop_all['证券代码'] == source_ticker)
            index_list = df_cop_all[condition].index
            if len(index_list) > 0 :
                index = index_list[0]
                df_cop_all.loc[index,'break_0'] = df_sc_cn.loc[i,'break_0']
                df_cop_all.loc[index,'break_1'] = df_sc_cn.loc[i,'break_1']
                df_cop_all.loc[index,'break_2'] = df_sc_cn.loc[i,'break_2']
                df_cop_all.loc[index,'break_3'] = df_sc_cn.loc[i,'break_3']
        if target_ticker is not np.nan :
            condition = (df_cop_all['year'] == year) & (df_cop_all['证券代码'] == target_ticker)
            index_list = df_cop_all[condition].index
            if len(index_list) > 0 :
                index = index_list[0]
                df_cop_all.loc[index,'break_0'] = df_sc_cn.loc[i,'break_0']
                df_cop_all.loc[index,'break_1'] = df_sc_cn.loc[i,'break_1']
                df_cop_all.loc[index,'break_2'] = df_sc_cn.loc[i,'break_2']
                df_cop_all.loc[index,'break_3'] = df_sc_cn.loc[i,'break_3']
        print(f'已解决{i+1}')
    else:
        print(f'已解决{i+1}')

Save('7.添加断裂指标后的上市公司数据',path_dic['save'],df_cop_all)
#endregion  -----7.将新建的断裂指标添加到上市公司数据中

# region  -----7.1 将新建的断裂指标添加到上市公司数据中_ 新计算方法(关联产业链破裂也算作break计入上市公司)
'''新计算方法说明:
    考虑到上市公司的安全性资金较为充裕，因此在贸易战期间其产业链不太可能会发生断裂。
    因此我们采用一种新的方法来计算成上市公司的产业链断裂。
    我们将非上市公司与上市公司的关联产业链纳入计算，如果关联产业链发生断裂，那么即意味着上市公司受到了贸易战冲击导致的间接产业链断裂效应
'''
'''以下代码处理逻辑：
根据文段内容，可将其分析拆解为以下4个步骤：


'''


#获取供应链数据
base_dir = path_dic['middle']
# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]
files
# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[5]
df_sc_cn = pd.read_excel(path,dtype={'source_company_id':str,'target_company_id':str,
                            'source_ticker':str,'target_ticker':str}) 
df_sc_cn.columns


base_dir = path_dic['cop_data']

# 获取当前目录下的所有文件
files = [os.path.join(base_dir, file) for file in os.listdir(base_dir)]

# 遍历文件列表，输出文件名
for index,file in enumerate(files):
    print(f'索引 {index}： {file}')
path = files[0]

df_cop_all = pd.read_excel(path,dtype={'证券代码':str,'股票代码':str})  # 公司df
df_cop_all.columns


df_cop_all['break_chain'] = None #上市公司当期断裂标记 ——指的是四份清单时间点

for i in df_sc_cn.index:
    source_ticker = df_sc_cn.loc[i,'source_ticker']
    target_ticker = df_sc_cn.loc[i,'target_ticker']
    break_chain = df_sc_cn.loc[i,'break_chain']
    
    if break_chain == 1:
        if source_ticker is not np.nan :
            year = df_sc_cn.loc[i,'start_'].year
            condition = (df_cop_all['year'] == year) & (df_cop_all['股票代码'] == source_ticker)
            index_list = df_cop_all[condition].index
            if len(index_list) > 0 :
                index = index_list[0]
                df_cop_all.loc[index,'break_chain'] = 1

        if target_ticker is not np.nan :
            condition = (df_cop_all['year'] == year) & (df_cop_all['股票代码'] == target_ticker)
            index_list = df_cop_all[condition].index
            if len(index_list) > 0 :
                index = index_list[0]
                df_cop_all.loc[index,'break_chain'] = 1
        print(f'已解决{i+1}')
    else:
        print(f'已解决{i+1}')

Save('7.添加断裂指标后的上市公司数据',path_dic['save'],df_cop_all)



import pandas as pd
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

#######################################################################
# 企业实体类
# 功能：存储企业基本信息，作为产业链网络中的节点基础数据
#######################################################################
class Company:
    def __init__(self, cid: str, country: str, listed: bool):
        """
        初始化企业对象
        
        参数说明：
        cid     - 企业唯一标识符（如"CN_001"）
                 - 建议格式：国家代码_序列号（需保证全局唯一性）
        country - 企业注册地（如"China"/"USA"）
                 - 用于后续跨境产业链分析
        listed  - 上市状态标识（True表示上市公司）
                 - 用于关联资本市场分析
        """
        self.id = cid       # 企业ID（必须保证唯一性）
        self.country = country  # 所属国家（基于ISO标准为佳）
        self.listed = listed     # 是否上市（布尔值）

