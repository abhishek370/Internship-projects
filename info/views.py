from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, JsonResponse
import razorpay
from .models import Dept, Class, Student, Attendance, Course, Teacher, Assign, AttendanceTotal, time_slots, \
    DAYS_OF_WEEK, AssignTime, AttendanceClass, StudentCourse, Marks, MarksClass,AddExam,QuestionBank,paper,result,eachexam,User
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
from datetime import date
from datetime import datetime,timedelta
import time
import calendar
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string

from django.conf import settings
from django.core.mail import send_mail

from weasyprint import HTML
from dateutil import relativedelta




from django.views.decorators.csrf import csrf_exempt
import razorpay
from CollegeERP.settings  import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
)
from .constants import PaymentStatus
from django.views.decorators.csrf import csrf_exempt
import json
from fpdf import FPDF

# Create your views here.
def student_signin(request):
    today = date.today()
    if request.method == 'POST':
        # Retrieving all the form data that has been inputted
        class_id = get_object_or_404(Class, id=request.POST['class'])
        name = request.POST['full_name']
        usn = request.POST['usn']
        dob = request.POST['dob']
        sex = request.POST['sex']
        username = request.POST['user_name']
        password = request.POST['password']
        confirm_password = request.POST['conpassword']

        print(class_id)
        print(class_id.fees) 

        # Creating a User with student username and password format
        # USERNAME: firstname + underscore + last 3 digits of USN
        # PASSWORD: firstname + underscore + year of birth(YYYY)
        
        if password == confirm_password:
            user = User.objects.create_user(
                username = username,
                password = password,
            )
            user.save()
            
        #     # Creating a new student instance with given data and saving it.
        #     Student(
        #         user=user,
        #         USN=usn,
        #         class_id=class_id,
        #         name=name,
        #         sex=sex,
        #         DOB=dob
        #     ).save()

        # amount = request.POST.get("amount")
        amount = class_id.fees
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create(
            {"amount": int(amount) * 100, "currency": "INR", "payment_capture": "1"}
        )
        
        order = Student.objects.create(
            user=user,payment_date=today,USN=usn,class_id=class_id,name=name,sex=sex,DOB=dob,amount=amount,provider_order_id=razorpay_order['id']
        )
        order.save()
        return render(
            request,
            "info/payment.html",
            {
                "callback_url": "http://" + "127.0.0.1:8000" + "/callback/",
                "razorpay_key": 'rzp_test_dlQqxmJYrI47rl',
                "order": order,
            },
        )
            
            # return redirect('/')
            
    all_classes = Class.objects.all().order_by('-id')
    return render(request, 'info/student_signin.html',{'all_classes':all_classes})

@csrf_exempt
def callback(request):
    def verify_signature(response_data):
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        return client.utility.verify_payment_signature(response_data)

    if "razorpay_signature" in request.POST:
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order = Student.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.signature_id = signature_id
        order.save()
        print(verify_signature(request.POST),"------------------------------------")
        if verify_signature(request.POST):
            order.status = PaymentStatus.SUCCESS
            user = User.objects.get(username=order.user)
            user.is_active = True
            user.save()
            order.save()
            return render(request, "info/callback.html", context={"status": order.status})
        else:
            order.status = PaymentStatus.FAILURE
            user = User.objects.get(username=order.user)
            user.is_active = False
            user.save()
            order.save()
            return render(request, "info/callback.html", context={"status": order.status})
    else:
        payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
        provider_order_id = json.loads(request.POST.get("error[metadata]")).get(
            "order_id"
        )
        order = Student.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.status = PaymentStatus.FAILURE
        user = User.objects.get(username=order.user)
        user.is_active = False
        user.save()
        order.save()
        return render(request, "info/callback.html", context={"status": order.status})


@login_required
def index(request):
    if request.user.is_teacher:
        return render(request, 'info/t_homepage.html')
    if request.user.is_student:
        student_subject = request.user.student


        # Check Expired or not
        today = date.today()
        delta = relativedelta.relativedelta(today, student_subject.payment_date)        
        res_months = delta.months + (delta.years * 12)
        if res_months == student_subject.class_id.month and delta.days == 0:
            student_subject.status = "Expired"
            user = User.objects.get(username=student_subject.user)
            user.is_active = False
            user.save()
            student_subject.save()
            exp = True
            return render(request, 'info/payfees.html',{'exp':exp})





        student_subject1 =  student_subject.class_id.id
        for add_exam_classid in AddExam.objects.all().values('class_id'):   
            if student_subject1 == add_exam_classid.get('class_id'):
                today = date.today()
                for add_exam_dates in AddExam.objects.filter(class_id=add_exam_classid.get('class_id')).values('exam_date'):
                    difference = add_exam_dates.get('exam_date') - today
                    days = difference.days
                    if days == 1:
                        remind = True
                        return render(request, 'info/homepage.html',{'remind':remind})
                for add_exam_time in AddExam.objects.filter(class_id=add_exam_classid.get('class_id')).values('exam_time_start'):        
                    now = datetime.now()
                    date1 = AddExam.objects.get(class_id=add_exam_classid.get('class_id'),exam_date=today)
                    current_time = now.strftime("%H:%M")
                    exam_time = add_exam_time.get('exam_time_start').strftime("%H:%M")
                    t1 = datetime.strptime(current_time, "%H:%M")
                    t2 = datetime.strptime(exam_time, "%H:%M")
                    d1 = t1 - t2
                    print(t1,t2,d1)
                    sec = d1.total_seconds()
                    hours = sec / (60 * 60)
                    print('difference in hours:', int(hours))
                    if hours == 0 and date1.exam_date == today:
                        exam_begin = True
                        return render(request, 'info/homepage.html',{'exam_begin':exam_begin})
        return render(request, 'info/homepage.html')                
      
    if request.user.is_superuser:
        return render(request, 'info/admin_page.html')
    return render(request, 'info/logout.html')

def payfees(request):
    if request.method == "POST":
        na = request.POST.get('name')
        rr = Student.objects.get(name=na)
        # ord = request.user.student.USN
        order = Student.objects.get(USN=rr.USN)
        # cl = razorpay.Client(razorpay_order_id=order.provider_order_id)
        print(PaymentStatus.SUCCESS)
        if PaymentStatus.SUCCESS:
            order.status = PaymentStatus.SUCCESS
            user = User.objects.get(username=order.user)
            user.is_active = True
            user.save()
            order.save()
        else:
            order.status = PaymentStatus.FAILURE
            order.save()    
        return render(request, 'info/paynow.html',{'order':order})  

    return render(request, 'info/payfees.html')
# paynow Method is not Needed for now
def paynow(request):
    ord = request.user.student.USN
    order = Student.objects.get(USN=ord)
    # cl = razorpay.Client(razorpay_order_id=order.provider_order_id)
    print(PaymentStatus.SUCCESS)
    if PaymentStatus.SUCCESS:
        order.status = PaymentStatus.SUCCESS
        user = User.objects.get(username=order.user)
        user.is_active = True
        user.save()
        order.save()
    else:
        order.status = PaymentStatus.FAILURE
        order.save()    
    return render(request, 'info/paynow.html',{'order':order})

