import numpy as np
from PyQt6.QtGui import QImage, qRgb
import os
pattern_list = ["GRBG", "GBRG", "RGGB", "BGGR"]
import re


def parse_image_info(filename, image_types=None, bayer_patterns=None):
    """
    从文件名中解析图像信息，包括宽高、图片类型和拜耳模式。

    参数:
        filename (str): 待解析的文件名
        image_types (list): 支持的图片类型列表，默认为常见类型
        bayer_patterns (list): 支持的拜耳模式列表，默认为常见模式

    返回:
        dict: 包含宽、高、图片类型、拜耳模式的字典
    """
    # 默认支持的图片类型
    if image_types is None:
        image_types = ['unpack10', 'raw8','unpack12']

    # 默认支持的拜耳模式
    if bayer_patterns is None:
        bayer_patterns = ['grbg', 'rggb', 'bggr', 'gbrg']

    result = {
        'width': None,
        'height': None,
        'image_type': None,
        'bayer_pattern': None
    }

    # 1. 提取宽高（支持 数字X数字 格式）
    resolution_match = re.search(r'(\d+)X(\d+)', filename, re.IGNORECASE)
    if resolution_match:
        result['width'] = int(resolution_match.group(1))
        result['height'] = int(resolution_match.group(2))

    # 2. 提取图片类型
    for img_type in image_types:
        if img_type.lower() in filename.lower():
            result['image_type'] = img_type
            break

    # 3. 提取拜耳模式
    for pattern in bayer_patterns:
        if pattern.lower() in filename.lower():
            result['bayer_pattern'] = pattern
            break

    return result



def get_raw8(raw_data, raw_type):
    diff_bit = 2
    if raw_type == 'unpack10':
        diff_bit = 2
    elif raw_type == 'unpack12':
        diff_bit = 4
    if raw_type != 'raw8':
        data_array = np.frombuffer(raw_data, dtype=np.uint16)
        raw8_values = data_array >> diff_bit
        return raw8_values.astype(np.uint8)
    else:
        return raw_data

def raw8_to_unpack16bit(raw8_data, raw_type):
    if raw_type == 'unpack10':
        diff_bit = 2
    elif raw_type == 'unpack12':
        diff_bit = 4
    else:
        return None
    data_array = np.frombuffer(raw8_data, dtype=np.uint8)
    raw10_values = (data_array.astype(np.uint16)) << diff_bit
    return raw10_values.astype(np.uint16)

"""
    获取raw图
"""
def read_raw(raw_path):
    file_name = os.path.basename(raw_path)
    if not os.path.splitext(file_name)[1] == ".raw":
        return None
    # 解析文件名 _000_1207D416A588_FailRaw_20260122T133327.4096X3072.unpack10_grbg.vcmpos_289.raw
    img_info = parse_image_info(file_name)
    if not img_info['image_type'] or not img_info['bayer_pattern']:
        return None
    with open(raw_path, 'rb') as f:
        raw_data = f.read()
    raw_data = get_raw8(raw_data, img_info.get('image_type', "unpack10"))
    return {
        "origin_type" : img_info.get('image_type', "raw8"),
        "origin_name" : file_name,
        "raw_data" : raw_data,
        "raw_width" : img_info['width'],
        "raw_height" : img_info['height'],
        "pattern" : img_info['bayer_pattern'].upper(),
    }


def raw_to_numpy_array(raw_data, raw_width, raw_height, pattern):
    # 将 raw_data 转换为 numpy 数组
    raw_array = np.frombuffer(raw_data, dtype=np.uint8).reshape(raw_height, raw_width)

    # 创建 RGB 数组
    rgb_array = np.zeros((raw_height, raw_width, 3), dtype=np.uint8)

    if pattern == "GRBG":
        # 偶数行偶数列: G
        rgb_array[0::2, 0::2, 1] = raw_array[0::2, 0::2]  # G通道
        # 奇数行奇数列: G
        rgb_array[1::2, 1::2, 1] = raw_array[1::2, 1::2]  # G通道
        # 偶数行奇数列: R
        rgb_array[0::2, 1::2, 0] = raw_array[0::2, 1::2]  # R通道
        # 奇数行偶数列: B
        rgb_array[1::2, 0::2, 2] = raw_array[1::2, 0::2]  # B通道
    elif pattern == "GBRG":
        # 偶数行偶数列: G
        rgb_array[0::2, 0::2, 1] = raw_array[0::2, 0::2]
        # 奇数行奇数列: G
        rgb_array[1::2, 1::2, 1] = raw_array[1::2, 1::2]
        # 奇数行偶数列: R
        rgb_array[1::2, 0::2, 0] = raw_array[1::2, 0::2]
        # 偶数行奇数列: B
        rgb_array[0::2, 1::2, 2] = raw_array[0::2, 1::2]
    elif pattern == "RGGB":
        # 偶数行偶数列: R
        rgb_array[0::2, 0::2, 0] = raw_array[0::2, 0::2]
        # 奇数行奇数列: B
        rgb_array[1::2, 1::2, 2] = raw_array[1::2, 1::2]
        # 其他位置: G
        rgb_array[0::2, 1::2, 1] = raw_array[0::2, 1::2]
        rgb_array[1::2, 0::2, 1] = raw_array[1::2, 0::2]
    elif pattern == "BGGR":
        # 偶数行偶数列: B
        rgb_array[0::2, 0::2, 2] = raw_array[0::2, 0::2]
        # 奇数行奇数列: R
        rgb_array[1::2, 1::2, 0] = raw_array[1::2, 1::2]
        # 其他位置: G
        rgb_array[0::2, 1::2, 1] = raw_array[0::2, 1::2]
        rgb_array[1::2, 0::2, 1] = raw_array[1::2, 0::2]
    else:
        return None
    return rgb_array
