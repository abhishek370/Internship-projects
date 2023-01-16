from django.urls import path, include
from . import views
from django.contrib import admin

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings


urlpatterns = [
    path('', views.index, name='index'),
    path('student/<slug:stud_id>/attendance/',
         views.attendance, name='attendance'),
    path('student/<slug:stud_id>/<slug:course_id>/attendance/',
         views.attendance_detail, name='attendance_detail'),
    path('student/<slug:class_id>/timetable/',
         views.timetable, name='timetable'),
    # path('student/<slug:class_id>/search/', views.student_search, name='student_search'),

    path('student/<slug:stud_id>/marks_list/',
         views.marks_list, name='marks_list'),

    path('teacher/<slug:teacher_id>/<int:choice>/Classes/',
         views.t_clas, name='t_clas'),

     path('addexam/',views.t_add_exam,name='t_add_exam'),
     path('examdetailes/',views.exam_detailes,name='exam_detailes'),
     path('question_bank/',views.question_bank,name='question_bank'),
     path('add_question',views.add_question,name='add_question'),
     path('start_exam',views.start_exam,name='start_exam'),
     path('quetion_bank_first',views.quetion_bank_first,name='quetion_bank_first'),
     path('result',views.result_s,name='result'),
     path('<pk>/t_add_exam_view',views.t_add_exam_view,name='t_add_exam_view'),
     path('<pk>/t_add_exam_edit_quetion',views.t_add_exam_edit_quetion,name='t_add_exam_edit_quetion'),
     path('<pk>/t_clas_gen_reports',views.t_clas_gen_reports,name='t_clas_gen_reports'),
     path('exam_timetable',views.exam_timetable,name='exam_timetable'),
     path('student_signin',views.student_signin,name='student_signin'),
     path("payment/", views.student_signin, name="payment"),
     path("callback/", views.callback, name="callback"),
     path("paynow",views.paynow,name='paynow'),
     path("payfees",views.payfees,name='payfees'),
     path("student_detailes",views.student_detailes,name="student_detailes"),
     # path('addexam/<slug:teacher_id>',)

    path('teacher/<int:assign_id>/Students/attendance/',
         views.t_student, name='t_student'),
    path('teacher/<int:assign_id>/ClassDates/',
         views.t_class_date, name='t_class_date'),
    path('teacher/<int:ass_c_id>/Cancel/',
         views.cancel_class, name='cancel_class'),
    path('teacher/<int:ass_c_id>/attendance/',
         views.t_attendance, name='t_attendance'),
    path('teacher/<int:ass_c_id>/Edit_att/', views.edit_att, name='edit_att'),
    path('teacher/<int:ass_c_id>/attendance/confirm/',
         views.confirm, name='confirm'),
    path('teacher/<slug:stud_id>/<slug:course_id>/attendance/',
         views.t_attendance_detail, name='t_attendance_detail'),
    path('teacher/<int:att_id>/change_attendance/',
         views.change_att, name='change_att'),
    path('teacher/<int:assign_id>/Extra_class/',
         views.t_extra_class, name='t_extra_class'),
    path('teacher/<slug:assign_id>/Extra_class/confirm/',
         views.e_confirm, name='e_confirm'),
    path('teacher/<int:assign_id>/Report/', views.t_report, name='t_report'),

    path('teacher/<slug:teacher_id>/t_timetable/',
         views.t_timetable, name='t_timetable'),
    path('teacher/<int:asst_id>/Free_teachers/',
         views.free_teachers, name='free_teachers'),

    path('teacher/<int:assign_id>/marks_list/',
         views.t_marks_list, name='t_marks_list'),
    path('teacher/<int:assign_id>/Students/Marks/',
         views.student_marks, name='t_student_marks'),
    path('teacher/<int:marks_c_id>/marks_entry/',
         views.t_marks_entry, name='t_marks_entry'),
    path('teacher/<int:marks_c_id>/marks_entry/confirm/',
         views.marks_confirm, name='marks_confirm'),
    path('teacher/<int:marks_c_id>/Edit_marks/',
         views.edit_marks, name='edit_marks'),
    path('api/auth/', include('djoser.urls')),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    path('add-student/', views.add_student, name='add_student'),

    
]


admin.site.site_url = None
admin.site.site_header = 'My Site'
