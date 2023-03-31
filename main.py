import evdev
import keyboard
import subprocess


def get_touchpad_id():
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


TOUCHPAD_DEVICE_ID = get_touchpad_id()  # 触摸板设备的 ID
ENABLE_TOUCHPAD = True

if TOUCHPAD_DEVICE_ID is None:
    print("Touchpad device not found")
    sys.exist(-1)


def toggle_touchpad():
    global TOUCHPAD_DEVICE_ID, ENABLE_TOUCHPAD
    ENABLE_TOUCHPAD = not ENABLE_TOUCHPAD
    if ENABLE_TOUCHPAD:
        # 启用触摸板设备
        subprocess.run(["xinput", "enable", str(TOUCHPAD_DEVICE_ID)])
    else:
        # 禁用触摸板设备
        subprocess.run(["xinput", "disable", str(TOUCHPAD_DEVICE_ID)])
    print(ENABLE_TOUCHPAD)


keyboard.add_hotkey("ctrl+shift+alt+n", toggle_touchpad, timeout=3)

# 查找触摸板设备对于的文件路径
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    if "Touchpad" in device.name:
        print("DEBUG find Touchpad", device.name, device.path, device.phys)
        global touchpad
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
    if ENABLE_TOUCHPAD:  # 普通模式就跳过本次循环
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
            keyboard.press_and_release(key)  # 模拟键盘按键按下事件
            isKey = False
            isDone = False
