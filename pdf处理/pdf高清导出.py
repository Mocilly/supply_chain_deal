import fitz  # PyMuPDF
from pathlib import Path
import os
def get_all_files(folder_path):
    """
    获取指定文件夹及其子文件夹中的所有文件路径
    
    参数：
        folder_path (str): 目标文件夹路径
        
    返回：
        list: 包含所有文件完整路径的列表，格式为：
              [
                  "完整路径/文件1.txt",
                  "完整路径/子文件夹/文件2.jpg",
                  ...
              ]
    """
    file_list = []
    
    # 遍历文件夹（包含所有子文件夹）
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 拼接完整路径
            full_path = os.path.join(root, file)
            # 添加到结果列表
            file_list.append(os.path.abspath(full_path))
    
    return [(full_path[full_path.rfind('\\')+1:full_path.rfind('.')], os.path.abspath(full_path)) for full_path in file_list]



def pdf_to_image(pdf_path, output_path, zoom=6):
    """
    将单页PDF转换为高清图片
    :param pdf_path: 输入的PDF文件路径
    :param output_path: 输出的图片路径（支持.png/.jpg等）
    :param zoom: 缩放因子（越大越清晰，默认3对应约300DPI）
    """
    doc = fitz.open(pdf_path)
    page = doc[0]  # 获取第一页
    
    # 创建缩放矩阵
    mat = fitz.Matrix(zoom, zoom)
    
    # 渲染页面为图像
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    # 保存图像
    pix.save(output_path)
    print(f"图片已保存至：{output_path}")

# 使用示例

source_folder = r"C:\Users\Mocilly\Desktop\外资在华企业供应链\裁剪PDF"
output_folder = r'C:\Users\Mocilly\Desktop\外资在华企业供应链\高清PNG'
source_files = get_all_files(source_folder)
source_files
for file_name, file_path in source_files:
    # 获取文件名（不带扩展名）
    output_path = os.path.join(output_folder, file_name + '.png')
    # 创建图片文件
    pdf_to_image(file_path, output_path, zoom=10)

# pdf_to_image(r"C:\Users\Mocilly\Desktop\127.0.0.1 (1).pdf", r"C:\Users\Mocilly\Desktop\output.png", zoom=6)