"""
AI Service - handles all AI model interactions
Based on demo.py and gemini_genai.py
TODO: use structured output API
"""
import os
import json
import re
import logging
import requests
import base64
from typing import List, Dict, Optional, Union
from textwrap import dedent
from openai import OpenAI
from PIL import Image
import io
from .prompts import (
    get_outline_generation_prompt,
    get_outline_parsing_prompt,
    get_page_description_prompt,
    get_image_generation_prompt,
    get_image_edit_prompt,
    get_description_to_outline_prompt,
    get_description_split_prompt,
    get_outline_refinement_prompt,
    get_descriptions_refinement_prompt
)

logger = logging.getLogger(__name__)


class ProjectContext:
    """项目上下文数据类，统一管理 AI 需要的所有项目信息"""
    
    def __init__(self, project_or_dict, reference_files_content: Optional[List[Dict[str, str]]] = None):
        """
        Args:
            project_or_dict: 项目对象（Project model）或项目字典（project.to_dict()）
            reference_files_content: 参考文件内容列表
        """
        # 支持直接传入 Project 对象，避免 to_dict() 调用，提升性能
        if hasattr(project_or_dict, 'idea_prompt'):
            # 是 Project 对象
            self.idea_prompt = project_or_dict.idea_prompt
            self.outline_text = project_or_dict.outline_text
            self.description_text = project_or_dict.description_text
            self.creation_type = project_or_dict.creation_type or 'idea'
        else:
            # 是字典
            self.idea_prompt = project_or_dict.get('idea_prompt')
            self.outline_text = project_or_dict.get('outline_text')
            self.description_text = project_or_dict.get('description_text')
            self.creation_type = project_or_dict.get('creation_type', 'idea')
        
        self.reference_files_content = reference_files_content or []
    
    def to_dict(self) -> Dict:
        """转换为字典，方便传递"""
        return {
            'idea_prompt': self.idea_prompt,
            'outline_text': self.outline_text,
            'description_text': self.description_text,
            'creation_type': self.creation_type,
            'reference_files_content': self.reference_files_content
        }