def raw_to_rgb_bayer(raw_data, raw_width, raw_height, pattern):
    # 将 raw_data 转换为 numpy 数组
    rgb_array = raw_to_numpy_array(raw_data, raw_width, raw_height, pattern)

    # 将 numpy 数组转换为 QImage
    q_img = QImage(rgb_array.data, raw_width, raw_height, 3 * raw_width, QImage.Format.Format_RGB888)
    # 必须保留对数组的引用，否则数据会被垃圾回收
    q_img.rgb_array = rgb_array
    return q_img

def raw_to_QImage(raw_data, raw_width, raw_height, pattern, mode="GRAY"):
    if mode == "GRAY":
        return QImage(raw_data, raw_width, raw_height, QImage.Format.Format_Grayscale8)

    if mode != "RGB":
        return None

    return raw_to_rgb_bayer(raw_data, raw_width, raw_height, pattern)

def qimage_to_rgb_numpy_array(q_img, pattern):
    # 获取 QImage 的尺寸
    width = q_img.width()
    height = q_img.height()

    # 将 QImage 转换为 numpy 数组
    q_img = q_img.convertToFormat(QImage.Format.Format_RGB888)
    ptr = q_img.bits()
    ptr.setsize(height * width * 3)
    rgb_array = np.frombuffer(ptr, dtype=np.uint8).reshape(height, width, 3)

    # 创建空的 raw 数组
    raw_array = np.zeros((height, width), dtype=np.uint8)

    # 根据 Bayer 模式从 RGB 中提取原始像素
    if pattern == "GRBG":
        # 偶数行偶数列: 取 G 通道
        raw_array[0::2, 0::2] = rgb_array[0::2, 0::2, 1]
        # 奇数行奇数列: 取 G 通道
        raw_array[1::2, 1::2] = rgb_array[1::2, 1::2, 1]
        # 偶数行奇数列: 取 R 通道
        raw_array[0::2, 1::2] = rgb_array[0::2, 1::2, 0]
        # 奇数行偶数列: 取 B 通道
        raw_array[1::2, 0::2] = rgb_array[1::2, 0::2, 2]

    elif pattern == "GBRG":
        # 偶数行偶数列: 取 G 通道
        raw_array[0::2, 0::2] = rgb_array[0::2, 0::2, 1]
        # 奇数行奇数列: 取 G 通道
        raw_array[1::2, 1::2] = rgb_array[1::2, 1::2, 1]
        # 奇数行偶数列: 取 R 通道
        raw_array[1::2, 0::2] = rgb_array[1::2, 0::2, 0]
        # 偶数行奇数列: 取 B 通道
        raw_array[0::2, 1::2] = rgb_array[0::2, 1::2, 2]

    elif pattern == "RGGB":
        # 偶数行偶数列: 取 R 通道
        raw_array[0::2, 0::2] = rgb_array[0::2, 0::2, 0]
        # 奇数行奇数列: 取 B 通道
        raw_array[1::2, 1::2] = rgb_array[1::2, 1::2, 2]
        # 偶数行奇数列: 取 G 通道
        raw_array[0::2, 1::2] = rgb_array[0::2, 1::2, 1]
        # 奇数行偶数列: 取 G 通道
        raw_array[1::2, 0::2] = rgb_array[1::2, 0::2, 1]

    elif pattern == "BGGR":
        # 偶数行偶数列: 取 B 通道
        raw_array[0::2, 0::2] = rgb_array[0::2, 0::2, 2]
        # 奇数行奇数列: 取 R 通道
        raw_array[1::2, 1::2] = rgb_array[1::2, 1::2, 0]
        # 偶数行奇数列: 取 G 通道
        raw_array[0::2, 1::2] = rgb_array[0::2, 1::2, 1]
        # 奇数行偶数列: 取 G 通道
        raw_array[1::2, 0::2] = rgb_array[1::2, 0::2, 1]

    else:
        return None

    return raw_array

def qimage_to_raw_rgb(q_img, pattern):
    """将 QImage 转换回原始 raw 数据"""
    raw_array= qimage_to_rgb_numpy_array(q_img, pattern)

    # 将 numpy 数组转换为原始 bytes 数据
    raw_data = raw_array.tobytes()

    return raw_data


def qimage_to_raw_gray(q_img):
    """将 QImage 转换回灰度 raw 数据"""
    # 获取 QImage 的尺寸
    width = q_img.width()
    height = q_img.height()

    # 将 QImage 转换为 numpy 数组
    q_img = q_img.convertToFormat(QImage.Format.Format_Grayscale8)
    ptr = q_img.bits()
    ptr.setsize(height * width)
    gray_array = np.frombuffer(ptr, dtype=np.uint8).reshape(height, width)

    # 将 numpy 数组转换为原始 bytes 数据
    raw_data = gray_array.tobytes()

    return raw_data