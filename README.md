# zread_enhanced

**适用于任意项目的 API 文档自动生成工具**

基于 [zread CLI](https://github.com/ZreadAI/zread-skill) 和 [zread skill](https://github.com/ZreadAI/zread-skill) 构建 — 零配置生成专业 API 文档。

[English](./Zread_enhanced/README.md) | 中文

---

## 这是什么

zread_enhanced 可以自动扫描你的源代码并生成 API 文档。只需指向项目目录，无需任何配置即可获得专业文档。

**工作流程：**
```
zread generate        → 创建基础 Wiki 结构
    ↓
zread_enhanced        → 扫描代码、识别 API、生成文档
    ↓
zread browse          → 查看你的 API 文档
```

---

## 核心特性

- **零配置** — 无需库列表或 API 定义。指向源码目录即可。
- **多语言支持** — C++、Python、JavaScript、TypeScript、Java、Go、Rust 等。
- **零成本缓存** — 已生成说明的 API 会缓存到本地。重复运行时直接命中缓存，不再调用 LLM，节省 token。
- **离线模式** — 纯正则模式，无需 API 密钥。
- **调用追踪** — 查看每个 API 在代码中的使用位置。

---

## 快速开始

### 前提条件

- 已安装 [zread CLI](https://github.com/ZreadAI/zread-skill)
- Python 3.8+

### 使用方法

首先进入你要生成文档的项目目录：

```bash
# 进入你的项目目录
cd your-project

# 一键运行完整工作流（指定源码目录）
.\path\to\zread-generate.ps1 -src-dir ./src

# 然后查看文档
zread browse
```

### 手动分步执行（备选）

```bash
# 1. 生成基础 Wiki
zread generate -y

# 2. 运行 API 增强（指定要扫描的源码目录）
python api-enhance.py --src-dir ./your-project

# 3. 查看文档
zread browse
```

### 参数选项

```bash
-src-dir DIR        要扫描的源码目录（必填）
-project-name NAME  项目名称（用于追踪）
-no-llm            离线模式（纯正则，无需 API 密钥）
```

---

## 示例

输入代码：
```cpp
cv::imread("photo.jpg");
pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
```

输出文档：
```
cv::imread
  → OpenCV 图像读取函数
  → 使用位置: src/Tracking.cc#42, src/Visualization.cc#18

pcl::PointCloud
  → PCL 点云数据结构
  → 使用位置: src/CloudProcessing.cc#15
```

---

## 组合使用

```
你的项目
    │
    ├── zread generate（创建 wiki 结构）
    │
    ├── zread_enhanced（扫描并生成文档）
    │       ├── 快速：正则模式匹配
    │       └── 准确：AI 驱动验证
    │
    └── zread browse（查看精美文档）
```

---

## License

MIT
