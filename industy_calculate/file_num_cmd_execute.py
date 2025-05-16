import os
import re
import pyperclip
# ================== 用户需修改部分 ==================
folder_path = ".\调用文件\用于行业分类分析的可视化表\中间文件"  # 替换为实际文件夹路径
# ==================================================

# 初始化十个十万区间的最大结束数字（0-9对应0-999999）
max_ends = {n: -1 for n in range(10)}

# 遍历文件夹中的文件
for filename in os.listdir(folder_path):
    # 匹配文件名格式：industry_identify_起始-结束.json
    match = re.fullmatch(r'industry_identify_(\d+)-(\d+)\.json', filename)
    if not match:
        continue  # 跳过不匹配的文件
    
    try:
        start = int(match.group(1))
        end = int(match.group(2))
    except ValueError:
        continue  # 跳过数字格式错误的文件
    
    # 计算结束数字所属的十万区间（n=0~9对应0-999999）
    n = end // 100000
    if 0 <= n < 10 and end > max_ends[n]:
        max_ends[n] = end  # 更新当前区间的最大结束数字

# 生成统计结果列表
result = []
for n in range(10):
    range_start = n * 100000
    range_end = (n + 1) * 100000 - 1
    current_max = max_ends[n]
    next_num = current_max + 1 if current_max != -1 else range_start  # 无文件时从区间起点开始
    
    result.append({
        "十万区间": f"{range_start}-{range_end}",
        "最高结束数字": current_max if current_max != -1 else "无文件",
        "最高数字+1": next_num
    })







# 输出统计结果
print("===== 每个十万区间统计结果 =====")
for item in result:
    print(f"{item['十万区间']} | 最高结束数字: {item['最高结束数字']} | 最高数字+1: {item['最高数字+1']}")

def modify_py_file_with_next_num(target_py_number, result):
    """
    修改指定py文件的末尾参数为对应区间的「最高数字+1」。
    target_py_number: 目标py文件序号（1-10）
    result: 区间统计结果列表
    """
    target_n = target_py_number - 1
    if target_n < 0 or target_n >= 10:
        print(f"\n错误：目标py文件序号{target_py_number}超出1-10范围")
        return

    target_next_num = result[target_n]['最高数字+1']
    py_file_path = (
        fr".\industy_calculate\execute_py_files\industry_belong_identify_first_time_{target_py_number}.py"
    )

    try:
        with open(py_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()


        if lines:
            lines[-1] = f"process_lines_with_skip({target_next_num})\n"

        with open(py_file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"\n成功修改文件：{py_file_path}")
        print(f"修改后末尾语句：process_lines_with_skip({target_next_num})")

    except FileNotFoundError:
        print(f"\n错误：未找到目标文件 {py_file_path}")
    except Exception as e:
        print(f"\n修改文件时发生错误：{str(e)}")

def generate_cmd_and_modify(result,py_number):
    """
    修改指定py文件末尾参数，并生成CMD执行命令。
    :param py_number: 目标py文件序号（1-10）
    :param result: 区间统计结果列表
    """
    # 步骤1：修改py文件参数
    modify_py_file_with_next_num(py_number, result)
    
    # 步骤2：生成CMD命令
    cmd = (
        f"& C:/Users/Mocilly/AppData/Local/Programs/Python/Python310/python.exe "
        f"c:/Users/Mocilly/Desktop/Githook/supply_chain_deal-3/industy_calculate/execute_py_files/industry_belong_identify_first_time_{py_number}.py"
    )
    
    # 步骤3：输出并复制到剪贴板
    print("\n===== 生成的CMD执行命令 =====")
    print(cmd)
    
    if pyperclip:
        pyperclip.copy(cmd)  # 自动复制命令到剪贴板
        print(f"提示：命令已自动复制到剪贴板，可直接在CMD中粘贴执行！")
    else:
        print("提示：未安装pyperclip库，无法自动复制。请手动复制上方命令。\n"
              "安装命令：pip install pyperclip")


generate_cmd_and_modify(result,1)
generate_cmd_and_modify(result,2)
generate_cmd_and_modify(result,3)
generate_cmd_and_modify(result,4)
generate_cmd_and_modify(result,5)
generate_cmd_and_modify(result,6)
generate_cmd_and_modify(result,7)
generate_cmd_and_modify(result,8)
generate_cmd_and_modify(result,9)
generate_cmd_and_modify(result,10)

