class PrivatePagesNoIndexMiddleware:
    """به موتور جستجو می‌گوید صفحات حساب/مدیریت را ایندکس نکند."""
    PRIVATE_PREFIXES=(
        "/admin/","/control/","/auth/","/business/","/support/",
        "/my-","/waiting/",
    )
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.path.startswith(self.PRIVATE_PREFIXES) or "/book/" in request.path or request.path.endswith("/qr/"):
            response["X-Robots-Tag"]="noindex, nofollow"
        return response
