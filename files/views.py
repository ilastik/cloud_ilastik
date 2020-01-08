from django.shortcuts import get_object_or_404
from rest_framework import viewsets, response, parsers, permissions

from . import models, serializers


class FileViewset(viewsets.ViewSet):
    parser_classes = [parsers.FileUploadParser]
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        file_obj = request.data["file"]
        file = models.File.objects.create(name=file_obj.name, data=file_obj, owner=request.user)
        serializer = serializers.FileSerializer(file, context={"request": request})
        return response.Response(serializer.data)

    def list(self, request):
        queryset = models.File.objects.all()
        serializer = serializers.FileSerializer(queryset, many=True, context={"request": request})
        return response.Response(serializer.data)

    def retrieve(self, request, pk=None):
        file = get_object_or_404(models.File, pk=pk, owner=request.user)
        serializer = serializers.FileSerializer(file, context={"request": request})
        return response.Response(serializer.data)
