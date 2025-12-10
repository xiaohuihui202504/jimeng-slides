#!/usr/bin/env python
"""Direct test of AI service without Flask"""
from dotenv import load_dotenv
import os

# Load .env first
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
from services.ai_service import AIService

def main():
    api_key = os.getenv('GOOGLE_API_KEY')
    api_base = os.getenv('GOOGLE_API_BASE')
    
    print("=" * 60)
    print("即梦后端 AI服务直接测试")
    print("=" * 60)
    print(f"✅ API Key配置: {'是' if api_key else '否'}")
    print(f"✅ API Base: {api_base}")
    print()
    
    # Initialize AI service
    print("🔧 初始化AI服务...")
    ai_service = AIService(api_key, api_base)
    print("✅ AI服务初始化成功")
    print()
    
    # Test outline generation
    print("🎯 测试生成大纲...")
    idea_prompt = "生成一份关于量子计算发展的PPT，包括基本原理、应用场景和未来展望，共5-7页"
    
    try:
        outline = ai_service.generate_outline(idea_prompt)
        print("✅ ✅ ✅ AI大纲生成成功！✅ ✅ ✅")
        print()
        
        # Flatten and display
        pages = ai_service.flatten_outline(outline)
        print(f"📄 生成了 {len(pages)} 页大纲:")
        print()
        
        for i, page in enumerate(pages, 1):
            part = f"[{page.get('part')}] " if 'part' in page else ""
            print(f"{i}. {part}{page.get('title', 'Untitled')}")
            if 'points' in page:
                for point in page['points']:
                    print(f"   - {point}")
            print()
        
        print("=" * 60)
        print("✅ 所有测试通过！AI服务工作正常！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ AI大纲生成失败:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

