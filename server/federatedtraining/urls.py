from django.urls import path
from . import views

app_name = "Benchmark"

urlpatterns = [
    path("", views.FederatedTrainingList.as_view()),
    path("<int:pk>/", views.FederatedTrainingDetail.as_view()),
    # path("<int:pk>/models/", views.BenchmarkModelList.as_view()),
    # path("<int:pk>/datasets/", views.BenchmarkDatasetList.as_view()),
    # path("<int:pk>/results/", views.BenchmarkResultList.as_view()),
]
