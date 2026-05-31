from openai import OpenAI

class LLMService:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_meeting_minutes(self, raw_text: str, progress_callback=None) -> str:
        """
        根据识别出来的讲话内容生成结构化会议纪要
        """
        if progress_callback:
            progress_callback("正在请求大模型生成会议纪要...")

        system_prompt = """
你是一个高级会议纪要助手。
用户会提供一份带时间戳和发言人标识的会议录音识别文本。
请你理解、润色并总结会议内容，修复语音识别中可能出现的错别字和重复词汇，忽略无效的口语化语气词（如“啊”、“那个”）。

请提供一份内容详实、结构清晰的 markdown 格式会议纪要。包含以下部分：
1. **会议概述**: 一句话总结会议主题。
2. **发言人要点**: 总结各个发言人的主要观点。
3. **详细内容/议程**: 按逻辑顺序列出讨论的具体内容。
4. **决策与待办**: 会议得出的结果和后续任务分配。
5. **会议流程图**: 如果讨论内容中有明显的业务流程、决策流程或操作步骤，请务必使用 mermaid 代码块（`mermaid`）绘制相应的流程图加以说明。如果没有明显流程，可以总结会议讨论过程的简单思维导图或时序图。

请直接输出 markdown 内容，语言必须极其专业且易读。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                temperature=0.3,
            )
            result = response.choices[0].message.content
            return result
        except Exception as e:
            raise Exception(f"大模型生成纪要失败: {str(e)}")
