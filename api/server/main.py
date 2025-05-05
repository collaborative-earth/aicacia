from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.controllers.chat_controller import chat_router
from server.controllers.chat_feedback_controller import chat_feedback_router
from server.controllers.feedback_controller import feedback_router
from server.controllers.user_controller import user_info_router, user_router
from server.controllers.query_controller import query_router


def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://3.137.35.87:3000",
            "http://3.137.35.87:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(query_router, prefix="/user_query", tags=["user_query"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
    app.include_router(user_router, prefix="/user", tags=["user"])
    app.include_router(user_info_router, prefix="/user_info", tags=["user_info"])
    app.include_router(chat_feedback_router, prefix="/chat_feedback", tags=["chat_feedback"])

    return app


app = create_app()
