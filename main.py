import os
import sys
from enum import Enum
from pathlib import Path
from lrc_parser import LrcParser
from translator import get_translator, get_default_translator_type

class TranslateResult(Enum):
    Success = 1
    Error = 2
    Skipped = 3
    Reset = 4

class GlobalChoice(Enum):
    Ask = 0
    YesAll = 1
    NoAll = 2

global_choice = GlobalChoice.Ask

def translate_lrc_file(file_path: str, translator) -> TranslateResult:
    global global_choice
    
    parser = LrcParser()
    if not parser.parse_file(file_path):
        print(f"无法解析文件: {file_path}")
        return TranslateResult.Error
    
    lyrics_lines = parser.get_lyrics_lines()
    if not lyrics_lines:
        print(f"文件中没有歌词内容: {file_path}")
        return TranslateResult.Error
    
    if parser.is_already_translated():
        print(f"检测到歌曲已翻译: {file_path}")
        
        if global_choice == GlobalChoice.YesAll:
            user_input = 'y'
        elif global_choice == GlobalChoice.NoAll:
            user_input = 'n'
        else:
            user_input = input("是否恢复成原翻译文本? (y:是 Y:全是, n:否 N:全否): ").strip()
            
            if user_input not in ['y', 'Y', 'n', 'N']:
                print("输入无效，跳过该歌曲")
                return TranslateResult.Skipped
        
        if user_input in ['y', 'Y']:
            if global_choice == GlobalChoice.Ask and user_input == 'Y':
                global_choice = GlobalChoice.YesAll
            
            path = Path(file_path)
            original_dir = path.parent / "original"
            original_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(original_dir / path.name)
            
            if parser.save_restored_original(output_path):
                print(f"已恢复原文并保存到: {output_path}")
                return TranslateResult.Reset
            else:
                print(f"保存恢复文件失败: {output_path}")
                return TranslateResult.Error
        else:
            if global_choice == GlobalChoice.Ask and user_input == 'N':
                global_choice = GlobalChoice.NoAll
            
            print(f"跳过该歌曲: {file_path}")
            return TranslateResult.Skipped
    
    print(f"开始翻译: {file_path}")
    
    translations = translator.translate_lyrics(lyrics_lines)
    
    if parser.update_translation(translations):
        path = Path(file_path)
        new_path = path.parent / "translated" / path.name
        new_path.parent.mkdir(parents=True, exist_ok=True)

        output_path = str(new_path)
        
        if parser.save_lrc(output_path, with_translation=True):
            print(f"翻译完成，保存到: {output_path}")
            return TranslateResult.Success
        else:
            print(f"保存文件失败: {output_path}")
            return TranslateResult.Error
    else:
        print("更新翻译失败")
        return TranslateResult.Error

def translate_lrc_directory(directory: str, translator_type: str = None) -> int:
    if not os.path.isdir(directory):
        print(f"错误：目录不存在或不是目录: {directory}")
        return 0
    
    translator = get_translator(translator_type)
    
    lrc_files = list(Path(directory).rglob('*.lrc'))
    
    if not lrc_files:
        print(f"目录中没有找到LRC文件: {directory}")
        return 0
    
    print(f"在目录 {directory} 中找到 {len(lrc_files)} 个LRC文件")
    
    success_count = 0
    skipped_count = 0
    reset_count = 0
    for lrc_file in lrc_files:
        result = translate_lrc_file(str(lrc_file), translator)
        if result == TranslateResult.Success:
            success_count += 1
        elif result == TranslateResult.Skipped:
            skipped_count += 1
        elif result == TranslateResult.Reset:
            reset_count += 1
    
    print(f"\n翻译完成！成功: {success_count}/{len(lrc_files)}, 跳过: {skipped_count}, 已还原: {reset_count}")
    
    return success_count

def pause_and_exit(code: int = 0):
    print("\n按任意键退出...")
    try:
        import msvcrt
        msvcrt.getch()
    except:
        input()
    sys.exit(code)

def main():
    default_translator = get_default_translator_type()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  将LRC文件或目录拖放到此程序上")
        print("  或通过命令行运行: LrcTranslator.exe <lrc文件或目录路径> [翻译器类型]")
        print("")
        print("翻译器类型:")
        print("  openai - 使用OpenAI API")
        print("  chatgpt - 使用ChatGPT API")
        print("  deepseek - 使用DeepSeek API")
        print(f"  当前默认翻译器: {default_translator}")
        print("")
        print("注意: 请确保.env文件与程序在同一目录下，并配置好API密钥")
        pause_and_exit(1)
    
    path = sys.argv[1]
    translator_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(path):
        print(f"错误：路径不存在: {path}")
        pause_and_exit(1)
    
    if os.path.isfile(path):
        if not path.lower().endswith('.lrc'):
            print("错误：文件必须是LRC格式")
            pause_and_exit(1)
        
        translator = get_translator(translator_type)
        translate_lrc_file(path, translator)
    else:
        translate_lrc_directory(path, translator_type)
    
    pause_and_exit(0)

if __name__ == '__main__':
    main()
