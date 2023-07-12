from fastapi import FastAPI
import json

app = FastAPI()

@app.get("/")
def get_json(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data

@app.get("/export")
def export_json():
    json_data = get_json("sample.json")
    return json_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="172.16.7.121", port=8000)