"""测试 ApiGenerator"""
import pytest
from pathlib import Path
from generators.api_generator import ApiGenerator
import tempfile


def test_generate_single_api_page():
    """测试生成单个 API 页面"""
    with tempfile.TemporaryDirectory() as tmpdir:
        api_data = {
            'OpenCV': [
                {'func': 'cv::imread', 'file': 'Tracking.cc', 'line': 42,
                 'code': 'cv::imread("test.png", cv::IMREAD_COLOR)'},
            ]
        }
        generator = ApiGenerator(Path(tmpdir))
        pages = generator.generate(api_data)
        assert len(pages) == 1
        assert pages[0]['filename'] == 'api-opencv.md'
        assert 'cv::imread' in pages[0]['content']
        # 检查行号引用格式
        assert 'Tracking.cc#42' in pages[0]['content']


def test_generate_multiple_libraries():
    """测试生成多个库的 API 页面"""
    with tempfile.TemporaryDirectory() as tmpdir:
        api_data = {
            'OpenCV': [
                {'func': 'cv::imread', 'file': 'Tracking.cc', 'line': 1,
                 'code': 'cv::imread("test.png")'},
            ],
            'PCL': [
                {'func': 'pcl::PassThrough', 'file': 'PointCloud.cc', 'line': 10,
                 'code': 'pcl::PassThrough<PointXYZ> pt'},
            ]
        }
        generator = ApiGenerator(Path(tmpdir))
        pages = generator.generate(api_data)
        assert len(pages) == 2
        filenames = [p['filename'] for p in pages]
        assert 'api-opencv.md' in filenames
        assert 'api-pcl.md' in filenames


def test_generate_skips_unknown_library():
    """测试跳过 Unknown 库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        api_data = {
            'Unknown': [{'func': 'unknown_func', 'file': 'test.cc', 'line': 1,
                         'code': 'unknown_func()'}]
        }
        generator = ApiGenerator(Path(tmpdir))
        pages = generator.generate(api_data)
        assert len(pages) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])