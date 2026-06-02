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

class LrcGroup:
    def __init__(self, times: List[float], text: str, translation: str = ''):
        self.times = times
        self.text = text
        self.translation = translation
    
    def __repr__(self):
        return f"LrcGroup(times={self.times}, text='{self.text}', translation='{self.translation}')"
    
    @staticmethod
    def format_single_time(time: float) -> str:
        minutes = int(time // 60)
        seconds = time % 60
        milliseconds = int((seconds % 1) * 100)
        seconds = int(seconds)
        return f"[{minutes:02d}:{seconds:02d}.{milliseconds:02d}]"
    
    def format_time_tags(self) -> str:
        return ''.join(self.format_single_time(t) for t in self.times)
    
    def to_lrc_lines(self, with_translation: bool = False) -> List[str]:
        lines = []
        time_tags_str = self.format_time_tags()
        lines.append(f"{time_tags_str}{self.text}")
        if with_translation and self.translation:
            lines.append(f"{time_tags_str}{self.translation}")
        return lines

class LrcParser:
    TIME_TAG_PATTERN = re.compile(r'\[(\d{2}):(\d{2})\.(\d{2,3})\]')
    META_TAG_PATTERN = re.compile(r'\[([a-zA-Z]+):(.+)\]')
    
    def __init__(self):
        self.groups: List[LrcGroup] = []
        self.metadata: dict = {}
    
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
        self.groups = []
        self.metadata = {}
        
        lines = content.split('\n')
        temp_lines: List[LrcLine] = []
        
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
                temp_lines.append(LrcLine(total_time, text))
        
        temp_lines.sort(key=lambda x: x.time)
        
        self.groups = []
        i = 0
        while i < len(temp_lines):
            current_line = temp_lines[i]
            times = [current_line.time]
            text = current_line.text
            translation = ''
            
            if i + 1 < len(temp_lines) and abs(current_line.time - temp_lines[i + 1].time) < 0.001:
                translation = temp_lines[i + 1].text
                i += 2
            else:
                i += 1
            
            self.groups.append(LrcGroup(times, text, translation))
        
        self._merge_duplicate_groups()
        return True
    
    def _merge_duplicate_groups(self):
        if not self.groups:
            return
        
        merged: List[LrcGroup] = []
        current_group = self.groups[0]
        
        for group in self.groups[1:]:
            if group.text == current_group.text and group.translation == current_group.translation:
                current_group.times.extend(group.times)
            else:
                current_group.times.sort()
                merged.append(current_group)
                current_group = group
        
        current_group.times.sort()
        merged.append(current_group)
        self.groups = merged
    
    def get_lyrics_text(self) -> str:
        return '\n'.join(group.text for group in self.groups)
    
    def save_lrc(self, file_path: str, with_translation: bool = False) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.metadata.items():
                    f.write(f"[{key.upper()}:{value}]\n")
                
                for group in self.groups:
                    for line in group.to_lrc_lines(with_translation):
                        f.write(line + '\n')
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def save_restored_original(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.metadata.items():
                    f.write(f"[{key.upper()}:{value}]\n")
                
                for group in self.groups:
                    f.write(f"{group.format_time_tags()}{group.text}\n")
            return True
        except Exception as e:
            print(f"保存恢复文件失败: {e}")
            return False
    
    def update_translation(self, translations: List[str]) -> bool:
        if len(translations) != len(self.groups):
            print(f"翻译数量不匹配: 期望 {len(self.groups)} 条，实际 {len(translations)} 条")
            return False
        
        for i, trans in enumerate(translations):
            self.groups[i].translation = trans
        return True
    
    def get_lyrics_lines(self) -> List[str]:
        return [group.text for group in self.groups]
    
    def is_already_translated(self, threshold: int = 5) -> bool:
        if len(self.groups) < 1:
            return False
        
        translated_count = 0
        for group in self.groups:
            if group.translation:
                translated_count += 1
                if translated_count >= threshold:
                    return True
        
        return False
    
    def restore_original(self) -> List[LrcLine]:
        original_lines = []
        for group in self.groups:
            for time in group.times:
                original_lines.append(LrcLine(time, group.text))
        return original_lines
