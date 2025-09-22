import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


def get_exif_datetime(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None

        # 找到 DateTimeOriginal
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                # 格式一般是 "2023:07:15 12:34:56"
                try:
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return None
        return None
    except Exception as e:
        print(f"⚠️ 无法读取 {image_path}: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python watermark_step1.py <图片目录>")
        sys.exit(1)

    input_dir = sys.argv[1]

    if not os.path.isdir(input_dir):
        print("❌ 输入路径不是有效目录")
        sys.exit(1)

    # 遍历目录
    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        dt = get_exif_datetime(filepath)
        if dt:
            print(f"{filename} -> {dt}")
        else:
            print(f"{filename} -> 无日期信息")


if __name__ == "__main__":
    main()
