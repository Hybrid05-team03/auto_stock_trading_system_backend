import os

def mapping_code_to_name(code: str) -> str:
    code = code.zfill(6)  # 6자리 zero-padding

    base_path = os.path.dirname(os.path.abspath(__file__))
    code_file_path = os.path.join(base_path, "kis_codes.txt")

    ## 파일에서 종목코드에 맞는 종목명 검색
    with open(code_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("종목코드"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                file_code = parts[0].zfill(6)
                name = parts[1]
                if file_code == code:
                    return name

    return "N/A"