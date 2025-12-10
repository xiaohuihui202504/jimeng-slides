import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { ArrowLeft, Save, ArrowRight, Plus, FileText, Sparkle } from 'lucide-react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Button, Loading, useConfirm, useToast, AiRefineInput, ReferenceFileList, FilePreviewModal } from '@/components/shared';
import { OutlineCard } from '@/components/outline/OutlineCard';
import { useProjectStore } from '@/store/useProjectStore';
import { refineOutline } from '@/api/endpoints';
import type { Page } from '@/types';

// 可排序的卡片包装器
const SortableCard: React.FC<{
  page: Page;
  index: number;
  onUpdate: (data: Partial<Page>) => void;
  onDelete: () => void;
  onClick: () => void;
  isSelected: boolean;
  isAiRefining?: boolean;
}> = (props) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: props.page.id || `page-${props.index}`,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <OutlineCard {...props} dragHandleProps={listeners} />
    </div>
  );
};

export const OutlineEditor: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId } = useParams<{ projectId: string }>();
  const fromHistory = (location.state as any)?.from === 'history';
  const {
    currentProject,
    syncProject,
    updatePageLocal,
    saveAllPages,
    reorderPages,
    deletePageById,
    addNewPage,
    generateOutline,
    isGlobalLoading,
  } = useProjectStore();

  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [isAiRefining, setIsAiRefining] = useState(false);
  const [previewFileId, setPreviewFileId] = useState<string | null>(null);
  const { confirm, ConfirmDialog } = useConfirm();
  const { show, ToastContainer } = useToast();

  // 加载项目数据
  useEffect(() => {
    if (projectId && (!currentProject || currentProject.id !== projectId)) {
      // 直接使用 projectId 同步项目数据
      syncProject(projectId);
    }
  }, [projectId, currentProject, syncProject]);


  // 拖拽传感器配置
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id && currentProject) {
      const oldIndex = currentProject.pages.findIndex((p) => p.id === active.id);
      const newIndex = currentProject.pages.findIndex((p) => p.id === over.id);

      const reorderedPages = arrayMove(currentProject.pages, oldIndex, newIndex);
      reorderPages(reorderedPages.map((p) => p.id).filter((id): id is string => id !== undefined));
    }
  };

  const handleGenerateOutline = async () => {
    if (!currentProject) return;
    
    if (currentProject.pages.length > 0) {
      confirm(
        '已有大纲内容，重新生成将覆盖现有内容，确定继续吗？',
        async () => {
          try {
            await generateOutline();
            // generateOutline 内部已经调用了 syncProject，这里不需要再次调用
          } catch (error) {
            console.error('生成大纲失败:', error);
          }
        },
        { title: '确认重新生成', variant: 'warning' }
      );
      return;
    }
    
    try {
      await generateOutline();
      // generateOutline 内部已经调用了 syncProject，这里不需要再次调用
    } catch (error) {
      console.error('生成大纲失败:', error);
    }
  };

  const handleAiRefineOutline = async (requirement: string, previousRequirements: string[]) => {
    if (!currentProject || !projectId) return;
    
    try {
      const response = await refineOutline(projectId, requirement, previousRequirements);
      await syncProject(projectId);
      show({ 
        message: response.data?.message || '大纲修改成功', 
        type: 'success' 
      });
    } catch (error: any) {
      console.error('修改大纲失败:', error);
      const errorMessage = error?.response?.data?.error?.message 
        || error?.message 
        || '修改失败，请稍后重试';
      show({ message: errorMessage, type: 'error' });
      throw error; // 抛出错误让组件知道失败了
    }
  };

  const selectedPage = currentProject?.pages.find((p) => p.id === selectedPageId);

  if (!currentProject) {
    return <Loading fullscreen message="加载项目中..." />;
  }

  if (isGlobalLoading) {
    return <Loading fullscreen message="生成大纲中..." />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶栏 */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-3 md:px-6 py-2 md:py-3 flex-shrink-0">
        <div className="flex items-center justify-between gap-2 md:gap-4">
          {/* 左侧：Logo 和标题 */}
          <div className="flex items-center gap-2 md:gap-4 flex-shrink-0">
            <Button
              variant="ghost"
              size="sm"
              icon={<ArrowLeft size={16} className="md:w-[18px] md:h-[18px]" />}
              onClick={() => {
                if (fromHistory) {
                  navigate('/history');
                } else {
                  navigate('/');
                }
              }}
              className="flex-shrink-0"
            >
              <span className="hidden sm:inline">返回</span>
            </Button>
            <div className="flex items-center gap-1.5 md:gap-2">
              <span className="text-xl md:text-2xl">🍌</span>
              <span className="text-base md:text-xl font-bold">即梦</span>
            </div>
            <span className="text-gray-400 hidden lg:inline">|</span>
            <span className="text-sm md:text-lg font-semibold hidden lg:inline">编辑大纲</span>
          </div>
          
          {/* 中间：AI 修改输入框 */}
          <div className="flex-1 max-w-xl mx-auto hidden md:block md:-translate-x-2 pr-10">
            <AiRefineInput
              title=""
              placeholder="例如：增加一页关于XXX的内容、删除第3页、合并前两页... · Ctrl+Enter提交"
              onSubmit={handleAiRefineOutline}
              disabled={false}
              className="!p-0 !bg-transparent !border-0"
              onStatusChange={setIsAiRefining}
            />
          </div>
          
          {/* 右侧：操作按钮 */}
          <div className="flex items-center gap-1.5 md:gap-2 flex-shrink-0">
            <Button 
              variant="secondary" 
              size="sm" 
              icon={<Save size={16} className="md:w-[18px] md:h-[18px]" />}
              onClick={async () => await saveAllPages()}
              className="hidden md:inline-flex"
            >
              <span className="hidden lg:inline">保存</span>
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ArrowRight size={16} className="md:w-[18px] md:h-[18px]" />}
              onClick={() => navigate(`/project/${projectId}/detail`)}
              className="text-xs md:text-sm"
            >
              <span className="hidden sm:inline">下一步</span>
              <span className="sm:hidden">→</span>
            </Button>
          </div>
        </div>
        
        {/* 移动端：AI 输入框 */}
        <div className="mt-2 md:hidden">
          <AiRefineInput
            title=""
            placeholder="例如：增加/删除页面... · Ctrl+Enter"
            onSubmit={handleAiRefineOutline}
            disabled={false}
            className="!p-0 !bg-transparent !border-0"
            onStatusChange={setIsAiRefining}
          />
        </div>
      </header>

      {/* 上下文栏 */}
      <div className="bg-banana-50 border-b border-banana-100 px-3 md:px-6 py-2 md:py-3 max-h-32 overflow-y-auto flex-shrink-0">
        <div className="flex items-start gap-1.5 md:gap-2 text-xs md:text-sm">
          {currentProject.creation_type === 'idea' && (
            <span className="font-medium text-gray-700 flex-shrink-0 flex items-center">
              <Sparkle size={12} className="mr-1" /> PPT构想:
              <span className="text-gray-900 font-normal ml-2 break-words whitespace-pre-wrap">{currentProject.idea_prompt}</span>
            </span>
          )}
          {currentProject.creation_type === 'outline' && (
            <span className="font-medium text-gray-700 flex-shrink-0 flex items-center">
              <FileText size={12} className="mr-1" /> 大纲:
              <span className="text-gray-900 font-normal ml-2 break-words whitespace-pre-wrap">{currentProject.outline_text || currentProject.idea_prompt}</span>
            </span>
          )}
          {currentProject.creation_type === 'descriptions' && (
            <span className="font-medium text-gray-700 flex-shrink-0 flex items-center">
              <FileText size={12} className="mr-1" /> 描述:
              <span className="text-gray-900 font-normal ml-2 break-words whitespace-pre-wrap">{currentProject.description_text || currentProject.idea_prompt}</span>
            </span>
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* 左侧：大纲列表 */}
        <div className="flex-1 p-3 md:p-6 overflow-y-auto min-h-0">
          <div className="max-w-4xl mx-auto">
            {/* 操作按钮 */}
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 md:mb-6">
              <Button
                variant="primary"
                icon={<Plus size={16} className="md:w-[18px] md:h-[18px]" />}
                onClick={addNewPage}
                className="w-full sm:w-auto text-sm md:text-base"
              >
                添加页面
              </Button>
              {currentProject.pages.length === 0 ? (
                <Button
                  variant="secondary"
                  onClick={handleGenerateOutline}
                  className="w-full sm:w-auto text-sm md:text-base"
                >
                  {currentProject.creation_type === 'outline' ? '解析大纲' : '自动生成大纲'}
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  onClick={handleGenerateOutline}
                  className="w-full sm:w-auto text-sm md:text-base"
                >
                  {currentProject.creation_type === 'outline' ? '重新解析大纲' : '重新生成大纲'}
                </Button>
              )}
            </div>

            {/* 已上传的文件列表 */}
            <ReferenceFileList
              projectId={projectId || null}
              onFileClick={setPreviewFileId}
              deleteMode="remove"
            />

            {/* 大纲卡片列表 */}
            {currentProject.pages.length === 0 ? (
              <div className="text-center py-20">
                <div className="flex justify-center mb-4">
                  <FileText size={64} className="text-gray-300" />
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  还没有页面
                </h3>
                <p className="text-gray-500 mb-6">
                  点击"添加页面"手动创建，或"自动生成大纲"让 AI 帮你完成
                </p>
              </div>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={currentProject.pages.map((p, idx) => p.id || `page-${idx}`)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-4">
                    {currentProject.pages.map((page, index) => (
                      <SortableCard
                        key={page.id || `page-${index}`}
                        page={page}
                        index={index}
                        onUpdate={(data) => page.id && updatePageLocal(page.id, data)}
                        onDelete={() => page.id && deletePageById(page.id)}
                        onClick={() => setSelectedPageId(page.id || null)}
                        isSelected={selectedPageId === page.id}
                        isAiRefining={isAiRefining}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            )}
          </div>
        </div>

        {/* 右侧：预览 */}
        <div className="hidden md:block w-96 bg-white border-l border-gray-200 p-4 md:p-6 overflow-y-auto flex-shrink-0">
          <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4">预览</h3>
          
          {selectedPage ? (
            <div className="space-y-3 md:space-y-4">
              <div>
                <div className="text-xs md:text-sm text-gray-500 mb-1">标题</div>
                <div className="text-base md:text-lg font-semibold text-gray-900">
                  {selectedPage.outline_content.title}
                </div>
              </div>
              <div>
                <div className="text-xs md:text-sm text-gray-500 mb-2">要点</div>
                <ul className="space-y-1.5 md:space-y-2">
                  {selectedPage.outline_content.points.map((point, idx) => (
                    <li key={idx} className="flex items-start text-sm md:text-base text-gray-700">
                      <span className="mr-2 text-banana-500 flex-shrink-0">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 md:py-10 text-gray-400">
              <div className="text-3xl md:text-4xl mb-2">👆</div>
              <p className="text-sm md:text-base">点击左侧卡片查看详情</p>
            </div>
          )}
        </div>
        
        {/* 移动端预览：底部抽屉 */}
        {selectedPage && (
          <div className="md:hidden fixed inset-x-0 bottom-0 bg-white border-t border-gray-200 p-4 max-h-[50vh] overflow-y-auto shadow-lg z-50">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">预览</h3>
            <div className="space-y-2">
              <div>
                <div className="text-xs text-gray-500 mb-1">标题</div>
                <div className="text-sm font-semibold text-gray-900">
                  {selectedPage.outline_content.title}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">要点</div>
                <ul className="space-y-1">
                  {selectedPage.outline_content.points.map((point, idx) => (
                    <li key={idx} className="flex items-start text-xs text-gray-700">
                      <span className="mr-1.5 text-banana-500 flex-shrink-0">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
      {ConfirmDialog}
      <ToastContainer />
      
      <FilePreviewModal fileId={previewFileId} onClose={() => setPreviewFileId(null)} />
    </div>
  );
};