@login_required()
def student_detailes(request):
    today = date.today()
    ch = PaymentStatus.SUCCESS
    if request.method == "POST":
        paid_amont = Student.objects.filter(status=PaymentStatus.SUCCESS)
        not_paid = Student.objects.filter(status=PaymentStatus.FAILURE)
        expired = Student.objects.filter(status='Expired')
        stud_data = Student.objects.all()
        ep = []
        for e in expired:ep.append(e.amount)
        paid_amount = []
        np = []
        total_amount = []
        for na in not_paid:np.append(na.amount)
        for pa in paid_amont:paid_amount.append(pa.amount)
        for ta in stud_data:total_amount.append(ta.amount)
        total = sum(total_amount)
        paid = sum(paid_amount)
        npaid = sum(np)
        epaid = sum(ep)
        status = request.POST.get('sf')
        order = request.POST.get('ad')

        search = request.POST.get('search')
        download = request.POST.get('Download')
        
        if search:
            if status != 'None':
                if status == '1':
                    stud_data = Student.objects.filter(status=PaymentStatus.SUCCESS)
                    paginator = Paginator(stud_data, 10)
                    page = request.GET.get('page')
                    try:
                        stud_data = paginator.page(page)
                    except PageNotAnInteger:
                        stud_data = paginator.page(1)    
                    except EmptyPage:
                        stud_data = paginator.page(paginator.num_pages)
                    return render(request, 'info/student_detailes.html',{'epaid':epaid,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})
                elif status == '3':
                    stud_data = Student.objects.filter(status='Expired')
                    paginator = Paginator(stud_data, 10)
                    page = request.GET.get('page')
                    try:
                        stud_data = paginator.page(page)
                    except PageNotAnInteger:
                        stud_data = paginator.page(1)    
                    except EmptyPage:
                        stud_data = paginator.page(paginator.num_pages)
                    return render(request, 'info/student_detailes.html',{'epaid':epaid,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})   
                else:
                    stud_data = Student.objects.filter(status=PaymentStatus.FAILURE)
                    paginator = Paginator(stud_data, 10)
                    page = request.GET.get('page')
                    try:
                        stud_data = paginator.page(page)
                    except PageNotAnInteger:
                        stud_data = paginator.page(1)    
                    except EmptyPage:
                        stud_data = paginator.page(paginator.num_pages)
                    return render(request, 'info/student_detailes.html',{'epaid':epaid,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})
            if order != 'None':
                if order == '1':
                    stud_data = Student.objects.all().order_by('user_id')
                    paginator = Paginator(stud_data, 10)
                    page = request.GET.get('page')
                    try:
                        stud_data = paginator.page(page)
                    except PageNotAnInteger:
                        stud_data = paginator.page(1)    
                    except EmptyPage:
                        stud_data = paginator.page(paginator.num_pages)
                    return render(request, 'info/student_detailes.html',{'epaid':epaid,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})            
                else:
                    stud_data = Student.objects.all().order_by('-user_id')
                    paginator = Paginator(stud_data, 10)
                    page = request.GET.get('page')
                    try:
                        stud_data = paginator.page(page)
                    except PageNotAnInteger:
                        stud_data = paginator.page(1)    
                    except EmptyPage:
                        stud_data = paginator.page(paginator.num_pages)
                    return render(request, 'info/student_detailes.html',{'epaid':epaid,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})
        if download:
            pdf = FPDF()
            
            pdf.add_page()

            pdf.set_font("Arial",size=15)

            pdf.cell(200,10, txt="Student Detailes",ln=1,align='C')
            pdf.cell(200,10, txt="Name  Amount  Status",ln=1,align='C')
            for n in stud_data:
                pdf.cell(200, 10, txt = f"{n.name}  {n.amount}  {n.status}",ln = 1, align = 'C')

            pdf.output("pdfs/GFG.pdf")

            # html_string = render_to_string('info/studentdetailpdf.html', {'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid})
            # # print(html_string,"----------------")
            # html = HTML(string=html_string)
            # print(html)
            # html.write_pdf(target='/tmp/mypdf.pdf')

            # fs = FileSystemStorage('/tmp')
            # with fs.open('mypdf.pdf') as pdf:
            #     response = HttpResponse(pdf, content_type='application/pdf')
            #     response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
            #     return response     
    stud_data = Student.objects.all()


    # Imp Method Also added in index student
    # for t in stud_data:
    #     delta = relativedelta.relativedelta(today, t.payment_date)        
    #     res_months = delta.months + (delta.years * 12)
    #     # delta1 = today - t.payment_date
    #     print(res_months,t.class_id.month,t.name,delta.days)
    #     # if (res_months >= t.class_id.month and t.status == PaymentStatus.SUCCESS) or (res_months == t.class_id.month and t.status == PaymentStatus.SUCCESS):
    #     if res_months == t.class_id.month and delta.days == 0:
    #         t.status = "Expired"
    #         user = User.objects.get(username=t.user)
    #         user.is_active = False
    #         user.save()
    #         t.save()
    #     else:
    #         print("Not Expired")    

    # pen = Student.objects.filter(payment_date = None)
    # print(pen)
    # for p in pen:
        # p.payment_date = today
        # print(p.amount)
        # p.save()
        # print(p.amount)

    # pen = Student.objects.filter(amount = None)
    # print(pen)
    # for p in pen:
    #     p.amount = 15000
    #     print(p.amount)
    #     p.save()
    #     print(p.amount)
    
    paid_amont = Student.objects.filter(status=PaymentStatus.SUCCESS)
    not_paid = Student.objects.filter(status=PaymentStatus.FAILURE)
    expired = Student.objects.filter(status='Expired')

    paid_amount = []
    np = []
    total_amount = []
    ep = []
    for e in expired:ep.append(e.amount)
    for na in not_paid:np.append(na.amount)
    for pa in paid_amont:paid_amount.append(pa.amount)
    for ta in stud_data:total_amount.append(ta.amount)

    total = sum(total_amount)
    paid = sum(paid_amount)
    npaid = sum(np)
    epaid = sum(ep)


    

    paginator = Paginator(stud_data, 10)
    page = request.GET.get('page')
    try:
        stud_data = paginator.page(page)
    except PageNotAnInteger:
        stud_data = paginator.page(1)    
    except EmptyPage:
        stud_data = paginator.page(paginator.num_pages)
            
    return render(request, 'info/student_detailes.html',{'epaid':epaid,'expired':expired,'stud_data':stud_data,'total':total,'paid':paid,'npaid':npaid,'ch':ch})

