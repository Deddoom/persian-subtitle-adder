#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم خودکار زیرنویس و هاردساب ویدیو برای زبان فارسی
نسخه: 1.0
"""

import os
import sys
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# بررسی و نصب کتابخانه‌های مورد نیاز
def check_and_install_requirements():
    """بررسی و راهنمای نصب کتابخانه‌های مورد نیاز"""
    required_packages = {
        'faster_whisper': 'faster-whisper',
        'transformers': 'transformers',
        'torch': 'torch',
        'pysubs2': 'pysubs2',
        'moviepy': 'moviepy',
        'arabic_reshaper': 'arabic-reshaper', 
        'bidi': 'python-bidi'                 
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    return missing

class PersianSubtitleApp:
    """کلاس اصلی برنامه زیرنویس‌ساز فارسی"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("سیستم خودکار زیرنویس فارسی - Persian Auto Subtitle System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # متغیرهای برنامه
        self.video_path = tk.StringVar()
        self.input_mode = tk.StringVar(value="single")
        self.batch_dir = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.home() / "SubtitleOutputs"))
        self.video_language = tk.StringVar(value="fa")
        self.font_name = tk.StringVar(value="Vazirmatn")
        self.font_size = tk.IntVar(value=18)
        self.font_color = tk.StringVar(value="#FFFFFF")
        self.outline_color = tk.StringVar(value="#000000")
        self.outline_width = tk.IntVar(value=2)
        self.subtitle_position = tk.StringVar(value="bottom")
        self.model_size = tk.StringVar(value="medium")
        self.processing = False
        
        self.create_widgets()
        self.check_dependencies()
    
    def create_widgets(self):
        """ایجاد رابط گرافیکی"""
        
        # نوار بالا - اطلاعات
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        title_label = ttk.Label(
            header_frame, 
            text="🎬 سیستم هوشمند زیرنویس‌ساز فارسی",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=5)
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Automatic Persian Subtitle Generator with AI",
            font=('Arial', 10, 'italic')
        )
        subtitle_label.grid(row=1, column=0)
        
        # نوت‌بوک برای تب‌ها
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # تب اصلی - انتخاب فایل و تنظیمات اصلی
        main_tab = ttk.Frame(notebook, padding="10")
        notebook.add(main_tab, text="📁 فایل ورودی و خروجی")
        
        self.create_main_tab(main_tab)
        
        # تب تنظیمات - شخصی‌سازی
        settings_tab = ttk.Frame(notebook, padding="10")
        notebook.add(settings_tab, text="⚙️ تنظیمات ظاهری")
        
        self.create_settings_tab(settings_tab)
        
        # تب پیشرفته
        advanced_tab = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_tab, text="🔧 تنظیمات پیشرفته")
        
        self.create_advanced_tab(advanced_tab)
        
        # پنل لاگ
        log_frame = ttk.LabelFrame(self.root, text="📋 وضعیت پردازش", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # دکمه‌های اصلی
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.process_btn = ttk.Button(
            button_frame,
            text="▶️ شروع پردازش",
            command=self.start_processing,
            style='Accent.TButton'
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹️ توقف",
            command=self.stop_processing,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🗑️ پاک کردن لاگ",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="❌ خروج",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)
        
        # تنظیم وزن برای تغییر اندازه
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
    
    def create_main_tab(self, parent):
        """تب اصلی - انتخاب فایل"""
        
        # انتخاب حالت ورودی
        mode_frame = ttk.LabelFrame(parent, text="📂 نوع ورودی", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(mode_frame, text="فایل تکی (Single File)", 
                       variable=self.input_mode, value="single",
                       command=self.toggle_input_mode).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(mode_frame, text="پردازش گروهی پوشه (Batch Folder)", 
                       variable=self.input_mode, value="batch",
                       command=self.toggle_input_mode).pack(side=tk.LEFT, padx=10)

        # فریم انتخاب فایل تکی
        self.single_frame = ttk.Frame(parent)
        self.single_frame.pack(fill=tk.X, pady=5)
        
        video_group = ttk.LabelFrame(self.single_frame, text="📹 انتخاب فایل ویدیو", padding="10")
        video_group.pack(fill=tk.X)
        
        ttk.Entry(video_group, textvariable=self.video_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(video_group, text="انتخاب فایل", command=self.select_video).pack(side=tk.LEFT, padx=5)

        # فریم انتخاب پوشه (برای حالت گروهی) - ابتدا مخفی است
        self.batch_frame = ttk.Frame(parent)
        
        batch_group = ttk.LabelFrame(self.batch_frame, text="📁 انتخاب پوشه حاوی ویدیوها", padding="10")
        batch_group.pack(fill=tk.X)
        
        ttk.Entry(batch_group, textvariable=self.batch_dir, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(batch_group, text="انتخاب پوشه", command=self.select_batch_dir).pack(side=tk.LEFT, padx=5)

        # انتخاب پوشه خروجی (مشترک)
        output_frame = ttk.LabelFrame(parent, text="💾 پوشه ذخیره خروجی", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="انتخاب پوشه", command=self.select_output_dir).pack(side=tk.LEFT, padx=5)
        # زبان ویدیو
        lang_frame = ttk.LabelFrame(parent, text="🌐 زبان ویدیوی ورودی", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        languages = [
            ("فارسی (Persian)", "fa"),
            ("انگلیسی (English)", "en"),
            ("عربی (Arabic)", "ar"),
            ("فرانسوی (French)", "fr"),
            ("آلمانی (German)", "de"),
            ("اسپانیایی (Spanish)", "es"),
            ("تشخیص خودکار (Auto)", "auto")
        ]
        
        for i, (text, value) in enumerate(languages):
            ttk.Radiobutton(
                lang_frame,
                text=text,
                variable=self.video_language,
                value=value
            ).grid(row=i//3, column=i%3, sticky=tk.W, padx=10, pady=2)
        
        # اطلاعات
        info_frame = ttk.LabelFrame(parent, text="ℹ️ راهنما", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_text = """
        🔹 ابتدا فایل ویدیوی خود را انتخاب کنید
        🔹 پوشه‌ای برای ذخیره خروجی مشخص کنید
        🔹 زبان صوتی ویدیو را انتخاب کنید (برای ویدیوهای غیرفارسی، ترجمه خودکار انجام می‌شود)
        🔹 در تب "تنظیمات ظاهری" می‌توانید فونت و رنگ را شخصی‌سازی کنید
        🔹 پس از تنظیمات، دکمه "شروع پردازش" را بزنید
        
        ⚠️ توجه: پردازش بسته به طول ویدیو ممکن است زمان‌بر باشد.
        """
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        self.toggle_input_mode()
    
    def toggle_input_mode(self):
        """تغییر نمایش بین حالت تکی و گروهی"""
        if self.input_mode.get() == "single":
            self.batch_frame.pack_forget()
            self.single_frame.pack(fill=tk.X, pady=5)
        else:
            self.single_frame.pack_forget()
            self.batch_frame.pack(fill=tk.X, pady=5)

    def select_batch_dir(self):
        """انتخاب پوشه ورودی برای حالت گروهی"""
        directory = filedialog.askdirectory(title="انتخاب پوشه حاوی ویدیوها")
        if directory:
            self.batch_dir.set(directory)
            self.log(f"📂 پوشه ورودی انتخاب شد: {directory}")
    
    def create_settings_tab(self, parent):
        """تب تنظیمات ظاهری"""
        
        # فونت
        font_frame = ttk.LabelFrame(parent, text="🔤 تنظیمات فونت", padding="10")
        font_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(font_frame, text="نام فونت:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        font_combo = ttk.Combobox(
            font_frame,
            textvariable=self.font_name,
            values=["Vazirmatn", "Samim", "Shabnam", "Sahel", "Tahoma", "Arial"]
        )
        font_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(font_frame, text="اندازه فونت:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(
            font_frame,
            from_=12,
            to=48,
            textvariable=self.font_size,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # رنگ‌ها
        color_frame = ttk.LabelFrame(parent, text="🎨 تنظیمات رنگ", padding="10")
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_frame, text="رنگ متن:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(color_frame, textvariable=self.font_color, width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(
            color_frame,
            text="انتخاب",
            command=lambda: self.choose_color(self.font_color)
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(color_frame, text="رنگ حاشیه:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(color_frame, textvariable=self.outline_color, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(
            color_frame,
            text="انتخاب",
            command=lambda: self.choose_color(self.outline_color)
        ).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(color_frame, text="ضخامت حاشیه:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(
            color_frame,
            from_=0,
            to=5,
            textvariable=self.outline_width,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # موقعیت
        position_frame = ttk.LabelFrame(parent, text="📍 موقعیت زیرنویس", padding="10")
        position_frame.pack(fill=tk.X, pady=5)
        
        positions = [
            ("پایین وسط", "bottom"),
            ("بالا وسط", "top"),
            ("پایین چپ", "bottom-left"),
            ("پایین راست", "bottom-right")
        ]
        
        for i, (text, value) in enumerate(positions):
            ttk.Radiobutton(
                position_frame,
                text=text,
                variable=self.subtitle_position,
                value=value
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=5)
        
        # پیش‌نمایش
        preview_frame = ttk.LabelFrame(parent, text="👁️ پیش‌نمایش", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_label = tk.Label(
            preview_frame,
            text="این یک نمونه زیرنویس است",
            font=(self.font_name.get(), self.font_size.get()),
            fg=self.font_color.get(),
            bg='#1a1a1a'
        )
        self.preview_label.pack(pady=20)
        
        ttk.Button(
            preview_frame,
            text="🔄 بروزرسانی پیش‌نمایش",
            command=self.update_preview
        ).pack()
    
    def create_advanced_tab(self, parent):
        """تب تنظیمات پیشرفته"""
        
        # اندازه مدل
        model_frame = ttk.LabelFrame(parent, text="🤖 اندازه مدل Whisper", padding="10")
        model_frame.pack(fill=tk.X, pady=5)
        
        model_info = """
        اندازه مدل تاثیر مستقیم بر دقت و سرعت دارد:
        
        • tiny: سریع‌ترین، کم‌ترین دقت (~1GB RAM)
        • base: سریع، دقت متوسط (~1GB RAM)
        • small: متوسط در سرعت و دقت (~2GB RAM)
        • medium: دقت خوب، سرعت متوسط (~5GB RAM) - پیشنهادی
        • large-v3: بالاترین دقت، کندترین (~10GB RAM)
        """
        
        ttk.Label(model_frame, text=model_info, justify=tk.LEFT).pack(anchor=tk.W, pady=5)
        
        models = ["tiny", "base", "small", "medium", "large-v3"]
        for model in models:
            ttk.Radiobutton(
                model_frame,
                text=model,
                variable=self.model_size,
                value=model
            ).pack(anchor=tk.W, padx=20)
        
        # سخت‌افزار
        hardware_frame = ttk.LabelFrame(parent, text="⚡ تنظیمات سخت‌افزاری", padding="10")
        hardware_frame.pack(fill=tk.X, pady=5)
        
        hardware_info = """
        🔹 استفاده از GPU (کارت گرافیک NVIDIA): سرعت پردازش را تا 10 برابر افزایش می‌دهد
        🔹 بدون GPU: پردازش روی CPU انجام می‌شود (کندتر اما قابل اطمینان)
        
        ⚠️ برای استفاده از GPU، نصب CUDA Toolkit الزامی است.
        """
        
        ttk.Label(hardware_frame, text=hardware_info, justify=tk.LEFT).pack(anchor=tk.W)
    
    def select_video(self):
        """انتخاب فایل ویدیو"""
        filename = filedialog.askopenfilename(
            title="انتخاب فایل ویدیو",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.video_path.set(filename)
            self.log(f"✅ فایل انتخاب شد: {filename}")
    
    def select_output_dir(self):
        """انتخاب پوشه خروجی"""
        directory = filedialog.askdirectory(title="انتخاب پوشه خروجی")
        if directory:
            self.output_dir.set(directory)
            self.log(f"✅ پوشه خروجی: {directory}")
    
    def choose_color(self, color_var):
        """انتخاب رنگ"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="انتخاب رنگ")
        if color[1]:
            color_var.set(color[1])
            self.update_preview()
    
    def update_preview(self):
        """بروزرسانی پیش‌نمایش زیرنویس"""
        try:
            self.preview_label.config(
                font=(self.font_name.get(), self.font_size.get()),
                fg=self.font_color.get()
            )
            self.log("🔄 پیش‌نمایش بروز شد")
        except Exception as e:
            self.log(f"❌ خطا در بروزرسانی پیش‌نمایش: {str(e)}")
    
    def check_dependencies(self):
        """بررسی وابستگی‌ها"""
        self.log("🔍 در حال بررسی وابستگی‌ها...")
        
        missing = check_and_install_requirements()
        
        if missing:
            self.log("⚠️ کتابخانه‌های زیر نصب نشده‌اند:")
            for pkg in missing:
                self.log(f"   - {pkg}")
            self.log("\n📦 برای نصب، دستور زیر را در ترمینال اجرا کنید:")
            self.log(f"pip install {' '.join(missing)}")
            messagebox.showwarning(
                "وابستگی‌های ناقص",
                f"کتابخانه‌های زیر باید نصب شوند:\n\n{', '.join(missing)}\n\n"
                f"دستور نصب:\npip install {' '.join(missing)}"
            )
        else:
            self.log("✅ تمام وابستگی‌ها نصب شده‌اند")
        
        # بررسی FFmpeg
        if not self.check_ffmpeg():
            self.log("⚠️ FFmpeg یافت نشد. لطفاً آن را نصب کنید.")
            messagebox.showwarning(
                "FFmpeg یافت نشد",
                "FFmpeg برای چسباندن زیرنویس به ویدیو ضروری است.\n\n"
                "دانلود: https://ffmpeg.org/download.html"
            )
    
    def check_ffmpeg(self):
        """بررسی نصب FFmpeg"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def log(self, message):
        """نمایش پیام در لاگ"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """پاک کردن لاگ"""
        self.log_text.delete(1.0, tk.END)
    
    def start_processing(self):
        """شروع پردازش (هوشمند)"""
        
        # بررسی ورودی بر اساس حالت انتخاب شده
        target_files = []
        
        if self.input_mode.get() == "single":
            if not self.video_path.get() or not os.path.exists(self.video_path.get()):
                messagebox.showerror("خطا", "لطفاً فایل ویدیو را انتخاب کنید")
                return
            target_files = [self.video_path.get()]
            
        else: # حالت Batch
            if not self.batch_dir.get() or not os.path.exists(self.batch_dir.get()):
                messagebox.showerror("خطا", "لطفاً پوشه ویدیوها را انتخاب کنید")
                return
            
            # پیدا کردن تمام ویدیوها در پوشه
            valid_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv')
            for root_dir, _, files in os.walk(self.batch_dir.get()):
                for file in files:
                    if file.lower().endswith(valid_extensions):
                        target_files.append(os.path.join(root_dir, file))
            
            if not target_files:
                messagebox.showerror("خطا", "هیچ فایل ویدیویی در پوشه انتخاب شده یافت نشد!")
                return
                
            self.log(f"📦 تعداد {len(target_files)} فایل برای پردازش پیدا شد.")

        # ایجاد پوشه خروجی
        os.makedirs(self.output_dir.get(), exist_ok=True)
        
        # قفل کردن دکمه‌ها
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.processing = True
        
        # ارسال لیست فایل‌ها به ترد پردازش
        thread = threading.Thread(target=self.process_manager, args=(target_files,), daemon=True)
        thread.start()
    
    def process_manager(self, file_list):
        """مدیریت صف پردازش فایل‌ها"""
        total_files = len(file_list)
        
        for index, video_file in enumerate(file_list):
            if not self.processing:
                self.log("⏹️ پردازش توسط کاربر متوقف شد.")
                break
            
            self.log("\n" + "*"*60)
            self.log(f"🎬 پردازش فایل {index + 1} از {total_files}")
            self.log(f"📂 فایل جاری: {os.path.basename(video_file)}")
            self.log("*"*60 + "\n")
            
            try:
                # فراخوانی تابع اصلی پردازش برای هر فایل
                self.process_video(input_file=video_file)
                
            except Exception as e:
                self.log(f"❌ خطا در پردازش فایل {os.path.basename(video_file)}: {e}")
                self.log("⚠️ ادامه پردازش فایل بعدی...")
                continue
        
        # پایان کار
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.processing = False
        
        if total_files > 1:
            messagebox.showinfo("پایان", "پردازش گروهی تمام فایل‌ها به پایان رسید.")
    
    def stop_processing(self):
        """توقف پردازش"""
        self.processing = False
        self.log("⏸️ درخواست توقف دریافت شد...")
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def process_video(self, input_file=None):
        """پردازش اصلی ویدیو"""
        try:
            video_file = input_file if input_file else self.video_path.get()
            
            if not os.path.exists(video_file):
                raise Exception("فایل یافت نشد")

            video_name = Path(video_file).stem
            
            # مرحله 1: استخراج صدا
            self.log("\n📀 مرحله 1: استخراج صدا از ویدیو...")
            audio_file = self.extract_audio(video_file)
            
            if not self.processing:
                return
            
            # مرحله 2: تشخیص گفتار
            self.log("\n🎤 مرحله 2: تشخیص گفتار با Whisper...")
            segments = self.transcribe_audio(audio_file)
            
            if not self.processing:
                return
            
            # مرحله 3: ترجمه (در صورت نیاز)
            if self.video_language.get() not in ['fa', 'auto']:
                self.log("\n🌐 مرحله 3: ترجمه به فارسی...")
                segments = self.translate_segments(segments)
            
            if not self.processing:
                return
            
            # مرحله 4: ایجاد فایل زیرنویس
            self.log("\n📝 مرحله 4: ایجاد فایل زیرنویس ASS...")
            subtitle_file = self.create_subtitle_file(segments, video_name)
            
            if not self.processing:
                return
            
            # مرحله 5: چسباندن زیرنویس
            self.log("\n🎬 مرحله 5: چسباندن زیرنویس به ویدیو...")
            output_file = self.hardcode_subtitle(video_file, subtitle_file, video_name)
            
            self.log("\n" + "="*60)
            self.log("✅ پردازش با موفقیت تکمیل شد!")
            self.log(f"📁 فایل خروجی: {output_file}")
            self.log("="*60)
            
            
            
        except Exception as e:
            self.log(f"\n❌ خطا در پردازش: {str(e)}")
            messagebox.showerror("خطا", f"خطا در پردازش:\n{str(e)}")
            raise e
        
        finally:
            self.log(f"✅ پایان پردازش: {video_name}")
        
    
    def extract_audio(self, video_file):
        """استخراج صدا از ویدیو"""
        try:
            from moviepy.editor import VideoFileClip
            
            audio_file = os.path.join(
                self.output_dir.get(),
                f"{Path(video_file).stem}_audio.wav"
            )
            
            video = VideoFileClip(video_file)
            video.audio.write_audiofile(audio_file, logger=None)
            video.close()
            
            self.log(f"✅ صدا استخراج شد: {audio_file}")
            return audio_file
            
        except Exception as e:
            raise Exception(f"خطا در استخراج صدا: {str(e)}")
    
    def transcribe_audio(self, audio_file):
        """تشخیص گفتار با Whisper + نوار پیشرفت"""
        try:
            from faster_whisper import WhisperModel
            import torch
            
            self.log(f"⏳ در حال بارگذاری/دانلود مدل {self.model_size.get()}...")
            self.log("⚠️ اگر اولین بار است، دانلود مدل ممکن است چند دقیقه طول بکشد. لطفاً صبر کنید...")
            
            # فعال کردن نوار پیشرفت
            self.progress_bar.start(10)
            self.root.update()
            
            # تشخیص سخت‌افزار
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            self.log(f"🖥️ دستگاه پردازش: {device.upper()}")
            
            # بارگذاری مدل (اینجا زمان‌بر است)
            model = WhisperModel(
                self.model_size.get(),
                device=device,
                compute_type=compute_type
            )
            
            # غیرفعال کردن نوار پیشرفت بعد از لود مدل
            self.progress_bar.stop()
            
            language = None if self.video_language.get() == "auto" else self.video_language.get()
            
            self.log("🎯 در حال تشخیص گفتار (Transcription)...")
            segments, info = model.transcribe(
                audio_file,
                beam_size=5,
                language=language
            )
            
            segments_list = list(segments)
            
            self.log(f"✅ تعداد {len(segments_list)} بخش شناسایی شد")
            self.log(f"📊 زبان شناسایی شده: {info.language}")
            
            return segments_list
            
        except Exception as e:
            self.progress_bar.stop()
            raise Exception(f"خطا در تشخیص گفتار: {str(e)}")
    
    def translate_segments(self, segments):
        """ترجمه زیرنویس‌ها به فارسی"""
        try:
            from transformers import pipeline
            
            self.log("⏳ در حال بارگذاری مدل ترجمه...")
            
            translator = pipeline(
                "translation",
                model="facebook/nllb-200-distilled-600M",
                src_lang=self.get_nllb_lang_code(self.video_language.get()),
                tgt_lang="fas_Arab"
            )
            
            translated_segments = []
            total = len(segments)
            
            for i, segment in enumerate(segments):
                if not self.processing:
                    break
                
                self.log(f"🔄 ترجمه بخش {i+1}/{total}...")
                
                translation = translator(segment.text, max_length=400)[0]['translation_text']
                
                # نگه‌داری زمان‌بندی اصلی
                segment.text = translation
                translated_segments.append(segment)
            
            self.log("✅ ترجمه تکمیل شد")
            return translated_segments
            
        except Exception as e:
            self.log(f"⚠️ خطا در ترجمه، از متن اصلی استفاده می‌شود: {str(e)}")
            return segments
    
    def get_nllb_lang_code(self, lang):
        """تبدیل کد زبان به فرمت NLLB"""
        lang_map = {
            'en': 'eng_Latn',
            'ar': 'arb_Arab',
            'fr': 'fra_Latn',
            'de': 'deu_Latn',
            'es': 'spa_Latn'
        }
        return lang_map.get(lang, 'eng_Latn')
    
    def fix_text_direction(self, text):
        """اصلاح جهت متن و حروف برای نمایش صحیح فارسی در زیرنویس هاردساب"""
        try:
            # اگر کتابخانه‌ها لود نشده باشند، همان متن اصلی را برگردان
            if 'arabic_reshaper' not in sys.modules or 'bidi' not in sys.modules:
                import arabic_reshaper
                from bidi.algorithm import get_display
            
            # بازآرایی حروف (چسباندن حروف جدا)
            reshaped_text = arabic_reshaper.reshape(text)
            # اصلاح جهت (راست‌چین کردن)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            self.log(f"⚠️ خطا در اصلاح فونت فارسی: {e}")
            return text
        
    def create_subtitle_file(self, segments, video_name):
        """ایجاد فایل زیرنویس ASS"""
        try:
            import pysubs2
            
            subs = pysubs2.SSAFile()
            
            # تعریف استایل
            style = pysubs2.SSAStyle()
            style.fontname = self.font_name.get()
            style.fontsize = self.font_size.get()
            style.primarycolor = pysubs2.Color(*self.hex_to_rgb(self.font_color.get()))
            style.outlinecolor = pysubs2.Color(*self.hex_to_rgb(self.outline_color.get()))
            style.outline = self.outline_width.get()
            style.bold = True
            
            # تنظیم موقعیت
            alignment_map = {
                'bottom': 2,
                'top': 8,
                'bottom-left': 1,
                'bottom-right': 3
            }
            style.alignment = alignment_map.get(self.subtitle_position.get(), 2)
            
            subs.styles["Default"] = style
            
            # اضافه کردن رویدادها
            for segment in segments:
                # === تغییر مهم: اصلاح متن برای هاردساب ===
                # برای فایل ASS که قرار است هاردساب شود، باید متن را برعکس کنیم
                display_text = self.fix_text_direction(segment.text)
                
                event = pysubs2.SSAEvent(
                    start=int(segment.start * 1000),
                    end=int(segment.end * 1000),
                    text=display_text
                )
                subs.append(event)
            
            subtitle_file = os.path.join(
                self.output_dir.get(),
                f"{video_name}_persian.ass"
            )
            
            subs.save(subtitle_file)
            
            self.log(f"✅ فایل زیرنویس ایجاد شد: {subtitle_file}")
            return subtitle_file
            
        except Exception as e:
            raise Exception(f"خطا در ایجاد فایل زیرنویس: {str(e)}")
    
    def hardcode_subtitle(self, video_file, subtitle_file, video_name):
        """چسباندن زیرنویس به ویدیو با اصلاح مسیر ویندوز"""
        try:
            output_file = os.path.join(
                self.output_dir.get(),
                f"{video_name}_with_persian_subtitle.mp4"
            )
            
            # === اصلاح مسیر برای ویندوز (فرمت FFmpeg) ===
            # در ویندوز، FFmpeg با \ مشکل دارد و : باید اسکیپ شود
            if os.name == 'nt':
                sub_path_fixed = subtitle_file.replace('\\', '/').replace(':', '\\:')
            else:
                sub_path_fixed = subtitle_file

            # دستور FFmpeg
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-vf', f"ass='{sub_path_fixed}'", # استفاده از مسیر اصلاح شده
                '-c:a', 'copy',
                '-y', # بازنویسی فایل اگر وجود داشت
                output_file
            ]
            
            self.log(f"⏳ در حال اجرای FFmpeg برای {video_name}...")
            # self.log(f"دستور: {' '.join(cmd)}") # برای دیباگ
            
            # استفاده از startupinfo برای مخفی کردن پنجره کنسول FFmpeg در ویندوز
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8', # تنظیم انکدینگ برای جلوگیری از خطای کاراکتر
                startupinfo=startupinfo
            )
            
            # خواندن خروجی برای نمایش زنده وضعیت
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                if 'time=' in line and self.processing:
                    # استخراج زمان پردازش شده برای نمایش به کاربر
                    time_str = line.split('time=')[1].split(' ')[0]
                    self.log(f"⏳ پیشرفت: {time_str}")
                    self.root.update() # بروزرسانی رابط کاربری
            
            process.wait()
            
            if process.returncode == 0:
                self.log("✅ زیرنویس با موفقیت چسبانده شد")
                return output_file
            else:
                raise Exception("FFmpeg با کد خطا بسته شد. لاگ را بررسی کنید.")
                
        except Exception as e:
            raise Exception(f"خطا در چسباندن زیرنویس: {str(e)}")
    
    def hex_to_rgb(self, hex_color):
        """تبدیل رنگ HEX به RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def main():
    """تابع اصلی"""
    root = tk.Tk()
    app = PersianSubtitleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
