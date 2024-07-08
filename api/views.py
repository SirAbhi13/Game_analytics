import io

import pandas as pd
import requests
from celery.result import AsyncResult
from django.conf import settings
from django.db import connection
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.models import Game
from api.serializers import CSVURLSerializer, GameSerializer
from api.tasks import process_csv_file

# Create your views here.


authentication = getattr(settings, "AUTHENTICATION", True)


class GameViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated if authentication else AllowAny,)
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    @action(detail=False, methods=["post"])
    def upload_csv(self, request):
        serializer = CSVURLSerializer(data=request.data)
        if serializer.is_valid():
            url = serializer.validated_data["url"]

            task = process_csv_file.delay(url)

            return Response(
                {"message": "CSV processing started", "task_id": task.id},
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def check_csv_status(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response(
                {"error": "No task_id provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        task_result = AsyncResult(task_id)
        if task_result.ready():
            if task_result.successful():
                return Response({"status": "completed", "result": task_result.result})
            else:
                return Response(
                    {"status": "failed", "error": str(task_result.result)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response({"status": "processing"})

    @action(detail=False, methods=["GET"])
    def query(self, request):
        params = request.query_params
        query = "SELECT * FROM api_game WHERE 1=1"
        query_params = []

        for field, value in params.items():
            if field in ["app_id", "required_age", "dlc_count", "positive", "negative"]:
                query += f" AND {field} = %s"
                query_params.append(value)
            elif field in [
                "name",
                "developers",
                "publishers",
                "categories",
                "genres",
                "tags",
            ]:
                query += f" AND {field} LIKE %s"
                query_params.append(f"%{value}%")
            elif field == "price":
                query += " AND price <= %s"
                query_params.append(float(value))
            elif field == "release_date":
                query += " AND release_date = %s"
                query_params.append(value)
            elif field.startswith("date_"):
                operator = ">=" if field.endswith("_from") else "<="
                date_field = "release_date"
                query += f" AND {date_field} {operator} %s"
                query_params.append(value)
            elif field.startswith("agg_"):
                # Handle aggregate queries
                agg_field, agg_type = field.split("_")[1:]
                if agg_type in ["min", "max", "avg"]:
                    agg_query = f"SELECT {agg_type.upper()}({agg_field}) as result FROM api_game"
                    with connection.cursor() as cursor:
                        cursor.execute(agg_query)
                        result = cursor.fetchone()[0]
                    return Response({f"{agg_type}_{agg_field}": result})

        with connection.cursor() as cursor:
            cursor.execute(query, query_params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response(results)
