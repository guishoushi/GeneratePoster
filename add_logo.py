from PIL import Image
from io import BytesIO
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QBuffer, QIODevice
import resources
import cv2
import numpy as np


def add_logo_to_poster(pixmap, name, position=(0, 0), logo_size=None):
    # 1. 将 QPixmap 转换为 QImage
    qimage = pixmap.toImage()

    # 2. 使用 QBuffer 作为内存缓冲区
    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)  # 以读写模式打开缓冲区
    qimage.save(buffer, "PNG")  # 将图像保存到 Qt 的缓冲区

    # 3. 转换为 Python 字节对象
    byte_data = buffer.data()  # 获取缓冲区内容作为 QByteArray
    buffer.close()

    # 4. 创建 Python 字节流
    python_buffer = BytesIO(byte_data)
    python_buffer.seek(0)  # 重置指针位置

    # 5. 用 PIL 加载字节流
    poster = Image.open(python_buffer)
    if name == 1:
        # 从Qt资源加载logo
        return poster
    elif name == 2:
        # 从Qt资源加载logo
        pixmap = QPixmap(":/white_logo.png")
    elif name == 3:
        pixmap = QPixmap(":/black_logo.png")

    if pixmap.isNull():
        raise ValueError("无法加载logo资源，请检查.qrc文件和资源路径")

    # 正确转换QPixmap到PIL.Image（使用QBuffer）
    qimage = pixmap.toImage()
    qt_buffer = QBuffer()
    qt_buffer.open(QIODevice.ReadWrite)  # 必须显式打开
    if not qimage.save(qt_buffer, "PNG"):  # 必须明确指定格式
        raise ValueError("logo图片格式转换失败")

    # 转换为PIL.Image
    qt_buffer.seek(0)
    logo = Image.open(BytesIO(qt_buffer.data().data()))  # 注意双重.data()

    # 调整logo大小（如果指定）
    if logo_size:
        new_size = (int(logo.width * logo_size),
                    int(logo.height * logo_size))
        logo = logo.resize(new_size, Image.LANCZOS)

    # 确保logo有alpha通道
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')

    # 粘贴logo到指定位置（处理透明部分）
    # 注意：这里使用传入的position参数，而不是覆盖它
    # poster_width, poster_height = poster.size
    # position = (poster_width - logo.width - 20, poster_height - logo.height - 20)
    poster.paste(logo, position, logo)

    # 保存结果
    # poster.save(output_path, quality=95)
    # return f"图片已保存至: {output_path}"

    return poster


# # 示例用法
# add_logo_to_poster(
#     poster_content="poster.jpg",
#     output_path="output_poster.jpg",
#     position=(591, 131),  # 距离左上角(100, 100)像素
#     logo_size=0.7  # 调整logo宽度为200px
# )


def remove_watermark(img):
    img = np.array(Image.open(BytesIO(img)))
    mask = np.zeros(img.shape[:2], dtype=np.uint8)  # 创建掩模

    # 手动/自动标记水印区域（示例：矩形区域）
    x, y, w, h = 24, 24, 90, 40  # 水印位置和大小
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    # 使用Telea算法修复
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

    # 保存结果
    # cv2.imwrite("output.jpg", result)
    return result
