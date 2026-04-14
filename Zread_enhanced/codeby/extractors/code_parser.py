"""代码解析器：通用 API 调用扫描器"""
import re
from typing import List, Dict, Set


# 通用正则：匹配 xxx::yyy() 或 xxx.yyy() 形式的 API 调用
CPP_PATTERN = re.compile(r'\b(\w+)::(\w+)\s*\(([^)]*)\)')
DOT_PATTERN = re.compile(r'\b(\w+)\.(\w+)\s*\(([^)]*)\)')

# 常见的变量方法名（应被过滤）
KNOWN_VAR_METHODS: Set[str] = {
    # 通用
    'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'index', 'count',
    'sort', 'reverse', 'copy', 'deepcopy',
    'keys', 'values', 'items', 'get', 'set', 'update', 'pop', 'delete',
    'has_key', 'iterkeys', 'itervalues', 'iteritems',
    'add', 'discard', 'union', 'intersection', 'difference',
    'join', 'split', 'strip', 'lstrip', 'rstrip', 'replace', 'format',
    'find', 'rfind', 'index', 'rindex', 'count', 'partition', 'rpartition',
    'startswith', 'endswith', 'isupper', 'islower', 'upper', 'lower', 'capitalize',
    'encode', 'decode', 'format', 'format_map',
    'call', 'apply', 'bind', 'prototype',
    'then', 'catch', 'finally', 'resolve', 'reject',
    'get', 'set', 'has', 'delete', 'forEach', 'map', 'filter', 'reduce',
}

# 已知的 C++ 库名前缀（用于 :: 模式匹配）
KNOWN_CPP_PREFIXES: Set[str] = {
    # C++ 常用库
    'cv', 'pcl', 'Eigen', 'g2o', 'DBoW2', 'boost', 'std', 'torch',
    ' Eigen', 'eigen', 'Sophus', 'sophus',
    # OpenCV 子模块
    'cv2', 'viz', 'aruco', 'bgsegm', 'bioinspired', 'calib3d', 'cuda',
    'dnn', 'features2d', 'flann', 'highgui', 'imgcodecs', 'imgproc',
    'java', 'ml', 'objdetect', 'photo', 'python', 'shape', 'stitching',
    'superres', 'video', 'videoio', 'xobjdetect', 'xphoto',
    # PCL 子模块
    'pcl_compression', 'pcl_conversions', 'pcl_geometry', 'pcl_io',
    'pcl_kdtree', 'pcl_keypoints', 'pcl_ml', 'pcl_octree', 'pcl_people',
    'pcl_recognition', 'pcl_registration', 'pcl_sample_consensus',
    'pcl_search', 'pcl_segmentation', 'pcl_stereo', 'pcl_surface',
    'pcl_tracking', 'pcl_visualization',
    # g2o
    'g2o_core', 'g2o_types_sba', 'g2o_types_slam3d', 'g2o_types_slam2d',
    'g2o solvers', 'g2o stuff',
    # ROS
    'ros', 'roslib', 'rospy', 'roscpp', 'sensor_msgs', 'geometry_msgs',
    'nav_msgs', 'std_msgs', 'trajectory_msgs', 'visualization_msgs',
}

# 已知的 Python/JS 库名前缀（用于 DOT 模式匹配）
KNOWN_LIBRARY_PREFIXES: Set[str] = {
    # Python 常用库
    'cv2', 'np', 'pd', 'plt', 'torch', 'tf', 'keras', 'sklearn', 'scipy',
    'PIL', 'Image', 'io', 'os', 'sys', 'json', 'yaml', 'pickle',
    'threading', 'multiprocessing', 'asyncio', 'aiohttp',
    'requests', 'urllib', 'http', 'flask', 'django', 'fastapi',
    'sqlalchemy', 'psycopg2', 'pymongo', 'redis',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
    'tensorflow', 'torch', 'keras', 'sklearn', 'scipy',
    # JavaScript/TypeScript 常用库和对象
    'console', 'document', 'window', 'Math', 'Array', 'Object', 'String', 'Number',
    'JSON', 'Promise', 'Set', 'Map', 'WeakMap', 'WeakSet',
    'Reflect', 'Proxy', 'Symbol',
    'React', 'Vue', 'Angular', 'jQuery', '$', '$.',
    'express', 'koa', 'http', 'fs', 'path', 'os', 'util', 'events', 'stream',
    'process', 'Buffer', 'setTimeout', 'setInterval',
    'Promise', 'async', 'await', 'fetch', 'axios',
    'Node', 'module', 'exports', 'require',
    'React', 'useState', 'useEffect', 'useRef', 'useCallback',
    # Java 常用
    'System', 'Math', 'Thread', 'String', 'Integer', 'Double',
    'List', 'ArrayList', 'HashMap', 'Map', 'Set', 'Collection',
    'Optional', 'Stream', 'Arrays', 'Objects',
    # Go 常用
    'fmt', 'os', 'io', 'bufio', 'strings', 'strconv', 'time', 'json',
    'errors', 'sync', 'atomic', 'math', 'bytes',
}


