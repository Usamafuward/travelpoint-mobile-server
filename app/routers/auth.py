from fastapi import APIRouter, HTTPException, status, Depends, Body, Response, Request
from app.utils.security import hash_password, verify_password
from app.schemas.auth import UserLogin, UserRegistration, OTPVerification
from app.schemas.error import SimpleErrorMessage
from app.database import cur, conn
from datetime import timedelta
from app.utils import token
from fastapi.responses import JSONResponse
from app.utils.oauth2 import get_current_user
import app.utils.oauth as oauth
from app.utils.email import generate_otp, send_otp_email, save_otp, validate_otp


router = APIRouter()

endpoint_errors = {
    500: {"model": SimpleErrorMessage, "description": "Database Error"},
}

user_data_storage = {}

@router.post("/register", status_code=status.HTTP_201_CREATED, responses=endpoint_errors)
async def register_user(payload: UserRegistration = Body(...)):
    
    otp = generate_otp()

    save_otp(payload.email, otp)
    
    user_data_storage[payload.email] = payload

    await send_otp_email(payload.email, otp)

    return JSONResponse(content={"message": "OTP sent to your email. Please verify it."})

@router.post("/verify-otp", status_code=status.HTTP_201_CREATED, responses=endpoint_errors)
async def verify_otp(data: OTPVerification):
    email = data.email
    otp = data.otp
    
    payload = user_data_storage.get(email)
    
    print(f"Payload: {payload}")
    
    if payload is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "No user registration found for this email."},
        )
        
    if validate_otp(email, otp):
        # Hash password before saving
        hashed_password = hash_password(payload.password)

        # Insert user data into the database
        query = """
        INSERT INTO users (first_name, last_name, username, phone_number, location, password, nic_passport, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cur.execute(
                query,
                (
                    payload.first_name,
                    payload.last_name,
                    payload.first_name.lower() + payload.last_name.lower(),
                    payload.phone_number,
                    payload.location,
                    hashed_password,
                    payload.nic_passport,
                    payload.email,
                ),
            )
            conn.commit()

            cur.execute(b"SELECT * FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                access_token_expires = timedelta(minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = token.create_access_token(data={"sub": email})

                return JSONResponse(
                    content={
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user_id": result["id"],
                        "user_type": result["type"],
                    },
                    status_code=status.HTTP_200_OK,
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"message": "Error retrieving user ID after registration."},
                )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Error while registering the user."},
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid OTP."},
        )


endpoint_status_codes = {
    200: {"description": "Login successful"},
    500: {"description": "Database Error"},
    404: {"description": "User not found"},
    401: {"description": "Invalid password"},
}

@router.post("/login", responses=endpoint_status_codes)  # type: ignore
async def login_user(
    payload: UserLogin = Body(...), response: Response = Response()
):
    email = payload.email
    password = payload.password

    query = b"SELECT * FROM users WHERE email = %s"
    try:
        cur.execute(query, (email,))
        result = cur.fetchone()
        if result:
            if verify_password(password, result["password"]):  # type: ignore
                access_token_expires = timedelta(
                    minutes=token.ACCESS_TOKEN_EXPIRE_MINUTES
                )
                access_token = token.create_access_token(data={"sub": email})
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user_id": result["id"],  # Return the user ID as well
                        "user_type": result["type"],
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"message": endpoint_status_codes[401]["description"]},
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": endpoint_status_codes[404]["description"]},
            )
    except Exception as e:
        print(f"ERROR - DB:\n{e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": endpoint_errors[500]["description"]},
        )


endpoint_status_codes = {
    201: {"description": "Post created"},
    500: {"description": "Database Error"},
}



# Google OAuth2 login route
@router.get("/login/google")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

# Google OAuth2 callback route
@router.route("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        email = user_info.get("email")

        access_token = token.create_access_token(data={"sub": email})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"access_token": access_token, "token_type": "bearer", "email": email},
        )
    except Exception as e:
        print(f"Error during Google authentication: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication failed")

# Protected endpoint that requires authentication
@router.get("/secure-endpoint")
async def secure_endpoint(current_user: UserLogin = Depends(get_current_user)):
    return {"message": f"Welcome {current_user.email}!"}
