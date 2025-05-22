from PIL import Image
from io import BytesIO
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QBuffer, QIODevice
import io
import resources


def add_logo_to_poster(poster_content, output_path, name, position=(0, 0), logo_size=None):
    # 打开海报图片
    poster = Image.open(BytesIO(poster_content))
    if name == "黑色logo":
        # 从Qt资源加载logo
        pixmap = QPixmap(":/black_logo.png")
    elif name == "白色logo":
        pixmap = QPixmap(":/white_logo.png")

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
    poster.save(output_path, quality=95)
    return f"图片已保存至: {output_path}"

# # 示例用法
# add_logo_to_poster(
#     poster_content="poster.jpg",
#     output_path="output_poster.jpg",
#     position=(591, 131),  # 距离左上角(100, 100)像素
#     logo_size=0.7  # 调整logo宽度为200px
# )
