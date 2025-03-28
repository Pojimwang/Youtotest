import os
import yt_dlp
from pydub import AudioSegment
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 從環境變數讀取OpenAI API金鑰
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# 檢查API金鑰是否存在
# if not openai.api_key:
#     raise ValueError("找不到OPENAI_API_KEY環境變數。請確保已設定正確的環境變數。")


class YouTubeTranscriber:
    def __init__(self):
        self.temp_dir = "temp_files"
        self.ensure_temp_directory()

    def ensure_temp_directory(self):
        """確保臨時文件目錄存在"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def sanitize_filename(self, filename):
        """清理檔案名稱，移除或替換特殊字元"""
        # 替換特殊字元
        invalid_chars = ['#', '/', '\\', '|', ':', '*', '?', '"', '<', '>', '⧸']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def download_audio(self, url):
        """使用yt-dlp從YouTube下載音頻"""
        try:
            print("正在下載音頻...")
            # 使用簡單的輸出模板
            output_template = os.path.join(self.temp_dir, "audio.%(ext)s")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self.progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                return os.path.join(self.temp_dir, "audio.mp3")
        except Exception as e:
            raise Exception(f"下載音頻時出錯: {str(e)}")

    def progress_hook(self, d):
        """顯示下載進度"""
        if d['status'] == 'downloading':
            percentage = d.get('_percent_str', '未知')
            print(f"下載進度: {percentage}")
        elif d['status'] == 'finished':
            print("下載完成，正在處理音頻...")

    def transcribe_audio(self, audio_file):
        """使用Whisper API進行語音識別"""
        try:
            print("正在轉錄音頻...")
            with open(audio_file, "rb") as file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file,
                    language="zh"
                )
            return transcript.text
        except Exception as e:
            raise Exception(f"轉錄音頻時出錯: {str(e)}")

    def cleanup(self):
        """清理臨時文件"""
        try:
            print("清理臨時文件...")
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"清理文件時出錯: {str(e)}")

    def process_url(self, url):
        """處理YouTube URL並返回轉錄文本"""
        try:
            # 下載音頻（已經轉換為MP3格式）
            audio_file = self.download_audio(url)

            # 進行轉錄
            transcript = self.transcribe_audio(audio_file)

            # 清理臨時文件
            self.cleanup()

            return transcript

        except Exception as e:
            self.cleanup()
            return f"處理過程中出錯: {str(e)}"


def main():
    transcriber = YouTubeTranscriber()

    while True:
        print("\n=== YouTube 轉錄工具 ===")
        url = input("請輸入YouTube URL (輸入'q'退出): ")

        if url.lower() == 'q':
            break

        try:
            print("\n開始處理...")
            transcript = transcriber.process_url(url)
            print("\n轉錄結果:")
            print("-" * 50)
            print(transcript)
            print("-" * 50)

            # 保存文本
            save = input("\n是否要保存文本? (y/n): ")
            if save.lower() == 'y':
                filename = input("請輸入文件名 (不需要副檔名): ") + ".txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcript)
                print(f"文本已保存到 {filename}")

        except Exception as e:
            print(f"\n錯誤: {str(e)}")

        cont = input("\n是否繼續處理其他視頻? (y/n): ")
        if cont.lower() != 'y':
            break

    print("\n感謝使用!")


if __name__ == "__main__":
    main()