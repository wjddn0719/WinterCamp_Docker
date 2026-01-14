import fitz
import pymupdf4llm
from fastapi import FastAPI, status, Request, HTTPException, UploadFile, File
import uvicorn
from pydantic import BaseModel
from starlette.responses import JSONResponse

full_text = ""
app = FastAPI()


@app.get("/hello")
def hello_world():
    return {"message": "Hello World"}


class LoginUser(BaseModel):
    username: str
    password: str


users = []
users.append(LoginUser(username="asd", password="jungwooLee"))


@app.post("/login")
def login(user: LoginUser):
    ok = any(u.username == user.username and u.password == user.password for u in users)
    if not ok:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid credentials"}
        )

    res = JSONResponse(content={"message": f"Welcome {user.username}"})
    res.set_cookie("username", user.username)
    return res


@app.get("/pages")
def pages(request: Request):
    username = request.cookies.get("username")
    if not username:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Not logged in"}
        )

    if username in (u.username for u in users):
        return JSONResponse(
            content={
                "ok": True,
                "message": f"Welcome {username}"
            }
        )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid user"}
    )

def get_current_user(request: Request) -> str:
    username = request.cookies.get("username")
    if not username:
        raise HTTPException(status_code = 401)
    if username not in [u.username for u in users]:
        raise HTTPException(status_code = 403)
    return username

@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    global full_text
    # 1) 쿠키 사용자 인증
    username = get_current_user(request)

    # 2) PDF만 허용 (content-type은 클라이언트가 속일 수 있어서 확장자도 같이 체크)
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

    if file.content_type not in (None, "application/pdf"):
        # 일부 클라이언트는 content_type이 None인 경우도 있어 None은 허용
        raise HTTPException(status_code=400, detail="content-type이 PDF가 아닙니다")

    # 3) 저장 없이 메모리에서 바이트로 읽기
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="빈 파일입니다")

    # 4) PyMuPDF로 바이트 스트림 열고 → pymupdf4llm로 Markdown 텍스트 추출
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = pymupdf4llm.to_markdown(doc)  # 문서 전체를 Markdown 텍스트로
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 파싱 실패: {e}")
    finally:
        try:
            doc.close()
        except Exception:
            pass

    # 여기서 full_text 변수를 원하는 대로 후처리/저장(DB 등)하면 됨
    # 지금은 예시로 일부 정보만 반환
    return {
        "ok": True,
        "user": username,
        "chars": len(full_text),
        "preview": full_text[:500],  # 너무 길면 잘라서
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)