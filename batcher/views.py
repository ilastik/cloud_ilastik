from rest_framework import viewsets, response, parsers
from . import models, serializers


class FileViewset(viewsets.ViewSet):
    parser_classes = [parsers.FileUploadParser]

    def create(self, request):
        file_obj = request.data["file"]
        file = models.File.objects.create(name=file_obj.name, data=file_obj)
        serializer = serializers.FileSerializer(file)
        return response.Response(serializer.data)

    def list(self, request):
        queryset = models.File.objects.all()
        serializer = serializers.FileSerializer(queryset, many=True)
        return response.Response(serializer.data)
