import re
from typing import List, Tuple, Optional

def detect_encoding(file_path: str) -> str:
    encodings = [
        'utf-8', 
        'utf-8-sig',
        'gbk', 
        'gb2312', 
        'cp936',
        'big5', 
        'cp950',
        'utf-16',
        'cp1252',
        'cp1251',
        'cp1250',
        'cp1256',
        'cp1253',
        'cp850',
        'cp852'
    ]
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    return 'utf-8'

class LrcLine:
    def __init__(self, time: float, text: str):
        self.time = time
        self.text = text
    
    def __repr__(self):
        return f"LrcLine(time={self.time:.2f}, text='{self.text}')"
    
    def format_time(self) -> str:
        minutes = int(self.time // 60)
        seconds = self.time % 60
        milliseconds = int((seconds % 1) * 100)
        seconds = int(seconds)
        return f"[{minutes:02d}:{seconds:02d}.{milliseconds:02d}]"
    
    def to_lrc_line(self) -> str:
        return f"{self.format_time()}{self.text}"

class LrcParser:
    TIME_TAG_PATTERN = re.compile(r'\[(\d{2}):(\d{2})\.(\d{2,3})\]')
    META_TAG_PATTERN = re.compile(r'\[([a-zA-Z]+):(.+)\]')
    
    def __init__(self):
        self.lines: List[LrcLine] = []
        self.metadata: dict = {}
        self.translated_lines: List[str] = []
    
    def parse_file(self, file_path: str) -> bool:
        try:
            encoding = detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return self.parse_content(content)
        except Exception as e:
            print(f"读取文件失败: {e}")
            return False
    
    def parse_content(self, content: str) -> bool:
        self.lines = []
        self.metadata = {}
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            meta_match = self.META_TAG_PATTERN.match(line)
            if meta_match:
                key = meta_match.group(1).lower()
                value = meta_match.group(2)
                self.metadata[key] = value
                continue
            
            time_tags = self.TIME_TAG_PATTERN.findall(line)
            if not time_tags:
                continue
            
            text = self.TIME_TAG_PATTERN.sub('', line).strip()
            if not text:
                continue
            
            for tag in time_tags:
                minutes = int(tag[0])
                seconds = int(tag[1])
                milliseconds = int(tag[2])
                if len(tag[2]) == 2:
                    milliseconds *= 10
                total_time = minutes * 60 + seconds + milliseconds / 1000
                self.lines.append(LrcLine(total_time, text))
        
        self.lines.sort(key=lambda x: x.time)
        return True
    
    def get_lyrics_text(self) -> str:
        return '\n'.join(line.text for line in self.lines)
    
    def save_lrc(self, file_path: str, with_translation: bool = False) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.metadata.items():
                    f.write(f"[{key.upper()}:{value}]\n")
                
                if with_translation and self.translated_lines:
                    for i, line in enumerate(self.lines):
                        f.write(line.to_lrc_line() + '\n')
                        if i < len(self.translated_lines) and self.translated_lines[i]:
                            f.write(f"{line.format_time()}{self.translated_lines[i]}\n")
                else:
                    for line in self.lines:
                        f.write(line.to_lrc_line() + '\n')
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def update_translation(self, translations: List[str]) -> bool:
        if len(translations) != len(self.lines):
            print(f"翻译数量不匹配: 期望 {len(self.lines)} 条，实际 {len(translations)} 条")
            return False
        
        self.translated_lines = translations
        return True
    
    def get_lyrics_lines(self) -> List[str]:
        return [line.text for line in self.lines]
    
    def is_already_translated(self, threshold: int = 5) -> bool:
        """
        检测歌曲是否已被翻译
        判断依据：连续两行出现相同的时间标签则计数器+1，计数器达到threshold则判定被翻译
        
        Args:
            threshold: 判定阈值，默认5次连续相同时间标签
        
        Returns:
            bool: True表示已被翻译，False表示未被翻译
        """
        if len(self.lines) < 2:
            return False
        
        same_time_count = 0
        
        for i in range(len(self.lines) - 1):
            current_time = self.lines[i].time
            next_time = self.lines[i + 1].time
            
            if abs(current_time - next_time) < 0.001:
                same_time_count += 1
                if same_time_count >= threshold:
                    return True
        
        return False
