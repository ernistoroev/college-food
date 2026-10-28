from django.conf import settings
from django.http import FileResponse, HttpResponse


def frontend(request):
    """
    "/" on the hosting: the built React site (backend/frontend_build/index.html).
    Locally the site runs on the Vite dev server instead, so here is just a hint.
    """
    index = settings.FRONTEND_BUILD_DIR / 'index.html'
    if index.exists():
        return FileResponse(index.open('rb'), content_type='text/html')
    return HttpResponse(
        'Сайт не собран. Для разработки откройте http://localhost:5173 (npm run dev), '
        'для хостинга выполните в frontend/: npm run build:deploy.',
        content_type='text/plain; charset=utf-8',
    )
