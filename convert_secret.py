import json

# JSON 파일 읽기
with open('serviceAccountKey.json', 'r', encoding='utf-8') as f:
    json_content = f.read()

# TOML 형식으로 변환
toml_output = f'''FIREBASE_SERVICE_ACCOUNT_KEY_JSON = """
{json_content}
''' + '"""'

print(toml_output)
