#!/usr/bin/env python3
"""
服务分离验证脚本
验证东方烟草报改写系统和CNIPA专利系统完全分离运行
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

# 服务配置
NEWS_SERVICE_URL = "http://localhost:8081"
PATENT_SERVICE_URL = "http://localhost:8082"

# 验证结果
validation_results = {
    "news_service": {},
    "patent_service": {},
    "separation": {},
    "overall": False
}

def test_health_check(service_name: str, url: str, expected_service: str, expected_port: int) -> Dict[str, Any]:
    """测试健康检查接口"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        response.raise_for_status()

        data = response.json()

        # 验证service字段
        actual_service = data.get("service", "")
        if actual_service != expected_service:
            return {
                "passed": False,
                "error": f"Service field mismatch: expected '{expected_service}', got '{actual_service}'"
            }

        # 验证port字段
        actual_port = data.get("port", 0)
        if actual_port != expected_port:
            return {
                "passed": False,
                "error": f"Port field mismatch: expected {expected_port}, got {actual_port}"
            }

        # 验证ok字段
        if not data.get("ok", False):
            return {
                "passed": False,
                "error": "Service health check returned not ok"
            }

        return {
            "passed": True,
            "data": data
        }

    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

def test_openapi_documentation(service_name: str, url: str, expected_title: str, expected_keywords: List[str]) -> Dict[str, Any]:
    """测试OpenAPI文档"""
    try:
        response = requests.get(f"{url}/openapi.json", timeout=10)
        response.raise_for_status()

        data = response.json()

        # 验证标题
        actual_title = data.get("info", {}).get("title", "")
        if actual_title != expected_title:
            return {
                "passed": False,
                "error": f"OpenAPI title mismatch: expected '{expected_title}', got '{actual_title}'"
            }

        # 验证描述包含关键词
        description = data.get("info", {}).get("description", "")
        missing_keywords = [kw for kw in expected_keywords if kw not in description]
        if missing_keywords:
            return {
                "passed": False,
                "error": f"OpenAPI description missing keywords: {missing_keywords}"
            }

        # 验证路径
        paths = list(data.get("paths", {}).keys())

        return {
            "passed": True,
            "data": {
                "title": actual_title,
                "description": description,
                "paths": paths
            }
        }

    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

