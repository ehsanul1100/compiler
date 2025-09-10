from rest_framework import serializers

class CompileRequestSerializer(serializers.Serializer):
    source = serializers.CharField()
    persist = serializers.BooleanField(required=False, default=False)

class CompileResponseSerializer(serializers.Serializer):
    stage_logs = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.DictField(), required=False)

    tokens = serializers.ListField(child=serializers.DictField(), required=False)
    ast = serializers.DictField(required=False)
    typed_ast = serializers.DictField(required=False)
    symbol_table = serializers.DictField(required=False)

    ir = serializers.ListField(child=serializers.CharField(), required=False)
    ir_optimized = serializers.ListField(child=serializers.CharField(), required=False)

    bytecode = serializers.ListField(child=serializers.CharField(), required=False)
    bytecode_optimized = serializers.ListField(child=serializers.CharField(), required=False)

    output = serializers.CharField(required=False)