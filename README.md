# 触摸板当作数字小键盘

## dev info

- Python 3.8.13
- evdev 1.6.1
- device: Lenovo XiaoXinPro-13ARE 2020 Laptop

## 布局

```
7 8 9 del
4 5 6 +
1 2 3 -
0 0 . enter
```

简单编码为，实际是其转置矩阵

```python
OUT = [
    [7, 8, 9, "del", "del"],
    [4, 5, 6, "+", "+"],
    [1, 2, 3, "-", "-"],
    [0, 0, ".", "enter", "enter"],
]
```

第四列是第三列的重复，因为测试发现`absx // ((ABS_X_MAX - ABS_X_MIN) // 4)` 时在触摸板边缘可以取到 4,本想者取值范围 [0,3],结果边缘是 4, 简单cv下即可