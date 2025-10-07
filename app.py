import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

class SimpleWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印工具 - 阶段2（含尺寸调整）")
        self.images = []
        self.current_image = None
        self.current_path = None

        # 左侧列表
        self.listbox = tk.Listbox(root, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

        # 右侧布局
        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 预览区
        self.preview_label = tk.Label(right_frame, bg="gray")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # 控制区
        ctrl_frame = tk.Frame(right_frame)
        ctrl_frame.pack(fill=tk.X)

        tk.Button(ctrl_frame, text="导入图片", command=self.add_images).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导入文件夹", command=self.add_folder).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导出当前图片", command=self.export_current_image).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导出全部图片", command=self.export_all_images).pack(side=tk.LEFT)

        # 水印设置
        settings_frame = tk.LabelFrame(right_frame, text="水印设置")
        settings_frame.pack(fill=tk.X, pady=5)

        tk.Label(settings_frame, text="水印文字：").grid(row=0, column=0, sticky="w")
        self.text_entry = tk.Entry(settings_frame, width=20)
        self.text_entry.insert(0, "示例水印")
        self.text_entry.grid(row=0, column=1)
        self.text_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        tk.Label(settings_frame, text="透明度(%)：").grid(row=1, column=0, sticky="w")
        self.alpha_scale = tk.Scale(settings_frame, from_=0, to=100, orient="horizontal", command=lambda e: self.update_preview())
        self.alpha_scale.set(50)
        self.alpha_scale.grid(row=1, column=1, sticky="we")

        tk.Label(settings_frame, text="位置：").grid(row=2, column=0, sticky="w")
        self.position_var = tk.StringVar(value="center")
        position_options = ["left_top", "right_top", "center", "left_bottom", "right_bottom"]
        self.position_menu = tk.OptionMenu(settings_frame, self.position_var, *position_options, command=lambda e: self.update_preview())
        self.position_menu.grid(row=2, column=1, sticky="we")

        # 导出设置
        export_frame = tk.LabelFrame(right_frame, text="导出设置")
        export_frame.pack(fill=tk.X, pady=5)

        tk.Label(export_frame, text="文件名前缀：").grid(row=0, column=0, sticky="w")
        self.prefix_entry = tk.Entry(export_frame, width=10)
        self.prefix_entry.grid(row=0, column=1, sticky="we")

        tk.Label(export_frame, text="文件名后缀：").grid(row=1, column=0, sticky="w")
        self.suffix_entry = tk.Entry(export_frame, width=10)
        self.suffix_entry.insert(0, "_watermarked")
        self.suffix_entry.grid(row=1, column=1, sticky="we")

        # ===== 新增：尺寸调整设置 =====
        tk.Label(export_frame, text="缩放模式：").grid(row=2, column=0, sticky="w")
        self.scale_mode = tk.StringVar(value="none")
        mode_menu = tk.OptionMenu(export_frame, self.scale_mode, "none", "width", "height", "percent")
        mode_menu.grid(row=2, column=1, sticky="we")

        tk.Label(export_frame, text="缩放数值：").grid(row=3, column=0, sticky="w")
        self.scale_value = tk.Entry(export_frame, width=10)
        self.scale_value.insert(0, "0")
        self.scale_value.grid(row=3, column=1, sticky="we")

    # ========== 图片导入 ==========
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

    # ========== 预览 ==========
    def show_preview(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        self.current_path = self.images[idx]
        self.current_image = Image.open(self.current_path).convert("RGBA")
        self.update_preview()

    def update_preview(self):
        if self.current_image is None:
            return
        text = self.text_entry.get()
        alpha = self.alpha_scale.get() / 100.0
        position = self.position_var.get()
        preview_img = self.apply_watermark(self.current_image, text, alpha, position)
        preview_resized = preview_img.copy()
        preview_resized.thumbnail((400, 400))
        self.tk_preview = ImageTk.PhotoImage(preview_resized)
        self.preview_label.config(image=self.tk_preview)

    # ========== 水印绘制 ==========
    def apply_watermark(self, image, text, alpha, position):
        img = image.copy()
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        try:
            font = ImageFont.truetype("arial.ttf", int(img.height * 0.05))
        except:
            font = ImageFont.load_default()

        text_size = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = text_size[2] - text_size[0], text_size[3] - text_size[1]
        margin = 20
        if position == "left_top":
            pos = (margin, margin)
        elif position == "right_top":
            pos = (img.width - text_w - margin, margin)
        elif position == "left_bottom":
            pos = (margin, img.height - text_h - margin)
        elif position == "right_bottom":
            pos = (img.width - text_w - margin, img.height - text_h - margin)
        else:
            pos = ((img.width - text_w) // 2, (img.height - text_h) // 2)

        draw.text(pos, text, font=font, fill=(255, 255, 255, int(255 * alpha)))
        return Image.alpha_composite(img, txt_layer)

    # ========== 尺寸调整 ==========
    def resize_image(self, img):
        """根据缩放设置调整尺寸"""
        mode = self.scale_mode.get()
        try:
            value = float(self.scale_value.get())
        except ValueError:
            return img  # 无效输入直接跳过

        if value <= 0 or mode == "none":
            return img

        w, h = img.size
        if mode == "width":
            new_w = int(value)
            new_h = int(h * new_w / w)
        elif mode == "height":
            new_h = int(value)
            new_w = int(w * new_h / h)
        elif mode == "percent":
            scale = value / 100.0
            new_w = int(w * scale)
            new_h = int(h * scale)
        else:
            return img

        return img.resize((new_w, new_h), Image.LANCZOS)

    # ========== 导出 ==========
    def export_current_image(self):
        if self.current_image is None:
            messagebox.showwarning("提示", "请先选择一张图片！")
            return

        out_dir = filedialog.askdirectory(title="选择导出文件夹")
        if not out_dir:
            return

        if os.path.abspath(os.path.dirname(self.current_path)) == os.path.abspath(out_dir):
            messagebox.showerror("错误", "禁止导出到原图片所在文件夹！")
            return

        text = self.text_entry.get()
        alpha = self.alpha_scale.get() / 100.0
        position = self.position_var.get()
        prefix = self.prefix_entry.get()
        suffix = self.suffix_entry.get()

        out_img = self.apply_watermark(self.current_image, text, alpha, position)
        out_img = self.resize_image(out_img)

        name, _ = os.path.splitext(os.path.basename(self.current_path))
        out_path = os.path.join(out_dir, f"{prefix}{name}{suffix}.png")
        out_img.convert("RGB").save(out_path)
        messagebox.showinfo("导出成功", f"已导出：{out_path}")

    def export_all_images(self):
        if not self.images:
            messagebox.showwarning("提示", "请先导入图片！")
            return

        out_dir = filedialog.askdirectory(title="选择导出文件夹")
        if not out_dir:
            return

        for path in self.images:
            if os.path.abspath(os.path.dirname(path)) == os.path.abspath(out_dir):
                messagebox.showerror("错误", f"文件 {os.path.basename(path)} 位于输出目录中，导出已取消！")
                return

        prefix = self.prefix_entry.get()
        suffix = self.suffix_entry.get()
        text = self.text_entry.get()
        alpha = self.alpha_scale.get() / 100.0
        position = self.position_var.get()

        count = 0
        for path in self.images:
            img = Image.open(path).convert("RGBA")
            out_img = self.apply_watermark(img, text, alpha, position)
            out_img = self.resize_image(out_img)
            name, _ = os.path.splitext(os.path.basename(path))
            out_path = os.path.join(out_dir, f"{prefix}{name}{suffix}.png")
            out_img.convert("RGB").save(out_path)
            count += 1

        messagebox.showinfo("导出完成", f"成功导出 {count} 张图片到：\n{out_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x600")
    app = SimpleWatermarkApp(root)
    root.mainloop()