@login_required()
def exam_detailes(request):
    student_subject = request.user.student
    student_subject1 =  student_subject.class_id.id
    for add_exam_classid in AddExam.objects.all().values('class_id'):    
        if student_subject1 == add_exam_classid.get('class_id'):
            exam_values = AddExam.objects.filter(class_id=student_subject1).values()
            for exam_detail in exam_values:
                exam_name1 = exam_detail.get('exam_name')
                exam_class_id_id1 = exam_detail.get('class_id_id')
                for stud_subject in Class.objects.filter(id=exam_class_id_id1):pass
                course_id1 = exam_detail.get('course_id')
                for stud_course in Course.objects.filter(id=course_id1):pass
                exam_date1 = exam_detail.get('exam_date')
                exam_time_start1 = exam_detail.get('exam_time_start')
                exam_time_end1 = exam_detail.get('exam_time_end')
                teacher_id1 = exam_detail.get('teacher_id')
                for teacher_name in Teacher.objects.filter(id=teacher_id1):pass
                print(exam_name1,exam_class_id_id1,course_id1,exam_date1,exam_time_start1,exam_time_end1,teacher_id1)
                start_time = datetime.strptime(str(exam_time_start1), "%H:%M:%S")
                end_time = datetime.strptime(str(exam_time_end1), "%H:%M:%S")
                duration = end_time - start_time
                context = {
                    'exam_name1':exam_name1,
                    'stud_subject':stud_subject,
                    'stud_course':stud_course,
                    'exam_date1':exam_date1,
                    'exam_time_start1':exam_time_start1,
                    'exam_time_end1':exam_time_end1,
                    'teacher_name':teacher_name,
                    'duration':duration
                }
                return render(request, 'info/exam_detailes.html',context)
    return render(request, 'info/exam_detailes.html')

@login_required()
def quetion_bank_first(request):
    return render(request, 'info/quetion_bank_first.html')

@login_required()
def question_bank(request):
    
       
    if request.method == "POST":
        teacher_name = request.user.teacher
        Que_list = QuestionBank.objects.all().values('question_description')
        op1_list = QuestionBank.objects.all().values('option_1')
        course_list = Course.objects.all().values('name')
        que_dis = []
        op1 = []
        course_name = []
        exam_list = AddExam.objects.all().values('exam_name')
        for que_value in Que_list:
            que_dis.append(que_value.get('question_description'))
        for op1_value in op1_list:
            op1.append(op1_value.get('option_1'))
        for course_value in course_list:
            course_name.append(course_value.get('name')) 

        # rs = request.POST.get('et')
        # if rs == 'Each':
        #     cd = True
        # else:
        #     cd = False    
        # print("+++++++++++++++",rs)
        # print(cd)       
       
        context = {
            'exam_list':exam_list,
            'teacher_name':teacher_name,
            'que_dis':que_dis,
            'op1':op1,
            'course_name':course_name,
            # 'cd':cd
        }
        
        
        ch = request.POST.getlist('check')
        
        if request.POST.get('cn') != 'Select courses':
           
            teacher_name = request.user.teacher
            
            op1_list = QuestionBank.objects.all().values('option_1')
            course_list = Course.objects.all().values('name')
            que_dis = []
            op1 = []
            course_name = []
            exam_list = AddExam.objects.all().values('exam_name')
           

            
            Que_list = QuestionBank.objects.filter(course__name=request.POST.get('cn')).values('question_description')
            ch = request.POST.get('check')
           
            for que_value in Que_list:
                que_dis.append(que_value.get('question_description'))
            for op1_value in op1_list:
                op1.append(op1_value.get('option_1'))
            for course_value in course_list:
                course_name.append(course_value.get('name'))

            rs = request.POST.get('et')
            if rs == 'Each':
                cd = True
            else:
                cd = False    
            print("+++++++++++++++",rs)
            print(cd) 

            context = {
                'exam_list':exam_list,
                'teacher_name':teacher_name,
                'que_dis':que_dis,
                'op1':op1,
                'course_name':course_name,
                'cd':cd
            }
            
        elif ch != None:
            print(ch)
            course_name_id = []
            Que_list = QuestionBank.objects.filter(question_description__in = ch)
            for ci in QuestionBank.objects.filter(question_description__in = ch).values('course'):
                course_name_id.append(ci.get('course'))
            teacher_id = request.user.teacher
            course_in = Course.objects.filter(id=ci.get('course'))
            for coin in course_in:pass
            exam_name = request.POST.get('ename')
            radio_check = request.POST.get('et')
            mark = request.POST.get('marks')
            each_mark_list = []
            exam = AddExam.objects.get(exam_name=exam_name)
            # for i in Que_list:print(i,"//*/*/*/*/*/*")
            if radio_check == 'Each':
                for i in request.POST.getlist('eachnum'):
                    if i != '':
                        each_mark_list.append(int(i))
                e_total = sum(each_mark_list)        
                for index,i in enumerate(Que_list):
                    obj = eachexam.objects.create(Exam=exam,teacher=teacher_id,Question=i,mark=each_mark_list[index],total=e_total)        
                    # each_num = request.POST.getlist('eachnum')
                    # print("----------------", each_num)        
            else:
                #     print(mark)
                # print(each_mark_list)               
                # exam = AddExam.objects.get(exam_name=exam_name)
                # print(exam_name,radio_check)
                obj = paper.objects.create(Exam=exam,teacher=teacher_id,course=coin,mark_format=radio_check,marks=mark)
                for i in Que_list:
                    question = QuestionBank.objects.get(id=i.id)
                    obj.Question.add(question)
                obj.save()
    else:
        teacher_name = request.user.teacher
        Que_list = QuestionBank.objects.all().values('question_description')
        op1_list = QuestionBank.objects.all().values('option_1')
        course_list = Course.objects.all().values('name')
        que_dis = []
        op1 = []
        course_name = []
        exam_name = request.POST.get('ename')
        print("Exam Name: ",exam_name)
        radio_check = request.POST.get('et')
        print("Radio Option: ",radio_check)
        mark = request.POST.get('marks')
        print("Mark: ",mark)

        exam_list = AddExam.objects.all().values('exam_name')
        # for e in exam_list:print(e)
        # print(exam_list)

        for que_value in Que_list:
            que_dis.append(que_value.get('question_description'))
        for op1_value in op1_list:
            op1.append(op1_value.get('option_1'))
        for course_value in course_list:
            course_name.append(course_value.get('name'))    
       
        context = {
            'exam_list':exam_list,
            'teacher_name':teacher_name,
            'que_dis':que_dis,
            'op1':op1,
            'course_name':course_name
        }
    return render(request, 'info/question_bank.html',context)

