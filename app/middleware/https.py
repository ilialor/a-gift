from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi import Request
from starlette.datastructures import URL
from starlette.responses import RedirectResponse

class CustomHTTPSRedirectMiddleware(HTTPSRedirectMiddleware):
    def __init__(self, app, *, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/webhook"]
        self.redirect_status_code = 307  # Add this line

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        
        # Исключаем определенные пути из HTTPS редиректа
        if request.url.path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        url = URL(scope=scope)
        if url.scheme == "https":
            await self.app(scope, receive, send)
            return

        redirect_url = url.replace(scheme="https")
        response = RedirectResponse(
            url=str(redirect_url), status_code=self.redirect_status_code
        )
        await response(scope, receive, send)
