from fastapi import FastAPI


def create_app():
    app = FastAPI()

    return app


app = create_app()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hell {name}"}
