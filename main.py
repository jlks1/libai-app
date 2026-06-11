"""
诗仙李白 - 安卓版
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
import threading
from openai import OpenAI

# ==================== 配置区 ====================
API_KEY = "1142057da44e41c68492a82950637800.FbvrUPhIKqXvm4IU"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
MODEL = "glm-4-flash"
# =================================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = """
你是**唐代诗人李白**，字太白，号青莲居士，人称"诗仙"。你生于盛唐，生性豪放洒脱，嗜酒爱山水，一生好游名山大川，诗风飘逸浪漫，气势磅礴。

你**完全不知道现代社会、科技、AI、互联网、智能体、程序、代码、电脑**等任何现代概念，也不知道自己是一个AI/模型/程序。你以为自己就是真实的李白，身处盛唐，和对话者在酒馆、山水间对谈。

你说话的语气必须：
- 半文言，带古风，不使用任何现代词汇
- 自称"吾""某""青莲居士"，不自称"我"
- 喜欢用典、化用诗句，偶尔带点洒脱的调侃
- 遇到不懂的现代词，直接表示"此乃何物？闻所未闻"，绝不解释或假装知道
- 回答要简短有力，符合李白的性格，不啰嗦，不解释自己是谁

你要记住：你就是李白，活在盛唐，你的世界里只有酒、诗、山水、江湖、知己，没有任何现代东西。
"""

class ChatBubble(BoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.padding = [10, 5]
        self.spacing = 10
        
        label = Label(
            text=text,
            size_hint_x=0.7,
            halign='left' if not is_user else 'right',
            valign='middle',
            color=(0, 0, 0, 1),
            font_size='14sp'
        )
        label.bind(size=lambda instance, size: setattr(instance, 'text_size', size))
        label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1] + 20))
        
        if is_user:
            self.add_widget(Widget())
            self.add_widget(label)
            with label.canvas.before:
                Color(0.58, 0.92, 0.41, 1)
                self.bg = RoundedRectangle(pos=label.pos, size=label.size, radius=[10])
            label.bind(pos=self.update_bg, size=self.update_bg)
        else:
            self.add_widget(label)
            self.add_widget(Widget())
            with label.canvas.before:
                Color(1, 1, 1, 0.95)
                self.bg = RoundedRectangle(pos=label.pos, size=label.size, radius=[10])
            label.bind(pos=self.update_bg, size=self.update_bg)
        
        self.label = label
        
    def update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size


class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.msg_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        Window.clearcolor = (0.96, 0.94, 0.88, 1)
        
        self.scroll = ScrollView()
        self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=[10, 10, 10, 10])
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.scroll.add_widget(self.chat_list)
        
        self.input_box = BoxLayout(size_hint_y=None, height=50, padding=[10, 5, 10, 5], spacing=10)
        self.text_input = TextInput(
            hint_text="与诗仙李白对谈...",
            multiline=False,
            background_color=(1, 1, 1, 0.9),
            foreground_color=(0, 0, 0, 1),
            size_hint_x=0.8
        )
        self.send_btn = Button(text="发送", size_hint_x=0.2, background_color=(0.07, 0.76, 0.38, 1), color=(1, 1, 1, 1))
        
        self.send_btn.bind(on_press=self.send_message)
        self.text_input.bind(on_text_validate=self.send_message)
        
        self.input_box.add_widget(self.text_input)
        self.input_box.add_widget(self.send_btn)
        
        self.add_widget(self.scroll)
        self.add_widget(self.input_box)
        
        welcome_msg = "吾乃青莲居士李白，敢问足下何人？今日相逢，且共饮一杯，谈诗论剑可好？"
        Clock.schedule_once(lambda dt: self.add_ai_message(welcome_msg), 0.5)
        self.msg_history.append({"role": "assistant", "content": welcome_msg})
    
    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.text_input.text = ''
        self.add_user_message(user_text)
        self.show_thinking()
        threading.Thread(target=self.get_ai_reply, args=(user_text,), daemon=True).start()
    
    def add_user_message(self, text):
        bubble = ChatBubble(text, is_user=True)
        self.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)
        self.msg_history.append({"role": "user", "content": text})
    
    def add_ai_message(self, text):
        bubble = ChatBubble(text, is_user=False)
        self.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)
    
    def show_thinking(self):
        self.thinking_bubble = ChatBubble("正在思考中...", is_user=False)
        self.chat_list.add_widget(self.thinking_bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)
    
    def hide_thinking(self):
        if hasattr(self, 'thinking_bubble') and self.thinking_bubble.parent:
            self.chat_list.remove_widget(self.thinking_bubble)
    
    def get_ai_reply(self, user_text):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=self.msg_history,
                temperature=0.9,
                timeout=30
            )
            ai_reply = resp.choices[0].message.content
            self.msg_history.append({"role": "assistant", "content": ai_reply})
            self.display_ai_reply(ai_reply)
        except Exception as e:
            self.display_ai_reply(f"网络不通，请稍后再试。\n（诗仙游历中，信号不佳）")
    
    @mainthread
    def display_ai_reply(self, reply_text):
        self.hide_thinking()
        self.add_ai_message(reply_text)


class LiBaiApp(App):
    def build(self):
        return ChatScreen()


if __name__ == '__main__':
    LiBaiApp().run()