class AIService:
    """Service for AI model interactions using DeepSeek and Jimeng"""

    def __init__(self, deepseek_api_key: str, deepseek_api_base: str = None,
                 jimeng_api_key: str = None, jimeng_api_base: str = None):
        """Initialize AI service with API credentials"""
        # Initialize DeepSeek client for text generation
        self.deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url=deepseek_api_base or 'https://api-inference.modelscope.cn/v1'
        )

        # Jimeng API configuration for image generation
        self.jimeng_api_key = jimeng_api_key
        self.jimeng_api_base = jimeng_api_base or 'https://jimeng1.duckcloud.fun/v1'

        # Model names
        self.text_model = "deepseek-ai/DeepSeek-V3.2"
        self.image_model = "jimeng-4.5"
    
    @staticmethod
    def extract_image_urls_from_markdown(text: str) -> List[str]:
        """
        从 markdown 文本中提取图片 URL
        
        Args:
            text: Markdown 文本，可能包含 ![](url) 格式的图片
            
        Returns:
            图片 URL 列表（包括 http/https URL 和 /files/mineru/ 开头的本地路径）
        """
        if not text:
            return []
        
        # 匹配 markdown 图片语法: ![](url) 或 ![alt](url)
        pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(pattern, text)
        
        # 过滤掉空字符串，支持 http/https URL 和 /files/mineru/ 开头的本地路径
        urls = []
        for url in matches:
            url = url.strip()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('/files/mineru/')):
                urls.append(url)
        
        return urls
    
    @staticmethod
    def remove_markdown_images(text: str) -> str:
        """
        从文本中移除 Markdown 图片链接，只保留 alt text（描述文字）
        
        Args:
            text: 包含 Markdown 图片语法的文本
            
        Returns:
            移除图片链接后的文本，保留描述文字
        """
        if not text:
            return text
        
        # 将 ![描述文字](url) 替换为 描述文字
        # 如果没有描述文字（空的 alt text），则完全删除该图片链接
        def replace_image(match):
            alt_text = match.group(1).strip()
            # 如果有描述文字，保留它；否则删除整个链接
            return alt_text if alt_text else ''
        
        pattern = r'!\[(.*?)\]\([^\)]+\)'
        cleaned_text = re.sub(pattern, replace_image, text)
        
        # 清理可能产生的多余空行
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text
    
    @staticmethod
    def _convert_mineru_path_to_local(mineru_path: str) -> Optional[str]:
        """
        将 /files/mineru/{extract_id}/{rel_path} 格式的路径转换为本地文件系统路径（支持前缀匹配）
        
        Args:
            mineru_path: MinerU URL 路径，格式为 /files/mineru/{extract_id}/{rel_path}
            
        Returns:
            本地文件系统路径，如果转换失败则返回 None
        """
        from utils.path_utils import find_mineru_file_with_prefix
        
        matched_path = find_mineru_file_with_prefix(mineru_path)
        return str(matched_path) if matched_path else None
    
    @staticmethod
    def download_image_from_url(url: str) -> Optional[Image.Image]:
        """
        从 URL 下载图片并返回 PIL Image 对象
        
        Args:
            url: 图片 URL
            
        Returns:
            PIL Image 对象，如果下载失败则返回 None
        """
        try:
            logger.debug(f"Downloading image from URL: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 从响应内容创建 PIL Image
            image = Image.open(response.raw)
            # 确保图片被加载
            image.load()
            logger.debug(f"Successfully downloaded image: {image.size}, {image.mode}")
            return image
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            return None
    
    def generate_outline(self, project_context: ProjectContext) -> List[Dict]:
        """
        Generate PPT outline from idea prompt
        Based on demo.py gen_outline()

        Args:
            project_context: 项目上下文对象，包含所有原始信息

        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        outline_prompt = get_outline_generation_prompt(project_context)

        # DeepSeek API call with thinking enabled
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': outline_prompt
                }
            ],
            extra_body=extra_body
        )

        outline_text = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        outline = json.loads(outline_text)
        return outline
    
    def parse_outline_text(self, project_context: ProjectContext) -> List[Dict]:
        """
        Parse user-provided outline text into structured outline format
        This method analyzes the text and splits it into pages without modifying the original text

        Args:
            project_context: 项目上下文对象，包含所有原始信息

        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        parse_prompt = get_outline_parsing_prompt(project_context)

        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': parse_prompt
                }
            ],
            extra_body=extra_body
        )

        outline_json = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        outline = json.loads(outline_json)
        return outline
    
    def flatten_outline(self, outline: List[Dict]) -> List[Dict]:
        """
        Flatten outline structure to page list
        Based on demo.py flatten_outline()
        """
        pages = []
        for item in outline:
            if "part" in item and "pages" in item:
                # This is a part, expand its pages
                for page in item["pages"]:
                    page_with_part = page.copy()
                    page_with_part["part"] = item["part"]
                    pages.append(page_with_part)
            else:
                # This is a direct page
                pages.append(item)
        return pages
    
    def generate_page_description(self, project_context: ProjectContext, outline: List[Dict], 
                                 page_outline: Dict, page_index: int) -> str:
        """
        Generate description for a single page
        Based on demo.py gen_desc() logic
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
            outline: Complete outline
            page_outline: Outline for this specific page
            page_index: Page number (1-indexed)
        
        Returns:
            Text description for the page
        """
        part_info = f"\nThis page belongs to: {page_outline['part']}" if 'part' in page_outline else ""
        
        desc_prompt = get_page_description_prompt(
            project_context=project_context,
            outline=outline,
            page_outline=page_outline,
            page_index=page_index,
            part_info=part_info
        )
        
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': desc_prompt
                }
            ],
            extra_body=extra_body
        )

        page_desc = response.choices[0].message.content
        return dedent(page_desc)
    
    def generate_outline_text(self, outline: List[Dict]) -> str:
        """
        Convert outline to text format for prompts
        Based on demo.py gen_outline_text()
        """
        text_parts = []
        for i, item in enumerate(outline, 1):
            if "part" in item and "pages" in item:
                text_parts.append(f"{i}. {item['part']}")
            else:
                text_parts.append(f"{i}. {item.get('title', 'Untitled')}")
        result = "\n".join(text_parts)
        return dedent(result)
    
    def generate_image_prompt(self, outline: List[Dict], page: Dict, 
                            page_desc: str, page_index: int, 
                            has_material_images: bool = False,
                            extra_requirements: Optional[str] = None) -> str:
        """
        Generate image generation prompt for a page
        Based on demo.py gen_prompts()
        
        Args:
            outline: Complete outline
            page: Page outline data
            page_desc: Page description text
            page_index: Page number (1-indexed)
            has_material_images: 是否有素材图片（从项目描述中提取的图片）
            extra_requirements: Optional extra requirements to apply to all pages
        
        Returns:
            Image generation prompt
        """
        outline_text = self.generate_outline_text(outline)
        
        # Determine current section
        if 'part' in page:
            current_section = page['part']
        else:
            current_section = f"{page.get('title', 'Untitled')}"
        
        # 在传给文生图模型之前，移除 Markdown 图片链接
        # 图片本身已经通过 additional_ref_images 传递，只保留文字描述
        cleaned_page_desc = self.remove_markdown_images(page_desc)
        
        prompt = get_image_generation_prompt(
            page_desc=cleaned_page_desc,
            outline_text=outline_text,
            current_section=current_section,
            has_material_images=has_material_images,
            extra_requirements=extra_requirements
        )
        
        return prompt
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def generate_image(self, prompt: str, ref_image_path: Optional[str] = None,
                      aspect_ratio: str = "16:9", resolution: str = "2K",
                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Generate image using Jimeng image model

        Args:
            prompt: Image generation prompt
            ref_image_path: Path to reference image (optional). If None, will generate based on prompt only.
            aspect_ratio: Image aspect ratio (e.g., "16:9", "4:3", "1:1")
            resolution: Image resolution (e.g., "2K", "4K", "1K")
            additional_ref_images: 额外的参考图片列表，可以是本地路径、URL 或 PIL Image 对象

        Returns:
            PIL Image object or None if failed

        Raises:
            Exception with detailed error message if generation fails
        """
        try:
            logger.debug(f"Reference image: {ref_image_path}")
            if additional_ref_images:
                logger.debug(f"Additional reference images: {len(additional_ref_images)}")
            logger.debug(f"Config - aspect_ratio: {aspect_ratio}, resolution: {resolution}")

            # Collect all reference images
            ref_images = []

            # Add main reference image
            if ref_image_path:
                if not os.path.exists(ref_image_path):
                    raise FileNotFoundError(f"Reference image not found: {ref_image_path}")
                main_ref_image = Image.open(ref_image_path)
                ref_images.append(main_ref_image)

            # Add additional reference images
            if additional_ref_images:
                for ref_img in additional_ref_images:
                    if isinstance(ref_img, Image.Image):
                        ref_images.append(ref_img)
                    elif isinstance(ref_img, str):
                        if os.path.exists(ref_img):
                            ref_images.append(Image.open(ref_img))
                        elif ref_img.startswith('http://') or ref_img.startswith('https://'):
                            downloaded_img = self.download_image_from_url(ref_img)
                            if downloaded_img:
                                ref_images.append(downloaded_img)
                            else:
                                logger.warning(f"Failed to download image from URL: {ref_img}, skipping...")
                        elif ref_img.startswith('/files/mineru/'):
                            local_path = self._convert_mineru_path_to_local(ref_img)
                            if local_path and os.path.exists(local_path):
                                ref_images.append(Image.open(local_path))
                            else:
                                logger.warning(f"MinerU image file not found (with prefix matching): {ref_img}, skipping...")

            # Determine API endpoint and request body based on whether we have reference images
            headers = {
                'Authorization': f'Bearer {self.jimeng_api_key}',
                'Content-Type': 'application/json'
            }

            if ref_images:
                # For now, we'll use text-to-image endpoint even with reference images
                # since the composition endpoint expects image URLs, not base64
                endpoint = f"{self.jimeng_api_base}/images/generations"

                data = {
                    "model": self.image_model,
                    "prompt": prompt,
                    "negativePrompt": "",
                    "ratio": aspect_ratio,
                    "resolution": resolution.lower()
                }
            else:
                # Use text-to-image endpoint (文生图)
                endpoint = f"{self.jimeng_api_base}/images/generations"

                data = {
                    "model": self.image_model,
                    "prompt": prompt,
                    "negativePrompt": "",
                    "ratio": aspect_ratio,
                    "resolution": resolution.lower()
                }

            logger.debug(f"Calling Jimeng API at {endpoint}...")
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")

            # Retry mechanism for image generation
            max_retries = 2
            retry_count = 0
            response = None

            while retry_count <= max_retries:
                try:
                    # Increase timeout to 5 minutes for image generation
                    response = requests.post(endpoint, headers=headers, json=data, timeout=300)
                    break  # Success, exit retry loop
                except requests.exceptions.ReadTimeout as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Timeout on attempt {retry_count}/{max_retries+1}, retrying...")
                        continue
                    else:
                        raise Exception(f"Image generation timeout after {max_retries+1} attempts") from e

            # Log response status and content
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text[:1000]}")

            response.raise_for_status()

            result = response.json()
            logger.debug("Jimeng API call completed")

            # Check if we got valid response
            if 'data' not in result or not result['data']:
                logger.error(f"Invalid response from Jimeng API: {result}")
                # Return a default image when API fails
                logger.info("Generating default placeholder image...")
                return self._generate_placeholder_image(prompt, aspect_ratio, resolution)

            # Get the first image URL
            image_url = result['data'][0]['url']
            logger.debug(f"Generated image URL: {image_url}")

            # Download the generated image
            downloaded_img = self.download_image_from_url(image_url)
            if downloaded_img:
                logger.debug(f"Successfully downloaded generated image: {downloaded_img.size}")
                return downloaded_img
            else:
                # Fallback to placeholder image
                logger.warning("Failed to download generated image, using placeholder")
                return self._generate_placeholder_image(prompt, aspect_ratio, resolution)

        except Exception as e:
            error_detail = f"Error generating image: {type(e).__name__}: {str(e)}"
            logger.error(error_detail, exc_info=True)
            # Return placeholder image instead of raising exception
            logger.info("API failed, generating placeholder image as fallback...")
            return self._generate_placeholder_image(prompt, aspect_ratio, resolution)

    def _generate_placeholder_image(self, prompt: str, aspect_ratio: str = "16:9", resolution: str = "2K") -> Image.Image:
        """
        Generate a simple placeholder image with text
        """
        from PIL import ImageDraw, ImageFont
        import textwrap

        # Parse aspect ratio to determine dimensions
        aspect_ratios = {
            "16:9": (1600, 900),
            "4:3": (1600, 1200),
            "1:1": (1200, 1200),
            "9:16": (900, 1600),
            "3:4": (1200, 1600)
        }

        width, height = aspect_ratios.get(aspect_ratio, (1600, 900))

        # Create a simple gradient background
        image = Image.new('RGB', (width, height), color='#f0f0f0')
        draw = ImageDraw.Draw(image)

        # Add a gradient effect
        for y in range(height):
            color_value = 240 + int((y / height) * 15)
            draw.line([(0, y), (width, y)], fill=f'#{color_value:02x}{color_value:02x}{color_value:02x}')

        # Add text
        try:
            # Try to use a larger font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        except:
            try:
                # Fallback to default font
                font = ImageFont.load_default()
            except:
                font = None

        # Prepare text
        title = "图片生成中..."
        subtitle = "Image Generation Failed\nUsing Placeholder"

        # Draw title
        if font:
            title_bbox = draw.textbbox((0, 0), title, font=font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]

            title_x = (width - title_width) // 2
            title_y = height // 2 - 100

            draw.text((title_x, title_y), title, fill='#333333', font=font)

            # Draw subtitle
            subtitle_lines = subtitle.split('\n')
            current_y = title_y + 80

            for line in subtitle_lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                draw.text((line_x, current_y), line, fill='#666666', font=font)
                current_y += 60
        else:
            # Simple text without custom font
            draw.text((width//2 - 100, height//2), title, fill='#333333')
            draw.text((width//2 - 150, height//2 + 50), subtitle, fill='#666666')

        # Add a simple border
        draw.rectangle([10, 10, width-10, height-10], outline='#cccccc', width=2)

        return image
    
    def edit_image(self, prompt: str, current_image_path: str,
                  aspect_ratio: str = "16:9", resolution: str = "2K",
                  original_description: str = None,
                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Edit existing image with natural language instruction
        Uses current image as reference
        
        Args:
            prompt: Edit instruction
            current_image_path: Path to current page image
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
            original_description: Original page description to include in prompt
            additional_ref_images: 额外的参考图片列表，可以是本地路径、URL 或 PIL Image 对象
        
        Returns:
            PIL Image object or None if failed
        """
        # Build edit instruction with original description if available
        edit_instruction = get_image_edit_prompt(
            edit_instruction=prompt,
            original_description=original_description
        )
        return self.generate_image(edit_instruction, current_image_path, aspect_ratio, resolution, additional_ref_images)
    
    def parse_description_to_outline(self, project_context: ProjectContext) -> List[Dict]:
        """
        从描述文本解析出大纲结构
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
        
        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        parse_prompt = get_description_to_outline_prompt(project_context)
        
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': parse_prompt
                }
            ],
            extra_body=extra_body
        )

        outline_json = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        outline = json.loads(outline_json)
        return outline
    
    def parse_description_to_page_descriptions(self, project_context: ProjectContext, outline: List[Dict]) -> List[str]:
        """
        从描述文本切分出每页描述
        
        Args:
            project_context: 项目上下文对象，包含所有原始信息
            outline: 已解析出的大纲结构
        
        Returns:
            List of page descriptions (strings), one for each page in the outline
        """
        split_prompt = get_description_split_prompt(project_context, outline)
        
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': split_prompt
                }
            ],
            extra_body=extra_body
        )

        descriptions_json = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        descriptions = json.loads(descriptions_json)
        
        # 确保返回的是字符串列表
        if isinstance(descriptions, list):
            return [str(desc) for desc in descriptions]
        else:
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))
    
    def refine_outline(self, current_outline: List[Dict], user_requirement: str,
                      project_context: ProjectContext,
                      previous_requirements: Optional[List[str]] = None) -> List[Dict]:
        """
        根据用户要求修改已有大纲
        
        Args:
            current_outline: 当前的大纲结构
            user_requirement: 用户的新要求
            project_context: 项目上下文对象，包含所有原始信息
            previous_requirements: 之前的修改要求列表（可选）
        
        Returns:
            修改后的大纲结构
        """
        refinement_prompt = get_outline_refinement_prompt(
            current_outline=current_outline,
            user_requirement=user_requirement,
            project_context=project_context,
            previous_requirements=previous_requirements
        )
        
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': refinement_prompt
                }
            ],
            extra_body=extra_body
        )

        outline_json = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        outline = json.loads(outline_json)
        return outline
    
    def refine_descriptions(self, current_descriptions: List[Dict], user_requirement: str,
                           project_context: ProjectContext,
                           outline: List[Dict] = None,
                           previous_requirements: Optional[List[str]] = None) -> List[str]:
        """
        根据用户要求修改已有页面描述
        
        Args:
            current_descriptions: 当前的页面描述列表，每个元素包含 {index, title, description_content}
            user_requirement: 用户的新要求
            project_context: 项目上下文对象，包含所有原始信息
            outline: 完整的大纲结构（可选）
            previous_requirements: 之前的修改要求列表（可选）
        
        Returns:
            修改后的页面描述列表（字符串列表）
        """
        refinement_prompt = get_descriptions_refinement_prompt(
            current_descriptions=current_descriptions,
            user_requirement=user_requirement,
            project_context=project_context,
            outline=outline,
            previous_requirements=previous_requirements
        )
        
        extra_body = {
            "enable_thinking": True
        }

        response = self.deepseek_client.chat.completions.create(
            model=self.text_model,
            messages=[
                {
                    'role': 'user',
                    'content': refinement_prompt
                }
            ],
            extra_body=extra_body
        )

        descriptions_json = response.choices[0].message.content.strip().strip("```json").strip("```").strip()
        descriptions = json.loads(descriptions_json)
        
        # 确保返回的是字符串列表
        if isinstance(descriptions, list):
            return [str(desc) for desc in descriptions]
        else:
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))

