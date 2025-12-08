"""
Claude API client for code translation.

Handles interactions with Anthropic's Claude API for intelligent code translation.
"""

from typing import Dict, Any, List, Optional
import os

from anthropic import Anthropic, APIError

from transmute.core.state import TranslationUnit, FeatureProfile
from transmute.core.config import LLMConfig
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Client for Anthropic's Claude API.
    
    Provides intelligent code translation using Claude models.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize Claude client.
        
        Args:
            config: LLM configuration (uses env var ANTHROPIC_API_KEY if not provided)
        """
        self.config = config or LLMConfig()
        
        # Get API key
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var or provide in config."
            )
        
        self.client = Anthropic(api_key=api_key)
        
        logger.info(f"Initialized Claude client with model: {self.config.model}")
    
    def translate_code(
        self,
        source_code: str,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None,
        context_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Translate code using Claude.
        
        Args:
            source_code: Source code to translate
            source_language: Source language name
            target_language: Target language name
            feature_profile: Optional feature profile for context
            context_patterns: Optional similar patterns from RAG
            
        Returns:
            Dictionary with translated_code, confidence, explanation
            
        Example:
            >>> client = ClaudeClient()
            >>> result = client.translate_code(
            ...     "def hello():\n    print('Hello')",
            ...     "python",
            ...     "java"
            ... )
            >>> print(result['translated_code'])
        """
        logger.info(f"Translating {source_language} -> {target_language}")
        
        # Build prompt
        prompt = self._build_translation_prompt(
            source_code=source_code,
            source_language=source_language,
            target_language=target_language,
            feature_profile=feature_profile,
            context_patterns=context_patterns
        )
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response
            response_text = response.content[0].text
            
            # Parse response
            result = self._parse_translation_response(response_text)
            
            logger.info("Translation successful")
            
            return result
            
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def _build_translation_prompt(
        self,
        source_code: str,
        source_language: str,
        target_language: str,
        feature_profile: Optional[FeatureProfile] = None,
        context_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build translation prompt for Claude.
        
        Args:
            source_code: Source code
            source_language: Source language
            target_language: Target language
            feature_profile: Feature profile
            context_patterns: Similar patterns from RAG
            
        Returns:
            Formatted prompt
        """
        prompt_parts = [
            f"You are an expert code translator. Translate the following {source_language} code to {target_language}.",
            "",
            "Requirements:",
            f"- Maintain the same functionality and logic",
            f"- Follow {target_language} best practices and conventions",
            f"- Preserve variable names where possible (convert to {target_language} naming conventions)",
            f"- Add appropriate type hints/annotations for {target_language}",
            f"- Ensure idiomatic {target_language} code",
            "",
        ]
        
        # Add feature context
        if feature_profile:
            features = ", ".join(list(feature_profile.features_used.keys())[:5])
            prompt_parts.extend([
                f"Code features to preserve: {features}",
                f"Complexity level: {feature_profile.complexity_score:.2f}/1.0",
                "",
            ])
        
        # Add similar patterns from RAG
        if context_patterns:
            prompt_parts.append("Reference examples of similar translations:")
            prompt_parts.append("")
            
            for i, pattern in enumerate(context_patterns[:3], 1):
                prompt_parts.append(f"Example {i}:")
                prompt_parts.append(f"Source ({source_language}):")
                prompt_parts.append(f"```{source_language}")
                prompt_parts.append(pattern['source_code'][:200])
                prompt_parts.append("```")
                prompt_parts.append(f"Target ({target_language}):")
                prompt_parts.append(f"```{target_language}")
                prompt_parts.append(pattern['target_code'][:200])
                prompt_parts.append("```")
                prompt_parts.append("")
        
        # Add source code
        prompt_parts.extend([
            f"Translate this {source_language} code:",
            "",
            f"```{source_language}",
            source_code,
            "```",
            "",
            "Provide your response in the following format:",
            "",
            "TRANSLATED_CODE:",
            f"```{target_language}",
            "// Your translated code here",
            "```",
            "",
            "CONFIDENCE: X.XX (0.0-1.0)",
            "",
            "EXPLANATION:",
            "Brief explanation of translation choices and any important notes.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_translation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's translation response.
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Dictionary with translated_code, confidence, explanation
        """
        result = {
            'translated_code': '',
            'confidence': 0.8,  # Default
            'explanation': ''
        }
        
        # Extract code block
        import re
        
        # Find code between ```language and ```
        code_pattern = r'```(?:\w+)?\n(.*?)```'
        code_matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        if code_matches:
            # Get the first code block after TRANSLATED_CODE:
            result['translated_code'] = code_matches[0].strip()
        else:
            # Fallback: try to find any code-like content
            result['translated_code'] = response_text.strip()
        
        # Extract confidence
        confidence_pattern = r'CONFIDENCE:\s*(\d+\.?\d*)'
        confidence_match = re.search(confidence_pattern, response_text)
        
        if confidence_match:
            try:
                result['confidence'] = float(confidence_match.group(1))
            except ValueError:
                pass
        
        # Extract explanation
        explanation_pattern = r'EXPLANATION:\s*(.+?)(?:\n\n|\Z)'
        explanation_match = re.search(explanation_pattern, response_text, re.DOTALL)
        
        if explanation_match:
            result['explanation'] = explanation_match.group(1).strip()
        
        return result
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4