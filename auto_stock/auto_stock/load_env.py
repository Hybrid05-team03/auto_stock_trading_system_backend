import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env():
    env = os.getenv("DJANGO_ENV", "local")  # 기본값 local
    env_file = BASE_DIR / f".env.{env}"

    if not env_file.exists():
        raise FileNotFoundError(f"환경 파일 {env_file}이 존재하지 않습니다.")

    load_dotenv(env_file)
    print(f"[ENV] Loaded {env_file}")
