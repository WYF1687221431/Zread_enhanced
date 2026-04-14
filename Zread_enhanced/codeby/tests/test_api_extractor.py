"""测试 ApiExtractor"""
import pytest
from extractors.api_extractor import ApiExtractor


def test_extract_single_api_call():
    """测试从代码字符串提取 API 调用"""
    code = '''
    cv::Mat image = cv::imread("test.png", cv::IMREAD_COLOR);
    cv::resize(image, resized, cv::Size(640, 480));
    '''
    extractor = ApiExtractor()
    result = extractor.extract_from_code(code)
    funcs = [r['func'] for r in result]
    # cv::Size 是类型，应该被过滤
    assert 'cv::imread' in funcs
    assert 'cv::resize' in funcs
    assert 'cv::Size' not in funcs  # 类型，不是函数


def test_extract_with_function_calls_only():
    """测试只提取函数调用，不提取类型"""
    code = '''
    pcl::PointCloud<pcl::PointXYZRGBA> cloud;
    cv::imshow("win", image);
    cv::waitKey(0);
    '''
    extractor = ApiExtractor()
    result = extractor.extract_from_code(code)
    funcs = [r['func'] for r in result]
    assert 'cv::imshow' in funcs
    assert 'cv::waitKey' in funcs
    # pcl::PointCloud 是类型，应该被过滤
    assert 'pcl::PointCloud' not in funcs


def test_extract_from_code_with_location():
    """测试 API 调用位置信息"""
    code = '''cv::imread("test.png");'''
    extractor = ApiExtractor()
    result = extractor.extract_from_code(code, 'test.cc')
    assert result[0]['file'] == 'test.cc'
    assert result[0]['line'] == 1
    assert result[0]['code'] == 'cv::imread("test.png")'


def test_extract_multiple_libraries():
    """测试从多库代码提取"""
    code = '''
    cv::imread("test.png");
    cv::namedWindow("win");
    pcl::visualization::PCLVisualizer viewer;
    '''
    extractor = ApiExtractor()
    result = extractor.extract_from_code(code)
    funcs = [r['func'] for r in result]
    assert 'cv::imread' in funcs
    assert 'cv::namedWindow' in funcs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])