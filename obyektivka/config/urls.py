from django.urls import include, path

urlpatterns = [
    path("", include("apps.obyektivka.urls")),
]

handler404 = "apps.obyektivka.views.not_found"
