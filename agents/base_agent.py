"""
Agent基础框架
为所有专业Agent提供统一的基础结构和接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import time
from anthropic import Anthropic

from utils import settings, get_agent_logger, AgentResponse, Timer, retry_with_backoff
from knowledge_base import knowledge_manager

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_agent_logger(name)
        self.anthropic_client = Anthropic(api_key=settings.claude_api_key)
        
        # 性能统计
        self.total_requests = 0
        self.total_processing_time = 0.0
        self.success_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理输入数据，子类必须实现"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词，子类必须实现"""
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResponse:
        """执行Agent处理流程"""
        with Timer() as timer:
            self.logger.info(f"开始处理: {self.name}")
            self.total_requests += 1
            
            try:
                # 输入验证
                if not await self.validate_input(input_data):
                    error_msg = "输入数据验证失败"
                    self.logger.error(error_msg)
                    self.error_count += 1
                    return AgentResponse(
                        success=False,
                        message=error_msg,
                        processing_time=timer.get_elapsed(),
                        agent_name=self.name
                    )
                
                # 执行前置处理
                preprocessed_data = await self.preprocess(input_data)
                
                # 核心处理逻辑
                result = await self.process(preprocessed_data)
                
                # 执行后置处理
                if result.success:
                    result = await self.postprocess(result)
                
                # 更新统计信息
                if result.success:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                self.total_processing_time += timer.get_elapsed()
                result.processing_time = timer.get_elapsed()
                
                self.logger.info(f"处理完成: {self.name}, 耗时: {timer.get_elapsed():.2f}s")
                return result
                
            except Exception as e:
                error_msg = f"Agent执行异常: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                self.error_count += 1
                
                return AgentResponse(
                    success=False,
                    message=error_msg,
                    processing_time=timer.get_elapsed(),
                    agent_name=self.name
                )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据，子类可以重写"""
        return input_data is not None
    
    async def preprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """前置处理，子类可以重写"""
        return input_data
    
    async def postprocess(self, result: AgentResponse) -> AgentResponse:
        """后置处理，子类可以重写"""
        return result
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def call_claude_api(self, messages: List[Dict[str, str]], 
                             max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """调用Claude API"""
        try:
            system_prompt = self.get_system_prompt()
            
            response = self.anthropic_client.messages.create(
                model=settings.claude_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude API调用失败: {e}")
            raise
    
    async def search_knowledge_base(self, query: str, category: Optional[str] = None, 
                                   n_results: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库"""
        try:
            return knowledge_manager.search_knowledge(
                query=query,
                category=category,
                n_results=n_results
            )
        except Exception as e:
            self.logger.error(f"知识库搜索失败: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        avg_processing_time = (
            self.total_processing_time / self.total_requests 
            if self.total_requests > 0 else 0
        )
        
        success_rate = (
            self.success_count / self.total_requests 
            if self.total_requests > 0 else 0
        )
        
        return {
            "agent_name": self.name,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_processing_time
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_requests = 0
        self.total_processing_time = 0.0
        self.success_count = 0
        self.error_count = 0

class TextProcessingAgent(BaseAgent):
    """文本处理Agent基类"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证文本输入"""
        content = input_data.get("content", "")
        if not content or not content.strip():
            return False
        
        # 检查文本长度
        if len(content) > settings.max_content_length:
            self.logger.warning(f"文本长度超限: {len(content)} > {settings.max_content_length}")
            return False
        
        return True
    
    def extract_knowledge_context(self, search_results: List[Dict[str, Any]]) -> str:
        """从搜索结果中提取知识上下文"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(search_results[:3]):  # 只取前3个最相关的结果
            content = result.get("content", "").strip()
            if content:
                context_parts.append(f"参考{i+1}: {content}")
        
        return "\n\n".join(context_parts)

class LLMAgent(TextProcessingAgent):
    """基于LLM的Agent基类"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
    
    async def process_with_llm(self, user_prompt: str, context: str = "") -> str:
        """使用LLM处理文本"""
        messages = []
        
        if context:
            messages.append({
                "role": "user",
                "content": f"上下文信息：\n{context}\n\n任务：\n{user_prompt}"
            })
        else:
            messages.append({
                "role": "user", 
                "content": user_prompt
            })
        
        return await self.call_claude_api(messages)
    
    async def process_with_knowledge_base(self, content: str, query: str, 
                                        category: Optional[str] = None) -> str:
        """结合知识库处理文本"""
        # 搜索相关知识
        knowledge_results = await self.search_knowledge_base(
            query=query,
            category=category
        )
        
        # 构建上下文
        knowledge_context = self.extract_knowledge_context(knowledge_results)
        
        # 构建提示词
        if knowledge_context:
            user_prompt = f"""请基于以下知识库信息处理文本：

知识库信息：
{knowledge_context}

待处理文本：
{content}

处理要求：
{query}
"""
        else:
            user_prompt = f"""待处理文本：
{content}

处理要求：
{query}
"""
        
        return await self.process_with_llm(user_prompt)

class AgentPipeline:
    """Agent流水线"""
    
    def __init__(self, name: str):
        self.name = name
        self.agents: List[BaseAgent] = []
        self.logger = get_agent_logger(f"Pipeline-{name}")
    
    def add_agent(self, agent: BaseAgent):
        """添加Agent到流水线"""
        self.agents.append(agent)
        self.logger.info(f"已添加Agent: {agent.name}")
    
    def remove_agent(self, agent_name: str) -> bool:
        """从流水线中移除Agent"""
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                removed_agent = self.agents.pop(i)
                self.logger.info(f"已移除Agent: {removed_agent.name}")
                return True
        return False
    
    async def execute_pipeline(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行整个流水线"""
        with Timer() as timer:
            self.logger.info(f"开始执行流水线: {self.name}")
            
            current_data = input_data.copy()
            pipeline_results = {
                "pipeline_name": self.name,
                "start_time": datetime.now().isoformat(),
                "agent_results": [],
                "final_data": None,
                "success": True,
                "total_processing_time": 0.0
            }
            
            try:
                for agent in self.agents:
                    agent_result = await agent.execute(current_data)
                    pipeline_results["agent_results"].append({
                        "agent_name": agent.name,
                        "success": agent_result.success,
                        "message": agent_result.message,
                        "processing_time": agent_result.processing_time
                    })
                    
                    if not agent_result.success:
                        pipeline_results["success"] = False
                        pipeline_results["error"] = f"Agent {agent.name} 执行失败: {agent_result.message}"
                        break
                    
                    # 将当前Agent的结果作为下一个Agent的输入
                    if agent_result.data:
                        current_data.update(agent_result.data)
                
                pipeline_results["final_data"] = current_data
                pipeline_results["end_time"] = datetime.now().isoformat()
                pipeline_results["total_processing_time"] = timer.get_elapsed()
                
                self.logger.info(f"流水线执行完成: {self.name}, 耗时: {timer.get_elapsed():.2f}s")
                return pipeline_results
                
            except Exception as e:
                error_msg = f"流水线执行异常: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                pipeline_results["success"] = False
                pipeline_results["error"] = error_msg
                pipeline_results["end_time"] = datetime.now().isoformat()
                pipeline_results["total_processing_time"] = timer.get_elapsed()
                
                return pipeline_results
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """获取流水线统计信息"""
        agent_stats = [agent.get_performance_stats() for agent in self.agents]
        
        return {
            "pipeline_name": self.name,
            "agent_count": len(self.agents),
            "agent_stats": agent_stats
        }