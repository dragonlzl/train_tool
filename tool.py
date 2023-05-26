import os
import yaml
from PIL import Image


def create_yaml_file(output_file, names, path='', train='', val='', test=''):
    data = {
        'path': path,
        'train': train,
        'val': val,
        'test': test,
        'names': names
    }


    with open(output_file, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


# 因为是动态获取截图的，不经过保存，所以不能直接用指定路径的方式
def get_image_size(image_path):
    # 打开图像
    img = Image.open(image_path)

    # 获取图像尺寸（宽度和高度）
    width, height = img.size

    return width, height


def rectangle_info(point1, point2, image_path='', class_id=0):

    x1, y1 = point1
    x2, y2 = point2

    # 计算另外两个点的坐标
    point3 = (x1, y2)
    point4 = (x2, y1)

    # 确定左上、右上、左下、右下的坐标
    left_top = (min(x1, x2), min(y1, y2))
    right_top = (max(x1, x2), min(y1, y2))
    left_bottom = (min(x1, x2), max(y1, y2))
    right_bottom = (max(x1, x2), max(y1, y2))

    # 计算中心点坐标
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    center_point = (center_x, center_y)

    # 计算矩形长和宽
    # if screen_orientation == 'landscape':
    rect_length = abs(y2 - y1)
    rect_width = abs(x2 - x1)
    # elif screen_orientation == 'portrait':
    # rect_length = abs(x2 - x1)
    # rect_width = abs(y2 - y1)

    # 将结果存储在字典中
    rect_info = {
        'image_path': image_path,
        'class_id': class_id,
        'left_top': left_top,
        'right_top': right_top,
        'left_bottom': left_bottom,
        'right_bottom': right_bottom,
        'center_point': center_point,
        'length': rect_length,
        'width': rect_width
    }
    print(f'写入归一化前的数据：{rect_info}')
    return rect_info


# 归一化并转为str，方便直接写入txt
def normalization(rect_info, img_width, img_height, image_path=None):
    if image_path is not None:
        img_width, img_height = get_image_size(image_path)
    class_id = rect_info['class_id']
    x_center, y_center = rect_info['center_point']
    width, height = rect_info['width'], rect_info['length']

    # 归一化坐标
    x_center /= img_width
    y_center /= img_height
    width /= img_width
    height /= img_height

    # 创建YOLOv5标注格式字符串
    annotation_str = f"{class_id} {x_center} {y_center} {width} {height}\n"
    print(f"归一化时的 img_width:{img_width},img_height:{img_height}")
    return annotation_str


# 读取归一化后的txt文件
# 转为左上角坐标和右下角坐标
# 用于重新画框
def read_txt(txt_path, img_width, img_height):
    rect_info_list = []
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            class_id, x_center, y_center, width, height = line.split(' ')
            x_center = float(x_center)
            y_center = float(y_center)
            width = float(width)
            height = float(height)

            # 从归一化坐标转为原始坐标
            x_center *= img_width
            y_center *= img_height
            width *= img_width
            height *= img_height

            # 计算左上角和右下角坐标
            left_top = (x_center - width / 2, y_center - height / 2)
            right_bottom = (x_center + width / 2, y_center + height / 2)

            # 将结果存储在字典中
            rect_info = {
                'class_id': class_id,
                'left_top': left_top,
                'right_bottom': right_bottom,
                'center_point': (x_center, y_center),
                'length': height,
                'width': width,
                'img_width': img_width,
                'img_height': img_height
            }
            rect_info_list.append(rect_info)
            print(f"读取txt数据：{rect_info_list}")
        return rect_info_list


# 读取归一化后的txt文件，返回归一化的txt str列表
def read_txt_to_str_list(txt_path):
    annotation_str_list = []
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            annotation_str_list.append(line)
    return annotation_str_list


def save_to_txt(annotation_str_list, image_path):
    if annotation_str_list:
        img_formats = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'tiff', 'jfif', 'svg', 'ico']
        if image_path.split('.')[-1] in img_formats:
            dirname = os.path.dirname(image_path)
            filename = os.path.basename(image_path)

            output_file = os.path.join(dirname, f"{filename.split('.')[0]}.txt")
            # 将字符串写入输出文件
            with open(output_file, "w") as f:
                for annotation_str in annotation_str_list:
                    f.writelines(annotation_str)
            return True
        else:
            print(f"{image_path.split('.')[-1]}格式不是标准图片格式")
            return False
    else:
        print(f"{annotation_str_list}不是list，而是{type(annotation_str_list)}")
        return False


def save_yolov5_annotation(rect_info, img_width, img_height, output_file):
    class_id = rect_info['class_id']
    x_center, y_center = rect_info['center_point']
    width, height = rect_info['width'], rect_info['length']

    # 归一化坐标
    x_center /= img_width
    y_center /= img_height
    width /= img_width
    height /= img_height

    # 创建YOLOv5标注格式字符串
    yolo_annotation = f"{class_id} {x_center} {y_center} {width} {height}\n"

    # 将字符串写入输出文件
    with open(output_file, "w") as f:
        f.write(yolo_annotation)


# 根据value找key
def find_keys_by_value(d, value):
    for key, val in d.items():
        if val == value:
            return key
    else:
        return None


# 通过完整全部步骤，传入步数，返回是第几个框
def qrects_to_step_num(tag_list, index):
    temp_dict = {}
    temp_list = []
    count = 0
    for i, item in enumerate(tag_list):
        if item == 'one_pos':
            temp_list.append(i)
            if len(temp_list) == 2:
                temp_dict[count] = temp_list
                temp_list = []
                count += 1
        else:
            temp_list.append(i)
            temp_dict[count] = temp_list
            temp_list = []
            count += 1
    keys = list(temp_dict.keys())
    if index <= len(keys):
        return temp_dict[index]


if __name__ == "__main__":
    # # 示例：已知两个对角点坐标和图像尺寸
    # point1 = (2, 3)
    # point2 = (6, 7)
    # image_path = "/Users/linzhenlong/PycharmProjects/train_tool/2023_03_25_15_24_06.png"
    # to_txt(point1, point2, image_path)

    # 测试 read_txt函数
    txt_path = "/Users/linzhenlong/PycharmProjects/train_tool/testpng/2023_03_29_21_46_08.txt"
    annotation_list = read_txt_to_str_list(txt_path)
    print(annotation_list)

    img_width, img_height = get_image_size("/Users/linzhenlong/PycharmProjects/train_tool/testpng/2023_03_29_21_46_08.png")
    rect_info = read_txt(txt_path, img_width, img_height)
    print(rect_info)
