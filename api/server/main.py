from controllers.chat_controller import chat_router
from controllers.feedback_controller import feedback_router
from controllers.hello_world_controller import hello_router
from controllers.user_controller import user_router
from controllers.user_query_controller import user_query_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(hello_router, prefix="/hello", tags=["hello"])
    app.include_router(user_query_router, prefix="/user_query", tags=["user_query"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
    app.include_router(user_router, prefix="/user", tags=["user"])

    return app


app = create_app()