class CodeParser:
    """通用 API 调用扫描器，自动识别任意库的 API"""

    def __init__(self):
        pass

    def extract_apis(self, code: str, filename: str = '') -> List[Dict]:
        """从代码字符串提取所有 API 调用"""
        results = []

        # 提取 C++ 风格 xxx::yyy() 的调用
        for match in CPP_PATTERN.finditer(code):
            namespace = match.group(1)  # 如 cv, std, pcl
            func_name = match.group(2)  # 如 imread, resize
            params_str = match.group(3) or ''

            full_name = f"{namespace}::{func_name}"

            # 跳过注释或字符串中的内容
            if self._is_in_comment_or_string(code, match.start()):
                continue
            # 跳过已知类型
            if full_name in KNOWN_TYPES:
                continue
            # C++ 模式：命名空间必须在已知前缀列表中
            if namespace not in KNOWN_CPP_PREFIXES:
                continue
            # 跳过模板内的嵌套（如 pcl::PointCloud<pcl::PointXYZ>）
            if self._is_inside_template(code, match.start()):
                continue
            # 跳过定义/声明（如 void func() 或 class Foo）
            if self._is_declaration(code, match.start()):
                continue

            results.append(self._make_api_entry(
                full_name, namespace, params_str, filename, code, match.start()
            ))

        # 提取 Python/JS 风格 xxx.yyy() 的调用
        for match in DOT_PATTERN.finditer(code):
            lib = match.group(1)  # 如 cv2, np, console
            func_name = match.group(2)  # 如 imread, log
            params_str = match.group(3) or ''

            # 跳过注释或字符串中的内容
            if self._is_in_comment_or_string(code, match.start()):
                continue
            # 跳过已知类型
            if f"{lib}.{func_name}" in KNOWN_TYPES:
                continue
            # 跳过 this.xxx(), self.xxx(), super.xxx() 等方法调用
            if lib in ('this', 'self', 'super', 'cls'):
                continue
            # DOT 模式：库名必须在已知前缀列表中（避免提取 variable.method()）
            if lib not in KNOWN_LIBRARY_PREFIXES:
                continue
            # 跳过常见方法名（虽然罕见，但已知库前缀可能被误用）
            if func_name in KNOWN_VAR_METHODS:
                continue

            results.append(self._make_api_entry(
                f"{lib}.{func_name}", lib, params_str, filename, code, match.start()
            ))

        # 按 (file, line) 排序
        results.sort(key=lambda x: (x['file'], x['line']))
        return results

    def _make_api_entry(self, func: str, library: str, params_str: str,
                        filename: str, code: str, match_start: int) -> Dict:
        """构建 API 条目"""
        line_num = code[:match_start].count('\n') + 1
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        return {
            'func': func,
            'library': library,
            'params': params,
            'params_str': params_str,
            'file': filename,
            'line': line_num,
            'code': f"{func}({params_str})"
        }

    def _is_inside_template(self, code: str, pos: int) -> bool:
        """检查位置是否在模板尖括号内"""
        before = code[:pos]
        last_lt = before.rfind('<')
        last_gt = before.rfind('>')
        return last_lt > last_gt

    def _is_declaration(self, code: str, pos: int) -> bool:
        """检查是否是函数/类声明而非调用"""
        # 往前看一行内的上下文
        line_start = code.rfind('\n', 0, pos) + 1
        line_content = code[line_start:pos]

        # 跳过返回类型声明、类/结构体定义
        skip_keywords = (
            'void ', 'int ', 'float ', 'double ', 'bool ', 'char ',
            'auto ', 'class ', 'struct ', 'enum ', 'typedef ',
            'inline ', 'virtual ', 'static ', 'const ', 'explicit ',
            'template<', 'using ', 'namespace '
        )
        for kw in skip_keywords:
            if kw in line_content:
                return True
        return False

    def _is_in_comment_or_string(self, code: str, pos: int) -> bool:
        """检查位置是否在注释或字符串内"""
        # 单行注释
        line_start = code.rfind('\n', 0, pos) + 1
        line_content = code[line_start:pos]
        if '//' in line_content:
            comment_pos = line_content.find('//')
            # 如果 // 在匹配位置之前，则是注释
            if comment_pos >= 0 and comment_pos < pos - line_start:
                return True

        # 多行注释
        before = code[:pos]
        # 找最后一个开始的多行注释
        last_open = before.rfind('/*')
        last_close = before.rfind('*/')
        if last_open > last_close:
            return True

        # 字符串内的检查（简单的字符串检测）
        # 查找最后一个未转义的引号
        in_string = False
        string_char = None
        i = line_start
        while i < pos:
            c = code[i]
            if in_string:
                if c == '\\' and i + 1 < len(code):
                    i += 2  # 跳过转义字符
                    continue
                if c == string_char:
                    in_string = False
                    string_char = None
            else:
                if c in '"\'':
                    in_string = True
                    string_char = c
            i += 1
        return in_string


