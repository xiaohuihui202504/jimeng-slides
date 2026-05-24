#!/usr/bin/env python
"""
端到端全流程测试脚本
基于PRD、模块设计文档和API设计文档

测试覆盖：
1. 项目管理（创建、获取、更新、删除）
2. 模板上传
3. AI大纲生成
4. 大纲编辑
5. AI页面描述生成（异步）
6. 描述编辑
7. AI图片生成（异步）
8. 图片编辑
9. PPTX导出
10. 静态文件访问
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量 - 支持从当前目录或父目录加载
load_dotenv()  # 首先尝试当前目录
if not os.getenv('GOOGLE_API_KEY'):
    # 如果没有找到，尝试父目录
    parent_env = str(Path(__file__).parent.parent / '.env')
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

import requests
import json
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.project_id: Optional[str] = None
        self.page_ids: list = []
        self.task_ids: Dict[str, str] = {}
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} | {test_name}")
        if details:
            print(f"    {details}")
        print()
        
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
    
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text:^80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}\n")
    
    def print_section(self, text: str):
        """打印小节"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}📋 {text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 80}{Colors.END}\n")
    
    def print_failed_pages_info(self, project_id: str):
        """查询并打印失败页面的详细信息"""
        try:
            response = self.make_request('GET', f"{API_BASE}/projects/{project_id}")
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    pages = data['data'].get('pages', [])
                    failed_pages = [p for p in pages if p.get('status') == 'FAILED']
                    
                    if failed_pages:
                        print(f"\n    {Colors.RED}失败的页面详情：{Colors.END}")
                        for i, page in enumerate(failed_pages, 1):
                            page_id = page.get('page_id', 'N/A')
                            order = page.get('order_index', 'N/A')
                            outline = page.get('outline_content', {})
                            title = outline.get('title', 'Unknown')
                            
                            print(f"\n    {Colors.RED}[失败页面 {i}]{Colors.END}")
                            print(f"      页面ID: {page_id}")
                            print(f"      顺序: {order}")
                            print(f"      标题: {title}")
                            print(f"      状态: {page.get('status')}")
                            
                            # 尝试从数据库查询更详细的错误（如果可能）
                            # 这里我们先显示基本信息
                        print()
        except Exception as e:
            print(f"    {Colors.RED}查询失败页面信息时出错: {e}{Colors.END}\n")
    
    def make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """发送HTTP请求并处理异常"""
        try:
            response = requests.request(method, url, timeout=120, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}请求失败: {e}{Colors.END}")
            return None
    
    def test_health_check(self):
        """测试1: 健康检查"""
        self.print_section("测试1: 健康检查")
        
        response = self.make_request('GET', f"{BASE_URL}/health")
        
        if response and response.status_code == 200:
            data = response.json()
            self.log_test(
                "健康检查",
                data.get('status') == 'ok',
                f"响应: {json.dumps(data, ensure_ascii=False)}"
            )
        else:
            self.log_test("健康检查", False, f"状态码: {response.status_code if response else 'N/A'}")
    
    def test_create_project(self):
        """测试2: 创建项目"""
        self.print_section("测试2: 创建项目 (idea模式)")
        
        payload = {
            "creation_type": "idea",
            "idea_prompt": "生成一份关于量子计算的PPT，包括基本概念、发展历程和未来应用，共4-5页"
        }
        
        response = self.make_request(
            'POST',
            f"{API_BASE}/projects",
            json=payload
        )
        
        if response and response.status_code in [200, 201]:
            data = response.json()
            if data.get('success'):
                self.project_id = data['data']['project_id']
                self.log_test(
                    "创建项目",
                    True,
                    f"项目ID: {self.project_id}\n    状态: {data['data'].get('status')}"
                )
                return True
            else:
                self.log_test("创建项目", False, f"响应错误: {data}")
        else:
            self.log_test("创建项目", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_get_project(self):
        """测试3: 获取项目详情"""
        self.print_section("测试3: 获取项目详情")
        
        if not self.project_id:
            self.log_test("获取项目详情", False, "没有可用的项目ID")
            return False
        
        response = self.make_request('GET', f"{API_BASE}/projects/{self.project_id}")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                project_data = data['data']
                self.log_test(
                    "获取项目详情",
                    True,
                    f"项目状态: {project_data.get('status')}\n    "
                    f"创建时间: {project_data.get('created_at')}\n    "
                    f"页面数: {len(project_data.get('pages', []))}"
                )
                return True
            else:
                self.log_test("获取项目详情", False, f"响应: {data}")
        else:
            self.log_test("获取项目详情", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_upload_template(self, template_path: str = "../../template_g.png"):
        """测试4: 上传模板"""
        self.print_section("测试4: 上传风格模板")
        
        if not self.project_id:
            self.log_test("上传模板", False, "没有可用的项目ID")
            return False
        
        # 查找可用的模板文件
        project_root = Path(__file__).parent.parent
        possible_paths = [
            template_path,
            str(project_root / "template_g.png"),
            str(project_root / "template_b.png"),
            str(project_root / "template.png")
        ]
        
        template_file = None
        for path in possible_paths:
            if os.path.exists(path):
                template_file = path
                break
        
        if not template_file:
            self.log_test("上传模板", False, "找不到模板文件，跳过此测试")
            return False
        
        try:
            with open(template_file, 'rb') as f:
                files = {'template_image': f}
                response = self.make_request(
                    'POST',
                    f"{API_BASE}/projects/{self.project_id}/template",
                    files=files
                )
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    template_url = data['data'].get('template_image_url')
                    file_size = os.path.getsize(template_file) / 1024 / 1024
                    self.log_test(
                        "上传模板",
                        True,
                        f"文件: {os.path.basename(template_file)} ({file_size:.2f} MB)\n    "
                        f"URL: {template_url}"
                    )
                    return True
                else:
                    self.log_test("上传模板", False, f"响应: {data}")
            else:
                self.log_test("上传模板", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        except Exception as e:
            self.log_test("上传模板", False, f"异常: {str(e)}")
        
        return False
    
    def test_generate_outline(self):
        """测试5: AI生成大纲"""
        self.print_section("测试5: AI生成大纲")
        
        if not self.project_id:
            self.log_test("生成大纲", False, "没有可用的项目ID")
            return False
        
        payload = {
            "idea_prompt": "生成一份关于量子计算的PPT，包括基本概念、发展历程和未来应用，共4-5页"
        }
        
        response = self.make_request(
            'POST',
            f"{API_BASE}/projects/{self.project_id}/generate/outline",
            json=payload
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                pages = data['data'].get('pages', [])
                self.page_ids = [p['page_id'] for p in pages]
                
                outline_info = []
                for i, page in enumerate(pages, 1):
                    outline = page.get('outline_content', {})
                    title = outline.get('title', 'Untitled')
                    points_count = len(outline.get('points', []))
                    outline_info.append(f"第{i}页: {title} ({points_count}个要点)")
                
                self.log_test(
                    "生成大纲",
                    True,
                    f"生成了 {len(pages)} 页大纲\n    " + "\n    ".join(outline_info)
                )
                return True
            else:
                error_msg = data.get('error', {}).get('message', '未知错误')
                self.log_test("生成大纲", False, f"错误: {error_msg}")
        else:
            self.log_test("生成大纲", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_edit_outline(self):
        """测试6: 编辑大纲"""
        self.print_section("测试6: 编辑单页大纲")
        
        if not self.project_id or not self.page_ids:
            self.log_test("编辑大纲", False, "没有可用的页面ID")
            return False
        
        # 编辑第一页
        page_id = self.page_ids[0]
        payload = {
            "outline_content": {
                "title": "量子计算：未来科技的基石（已编辑）",
                "points": [
                    "量子计算的基本原理",
                    "量子比特与经典比特的区别",
                    "量子叠加和量子纠缠"
                ]
            }
        }
        
        response = self.make_request(
            'PUT',
            f"{API_BASE}/projects/{self.project_id}/pages/{page_id}/outline",
            json=payload
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test(
                    "编辑大纲",
                    True,
                    f"成功编辑页面: {page_id}\n    "
                    f"新标题: {payload['outline_content']['title']}"
                )
                return True
            else:
                self.log_test("编辑大纲", False, f"响应: {data}")
        else:
            self.log_test("编辑大纲", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_generate_descriptions(self):
        """测试7: 批量生成页面描述（异步）"""
        self.print_section("测试7: 批量生成页面描述（异步）")
        
        if not self.project_id:
            self.log_test("生成描述", False, "没有可用的项目ID")
            return False
        
        payload = {
            "max_workers": 3
        }
        
        response = self.make_request(
            'POST',
            f"{API_BASE}/projects/{self.project_id}/generate/descriptions",
            json=payload
        )
        
        if response and response.status_code in [200, 202]:
            data = response.json()
            if data.get('success'):
                task_id = data['data'].get('task_id')
                self.task_ids['descriptions'] = task_id
                
                self.log_test(
                    "生成描述（异步）",
                    True,
                    f"任务ID: {task_id}\n    "
                    f"状态: {data['data'].get('status')}"
                )
                return True
            else:
                error_msg = data.get('error', {}).get('message', '未知错误')
                self.log_test("生成描述（异步）", False, f"错误: {error_msg}")
        else:
            self.log_test("生成描述（异步）", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_task_progress(self, task_type: str):
        """测试8: 查询任务进度"""
        self.print_section(f"测试8: 查询{task_type}任务进度")
        
        if not self.project_id or task_type not in self.task_ids:
            self.log_test(f"查询{task_type}任务进度", False, "没有可用的任务ID")
            return False
        
        task_id = self.task_ids[task_type]
        max_wait_time = 300  # 5分钟
        check_interval = 5  # 5秒检查一次
        elapsed_time = 0
        
        print(f"等待任务完成（最长等待{max_wait_time}秒）...")
        
        while elapsed_time < max_wait_time:
            response = self.make_request(
                'GET',
                f"{API_BASE}/projects/{self.project_id}/tasks/{task_id}"
            )
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    task_data = data['data']
                    status = task_data.get('status')
                    progress = task_data.get('progress', {})
                    
                    total = progress.get('total', 0)
                    completed = progress.get('completed', 0)
                    failed = progress.get('failed', 0)
                    
                    print(f"    进度: {completed}/{total} 完成, {failed} 失败, 状态: {status}")
                    
                    # 如果有任何失败，立即查询并显示失败页面的详细信息
                    if failed > 0:
                        print(f"\n    {Colors.YELLOW}⚠️  检测到 {failed} 个页面失败，正在查询详细信息...{Colors.END}")
                        self.print_failed_pages_info(self.project_id)
                    
                    if status in ['COMPLETED', 'FAILED']:
                        error_msg = task_data.get('error_message', '')
                        details = f"最终状态: {status}\n    "
                        details += f"完成: {completed}/{total}, 失败: {failed}\n    "
                        details += f"耗时: {elapsed_time}秒"
                        if error_msg:
                            details += f"\n    错误信息: {error_msg}"
                        
                        # 如果有失败，再次显示失败页面信息
                        if failed > 0 and status == 'COMPLETED':
                            details += f"\n    {Colors.YELLOW}查看上方失败页面的详细错误信息{Colors.END}"
                        
                        self.log_test(
                            f"查询{task_type}任务进度",
                            status == 'COMPLETED' and failed == 0,  # 有失败也算测试失败
                            details
                        )
                        return status == 'COMPLETED' and failed == 0
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        self.log_test(f"查询{task_type}任务进度", False, f"任务超时（{max_wait_time}秒）")
        return False
    
    def test_edit_description(self):
        """测试9: 编辑页面描述"""
        self.print_section("测试9: 编辑页面描述")
        
        if not self.project_id or not self.page_ids:
            self.log_test("编辑描述", False, "没有可用的页面ID")
            return False
        
        page_id = self.page_ids[0]
        payload = {
            "description_content": {
                "title": "量子计算：未来科技的基石",
                "text_content": [
                    "量子计算是一种利用量子力学原理进行信息处理的新型计算范式",
                    "相比传统计算机，量子计算机具有指数级的计算优势",
                    "主要应用于密码破解、药物研发、金融建模等领域"
                ],
                "layout_suggestion": "标题居中，正文左对齐，使用简洁的设计风格"
            }
        }
        
        response = self.make_request(
            'PUT',
            f"{API_BASE}/projects/{self.project_id}/pages/{page_id}/description",
            json=payload
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test(
                    "编辑描述",
                    True,
                    f"成功编辑页面描述: {page_id}\n    "
                    f"文本内容: {len(payload['description_content']['text_content'])} 段"
                )
                return True
            else:
                self.log_test("编辑描述", False, f"响应: {data}")
        else:
            self.log_test("编辑描述", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_generate_images(self):
        """测试10: 批量生成图片（异步）"""
        self.print_section("测试10: 批量生成图片（异步）")
        
        if not self.project_id:
            self.log_test("生成图片", False, "没有可用的项目ID")
            return False
        
        payload = {
            "max_workers": 3,
            "use_template": True
        }
        
        response = self.make_request(
            'POST',
            f"{API_BASE}/projects/{self.project_id}/generate/images",
            json=payload
        )
        
        if response and response.status_code in [200, 202]:
            data = response.json()
            if data.get('success'):
                task_id = data['data'].get('task_id')
                self.task_ids['images'] = task_id
                
                self.log_test(
                    "生成图片（异步）",
                    True,
                    f"任务ID: {task_id}\n    "
                    f"状态: {data['data'].get('status')}"
                )
                return True
            else:
                error_msg = data.get('error', {}).get('message', '未知错误')
                self.log_test("生成图片（异步）", False, f"错误: {error_msg}")
        else:
            self.log_test("生成图片（异步）", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_edit_image(self):
        """测试11: 编辑单页图片"""
        self.print_section("测试11: 自然语言编辑图片")
        
        if not self.project_id or not self.page_ids:
            self.log_test("编辑图片", False, "没有可用的页面ID")
            return False
        
        page_id = self.page_ids[0]
        payload = {
            "edit_instruction": "将标题的颜色改为深蓝色，背景改为浅灰色"
        }
        
        response = self.make_request(
            'POST',
            f"{API_BASE}/projects/{self.project_id}/pages/{page_id}/edit/image",
            json=payload
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test(
                    "编辑图片",
                    True,
                    f"成功提交编辑指令: {payload['edit_instruction']}\n    "
                    f"页面: {page_id}"
                )
                return True
            else:
                error_msg = data.get('error', {}).get('message', '未知错误')
                self.log_test("编辑图片", False, f"错误: {error_msg}")
        else:
            self.log_test("编辑图片", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_export_pptx(self):
        """测试12: 导出PPTX"""
        self.print_section("测试12: 导出PPTX文件")
        
        if not self.project_id:
            self.log_test("导出PPTX", False, "没有可用的项目ID")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_export_{timestamp}.pptx"
        
        response = self.make_request(
            'GET',
            f"{API_BASE}/projects/{self.project_id}/export/pptx",
            params={'filename': output_file}
        )
        
        if response and response.status_code == 200:
            # 保存文件
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024 / 1024
            
            self.log_test(
                "导出PPTX",
                True,
                f"文件: {output_file}\n    "
                f"大小: {file_size:.2f} MB"
            )
            return True
        else:
            self.log_test("导出PPTX", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_static_file_access(self):
        """测试13: 静态文件访问"""
        self.print_section("测试13: 静态文件服务")
        
        if not self.project_id:
            self.log_test("静态文件访问", False, "没有可用的项目ID")
            return False
        
        # 测试访问模板文件
        response = self.make_request(
            'GET',
            f"{BASE_URL}/files/{self.project_id}/template/template.png"
        )
        
        if response and response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = len(response.content)
            
            self.log_test(
                "静态文件访问",
                'image' in content_type,
                f"Content-Type: {content_type}\n    "
                f"大小: {content_length / 1024:.2f} KB"
            )
            return True
        else:
            self.log_test("静态文件访问", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_update_project(self):
        """测试14: 更新项目"""
        self.print_section("测试14: 更新项目信息")
        
        if not self.project_id or not self.page_ids:
            self.log_test("更新项目", False, "没有可用的项目ID或页面ID")
            return False
        
        # 重新排序页面
        reversed_order = list(reversed(self.page_ids))
        payload = {
            "pages_order": reversed_order
        }
        
        response = self.make_request(
            'PUT',
            f"{API_BASE}/projects/{self.project_id}",
            json=payload
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test(
                    "更新项目",
                    True,
                    f"成功重新排序 {len(reversed_order)} 个页面"
                )
                return True
            else:
                self.log_test("更新项目", False, f"响应: {data}")
        else:
            self.log_test("更新项目", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_delete_page(self):
        """测试15: 删除页面"""
        self.print_section("测试15: 删除单页")
        
        if not self.project_id or not self.page_ids:
            self.log_test("删除页面", False, "没有可用的页面ID")
            return False
        
        # 删除最后一页
        page_id = self.page_ids[-1]
        
        response = self.make_request(
            'DELETE',
            f"{API_BASE}/projects/{self.project_id}/pages/{page_id}"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.page_ids.remove(page_id)
                self.log_test(
                    "删除页面",
                    True,
                    f"成功删除页面: {page_id}\n    "
                    f"剩余页面: {len(self.page_ids)}"
                )
                return True
            else:
                self.log_test("删除页面", False, f"响应: {data}")
        else:
            self.log_test("删除页面", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def test_delete_project(self):
        """测试16: 删除项目"""
        self.print_section("测试16: 删除项目")
        
        if not self.project_id:
            self.log_test("删除项目", False, "没有可用的项目ID")
            return False
        
        response = self.make_request(
            'DELETE',
            f"{API_BASE}/projects/{self.project_id}"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test(
                    "删除项目",
                    True,
                    f"成功删除项目: {self.project_id}"
                )
                return True
            else:
                self.log_test("删除项目", False, f"响应: {data}")
        else:
            self.log_test("删除项目", False, f"HTTP状态: {response.status_code if response else 'N/A'}")
        
        return False
    
    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结报告")
        
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = sum(1 for r in self.test_results if not r['passed'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        elapsed = datetime.now() - self.start_time
        
        print(f"总测试数: {total}")
        print(f"{Colors.GREEN}通过: {passed}{Colors.END}")
        print(f"{Colors.RED}失败: {failed}{Colors.END}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"耗时: {elapsed.total_seconds():.2f}秒")
        print()
        
        if failed > 0:
            print(f"{Colors.RED}失败的测试:{Colors.END}")
            for r in self.test_results:
                if not r['passed']:
                    print(f"  ❌ {r['name']}")
                    if r['details']:
                        print(f"     {r['details']}")
            print()
        
        if success_rate == 100:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️  部分测试失败，请检查上述错误{Colors.END}")
        
        print()
    
    def run_full_test(self):
        """运行完整测试流程"""
        self.print_header("🍌 即梦 (Banana Slides) 后端端到端测试")
        
        print(f"测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API地址: {API_BASE}")
        print()
        
        # 基础测试
        self.test_health_check()
        
        # 项目管理测试
        if not self.test_create_project():
            print(f"{Colors.RED}项目创建失败，停止后续测试{Colors.END}")
            self.print_summary()
            return
        
        self.test_get_project()
        
        # 模板测试
        self.test_upload_template()
        
        # AI生成流程
        if self.test_generate_outline():
            self.test_edit_outline()
            
            # 生成描述
            if self.test_generate_descriptions():
                if self.test_task_progress('descriptions'):
                    self.test_edit_description()
                    
                    # 生成图片
                    if self.test_generate_images():
                        if self.test_task_progress('images'):
                            # 编辑图片（可选，可能耗时较长）
                            # self.test_edit_image()
                            
                            # 导出测试
                            self.test_export_pptx()
        
        # 其他功能测试
        self.test_static_file_access()
        self.test_update_project()
        
        # 清理测试（可选）
        # self.test_delete_page()
        # self.test_delete_project()
        
        # 打印总结
        self.print_summary()


def main():
    """主函数"""
    print(f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              🍌 即梦 (Banana Slides) 后端端到端测试套件 🍌              ║
║                                                                           ║
║                   基于PRD、模块设计文档、API设计文档                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝{Colors.END}
""")
    
    # 检查服务器是否运行
    print("检查后端服务器状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ 后端服务器运行正常{Colors.END}\n")
        else:
            print(f"{Colors.RED}✗ 后端服务器响应异常{Colors.END}\n")
            return
    except requests.exceptions.RequestException:
        print(f"{Colors.RED}✗ 无法连接到后端服务器 ({BASE_URL}){Colors.END}")
        print(f"{Colors.YELLOW}请确保后端服务器正在运行: python app.py{Colors.END}\n")
        return
    
    # 运行测试
    runner = E2ETestRunner()
    runner.run_full_test()
    
    print(f"\n{Colors.BOLD}测试完成！{Colors.END}\n")


if __name__ == "__main__":
    main()

