#!/usr/bin/env python3
"""
Nexus API 测试脚本
用于测试Nexus连接和文件上传功能
"""

import requests
from requests.auth import HTTPBasicAuth
import os
import sys


class NexusClient:
    """Nexus API 客户端"""

    def __init__(self, base_url, username, password):
        """
        初始化Nexus客户端

        Args:
            base_url: Nexus服务器地址 (例如: http://localhost:8081)
            username: 用户名
            password: 密码
        """
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def test_connection(self):
        """
        测试Nexus连接

        Returns:
            bool: 连接成功返回True，否则返回False
        """
        try:
            # 测试连接 - 可以使用status endpoint
            url = f"{self.base_url}/service/rest/v1/status"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                print(f"✓ 连接成功: {self.base_url}")
                print(f"  状态码: {response.status_code}")
                return True
            else:
                print(f"✗ 连接失败: {self.base_url}")
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ 连接错误: {e}")
            return False

    def upload_file(self, repository, file_path, directory="", asset_name=None):
        """
        上传文件到Nexus仓库

        Args:
            repository: 仓库名称
            file_path: 本地文件路径
            directory: 目标目录路径 (可选)
            asset_name: 上传后的文件名 (可选，默认使用原文件名)

        Returns:
            bool: 上传成功返回True，否则返回False
        """
        if not os.path.exists(file_path):
            print(f"✗ 文件不存在: {file_path}")
            return False

        try:
            # 构建上传URL
            # 注意: 根据你的Nexus仓库类型(raw, maven, npm等)，URL格式可能不同
            # 这里使用raw仓库的上传API作为示例

            # 获取文件名
            filename = asset_name or os.path.basename(file_path)

            # 构建路径
            path = f"{directory}/{filename}" if directory else filename
            path = path.lstrip('/')

            # Raw仓库上传URL格式
            url = f"{self.base_url}/repository/{repository}/{path}"

            # 读取文件
            with open(file_path, 'rb') as f:
                files_data = f.read()

            # 上传文件
            response = self.session.put(
                url,
                data=files_data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=30
            )

            if response.status_code in [200, 201, 204]:
                print(f"✓ 文件上传成功")
                print(f"  文件: {file_path}")
                print(f"  目标: {repository}/{path}")
                print(f"  状态码: {response.status_code}")
                return True
            else:
                print(f"✗ 文件上传失败")
                print(f"  文件: {file_path}")
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text}")
                return False

        except Exception as e:
            print(f"✗ 上传错误: {e}")
            return False

    def upload_with_components_api(self, repository, file_path, component_attrs=None):
        """
        使用Components API上传文件（适用于Maven等仓库）

        Args:
            repository: 仓库名称
            file_path: 本地文件路径
            component_attrs: 组件属性字典 (例如: groupId, artifactId, version等)

        Returns:
            bool: 上传成功返回True，否则返回False
        """
        if not os.path.exists(file_path):
            print(f"✗ 文件不存在: {file_path}")
            return False

        try:
            url = f"{self.base_url}/service/rest/v1/components"

            # 准备multipart/form-data
            files = {
                'raw.asset1': (os.path.basename(file_path), open(file_path, 'rb'))
            }

            data = {
                'raw.directory': component_attrs.get('directory', '/') if component_attrs else '/',
                'raw.asset1.filename': component_attrs.get('filename', os.path.basename(file_path)) if component_attrs else os.path.basename(file_path)
            }

            # 添加仓库参数
            params = {'repository': repository}

            response = self.session.post(
                url,
                params=params,
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code in [200, 201, 204]:
                print(f"✓ 文件上传成功（Components API）")
                print(f"  文件: {file_path}")
                print(f"  仓库: {repository}")
                print(f"  状态码: {response.status_code}")
                return True
            else:
                print(f"✗ 文件上传失败")
                print(f"  状态码: {response.status_code}")
                print(f"  响应: {response.text}")
                return False

        except Exception as e:
            print(f"✗ 上传错误: {e}")
            return False


def main():
    """主函数"""

    # ==================== 配置区域 ====================
    # 请在此处填入你的Nexus服务器信息

    NEXUS_URL = "http://localhost:8081"  # Nexus服务器地址
    USERNAME = "admin"                    # 用户名
    PASSWORD = "admin123"                 # 密码
    REPOSITORY = "raw-hosted"             # 仓库名称

    # 测试文件路径（请修改为实际的文件路径）
    TEST_FILE = "/path/to/your/test/file.txt"

    # 上传目标目录（可选）
    TARGET_DIRECTORY = "test"

    # ================================================

    print("=" * 60)
    print("Nexus API 测试")
    print("=" * 60)
    print()

    # 创建客户端
    client = NexusClient(NEXUS_URL, USERNAME, PASSWORD)

    # 测试连接
    print("1. 测试连接...")
    print("-" * 60)
    connection_ok = client.test_connection()
    print()

    if not connection_ok:
        print("连接失败，请检查配置")
        sys.exit(1)

    # 测试文件上传
    print("2. 测试文件上传...")
    print("-" * 60)

    if os.path.exists(TEST_FILE):
        # 使用直接上传方式（适用于raw仓库）
        client.upload_file(
            repository=REPOSITORY,
            file_path=TEST_FILE,
            directory=TARGET_DIRECTORY
        )
        print()

        # 如果需要使用Components API，可以取消下面的注释
        # client.upload_with_components_api(
        #     repository=REPOSITORY,
        #     file_path=TEST_FILE,
        #     component_attrs={
        #         'directory': TARGET_DIRECTORY,
        #         'filename': os.path.basename(TEST_FILE)
        #     }
        # )
    else:
        print(f"测试文件不存在，跳过上传测试")
        print(f"请修改 TEST_FILE 变量指向一个实际的文件")

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
