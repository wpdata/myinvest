"""Livermore AI Advisor using Google ADK."""

import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class LivermoreAdvisor:
    """Livermore AI Advisor using Google Gemini via ADK.

    Note: Google ADK integration is simplified for v0.1.
    In production, this would use the full ADK Agent framework.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """初始化 Livermore Advisor。

        Args:
            model: Gemini 模型名称
        """
        self.model = model
        self.prompt_version = "v1.0.0"

        # 加载 Prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / f"livermore-{self.prompt_version}.md"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_content = f.read()

        # 初始化 Gemini API（简化版，v0.1 使用直接 API 调用）
        try:
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")

            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

    def get_recommendation(
        self,
        symbol: str,
        signal: Dict,
        market_context: Dict,
        portfolio_state: Dict
    ) -> Dict[str, Any]:
        """获取 Livermore Advisor 的投资建议。

        Args:
            symbol: 股票代码
            signal: 量化策略生成的信号
            market_context: 市场上下文
            portfolio_state: 投资组合状态

        Returns:
            {
                "advisor": "Livermore",
                "advisor_version": "v1.0.0",
                "timestamp": "2025-10-14T10:30:00Z",
                "recommendation": "APPROVE" | "REJECT" | "MODIFY",
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": str,
                "key_factors": [str],
                "modifications": dict,
                "historical_precedent": str
            }
        """
        # 构造输入
        agent_input = {
            "symbol": symbol,
            "signal": signal,
            "market_context": market_context,
            "portfolio_state": portfolio_state
        }

        # 构造完整的 Prompt
        full_prompt = f"""{self.prompt_content}

---

Now analyze this input and provide your recommendation:

{json.dumps(agent_input, indent=2, ensure_ascii=False)}

Remember: Respond with ONLY the JSON object, no markdown formatting.
"""

        # 调用 Gemini API
        try:
            response = self.gemini_model.generate_content(full_prompt)
            response_text = response.text.strip()

            # 清理可能的 Markdown 代码块标记
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # 解析 JSON
            advisor_output = json.loads(response_text)

            # 添加元数据
            advisor_output.update({
                "advisor": "Livermore",
                "advisor_version": self.prompt_version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_used": self.model
            })

            return advisor_output

        except json.JSONDecodeError as e:
            # JSON 解析失败，返回降级建议
            print(f"Failed to parse Advisor response: {e}")
            print(f"Raw response: {response_text}")

            return {
                "advisor": "Livermore",
                "advisor_version": self.prompt_version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "recommendation": "REJECT",
                "confidence": "LOW",
                "reasoning": "Failed to parse advisor response, rejecting for safety.",
                "key_factors": ["Advisor API error"],
                "modifications": {},
                "historical_precedent": "",
                "error": str(e)
            }

        except Exception as e:
            # 其他错误
            print(f"Advisor error: {e}")

            return {
                "advisor": "Livermore",
                "advisor_version": self.prompt_version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "recommendation": "REJECT",
                "confidence": "LOW",
                "reasoning": f"Advisor API error: {str(e)}",
                "key_factors": ["API failure"],
                "modifications": {},
                "historical_precedent": "",
                "error": str(e)
            }