@login_required()
def start_exam(request):
    
    if request.method == "POST":
        today = date.today()
        student_subject = request.user.student
        student_subject1 =  student_subject.class_id.id
        paper_list = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('Question')
        paper_mf = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark_format')
        paper_mark = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
    
        for pmf in paper_mf:pass
        format = pmf.get('mark_format')
        
        # for mark in paper_mark:pass
        
        # if format == 'Each':
        #     marks = mark.get('marks')
        #     t_marks = marks * len(paper_list)
        # else:
        #     mar = mark.get('marks')
        #     t_marks = mar
        #     marks = t_marks / len(paper_list)

        checklist = request.POST.getlist('checks')
        cur_an = []

        mv = 'Total'
        if format == 'Total':
            tkm = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
            for i in tkm:pass
            t_marks = i.get('marks')
            marks = t_marks / len(paper_list)  
            Quedata = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)
            paper_list = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)
            extra_context = {'marks':marks}
            
        else:
            tko = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('total')
            for i in tko:pass
            t_marks = i.get('total')
            Quedata = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)
            paper_list = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)

        print(paper_list,"///////////////") 

        for index,a in enumerate(paper_list):
            print(a.Question)
            cur_an.append(a.Question.current_answer)
            if cur_an[index] == checklist[index]:
                obj = result.objects.create(student=request.user.student,Question=a.Question,answer=checklist[index],cur_answer=True)   
            else:
                obj = result.objects.create(student=request.user.student,Question=a.Question,answer=checklist[index],cur_answer=False) 



        # print(cur_an)
        # print(checklist)

        
        # Quedata = []
        # cur_a = []
        
        # for index,Que_id in enumerate(paper_list):
        #     Que_de = QuestionBank.objects.filter(id=Que_id.get('Question')).values()
        #     Que_de1 = QuestionBank.objects.filter(id=Que_id.get('Question'))
        #     print("*-*-*-*-*-*-*-*-*-*",Que_de1)
            
            # all1 = list(Que_de1) + list(checklist[index])
            # print("//////////////////////",all1)
            # for Que_d in Que_de:
            #     Quedata.append(Que_d)
            #     cur_an.append(Que_d.get('current_answer'))
            # for Que_d1 in Que_de1:
            #     # pass
            #     # obj = result.objects.create(student=request.user.student,Question=Que_d1,answer=checklist[index],cur_answer=False)
            #     if cur_an[index] == checklist[index]:
            #         obj = result.objects.create(student=request.user.student,Question=Que_d1,answer=checklist[index],cur_answer=True)   
            #     else:
            #         obj = result.objects.create(student=request.user.student,Question=Que_d1,answer=checklist[index],cur_answer=False) 
                
           
               
        # for cur_ans in Quedata:
        #     print("Cur: ",cur_ans)
        #     cur_a.append(cur_ans.get('current_answer'))        
        # # checklist = request.POST.getlist('checks')
        
        # print("Checks",checklist)
        # result1 = []
        # for i in range(len(Quedata)):
        #     if cur_a[i] == checklist[i]:
        #         result1.append(marks)
        #     else:
        #         pass
        # print("Result:- ",sum(result1))            
        # # print(Quedata)

        # stud = request.user.student
        # print("Student:- ",stud)


        context = {
            'Quedata':Quedata,
            't_marks':t_marks,
            'format':format,
            'mv':mv
        }

    today = date.today()
    student_subject = request.user.student
    student_subject1 =  student_subject.class_id.id
    paper_list = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('Question')
    paper_mf = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark_format')
    paper_mark = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
  
    for pmf in paper_mf:pass
    format = pmf.get('mark_format')
    
    for mark in paper_mark:pass
    
    # if format == 'Each':
    #     marks = mark.get('marks')
    #     t_marks = marks * len(paper_list)
    # else:
    # mar = mark.get('marks')
    # t_marks = mar
    # marks = t_marks / len(paper_list)   
    
    
    mv = 'Total'
    if format == 'Total':
        tkm = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
        for i in tkm:pass
        t_marks = i.get('marks')
        marks = t_marks / len(paper_list)  
        Quedata = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)
        print(Quedata,"////////////////////")
        for e in Quedata:print(e)
        extra_context = {'marks':marks}
    else:
        tko = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('total')
        for i in tko:pass
        t_marks = i.get('total')
        Quedata = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1)   



    # Quedata = []

    # for Que_id in paper_list:
    #     Que_de = QuestionBank.objects.filter(id=Que_id.get('Question')).values()
    #     for Que_d in Que_de:
    #         Quedata.append(Que_d)
    # print(Quedata)
    context = {
        'Quedata':Quedata,
        't_marks':t_marks,
        'format':format,
        'mv':mv
    }        
    return render(request, 'info/start_exam.html',context)


@login_required()
def result_s(request):
    if request.method == "POST":
        today = date.today()
        student_subject = request.user.student
        student_subject1 =  student_subject.class_id.id
        paper_list = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('Question')
        paper_mf = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark_format')
        paper_mark = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')

        for pmf in paper_mf:pass
        format = pmf.get('mark_format')
        
        mv = 'Total'
        if format == 'Total':
            tkm = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
            for i in tkm:pass
            t_marks = i.get('marks')
            marks = t_marks / len(paper_list)  
            # for e in Quedata:print(e)
            tmarks = []
            result11 = result.objects.all().values('cur_answer')
            for i in result11:
                if i.get('cur_answer') == True:
                    tmarks.append(marks)
                else:
                    pass

            s_mark = sum(tmarks)
            extra_context = {'marks':marks}
            
        else:
            tko = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('total')
            for i in tko:pass
            t_marks = i.get('total')
            mk = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark')
            ma = []
            for c in mk:ma.append(c.get('mark'))
            tmarks = []
            result11 = result.objects.all().values('cur_answer')
            for index,i in enumerate(result11):
                if i.get('cur_answer') == True:
                    tmarks.append(ma[index])
                else:
                    pass
            s_mark = sum(tmarks)            
            # print(ma,"************************")
            # print(t_marks,"////////////////////////")
            # Quedata = eachexam.objects.filter(Exam__exam_date=today+timedelta(days=1)) 

        # for mark in paper_mark:pass


        # if format == 'Each':
        #     marks = mark.get('marks')
        #     t_marks = marks * len(paper_list)
        # else:
        #     mar = mark.get('marks')
        #     t_marks = mar
        #     marks = t_marks / len(paper_list)


        A,B,C,D = 'A','B','C','D'

        # tmarks = []
        result_list = result.objects.all()
        # answer1 = result.objects.all().values('answer')
        # result11 = result.objects.all().values('cur_answer')
        # for i in result11:
        #     if i.get('cur_answer') == True:
        #         tmarks.append(marks)
        #     else:
        #         pass
        # s_mark = sum(tmarks)            

        context = {
                # 'marks':marks,
                't_marks':t_marks,
                # 'answer1':answer1,
                # 'result11':result11,
                'A':A,
                'B':B,
                'C':C,
                'D':D,
                'result_list':result_list,
                'ma':ma,
                'format':format,
                'mv':mv,
                's_mark':s_mark        
            }
        html_string = render_to_string('info/resultpdf.html', {'result_list': result_list,'t_marks':t_marks,'A':A,'B':B,'C':C,'D':D,'result_list':result_list,'format':format,'mv':mv,'ma':ma,'s_mark':s_mark})

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
            return response 

      

    today = date.today()
    student_subject = request.user.student
    student_subject1 =  student_subject.class_id.id
    paper_list = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('Question')
    paper_mf = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark_format')
    paper_mark = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')


    for pmf in paper_mf:pass
    format = pmf.get('mark_format')

    mv = 'Total'
    if format == 'Total':
        tkm = paper.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('marks')
        for i in tkm:pass
        t_marks = i.get('marks')
        marks = t_marks / len(paper_list)  
        # for e in Quedata:print(e)
        tmarks = []
        result11 = result.objects.all().values('cur_answer')
        for i in result11:
            if i.get('cur_answer') == True:
                tmarks.append(marks)
            else:
                pass

        s_mark = sum(tmarks) 
        extra_context = {'marks':marks}
        
    else:
        tko = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('total')
        for i in tko:pass
        t_marks = i.get('total')
        mk = eachexam.objects.filter(Exam__exam_date=today,Exam__class_id=student_subject1).values('mark')
        ma = []
        for c in mk:ma.append(c.get('mark'))
        tmarks = []
        result11 = result.objects.all().values('cur_answer')
        for index,i in enumerate(result11):
            if i.get('cur_answer') == True:
                tmarks.append(ma[index])
            else:
                pass
        s_mark = sum(tmarks)
        # print(ma,"************************")
        # print(t_marks,"////////////////////////")
        # Quedata = eachexam.objects.filter(Exam__exam_date=today+timedelta(days=1))  


    for mark in paper_mark:pass

    # if format == 'Each':
    #     marks = mark.get('marks')
    #     t_marks = marks * len(paper_list)
    # else:
    #     mar = mark.get('marks')
    #     t_marks = mar
    #     marks = t_marks / len(paper_list) 


    A,B,C,D = 'A','B','C','D'


    # tmarks = []
    result_list = result.objects.all()
    # answer1 = result.objects.all().values('answer')
    # result11 = result.objects.all().values('cur_answer')

    # for i in result11:
    #     if i.get('cur_answer') == True:
    #         tmarks.append(marks)
    #     else:
    #         pass

    # s_mark = sum(tmarks)    


    context = {
        # 'marks':marks,
        't_marks':t_marks,
        # 'answer1':answer1,
        # 'result11':result11,
        'A':A,
        'B':B,
        'C':C,
        'D':D,
        'result_list':result_list,
        'ma':ma,
        'format':format,
        'mv':mv,
        's_mark':s_mark        
    }
    return render(request, 'info/result.html',context)    
    
