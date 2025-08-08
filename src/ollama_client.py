"""Ollama原生API适配器 - 将OpenAI SDK调用转换为Ollama原生/api/generate接口"""

import httpx
import logging
import json
import time
import uuid
from typing import Any, Dict, AsyncGenerator, Optional, List
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

logger = logging.getLogger(__name__)


class OllamaAsyncOpenAI:
    """
    Ollama原生API适配器
    将OpenAI SDK格式的请求转换为Ollama原生/api/generate接口调用
    即使Ollama只部署了原生API，也能通过OpenAI SDK访问
    """
    
    def __init__(self, base_url: str, api_key: str):
        # 移除/v1后缀，使用原生API端点
        self.base_url = base_url.rstrip('/').replace('/v1', '')
        self.api_key = api_key
        
        # 创建HTTP客户端
        self._http_client = httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(300.0)  # Ollama生成可能需要较长时间
        )
        
        # 创建chat接口
        self.chat = ChatCompletions(self)
        
        logger.info(f"🔄 OllamaAsyncOpenAI (Native API Adapter) initialized")
        logger.info(f"📍 Target: {self.base_url}/api/generate")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()
    
    async def close(self):
        """关闭HTTP客户端"""
        await self._http_client.aclose()


class ChatCompletions:
    """Chat completions接口适配器"""
    
    def __init__(self, client: OllamaAsyncOpenAI):
        self.client = client
    
    @property
    def completions(self):
        """返回completions接口"""
        return Completions(self.client)


