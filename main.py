import subprocess
import sys

import evdev
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode


KEY_MAP = {
    Key.ctrl_l: "ctrl",
    Key.ctrl_r: "ctrl",
    Key.alt_l: "alt",
    Key.alt_r: "alt",
}


def key_string(key):
    """将按键键码转换为方便对比的字符

    Args:
        key (pynput.keyboard._xorg.KeyCode): 按键键码

    Returns:
        str: 按键对应的字符 或 None
    """
    if isinstance(key, KeyCode):
        key = key.char
    elif isinstance(key, Key):
        key = KEY_MAP.get(key, None)  # 不在表中的返回 None
    return key


class TouchpadAsNumpad:
    def __init__(self):
        self.touchpad_device_id = self.get_touchpad_id()  # 触摸板设备的 ID
        if self.touchpad_device_id is None:
            print("Touchpad device not found")
            sys.exit(-1)
        self.touchpad = self.find_touchpad()
        self.get_abs_range()
        self.enable_touchpad = True  # True 代表触摸板处于普通模式，False代表小键盘模式

        self.isKey = False  # 触摸板是否按下
        self.isDone = False  # 触摸板是否按下并释放
        self.LINE_X = (self.abs_x_max - self.abs_x_min) // 4  # 触摸板划分为四行四列
        self.LINE_Y = (self.abs_y_max - self.abs_y_min) // 4
        self.OUT = [
            ["7", "4", "1", "0"],
            ["8", "5", "2", "0"],
            ["9", "6", "3", "."],
            ["backspace", "+", "-", "enter"],
        ]
        self.keyboard = Controller()  # 初始化键盘控制器
        self.ctrl_pressed = False  # 模式切换快捷键 ctrl 的标志位
        self.alt_pressed = False  # 模式切换快捷键 alt 的标志位
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )  # 设置键盘监听的回调函数
        self.listener.start()  # 启动监听模式切换快捷键
        if not self.enable_touchpad:  # 如果默认是小键盘模式，则要禁用触摸板
            subprocess.run(["xinput", "disable", str(self.touchpad_device_id)])

    def get_touchpad_id(self):
        """
        Get the touchpad device id. If not exist, return None
        """
        # Run the command "xinput list" and capture the output
        output = subprocess.check_output(["xinput", "list"]).decode("utf-8")

        # Split the output by lines
        lines = output.split("\n")

        # Loop through each line
        for line in lines:
            # If the line contains "TouchPad", extract the ID and return -1
            if "TouchPad" in line or "Touchpad" in line:
                return line.split("id=")[1].split("\t")[0]
        return None

    def toggle_touchpad(self):
        self.enable_touchpad = not self.enable_touchpad
        if self.enable_touchpad:
            # 启用触摸板设备
            subprocess.run(["xinput", "enable", str(self.touchpad_device_id)])
            # 通知用户模式切换方式
            subprocess.Popen(
                ["notify-send", "Touchpad enable", "use ctrl+alt+n to turn to numpad"]
            )
        else:
            # 禁用触摸板设备
            subprocess.run(["xinput", "disable", str(self.touchpad_device_id)])
            subprocess.Popen(
                ["notify-send", "Numpad enable", "use ctrl+alt+n to enable Touchpad"]
            )
        print(self.enable_touchpad)

    def find_touchpad(self):
        # 查找触摸板设备对于的文件路径，如 /dev/input/event6
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if "Touchpad" in device.name:
                print("DEBUG find Touchpad", device.name, device.path, device.phys)
                touchpad = evdev.InputDevice(device.path)  # Touch Pad 对应文件
                return touchpad
        return None

    def get_abs_range(self):
        # 获取坐标轴的范围
        abs = self.touchpad.capabilities()[3]
        self.abs_x_min, self.abs_x_max = 0, 0
        self.abs_y_min, self.abs_y_max = 0, 0
        for k, v in abs:
            if k == 53:
                self.abs_x_min, self.abs_x_max = v.min, v.max
            elif k == 54:
                self.abs_y_min, self.abs_y_max = v.min, v.max
        print(
            "x in [%d, %d], y in [%d, %d]"
            % (self.abs_x_min, self.abs_x_max, self.abs_y_min, self.abs_y_max)
        )

    def run(self):
        try:
            for e in self.touchpad.read_loop():
                if self.enable_touchpad:  # 普通模式就跳过本次循环
                    continue
                # 获取触摸坐标
                if e.type == 3:  # EV_ABS
                    if e.code == 0:  # ABS_X
                        self.absx = e.value
                        # print("update ABS_X:%d"%absx)
                    elif e.code == 1:  # ABS_Y
                        self.absy = e.value
                        # print("update ABS_Y:%d"%absy)
                elif e.type == 1:  # EV_KEY
                    # print("EV_KEY",e)    # 330 BTN_TOUCH    325 BTN_TOOL_FINGER
                    if e.code == 330:
                        if e.value == 1:
                            self.isKey = True
                        elif e.value == 0 and self.isKey:
                            self.isDone = True
                elif e.type == 0:  # EV_SYN
                    # print("EV_SYN",e)
                    # 根据坐标所在区域输出对应的内容
                    if self.isDone:
                        x, y = self.absx // self.LINE_X, self.absy // self.LINE_Y
                        if x >= 4:
                            x = x - 1
                        if y >= 4:
                            y = y - 1
                        key = self.OUT[x][y]
                        print(key)
                        # 模拟键盘按键按下事件
                        if key == "backspace":  # 特殊按键
                            self.keyboard.press(Key.backspace)
                            self.keyboard.release(Key.backspace)
                        elif key == "enter":
                            self.keyboard.press(Key.enter)
                            self.keyboard.release(Key.enter)
                        else:
                            self.keyboard.press(key)
                        self.isKey = False
                        self.isDone = False
        except Exception as e:
            print("debug", e)
        finally:
            if not self.enable_touchpad:  # disable touchpad when exit. enable it
                self.toggle_touchpad()

    def on_press(self, key):
        """
        键盘按下回调事件，若 ctrl+alt+n 同时按下，则调用 toggle_touchpad 进行模式切换

        key: 按键对应键码
        """
        key = key_string(key)
        if key and key == "ctrl":
            self.ctrl_pressed = True
        elif key and key == "alt":
            self.alt_pressed = True
        elif key and key == "n" and self.ctrl_pressed and self.alt_pressed:
            self.toggle_touchpad()

    def on_release(self, key):
        """
        键盘抬起回调事件，清除快捷键的标志位
        """
        key = key_string(key)
        if key and key == "ctrl":
            self.ctrl_pressed = False
        elif key and key == "alt":
            self.alt_pressed = False


if __name__ == "__main__":
    touchpad_as_numpad = TouchpadAsNumpad()
    touchpad_as_numpad.run()