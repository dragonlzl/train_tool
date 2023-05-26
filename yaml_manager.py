import os

import yaml


def yaml_read(file_path):
    # 读取 YAML 文件
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def yaml_write(file_path, config):
    # 写入 YAML 文件
    with open(file_path, 'w') as f:
        yaml.dump(config, f)


if __name__ == '__main__':
    yaml_path = '/Users/linzhenlong/AI/yolov5/data/coco128.yaml'
    config = yaml_read(yaml_path)
    print(config)