class Completions:
    """Completions接口实现 - OpenAI到Ollama原生API的核心适配器"""
    
    def __init__(self, client: OllamaAsyncOpenAI):
        self.client = client
    
    async def create(self, **kwargs) -> Any:
        """
        创建chat completion请求 - 转换为Ollama原生/api/generate调用
        """
        logger.info(f"🔄 === OpenAI -> Ollama Native API Conversion ===")
        logger.info(f"📍 Target: {self.client.base_url}/api/generate")
        logger.info(f"🤖 Model: {kwargs.get('model', 'Unknown')}")
        logger.info(f"📡 Stream: {kwargs.get('stream', False)}")
        
        # 转换OpenAI格式到Ollama原生格式
        ollama_request = self._convert_openai_to_ollama(kwargs)
        
        # 构建请求URL - 使用Ollama原生API端点
        url = f"{self.client.base_url}/api/generate"
        
        # 设置请求头
        headers = {
            'Content-Type': 'application/json',
        }
        
        try:
            logger.info(f"📤 Sending request to: {url}")
            logger.info(f"📋 Ollama request: {json.dumps(ollama_request, indent=2, ensure_ascii=False)}")
            
            # 发送请求到Ollama原生API
            response = await self.client._http_client.post(
                url,
                headers=headers,
                json=ollama_request
            )
            
            response.raise_for_status()
            logger.info(f"✅ Ollama native API call successful - Status: {response.status_code}")
            
            # 处理响应
            if ollama_request.get('stream', False):
                return await self._handle_stream_response(response, kwargs)
            else:
                # 非流式响应
                result = response.json()
                return self._convert_ollama_to_openai(result, kwargs)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ollama Native API Error: {e.response.status_code}")
            logger.error(f"📍 Request URL: {e.request.url}")
            logger.error(f"📄 Response text: {e.response.text}")
            
            if e.response.status_code == 400:
                logger.error(f"🔍 400 Bad Request Analysis:")
                logger.error(f"  - Check if model '{kwargs.get('model')}' is available: ollama list")
                logger.error(f"  - Verify Ollama service is running: ollama serve")
                logger.error(f"  - Check if /api/generate endpoint is accessible")
                
                # 尝试解析错误响应
                try:
                    error_data = e.response.json()
                    logger.error(f"  - Ollama error details: {error_data}")
                except:
                    pass
            
            raise
        except Exception as e:
            logger.error(f"❌ Ollama native API call failed: {str(e)}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            raise
    
    def _convert_openai_to_ollama(self, openai_params: dict) -> dict:
        """将OpenAI格式的请求转换为Ollama原生API格式"""
        logger.info(f"🔄 Converting OpenAI format to Ollama native format")
        
        # 提取基本参数
        model = openai_params.get('model')
        messages = openai_params.get('messages', [])
        stream = openai_params.get('stream', False)
        
        # 验证必需参数
        if not model:
            raise ValueError("Model is required")
        if not messages:
            raise ValueError("Messages are required")
        
        # 将messages转换为单个prompt
        prompt = self._messages_to_prompt(messages)
        
        # 构建Ollama原生API请求
        ollama_request = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        # 添加可选参数
        if 'temperature' in openai_params:
            ollama_request['options'] = ollama_request.get('options', {})
            ollama_request['options']['temperature'] = openai_params['temperature']
        
        if 'max_tokens' in openai_params:
            ollama_request['options'] = ollama_request.get('options', {})
            ollama_request['options']['num_predict'] = openai_params['max_tokens']
        
        # 添加其他Ollama支持的参数
        if 'top_p' in openai_params:
            ollama_request['options'] = ollama_request.get('options', {})
            ollama_request['options']['top_p'] = openai_params['top_p']
        
        logger.info(f"✅ Converted to Ollama format: model={model}, prompt_length={len(prompt)}")
        return ollama_request
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """将OpenAI messages格式转换为单个prompt字符串"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            else:
                # 未知角色，直接添加内容
                prompt_parts.append(content)
        
        # 添加最后的Assistant提示
        prompt_parts.append("Assistant:")
        
        prompt = "\n\n".join(prompt_parts)
        logger.info(f"📝 Converted {len(messages)} messages to prompt ({len(prompt)} chars)")
        return prompt
    
    def _convert_ollama_to_openai(self, ollama_response: dict, original_params: dict) -> ChatCompletion:
        """将Ollama原生API响应转换为OpenAI格式"""
        logger.info(f"🔄 Converting Ollama response to OpenAI format")
        
        # 提取响应内容
        response_text = ollama_response.get('response', '')
        model = ollama_response.get('model', original_params.get('model', 'unknown'))
        
        # 创建OpenAI格式的响应
        completion = ChatCompletion(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=self._create_usage_stats(ollama_response)
        )
        
        logger.info(f"✅ Converted to OpenAI format: {len(response_text)} chars")
        return completion
    
    def _create_usage_stats(self, ollama_response: dict) -> CompletionUsage:
        """从Ollama响应创建使用统计"""
        # Ollama原生API可能包含token统计信息
        prompt_tokens = ollama_response.get('prompt_eval_count', 0)
        completion_tokens = ollama_response.get('eval_count', 0)
        total_tokens = prompt_tokens + completion_tokens
        
        return CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    
    async def _handle_stream_response(self, response: httpx.Response, original_params: dict) -> AsyncGenerator[ChatCompletionChunk, None]:
        """处理Ollama流式响应并转换为OpenAI格式"""
        logger.info(f"🌊 Handling Ollama stream response")
        
        async for line in response.aiter_lines():
            if line.strip():
                try:
                    # 解析Ollama流式响应
                    ollama_chunk = json.loads(line)
                    
                    # 转换为OpenAI格式的chunk
                    openai_chunk = self._convert_ollama_chunk_to_openai(ollama_chunk, original_params)
                    if openai_chunk:
                        yield openai_chunk
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse stream line: {line}")
                    continue
    
    def _convert_ollama_chunk_to_openai(self, ollama_chunk: dict, original_params: dict) -> Optional[ChatCompletionChunk]:
        """将Ollama流式chunk转换为OpenAI格式"""
        response_text = ollama_chunk.get('response', '')
        done = ollama_chunk.get('done', False)
        
        if response_text or done:
            from openai.types.chat.chat_completion_chunk import ChoiceDelta
            from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
            
            chunk = ChatCompletionChunk(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                object="chat.completion.chunk",
                created=int(time.time()),
                model=ollama_chunk.get('model', original_params.get('model', 'unknown')),
                choices=[
                    ChunkChoice(
                        index=0,
                        delta=ChoiceDelta(
                            content=response_text if not done else None
                        ),
                        finish_reason="stop" if done else None
                    )
                ]
            )
            return chunk
        
        return None


# Ollama原生API适配器实现完成
# 支持将OpenAI SDK调用转换为Ollama原生/api/generate接口
# 即使Ollama只部署了原生API，也能通过OpenAI SDK访问
