from typing import Dict
from compiler_core.models import CompilationRun


class CompilationRunRepository:
    def save_run(self, source: str, result_json: Dict):
        return CompilationRun.objects.create(source=source, result_json=result_json)
