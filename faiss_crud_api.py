import os
import openai
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,HTTPException , UploadFile, File
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
from dotenv import load_dotenv



class UserData(BaseModel): # pydantic model
    name: str
    description: str

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables and set OpenAI API key
load_dotenv()

embeddings = OpenAIEmbeddings()


if os.path.exists("test_db")!=True:
    db = FAISS.from_texts(["test entry "], embeddings, ids=["65"])
    db.save_local("test_db")
else:
    db=FAISS.load_local("test_db",embeddings)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/view_docs/")
async def view_items():
    try:
       return {"message": db.docstore._dict}
    except Exception as e:
        return {"error": "An unexpected error occurred." + str(e)}

@app.post("/add_docs_simple/")
async def add_docs(id:int ,file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text_data = contents.decode("utf-8")
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        # Write contents to a text file
        filename = f"uploaded_{id}.txt"
        with open(filename, "w") as text_file:
            text_file.write(text_data)
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        # Assuming TextLoader and FAISS are defined elsewhere in your code
        text_data = TextLoader(f"uploaded_{id}.txt").load()
        db_test = await FAISS.afrom_documents(text_data, embedding=embeddings, ids=[str(id)])
        db.merge_from(db_test)

    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}
    return {"message": "File processed and saved successfully.", "file": filename}

@app.post("/add_docs_metadata/")
async def add_meta_data(id:int,file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Only JSON files can be uploaded")

    try:
        contents = await file.read()
        file_data = json.loads(contents)
        text = file_data["content"]["text"]
        metadata_name = file_data["metadata"]["Name"]
        metadata_description = file_data["metadata"]["description"]
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
         # writing text to a file and saving it so we can pass meta data to the vector db when adding this document
        filename = f"uploaded_{id}.txt"
        with open(filename, "w") as text_file:
            text_file.write(text)
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        text_data = TextLoader(f"uploaded_{id}.txt").load()
        text_data[0].metadata={"Name": metadata_name ,"description": metadata_description,"source":text_data[0].metadata.get("source")}
        db_test = await FAISS.afrom_documents(text_data, embedding=embeddings, ids=[str(id)])
        db.merge_from(db_test)
        db.save_local("test_db")
        print(db.docstore._dict)


    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}
    return {"message": "File processed and saved successfully.", "file": filename}


@app.post("/update_docs_metadata/")
async def update_docs(id:int,file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Only JSON files can be uploaded")

    try:
        db.docstore._dict.pop(str(id))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document with id {id} not found.")

    try:
        contents = await file.read()
        file_data = json.loads(contents)
        text = file_data["content"]["text"]
        metadata = file_data["metadata"]
        metadata_name = file_data["metadata"]["Name"]
        metadata_description = file_data["metadata"]["description"]
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        filename = f"uploaded_{id}.txt"
        with open(filename, "w") as text_file:
            text_file.write(text)
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        text_data = TextLoader(f"uploaded_{id}.txt").load()
        text_data[0].metadata={"Name": metadata_name ,"description": metadata_description,"source":text_data[0].metadata.get("source")}
        db_test = await FAISS.afrom_documents(text_data, embedding=embeddings, ids=[str(id)])
        db.merge_from(db_test)
        db.save_local("test_db")


    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}
    return {"message": "File updated and saved successfully.", "file": filename}



@app.post("/update_docs/")
async def update_docs(id:int,file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Only JSON files can be uploaded")

    try:
        db.docstore._dict.pop(str(id))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document with id {id} not found.")

    try:
        contents = await file.read()
        text_data = contents.decode("utf-8")
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        # Write contents to a text file
        filename = f"uploaded_{id}.txt"
        with open(filename, "w") as text_file:
            text_file.write(text_data)
    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}

    try:
        # Assuming TextLoader and FAISS are defined elsewhere in your code
        text_data = TextLoader(f"uploaded_{id}.txt").load()
        db_test = await FAISS.afrom_documents(text_data, embedding=embeddings, ids=[str(id)])
        db.merge_from(db_test)

    except Exception as e:
        return {"message": "The code threw an exception :" + str(e)}
    return {"message": "File processed and saved successfully.", "file": filename}

@app.post("/delete_docs/")
async def delete_docs(id:int):
    try:
        db.docstore._dict.pop(str(id))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document with id {id} not found.")
    except Exception as e:
        return {"error": "An unexpected error occurred." + str(e)}
    return {"message": "File removed successfully." }

@app.post("/query_docs/")
async def query_docs(query:str):
    try:
        a=db.similarity_search(query)
        return {"message": a}
    except Exception as e:
        return {"error": "An unexpected error occurred." + str(e)}
    return {"message": "File removed successfully." }


