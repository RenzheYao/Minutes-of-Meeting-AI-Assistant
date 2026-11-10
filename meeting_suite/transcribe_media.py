import os
import argparse
import whisper

def transcribe_media(file_path, model_size="base", output_txt=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Loading Whisper model ('{model_size}')...")
    model = whisper.load_model(model_size)

    print(f"Transcribing '{file_path}'...")
    result = model.transcribe(file_path, fp16=False)
    transcript_text = result.get("text", "").strip()

    if not output_txt:
        base_name = os.path.splitext(file_path)[0]
        output_txt = f"{base_name}_transcript.txt"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    print(f"Saved: {output_txt}")
    return transcript_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Whisper Audio/Video Transcriber")
    parser.add_argument("input_file", help="Path to audio or video file")
    parser.add_argument("--model", default="base", help="Model size: tiny, base, small, medium, large")
    parser.add_argument("--output", default=None, help="Output text file path")
    args = parser.parse_args()

    transcribe_media(args.input_file, args.model, args.output)