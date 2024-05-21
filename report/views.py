from urllib.parse import urljoin

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from report.models import Refrigerator, Report


@login_required(login_url='login')
def index(request):
    current_user = request.user
    employee_refrigerators = Refrigerator.objects.filter(is_assigned=current_user).prefetch_related('reports')
    refrigerators = [{
        'id': refrigerator.pk,
        'serial': refrigerator.serial_number,
        'model': refrigerator.model,
        'organization': refrigerator.organization.name,
        'organization_address': refrigerator.organization.address,
        'report_date': refrigerator.reports.last().date if refrigerator.reports.last() else None,
        'report_status': refrigerator.reports.last().status if refrigerator.reports.last() else None
    } for refrigerator in employee_refrigerators
    ]
    employee_statistics = {
        'refrigerators_count': employee_refrigerators.count(),
        'total_reports': current_user.reports.all().count(),
        'approved_reports': current_user.reports.filter(status='approved').count()
    }

    user = get_current_user(request)
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


@login_required(login_url='login')
def get_reports(request):
    search_query = request.GET.get('q', '').strip().lower()
    reports = Report.objects.filter(sender=request.user).select_related('refrigerator')
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
            'id': report.pk,
            'organization': report.refrigerator.organization.name,
            'organization_address': report.refrigerator.organization.address,
            'date': report.date,
            'status': report.status,
        } for report in reports
    ]
    user = get_current_user(request)

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


@login_required(login_url='login')
def get_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, sender=request.user)
    report_review = {
        'ref_model': report.refrigerator.model,
        'ref_serial': report.refrigerator.serial_number,
        'organization': report.refrigerator.organization.name,
        'organization_address': report.refrigerator.organization.address,
        'status': report.status,
        'comment_manager': report.comment_manager if report.comment_manager else None,
        'comment_admin': report.comment_admin if report.comment_admin else None

    }
    user = get_current_user(request)

    return render(
        request,
        'report/report.html',
        context={
            'report': report_review,
            'user': user
        }
    )


def get_current_user(request):
    current_user = request.user
    user = {
        'name': f'{current_user.first_name} {current_user.last_name}',
        'email': current_user.email,
        'photo': request.build_absolute_uri(current_user.photo.url) if current_user.photo else None
    }
    return user
