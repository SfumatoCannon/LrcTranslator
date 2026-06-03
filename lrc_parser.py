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
        self._raw_lines: List[Tuple[List[float], str]] = []
        self._empty_line_times: List[Tuple[int, List[float]]] = []  # (group_index, times)
    
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
        self._raw_lines = []
        self._empty_line_times = []
        
        lines = content.split('\n')
        
        group_index = 0
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
                # 记录空行的时间戳
                times = []
                for tag in time_tags:
                    minutes = int(tag[0])
                    seconds = int(tag[1])
                    milliseconds = int(tag[2])
                    if len(tag[2]) == 2:
                        milliseconds *= 10
                    total_time = minutes * 60 + seconds + milliseconds / 1000
                    times.append(total_time)
                self._empty_line_times.append((group_index, times))
                continue
            
            times = []
            for tag in time_tags:
                minutes = int(tag[0])
                seconds = int(tag[1])
                milliseconds = int(tag[2])
                if len(tag[2]) == 2:
                    milliseconds *= 10
                total_time = minutes * 60 + seconds + milliseconds / 1000
                times.append(total_time)
            
            self._raw_lines.append((times, text))
            group_index += 1
        
        self.groups = [LrcGroup(times, text, '') for times, text in self._raw_lines]
        return True
    
    def get_lyrics_text(self) -> str:
        return '\n'.join(group.text for group in self.groups)
    
    def save_lrc(self, file_path: str, with_translation: bool = False) -> bool:
        try:
            # 构建空行索引集合，key 为 group_index，value 为 times 列表
            empty_lines_map = {}
            for idx, times in self._empty_line_times:
                if idx not in empty_lines_map:
                    empty_lines_map[idx] = []
                empty_lines_map[idx].extend(times)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.metadata.items():
                    f.write(f"[{key.upper()}:{value}]\n")
                
                for i, group in enumerate(self.groups):
                    # 在当前位置之前插入空行
                    if i in empty_lines_map:
                        for time in empty_lines_map[i]:
                            f.write(LrcGroup.format_single_time(time) + '\n')
                    
                    for line in group.to_lrc_lines(with_translation):
                        f.write(line + '\n')
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def save_restored_original(self, file_path: str) -> bool:
        try:
            # 构建空行索引集合
            empty_lines_map = {}
            for idx, times in self._empty_line_times:
                if idx not in empty_lines_map:
                    empty_lines_map[idx] = []
                empty_lines_map[idx].extend(times)
            
            restored_groups = self._get_restored_groups()
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in self.metadata.items():
                    f.write(f"[{key.upper()}:{value}]\n")
                
                for i, group in enumerate(restored_groups):
                    # 在当前位置之前插入空行
                    if i in empty_lines_map:
                        for time in empty_lines_map[i]:
                            f.write(LrcGroup.format_single_time(time) + '\n')
                    
                    f.write(f"{group.format_time_tags()}{group.text}\n")
            return True
        except Exception as e:
            print(f"保存恢复文件失败: {e}")
            return False
    
    def _get_restored_groups(self) -> List[LrcGroup]:
        temp_lines = []
        for times, text in self._raw_lines:
            for time in times:
                temp_lines.append(LrcLine(time, text))
        
        temp_lines.sort(key=lambda x: x.time)
        
        paired_groups = []
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
            
            paired_groups.append(LrcGroup(times, text, translation))
        
        merged = []
        if paired_groups:
            current_group = paired_groups[0]
            for group in paired_groups[1:]:
                if group.text == current_group.text and group.translation == current_group.translation:
                    current_group.times.extend(group.times)
                else:
                    current_group.times.sort()
                    merged.append(current_group)
                    current_group = group
            current_group.times.sort()
            merged.append(current_group)
        
        return merged
    
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
        temp_lines = []
        for times, text in self._raw_lines:
            for time in times:
                temp_lines.append(LrcLine(time, text))
        
        temp_lines.sort(key=lambda x: x.time)
        
        same_time_count = 0
        i = 0
        while i < len(temp_lines) - 1:
            if abs(temp_lines[i].time - temp_lines[i + 1].time) < 0.001:
                same_time_count += 1
                if same_time_count >= threshold:
                    return True
                i += 2
            else:
                i += 1
        
        return False
    
    def restore_original(self) -> List[LrcLine]:
        restored_groups = self._get_restored_groups()
        original_lines = []
        for group in restored_groups:
            for time in group.times:
                original_lines.append(LrcLine(time, group.text))
        return original_lines