# 常见的类型名（非函数调用），排除这些
KNOWN_TYPES: Set[str] = {
    # C++ STL/模板类型
    'std::string', 'std::vector', 'std::map', 'std::set', 'std::unordered_map',
    'std::list', 'std::deque', 'std::stack', 'std::queue', 'std::pair',
    'std::shared_ptr', 'std::unique_ptr', 'std::weak_ptr', 'std::make_shared',
    'std::make_pair', 'std::tuple', 'std::array',
    # OpenCV 类型
    'cv::Mat', 'cv::Size', 'cv::Point', 'cv::Point2f', 'cv::Point3f',
    'cv::Rect', 'cv::Scalar', 'cv::Vec', 'cv::Vec2f', 'cv::Vec3b',
    'cv::Range', 'cv::String', 'cv::FileStorage', 'cv::FileNode',
    'cv::DMatch', 'cv::KeyPoint', 'cv::DescriptorMatcher',
    # PCL 类型
    'pcl::PointCloud', 'pcl::PointXYZ', 'pcl::PointXYZRGBA', 'pcl::PointXYZI',
    'pcl::PointNormal', 'pcl::PointSurfel', 'pcl::PCDReader', 'pcl::PCDWriter',
    'pcl::PassThrough', 'pcl::VoxelGrid', 'pcl::StatisticalOutlierRemoval',
    # Eigen 类型
    'Eigen::Matrix', 'Eigen::Vector', 'Eigen::Map', 'Eigen::Quaternion',
    'Eigen::AngleAxis', 'Eigen::Translation', 'Eigen::Transform',
    # g2o 类型
    'g2o::VertexSE3', 'g2o::EdgeSE3', 'g2o::OptimizableGraph',
    'g2o::SparseOptimizer', 'g2o::OptimizationAlgorithm',
    # DBoW2 类型
    'DBoW2::BowVector', 'DBoW2::FeatureVector', 'DBoW2::ORBVocabulary',
    # Boost 类型
    'boost::shared_ptr', 'boost::make_shared', 'boost::weak_ptr',
    'boost::function', 'boost::bind', 'boost::ref',
    # Python 内置类型
    'np.ndarray', 'pd.DataFrame', 'pd.Series', 'pd.Index',
    'torch.Tensor', 'torch.nn.Module', 'torch.optim.Optimizer',
    # JavaScript 内置对象（这些是函数调用，不是类型，已移至 KNOWN_LIBRARY_PREFIXES 过滤）
    # console.*, document.*, Math.*, JSON.*, Promise.* 等通过 KNOWN_LIBRARY_PREFIXES 过滤
}


