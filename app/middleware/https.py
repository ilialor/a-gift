from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi import Request
from starlette.datastructures import URL
from starlette.responses import RedirectResponse

class CustomHTTPSRedirectMiddleware(HTTPSRedirectMiddleware):
    def __init__(self, app, *, exclude_paths=None, exclude_hosts=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/webhook"]
        self.exclude_hosts = exclude_hosts or []
        self.redirect_status_code = 307

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        url = URL(scope=scope)

        # Skip HTTPS redirect for excluded paths and hosts
        if (request.url.path in self.exclude_paths or
            request.headers.get("host") in self.exclude_hosts or
            url.scheme == "https"):
            await self.app(scope, receive, send)
            return

        redirect_url = url.replace(scheme="https")
        response = RedirectResponse(
            url=str(redirect_url), status_code=self.redirect_status_code
        )
        await response(scope, receive, send)
