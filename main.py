from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
import socket
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import requests

# ============ 卡密 & 时间配置区（自行修改） ============
VALID_KEY = "ABC123456"
EXPIRE_TIME = datetime(2026, 9, 20, 0, 0, 0)
# ======================================================

# 内置两组域名库
domain_dict = {
    "百青藤(百度)": [
        "als.baidu.com",
        "www.baidu.com",
        "nadvideo.baidu.com",
        "nadvideo2.baidu.com",
        "cpu-openapi.baidu.com",
        "wn.pos.baidu.com",
        "mobads-logs.baidu.com",
        "mobads.baidu.com"
    ],
    "穿山甲(字节)": [
        "pangolin.bytedance.com",
        "ttadpub.bytedance.com",
        "api.pangolin-sdk-toutiao.com",
        "ad.toutiao.com",
        "p3-adx-sign.byteimg.com",
        "ttlivecdn.com",
        "byteimg.com",
        "snssdk.com"
    ]
}

def get_my_public_ip():
    ip_urls = [
        "http://api.ipify.org",
        "http://icanhazip.com",
    ]
    for url in ip_urls:
        try:
            resp = requests.get(url, timeout=2.5)
            ip = resp.text.strip()
            if ip:
                return ip
        except Exception:
            continue
    return "获取失败(网络无法访问IP查询服务)"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "获取失败"

def is_cgnat_ip(ip_str):
    try:
        parts = list(map(int, ip_str.split('.')))
        if len(parts) !=4:
            return False
        first, second = parts[0], parts[1]
        if first == 100 and 64 <= second <=127:
            return True
        return False
    except:
        return False

def resolve_ipv4(host):
    addrinfo = socket.getaddrinfo(host, None, family=socket.AF_INET)
    return addrinfo[0][4][0]

