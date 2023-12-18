from pydantic import BaseModel
from http.client import HTTPException
import token
from typing_extensions import Annotated
# import db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError
from datetime import timedelta,datetime
import jwt

router = APIRouter(
    prefix = '/auth',
    tags = ['auth']
    
)

SECRETE_KEY = '12390k7876757t7'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl ='auth/token' )

class CreateUserRequest(BaseModel):
    username: str
    password: str
    

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, 
                        create_user_request:CreateUserRequest):

    create_user_model = Users (
    username=create_user_request.username,
    hashed_password=bcrypt_context.hash(create_user_request.password),
    )

    db.add(create_user_model)

    db.commit()
    
    
@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user.')
    token = create_access_token(user.username, user.id, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}
    
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username== username).first()

    if not user:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False

    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode1 = {'sub': username, 'id': user_id}
    expires= datetime.utcnow() + expires_delta
    encode1.update({'exp': expires})
    return jwt.encode(encode1, SECRETE_KEY, algorithm=ALGORITHM)