@login_required()
def add_question(request):
    if request.method == "POST":
        teacher_list = Teacher.objects.all().values('name')
        course_list = Course.objects.all().values('name')
        teacher_name = []
        course_name = []
        for teacher_value in teacher_list:
            teacher_name.append(teacher_value.get('name'))
        for course_value in course_list:
            course_name.append(course_value.get('name'))

        teacher_name1 = request.POST.get('teacher_name')
        teacher_insta = Teacher.objects.filter(name=teacher_name1)
        for teacher_i in teacher_insta:pass
        course1 = request.POST.get('course')
        course_insta = Course.objects.filter(name=course1)
        for course_i in course_insta:pass
        
        que_dis = request.POST.get('que_dis')
        option_1 = request.POST.get('option_1')
        option_2 = request.POST.get('option_2')
        option_3 = request.POST.get('option_3')
        option_4 = request.POST.get('option_4')
        cur_ans = request.POST.get('cur_ans')

        # print(teacher_name1,course1,que_dis,option_1,option_2,option_3,option_4,cur_ans)
        obj = QuestionBank.objects.create(teacher=teacher_i,course=course_i,question_description=que_dis,option_1=option_1,option_2=option_2,option_3=option_3,option_4=option_4,current_answer=cur_ans)

        context = {
            'teacher_name':teacher_name,
            'course_name':course_name
        }
        
    else:
        teacher_list = Teacher.objects.all().values('name')
        course_list = Course.objects.all().values('name')
        teacher_name = []
        course_name = []
        for teacher_value in teacher_list:
            teacher_name.append(teacher_value.get('name'))
        for course_value in course_list:
            course_name.append(course_value.get('name'))

        context = {
            'teacher_name':teacher_name,
            'course_name':course_name
        }
    return render(request, 'info/add_question.html',context)

@login_required()
def attendance(request, stud_id):
    stud = Student.objects.get(USN=stud_id)
    ass_list = Assign.objects.filter(class_id_id=stud.class_id)
    att_list = []
    for ass in ass_list:
        try:
            a = AttendanceTotal.objects.get(student=stud, course=ass.course)
        except AttendanceTotal.DoesNotExist:
            a = AttendanceTotal(student=stud, course=ass.course)
            a.save()
        att_list.append(a)
    return render(request, 'info/attendance.html', {'att_list': att_list})

# def findDay(date):
#     born = datetime.datetime.strptime(date, '%d %m %Y').weekday()
#     return (calendar.day_name[born])

@login_required()
def attendance_detail(request, stud_id, course_id):
    if request.method == "POST":
        stud = get_object_or_404(Student, USN=stud_id)
        cr = get_object_or_404(Course, id=course_id)
        stud1 = Student.objects.get(USN=stud_id)
        att_list = Attendance.objects.filter(course=cr, student=stud).order_by('-date')
        # email = Student.objects.filter(name=stud1).values('email')
        # email = 'shahabhishek548@gmail.com'
        today = date.today()
        d2 = today.strftime("%B %d, %Y")
        # print("Email:",email)
        # subject = 'welcome to GFG world'
        # message = f'Hi {stud1}, thank you for registering in geeksforgeeks.'
        # email_from = settings.EMAIL_HOST_USER
        # recipient_list = [email, ]
        # send_mail( subject, message, email_from, recipient_list )


        html_string = render_to_string('info/pdf_template.html', {'att_list': att_list,'cr':cr,'stud1':stud1,'d2':d2})

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
            return response        
            
    else:
        stud = get_object_or_404(Student, USN=stud_id)
        cr = get_object_or_404(Course, id=course_id)
        att_list = Attendance.objects.filter(course=cr, student=stud).order_by('-date')
        stud1 = Student.objects.get(USN=stud_id)
        today = date.today()
        d2 = today.strftime("%B %d, %Y")
        for a in att_list:
            print("//////////",a.date)
            if a.status is True:
                print("*********  Present")
            else:
                print("*******  Absent")    

        print("Data/*/*/*/*/",att_list)
    return render(request, 'info/att_detail.html', {'att_list': att_list, 'cr': cr,'stud1':stud1,'d2':d2})


# Teacher Views

@login_required
def t_clas(request, teacher_id, choice):
    teacher1 = get_object_or_404(Teacher, id=teacher_id)
    exam_list = AddExam.objects.all().order_by('-id')
    return render(request, 'info/t_clas.html', {'teacher1': teacher1, 'choice': choice,'exam_list':exam_list})

@login_required
def t_clas_gen_reports(request,pk):
    exam_data = AddExam.objects.get(id=pk)
    student_data = Student.objects.filter(class_id=exam_data.class_id)
    print("==========",student_data)

    assign_id = Assign.objects.get(class_id=exam_data.class_id)
    print("--------------",assign_id.id)
    ass = get_object_or_404(Assign, id=assign_id.id)
    sc_list = []
    for stud in ass.class_id.student_set.all():
        a = StudentCourse.objects.get(student=stud, course=ass.course)
        sc_list.append(a)

    return render(request, 'info/t_clas_gen_reports.html',{'exam_data':exam_data,'student_data':student_data,'sc_list':sc_list})

