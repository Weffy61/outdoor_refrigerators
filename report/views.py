from urllib.parse import urljoin

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from report.models import Refrigerator, Report


@login_required(login_url='login')
def index(request):
    current_user = request.user
    employee_refrigerators = Refrigerator.objects.filter(is_assigned=current_user).prefetch_related('reports')
    refrigerators = [{
        'id': refrigerator.pk,
        'serial': refrigerator.serial_number,
        'model': refrigerator.model,
        'organization': refrigerator.organization,
        'organization_address': refrigerator.organization_address,
        'report_date': refrigerator.reports.last().date if refrigerator.reports.last() else None,
        'report_status': refrigerator.reports.last().status if refrigerator.reports.last() else None
    } for refrigerator in employee_refrigerators
    ]
    employee_statistics = {
        'refrigerators_count': employee_refrigerators.count(),
        'total_reports': current_user.reports.all().count(),
        'approved_reports': current_user.reports.filter(status='approved').count()
    }
    user = {
        'name': f'{current_user.first_name} {current_user.last_name}',
        'email': current_user.email,
        'photo': request.build_absolute_uri(current_user.photo.url) if current_user.photo else None
    }
    paginator = Paginator(refrigerators, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'report/index.html',
        context={
            'page': page,
            'statistic': employee_statistics,
            'user': user
        })


def get_reports(request):
    current_user = request.user
    base_report_url = urljoin(request.build_absolute_uri('/'), 'report/')
    search_query = request.GET.get('q', '').strip().lower()
    reports = Report.objects.filter(sender=current_user).select_related('refrigerator')
    status_mapping = {
        'на рассмотрении': 'on_review',
        'одобрен': 'approved',
        'отклонен': 'decline'
    }
    if search_query:
        status_query = status_mapping.get(search_query)
        reports = reports.filter(
            Q(refrigerator__organization__icontains=search_query) |
            Q(refrigerator__organization_address__icontains=search_query) |
            Q(date__icontains=search_query) |
            Q(status__icontains=status_query) if status_query else Q()
        )
    reports_statistic = [
        {
            'organization': report.refrigerator.organization,
            'organization_address': report.refrigerator.organization_address,
            'date': report.date,
            'status': report.status,
            'url': urljoin(base_report_url, str(report.pk))

        } for report in reports
    ]
    user = {
        'name': f'{current_user.first_name} {current_user.last_name}',
        'email': current_user.email,
        'photo': request.build_absolute_uri(current_user.photo.url) if current_user.photo else None
    }

    paginator = Paginator(reports_statistic, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'report/reports.html',
        context={
            'page': page,
            'user': user,
            'search_query': search_query
        }
    )
