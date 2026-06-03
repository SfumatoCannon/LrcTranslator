import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

load_dotenv(get_base_path() / ".env")

class Translator:
    def __init__(self):
        self.target_language = os.getenv('TARGET_LANGUAGE', 'zh')
    
    def translate_lyrics(self, lyrics: List[str]) -> List[str]:
        pass

class OpenAITranslator(Translator):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

    def translate_lyrics(self, lyrics: List[str]) -> List[str]:
        if not self.api_key:
            print("错误：未配置OPENAI_API_KEY")
            return [''] * len(lyrics)

        lyrics_text = '\n'.join(lyrics)
        line_count = len(lyrics)

        prompt = f"""请将以下歌词翻译成{self.target_language}。

要求：
1. 每行歌词翻译成一行，保持原有行数（共{line_count}行）
2. 只返回翻译结果，每行用换行符分隔
3. 不要添加任何解释、编号或额外内容
4. 如果某行只是歌曲的标题等元信息，不要忽略它，正常翻译
5. 翻译后文本的格式严格与原始歌词保持一致，绝对不可添加额外的回车符，也不能添加额外的空行，一个不多一个不少
6. 若某行难以翻译，不要跳过它或输出空行，直接返回该行的原文即可

歌词：
{lyrics_text}"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }

        try:
            print(f"正在翻译 {line_count} 行歌词...")
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                translated_lines = translated_text.split('\n')
                
                while len(translated_lines) < line_count:
                    translated_lines.append('')
                translated_lines = translated_lines[:line_count]
                
                print(f"翻译完成")
                return translated_lines
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return [''] * line_count
        except Exception as e:
            print(f"翻译请求异常: {e}")
            return [''] * line_count

class ChatGPTTranslator(Translator):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('CHATGPT_API_KEY')
        self.api_base = os.getenv('CHATGPT_API_BASE', 'https://api.chatgpt.com/v1')
        self.model = os.getenv('CHATGPT_MODEL', 'gpt-3.5-turbo')

    def translate_lyrics(self, lyrics: List[str]) -> List[str]:
        if not self.api_key:
            print("错误：未配置CHATGPT_API_KEY")
            return [''] * len(lyrics)

        lyrics_text = '\n'.join(lyrics)
        line_count = len(lyrics)

        prompt = f"""Translate the following lyrics to {self.target_language}.

Requirements:
1. Translate each line to one line, keep the same number of lines ({line_count} lines total)
2. Only return the translation, separated by newlines
3. Do not add any explanation, numbering or extra content
4. If a line is just the song title or other metadata, do not ignore it, translate it as well
5. The translated text must have the same format as the original lyrics, with no extra newlines, and one line for each original line
6. If a line is difficult to translate, do not skip it or output an empty line, just return the original line


Lyrics:
{lyrics_text}"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }

        try:
            print(f"正在翻译 {line_count} 行歌词...")
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                translated_lines = translated_text.split('\n')
                
                while len(translated_lines) < line_count:
                    translated_lines.append('')
                translated_lines = translated_lines[:line_count]
                
                print(f"翻译完成")
                return translated_lines
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                return [''] * line_count
        except Exception as e:
            print(f"翻译请求异常: {e}")
            return [''] * line_count

class DeepSeekTranslator(Translator):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    def translate_lyrics(self, lyrics: List[str]) -> List[str]:
        if not self.api_key:
            print("错误：未配置DEEPSEEK_API_KEY")
            return [''] * len(lyrics)

        lyrics_text = '\n'.join(lyrics)
        line_count = len(lyrics)

        prompt = f"""请将以下歌词翻译成{self.target_language}。

要求：
1. 每行歌词翻译成一行，保持原有行数（共{line_count}行）
2. 只返回翻译结果，每行用换行符分隔
3. 不要添加任何解释、编号或额外内容
4. 如果某行只是歌曲的标题等元信息，不要忽略它，正常翻译
5. 翻译后文本的格式严格与原始歌词保持一致，绝对不可添加额外的回车符，也不能添加额外的空行，一个不多一个不少
6. 若某行难以翻译，不要跳过它或输出空行，直接返回该行的原文即可

歌词：
{lyrics_text}"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }

        try:
            print(f"正在翻译 {line_count} 行歌词...")
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                translated_lines = translated_text.split('\n')
                
                while len(translated_lines) < line_count:
                    translated_lines.append('')
                translated_lines = translated_lines[:line_count]
                
                print(f"翻译完成")
                return translated_lines
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return [''] * line_count
        except Exception as e:
            print(f"翻译请求异常: {e}")
            return [''] * line_count

def get_default_translator_type() -> str:
    return os.getenv('DEFAULT_TRANSLATOR', 'openai')

def get_translator(translator_type: str = None) -> Translator:
    if translator_type is None:
        translator_type = get_default_translator_type()
    translator_type = translator_type.lower()
    if translator_type == 'chatgpt':
        return ChatGPTTranslator()
    elif translator_type == 'deepseek':
        return DeepSeekTranslator()
    else:
        return OpenAITranslator()
