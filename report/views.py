import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from report.clustering import cluster_organizations
from report.forms import ReportForm, PhotoFormSet, ManagerReportForm
from report.models import Refrigerator, Report, Photo
from report.service import check_exif, extract_gps_coords


@login_required(login_url='login')
def index(request):
    current_user = request.user
    employee_refrigerators = Refrigerator.objects.filter(is_assigned=current_user).prefetch_related('reports')

    search_query = request.GET.get('q')

    if search_query:
        employee_refrigerators = employee_refrigerators.filter(
            Q(organization__name__icontains=search_query) |
            Q(organization__name__startswith=search_query.capitalize()) |
            Q(organization__name__istartswith=search_query.upper()) |
            Q(organization__name__istartswith=search_query.lower()) |
            Q(organization__address__icontains=search_query) |
            Q(organization__address__startswith=search_query.capitalize()) |
            Q(organization__address__istartswith=search_query.upper()) |
            Q(organization__address__istartswith=search_query.lower())
        )

    refrigerators = [{
        'id': refrigerator.pk,
        'serial': refrigerator.serial_number,
        'model': refrigerator.model,
        'organization': refrigerator.organization.name,
        'organization_address': refrigerator.organization.address,
        'report_date': last_report.date if last_report else None,
        'report_status': last_report.status if last_report else None,
        'report_id': last_report.pk if last_report else None,
    } for refrigerator in employee_refrigerators for last_report in [refrigerator.reports.last()]]

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
            'user': user,
            'search_query': search_query
        })


@login_required(login_url='login')
def get_manager_refrigerators(request):
    current_user = request.user
    if not current_user.is_manager:
        raise PermissionDenied
    user = get_current_user(request)
    manager_refrigerators = Refrigerator.objects.filter(
        is_assigned__in=current_user.subordinates.all()).prefetch_related('reports').prefetch_related('is_assigned')
    manager_statistic = {
        'employees_count': current_user.subordinates.all().count(),
        'refrigerators_count': manager_refrigerators.count(),
        'reports_review_count': Report.objects.filter(
            sender__in=current_user.subordinates.all(),
            status='on_review').count(),
        'reports_approved_count': Report.objects.filter(
            sender__in=current_user.subordinates.all(),
            status='approved').count(),
        'reports_total': Report.objects.filter(sender__in=current_user.subordinates.all()).count()

    }

    manager_assigned_refs = [{
        'id': refrigerator.pk,
        'serial': refrigerator.serial_number,
        'model': refrigerator.model,
        'assigned': f'{refrigerator.is_assigned.first_name} {refrigerator.is_assigned.last_name}',
        'organization': refrigerator.organization.name,
        'organization_address': refrigerator.organization.address,
        'report_date': last_report.date if last_report else None,
        'report_status': last_report.status if last_report else None,
        'report_id': last_report.pk if last_report else None,

    } for refrigerator in manager_refrigerators for last_report in [refrigerator.reports.last()]
    ]
    paginator = Paginator(manager_assigned_refs, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'report/manager_refrigerators.html',
        context={
            'page': page,
            'user': user,
            'manager': manager_statistic,
        })


