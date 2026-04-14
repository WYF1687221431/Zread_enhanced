# zread_enhanced

**API Documentation Auto-Generator for Any Project**

[English](./README.md) | [中文](./README_zh.md)

Built on [zread CLI](https://github.com/ZreadAI/zread-skill) and [zread skill](https://github.com/ZreadAI/zread-skill) — generate beautiful API docs with zero configuration.

---

## What is This

zread_enhanced automatically scans your source code and generates API documentation. Just point it at your project directory and get professional docs without any setup.

**How it works:**
```
zread generate        → Creates base Wiki structure
    ↓
zread_enhanced        → Scans code, identifies APIs, generates docs
    ↓
zread browse          → View your API documentation
```

---

## Features

- **Zero Config** — No library lists or API definitions needed. Point to your source and go.
- **Multi-Language** — C++, Python, JavaScript, TypeScript, Java, Go, Rust, and more.
- **Zero-Cost Cache** — Already-documented APIs are cached. Re-runs skip LLM calls entirely, saving tokens.
- **Offline Mode** — Works without API keys using pure regex mode.
- **Call Tracking** — See where each API is used in your codebase.

---

## Quick Start

### Prerequisites

- [zread CLI](https://github.com/ZreadAI/zread-skill) installed
- Python 3.8+

### Usage

```bash
# Run the complete workflow in one step
.\zread-generate.ps1 -src-dir ./your-project

# Then view your docs
zread browse
```

### Manual Steps (alternative)

```bash
# 1. Generate base Wiki
zread generate -y

# 2. Run API enhancement (specify your source directory)
python api-enhance.py --src-dir ./your-project

# 3. View your docs
zread browse
```

### Options

```bash
-src-dir DIR        Source directory to scan (required)
-project-name NAME  Project name for tracking
-no-llm            Offline mode (pure regex, no API key needed)
```

---

## Example

Input code:
```cpp
cv::imread("photo.jpg");
pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
```

Output docs:
```
cv::imread
  → OpenCV image reading function
  → Used in: src/Tracking.cc#42, src/Visualization.cc#18

pcl::PointCloud
  → PCL point cloud data structure
  → Used in: src/CloudProcessing.cc#15
```

---

## How It Fits Together

```
Your Project
    │
    ├── zread generate (creates wiki structure)
    │
    ├── zread_enhanced (scans & documents APIs)
    │       ├── Fast: Regex pattern matching
    │       └── Accurate: AI-powered verification
    │
    └── zread browse (view beautiful docs)
```

---

## License

MIT
