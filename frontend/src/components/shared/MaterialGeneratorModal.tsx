import React, { useState, useEffect, useRef } from 'react';
import { Image as ImageIcon, ImagePlus, Upload, X, FolderOpen } from 'lucide-react';
import { Modal, Textarea, Button, useToast, MaterialSelector, Skeleton } from '@/components/shared';
import { generateMaterialImage, getTaskStatus } from '@/api/endpoints';
import { getImageUrl } from '@/api/client';
import { materialUrlToFile } from './MaterialSelector';
import type { Material } from '@/api/endpoints';
import type { Task } from '@/types';

interface MaterialGeneratorModalProps {
  projectId?: string | null; // 可选，如果不提供则生成全局素材
  isOpen: boolean;
  onClose: () => void;
}

/**
 * 素材生成模态卡片
 * - 输入提示词 + 上传参考图
 * - 提示词原样传给文生图模型（不做额外修饰）
 * - 生成结果展示在模态顶部
 * - 结果统一保存在项目下的历史素材库（backend /uploads/{projectId}/materials）
 */
export const MaterialGeneratorModal: React.FC<MaterialGeneratorModalProps> = ({
  projectId,
  isOpen,
  onClose,
}) => {
  const { show } = useToast();
  const [prompt, setPrompt] = useState('');
  const [refImage, setRefImage] = useState<File | null>(null);
  const [extraImages, setExtraImages] = useState<File[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isMaterialSelectorOpen, setIsMaterialSelectorOpen] = useState(false);

  const handleRefImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = (e.target.files && e.target.files[0]) || null;
    if (file) {
      setRefImage(file);
    }
  };

  const handleExtraImagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // 如果还没有主参考图，优先把第一张作为主参考图，其余作为额外参考图
    if (!refImage) {
      const [first, ...rest] = files;
      setRefImage(first);
      if (rest.length > 0) {
        setExtraImages((prev) => [...prev, ...rest]);
      }
    } else {
      setExtraImages((prev) => [...prev, ...files]);
    }
  };

  const removeExtraImage = (index: number) => {
    setExtraImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSelectMaterials = async (materials: Material[]) => {
    try {
      // 将选中的素材转换为File对象
      const files = await Promise.all(
        materials.map((material) => materialUrlToFile(material))
      );

      if (files.length === 0) return;

      // 如果没有主图，优先把第一张设为主参考图
      if (!refImage) {
        const [first, ...rest] = files;
        setRefImage(first);
        if (rest.length > 0) {
          setExtraImages((prev) => [...prev, ...rest]);
        }
      } else {
        setExtraImages((prev) => [...prev, ...files]);
      }

      show({ message: `已添加 ${files.length} 个素材`, type: 'success' });
    } catch (error: any) {
      console.error('加载素材失败:', error);
      show({
        message: '加载素材失败: ' + (error.message || '未知错误'),
        type: 'error',
      });
    }
  };

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const pollMaterialTask = async (taskId: string) => {
    const targetProjectId = projectId || 'global'; // 使用'global'作为Task的project_id
    const maxAttempts = 60; // 最多轮询60次（约2分钟）
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const response = await getTaskStatus(targetProjectId, taskId);
        const task: Task = response.data;

        if (task.status === 'COMPLETED') {
          // 任务完成，从progress中获取结果
          const progress = task.progress || {};
          const imageUrl = progress.image_url;
          
          if (imageUrl) {
            setPreviewUrl(getImageUrl(imageUrl));
            const message = projectId 
              ? '素材生成成功，已保存到历史素材库' 
              : '素材生成成功，已保存到全局素材库';
            show({ message, type: 'success' });
          } else {
            show({ message: '素材生成完成，但未找到图片地址', type: 'error' });
          }
          
          setIsGenerating(false);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        } else if (task.status === 'FAILED') {
          show({
            message: task.error_message || '素材生成失败',
            type: 'error',
          });
          setIsGenerating(false);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        } else if (task.status === 'PENDING' || task.status === 'PROCESSING') {
          // 继续轮询
          if (attempts >= maxAttempts) {
            show({ message: '素材生成超时，请稍后查看素材库', type: 'warning' });
            setIsGenerating(false);
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        }
      } catch (error: any) {
        console.error('轮询任务状态失败:', error);
        if (attempts >= maxAttempts) {
          show({ message: '轮询任务状态失败，请稍后查看素材库', type: 'error' });
          setIsGenerating(false);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      }
    };

    // 立即执行一次，然后每2秒轮询一次
    poll();
    pollingIntervalRef.current = setInterval(poll, 2000);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      show({ message: '请输入提示词', type: 'error' });
      return;
    }

    setIsGenerating(true);
    try {
      // 如果没有projectId，使用'none'表示生成全局素材（后端会转换为'global'用于Task）
      const targetProjectId = projectId || 'none';
      const resp = await generateMaterialImage(targetProjectId, prompt.trim(), refImage as File, extraImages);
      const taskId = resp.data?.task_id;
      
      if (taskId) {
        // 开始轮询任务状态
        await pollMaterialTask(taskId);
      } else {
        show({ message: '素材生成失败：未返回任务ID', type: 'error' });
        setIsGenerating(false);
      }
    } catch (error: any) {
      show({
        message: error?.response?.data?.error?.message || error.message || '素材生成失败',
        type: 'error',
      });
      setIsGenerating(false);
    }
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="素材生成" size="lg">
      <blockquote className="text-sm text-gray-500 mb-4">生成的素材会保存到素材库</blockquote>
      <div className="space-y-4">
        {/* 顶部：生成结果预览（始终显示最新一次生成） */}
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">生成结果</h4>
          {isGenerating ? (
            <div className="aspect-video rounded-lg overflow-hidden border border-gray-200">
              <Skeleton className="w-full h-full" />
            </div>
          ) : previewUrl ? (
            <div className="aspect-video bg-white rounded-lg overflow-hidden border border-gray-200 flex items-center justify-center">
              <img
                src={previewUrl}
                alt="生成的素材"
                className="w-full h-full object-contain"
              />
            </div>
          ) : (
            <div className="aspect-video bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-400 text-sm">
              <div className="text-3xl mb-2">🎨</div>
              <div>生成的素材会展示在这里</div>
            </div>
          )}
        </div>

        {/* 提示词：原样传给模型 */}
        <Textarea
          label="提示词（原样发送给文生图模型）"
          placeholder="例如：蓝紫色渐变背景，带几何图形和科技感线条，用于科技主题标题页..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
        />

        {/* 参考图上传区 */}
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-700">
              <ImagePlus size={16} className="text-gray-500" />
              <span className="font-medium">参考图片（可选）</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              icon={<FolderOpen size={16} />}
              onClick={() => setIsMaterialSelectorOpen(true)}
            >
              从素材库选择
            </Button>
          </div>
          <div className="flex flex-wrap gap-4">
            {/* 主参考图（可选） */}
            <div className="space-y-2">
              <div className="text-xs text-gray-600">主参考图（可选）</div>
              <label className="w-40 h-28 border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center cursor-pointer hover:border-banana-500 transition-colors bg-white relative group">
                {refImage ? (
                  <>
                    <img
                      src={URL.createObjectURL(refImage)}
                      alt="主参考图"
                      className="w-full h-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setRefImage(null);
                      }}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow z-10"
                    >
                      <X size={12} />
                    </button>
                  </>
                ) : (
                  <>
                    <ImageIcon size={24} className="text-gray-400 mb-1" />
                    <span className="text-xs text-gray-500">点击上传</span>
                  </>
                )}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleRefImageChange}
                />
              </label>
            </div>

            {/* 额外参考图（可选） */}
            <div className="flex-1 space-y-2 min-w-[180px]">
              <div className="text-xs text-gray-600">额外参考图（可选，多张）</div>
              <div className="flex flex-wrap gap-2">
                {extraImages.map((file, idx) => (
                  <div key={idx} className="relative group">
                    <img
                      src={URL.createObjectURL(file)}
                      alt={`extra-${idx + 1}`}
                      className="w-20 h-20 object-cover rounded border border-gray-300"
                    />
                    <button
                      onClick={() => removeExtraImage(idx)}
                      className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
                <label className="w-20 h-20 border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center cursor-pointer hover:border-banana-500 transition-colors bg-white">
                  <Upload size={18} className="text-gray-400 mb-1" />
                  <span className="text-[11px] text-gray-500">添加</span>
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={handleExtraImagesChange}
                  />
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="ghost" onClick={handleClose} disabled={isGenerating}>
            关闭
          </Button>
          <Button
            variant="primary"
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating ? '生成中...' : '生成素材'}
          </Button>
        </div>
      </div>
      {/* 素材选择器 */}
      <MaterialSelector
        projectId={projectId}
        isOpen={isMaterialSelectorOpen}
        onClose={() => setIsMaterialSelectorOpen(false)}
        onSelect={handleSelectMaterials}
        multiple={true}
      />
    </Modal>
  );
};


