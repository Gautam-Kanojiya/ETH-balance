"""
声音播放模块
负责播放报警声音
"""

import os
import time
import threading
import platform
import logging
from typing import Optional


class SoundPlayer:
    """声音播放器"""
    
    def __init__(self):
        """初始化声音播放器"""
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self._is_playing = False
        
        # 检测系统支持的声音播放方式
        self._setup_sound_system()
    
    def _setup_sound_system(self) -> None:
        """设置系统声音播放方式"""
        self.sound_method = None
        
        if self.system == "Darwin":  # macOS
            if self._command_exists("afplay"):
                self.sound_method = "afplay"
                self.logger.info("🔊 使用 afplay 播放声音 (macOS)")
            else:
                self.sound_method = "system_beep"
                self.logger.info("🔊 使用系统提示音 (macOS)")
        
        elif self.system == "Linux":
            if self._command_exists("aplay"):
                self.sound_method = "aplay"
                self.logger.info("🔊 使用 aplay 播放声音 (Linux)")
            elif self._command_exists("paplay"):
                self.sound_method = "paplay"
                self.logger.info("🔊 使用 paplay 播放声音 (Linux)")
            else:
                self.sound_method = "system_beep"
                self.logger.info("🔊 使用系统提示音 (Linux)")
        
        elif self.system == "Windows":
            try:
                import winsound
                self.sound_method = "winsound"
                self.logger.info("🔊 使用 winsound 播放声音 (Windows)")
            except ImportError:
                self.sound_method = "system_beep"
                self.logger.info("🔊 使用系统提示音 (Windows)")
        
        else:
            self.sound_method = "system_beep"
            self.logger.info(f"🔊 未知系统 {self.system}，使用系统提示音")
    
    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        return os.system(f"which {command} > /dev/null 2>&1") == 0
    
    def play_sound(self, sound_file: Optional[str] = None, repeat_count: int = 1, interval: float = 1.0, duration: float = 2.0) -> None:
        """
        播放声音
        
        Args:
            sound_file: 声音文件路径（可选）
            repeat_count: 重复次数
            interval: 重复间隔（秒）
            duration: 单次播放时长（秒）
        """
        if self._is_playing:
            self.logger.warning("⚠️ 声音正在播放中，跳过此次播放")
            return
        
        # 在新线程中播放声音，避免阻塞
        thread = threading.Thread(
            target=self._play_sound_thread,
            args=(sound_file, repeat_count, interval, duration),
            daemon=True
        )
        thread.start()
    
    def _play_sound_thread(self, sound_file: Optional[str], repeat_count: int, interval: float, duration: float) -> None:
        """声音播放线程"""
        self._is_playing = True
        
        try:
            for i in range(repeat_count):
                self.logger.info(f"🔔 播放报警声音 ({i + 1}/{repeat_count})")
                
                success = self._play_single_sound(sound_file, duration)
                
                if not success:
                    self.logger.warning("⚠️ 声音播放失败，使用备用提示音")
                    self._play_system_beep(duration)
                
                # 等待间隔（最后一次不等待）
                if i < repeat_count - 1:
                    time.sleep(interval)
                    
        except Exception as e:
            self.logger.error(f"❌ 声音播放出错: {str(e)}")
        
        finally:
            self._is_playing = False
    
    def _play_single_sound(self, sound_file: Optional[str], duration: float = 2.0) -> bool:
        """播放单次声音"""
        try:
            # 如果没有提供声音文件或文件不存在，使用系统提示音
            if not sound_file or not os.path.exists(sound_file):
                return self._play_system_beep(duration)
            
            # 根据系统类型播放声音文件
            if self.sound_method == "afplay":
                return os.system(f"afplay '{sound_file}' > /dev/null 2>&1") == 0
            
            elif self.sound_method == "aplay":
                return os.system(f"aplay '{sound_file}' > /dev/null 2>&1") == 0
            
            elif self.sound_method == "paplay":
                return os.system(f"paplay '{sound_file}' > /dev/null 2>&1") == 0
            
            elif self.sound_method == "winsound":
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                return True
            
            else:
                return self._play_system_beep(duration)
                
        except Exception as e:
            self.logger.error(f"❌ 播放声音文件失败: {str(e)}")
            return False
    
    def _play_system_beep(self, duration: float = 2.0) -> bool:
        """播放系统提示音 - 尖锐鸣叫声"""
        try:
            if self.system == "Darwin":  # macOS
                # 计算每个beep的时长，确保总时长为duration
                beep_count = max(int(duration * 2), 3)  # 至少3次beep，每秒2次
                beep_interval = duration / beep_count
                
                for i in range(beep_count):
                    # 使用系统响铃
                    os.system("osascript -e 'beep' > /dev/null 2>&1")
                    if i < beep_count - 1:  # 最后一次不等待
                        import time
                        time.sleep(beep_interval)
                return True
            
            elif self.system == "Linux":
                # 尝试多种方式产生尖锐声音
                if self._command_exists("speaker-test"):
                    # 快速播放多个高频音调
                    frequencies = [2000, 1500, 2500, 1800]
                    for freq in frequencies:
                        os.system(f"speaker-test -t sine -f {freq} -l 1 -s 1 > /dev/null 2>&1 &")
                        import time
                        time.sleep(0.1)
                    return True
                elif self._command_exists("beep"):
                    # 快速连续的高频哔声
                    os.system("beep -f 2000 -l 100; beep -f 1500 -l 100; beep -f 2500 -l 100")
                    return True
                else:
                    # 多次终端响铃
                    for _ in range(3):
                        print("\\a", end="", flush=True)
                        import time
                        time.sleep(0.1)
                    return True
            
            elif self.system == "Windows":
                if self.sound_method == "winsound":
                    import winsound
                    # 快速连续的高频哔声
                    frequencies = [2000, 1500, 2500, 1800, 2200]
                    for freq in frequencies:
                        winsound.Beep(freq, 100)
                    return True
                else:
                    # 多次终端响铃
                    for _ in range(3):
                        print("\\a", end="", flush=True)
                        import time
                        time.sleep(0.1)
                    return True
            
            else:
                # 通用终端响铃 - 多次快速响铃
                for _ in range(5):
                    print("\\a", end="", flush=True)
                    import time
                    time.sleep(0.05)
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 播放系统提示音失败: {str(e)}")
            return False
    
    def stop_playing(self) -> None:
        """停止播放声音（注意：可能无法立即停止正在播放的声音）"""
        self._is_playing = False
        self.logger.info("🛑 停止声音播放")
    
    def is_playing(self) -> bool:
        """检查是否正在播放声音"""
        return self._is_playing
    
    def test_sound(self, sound_file: Optional[str] = None) -> bool:
        """
        测试声音播放
        
        Args:
            sound_file: 声音文件路径（可选）
            
        Returns:
            是否播放成功
        """
        self.logger.info("🧪 测试声音播放...")
        
        if sound_file and os.path.exists(sound_file):
            self.logger.info(f"测试声音文件: {sound_file}")
            success = self._play_single_sound(sound_file)
        else:
            self.logger.info("测试系统提示音")
            success = self._play_system_beep()
        
        if success:
            self.logger.info("✅ 声音播放测试成功")
        else:
            self.logger.error("❌ 声音播放测试失败")
        
        return success
    
    def get_system_info(self) -> dict:
        """获取系统声音信息"""
        return {
            'system': self.system,
            'sound_method': self.sound_method,
            'is_playing': self._is_playing,
            'available_commands': {
                'afplay': self._command_exists("afplay"),
                'aplay': self._command_exists("aplay"),
                'paplay': self._command_exists("paplay"),
                'beep': self._command_exists("beep"),
                'speaker-test': self._command_exists("speaker-test")
            }
        }
