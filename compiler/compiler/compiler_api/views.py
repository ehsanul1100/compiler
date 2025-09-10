from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CompileRequestSerializer, CompileResponseSerializer
from compiler_core.services.compiler_service import CompilerService


class CompileView(APIView):
    def post(self, request):
        req_ser = CompileRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        source = req_ser.validated_data['source']
        persist = req_ser.validated_data['persist']


        result = CompilerService().compile(source, persist=persist)
        res_ser = CompileResponseSerializer(result)
        return Response(res_ser.data, status=status.HTTP_200_OK)