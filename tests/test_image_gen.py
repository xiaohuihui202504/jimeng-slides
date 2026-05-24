from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from gemini_genai import gen_image

print("=== 测试图片生成 ===")
print()

prompt = """
利用专业平面设计知识，根据参考图片的色彩与风格生成一页设计风格相同的ppt页面，内容是:

页面标题：量子计算简介
页面文字：
- 量子计算是利用量子力学现象进行信息处理的新型计算范式
- 突破经典计算的限制，开启科技新纪元
- 核心：量子叠加与量子纠缠

要求文字清晰锐利，画面为4k分辨率 16:9比例。画面风格与配色保持严格一致。ppt使用全中文。
"""

print("提示词:")
print(prompt)
print()

try:
    print("🎨 开始生成图片...")
    image = gen_image(prompt, "../template_g.png")
    
    if image:
        print("✅ 图片生成成功！")
        output_file = "test_output.png"
        image.save(output_file)
        print(f"已保存到: {output_file}")
        
        # 检查文件
        import os
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"文件大小: {size/1024:.1f} KB")
    else:
        print("❌ 图片生成失败 - 返回None")
        
except Exception as e:
    print(f"❌ 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
