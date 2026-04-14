"""API 说明补充器：使用 SQLite 数据库 + LLM 生成说明"""
import os
import json
from typing import Dict, List, Set
from pathlib import Path
from extractors.api_database import ApiDatabase


def find_missing_apis(api_data: dict, db: ApiDatabase) -> Set[str]:
    """找出所有数据库中没有说明的 API"""
    missing = set()
    for lib_name, apis in api_data.items():
        for api in apis:
            func = api['func']
            if not db.has_description(func):
                missing.add(func)
    return missing


def generate_descriptions_batch(missing_apis: List[str]) -> Dict[str, str]:
    """调用 MiniMax LLM 批量生成 API 说明"""
    if not missing_apis:
        return {}

    api_key = os.environ.get('MINIMAX_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')
    base_url = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimax.com/v1')

    if not api_key:
        print("Warning: MINIMAX_API_KEY not set, cannot generate descriptions")
        return {}

    import urllib.request
    import urllib.error

    prompt = f"""你是一个专业的代码 API 文档助手。请为以下 API 生成简洁的中文说明（1-2句话）。

要求：
- 说明函数/类的用途
- 简要说明关键参数（如果有）
- 使用专业但易懂的语言
- 如果是未知库，根据函数名推断用途

API 列表：
{chr(10).join(f"- {api}" for api in missing_apis)}

请以 JSON 格式返回，key 是 API 名称，value 是说明。例如：
{{
  "cv::imread": "从文件读取图像，支持多种格式如 PNG、JPG、BMP 等",
  "torch.nn.Module": "PyTorch 神经网络模块基类，所有网络层需继承此类"
}}

只返回 JSON，不要有其他文字："""

    payload = json.dumps({
        'model': 'MiniMax-M2.7',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 4096,
        'temperature': 0.3
    }).encode('utf-8')

    req = urllib.request.Request(
        f'{base_url}/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response_body = resp.read().decode('utf-8')
            if not response_body.strip():
                print("Warning: LLM returned empty response")
                return {}
            result = json.loads(response_body)
            content = result['choices'][0]['message']['content']
            # 处理 MiniMax 思考层输出
            content = content.strip()
            if '</think>' in content:
                parts = content.split('</think>')
                content = parts[-1].strip()
            # 提取 JSON
            if content.startswith('```'):
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1])
            return json.loads(content)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')[:500]
        print(f"Warning: LLM HTTP error {e.code}: {body}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: LLM JSON decode error: {e}")
        return {}
    except Exception as e:
        print(f"Warning: LLM call failed: {type(e).__name__}: {e}")
        return {}


def enrich_api_descriptions(api_data: dict, db: ApiDatabase) -> dict:
    """为 api_data 中所有缺失的 API 补充说明"""
    missing = find_missing_apis(api_data, db)

    if not missing:
        total = sum(len(v) for v in api_data.values())
        print(f"All {total} APIs have descriptions in database (cache hit)")
        # 仍然记录调用位置
        for lib_name, apis in api_data.items():
            for api in apis:
                db.add_call_location(
                    func=api['func'],
                    project=api.get('project', ''),
                    file=api.get('file', ''),
                    line=api.get('line', 0),
                    code=api.get('code', '')
                )
        return api_data

    print(f"Generating descriptions for {len(missing)} missing APIs...")

    # 批量生成
    new_descriptions = generate_descriptions_batch(sorted(missing))

    if not new_descriptions:
        print("Warning: Could not generate descriptions from LLM")
        return api_data

    # 保存到数据库
    for func, description in new_descriptions.items():
        db.add_api(func, description, source='llm')

    print(f"Generated and cached {len(new_descriptions)} new descriptions")

    # 记录调用位置
    for lib_name, apis in api_data.items():
        for api in apis:
            db.add_call_location(
                func=api['func'],
                project=api.get('project', ''),
                file=api.get('file', ''),
                line=api.get('line', 0),
                code=api.get('code', '')
            )

    return api_data
