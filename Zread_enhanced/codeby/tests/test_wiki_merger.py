"""测试 WikiMerger"""
import pytest
from mergers.wiki_merger import WikiMerger


def test_merge_api_pages():
    """测试合并 API 页面到 wiki.json"""
    wiki_json = {
        'id': 'test-version',
        'pages': [
            {'slug': '7-tracking', 'title': 'Tracking跟踪线程', 'group': '核心架构'},
        ]
    }
    api_pages = [
        {'slug': 'api-tracking', 'title': 'Tracking API 速查', 'group': 'API 速查'},
    ]
    merger = WikiMerger()
    result = merger.merge(wiki_json, api_pages)
    assert len(result['pages']) == 2
    assert result['pages'][1]['slug'] == 'api-tracking'
    assert result['pages'][1]['group'] == 'API 速查'


def test_generate_api_index():
    """测试生成 API 索引"""
    pages = [
        {'filename': 'api-opencv.md', 'lib': 'OpenCV'},
        {'filename': 'api-pcl.md', 'lib': 'PCL'},
    ]
    merger = WikiMerger()
    index = merger.generate_api_index(pages)
    assert len(index) == 2
    assert index[0]['slug'] == 'api-opencv'
    assert index[0]['title'] == 'OpenCV API 速查'
    assert index[1]['slug'] == 'api-pcl'
    assert index[1]['title'] == 'PCL API 速查'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])