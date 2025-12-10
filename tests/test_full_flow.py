#!/usr/bin/env python
"""完整的PPT生成流程测试"""
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from demo import gen_outline, gen_desc, gen_prompts, gen_images_parallel, create_pptx_from_images
from datetime import datetime

print("=" * 70)
print("🍌 即梦 - 完整PPT生成流程测试")
print("=" * 70)
print()

# 1. 生成大纲
print("📝 步骤1: 生成大纲...")
idea_prompt = "生成一份关于量子计算的简短PPT，包括基本概念和应用，共3-5页"
outline = gen_outline(idea_prompt)

pages = []
for item in outline:
    if "part" in item and "pages" in item:
        for page in item["pages"]:
            page_with_part = page.copy()
            page_with_part["part"] = item["part"]
            pages.append(page_with_part)
    else:
        pages.append(item)

print(f"✅ 生成了 {len(pages)} 页大纲")
for i, page in enumerate(pages, 1):
    part = f"[{page.get('part')}] " if 'part' in page else ""
    print(f"  {i}. {part}{page.get('title', 'Untitled')}")
print()

# 2. 生成描述
print("📄 步骤2: 生成页面描述（并行）...")
desc = gen_desc(idea_prompt, outline)
print(f"✅ 生成了 {len(desc)} 页描述")
print()

# 3. 生成提示词
print("🎨 步骤3: 生成图片提示词...")
prompts = gen_prompts(outline, desc)
print(f"✅ 生成了 {len(prompts)} 个提示词")
print()

# 4. 生成图片
print("🖼️  步骤4: 并行生成图片（这需要一些时间）...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"output_{timestamp}"
ref_image = "../template_g.png"

image_files = gen_images_parallel(prompts, ref_image, output_dir)
successful = [f for f in image_files if f is not None]
print(f"✅ 成功生成 {len(successful)}/{len(image_files)} 张图片")
print()

# 5. 导出PPTX
if successful:
    print("📊 步骤5: 生成PPTX文件...")
    pptx_filename = f"presentation_{timestamp}.pptx"
    create_pptx_from_images(output_dir, pptx_filename)
    
    import os
    if os.path.exists(pptx_filename):
        size = os.path.getsize(pptx_filename)
        print(f"✅ ✅ ✅ PPTX文件生成成功！✅ ✅ ✅")
        print(f"文件名: {pptx_filename}")
        print(f"大小: {size/1024/1024:.2f} MB")
        print()
        print("=" * 70)
        print("🎉 完整流程测试成功！PPT已生成！")
        print("=" * 70)
    else:
        print("❌ PPTX文件生成失败")
else:
    print("❌ 没有成功生成的图片，跳过PPTX生成")
