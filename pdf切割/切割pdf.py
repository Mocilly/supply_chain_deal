import os
# 使用PyPDF2实现
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_path, output_path, page_range):
    reader = PdfReader(input_path)
    

    
    # 后续代码保持不变...
# 调用示例（提取第3-5页）
split_pdf("input.pdf", "output.pdf", range(3,6))

import fitz  # PyMuPDF的导入名称

def split_pdf(input_path, output_path, page_range):
    doc = fitz.open(input_path)
    
    # 处理加密（若有）
    if doc.is_encrypted:
        if not doc.authenticate(""):  # 尝试空密码
            raise Exception("需要密码才能打开PDF")
    
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_range[0]-1, to_page=page_range[-1]-1)
    new_doc.save(output_path)
    new_doc.close()

	# 使用原始字符串+os.path处理路径（推荐）
base_path = r"C:\Users\32915\Desktop"  # 此处必须是有效的实际路径
input_file = "论《共产党宣言》中人的解放思想_王召群 (1).pdf"
output_file = "切割.pdf"
 
split_pdf(
    input_path=os.path.join(base_path, input_file),
    output_path=os.path.join(base_path,output_file),
    page_range=range(51,55)  # 输出原文件第48-55页（PyPDF2索引从0开始）
)
