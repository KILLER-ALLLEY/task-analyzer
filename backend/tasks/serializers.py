from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    id = serializers.JSONField(required=False, allow_null=True)
    title = serializers.JSONField(required=False, allow_null=True)
    due_date = serializers.JSONField(required=False, allow_null=True)

    estimated_hours = serializers.JSONField(required=False, allow_null=True)
    importance = serializers.JSONField(required=False, allow_null=True)

    dependencies = serializers.JSONField(required=False, allow_null=True)
