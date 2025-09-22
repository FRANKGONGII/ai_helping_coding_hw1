import os
import sys
from PIL import Image, ImageDraw, ImageFont, ExifTags
from datetime import datetime


def get_exif_datetime(image_path):
    """读取EXIF中的拍摄日期（年月日）"""
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None

        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                try:
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return None
        return None
    except Exception:
        return None


def add_watermark(image_path, output_path, text, font_size, color, position):
    """在图片上添加水印并保存"""
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    try:
        # 默认字体，如果找不到字体可以换成系统的路径，比如 "C:/Windows/Fonts/arial.ttf"
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # 回退到内置字体
        font = ImageFont.load_default()

    text_width, text_height = draw.textsize(text, font=font)
    width, height = image.size

    # 计算位置
    if position == "left-top":
        pos = (10, 10)
    elif position == "left-bottom":
        pos = (10, height - text_height - 10)
    elif position == "right-top":
        pos = (width - text_width - 10, 10)
    elif position == "right-bottom":
        pos = (width - text_width - 10, height - text_height - 10)
    elif position == "center":
        pos = ((width - text_width) // 2, (height - text_height) // 2)
    else:
        pos = (10, 10)  # 默认左上角

    draw.text(pos, text, font=font, fill=color)
    image.save(output_path, "JPEG")


def main():
    if len(sys.argv) < 5:
        print("用法: python watermark_step2.py <图片目录> <字体大小> <颜色> <位置>")
        print("位置选项: left-top, left-bottom, right-top, right-bottom, center")
        print("颜色格式: '#RRGGBB' 或 'red'")
        sys.exit(1)

    input_dir = sys.argv[1]
    font_size = int(sys.argv[2])
    color = sys.argv[3]
    position = sys.argv[4]

    if not os.path.isdir(input_dir):
        print("❌ 输入路径不是有效目录")
        sys.exit(1)

    output_dir = input_dir.rstrip("/\\") + "_watermark"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        dt = get_exif_datetime(filepath)
        if not dt:
            print(f"{filename} -> 无日期信息，跳过")
            continue

        output_path = os.path.join(output_dir, filename)
        add_watermark(filepath, output_path, dt, font_size, color, position)
        print(f"✅ {filename} 已保存到 {output_path}")


if __name__ == "__main__":
    main()
