from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import logging
from dotenv import load_dotenv

load_dotenv()


class BrowserManager:
    def __init__(self):
        self.browser = None

    def init_browser(self):
        """初始化浏览器"""
        co = self._get_browser_options()
        # self.browser = Chromium(co)
        self.browser = self.connect_to_chrome()
        return self.browser

    def _get_browser_options(self):
        """获取浏览器配置"""
        co = ChromiumOptions()
        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
        except FileNotFoundError as e:
            logging.warning(f"警告: {e}")

        co.set_user_agent(
            os.getenv('BROWSER_USER_AGENT', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36")
        )
        co.set_pref("credentials_enable_service", False)
        co.set_argument("--hide-crash-restore-bubble")
        proxy = os.getenv('BROWSER_PROXY')
        if proxy:
            co.set_proxy(proxy)
        
        co.auto_port()
        co.headless(os.getenv('BROWSER_HEADLESS', 'True').lower() == 'true')  # 生产环境使用无头模式

        # 设置用户数据目录
        user_data_dir = r"C:\Users\admin\AppData\Local\Google\Chrome\User Data"
        co.set_user_data_path(user_data_dir)

        # Mac 系统特殊处理
        if sys.platform == "darwin":
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co

    def _get_extension_path(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "turnstilePatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path

    def quit(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
    def find_chrome_path(self):
        """自动查找Chrome浏览器路径"""
        # Windows系统常见的Chrome安装路径
        windows_paths = [
            os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'),
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
        ]
        
        # 遍历可能的路径
        for path in windows_paths:
            if os.path.exists(path):
                return path
                
        # 如果上述路径都不存在，尝试通过注册表查找
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
            chrome_path = winreg.QueryValue(key, None)
            if os.path.exists(chrome_path):
                return chrome_path
        except:
            pass
        
        return None

    def connect_to_chrome(self, port=9222):
        """连接到已运行的Chrome或启动新实例"""
        try:
            # 尝试连接到已运行的Chrome
            co = ChromiumOptions()
            co.set_local_port(port)  # 设置本地端口
            browser = Chromium(co)
            print("成功连接到现有Chrome实例")
            return browser
        except:
            # 如果连接失败，启动新的Chrome实例
            chrome_path = self.find_chrome_path()
            if not chrome_path:
                raise Exception("未找到Chrome浏览器，请确认已安装Chrome")
            
            # 通过命令行启动Chrome
            import subprocess
            cmd = f'"{chrome_path}" --remote-debugging-port={port} --user-data-dir="./chrome_debug_profile"'
            subprocess.Popen(cmd, shell=True)
            
            # 等待Chrome启动并尝试连接
            import time
            for _ in range(5):  # 最多尝试5次
                try:
                    time.sleep(2)  # 等待2秒
                    co = ChromiumOptions()
                    co.set_local_port(port)  # 设置本地端口
                    browser = Chromium(co)
                    print(f"Chrome已启动并连接成功，调试端口：{port}")
                    return browser
                except Exception as e:
                    print(f"连接尝试失败: {str(e)}")
                    continue
                
            raise Exception("无法连接到Chrome，请检查Chrome是否正常启动")