def ping_icmp_ipv4(ip_addr, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        res = sock.connect_ex((ip_addr, 80))
        sock.close()
        return res == 0
    except Exception:
        return False

def check_tcp_port(ip, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        res = sock.connect_ex((ip, port))
        sock.close()
        return res == 0
    except:
        return False

# 登录页面
class LoginPage(BoxLayout):
    def __init__(self, switch_page, **kwargs):
        super().__init__(**kwargs)
        self.switch_page = switch_page
        self.orientation = "vertical"
        self.spacing = 30
        self.padding = 60

        self.add_widget(Label(text="请输入卡密", font_size=32, size_hint_y=0.2))
        self.key_input = TextInput(hint_text="卡密", password=True, font_size=22, size_hint_y=0.15)
        self.add_widget(self.key_input)
        login_btn = Button(text="登录", font_size=22, size_hint_y=0.15, background_color=(0.1,0.4,0.8,1))
        login_btn.bind(on_press=self.check_key)
        self.add_widget(login_btn)

    def check_key(self, instance):
        input_key = self.key_input.text.strip()
        now_time = datetime.now()
        if now_time > EXPIRE_TIME:
            self.key_input.text = "卡密已过期！"
            return
        if input_key == VALID_KEY:
            self.switch_page("main")
        else:
            self.key_input.text = "卡密错误！"

# 主检测页面
class MainPage(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing=10
        self.padding=10
        self.is_running = False

        top_layout = BoxLayout(size_hint_y=0.1)
        top_layout.add_widget(Label(text="广告平台："))
        self.platform_spinner = Spinner(text="穿山甲(字节)", values=list(domain_dict.keys()))
        top_layout.add_widget(self.platform_spinner)
        self.add_widget(top_layout)

        check_layout = BoxLayout(size_hint_y=0.15)
        self.usb_debug = CheckBox()
        check_layout.add_widget(Label(text="USB调试"))
        check_layout.add_widget(self.usb_debug)

        self.access = CheckBox()
        check_layout.add_widget(Label(text="无障碍"))
        check_layout.add_widget(self.access)

        self.dev_opt = CheckBox()
        check_layout.add_widget(Label(text="开发者选项"))
        check_layout.add_widget(self.dev_opt)
        self.add_widget(check_layout)

        check_layout2 = BoxLayout(size_hint_y=0.15)
        self.mock_loc = CheckBox()
        check_layout2.add_widget(Label(text="模拟位置"))
        check_layout2.add_widget(self.mock_loc)

        self.multi = CheckBox()
        check_layout2.add_widget(Label(text="多改机"))
        check_layout2.add_widget(self.multi)
        self.add_widget(check_layout2)

        self.run_btn = Button(text="开始检测", size_hint_y=0.12, background_color=(0.1,0.4,0.8,1))
        self.run_btn.bind(on_press=self.start_check_thread)
        self.add_widget(self.run_btn)

        scroll = ScrollView(size_hint_y=0.48)
        self.log_text = Label(text="日志输出区域", font_size=14, size_hint_y=None)
        self.log_text.bind(texture_size=self.log_text.setter('size'))
        scroll.add_widget(self.log_text)
        self.scroll_view = scroll
        self.add_widget(scroll)

    def set_log(self, text):
        def _dt(x):
            self.log_text.text = text
            self.scroll_view.scroll_y = 0
        Clock.schedule_once(_dt,0)

    def set_btn_state(self, running:bool):
        def _dt(x):
            if running:
                self.run_btn.text = "正在检查…"
                self.run_btn.disabled = True
            else:
                self.run_btn.text = "开始检测"
                self.run_btn.disabled = False
        Clock.schedule_once(_dt,0)

    def start_check_thread(self, instance):
        if self.is_running:
            return
        self.is_running = True
        self.set_btn_state(True)
        t = threading.Thread(target=self.run_check, daemon=True)
        t.start()

    def _check_one_domain(self, domain):
        log_seg = f"【域名】{domain}\n"
        icmp_ok = False
        tcp443_ok = False
        http80_ok = False
        https443_ok = False
        resolve_fail = False
        try:
            ip = resolve_ipv4(domain)
            icmp_ok = ping_icmp_ipv4(ip, timeout=1)
            tcp443_ok = check_tcp_port(ip,443,1)
            http80_ok = check_tcp_port(ip,80,1)
            https443_ok = check_tcp_port(ip,443,1)

            log_seg += f"IPv4:{ip}\n"
            log_seg += "✅ICMP Ping：正常\n" if icmp_ok else "❌ICMP Ping：不通\n"
            log_seg += "✅ TCP(443)握手连通\n" if tcp443_ok else "❌ TCP(443)握手失败\n"
            log_seg += "✅ HTTP(80)端口连通\n" if http80_ok else "❌ HTTP(80)端口不通\n"
            log_seg += "✅ HTTPS(443)端口连通\n" if https443_ok else "❌ HTTPS(443)端口不通\n"
        except Exception:
            log_seg += "❌IPv4解析失败\n"
            resolve_fail = True
        log_seg += "----------------------------------------\n\n"
        return {
            "seg":log_seg,
            "icmp_ok":icmp_ok,
            "tcp443_ok":tcp443_ok,
            "http80_ok":http80_ok,
            "https443_ok":https443_ok,
            "resolve_fail":resolve_fail
        }

    def run_check(self):
        start_time = time.time()
        platform = self.platform_spinner.text
        log = "===== 广告SDK网络环境检测系统 =====\n\n"

        my_public_ip = get_my_public_ip()
        my_local_ip = get_local_ip()
        log += f"📶 当前本机出口公网IP：{my_public_ip}\n"
        log += f"📱 本机局域网IP：{my_local_ip}\n"

        if my_public_ip != "获取失败(网络无法访问IP查询服务)":
            if is_cgnat_ip(my_public_ip):
                log += "⚠️ 【警告】当前线路为CGNAT共享IP，多用户共用出口IP，存在风控关联风险！\n"
            else:
                log += "✅ 【IP类型】公网独立IP，无CGNAT共享风险\n"

        log += "----------------------------------------\n\n"
        domain_list = domain_dict[platform]

        fail_icmp_count = 0
        fail_tcp_count = 0
        fail_http_count = 0
        fail_https_count = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._check_one_domain, d) for d in domain_list]
            for fu in as_completed(futures):
                try:
                    res = fu.result(timeout=8)
                    log += res["seg"]
                    if not res["icmp_ok"]: fail_icmp_count +=1
                    if not res["tcp443_ok"]: fail_tcp_count +=1
                    if not res["http80_ok"]: fail_http_count +=1
                    if not res["https443_ok"]: fail_https_count +=1
                except TimeoutError:
                    log += "⚠️ 任务超时\n----------------------------------------\n\n"
                except Exception as e:
                    log += f"⚠️ 检测异常:{str(e)}\n----------------------------------------\n\n"
        self.set_log(log)

        total_cost = round(time.time() - start_time,2)
        log += "==================== 汇总结果 ====================\n"
        log += f"检测总耗时：{total_cost} 秒\n"
        log += f"ICMP不通数量：{fail_icmp_count}\n"
        log += f"TCP(443)握手失败数量：{fail_tcp_count}\n"
        log += f"HTTP(80)不通数量：{fail_http_count}\n"
        log += f"HTTPS(443)不通数量：{fail_https_count}\n"

        log += "\n【环境判定报告】\n"
        log += "✅ TCP/HTTP/HTTPS全部连通：网络链路纯净无拦截，广告SDK访问通道正常，无DNS污染、路由劫持。\n"
        log += "❌ TCP握手失败：路由层面阻断连接，广告大概率黑屏、加载卡住、XXs倒计时异常。\n"
        log += "💡 ICMP Ping不通仅为运营商端口屏蔽，不影响广告SDK业务通信，可直接忽略。\n"

        if fail_tcp_count == 0 and fail_https_count ==0:
            log += "\n🔥【网络最终判定】网络环境合格！\n"
        else:
            log += "\n⚠️【网络最终判定】网络环境异常，存在TCP/HTTPS阻断，需排查路由/ DNS！\n"

        risk_count = 0
        if self.usb_debug.active: risk_count +=1
        if self.access.active: risk_count +=1
        if self.dev_opt.active: risk_count +=1
        if self.mock_loc.active: risk_count +=1
        if self.multi.active: risk_count +=1

        log += "\n================ 设备环境风险评估 ================\n"
        log += "【百青藤&穿山甲风控检测项】\n"
        log += f"USB调试：{'☑开启【高风险】' if self.usb_debug.active else '☐关闭【干净】'}\n"
        log += f"无障碍服务：{'☑开启【高风险】' if self.access.active else '☐关闭【干净】'}\n"
        log += f"开发者选项：{'☑开启【中风险】' if self.dev_opt.active else '☐关闭【干净】'}\n"
        log += f"模拟位置：{'☑开启【高风险】' if self.mock_loc.active else '☐关闭【干净】'}\n"
        log += f"多开/改机软件：{'☑已安装【极高风险】' if self.multi.active else '☐未安装【干净】'}\n"
        log += f"\n当前设备风险项总数：{risk_count} 项\n"

        if risk_count == 0:
            log += "🔥【设备判定】设备环境纯净，风控标记风险低！\n"
        elif 1 <= risk_count <=2:
            log += "⚠️【设备判定】存在少量风险项，有概率触发广告风控限流！\n"
        else:
            log += "🚨【设备判定】多项高危特征，极易被风控拦截！\n"

        log += "\n💡说明：以上为广告SDK风控引擎重点采集设备特征。\n"
        log += "开启高危选项，会导致广告加载异常、账号风控。\n"

        self.set_log(log)
        def finish_cb(x):
            self.is_running = False
            self.set_btn_state(False)
        Clock.schedule_once(finish_cb,0)

class RootLayout(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.login_page = LoginPage(switch_page=self.switch)
        self.main_page = MainPage()
        self.add_widget(self.login_page)

    def switch(self, page_name):
        self.clear_widgets()
        if page_name == "main":
            self.add_widget(self.main_page)

class NetCheckApp(App):
    def build(self):
        return RootLayout()

if __name__ == "__main__":
    NetCheckApp().run()