@login_required
def t_add_exam(request):
    today = date.today()
    if request.method == "POST":
        
        ec = AddExam.objects.all().values('exam_name')
        ec1 = []
        for s in ec:ec1.append(s.get('exam_name'))
        ename = request.POST.get('ename')
        name = request.POST.get('exam_name')
        if (ename == '') or (name in ec1):
            edit = True
            print("Working")
            name = request.POST.get('exam_name')
            print("Exam Name ==== ",name)

            edit_data = AddExam.objects.get(exam_name=name)
            print(edit_data.exam_date)

            edit_date =  edit_data.exam_date.strftime("%Y-%m-%d")    
            print(edit_date,"===========",type(edit_date))

            print("time: ",edit_data.exam_time_start,"----------------",type(edit_data.exam_time_start))

            edit_time_s =  edit_data.exam_time_start.strftime("%H:%M")
            edit_time_e =  edit_data.exam_time_end.strftime("%H:%M")

            teacher_id = Teacher.objects.get(user=request.user)
            teacher_id = teacher_id.id
            teacher1 = get_object_or_404(Teacher, id=teacher_id)
            exam = AddExam.objects.all().order_by('-id')

            if name in ec1:
                edate1 = request.POST.get('edate')
                etimes1 = request.POST.get('etimes')
                etimee1 = request.POST.get('etimee')
                ename1 = request.POST.get('ename')
                
                print("YYYYYYYYYYYYYYY",edate1,etimes1,etimee1,ename1,"YYYYYYYYYYYYYYYYYY")
                if ename != '':
                    edit_data.exam_name = ename1
                if edate1 != '':    
                    edit_data.exam_date = edate1
                if etimes1 != '':    
                    edit_data.exam_time_start = etimes1
                if etimee1 != '':    
                    edit_data.exam_time_end = etimee1
                edit_data.save()
                # obj = edit_data.

                

            return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'exam':exam,'edit_data':edit_data,'edit':edit,'edit_date':edit_date,'edit_time_s':edit_time_s,'edit_time_e':edit_time_e,'today':today})
        else:

            today = date.today()
            teacher_id1 = Teacher.objects.get(user=request.user)
            teacher_id = teacher_id1.id
            teacher1 = get_object_or_404(Teacher, id=teacher_id)
            exam = AddExam.objects.all().order_by('-id')    
            
            sub = request.POST.get('sub')
            cou = request.POST.get('cou')
            edate = request.POST.get('edate')
            etimes = request.POST.get('etimes')
            etimee = request.POST.get('etimee')
            ename = request.POST.get('ename')
            for ass in teacher1.assign_set.all():
                if str(ass.class_id) == sub:
                    subject1 = ass.class_id
                if str(ass.course) == cou:    
                    course1 = ass.course
            add_exam_students = []        
            for students in Student.objects.filter(class_id=subject1):
                add_exam_students.append(students)
        

        
            time_obj_start = datetime.strptime(etimes, '%H:%M').time()
            time_obj_end  =  datetime.strptime(etimee, '%H:%M').time()
            
        
            date_object = datetime.strptime(edate, '%Y-%m-%d').date()
        

            add_exam_stime = AddExam.objects.filter(exam_date=today)
        
            for t in add_exam_stime:print(t.exam_time_start)
            if time_obj_start >= time_obj_end:
                checker = True
                return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'checker':checker})
            elif today == date_object:
                for t in add_exam_stime:
                    if time_obj_start == t.exam_time_start:
                        st = t.exam_time_start
                        et = t.exam_time_end
                        st_checker = True
                        return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'st_checker':st_checker,'st':st,'et':et})
                    elif time_obj_end == t.exam_time_end:
                        et_checker = True
                        st = t.exam_time_start
                        et = t.exam_time_end
                        return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'et_checker':et_checker,'st':st,'et':et})    
                    else:break    
            else:
                # pass
                obj = AddExam.objects.create(exam_name=ename,class_id=subject1,course=course1,exam_date=edate,exam_time_start=etimes,exam_time_end=etimee,teacher=teacher_id1)
                
            # student1 = Student.objects.filter(class_id=subject1)        
            # print("/**/*/**//*/",student1)
            # print(subject1.id,"  ",course1.id)
            # print(ename,"/*/*/*",sub,"/*/*//*/",cou,"/*/*//*/*/",edate,"/*/*/*/*/*//",etimes,"/*/*/*/*/*//",etimee,"/*/*/*/*/*",teacher_id1)
            # obj = AddExam.objects.create(exam_name=ename,class_id=subject1,course=course1,exam_date=edate,exam_time_start=etimes,exam_time_end=etimee,teacher=teacher_id1)
            return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'exam':exam,'today':today})
    else:
        teacher_id = Teacher.objects.get(user=request.user)
        teacher_id = teacher_id.id
        teacher1 = get_object_or_404(Teacher, id=teacher_id)
        exam = AddExam.objects.all().order_by('-id')
          

        return render(request,'info/t_add_exam.html',{'teacher1': teacher1,'exam':exam,'today':today})

@login_required()
def t_add_exam_view(request,pk):
    view_data = AddExam.objects.get(id=pk)
    print(view_data)

    paper_data = paper.objects.filter(Exam=view_data)
    print(paper_data)
    
    result_data = result.objects.filter(Exam=view_data)
    

    if result_data.exists():
        rd = True
        A,B,C,D = 'A','B','C','D'
        return render(request,'info/t_add_exam_view.html',{'view_data':view_data,'rd':rd,'result_data':result_data,'A':A,'B':B,'C':C,'D':D})
    elif paper_data.exists():
        pd = True
        return render(request,'info/t_add_exam_view.html',{'view_data':view_data,'paper_data':paper_data,'pd':pd})    
    else:
        nd = True    
        return render(request,'info/t_add_exam_view.html',{'view_data':view_data,'nd':nd})

    return render(request,'info/t_add_exam_view.html',{'view_data':view_data})

@login_required()
def t_add_exam_edit_quetion(request,pk):
    if request.method == "POST":
        edit_que = eachexam.objects.filter(Exam__id=pk)
        edd = []
        edm = []
        for a in edit_que:edd.append(a.Question.question_description)

        que_data = QuestionBank.objects.filter(teacher=a.teacher)
        for b in edit_que:edm.append(int(b.mark))
        print(edm)





        check = request.POST.getlist('check')
        print("---------",check)
    else:
        edit_que = eachexam.objects.filter(Exam__id=pk)
        edd = []
        edm = []
        for a in edit_que:edd.append(a.Question.question_description)

        que_data = QuestionBank.objects.filter(teacher=a.teacher)
        for b in edit_que:edm.append(int(b.mark))
        print(edm)
        # for c in que_data:print(c.question_description)
                
    return render(request,'info/t_add_exam_edit_quetion.html',{'edit_que':edit_que,'que_data':que_data,'edd':edd,'edm':edm})    

