#!/usr/bin/env python3
"""
生成尖锐的报警声音文件
创建高频率、紧急的警报音效
"""

import numpy as np
import wave
import math
import os


def generate_beep_tone(frequency, duration, sample_rate=44100, amplitude=0.7):
    """
    生成指定频率的纯音调
    
    Args:
        frequency: 频率 (Hz)
        duration: 持续时间 (秒)
        sample_rate: 采样率
        amplitude: 振幅 (0-1)
    
    Returns:
        音频数据数组
    """
    frames = int(duration * sample_rate)
    arr = np.zeros(frames)
    
    for i in range(frames):
        # 生成正弦波
        arr[i] = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
    
    return arr


def generate_alarm_pattern():
    """
    生成复杂的报警音模式
    使用多种频率组合创建更尖锐的声音
    """
    sample_rate = 44100
    
    # 高频报警音模式
    patterns = [
        # 第一段：快速上升音调
        (2000, 0.1),  # 2000Hz, 0.1秒
        (2500, 0.1),  # 2500Hz, 0.1秒
        (3000, 0.1),  # 3000Hz, 0.1秒
        (3500, 0.1),  # 3500Hz, 0.1秒
        
        # 第二段：快速下降音调
        (3000, 0.1),  # 3000Hz, 0.1秒
        (2500, 0.1),  # 2500Hz, 0.1秒
        (2000, 0.1),  # 2000Hz, 0.1秒
        
        # 第三段：紧急连续音
        (2800, 0.05), # 2800Hz, 短促
        (0, 0.02),    # 静音间隔
        (2800, 0.05), # 重复
        (0, 0.02),    # 静音间隔
        (2800, 0.05), # 重复
        (0, 0.02),    # 静音间隔
        (2800, 0.05), # 重复
        
        # 第四段：强调音
        (4000, 0.2),  # 4000Hz, 长音
    ]
    
    audio_data = np.array([])
    
    for frequency, duration in patterns:
        if frequency == 0:  # 静音
            silence = np.zeros(int(duration * sample_rate))
            audio_data = np.concatenate([audio_data, silence])
        else:
            # 添加振幅调制，使声音更尖锐
            tone = generate_beep_tone(frequency, duration, sample_rate, amplitude=0.8)
            
            # 添加轻微的颤音效果
            vibrato_freq = 8  # 颤音频率
            vibrato_depth = 0.1  # 颤音深度
            
            for i in range(len(tone)):
                vibrato = 1 + vibrato_depth * math.sin(2 * math.pi * vibrato_freq * i / sample_rate)
                tone[i] *= vibrato
            
            audio_data = np.concatenate([audio_data, tone])
    
    return audio_data, sample_rate


def save_wav_file(audio_data, sample_rate, filename):
    """
    保存音频数据为WAV文件
    
    Args:
        audio_data: 音频数据数组
        sample_rate: 采样率
        filename: 输出文件名
    """
    # 转换为16位整数
    audio_data = np.clip(audio_data, -1, 1)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # 写入WAV文件
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16位
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())


def generate_alternative_sound():
    """
    生成备选的尖锐报警声
    使用不同的音调模式
    """
    sample_rate = 44100
    
    # 警笛式声音
    siren_data = np.array([])
    
    # 从1000Hz到4000Hz快速扫频
    base_freq = 1000
    max_freq = 4000
    sweep_duration = 0.3
    frames = int(sweep_duration * sample_rate)
    
    for i in range(frames):
        # 计算当前频率（线性扫频）
        progress = i / frames
        current_freq = base_freq + (max_freq - base_freq) * progress
        
        # 生成正弦波
        sample = 0.7 * math.sin(2 * math.pi * current_freq * i / sample_rate)
        siren_data = np.append(siren_data, sample)
    
    # 从4000Hz到1000Hz快速扫频
    for i in range(frames):
        progress = i / frames
        current_freq = max_freq - (max_freq - base_freq) * progress
        
        sample = 0.7 * math.sin(2 * math.pi * current_freq * i / sample_rate)
        siren_data = np.append(siren_data, sample)
    
    # 添加快速脉冲音
    pulse_freq = 3000
    pulse_duration = 0.1
    pulse_frames = int(pulse_duration * sample_rate)
    
    for pulse in range(3):  # 3个脉冲
        pulse_data = generate_beep_tone(pulse_freq, pulse_duration, sample_rate, 0.8)
        siren_data = np.concatenate([siren_data, pulse_data])
        
        # 添加短暂静音
        if pulse < 2:  # 最后一个脉冲后不加静音
            silence = np.zeros(int(0.05 * sample_rate))
            siren_data = np.concatenate([siren_data, silence])
    
    return siren_data, sample_rate


def main():
    """主函数"""
    print("🎵 生成尖锐报警声音文件...")
    
    try:
        # 检查numpy是否可用
        import numpy
        print("✅ numpy 可用")
    except ImportError:
        print("❌ 需要安装numpy: pip install numpy")
        return
    
    # 生成主要报警声音
    print("🔊 生成复杂报警音模式...")
    audio_data, sample_rate = generate_alarm_pattern()
    
    # 保存为WAV文件
    output_file = "alert.wav"
    save_wav_file(audio_data, sample_rate, output_file)
    print(f"✅ 主报警声音已保存: {output_file}")
    print(f"   文件大小: {os.path.getsize(output_file)} 字节")
    print(f"   时长: {len(audio_data) / sample_rate:.2f} 秒")
    
    # 生成备选声音
    print("🔊 生成警笛式报警声...")
    siren_data, siren_rate = generate_alternative_sound()
    
    # 保存备选声音
    siren_file = "alert_siren.wav"
    save_wav_file(siren_data, siren_rate, siren_file)
    print(f"✅ 警笛式声音已保存: {siren_file}")
    print(f"   文件大小: {os.path.getsize(siren_file)} 字节")
    print(f"   时长: {len(siren_data) / siren_rate:.2f} 秒")
    
    print("\\n🎯 声音文件特性:")
    print("📋 alert.wav:")
    print("   - 复杂音调模式 (2000-4000Hz)")
    print("   - 包含上升、下降、脉冲音")
    print("   - 带颤音效果，更加尖锐")
    
    print("📋 alert_siren.wav:")
    print("   - 警笛式扫频音 (1000-4000Hz)")
    print("   - 快速频率变化")
    print("   - 紧急脉冲音结尾")
    
    print("\\n💡 使用方法:")
    print("1. 在config.yaml中设置:")
    print('   sound_file_path: "alert.wav"')
    print("   或")
    print('   sound_file_path: "alert_siren.wav"')
    print("\\n2. 重新启动监控程序测试声音效果")


if __name__ == "__main__":
    main()
