import evdev
import keyboard
import subprocess

TOUCHPAD_DEVICE_ID = 14 # 触摸板设备的 ID

ENABLE_TOUCHPAD=True
def dis_en_touchpad():
    global ENABLE_TOUCHPAD
    ENABLE_TOUCHPAD=not ENABLE_TOUCHPAD
    if ENABLE_TOUCHPAD:
        # 启用触摸板设备
        subprocess.run(["xinput", "set-prop", str(TOUCHPAD_DEVICE_ID), "Device Enabled", "1"])
    else:
        # 禁用触摸板设备
        subprocess.run(["xinput", "set-prop", str(TOUCHPAD_DEVICE_ID), "Device Enabled", "0"]) 
    print(ENABLE_TOUCHPAD)
keyboard.add_hotkey('ctrl+shift+alt+n', dis_en_touchpad,timeout=3)

# 查找触摸板设备对于的文件路径
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    if "Touchpad" in device.name:
        print("DEBUG find Touchpad", device.name, device.path, device.phys)
        touchpad = evdev.InputDevice(device.path)  # Touch Pad 对应文件
        break
# 获取坐标轴的范围
abs = touchpad.capabilities()[3]
ABS_X_MIN, ABS_X_MAX = 0, 0
ABS_Y_MIN, ABS_Y_MAX = 0, 0
for k, v in abs:
    if k == 53:
        ABS_X_MIN, ABS_X_MAX = v.min, v.max
    elif k == 54:
        ABS_Y_MIN, ABS_Y_MAX = v.min, v.max
print("x in [%d, %d], y in [%d, %d]" % (ABS_X_MIN, ABS_X_MAX, ABS_Y_MIN, ABS_Y_MAX))


x, y, absx, absy = 0, 0, 0, 0
isKey = False
isDone = False
LINE_X = (ABS_X_MAX - ABS_X_MIN) // 4
LINE_Y = (ABS_Y_MAX - ABS_Y_MIN) // 4
OUT = [
    ["7", "4", "1", "0"],
    ["8", "5", "2", "0"],
    ["9", "6", "3", "."],
    ["backspace", "shift+=", "-", "enter"],
    ["backspace", "shift+=", "-", "enter"],
]

for e in touchpad.read_loop():
    if ENABLE_TOUCHPAD: # 普通模式就跳过本次循环
        continue
    # 获取触摸坐标
    if e.type == 3:  # EV_ABS
        if e.code == 0:  # ABS_X
            absx = e.value
            # print("update ABS_X:%d"%absx)
        elif e.code == 1:  # ABS_Y
            absy = e.value
            # print("update ABS_Y:%d"%absy)
        else:
            pass  # such as 47, 57
    elif e.type == 1:  # EV_KEY
        # print("EV_KEY",e)    # 330 BTN_TOUCH    325 BTN_TOOL_FINGER
        if e.code == 330:
            if e.value == 1:
                isKey = True
            elif e.value == 0 and isKey:
                isDone = True
    elif e.type == 0:  # EV_SYN
        # print("EV_SYN",e)
        # 根据坐标所在区域输出对应的内容
        if isDone:
            key = OUT[absx // LINE_X][absy // LINE_Y]
            print(key)
            keyboard.press_and_release(key) # 模拟键盘按键按下事件
            isKey = False
            isDone = False
