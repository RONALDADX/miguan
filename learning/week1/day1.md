# 第1天学习笔记 - 环境检查和Python入门

**日期：** 2025-03-28
**学习时长：** 60分钟

## 📝 今日学习内容

### 1. 环境检查结果
- ✅ Python 3.6.8 已安装
- ✅ Git 2.43.5 已安装并配置
- ✅ 基础开发工具齐全
- ✅ 磁盘空间充足 (71GB可用)

### 2. Python基础语法学习

#### 2.1 第一个Python程序
```python
# hello.py
print("Hello, 蜜罐!")
print("欢迎来到编程世界")
```

运行结果：
```
Hello, 蜜罐!
欢迎来到编程世界
```

#### 2.2 变量和数据类型
```python
# 变量定义
name = "Ronald"      # 字符串
age = 30             # 整数
height = 1.75        # 浮点数
is_learning = True   # 布尔值

# 打印变量
print(f"姓名: {name}")
print(f"年龄: {age}")
print(f"身高: {height}米")
print(f"正在学习: {is_learning}")
```

#### 2.3 基本运算
```python
# 数学运算
a = 10
b = 3

print(f"加法: {a} + {b} = {a + b}")
print(f"减法: {a} - {b} = {a - b}")
print(f"乘法: {a} × {b} = {a * b}")
print(f"除法: {a} ÷ {b} = {a / b}")
print(f"整除: {a} // {b} = {a // b}")
print(f"取余: {a} % {b} = {a % b}")
```

### 3. Git基础命令实践

#### 3.1 查看当前状态
```bash
git status
```

#### 3.2 添加学习笔记
```bash
git add learning/week1/day1.md
```

#### 3.3 提交更改
```bash
git commit -m "添加第1天学习笔记：环境检查和Python基础"
```

### 4. 遇到的问题和解决方案

#### 问题1：Python版本较旧
- **现状：** Python 3.6.8 (2018年发布)
- **建议：** 暂时使用，后续可升级到Python 3.10+

#### 问题2：Flask未安装
- **解决方案：** 需要时再安装
```bash
pip3 install flask
```

### 5. 学习心得
1. **环境搭建是第一步** - 检查工具是否齐全很重要
2. **从简单开始** - 先写`print("Hello")`，再逐步深入
3. **及时记录** - 写笔记帮助理解和记忆

### 6. 明日计划
- [ ] 学习Python条件语句 (if/else)
- [ ] 学习Python循环 (for/while)
- [ ] 完成第一个小练习：判断奇偶数
- [ ] 学习Git分支基础

## 💡 今日收获
1. 了解了当前编程环境的完整状态
2. 学会了Python基础语法：变量、打印、运算
3. 实践了Git的基本工作流程
4. 建立了学习笔记系统

---

**学习编程就像挖蜜罐，今天挖了第一铲！** 🍯

*明日继续...*