@login_required()
def t_student(request, assign_id):
    ass = Assign.objects.get(id=assign_id)
    att_list = []
    for stud in ass.class_id.student_set.all():
        try:
            a = AttendanceTotal.objects.get(student=stud, course=ass.course)
        except AttendanceTotal.DoesNotExist:
            a = AttendanceTotal(student=stud, course=ass.course)
            a.save()
        att_list.append(a)
    return render(request, 'info/t_students.html', {'att_list': att_list})


@login_required()
def t_class_date(request, assign_id):
    if request.method == "POST":
        
        ass = get_object_or_404(Assign, id=assign_id)
        selected_checkbox = request.POST.getlist('m')
        search_keyword = request.POST.get('search')

        
        x = 1
        y = 0
        z = 2
        if selected_checkbox != 'None':
            att_list = ass.attendanceclass_set.filter(status__in = selected_checkbox)
        if search_keyword != 'None':    
            att_list = ass.attendanceclass_set.filter(date=search_keyword)
        context = {
            'att_list': att_list,
            'x':x,
            'y':y,
            'z':z,
            
        }
        
        return render(request, 'info/t_class_date.html', context)
    else:    
        now = timezone.now()
        ass = get_object_or_404(Assign, id=assign_id)
        att_list = ass.attendanceclass_set.filter(date__lte=now).order_by('-date')
        paginator = Paginator(att_list, 7)
        page = request.GET.get('page')
        try:
            att_list = paginator.page(page)
        except PageNotAnInteger:
            att_list = paginator.page(1)    
        except EmptyPage:
            att_list = paginator.page(paginator.num_pages)
        return render(request, 'info/t_class_date.html', {'att_list': att_list})         
    

