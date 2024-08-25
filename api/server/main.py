from controllers.hello_world_controller import HelloworldController
from controllers.user_query_controller import UserQueryController
from fastapi import FastAPI
from fastapi_utils import Api


def create_app():
    app = FastAPI()
    api = Api(app)

    hello_world_controller = HelloworldController()
    user_query_controller = UserQueryController()
    api.add_resource(hello_world_controller, "/hello")
    api.add_resource(user_query_controller, "/user_query")

    return app


app = create_app()