def test_functionality(service_name: str, url: str, test_endpoint: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """测试基本功能"""
    try:
        if test_endpoint == "/rewrite":
            response = requests.post(f"{url}{test_endpoint}", json=test_data, timeout=30)
        else:
            response = requests.post(f"{url}{test_endpoint}", json=test_data, timeout=30)

        response.raise_for_status()

        data = response.json()

        # 基本验证
        if service_name == "news" and "title" in data and "lead" in data:
            return {"passed": True, "data": data}
        elif service_name == "patent" and data.get("success", False):
            return {"passed": True, "data": data}
        else:
            return {
                "passed": False,
                "error": "Response structure validation failed"
            }

    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

def check_no_contamination() -> Dict[str, Any]:
    """检查服务间无交叉污染"""
    try:
        # 获取两个服务的OpenAPI文档
        news_openapi = requests.get(f"{NEWS_SERVICE_URL}/openapi.json", timeout=10).json()
        patent_openapi = requests.get(f"{PATENT_SERVICE_URL}/openapi.json", timeout=10).json()

        news_paths = set(news_openapi.get("paths", {}).keys())
        patent_paths = set(patent_openapi.get("paths", {}).keys())

        # 检查新闻服务是否有专利端点
        patent_specific_paths = {"/process", "/gates", "/system-info", "/upload-and-process"}
        news_has_patent_paths = news_paths.intersection(patent_specific_paths)
        if news_has_patent_paths:
            return {
                "passed": False,
                "error": f"News service contains patent-specific paths: {news_has_patent_paths}"
            }

        # 检查专利服务是否有新闻端点
        news_specific_paths = {"/rewrite", "/learning-stats"}
        patent_has_news_paths = patent_paths.intersection(news_specific_paths)
        if patent_has_news_paths:
            return {
                "passed": False,
                "error": f"Patent service contains news-specific paths: {patent_has_news_paths}"
            }

        return {
            "passed": True,
            "data": {
                "news_paths": list(news_paths),
                "patent_paths": list(patent_paths)
            }
        }

    except Exception as e:
        return {
            "passed": False,
            "error": str(e)
        }

def validate_service_separation():
    """执行完整的验证流程"""
    print("🚀 开始服务分离验证...")
    print("=" * 60)

    # 1. 验证新闻服务
    print("📰 验证东方烟草报风格改写系统 (端口: 8081)")
    print("-" * 50)

    # 健康检查
    news_health = test_health_check(
        "news", NEWS_SERVICE_URL,
        "东方烟草报风格改写系统", 8081
    )
    validation_results["news_service"]["health"] = news_health
    print(f"  健康检查: {'✅ 通过' if news_health['passed'] else '❌ 失败'}")
    if not news_health['passed']:
        print(f"    错误: {news_health['error']}")

    # OpenAPI文档
    news_openapi = test_openapi_documentation(
        "news", NEWS_SERVICE_URL,
        "东方烟草报风格改写系统 API",
        ["烟草", "新华财经"]
    )
    validation_results["news_service"]["openapi"] = news_openapi
    print(f"  OpenAPI文档: {'✅ 通过' if news_openapi['passed'] else '❌ 失败'}")
    if not news_openapi['passed']:
        print(f"    错误: {news_openapi['error']}")

    # 功能测试
    news_functionality = test_functionality(
        "news", NEWS_SERVICE_URL, "/rewrite",
        {"text": "镇江烟草推进数字化转型工作"}
    )
    validation_results["news_service"]["functionality"] = news_functionality
    print(f"  功能测试: {'✅ 通过' if news_functionality['passed'] else '❌ 失败'}")
    if not news_functionality['passed']:
        print(f"    错误: {news_functionality['error']}")

    print()

    # 2. 验证专利服务
    print("📋 验证CNIPA发明专利高质量改写系统 (端口: 8082)")
    print("-" * 50)

    # 健康检查
    patent_health = test_health_check(
        "patent", PATENT_SERVICE_URL,
        "CNIPA发明专利高质量改写系统", 8082
    )
    validation_results["patent_service"]["health"] = patent_health
    print(f"  健康检查: {'✅ 通过' if patent_health['passed'] else '❌ 失败'}")
    if not patent_health['passed']:
        print(f"    错误: {patent_health['error']}")

    # OpenAPI文档
    patent_openapi = test_openapi_documentation(
        "patent", PATENT_SERVICE_URL,
        "CNIPA发明专利高质量改写系统 API",
        ["CNIPA", "专利"]
    )
    validation_results["patent_service"]["openapi"] = patent_openapi
    print(f"  OpenAPI文档: {'✅ 通过' if patent_openapi['passed'] else '❌ 失败'}")
    if not patent_openapi['passed']:
        print(f"    错误: {patent_openapi['error']}")

    # 功能测试
    patent_functionality = test_functionality(
        "patent", PATENT_SERVICE_URL, "/process",
        {
            "draft_content": "一种改进的烟草加工设备和方法",
            "invention_type": "invention",
            "enable_checks": True
        }
    )
    validation_results["patent_service"]["functionality"] = patent_functionality
    print(f"  功能测试: {'✅ 通过' if patent_functionality['passed'] else '❌ 失败'}")
    if not patent_functionality['passed']:
        print(f"    错误: {patent_functionality['error']}")

    print()

    # 3. 验证服务分离
    print("🔍 验证服务分离和无交叉污染")
    print("-" * 50)

    no_contamination = check_no_contamination()
    validation_results["separation"]["no_contamination"] = no_contamination
    print(f"  无交叉污染: {'✅ 通过' if no_contamination['passed'] else '❌ 失败'}")
    if not no_contamination['passed']:
        print(f"    错误: {no_contamination['error']}")

    print()

    # 4. 总体结果
    print("📊 验证结果汇总")
    print("=" * 60)

    all_passed = True

    # 检查新闻服务
    for test_name, result in validation_results["news_service"].items():
        if not result['passed']:
            all_passed = False
            break

    # 检查专利服务
    for test_name, result in validation_results["patent_service"].items():
        if not result['passed']:
            all_passed = False
            break

    # 检查分离
    for test_name, result in validation_results["separation"].items():
        if not result['passed']:
            all_passed = False
            break

    validation_results["overall"] = all_passed

    if all_passed:
        print("🎉 所有验证测试通过！")
        print("✅ 东方烟草报风格改写系统和CNIPA发明专利高质量改写系统已完全分离")
        print("✅ 两个系统运行在不同的端口，没有交叉污染")
        print("✅ OpenAPI文档正确标识了各自的服务")
        print("✅ 基本功能测试通过")
    else:
        print("❌ 验证测试失败")
        print("请检查上述错误信息并修复问题")

    print()
    print("📋 服务访问信息:")
    print(f"  📰 东方烟草报风格改写系统: {NEWS_SERVICE_URL}")
    print(f"  📋 CNIPA发明专利高质量改写系统: {PATENT_SERVICE_URL}")
    print(f"  📖 API文档: {NEWS_SERVICE_URL}/docs 和 {PATENT_SERVICE_URL}/docs")

    return all_passed

def main():
    """主函数"""
    print("🔧 服务分离验证工具")
    print("=" * 60)
    print("该工具将验证两个服务是否完全分离运行:")
    print("  1. 东方烟草报风格改写系统 (端口 8081)")
    print("  2. CNIPA发明专利高质量改写系统 (端口 8082)")
    print()

    # 等待用户确认服务已启动
    input("请确保两个服务都已启动，然后按回车键继续...")

    # 执行验证
    success = validate_service_separation()

    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()