from benchmarkmodel.serializers import BenchmarkListofModelsSerializer
from result.serializers import ModelResultSerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import FederatedTraining
from .serializers import FederatedTrainingSerializer, FederatedTrainingApprovalSerializer
from .permissions import IsAdmin, IsTrainingOwner


class FederatedTrainingList(GenericAPIView):
    serializer_class = FederatedTrainingSerializer
    queryset = ""

    @extend_schema(operation_id="federated_trainings_retrieve_all")
    def get(self, request, format=None):
        """
        List all benchmarks
        """
        trainings = FederatedTraining.objects.all()
        trainings = self.paginate_queryset(trainings)
        serializer = FederatedTrainingSerializer(trainings, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new benchmark
        """
        serializer = FederatedTrainingSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class BenchmarkModelList(GenericAPIView):
#     # TODO: instead of using IsAssociatedDatasetOwner, add a new endpoint?
#     #       at /datasets/<data_id>/benchmarks/<benchmark_id>/models
#     permission_classes = [IsAdmin | IsTrainingOwner]  # | IsAssociatedDatasetOwner]
#     serializer_class = BenchmarkListofModelsSerializer
#     queryset = ""
#
#     def get_object(self, pk):
#         try:
#             return FederatedTraining.objects.get(pk=pk)
#         except FederatedTraining.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         """
#         Retrieve models associated with a benchmark instance.
#         """
#         benchmark = self.get_object(pk)
#         models = benchmark.benchmarkmodel_set.all()
#         models = self.paginate_queryset(models)
#         serializer = BenchmarkListofModelsSerializer(models, many=True)
#         return self.get_paginated_response(serializer.data)
#
#
# class BenchmarkDatasetList(GenericAPIView):
#     # TODO: should we have an endpoint that returns datasets instead of associations?
#     permission_classes = [IsAdmin | IsBenchmarkOwner]
#     serializer_class = BenchmarkListofDatasetsSerializer
#     queryset = ""
#
#     def get_object(self, pk):
#         try:
#             return Benchmark.objects.get(pk=pk)
#         except Benchmark.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         """
#         Retrieve datasets associated with a benchmark instance.
#         """
#         benchmark = self.get_object(pk)
#         datasets = benchmark.benchmarkdataset_set.all()
#         datasets = self.paginate_queryset(datasets)
#         serializer = BenchmarkListofDatasetsSerializer(datasets, many=True)
#         return self.get_paginated_response(serializer.data)
#
#
# class BenchmarkResultList(GenericAPIView):
#     permission_classes = [IsAdmin | IsBenchmarkOwner]
#     serializer_class = ModelResultSerializer
#     queryset = ""
#
#     def get_object(self, pk):
#         try:
#             return Benchmark.objects.get(pk=pk)
#         except Benchmark.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         """
#         Retrieve results associated with a benchmark instance.
#         """
#         benchmark = self.get_object(pk)
#         results = benchmark.modelresult_set.all()
#         results = self.paginate_queryset(results)
#         serializer = ModelResultSerializer(results, many=True)
#         return self.get_paginated_response(serializer.data)
#

class FederatedTrainingDetail(GenericAPIView):
    serializer_class = FederatedTrainingApprovalSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsTrainingOwner]
            if "approval_status" in self.request.data:
                self.permission_classes = [IsAdmin]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return FederatedTraining.objects.get(pk=pk)
        except FederatedTraining.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a federated training instance.
        """
        training = self.get_object(pk)
        serializer = FederatedTrainingSerializer(training)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a federated training instance.
        """
        training = self.get_object(pk)
        serializer = FederatedTrainingApprovalSerializer(
            training, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a federated training instance.
        """
        training = self.get_object(pk)
        training.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
