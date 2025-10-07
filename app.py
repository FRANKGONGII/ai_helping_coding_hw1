import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
TEMPLATE_FILE = "templates.json"

class SimpleWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印工具 - 带字体大小调节版")
        self.images = []
        self.current_image = None
        self.current_path = None
        self.current_color = (255, 255, 255)
        self.shadow_enabled = tk.BooleanVar(value=False)
        self.outline_enabled = tk.BooleanVar(value=False)
        self.watermark_pos = [0, 0]
        self.drag_data = {"x": 0, "y": 0}

        # ===== 左侧列表 =====
        self.listbox = tk.Listbox(root, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

        # ===== 右侧滚动面板 =====
        right_container = tk.Frame(root)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_canvas = tk.Canvas(right_container)
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(right_container, orient="vertical", command=self.right_canvas.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.right_canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame = tk.Frame(self.right_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
        )
        self.right_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # ===== 预览 Canvas =====
        self.canvas = tk.Canvas(self.scrollable_frame, bg="gray", height=400)
        self.canvas.pack(fill=tk.BOTH, expand=False)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_watermark)

        # ===== 控制区 =====
        ctrl_frame = tk.Frame(self.scrollable_frame)
        ctrl_frame.pack(fill=tk.X)
        tk.Button(ctrl_frame, text="导入图片", command=self.add_images).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导入文件夹", command=self.add_folder).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导出当前图片", command=self.export_current_image).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="导出全部图片", command=self.export_all_images).pack(side=tk.LEFT)

        # ===== 水印设置 =====
        settings_frame = tk.LabelFrame(self.scrollable_frame, text="水印设置")
        settings_frame.pack(fill=tk.X, pady=5)

        tk.Label(settings_frame, text="水印文字：").grid(row=0, column=0, sticky="w")
        self.text_entry = tk.Entry(settings_frame, width=20)
        self.text_entry.insert(0, "示例水印")
        self.text_entry.grid(row=0, column=1)
        self.text_entry.bind("<KeyRelease>", lambda e: self.update_preview())

        # ==== 颜色 + 字体大小 ====
        tk.Label(settings_frame, text="颜色：").grid(row=0, column=2, sticky="w")
        tk.Button(settings_frame, text="选择颜色", command=self.choose_color).grid(row=0, column=3, sticky="w")

        tk.Label(settings_frame, text="字体大小(%)：").grid(row=0, column=4, sticky="w")
        self.font_size_var = tk.DoubleVar(value=5.0)
        self.font_size_scale = tk.Scale(settings_frame, from_=1, to=20, resolution=0.5, orient="horizontal",
                                        variable=self.font_size_var, command=lambda e: self.update_preview())
        self.font_size_scale.grid(row=0, column=5, sticky="we")

        self.font_size_entry = tk.Entry(settings_frame, width=5)
        self.font_size_entry.insert(0, "5")
        self.font_size_entry.grid(row=0, column=6, sticky="w")
        self.font_size_entry.bind("<Return>", self.update_font_size_from_entry)

        tk.Label(settings_frame, text="%").grid(row=0, column=7, sticky="w")

        tk.Label(settings_frame, text="透明度(%)：").grid(row=1, column=0, sticky="w")
        self.alpha_scale = tk.Scale(settings_frame, from_=0, to=100, orient="horizontal",
                                    command=lambda e: self.update_preview())
        self.alpha_scale.set(50)
        self.alpha_scale.grid(row=1, column=1, sticky="we")

        tk.Label(settings_frame, text="位置：").grid(row=2, column=0, sticky="w")
        self.position_var = tk.StringVar(value="center")
        position_options = ["left_top", "right_top", "center", "left_bottom", "right_bottom"]
        self.position_menu = tk.OptionMenu(settings_frame, self.position_var, *position_options,
                                           command=self.set_position)
        self.position_menu.grid(row=2, column=1, sticky="we")

        tk.Checkbutton(settings_frame, text="阴影", variable=self.shadow_enabled,
                       command=self.update_preview).grid(row=3, column=0, sticky="w")
        tk.Checkbutton(settings_frame, text="描边", variable=self.outline_enabled,
                       command=self.update_preview).grid(row=3, column=1, sticky="w")

        # ===== 模板管理 =====
        tk.Label(settings_frame, text="模板：").grid(row=4, column=0, sticky="w")
        self.template_var = tk.StringVar(value="默认")
        self.templates = self.load_templates()
        if not self.templates:
            self.templates = {}
        self.template_menu = tk.OptionMenu(settings_frame, self.template_var, "默认")
        self.template_menu.grid(row=4, column=1, sticky="we")
        self.update_template_menu()
        tk.Button(settings_frame, text="保存模板", command=self.save_current_template).grid(row=4, column=2)
        tk.Button(settings_frame, text="删除模板", command=self.delete_template).grid(row=4, column=3)

        # ===== 导出设置 =====
        export_frame = tk.LabelFrame(self.scrollable_frame, text="导出设置")
        export_frame.pack(fill=tk.X, pady=5)

        tk.Label(export_frame, text="文件名前缀：").grid(row=0, column=0, sticky="w")
        self.prefix_entry = tk.Entry(export_frame, width=10)
        self.prefix_entry.grid(row=0, column=1, sticky="we")

        tk.Label(export_frame, text="文件名后缀：").grid(row=1, column=0, sticky="w")
        self.suffix_entry = tk.Entry(export_frame, width=10)
        self.suffix_entry.insert(0, "_watermarked")
        self.suffix_entry.grid(row=1, column=1, sticky="we")

        tk.Label(export_frame, text="缩放模式：").grid(row=2, column=0, sticky="w")
        self.scale_mode = tk.StringVar(value="none")
        mode_menu = tk.OptionMenu(export_frame, self.scale_mode, "none", "width", "height", "percent")
        mode_menu.grid(row=2, column=1, sticky="we")

        tk.Label(export_frame, text="缩放数值：").grid(row=3, column=0, sticky="w")
        self.scale_value = tk.Entry(export_frame, width=10)
        self.scale_value.insert(0, "0")
        self.scale_value.grid(row=3, column=1, sticky="we")

        tk.Label(export_frame, text="导出格式：").grid(row=4, column=0, sticky="w")
        self.format_var = tk.StringVar(value="PNG")
        format_menu = tk.OptionMenu(export_frame, self.format_var, "PNG", "JPEG")
        format_menu.grid(row=4, column=1, sticky="we")

        # 自动加载上一次模板
        last_tpl = self.templates.get("_last_used")
        if last_tpl:
            self.load_template(last_tpl)

    # ===== 字体选择 =====
    def get_font(self, img_height):
        percent = self.font_size_var.get() / 100.0
        font_size = max(12, int(img_height * percent))
        win_font = "C:\\Windows\\Fonts\\msyh.ttc"
        if os.path.exists(win_font):
            return ImageFont.truetype(win_font, font_size)
        linux_font = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        if os.path.exists(linux_font):
            return ImageFont.truetype(linux_font, font_size)
        mac_font = "/System/Library/Fonts/STHeiti Medium.ttc"
        if os.path.exists(mac_font):
            return ImageFont.truetype(mac_font, font_size)
        raise RuntimeError("未找到可用的TrueType字体，请安装中文字体")

    def update_font_size_from_entry(self, event=None):
        try:
            val = float(self.font_size_entry.get())
            if 1 <= val <= 20:
                self.font_size_var.set(val)
                self.update_preview()
        except ValueError:
            pass

    # ===== 图片导入 =====
    def add_images(self):
        files = filedialog.askopenfilenames(title="选择图片",
                                            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")])
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

    # ===== 预览 =====
    def show_preview(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        self.current_path = self.images[idx]
        self.current_image = Image.open(self.current_path).convert("RGBA")
        self.watermark_pos = None
        self.update_preview()

    def set_position(self, val):
        self.watermark_pos = None
        self.update_preview()

    def update_preview(self):
        if self.current_image is None:
            return
        text = self.text_entry.get()
        alpha = self.alpha_scale.get() / 100.0
        pos_to_use = self.watermark_pos if self.watermark_pos else self.position_var.get()
        preview_img = self.apply_watermark(self.current_image, text, alpha, pos_to_use,
                                           font=self.get_font(self.current_image.height),
                                           color=self.current_color,
                                           shadow=self.shadow_enabled.get(),
                                           outline=self.outline_enabled.get())
        preview_resized = preview_img.copy()
        preview_resized.thumbnail((400, 400))
        self.tk_preview = ImageTk.PhotoImage(preview_resized)
        self.canvas.delete("all")
        self.canvas.create_image(200, 200, image=self.tk_preview)

    # ===== 水印绘制 =====
    def apply_watermark(self, image, text, alpha, position, font=None, color=(255, 255, 255),
                        shadow=False, outline=False):
        img = image.copy()
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        if font is None:
            font = self.get_font(img.height)

        text_size = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = text_size[2] - text_size[0], text_size[3] - text_size[1]
        margin = 20

        if isinstance(position, tuple):
            pos = position
        else:
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

        if shadow:
            shadow_color = (0, 0, 0, int(255 * alpha))
            draw.text((pos[0]+2, pos[1]+2), text, font=font, fill=shadow_color)
        if outline:
            outline_color = (0, 0, 0, int(255*alpha))
            offsets = [(-1,0),(1,0),(0,-1),(0,1)]
            for dx,dy in offsets:
                draw.text((pos[0]+dx,pos[1]+dy), text, font=font, fill=outline_color)

        rgba = (*color, int(255 * alpha))
        draw.text(pos, text, font=font, fill=rgba)
        return Image.alpha_composite(img, txt_layer)

    # ===== 拖拽 =====
    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def drag_watermark(self, event):
        if self.current_image is None:
            return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        if self.watermark_pos is None:
            self.watermark_pos = ((self.current_image.width - 100)//2, (self.current_image.height-30)//2)
        x = self.watermark_pos[0] + dx
        y = self.watermark_pos[1] + dy
        self.watermark_pos = (x, y)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.update_preview()

    # ===== 其他导出逻辑同原版 =====
    def resize_image(self, img):
        mode = self.scale_mode.get()
        try:
            value = float(self.scale_value.get())
        except ValueError:
            return img
        if value <= 0 or mode=="none":
            return img
        w,h = img.size
        if mode=="width":
            new_w=int(value)
            new_h=int(h*new_w/w)
        elif mode=="height":
            new_h=int(value)
            new_w=int(w*new_h/h)
        elif mode=="percent":
            scale=value/100.0
            new_w=int(w*scale)
            new_h=int(h*scale)
        else:
            return img
        return img.resize((new_w,new_h),Image.LANCZOS)

    def save_image(self, img, out_path, fmt):
        if fmt.upper()=="JPEG":
            img.convert("RGB").save(out_path,format="JPEG",quality=95)
        else:
            img.save(out_path,format="PNG")

    def export_current_image(self):
        if self.current_image is None:
            messagebox.showwarning("提示","请先选择一张图片！")
            return
        out_dir=filedialog.askdirectory(title="选择导出文件夹")
        if not out_dir:
            return
        if os.path.abspath(os.path.dirname(self.current_path))==os.path.abspath(out_dir):
            messagebox.showerror("错误","禁止导出到原图片所在文件夹！")
            return
        text=self.text_entry.get()
        alpha=self.alpha_scale.get()/100.0
        position=self.watermark_pos if self.watermark_pos else self.position_var.get()
        prefix=self.prefix_entry.get()
        suffix=self.suffix_entry.get()
        fmt=self.format_var.get()

        out_img=self.apply_watermark(self.current_image,text,alpha,position,
                                     font=self.get_font(self.current_image.height),
                                     color=self.current_color,
                                     shadow=self.shadow_enabled.get(),
                                     outline=self.outline_enabled.get())
        out_img=self.resize_image(out_img)
        name,_=os.path.splitext(os.path.basename(self.current_path))
        out_path=os.path.join(out_dir,f"{prefix}{name}{suffix}.{fmt.lower()}")
        self.save_image(out_img,out_path,fmt)
        messagebox.showinfo("导出成功",f"已导出：{out_path}")

    def export_all_images(self):
        if not self.images:
            messagebox.showwarning("提示","请先导入图片！")
            return
        out_dir=filedialog.askdirectory(title="选择导出文件夹")
        if not out_dir:
            return
        prefix=self.prefix_entry.get()
        suffix=self.suffix_entry.get()
        text=self.text_entry.get()
        alpha=self.alpha_scale.get()/100.0
        fmt=self.format_var.get()
        count=0
        for path in self.images:
            if os.path.abspath(os.path.dirname(path))==os.path.abspath(out_dir):
                messagebox.showerror("错误",f"文件 {os.path.basename(path)} 位于输出目录中，导出已取消！")
                return
            img=Image.open(path).convert("RGBA")
            position=self.position_var.get()
            out_img=self.apply_watermark(img,text,alpha,position,
                                         font=self.get_font(img.height),
                                         color=self.current_color,
                                         shadow=self.shadow_enabled.get(),
                                         outline=self.outline_enabled.get())
            out_img=self.resize_image(out_img)
            name,_=os.path.splitext(os.path.basename(path))
            out_path=os.path.join(out_dir,f"{prefix}{name}{suffix}.{fmt.lower()}")
            self.save_image(out_img,out_path,fmt)
            count+=1
        messagebox.showinfo("导出完成",f"成功导出 {count} 张图片到：\n{out_dir}")

    # ===== 颜色选择 =====
    def choose_color(self):
        color_code=colorchooser.askcolor(title="选择水印颜色")
        if color_code:
            self.current_color=tuple(int(c) for c in color_code[0])
            self.update_preview()

    # ===== 模板管理 =====
    def save_current_template(self):
        name=simple_input("输入模板名称")
        if not name:
            return
        tpl={
            "text":self.text_entry.get(),
            "color":self.current_color,
            "alpha":self.alpha_scale.get(),
            "font_size":self.font_size_var.get(),
            "position":self.watermark_pos,
            "shadow":self.shadow_enabled.get(),
            "outline":self.outline_enabled.get(),
            "scale_mode":self.scale_mode.get(),
            "scale_value":self.scale_value.get(),
            "prefix":self.prefix_entry.get(),
            "suffix":self.suffix_entry.get(),
            "format":self.format_var.get()
        }
        self.templates[name]=tpl
        self.templates["_last_used"]=name
        self.save_templates()
        self.update_template_menu()
        messagebox.showinfo("模板保存","模板已保存！")

    def load_template(self,name):
        tpl=self.templates.get(name)
        if not tpl:
            return
        self.text_entry.delete(0,tk.END)
        self.text_entry.insert(0,tpl["text"])
        self.current_color=tuple(tpl["color"])
        self.alpha_scale.set(tpl["alpha"])
        self.font_size_var.set(tpl.get("font_size",5.0))
        self.font_size_entry.delete(0,tk.END)
        self.font_size_entry.insert(0,str(tpl.get("font_size",5.0)))
        self.watermark_pos = tpl["position"]
        self.shadow_enabled.set(tpl.get("shadow",False))
        self.outline_enabled.set(tpl.get("outline",False))
        self.scale_mode.set(tpl.get("scale_mode","none"))
        self.scale_value.delete(0,tk.END)
        self.scale_value.insert(0,tpl.get("scale_value","0"))
        self.prefix_entry.delete(0,tk.END)
        self.prefix_entry.insert(0,tpl.get("prefix",""))
        self.suffix_entry.delete(0,tk.END)
        self.suffix_entry.insert(0,tpl.get("suffix","_watermarked"))
        self.format_var.set(tpl.get("format","PNG"))
        self.update_preview()

    def delete_template(self):
        name=self.template_var.get()
        if name in self.templates:
            del self.templates[name]
            self.save_templates()
            self.update_template_menu()
            messagebox.showinfo("模板删除","模板已删除！")

    def update_template_menu(self):
        menu=self.template_menu["menu"]
        menu.delete(0,tk.END)
        for name in self.templates.keys():
            if name=="_last_used":
                continue
            menu.add_command(label=name,command=lambda v=name:self.select_template(v))

    def select_template(self,name):
        self.template_var.set(name)
        self.load_template(name)

    def save_templates(self):
        with open(TEMPLATE_FILE,"w",encoding="utf-8") as f:
            json.dump(self.templates,f,ensure_ascii=False,indent=2)

    def load_templates(self):
        if os.path.exists(TEMPLATE_FILE):
            with open(TEMPLATE_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        return {}

# ===== 简单输入框 =====
def simple_input(prompt):
    win=tk.Toplevel()
    win.title("输入")
    tk.Label(win,text=prompt).pack(padx=10,pady=5)
    entry=tk.Entry(win)
    entry.pack(padx=10,pady=5)
    res=[]
    def ok():
        res.append(entry.get())
        win.destroy()
    tk.Button(win,text="确定",command=ok).pack(pady=5)
    win.grab_set()
    win.wait_window()
    return res[0] if res else None

if __name__=="__main__":
    root=tk.Tk()
    root.geometry("1100x700")
    app=SimpleWatermarkApp(root)
    root.mainloop()
