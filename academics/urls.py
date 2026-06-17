from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Faculty
    path('faculties/', views.FacultyListView.as_view(), name='faculty_list'),
    path('faculties/create/', views.FacultyCreateView.as_view(), name='faculty_create'),
    path('faculties/<int:pk>/', views.FacultyDetailView.as_view(), name='faculty_detail'),
    path('faculties/<int:pk>/update/', views.FacultyUpdateView.as_view(), name='faculty_update'),
    path('faculties/<int:pk>/delete/', views.FacultyDeleteView.as_view(), name='faculty_delete'),

    # Study Programs
    path('study-programs/', views.StudyProgramListView.as_view(), name='studyprogram_list'),
    path('study-programs/create/', views.StudyProgramCreateView.as_view(), name='studyprogram_create'),
    path('study-programs/<int:pk>/update/', views.StudyProgramUpdateView.as_view(), name='studyprogram_update'),
    path('study-programs/<int:pk>/delete/', views.StudyProgramDeleteView.as_view(), name='studyprogram_delete'),

    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    # Classes
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('classes/<int:pk>/update/', views.ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),

    # Semesters
    path('semesters/', views.SemesterListView.as_view(), name='semester_list'),
    path('semesters/create/', views.SemesterCreateView.as_view(), name='semester_create'),
    path('semesters/<int:pk>/update/', views.SemesterUpdateView.as_view(), name='semester_update'),
    path('semesters/<int:pk>/delete/', views.SemesterDeleteView.as_view(), name='semester_delete'),
    path('semesters/<int:pk>/activate/', views.SemesterActivateView.as_view(), name='semester_activate'),

    # Academic Years
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('academic-years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<int:pk>/update/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),
    path('academic-years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),

    # Enrollments
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/create/', views.EnrollmentCreateView.as_view(), name='enrollment_create'),
    path('enrollments/<int:pk>/update/', views.EnrollmentUpdateView.as_view(), name='enrollment_update'),
    path('enrollments/<int:pk>/delete/', views.EnrollmentDeleteView.as_view(), name='enrollment_delete'),

    # HTMX endpoints
    path('load-study-programs/', views.load_study_programs, name='load_study_programs'),
    path('load-courses/', views.load_courses, name='load_courses'),
]
