from django.db import models
from django.db.models import QuerySet
from .models import Report

class ReportRepository:
    def get_by_id(self, report_id: int) -> Report | None:
        return Report.objects.filter(id=report_id).select_related('generated_by').first()

    def get_all(self) -> QuerySet[Report]:
        return Report.objects.select_related('generated_by').all()

    def get_by_type(self, report_type: str) -> QuerySet[Report]:
        return Report.objects.filter(report_type=report_type).select_related('generated_by')

    def get_by_user(self, user_id: int) -> QuerySet[Report]:
        return Report.objects.filter(generated_by_id=user_id).select_related('generated_by')

    def get_ready(self) -> QuerySet[Report]:
        return Report.objects.filter(is_ready=True).select_related('generated_by')

    def get_pending(self) -> QuerySet[Report]:
        return Report.objects.filter(is_ready=False).select_related('generated_by')

    def create_report(self, title: str, report_type: str, format: str,
                      parameters: dict, generated_by) -> Report:
        return Report.objects.create(
            title=title, report_type=report_type, format=format,
            parameters=parameters, generated_by=generated_by
        )

    def mark_ready(self, report_id: int, file_path: str) -> bool:
        return Report.objects.filter(id=report_id).update(
            is_ready=True, file=file_path
        ) > 0

    def delete_report(self, report_id: int) -> bool:
        return Report.objects.filter(id=report_id).delete()[0] > 0

    def count_by_type(self) -> dict:
        counts = Report.objects.values('report_type').annotate(count=models.Count('id'))
        return {item['report_type']: item['count'] for item in counts}

    def get_recent(self, limit: int = 10) -> QuerySet[Report]:
        return Report.objects.select_related('generated_by').all()[:limit]
