from django.shortcuts import get_object_or_404
from rest_framework import viewsets, response, permissions, generics

from . import serializers, models


class ProjectViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = serializers.ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = models.Project.objects.create(**serializer.validated_data)

        serializer = serializers.ProjectSerializer(project, context={"request": request})
        return response.Response(serializer.data)

    def list(self, request):
        queryset = models.Project.objects.filter(file__owner=request.user)
        serializer = serializers.ProjectSerializer(queryset, many=True)
        return response.Response(serializer.data)


class BatchJobViewset(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        from uuid import uuid4

        serializer = serializers.BatchJob(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        models.Job.objects.create(owner=user, external_id=uuid4().hex)
        return response.Response(serializer.data)


class JobDoneView(generics.UpdateAPIView):
    def update(self, request, external_id: str):
        serializer = serializers.JobUpdate(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(models.Job, external_id=external_id)
        job.status = serializer.data["status"]
        job.save()

        return response.Response(status=204)
