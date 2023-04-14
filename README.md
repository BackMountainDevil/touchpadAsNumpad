# 触摸板当作数字小键盘

这python代码的作用是使笔记本的触摸板当作数字小键盘，即触摸板从移动光标模式切换为数字小键盘模式之后，这个代码监听用户触摸的位置，然后模拟对应的键盘事件

## dev info

- Python 3.8.13
- evdev 1.6.1
- keyboard 0.13.5
- device: Lenovo XiaoXinPro-13ARE 2020 Laptop

## 布局

```
7 8 9 backspace
4 5 6 +
1 2 3 -
0 0 . enter
```

简单编码为，实际是其转置矩阵

```python
OUT = [
    [7, 8, 9, "backspace", "backspace"],
    [4, 5, 6, "+", "+"],
    [1, 2, 3, "-", "-"],
    [0, 0, ".", "enter", "enter"],
]
```

第四列是第三列的重复，因为测试发现`absx // ((ABS_X_MAX - ABS_X_MIN) // 4)` 时在触摸板边缘可以取到 4,本想者取值范围 [0,3],结果边缘是 4, 简单cv下即可

然后因为 keyboard 的原因，数字要使用字符形式，不然会被识别为键码，`+` 也要替换为 `shift+=`，相当于按下两个按键来表示`+`，不然会得到`=`

# 模式切换

切换快捷键组合：ctrl+shift+alt+n

普通模式和数字小键盘模式：触摸板正常工作即为普通模式，当在程序里切换为数字小键盘之后，系统不再相应移动光标和单击，直到切换回普通模式

`xinput list` 可以获取到触摸板设备的id，`xinput list-props device` 可以获取到设备有哪些属性和对应的编号。根据前面两条指令可以得到“Device Enabled (162)”，`xinput set-prop 14 162 0`的意思是把设备14（因设备而异，我的触控板ID是14），162就是前面得到的属性，0就是关闭这个属性（1是开启），实测表明：关闭该属性不能移动鼠标，按钮无效、滚动无效，但是可以响应多指事件。

# 通知

QSystemTrayIcon 可以发送通知，结合 QMenu 还可以加一个退出按钮，但是和代码结果起来效果就变了。copilot 还给刘个建议是 `from gi.repository import Notify`。搜索引擎得到一个 `subprocess.Popen(['notify-send', summary, body])`，效果正好，但是用root运行就变的异常了。

# Refer

[How do I send text messages to the notification bubbles? 2012](https://askubuntu.com/questions/108764/how-do-i-send-text-messages-to-the-notification-bubbles)
