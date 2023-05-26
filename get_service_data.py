import io

import requests
import json

from config import server_url, request_api, timeout, port


def get_service_data():
  url = f"http://{server_url}:{port}/{request_api}"

  headers = {
    'Content-Type': 'application/json'
  }

  response = requests.get(url, headers=headers, timeout=timeout)
  data = json.loads(response.text)
  return data


def class_data():
    data = get_service_data()
    return data


def download_image(class_id):

    # image_url = f"http://{server_url}:{port}/images/{class_id}"
    image_url = f"http://{server_url}:{port}/api/labelimg/get_img/{class_id}"
    # image_name = '2023_04_20_10_09_18.png'
    params = {
        "class_id": class_id
    }

    data = get_service_data()
    data = data['data']

    for item in data.keys():
        for i in range(len(data[item])):
            if data[item][i]["class_id"] == class_id:
                img_list = data[item][i]["label_img_path"]
                for img_p in img_list:
                    img_p = img_p.split("/")[-1]

    response = requests.get(image_url, params=params)
    image_list = response.json()
    # image_urls = [f'{image_url}/{image_name}' for image_name in image_list]
    image_urls = [f'{image_url}/{img_p}']
    return image_urls


if __name__ == '__main__':
    data = get_service_data()
    print(data)
    image_data = download_image("战斗")
    print(image_data)

