from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TaskSerializer
from .scoring import TaskScorer


class AnalyzeTasks(APIView):
    def post(self, request):
        import inspect

        print("USING SERIALIZER FROM:", inspect.getfile(TaskSerializer))
        print("RAW DATA =", request.body)
        print("PARSED DATA =", request.data)

        serializer = TaskSerializer(data=request.data, many=True)

        if not serializer.is_valid():
            print("VALIDATION ERRORS =", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tasks = serializer.validated_data
        strategy = request.query_params.get("strategy", "smart_balance")
        scorer = TaskScorer(strategy=strategy)

        try:
            scored = scorer.score_all(tasks)
        except ValueError as e:
            payload = e.args[0] if e.args else {"error": "Circular dependency detected"}
            return Response(
                {"error": "Circular dependency detected", "cycles": payload.get("cycles", [])},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(scored, status=status.HTTP_200_OK)


class SuggestTasks(APIView):
    def post(self, request):
        import inspect

        print("USING SERIALIZER FROM:", inspect.getfile(TaskSerializer))
        print("RAW DATA =", request.body)
        print("PARSED DATA =", request.data)

        serializer = TaskSerializer(data=request.data, many=True)

        if not serializer.is_valid():
            print("VALIDATION ERRORS =", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tasks = serializer.validated_data
        scorer = TaskScorer(strategy="smart_balance")

        try:
            scored = scorer.score_all(tasks)
        except ValueError as e:
            payload = e.args[0] if e.args else {"error": "Circular dependency detected"}
            return Response(
                {"error": "Circular dependency detected", "cycles": payload.get("cycles", [])},
                status=status.HTTP_400_BAD_REQUEST,
            )

        top3 = scored[:3]
        for t in top3:
            t["reason"] = f"This task is selected because it has a high priority score ({t['score']})."

        return Response(top3, status=status.HTTP_200_OK)
