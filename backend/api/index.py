from app import create_app

class VercelPathPrefixMiddleware:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        prefix = "/api/index.py"
        if path.startswith(prefix):
            environ["PATH_INFO"] = path[len(prefix):] or "/"
        return self.application(environ, start_response)

app = create_app()
app.wsgi_app = VercelPathPrefixMiddleware(app.wsgi_app)
