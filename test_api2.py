import requests
r = requests.get("https://generativelanguage.googleapis.com/v1beta/models?key=AQ.Ab8RN6LxAPDYjtnC2UGoMysranGo_fy9tMpkN19qMNSLzl3BHg")
print(r.status_code)
print(r.text)