@login_required()
def cancel_class(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    assc.status = 2
    assc.save()
    return HttpResponseRedirect(reverse('t_class_date', args=(assc.assign_id,)))


@login_required()
def t_attendance(request, ass_c_id):
    if request.method == "POST":
        n = request.POST.get('name')
        assc = get_object_or_404(AttendanceClass, id=ass_c_id)
        ass = assc.assign
        c = ass.class_id
        t = c.student_set.all()
        att_list = Attendance.objects.filter(attendanceclass=assc,student__name = n)
        context = {
            'ass': ass,
            'c': c,
            'assc': assc,
            'att_list':att_list
        }
        return render(request, 'info/t_attendance.html', context)
    else:    
        assc = get_object_or_404(AttendanceClass, id=ass_c_id)
        ass = assc.assign
        c = ass.class_id
        context = {
            'ass': ass,
            'c': c,
            'assc': assc,
        }
        return render(request, 'info/t_attendance.html', context)


@login_required()
def edit_att(request, ass_c_id):             
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    cr = assc.assign.course
    att_list = Attendance.objects.filter(attendanceclass=assc, course=cr)

    per_page = 2
    obj_paginator = Paginator(att_list, per_page)
    first_page = obj_paginator.page(1).object_list
    page_range = obj_paginator.page_range
    aid = ass_c_id
    print(ass_c_id)

    
    # paginator = Paginator(att_list, 2)
    # page = request.GET.get('page',1)
    # try:
    #     att_list = paginator.page(page)
    # except PageNotAnInteger:
    #     att_list = paginator.page(1)    
    # except EmptyPage:
    #     att_list = paginator.page(paginator.num_pages)

   
    print("1")


    context = {
        'assc': assc,
        'att_list': att_list,
        'obj_paginator':obj_paginator,
        'first_page':first_page,
        'page_range':page_range,
        'aid':aid
    }

    if request.method == "POST":
        sub = request.POST.get('submit')
        print("2")
        if sub:
            n = request.POST.get('name')
            assc = get_object_or_404(AttendanceClass, id=ass_c_id)
            cr = assc.assign.course
            print("3")
            att_list = Attendance.objects.filter(attendanceclass=assc, course=cr,student__name = n)
            context = {
                'assc': assc,
                'att_list':att_list
            }
            return render(request, 'info/t_edit_att.html', context)
        else:
            print("4")
            page_no = request.POST.get('page_no', None) 
            results = list(obj_paginator.page(page_no).object_list.values('id', 'student','status'))
            print(results,"=====================")
            return JsonResponse({"results":results})
    print("5")          
    return render(request, 'info/t_edit_att.html', context)


@login_required()
def confirm(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    ass = assc.assign
    cr = ass.course
    cl = ass.class_id
    for i, s in enumerate(cl.student_set.all()):
        status = request.POST[s.USN]
        if status == 'present':
            status = 'True'
        else:
            status = 'False'
        if assc.status == 1:
            try:
                a = Attendance.objects.get(course=cr, student=s, date=assc.date, attendanceclass=assc)
                a.status = status
                a.save()
            except Attendance.DoesNotExist:
                a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
                a.save()
        else:
            a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
            a.save()
            assc.status = 1
            assc.save()

    return HttpResponseRedirect(reverse('t_class_date', args=(ass.id,)))


@login_required()
def t_attendance_detail(request, stud_id, course_id):
    stud = get_object_or_404(Student, USN=stud_id)
    cr = get_object_or_404(Course, id=course_id)
    att_list = Attendance.objects.filter(course=cr, student=stud).order_by('date')
    return render(request, 'info/t_att_detail.html', {'att_list': att_list, 'cr': cr})


@login_required()
def change_att(request, att_id):
    a = get_object_or_404(Attendance, id=att_id)
    a.status = not a.status
    a.save()
    return HttpResponseRedirect(reverse('t_attendance_detail', args=(a.student.USN, a.course_id)))


@login_required()
def t_extra_class(request, assign_id):
    ass = get_object_or_404(Assign, id=assign_id)
    c = ass.class_id
    context = {
        'ass': ass,
        'c': c,
    }
    return render(request, 'info/t_extra_class.html', context)


@login_required()
def e_confirm(request, assign_id):
    ass = get_object_or_404(Assign, id=assign_id)
    cr = ass.course
    cl = ass.class_id
    assc = ass.attendanceclass_set.create(status=1, date=request.POST['date'])
    assc.save()

    for i, s in enumerate(cl.student_set.all()):
        status = request.POST[s.USN]
        if status == 'present':
            status = 'True'
        else:
            status = 'False'
        date = request.POST['date']
        a = Attendance(course=cr, student=s, status=status, date=date, attendanceclass=assc)
        a.save()

    return HttpResponseRedirect(reverse('t_clas', args=(ass.teacher_id, 1)))


@login_required()
def t_report(request, assign_id):
    ass = get_object_or_404(Assign, id=assign_id)
    sc_list = []
    for stud in ass.class_id.student_set.all():
        a = StudentCourse.objects.get(student=stud, course=ass.course)
        sc_list.append(a)
    return render(request, 'info/t_report.html', {'sc_list': sc_list})


@login_required()
def timetable(request, class_id):
    asst = AssignTime.objects.filter(assign__class_id=class_id)
    matrix = [['' for i in range(12)] for j in range(6)]

    for i, d in enumerate(DAYS_OF_WEEK):
        t = 0
        for j in range(12):
            if j == 0:
                matrix[i][0] = d[0]
                continue
            if j == 4 or j == 8:
                continue
            try:
                a = asst.get(period=time_slots[t][0], day=d[0])
                matrix[i][j] = a.assign.course_id
            except AssignTime.DoesNotExist:
                pass
            t += 1

    context = {'matrix': matrix}
    return render(request, 'info/timetable.html', context)


@login_required()
def t_timetable(request, teacher_id):
    asst = AssignTime.objects.filter(assign__teacher_id=teacher_id)
    class_matrix = [[True for i in range(12)] for j in range(6)]
    for i, d in enumerate(DAYS_OF_WEEK):
        t = 0
        for j in range(12):
            if j == 0:
                class_matrix[i][0] = d[0]
                continue
            if j == 4 or j == 8:
                continue
            try:
                a = asst.get(period=time_slots[t][0], day=d[0])
                class_matrix[i][j] = a
            except AssignTime.DoesNotExist:
                pass
            t += 1

    context = {
        'class_matrix': class_matrix,
    }
    return render(request, 'info/t_timetable.html', context)

@login_required()
def exam_timetable(request):
    today = date.today()
    exam_list = AddExam.objects.all().order_by('-exam_date')
    ee = AddExam.objects.filter(exam_date__gte=today)  
    return render(request, 'info/exam_timetable.html',{'exam_list':exam_list,'today':today})


@login_required()
def free_teachers(request, asst_id):
    asst = get_object_or_404(AssignTime, id=asst_id)
    ft_list = []
    t_list = Teacher.objects.filter(assign__class_id__id=asst.assign.class_id_id)
    for t in t_list:
        at_list = AssignTime.objects.filter(assign__teacher=t)
        if not any([True if at.period == asst.period and at.day == asst.day else False for at in at_list]):
            ft_list.append(t)

    return render(request, 'info/free_teachers.html', {'ft_list': ft_list})


# student marks


@login_required()
def marks_list(request, stud_id):
    stud = Student.objects.get(USN=stud_id, )
    ass_list = Assign.objects.filter(class_id_id=stud.class_id)
    sc_list = []
    for ass in ass_list:
        try:
            sc = StudentCourse.objects.get(student=stud, course=ass.course)
        except StudentCourse.DoesNotExist:
            sc = StudentCourse(student=stud, course=ass.course)
            sc.save()
            sc.marks_set.create(type='I', name='Internal test 1')
            sc.marks_set.create(type='I', name='Internal test 2')
            sc.marks_set.create(type='I', name='Internal test 3')
            sc.marks_set.create(type='E', name='Event 1')
            sc.marks_set.create(type='E', name='Event 2')
            sc.marks_set.create(type='S', name='Semester End Exam')
        sc_list.append(sc)

    return render(request, 'info/marks_list.html', {'sc_list': sc_list})


# teacher marks


@login_required()
def t_marks_list(request, assign_id):
    ass = get_object_or_404(Assign, id=assign_id)
    m_list = MarksClass.objects.filter(assign=ass)
    return render(request, 'info/t_marks_list.html', {'m_list': m_list})


@login_required()
def t_marks_entry(request, marks_c_id):
    mc = get_object_or_404(MarksClass, id=marks_c_id)
    ass = mc.assign
    c = ass.class_id
    context = {
        'ass': ass,
        'c': c,
        'mc': mc,
    }
    return render(request, 'info/t_marks_entry.html', context)


@login_required()
def marks_confirm(request, marks_c_id):
    mc = get_object_or_404(MarksClass, id=marks_c_id)
    ass = mc.assign
    cr = ass.course
    cl = ass.class_id
    for s in cl.student_set.all():
        mark = request.POST[s.USN]
        sc = StudentCourse.objects.get(course=cr, student=s)
        m = sc.marks_set.get(name=mc.name)
        m.marks1 = mark
        m.save()
    mc.status = True
    mc.save()

    return HttpResponseRedirect(reverse('t_marks_list', args=(ass.id,)))


@login_required()
def edit_marks(request, marks_c_id):
    mc = get_object_or_404(MarksClass, id=marks_c_id)
    cr = mc.assign.course
    stud_list = mc.assign.class_id.student_set.all()
    m_list = []
    for stud in stud_list:
        sc = StudentCourse.objects.get(course=cr, student=stud)
        m = sc.marks_set.get(name=mc.name)
        m_list.append(m)
    context = {
        'mc': mc,
        'm_list': m_list,
    }
    return render(request, 'info/edit_marks.html', context)


@login_required()
def student_marks(request, assign_id):
    ass = Assign.objects.get(id=assign_id)
    sc_list = StudentCourse.objects.filter(student__in=ass.class_id.student_set.all(), course=ass.course)
    return render(request, 'info/t_student_marks.html', {'sc_list': sc_list})


@login_required()
def add_teacher(request):
    if not request.user.is_superuser:
        return redirect("/")

    if request.method == 'POST':
        dept = get_object_or_404(Dept, id=request.POST['dept'])
        name = request.POST['full_name']
        id = request.POST['id'].lower()
        dob = request.POST['dob']
        sex = request.POST['sex']
        username = request.POST['user_name']
        password = request.POST['password']
        confirm_password = request.POST['conpassword']
        # Creating a User with teacher username and password format
        # USERNAME: firstname + underscore + unique ID
        # PASSWORD: firstname + underscore + year of birth(YYYY)
        if password == confirm_password:
            user = User.objects.create_user(
                username = username,
                password = password
            )
            user.save()

            Teacher(
                user=user,
                id=id,
                dept=dept,
                name=name,
                sex=sex,
                DOB=dob
            ).save()
            
         
            return redirect('/')
       
               
    
    all_dept = Dept.objects.order_by('-id')
    context = {'all_dept': all_dept}

    return render(request, 'info/add_teacher.html', context)


@login_required()
def add_student(request):
    # If the user is not admin, they will be redirected to home
    if not request.user.is_superuser:
        return redirect("/")

    if request.method == 'POST':
        # Retrieving all the form data that has been inputted
        class_id = get_object_or_404(Class, id=request.POST['class'])
        name = request.POST['full_name']
        usn = request.POST['usn']
        dob = request.POST['dob']
        sex = request.POST['sex']
        username = request.POST['user_name']
        password = request.POST['password']
        confirm_password = request.POST['conpassword'] 

        # Creating a User with student username and password format
        # USERNAME: firstname + underscore + last 3 digits of USN
        # PASSWORD: firstname + underscore + year of birth(YYYY)
        if password == confirm_password:
            user = User.objects.create_user(
                username = username,
                password = password,
            )
            user.save()

            # Creating a new student instance with given data and saving it.
            Student(
                user=user,
                USN=usn,
                class_id=class_id,
                name=name,
                sex=sex,
                DOB=dob
            ).save()
            return redirect('/')
        
                
    
    all_classes = Class.objects.order_by('-id')
    context = {'all_classes': all_classes}
    return render(request, 'info/add_student.html', context)