import fitz  # PyMuPDF

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
pdf_to_image(r"C:\Users\Mocilly\Desktop\127.0.0.1 (1).pdf", r"C:\Users\Mocilly\Desktop\output.png", zoom=6)