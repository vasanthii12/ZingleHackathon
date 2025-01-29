from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
import os
import time
from sql_desc import extract_columns_from_sql, generate_column_description
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="SQL Analysis API")


# Add CORS middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  #React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>SQL Analysis API</title>
        </head>
        <body>
            <h1>SQL Analysis API</h1>
            <p>Available endpoints:</p>
            <ul>
                <li><a href="/docs">/docs</a> - Interactive API documentation</li>
                <li><a href="/redoc">/redoc</a> - Alternative API documentation</li>
                <li>POST /upload-sql/ - Upload SQL files</li>
                <li>GET /analyze-sql/ - Process SQL files and generate descriptions</li>
                <li>GET /get-descriptions/ - Retrieve stored descriptions</li>
            </ul>
        </body>
    </html>
    """

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_storage.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class SQLQuery(Base):
    __tablename__ = "sql_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    
class ColumnDescription(Base):
    __tablename__ = "column_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True)
    column_name = Column(String, index=True)
    description = Column(Text)

# Create database tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-sql/")
async def upload_sql_files(files: List[UploadFile]):
    """
    Upload one or more SQL files and store their contents in the database
    """
    db = SessionLocal()
    try:
        stored_files = []
        for file in files:
            if not file.filename.endswith('.sql'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a SQL file")
            
            # Read file content
            content = await file.read()
            sql_content = content.decode()
            
            # Store in database
            db_query = SQLQuery(filename=file.filename, content=sql_content)
            db.add(db_query)
            stored_files.append(file.filename)
        
        db.commit()
        return {"message": f"Successfully stored SQL files: {', '.join(stored_files)}"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/analyze-sql/")
async def analyze_sql():
    """ Process stored SQL files and generate column descriptions """
    db = SessionLocal()
    try:
        # Configure Gemini API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Get all stored SQL queries
        sql_queries = db.query(SQLQuery).all()
        if not sql_queries:
            raise HTTPException(status_code=404, detail="No SQL files found in database")
        
        # Create temporary file with all SQL queries
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            for query in sql_queries:
                temp_file.write(query.content + ";\n")
            temp_file_path = temp_file.name

        try:
            # Extract columns from the temporary file
            columns = extract_columns_from_sql(temp_file_path)
            if not columns:
                raise HTTPException(status_code=404, detail="No columns found in SQL queries")

            results = []
            batch_size =20

            for i in range(0, len(columns),batch_size):
                batch = columns[i:i + batch_size]

                for col in batch:
                    description = generate_column_description(col, model)
                    db_desc = ColumnDescription(
                        table_name=col['table'],
                        column_name=col['column'],
                        description=description
                    )
                    db.add(db_desc)
                    results.append({
                        'table': col['table'],
                        'column': col['column'],
                        'description': description
                    })
            
                db.commit()
                time.sleep(1)  # Reduced delay between batches
            return {
                "message": "Analysis complete",
                "total_columns_processed": len(results),
                "results": results
            }
        
        finally:
            os.unlink(temp_file_path)  # Clean up temp file
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/get-descriptions/")
async def get_descriptions(table_name: str = None):
    """
    Retrieve stored column descriptions, optionally filtered by table name
    """
    db = SessionLocal()
    try:
        query = db.query(ColumnDescription)
        if table_name:
            query = query.filter(ColumnDescription.table_name == table_name)
        
        descriptions = query.all()
        return [{
            "table": desc.table_name,
            "column": desc.column_name,
            "description": desc.description
        } for desc in descriptions]
    
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)