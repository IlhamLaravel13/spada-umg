from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'name': 'SPADA UMG API',
        'version': '1.0.0',
        'description': 'Sistem Pembelajaran Daring Universitas Muhammadiyah Gresik',
        'documentation': '/api/docs/',
        'endpoints': {
            'auth': '/api/auth/',
            'users': '/api/users/',
            'faculties': '/api/faculties/',
            'study_programs': '/api/study-programs/',
            'courses': '/api/courses/',
            'classes': '/api/classes/',
            'semesters': '/api/semesters/',
            'enrollments': '/api/enrollments/',
            'academic_years': '/api/academic-years/',
            'materials': '/api/materials/',
            'assignments': '/api/assignments/',
            'quizzes': '/api/quizzes/',
            'attendance': '/api/attendance/',
            'announcements': '/api/announcements/',
            'forums': '/api/forums/',
            'messages': '/api/messages/',
            'notifications': '/api/notifications/',
            'analytics': '/api/analytics/',
            'media': '/api/media/',
            'settings': '/api/settings/',
            'payments': '/api/payments/',
            'certificates': '/api/certificates/',
            'library': '/api/library/',
            'ai': '/api/ai/',
            'reports': '/api/reports/',
            'health': '/api/health/',
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0.0',
    })
