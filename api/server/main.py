from controllers.feedback_controller import FeedbackController
from controllers.hello_world_controller import HelloworldController
from controllers.user_controller import UserController, UserLoginController
from controllers.user_query_controller import UserQueryController
from fastapi import FastAPI
from fastapi_utils import Api


def create_app():
    app = FastAPI()
    api = Api(app)

    hello_world_controller = HelloworldController()
    user_query_controller = UserQueryController()
    feedback_controller = FeedbackController()
    user_controller = UserController()
    user_login_controller = UserLoginController()
    api.add_resource(hello_world_controller, "/hello")
    api.add_resource(user_query_controller, "/user_query")
    api.add_resource(feedback_controller, "/feedback")
    api.add_resource(user_controller, "/user")
    api.add_resource(user_login_controller, "/user/login")

    return app


app = create_app()