@login_required(login_url='login')
def get_manager_reports(request):
    current_user = request.user
    if not current_user.is_manager:
        raise PermissionDenied
    user = get_current_user(request)
    search_query = request.GET.get('q', '').strip().lower()
    manager_reports = Report.objects.filter(
        sender__in=current_user.subordinates.all(),
        status='on_review',
        manager_review=None).prefetch_related('refrigerator').prefetch_related('sender').order_by('-date')

    status_mapping = {
        'на рассмотрении': 'on_review',
        'одобрен': 'approved',
        'отклонен': 'decline'
    }

    if search_query:
        status_query = status_mapping.get(search_query)
        manager_reports = manager_reports.filter(
            Q(refrigerator__is_assigned__first_name__contains=search_query) |
            Q(refrigerator__is_assigned__last_name__contains=search_query) |
            Q(refrigerator__organization__name__contains=search_query) |
            Q(refrigerator__organization__address__contains=search_query) |
            Q(date__contains=search_query) |
            Q(status__contains=status_query) if status_query else Q()
        )

    manager_reports_statistic = [
        {
            'id': report.pk,
            'sender': f'{report.sender.first_name} {report.sender.last_name}',
            'organization': report.refrigerator.organization.name,
            'organization_address': report.refrigerator.organization.address,
            'date': report.date,
            'status': report.status,
        } for report in manager_reports
    ]
    paginator = Paginator(manager_reports_statistic, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'report/manager_reports.html',
        context={
            'page': page,
            'user': user,
            'search_query': search_query
        }
    )


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
            Q(refrigerator__organization__name__contains=search_query) |
            Q(refrigerator__organization__address__contains=search_query) |
            Q(date__contains=search_query) |
            Q(status__contains=status_query) if status_query else Q()
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
    current_user = request.user
    report = get_object_or_404(Report, id=report_id)
    if not report.exif_description:
        photos = report.photos.all()
        if photos.exists():
            exif_reports = [f'Отчет по файлу {img_num + 1}:\n {check_exif(request.build_absolute_uri(photo.image.url))}'
                            for img_num, photo in enumerate(photos)]
            report.exif_description = "\n\n\n\n".join(exif_reports)
            report.save()
            for photo in photos:
                lat, lng = extract_gps_coords(request.build_absolute_uri(photo.image.url))
                if lat is not None and lng is not None:
                    Photo.objects.filter(pk=photo.pk).update(latitude=lat, longitude=lng)

    if report.sender != current_user and report.sender.manager != current_user:
        raise PermissionDenied

    if request.method == 'POST':
        form = ManagerReportForm(request.POST)
        if form.is_valid():
            manager_review = form.cleaned_data['manager_review']
            comment_manager = form.cleaned_data['comment_manager']
            report.manager_review = manager_review
            report.comment_manager = comment_manager
            report.save()

            return redirect('reports')
    else:
        initial_data = {'manager_review': report.manager_review, 'comment_manager': report.comment_manager}
        form = ManagerReportForm(initial=initial_data)

    report_review = {
        'sender': f'{report.sender.first_name} {report.sender.last_name}',
        'sender_user_id': report.sender.id,
        'ref_model': report.refrigerator.model,
        'ref_serial': report.refrigerator.serial_number,
        'organization': report.refrigerator.organization.name,
        'organization_address': report.refrigerator.organization.address,
        'status': report.status,
        'comment': report.comment,
        'images': report.photos.all(),
        'comment_manager': report.comment_manager if report.comment_manager else None,
        'comment_admin': report.comment_admin if report.comment_admin else None,
        'exif_description': report.exif_description,
        'manager_review': report.manager_review,
        'form': form

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
        'id': current_user.pk,
        'name': f'{current_user.first_name} {current_user.last_name}',
        'email': current_user.email,
        'photo': request.build_absolute_uri(current_user.photo.url) if current_user.photo else None,
        'is_manager': current_user.is_manager,
        'employee_code': current_user.employee_code,
    }
    return user


@login_required(login_url='login')
def create_report(request, refrigerator_id=None):
    user = get_current_user(request)
    if request.method == 'POST':
        report_form = ReportForm(request.POST, user=request.user)
        photo_formset = PhotoFormSet(request.POST, request.FILES)

        if report_form.is_valid() and photo_formset.is_valid():
            report = report_form.save(commit=False)
            report.sender = request.user
            report.save()
            photo_formset.instance = report
            photo_formset.save()
            return redirect('reports')

    else:
        initial_data = {}
        if refrigerator_id:
            refrigerator = get_object_or_404(Refrigerator, id=refrigerator_id)
            initial_data = {'refrigerator': refrigerator}

        report_form = ReportForm(initial=initial_data, user=request.user)
        photo_formset = PhotoFormSet()

    return render(request, 'report/create_report.html', {
        'report_form': report_form,
        'photo_formset': photo_formset,
        'user': user
    })


@login_required(login_url='login')
def get_upload_instruction(request):
    user = get_current_user(request)
    return render(request, 'report/report_photo_instruction.html', {'user': user})


@login_required(login_url='login')
def map_view(request):
    user = get_current_user(request)
    return render(request, 'report/map.html', {'user': user})


@login_required(login_url='login')
def cluster_map_view(request):
    eps_km = float(request.GET.get('eps', 1.0))
    min_samples = int(request.GET.get('min_samples', 2))

    orgs = cluster_organizations(eps_km=eps_km, min_samples=min_samples)

    n_clusters = len(set(o['cluster'] for o in orgs if o['cluster'] != -1))
    n_noise = sum(1 for o in orgs if o['cluster'] == -1)

    user = get_current_user(request)
    return render(request, 'report/cluster_map.html', {
        'orgs_json': json.dumps(orgs),
        'orgs': orgs,
        'eps': eps_km,
        'min_samples': min_samples,
        'n_clusters': n_clusters,
        'n_noise': n_noise,
        'user': user,
    })
