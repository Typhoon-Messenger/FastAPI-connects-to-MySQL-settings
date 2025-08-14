from fastapi import FastAPI,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from sqlalchemy.orm import *
from sqlalchemy import String,Integer,select
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.requests import Request

DB_URI = "mysql+asyncmy://ikun:123123@127.0.0.1:3306/kunkun?charset=utf8mb4"
engine = create_async_engine(
    DB_URI,
    # 将输出所有执行SQL的日志（默认是关闭的）
    echo=True,
    # 连接池大小（默认是5个）
    pool_size=10,
    # 允许连接池最大的连接数（默认是10个）
    max_overflow=20,
    # 获得连接超时时间（默认是30s）
    pool_timeout=10,
    # 连接回收时间（默认是-1，代表永不回收）
    pool_recycle=3600,
    # 连接前是否预检查（默认为False）
    pool_pre_ping=True,)

AsyncSessionFactory = sessionmaker(
    # Engine或者其子类对象（这里是AsyncEngine）
    bind=engine,
    # Session类的代替（默认是Session类）
    class_=AsyncSession,
    # 是否在查找之前执行flush操作（默认是True）
    autoflush=True,
    # 是否在执行commit操作后Session就过期（默认是True）
    expire_on_commit=False
)

# 数据表 Model
class Base(DeclarativeBase):
    pass

class StudentEntity(Base):
    __tablename__ = 'Student'
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    name : Mapped[str] = mapped_column(String(64), nullable=False)
    gender :Mapped[str] = mapped_column(String(10), nullable=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时释放连接池
    await engine.dispose()  # 关键清理[4,5](@ref)

# 输入输出类 Model
class StudentBase(BaseModel):
    name : str 
    gender : str
    
class StudentCreate(StudentBase):
    ...
    
class studentOut(StudentBase):
    id : int

async def creat_session_middleware(request:Request,call_next):
    session = AsyncSessionFactory()
    request.state.session = session
    response = await call_next(request)
    await session.close()
    return response

app = FastAPI()

app.add_middleware(BaseHTTPMiddleware,dispatch=creat_session_middleware)

@app.get("/student",response_model=List[studentOut])
async def get_student_list(request: Request):
    session = request.state.session
    try:
        async with session.begin():
            sql = select(StudentEntity)
            query =  await session.execute(sql)
            select_result = query.scalars().all()
            return select_result
    except:
        raise HTTPException(status_code=400,detail="查找用户失败")