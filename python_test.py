from descript_util import *


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploaded_files", StaticFiles(directory="uploaded_files"), name="uploaded_files")

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    with open("static/LG U+ 홈Agent PoC.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    descript = get_image_description(file.filename)

    return JSONResponse(content={"descript": descript})

@app.post("/get_sample")
async def upload_video(file: UploadFile = File(...), sample_time: int = Form(0)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(sample_time)
    sample_list = get_sample(file.filename, sample_time)

    return JSONResponse(content={"sample_list":sample_list})

@app.post("/vlm_query")
async def upload_video(sample_list: list = Form(0)):

    descript = get_description(sample_list)

    return JSONResponse(content={"descript_dict":descript})

@app.post("/make_excel")
async def upload_video(file: UploadFile = File(...), sample_time: int = Form(0)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(sample_time)
    sample_list = get_sample(file.filename, sample_time)

    descript = get_description(sample_list)

    make_excel(file.filename, sample_list, descript)

    return JSONResponse(content={"descript_dict":descript})

@app.post("/excel_data")
async def get_excel_data(file: UploadFile = File(...)):
    file_name, file_extension = os.path.splitext(file.filename)
    excel_path = f"./uploaded_files/{file_name}.xlsx"
    result_sheet = pd.read_excel(excel_path, sheet_name='Sheet', usecols= [1,2,3,4])

    result_sheet = result_sheet.replace([float('inf'), float('-inf')], pd.NA)
    result_sheet = result_sheet.fillna('')

    result_wb = load_workbook(excel_path)
    result_ws = result_wb.active

    image_urls = []
    for row in result_ws.iter_rows(min_row=2):
        time_str = row[1].value
        h, m, s = map(int, time_str.split(":"))
        file_time = f"{h:02d}_{m:02d}_{s:02d}"
        image_filename = f"baby_test_{file_time}.jpg"
        image_urls.append(f"/{UPLOAD_DIR}/{file_name}/{image_filename}")
    
    result_sheet.insert(0, "이미지", image_urls)

    return JSONResponse(content={
        "columns": list(result_sheet.columns),
        "data": result_sheet.values.tolist()
    })