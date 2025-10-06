import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

class SimpleWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印工具 - 阶段1")
        self.images = []  # 存储图片路径
        self.thumbs = []  # 存储缩略图

        # 左侧列表
        self.listbox = tk.Listbox(root, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

        # 右侧预览
        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.preview_label = tk.Label(right_frame, text="预览区域", bg="gray")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # 按钮
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="导入图片", command=self.add_images).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="导入文件夹", command=self.add_folder).pack(side=tk.LEFT)

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        self.add_image_list(files)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS]
            self.add_image_list(files)

    def add_image_list(self, files):
        for f in files:
            if f not in self.images:
                self.images.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))
                # 创建缩略图
                img = Image.open(f)
                img.thumbnail((100, 100))
                self.thumbs.append(ImageTk.PhotoImage(img))

    def show_preview(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        img_path = self.images[idx]
        img = Image.open(img_path)
        img.thumbnail((400, 400))
        self.preview_img = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.preview_img, text="")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = SimpleWatermarkApp(root)
    root.mainloop()
