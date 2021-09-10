from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
import sqlite3
from django.template import Template
import csv  
import xlwt
import xlsxwriter
import io
from tracker.models import *
from tracker.form import *

#FOR SENDING MAIL 
from AgappeTracker import settings
from django.core.mail import send_mail
#FOR SENDING MAIL  END

# FOR LOGIN
from .models import User
from .models import TaskCategory
from .models import Projects
from .models import PMProjects

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
# END FOR LOGIN

#pagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# # Create your views here.
from django.db.models import Count
from django.db import connection

import calendar
from calendar import monthrange
import datetime
import json
from django.db.models import Sum
from django.http import JsonResponse
from django.template.loader import render_to_string

g_page_no = 10
g_hod_id = 2

def registration(request):
    if request.method == 'POST':
        fname = request.POST.get('firstname')
        lname = request.POST.get('lname')
        contact= request.POST.get('contact')
        empcode=request.POST.get('empcode')
        uname = request.POST.get('email')
        pwd = request.POST.get('password')
        email = request.POST.get('email')
        usertype = 4        
        
        isactive="0"
    
        istaff = False
        if not User.objects.filter(username=uname).exists():
            User.objects.create_user(first_name=fname,empcode=empcode,empmobile=contact,username=uname,password=pwd,email=email,is_staff=istaff,is_active=isactive,usertype=usertype)
            return redirect(logins)
        else:
            msg = 'username already exists'
            return render(request,'registration.html',{'error':msg})            
    else:
        return render(request,'registration.html')

def forgotpassword(request):
    if request.method=='POST':
        usern = request.POST.get('username')
        passw1 = request.POST.get('newpwd')
        passw2 = request.POST.get('confirmpwd')
        objUser = User.objects.filter(username=usern).first()
        msg=""
        err=""
        if usern != "" and passw1 != "" and passw2 != "":
            if objUser:
                if passw1 == passw2:
                    objUser.set_password(passw1)
                    objUser.save()
                    msg = "Password reset successfully. Please login with the new password"
                else:
                    err = "Passwords mismatch"
            else:
                err = "Such a user does not exist!"            
        else:
            err = "Please enter all the fields!"
        return render(request,'forgot-password.html',{'err':err, 'msg':msg})
    else:
        return render(request,'forgot-password.html')

def logins(request):
    if request.method=='POST':
        usern = request.POST.get('username')
        passw = request.POST.get('password')
        try:
            remember = request.POST['remember_me']
        except MultiValueDictKeyError:
            remember = False

        if remember:
            response = HttpResponse("Remember me")
            response.set_cookie('cid1', usern)
            response.set_cookie('cid2', passw)

        user = authenticate(request,username=usern,password=passw)
        #SUPER ADMIN LOGIN
        if user is not None and user.is_superuser == 1:
            login(request,user)
            request.session['userid'] = user.id
            superadmin = User.objects.get(id=request.session['userid']) 
            return redirect(index)
        #Activated staff login
        elif user is not None and user.is_active == 1 and user.usertype == 4:
            login(request,user)
            request.session['userid'] = user.id
            normalstaff = User.objects.get(id=request.session['userid']) 
            HoursContributedCurrentMonth(request,user.id)
            return redirect(index)
        #Login for project manager   
        elif user is not None and user.is_staff == 0 and user.is_projectmanager == 1 and user.usertype == 3:
            login(request,user)
            request.session['userid'] = user.id
            pmstaff = User.objects.get(id=request.session['userid']) 
            return redirect(index)
        #Login for HOD 
        elif user is not None and user.is_staff == 1 and user.is_active == 1 and user.usertype == 2:
            login(request,user)
            request.session['userid'] = user.id
            hod = User.objects.get(id=request.session['userid']) 
            return redirect(index)
        else:
            return render(request, 'login.html',{'error':'Please recheck the email and password entered'})
    else:
        if request.COOKIES.get('cid1'):
            return render(request, 'login.html',{'ck1':request.COOKIES.get('cid1'), 'ck2':request.COOKIES.get('cid2')})
        else:
            return render(request, 'login.html')

@login_required(login_url='loginpage')
def index(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        return redirect(adminhome)
    elif staff.usertype == 2:
        return redirect(hodhome)
    elif staff.usertype == 3:
        return redirect(pmhome)
    elif staff.usertype == 4:
        return redirect(employeehome)
    else:
        return render(request,'index.html',{'username':staff})

@login_required(login_url='loginpage')
def logouts(request):
    logout(request)
    return redirect(logins)

#ADMIN LOGIN PAGES
@login_required(login_url='loginpage')
def adminhome(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        today = datetime.date.today()
        current = str(today.strftime("%m")) +'/'+str(today.year)
        forcsvfile = str(today.strftime("%m")) +'_'+str(today.year)
        return render(request, 'admDashboard.html',{'username':staff, 'current':current, 'forcsvfile':forcsvfile})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def employee(request):
    global g_page_no
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        if request.method == 'POST':
            namesearch = request.POST.get('namesearch')
            rows = User.objects.filter(first_name__contains=namesearch,is_staff=False)
        else:
            rows = User.objects.all().filter(is_staff=False).order_by('id').reverse()
        page = request.GET.get('page', 1)
        paginator = Paginator(rows, g_page_no)
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)
        return render(request,'employee.html',{'users':users,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addemployee(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        if request.method == 'POST':
            fname = request.POST.get('first_name')
            empcode = request.POST.get('empcode')
            email = request.POST.get('email')
            empmobile = request.POST.get('empmobile')
            is_projectmanager = request.POST.get('is_projectmanager')
           
            if is_projectmanager == None:
                is_projectmanager = False
                usertype = 4
            else:
                is_projectmanager = True
                usertype = 3
            password1 = request.POST.get('password1')
            if not User.objects.filter(username=email).exists():
                User.objects.create_user(password = password1,username=email,first_name=fname,email=email,is_active = True, empcode=empcode,empmobile=empmobile,is_projectmanager=is_projectmanager, usertype=usertype)
                return redirect(employee)
            else:
                error = "Username already exists"
                return render(request,'addemployee.html',{'username':staff, 'error':error})
        else:
            return render(request,'addemployee.html',{'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def empupdate(request):
    staff = User.objects.get(id=request.session['userid'])  
    if staff.usertype == 1:
        userid = request.GET.get('userid')  
        objUser = User.objects.get(id=userid)
        html = render_to_string('empupdate.html', {'username':staff,'objUser':objUser},request = request)
        return HttpResponse(html)  
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def empedited(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1:
        if request.method == 'POST':
            objU = User.objects.get(id=request.POST.get('userid'))
            objU.first_name = request.POST.get('first_name')
            objU.email = request.POST.get('email')
            objU.empcode = request.POST.get('empcode')
            objU.empmobile = request.POST.get('empmobile')
            if request.POST.get('is_projectmanager'):
                objU.is_projectmanager = request.POST.get('is_projectmanager')
            else:
                objU.is_projectmanager = 0
            objU.save()
            return redirect(employee)
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def activateEmp(request):
    empid = request.GET.get('tid')
    cust = User.objects.get(id=empid) 
    cust.is_active = 1
    cust.save()
    return HttpResponse(json.dumps(1), content_type="application/json")

@login_required(login_url='loginpage')
def deactivateEmp(request):
    empid = request.GET.get('tid')
    cust = User.objects.get(id=empid) 
    cust.is_active = 0
    cust.save()
    return HttpResponse(json.dumps(1), content_type="application/json")

@login_required(login_url='loginpage')
def addteam (request):
    #session
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        if request.method == 'POST': 
            pmid = request.POST.get('pmUserId') #get project manager id
            empid = request.POST.getlist('empUserId') # get staff id, selected team mates
            if len(empid) == 0:
                msg =  "No team members selected!"
            else:
                exists = Team.objects.filter(PMid=pmid, is_active=0) #checking if such a team already exists
                if exists.exists():
                    myteamid = Team.objects.get(PMid = pmid, is_active=0) 
                    msg = "Team already created for the selected Project Manager"
                else:
                    myteamid = Team.objects.create(PMid = User.objects.get(id=pmid))
                    empid = request.POST.getlist('empUserId')
                    for i in empid :
                        #exists = TeamMembership.objects.filter(staffid=i,is_active=0) 
                        exists = TeamMembership.objects.filter(staffid=i)
                        if exists.exists(): 
                            rows = User.objects.get(id = i)
                            msg =  rows.first_name+" already exists in selected team"
                            break
                        else:
                            TeamMembership.objects.create(staffid=User.objects.get(id=i),teamid=myteamid)
                            msg = ""
            rows = User.objects.all().filter(is_projectmanager=True)
            rows1 = User.objects.all().filter(is_staff=False,is_projectmanager=False)
            if msg !="":
                return render(request,'addTeam.html',{'form':rows,'form1':rows1,'error':msg,'username':staff})
            else:
                teams = Team.objects.filter(is_active=0) 
                return render(request,'teams.html',{'form':teams,'username':staff})
        else:
            projectmanagers = User.objects.all().filter(is_projectmanager=True)
            #projectmanagers = User.objects.all().filter(is_superuser=False,is_staff=False,is_active=True)
            teammates = User.objects.all().filter(is_staff=False,is_active=True,is_projectmanager=False)
            return render(request,'addTeam.html',{'form':projectmanagers,'form1':teammates,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def editteam (request,pk):

    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        rows1 = Team.objects.filter(PMid=pk)
        for x in rows1:
            selectedteammates = x.members.all()

        projectmanagers = User.objects.all().filter(is_projectmanager=True)
        teammates = User.objects.all().filter(is_staff=False,is_projectmanager=False)
        return render(request,'updTeam.html',{'form':projectmanagers,'disTM':teammates,'username':staff,'selectedteam':selectedteammates,'ID':pk})
    else:
        return render(request,'403.html',{'username':staff})
#function to list all the teams
#also when update button is clicked
@login_required(login_url='loginpage')
def teams(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
    #When the edit button is clicked on the team listing page
        if request.method == 'POST': 
            pmid = request.POST.get('PMID')
            staff = User.objects.get(id=request.session['userid']) 

            rows1 = Team.objects.filter(PMid=pmid)
            for x in rows1:
                teamID = x.id
                selectedteammates = x.members.all()

            pmstaff = User.objects.get(id=pmid) 
            projectmanagers = User.objects.all().filter(is_projectmanager=True)
            teammates = User.objects.all().filter(is_staff=False,is_projectmanager=False,is_active=True)

            return render(request,'updTeam.html',{'form':projectmanagers,'disTM':teammates,'username':staff,'selectedteam':selectedteammates,'ID':int(pmid),'teamdetails': teamID, 'pmstaff':pmstaff})
        else:
            rows = Team.objects.all()  
            page = request.GET.get('page', 1)
            paginator = Paginator(rows, g_page_no)
            try:
                teams = paginator.page(page)
            except PageNotAnInteger:
                teams = paginator.page(1)
            except EmptyPage:
                teams = paginator.page(paginator.num_pages) 
            return render(request,'teams.html',{'form':teams,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def showeditpage(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1:
        if request.method == 'POST': 
            pmid = request.POST.get('PMID')
            rows1 = Team.objects.filter(PMid=pmid)
            for x in rows1:
                teamID = x.id
                selectedteammates = x.members.all()

            projectmanagers = User.objects.all().filter(is_projectmanager=True)
            teammates = User.objects.all().filter(is_staff=False,is_projectmanager=False,is_active=True)

            return render(request,'updTeam.html',{'form':projectmanagers,'disTM':teammates,'username':staff,'selectedteam':selectedteammates,'ID':int(pmid),'teamdetails': teamID})
    else:
        return render(request,'403.html',{'username':staff})
#after updating the teams in the team form
@login_required(login_url='loginpage')
def teamupd (request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:    
        arrNewList = []
        msg = ""
        flag = 0
        if request.method == 'POST': 
            teamid = request.POST.get('updTeamId')
            pmid = request.POST.get('pmUserId')
            oldmembers = TeamMembership.objects.filter(teamid=teamid) 
        
            updatedempid = request.POST.getlist('empUserId')
            for i in updatedempid :
                exists = TeamMembership.objects.filter(staffid=i).first()
                if exists:
                    if exists.teamid.id != int(teamid):
                        rows = User.objects.get(id = i)
                        msg =  rows.first_name+" already assigned to a different team"
                        flag = 1
                        break
                    else:
                        arrNewList.append(i)

                else:
                    arrNewList.append(i)
            if flag == 1:
                projectmanagers = User.objects.all().filter(is_projectmanager=True)
                teammates = User.objects.all().filter(is_staff=False,is_projectmanager=False)
                rows1 = Team.objects.filter(PMid=pmid)
                for x in rows1:
                    teamID = x.id
                    selectedteammates = x.members.all()
                return render(request,'updTeam.html',{'form':projectmanagers,'disTM':teammates,'username':staff,'selectedteam':selectedteammates,'ID':int(pmid),'teamdetails': teamID,'error':msg})
            else:
                for old in oldmembers:
                    if str(old.staffid.id) in arrNewList:
                        pass
                    else:
                        TeamMembership.objects.filter(staffid=User.objects.get(id=int(old.staffid.id))).delete()
                        msg+="Delete "+str(old.staffid.id)

                if len(arrNewList) > 0:
                    for k in arrNewList:
                        ingroup = TeamMembership.objects.filter(staffid=int(k),teamid=int(teamid))
                        if not ingroup.exists():
                            TeamMembership.objects.create(staffid=User.objects.get(id=int(k)),teamid=Team.objects.get(id=teamid))

                return redirect(teams)
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def viewteam(request,id):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        rows1 = Team.objects.filter(PMid=id)
        pm = User.objects.get(id=id) 
        pjts = Projects.objects.filter(PMId=id)
        for x in rows1:
            k = x.members.all()

        return render(request,'viewteam.html',{'form':k,'username':staff, 'disPM':pm, 'projects':pjts})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def category(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        rows = TaskCategory.objects.all()
        #return render(request,'category.html',{'form':rows})
        page = request.GET.get('page', 1)
        paginator = Paginator(rows, g_page_no)
        try:
            catg = paginator.page(page)
        except PageNotAnInteger:
            catg = paginator.page(1)
        except EmptyPage:
            catg = paginator.page(paginator.num_pages)
        return render(request,'category.html',{'form':catg,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addcategory(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        if request.method == 'POST':
            category = request.POST.get('category')
            forpm = request.POST.get('forpm')
            if forpm != "1":
                forpm = 0
            objT = TaskCategory()
            objT.category = category
            objT.forpm = forpm
            objT.save()
            rows = TaskCategory.objects.all()
            return render(request,'category.html',{'form':rows,'username':staff})
        else:
            return render(request,'addcategory.html',{'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def editcategory(request):
    if request.method == 'POST':         
        catid= request.POST.get('catid')
        catgName= request.POST.get('categoryname')
        objT = TaskCategory.objects.get(id = catid)
        objT.category = catgName
        objT.save()
        return redirect(category)
    else:
        categoryid =  request.GET.get('catid')
        row = TaskCategory.objects.get(id=categoryid)
        return JsonResponse(data={
            'labels': row.category
            })

@login_required(login_url='loginpage')
def subcategory(request):
    staff = User.objects.get(id=request.session['userid'])
    categories = TaskCategory.objects.all()
    selectedcatid = 0
    if staff.usertype == 1:
        if request.method == 'POST':
            selectedcatid = int(request.POST.get('category'))
            rows = TaskSubCategory.objects.filter(CatId=TaskCategory.objects.get(id=selectedcatid)).order_by('CatId')
        else:
            if request.GET.get('catid'):
                if request.GET.get('catid') == 0:
                    selectedcatid = request.GET.get('catid')
                    rows = TaskSubCategory.objects.filter(CatId=TaskCategory.objects.get(id=request.GET.get('catid'))).order_by('CatId')
                else:
                    rows = TaskSubCategory.objects.all().order_by('CatId')
            else:
                rows = TaskSubCategory.objects.all().order_by('CatId')
        
        page = request.GET.get('page', 1)
        paginator = Paginator(rows, g_page_no)
        try:
            subcatg = paginator.page(page)
        except PageNotAnInteger:
            subcatg = paginator.page(1)
        except EmptyPage:
            subcatg = paginator.page(paginator.num_pages)
        return render(request,'subcategory.html',{'form':subcatg,'username':staff,'categories':categories, 'selectedcatid':selectedcatid})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addsubcategory(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        if request.method == 'POST':
            catId = request.POST.get('catId')
            # subcategory = request.POST.get('subcategory')
            subcategory = request.POST.getlist('subcategory[]')
            for val in subcategory:
                if val !="":
                    objT = TaskSubCategory()
                    objT.CatId = TaskCategory.objects.get(id = catId)
                    objT.subcategory = val
                    objT.save()
            rows = TaskSubCategory.objects.all()
            return render(request,'subcategory.html',{'form':rows,'username':staff})
        else:
            rows = TaskCategory.objects.all()
            return render(request,'addsubcategory.html',{'form':rows,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def editsubcategory(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1:
        if request.method == 'POST':
            subcatid = request.POST.get('subcatid')
            catId = request.POST.get('catId')
            subcatname = request.POST.get('subcatname')
            # returns all the projects assigned to that PM
            objSub = TaskSubCategory.objects.filter(id = subcatid).first()
            if objSub:
                objSub.CatId = TaskCategory.objects.get(id=catId)
                objSub.subcategory = subcatname
                objSub.save()
                return redirect(subcategory)
        else:
            subcatid = request.GET.get('subcatId')   #assigned project ID
            obj = TaskSubCategory.objects.get(id=subcatid)
            categories = TaskCategory.objects.all()
            html = render_to_string('editsubcategory.html', {'categories':categories,'username':staff,'subcat':obj},request = request)
            return HttpResponse(html)  
    else:
        return render(request,'403.html',{'username':staff})    

@login_required(login_url='loginpage')
def projects(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        rows = Projects.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(rows, g_page_no)
        try:
            pjts = paginator.page(page)
        except PageNotAnInteger:
            pjts = paginator.page(1)
        except EmptyPage:
            pjts = paginator.page(paginator.num_pages)
        return render(request,'projects.html',{'form':pjts,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addproject(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        if request.method == 'POST':  
            project = request.POST.get('projectname')
            objP = Projects()
            objP.project = project
            objP.save()
            rows = Projects.objects.all()
            return render(request,'projects.html',{'form':rows,'username':staff})
        else:
            return render(request,'addproject.html',{'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def editproject(request):
    if request.method == 'POST':         
        projid= request.POST.get('pjtid')
        proj= request.POST.get('project')
        objT = Projects.objects.get(id = projid)
        objT.project = proj
        objT.save()
        return redirect(projects)
    else:
        pid =  request.GET.get('pjtid')
        row = Projects.objects.get(id=pid)
        return JsonResponse(data={
            'labels': row.project
            })

@login_required(login_url='loginpage')
def assignedprojectlist(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        allocatedprojects = PMProjects.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(allocatedprojects, g_page_no)
        try:
            pjts = paginator.page(page)
        except PageNotAnInteger:
            pjts = paginator.page(1)
        except EmptyPage:
            pjts = paginator.page(paginator.num_pages)
        return render(request,'assignedpjts.html',{'form':pjts,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

def assignProject(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1: 
        projectmanagers = User.objects.all().filter(is_projectmanager=True)
        pjts = Projects.objects.all()
        arrNewList = []
        
        msg  =""
        flag = False
        if request.method == 'POST':
            PMId = request.POST.get('pmUserId')
            projectids = request.POST.getlist('projectids')
            if len(projectids) == 0:
                msg =  "No project selected"
                return render(request,'assignproj.html',{'form':projectmanagers,'username':staff,'project':pjts,'error':msg})
            else:
                for i in projectids:
                    exists = PMProjects.objects.filter(projectid=i).first()
                    if exists:
                        if exists.PMId.id == int(PMId):
                            flag = True
                            msg = "Project already assigned to selected Project manager"
                            break
                        else:
                            flag = True
                            msg = "Project already assigned to a different Project manager" 
                            break
                    else:
                        # add to the table append first teh ids
                        arrNewList.append(i)                    
                
                if flag == True:
                    return render(request,'assignproj.html',{'form':projectmanagers,'username':staff,'project':pjts,'error':msg})
                else:
                    # iterate the ids appended
                    for i in arrNewList:
                        objP =  PMProjects()
                        objP.PMId = User.objects.get(id = PMId)
                        objP.projectid = Projects.objects.get(id = i)
                        objP.save()
                    allocatedprojects = PMProjects.objects.all()
                    return render(request,'assignedpjts.html',{'form':allocatedprojects,'username':staff})
        else:
            return render(request,'assignproj.html',{'form':projectmanagers,'username':staff,'project':pjts})
    else:
        return render(request,'403.html',{'username':staff})

#here we are not actually deleting the teams,
#just setting the is_active field to 1
#so while listing the teams, only `is_active` = 0 will be displayed
@login_required(login_url='loginpage')
def teamdelete(request):
    teamId = request.GET.get('tid')
    # cust = Team.objects.get(id=teamId) 
    # cust.is_active = 1
    # cust.save()
    rows1 = Team.objects.filter(id=teamId).delete()
    return HttpResponse(json.dumps(1), content_type="application/json")

@login_required(login_url='loginpage')
def assgnprojdel(request):
    assgnprojId = request.GET.get('tid')
    rows1 = PMProjects.objects.filter(id=assgnprojId).delete()
    return HttpResponse(json.dumps(1), content_type="application/json")

@login_required(login_url='loginpage')
def updproj(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1:
        aspjId = request.GET.get('aspjId')   #assigned project ID
        obj = PMProjects.objects.get(id=aspjId)

        projectmanagers = User.objects.all().filter(is_projectmanager=True)
        html = render_to_string('updpmproject.html', {'form':projectmanagers,'username':staff,'assignedpjid':obj},request = request)
        return HttpResponse(html)  
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def workhrs(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 1:
        workhourslist = WorkingHours.objects.all()
        page = request.GET.get('page', 1)
        paginator = Paginator(workhourslist, g_page_no)
        try:
            work = paginator.page(page)
        except PageNotAnInteger:
            work = paginator.page(1)
        except EmptyPage:
            work = paginator.page(paginator.num_pages)

        return render(request,'workhrslist.html',{'username':staff, 'form':work}) 
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def editworkhrs(request):
    if request.method == 'POST':         
        wid= request.POST.get('workid')
        hours= request.POST.get('workhours')
        objT = WorkingHours.objects.get(id = wid)
        objT.tothours = hours
        objT.save()
        return redirect(workhrs)
    else:
        wid =  request.GET.get('workid')
        row = WorkingHours.objects.get(id=wid)
        return JsonResponse(data={
            'labels': row.tothours
            })

@login_required(login_url='loginpage')
def addworkhrs(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 1:
        if request.method == 'POST':
            monthrange= request.POST.get('workhrs')
            total= request.POST.get('totalhrs')
            datetimeobject = datetime.datetime.strptime(monthrange,'%m/%Y')
            new_format1 = str(datetimeobject.strftime('%m-%Y'))

            # check if total hours already entered for month/year
            rows = WorkingHours.objects.filter(monthyear = new_format1)
            if rows.exists():
                msg = "Total hours already entered for the selected month-year"
                return render(request,'addworkhrs.html',{'username':staff,'error':msg})
                # error message
            else:       
                objW = WorkingHours()
                objW.monthyear = new_format1
                objW.tothours = total
                objW.save()
                workhourslist = WorkingHours.objects.all()
                return render(request,'workhrslist.html',{'username':staff, 'form':workhourslist}) 
        else:
            return render(request,'addworkhrs.html',{'username':staff}) 
    else:
        return render(request,'403.html',{'username':staff})

#super admin and hod uses the same function
@login_required(login_url='loginpage')
def tasklist(request):
    staff = User.objects.get(id=request.session['userid']) 
    pmid = 0
    projectid = 0
    taskdate = ""
    
    if staff.usertype == 1 or staff.usertype == 2:
        if request.method == 'POST':
            projectid= request.POST.get('projectid')
            taskdate= request.POST.get('taskdatepicker')
            pmid = request.POST.get('projectmanagerid')

            if taskdate:
                datetimeobject = datetime.datetime.strptime(taskdate,'%m/%Y')

            if taskdate and int(projectid) != 0 and int(pmid)!=0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid),PMId=pmid,startdate__year=datetimeobject.year,startdate__month=datetimeobject.month)
            elif taskdate and int(projectid) == 0 and int(pmid) == 0:
                rows = Task.objects.all().filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month)
            elif taskdate and int(projectid) != 0 and int(pmid)==0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month)
            elif taskdate and int(projectid) == 0 and int(pmid)!=0:
                rows = Task.objects.all().filter(PMId=pmid,startdate__year=datetimeobject.year,startdate__month=datetimeobject.month)
            elif taskdate=="" and int(projectid) != 0 and int(pmid)!=0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid),PMId=pmid)
            elif taskdate=="" and int(projectid) == 0 and int(pmid)!=0:
                rows = Task.objects.all().filter(PMId=pmid)
            elif taskdate=="" and int(projectid) != 0 and int(pmid)==0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid))
            else:
                rows = Task.objects.all().order_by('startdate') 
        else:
            rows = Task.objects.all().order_by('startdate')
        
        allocatedprojects = PMProjects.objects.all()
        pm = User.objects.all().filter(is_projectmanager=True)

        page = request.POST.get('pagep')
        paginator = Paginator(rows, g_page_no)
        try:
            tasklist = paginator.page(page)
        except PageNotAnInteger:
            tasklist = paginator.page(1)
        except EmptyPage:
            tasklist = paginator.page(paginator.num_pages)

        return render(request,'admin_view_tasklist.html',{'username':staff,'form':tasklist,'projects':allocatedprojects,'pm':pm,'pmid':int(pmid),'pjid':int(projectid),'tdate':taskdate})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def exportcsv(request):   
    selecteddate  = request.GET.get('mn_yr') 
    new = selecteddate.replace("_", "/")

    datetimeobject = datetime.datetime.strptime(new,'%m/%Y')
    filename = 'R&DEq_'+selecteddate+'.csv'
    staff = User.objects.get(id=request.session['userid']) 
  
    response = HttpResponse(content_type='text/csv')  
    response['Content-Disposition'] = 'attachment; filename="'+filename+'"'  

    rows = Task.objects.all().filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month)
    writer = csv.writer(response)  
    writer.writerow(["NAME","PROJECT","REPORTING HEAD","DATE","DURATION","CATEGORY","TASK TYPE","DESCRIPTION", "STATUS"])
    for row in rows: 
        projectmanager = User.objects.get(id=row.PMId.id)
        if row.work_status == True:
            work_status = "Completed"
        else:
            work_status = "In progress"

        writer.writerow([row.userid.first_name,row.projectid.project,projectmanager.first_name,row.startdate,row.hours,row.catid.category,row.subcatid.subcategory,row.description, work_status])  
    return response  

@login_required(login_url='loginpage')
def barclick(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y') 
    staffname = request.GET.get('fn')
    staffhrs = request.GET.get('shrs')
    pmid = request.GET.get('pmid')
    category = []
    desc = []
    hrs = []
    proj = []
    startdate = []
    user = User.objects.get(first_name=staffname)

    rows = Task.objects.all().filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=user.id)
    for entry in rows:
        category.append(entry.catid.category)
        desc.append(entry.description)
        hrs.append(entry.hours)
        proj.append(entry.projectid.project)
        startdate.append(entry.startdate)
    return JsonResponse(data={
        'category': category,
        'desc': desc,
        'hrs': hrs,
        'proj':proj,
        'startdate':startdate
        })

def exportmetric(request):
    # selecteddate = '09/2021'
    # datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y') 
    selecteddate  = request.GET.get('mn_yr') 

    new = selecteddate.replace("_", "/")
    datetimeobject = datetime.datetime.strptime(new,'%m/%Y') 
    datetime_object = datetime.datetime.strptime(str(datetimeobject.month), "%m")
    full_month_name = datetime_object.strftime("%B")
    full_year = str(datetimeobject.year)

    arrProjs = Projects.objects.all()

    arrUsers = User.objects.all().filter(is_staff =0, is_active=1)
    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output)
    ws = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True,'bg_color':'#87CEFA','border':1})
    border_format = workbook.add_format({'border':1})
    merge_format = workbook.add_format({'align': 'center','font_size':20,'font_name':'Trebuchet MS'})
    rowlabel_format = workbook.add_format({'bold': True,'bg_color':'#87CEFA','border':1})
    ws.set_column(0, 0, 30) 
    ws.merge_range('C2:L4', 'AGAPPE TRACKER SHEET - '+ full_month_name +' '+full_year, merge_format)

    ws.write(1, 0, "Delivered Month",bold)
    ws.write(1, 1, full_month_name+' '+full_year,bold)
    ws.write(3, 0, "Sum of actual efforts",bold)
    ws.write(3, 1, "Column labels",bold)
    ws.write(4, 0, "Row labels",rowlabel_format)
   
    row_num = 4 #0
    col_num = 1
    for x in arrUsers:
        ws.write(row_num, col_num, x.first_name,rowlabel_format) #1/1,2,3
        col_num = col_num+1

    for j in arrProjs:
        row_num += 1
        ws.write(row_num, 0, j.project,border_format) #2/3/4
    ws.write(row_num+1, 0, "Grand Total",border_format)

    col_num = 1
    for x in arrUsers:
        row_num = 5
        for j in arrProjs:
            queryset = Task.objects.filter(userid=x.id,projectid=j.id,startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
            ws.write(row_num, col_num, queryset['hours__sum'],border_format)
            row_num += 1
        col_num += 1

    ws.write(4, col_num, 'Grand Total',bold)

    row_i = 5
    sum_pro = 0
    for j in arrProjs:
        queryset = Task.objects.filter(projectid=j.id,startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
        ws.write(row_i,col_num,queryset['hours__sum'],border_format)
        if queryset['hours__sum'] is None:
            queryset['hours__sum'] = 0
        sum_pro += queryset['hours__sum']
        row_i += 1

    col_i = 1
    sum_user = 0
    for x in arrUsers:
        queryset = Task.objects.filter(userid=x.id,startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
        ws.write(row_num,col_i,queryset['hours__sum'],border_format)
        if queryset['hours__sum'] is None:
            queryset['hours__sum'] = 0
        sum_user += queryset['hours__sum']
        col_i += 1

    if sum_user == sum_pro:
        ws.write(row_i,col_i,sum_user)
    else:
        ws.write(row_i,col_i,'Error')

        # Close the workbook before sending the data.
    workbook.close()
        # Rewind the buffer.
    output.seek(0)
        # Set up the Http response.
    filename = 'django_simple.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response   

#STAFF LOGIN
@login_required(login_url='loginpage')
def employeehome(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 4:
        today = datetime.date.today()
        current = str(today.strftime("%m")) +'/'+str(today.year)
        try:
            objMembership = TeamMembership.objects.get(staffid=request.session['userid'])
        except TeamMembership.DoesNotExist:
            objMembership = None
        if objMembership!=None:
            #else:
            id_pm = objMembership.teamid.PMid.id
            projectmanager = User.objects.get(id=objMembership.teamid.PMid.id)  
            rows1 = Team.objects.filter(PMid=id_pm)
            for x in rows1:
                selectedteammates = x.members.all()
            return render(request, 'empDashboard.html',{'username':staff, 'current':current,'pm':projectmanager,'team':selectedteammates})
        else:
            return render(request,'empDashboard.html',{'username':staff, 'current':current,'msg':"Not assigned to any team"})    
    else:
        return render(request,'403.html',{'username':staff})

def myprofile(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 4: 
        if request.method == 'POST':
            objUser = User.objects.get(id=request.POST.get('userid'))
            objUser.first_name = request.POST.get('first_name')
            objUser.email = request.POST.get('email')
            objUser.empcode = request.POST.get('empcode')
            objUser.empmobile = request.POST.get('empmobile')
            objUser.save()
            msg="Successfully updated!"
        else:
            objUser = User.objects.get(id=staff.id)
            msg=""
        return render(request,'viewprofile.html',{'objUser':objUser,'username':staff,'msg':msg})
    else:
        return render(request,'403.html',{'username':staff})

def chgpwd(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 4:
        if request.method == 'POST':        
            current_password = request.POST.get('current_pwd')
            new_pwd = request.POST.get('new_pwd')
            conf_pwd = request.POST.get('confirm_pwd')
            user = authenticate(request,username=staff.email,password=current_password)
            msg=""
            err=""
            if user is not None:
                objUser = User.objects.get(id=staff.id)
                if new_pwd == conf_pwd:
                    objUser.set_password(new_pwd)
                    objUser.save()
                    msg = "Password changed successfully"
                else:
                    err = "Password mismatch"
            else:
                err="Login password does not match with the current records"
            return render(request,'chgpwd.html',{'username':staff,'msg':msg,'err':err})
        else:     
            return render(request,'chgpwd.html',{'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addtask(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 4: 
        projects = PMProjects.objects.all()
        category = TaskCategory.objects.all()
        firstcategory = TaskCategory.objects.all().first()
        subcategory = TaskSubCategory.objects.filter(CatId = firstcategory.id)
        msg=""
        totalhrsentered=0
        try:
            objMembership = TeamMembership.objects.get(staffid=request.session['userid'])
        except TeamMembership.DoesNotExist:
            objMembership = None
        
        if objMembership != None:
            id_pm = objMembership.teamid.PMid.id
            projectmanager = User.objects.get(id=objMembership.teamid.PMid.id)

        if request.method == 'POST':
            #check if the total hours entered for the selected month is less than or equal to the actual working hours set by admin
            taskdate= request.POST.get('taskdate')
            #fetch total hours entered for this month in the tasks table for the logged in user
            datetimeobject = datetime.datetime.strptime(taskdate,'%m/%d/%Y')
            staffworkinghrs = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
            #totalhrsentered = staffworkinghrs['hours__sum']
            if(staffworkinghrs['hours__sum']):
                totalhrsentered = staffworkinghrs['hours__sum']
            else:
                totalhrsentered = 0

            duration = request.POST.getlist('duration[]')

            #calculate the hours entered for the current date
            sum1=0
            for hrs in duration:
                sum1+=int(hrs)

            #sum of already entered hours and currently entered hours
            totalhrsemp = totalhrsentered + sum1

            # fetch the total working  hours from workinghours table for the selected month
            new_format1 = str(datetimeobject.strftime('%m-%Y'))      
            totalworkinghrs = WorkingHours.objects.get(monthyear = new_format1)
            totalhours = totalworkinghrs.tothours

            if totalhrsemp <= totalhours:
                #insert intotask table
                projId = request.POST.getlist('projectid[]')
                catId = request.POST.getlist('id_category[]')
                subcatId = request.POST.getlist('id_subcategory[]')
                description = request.POST.getlist('description[]')
                comments = request.POST.getlist('comments[]')
                work_status = request.POST.getlist('work_status[]')
                #duration = request.POST.getlist('duration[]')
                cnt = len(projId)
                
                new_format1 = str(datetimeobject.strftime('%Y-%m-%d'))

                for i in range(cnt):
                    # collectedhours = checkIfHoursExceeded(request,new_format1,duration[i]) 
                    addTask = Task.objects.create(PMId = User.objects.get(id=id_pm),startdate=new_format1,enddate=new_format1,
                        hours=duration[i],description=description[i],comments=comments[i],work_status=work_status[i],
                        catid=TaskCategory.objects.get(id=catId[i]),projectid=Projects.objects.get(id=projId[i]),
                        subcatid=TaskSubCategory.objects.get(id=subcatId[i]),
                        userid=User.objects.get(id=request.session['userid']))

                rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']))    
                return render(request,'tasks.html',{'username':staff,'form':rows,'pm':projectmanager})            
            else:
                #alert error message telling total hours will exceed the actual working hours
                projects = PMProjects.objects.all()
                category = TaskCategory.objects.filter(forpm = 0)
                firstcategory = TaskCategory.objects.filter(forpm = 0).first()
                subcategory = TaskSubCategory.objects.filter(CatId = firstcategory.id)
                msg = "Total hours entered for this month will exceed the actual working hours. Please recheck."
            return render(request,'addtask.html',{'username':staff,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory,'pm':projectmanager,'error':msg})       


        else:
            if objMembership != None:
                today = datetime.date.today()
                current = str(today.month) +'/'+str(today.day)+'/'+str(today.year)
                num_days = monthrange(int(today.year), int(today.month))[1] # num_days = 28
                mindate = str(today.month)+'/01/'+str(today.year)
                maxxdate = str(today.month)+'/'+str(num_days)+'/'+str(today.year)

                return render(request,'addtask.html',{'username':staff,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory,'pm':projectmanager,'current':current,'mindate':mindate,'maxxdate':maxxdate})       
            else:
                return render(request,'index.html',{'username':staff,'msg':"You are not assigned to any team"})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def tasks(request):
    staff = User.objects.get(id=request.session['userid'])
    projectid = 0
    taskdate = ""
    if staff.usertype == 4:  
        if request.method == 'POST':
            projectid= request.POST.get('projectid')
            taskdate= request.POST.get('taskdatepicker')
            if taskdate:
                datetimeobject = datetime.datetime.strptime(taskdate,'%m/%Y')
            if taskdate and int(projectid) != 0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            elif taskdate and int(projectid) == 0:
                rows = Task.objects.all().filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            elif taskdate=='' and int(projectid) != 0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=projectid),userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            else:
                rows = Task.objects.all().filter(userid = User.objects.get(id=request.session['userid'])).order_by('startdate') 
        else:
            rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
        
        #page = request.GET.get('page', 1)
        page = request.POST.get('pagep')
        paginator = Paginator(rows, g_page_no)
        try:
            tasklist = paginator.page(page)
        except PageNotAnInteger:
            tasklist = paginator.page(1)
        except EmptyPage:
            tasklist = paginator.page(paginator.num_pages)

        try:
            objMembership = TeamMembership.objects.get(staffid=request.session['userid'])
        except TeamMembership.DoesNotExist:
            objMembership = None

        #getPMId = TeamMembership.objects.get(staffid=request.session['userid'])
        if objMembership!=None:
            id_pm = objMembership.teamid.PMid.id
            projectmanager = User.objects.get(id=objMembership.teamid.PMid.id)  
            allocatedprojects = PMProjects.objects.all()
            return render(request,'tasks.html',{'username':staff,'form':tasklist,'pm':projectmanager,'projects':allocatedprojects,'pjid':int(projectid),'taskdate':taskdate})
        else:
            return render(request,'tasks.html',{'username':staff,'form':tasklist, 'msg':"You are not assigned to any team"})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def taskdelete(request):
    taskId = request.GET.get('tid')
    rows1 = Task.objects.filter(id=taskId).delete()
    return HttpResponse(json.dumps(rows1[0]), content_type="application/json")

@login_required(login_url='loginpage')
def taskupdate(request):
    staff = User.objects.get(id=request.session['userid'])     
    projects = PMProjects.objects.all()
    category = TaskCategory.objects.all()
    
    taskId = request.GET.get('taskId')
    tasks = Task.objects.get(id=taskId)
    subcategory = TaskSubCategory.objects.filter(CatId = tasks.catid)
    html = render_to_string('taskupdate.html', {'username':staff,'tasks':tasks,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory},request = request)
    return HttpResponse(html)

@login_required(login_url='loginpage')
def taskedited(request):
    staff = User.objects.get(id=request.session['userid'])
    if request.method == 'POST':
        taskId = request.POST.get('taskId')
        obj = Task.objects.get(id=taskId)
        #check if the total hours entered for the selected month is less than or equal to the actual working hours set by admin
        taskdate= obj.startdate
        #fetch total hours entered for this month in the tasks table for the logged in user
        datetimeobject = datetime.datetime.strptime(str(taskdate),'%Y-%m-%d')
        staffworkinghrs = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
        #totalhrsentered = staffworkinghrs['hours__sum']
        if(staffworkinghrs['hours__sum']):
            totalhrsentered = staffworkinghrs['hours__sum']
        else:
            totalhrsentered = 0

        duration = request.POST.get('duration')

        #sum of already entered hours and currently entered hours
        totalhrsemp = totalhrsentered + int(duration)

        # fetch the total working  hours from workinghours table for the selected month
        new_format1 = str(datetimeobject.strftime('%m-%Y'))      
        totalworkinghrs = WorkingHours.objects.get(monthyear = new_format1)
        totalhours = totalworkinghrs.tothours

        if totalhrsemp <= totalhours:
            #insert intotask table
            projId = request.POST.get('projectid')
            catId = request.POST.get('id_category')
            subcatId = request.POST.get('id_subcategory')
            description = request.POST.get('description')
            comments = request.POST.get('comments')
            work_status = request.POST.get('work_status')        
            new_format1 = str(datetimeobject.strftime('%Y-%m-%d'))

            objT = Task.objects.get(id=taskId)
            objT.startdate = new_format1
            objT.enddate = new_format1
            objT.hours = duration
            objT.description = description
            objT.comments = comments
            objT.work_status = work_status
            objT.catid = TaskCategory.objects.get(id=catId)
            objT.subcatid = TaskSubCategory.objects.get(id=subcatId)
            objT.projectid = Projects.objects.get(id=projId)
            objT.save()
            return redirect(tasks)
         
        # else:
            #alert error message telling total hours will exceed the actual working hours
            # projects = Projects.objects.all()
            # category = TaskCategory.objects.all()            
            # task = Task.objects.get(id=taskId)
            # subcategory = TaskSubCategory.objects.filter(CatId = task.catid)
            # msg = "Total hours entered for this month will exceed the actual working hours. Please recheck."
            # html = render_to_string('taskupdate.html', {'username':staff,'tasks':task,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory,'error':msg},request = request)
            # return HttpResponse(html)           

#COMMON FUNCTIONS
def checkIfHoursExceeded(request,taskdate, hourInput): 
    rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate=taskdate).aggregate(Sum('hours'))
    return rows['hours__sum']

def checkIfHoursExceededForUpdate(request,taskdate, hourInput,hoursin): 
    rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate=taskdate).aggregate(Sum('hours'))
    return rows['hours__sum'] - int(hoursin)

def load_categories(request):
    category_id = request.GET.get('id')
    result = list(TaskSubCategory.objects.filter(CatId=int(category_id)).values('id', 'subcategory'))
    return HttpResponse(json.dumps(result), content_type="application/json")

def checkhours(request):
    hourInput = request.GET.get('hrs')
    send_date = request.GET.get('dta')
    datetimeobject = datetime.datetime.strptime(send_date,'%m/%d/%Y')
    new_format1 = str(datetimeobject.strftime('%Y-%m-%d'))
    if request.GET.get('tid'):
        row = Task.objects.get(id=request.GET.get('tid')) 
        collectedhours = checkIfHoursExceededForUpdate(request,new_format1, hourInput,row.hours)
    else:
        collectedhours = checkIfHoursExceeded(request,new_format1, hourInput)
    return HttpResponse(json.dumps(collectedhours), content_type="application/json")

@login_required(login_url='loginpage')
def HoursContributedCurrentMonth(request,staffid):
    today = datetime.date.today()
    datetimeobject = datetime.datetime.strptime(str(today),'%Y-%m-%d')
    new_format1 = str(datetimeobject.strftime('%m-%Y'))
    pass

@login_required(login_url='loginpage')
def pmprojectsedit (request):
    staff = User.objects.get(id=request.session['userid']) 
    projectmanagers = User.objects.all().filter(is_projectmanager=True)    

    msg = ""
    if request.method == 'POST': 
        pmprojId = request.POST.get('pmprojectsId')
        pmid = request.POST.get('pmUserId')
        projId = request.POST.get('projId')
        # returns all the projects assigned to that PM
        #
        exists = PMProjects.objects.filter(projectid=projId).first()
        if exists:
            obj = PMProjects.objects.get(id=pmprojId) 
            obj.PMId = User.objects.get(id=pmid)
            obj.projectid = Projects.objects.get(id=projId)
            obj.save()
            return redirect(assignedprojectlist)

#HOD LOGIN
@login_required(login_url='loginpage')
def hodhome(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 2: 
        today = datetime.date.today()
        current = str(today.strftime("%m")) +'/'+str(today.year)
        return render(request, 'hodDashboard.html',{'username':staff, 'current':current})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def pmlist(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 2:
        projectmanagers = User.objects.all().filter(is_projectmanager=True)
        teams = Team.objects.all()
        mems = TeamMembership.objects.all()
        pmprojects = PMProjects.objects.all()
        if request.method == 'POST':
            current = request.POST.get('monthcalendar1')
        else:
            today = datetime.date.today()
            current = str(today.month) +'/'+str(today.year)
        return render(request, 'pmlist.html',{'username':staff, 'teams':teams,'mems':mems,'pmprojects':pmprojects,'current':current})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def admindrawchart(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  

    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []

    pjts = PMProjects.objects.all()
    for x in pjts:
        labels.append(x.projectid.project)
        queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,projectid=x.projectid.id).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

#for drawing bar chart for project managers in HOD log in
@login_required(login_url='loginpage')
def pmteamchart(request):
    selecteddate =  request.GET.get('mn_yr')
    passedpmid = request.GET.get('xpmid')

    pm_query=Team.objects.filter(PMid=passedpmid)
    for x in pm_query:
        selectedteammates = x.members.all()

    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  
    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []

    user = User.objects.get(id=passedpmid)
    labels.append(user.first_name)
    queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=passedpmid).aggregate(Sum('hours'))
    data.append(queryset['hours__sum'])

    for tem in selectedteammates:
        userid = tem.id
        user = User.objects.get(id=userid)
        labels.append(user.first_name)
        queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=userid).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required(login_url='loginpage')
def drawchart(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  

    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []

    queryset = Task.objects.values('projectid__project').annotate(projectid_hours=Sum('hours')).order_by('-projectid_hours').filter(userid=User.objects.get(id=request.session['userid']),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month )
    for entry in queryset:
        labels.append(entry['projectid__project'])
        data.append(entry['projectid_hours'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required(login_url='loginpage')
def adminstaffchart(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  
    labels = []
    data = []

    getusers = User.objects.all().filter(is_staff =0, is_active=1)
    for user in getusers:
        labels.append(user.first_name)
        queryset = Task.objects.filter(userid = User.objects.get(id=user.id),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

def test(request):
    return render(request, 'test.html')

def mail(request):
    subject = 'Test mail'
    message = 'ii alllllgdhgsjhas'
    to = 'shinyjoysimon@gmail.com'
    res = send_mail(subject,message, settings.EMAIL_HOST_USER,[to])
    if res == 1:
        message = 'sent success'
    else:
        message = 'failed sending'
    return HttpResponse(message)

    #######FROM ANJITH############

#PM LOGIN 
@login_required(login_url='loginpage')
def pmhome(request):
    staff = User.objects.get(id=request.session['userid']) 
    if staff.usertype == 3:
        today = datetime.date.today()
        current = str(today.strftime("%m")) +'/'+str(today.year)
        return render(request, 'pmDashboard.html',{'username':staff, 'current':current})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def pmchart(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  
 
    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []

    pjts = PMProjects.objects.filter(PMId=request.session['userid'])
    useridpm=request.session['userid']
    for x in pjts:
        labels.append(x.projectid.project)
        queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=useridpm,projectid=x.projectid.id).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])
 
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })
 
@login_required(login_url='loginpage')
def projectpmchart(request):
    selecteddate =  request.GET.get('mn_yr')
    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  
 
    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []
    pjts = PMProjects.objects.filter(PMId=request.session['userid'])
    useridpm=request.session['userid']
    for x in pjts:
        labels.append(x.projectid.project)
        queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,projectid=x.projectid.id).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])
 
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })
 
@login_required(login_url='loginpage')
def teamsforpm(request):
    staff = User.objects.get(id=request.session['userid'])
    if staff.usertype == 3:
        pm_query=Team.objects.filter(PMid=staff.id)
        for x in pm_query:
            selectedteammates = x.members.all()
        return render(request,'teamsforpm.html',{'form':selectedteammates,'username':staff})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def addtaskpm(request):    
    staff = User.objects.get(id=request.session['userid']) 
    today = datetime.date.today()
    new_format1 = str(today.strftime('%Y-%m'))
    current = str(today.strftime("%m")) +'-'+str(today.year)
    num_days = monthrange(int(today.year), int(today.month))[1] # num_days = 28
    mindate = str(today.month)+'/01/'+str(today.year)
    maxxdate = str(today.month)+'/'+str(num_days)+'/'+str(today.year)

    if staff.usertype == 3:
        projects = PMProjects.objects.filter(PMId_id=staff.id)
        if request.method == 'POST':
            taskdate= request.POST.get('taskdate')
            taskenddate= request.POST.get('taskenddate')
            projId = request.POST.getlist('projectid[]')

            catId = request.POST.getlist('id_category[]')
            subcatId = request.POST.getlist('id_subcategory[]')
            description = request.POST.getlist('description[]')
            comments = request.POST.getlist('comments[]')
            work_status = request.POST.getlist('work_status[]')
            duration = request.POST.getlist('duration[]')
            cnt = len(projId)
            
            datetimeobject = datetime.datetime.strptime(taskdate,'%m/%d/%Y')
            new_format1 = str(datetimeobject.strftime('%Y-%m-%d'))
            datetimeobject1 = datetime.datetime.strptime(taskenddate,'%m/%d/%Y')
            new_format2 = str(datetimeobject1.strftime('%Y-%m-%d'))


            for i in range(cnt):
                addTask = Task.objects.create(PMId = User.objects.get(id=g_hod_id),startdate=new_format1,enddate=new_format2,
                    hours=duration[i],description=description[i],comments=comments[i],work_status=work_status[i],
                    catid=TaskCategory.objects.get(id=catId[i]),projectid=Projects.objects.get(id=projId[i]),
                    subcatid=TaskSubCategory.objects.get(id=subcatId[i]),
                    userid=User.objects.get(id=request.session['userid']))

            rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']))
            return redirect(taskspm)    
            #return render(request,'taskspm.html',{'username':staff,'form':rows,'listprojects':projects,'current':current})
        else:        
            projects = PMProjects.objects.filter(PMId_id=staff.id)
            date = datetime.date.today()
            new_format1 = str(date.strftime('%m-%Y'))

            category = TaskCategory.objects.filter(forpm = 1)
            firstcategory = TaskCategory.objects.filter(forpm = 1).first()
            subcategory = TaskSubCategory.objects.filter(CatId = firstcategory.id)
            tothours = WorkingHours.objects.get(monthyear = new_format1)
            return render(request,'addtaskpm.html',{'username':staff,'tothours':tothours.tothours,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory,'mindate':mindate,'maxxdate':maxxdate})       
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def taskspm(request):
    staff = User.objects.get(id=request.session['userid']) 
    current = ""
    pjct = 0
    if staff.usertype == 3:
        projects = PMProjects.objects.filter(PMId_id=staff.id)

        if request.method == 'POST':
            seekmonth = request.POST.get('monthyear')
            pjct = request.POST.get('projectid')
            current = seekmonth
            if seekmonth:
                datetimeobject = datetime.datetime.strptime(seekmonth,'%m-%Y')
            if seekmonth and int(pjct) != 0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=pjct),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            elif seekmonth and int(pjct) == 0:
                rows = Task.objects.all().filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            elif seekmonth=='' and int(pjct) != 0:
                rows = Task.objects.all().filter(projectid=Projects.objects.get(id=pjct),userid = User.objects.get(id=request.session['userid'])).order_by('startdate')  
            else:
                rows = Task.objects.all().filter(userid = User.objects.get(id=request.session['userid'])).order_by('startdate') 
        else:
            today = datetime.date.today()
            new_format1 = str(today.strftime('%Y-%m'))
            current = str(today.strftime("%m")) +'-'+str(today.year)
            rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate__contains=new_format1)  
            
        #page = request.GET.get('page', 1)
        page = request.POST.get('pagep')
        paginator = Paginator(rows, g_page_no)
        try:
            tasklist = paginator.page(page)
        except PageNotAnInteger:
            tasklist = paginator.page(1)
        except EmptyPage:
            tasklist = paginator.page(paginator.num_pages)

        return render(request,'taskspm.html',{'username':staff,'form':tasklist,'listprojects':projects,'current':current, 'pjid':int(pjct)})
    else:
        return render(request,'403.html',{'username':staff})

@login_required(login_url='loginpage')
def taskdeletepm(request):
    taskId = request.GET.get('tid')
    rows1 = Task.objects.filter(id=taskId).delete()
    return HttpResponse(json.dumps(rows1[0]), content_type="application/json")

@login_required(login_url='loginpage')
def viewmemberstask(request):
    staff = User.objects.get(id=request.session['userid'])
    seekmonth = "" 
    sid = 0
    if staff.usertype == 3:
        if request.method == 'POST':        
            seekmonth = request.POST.get('monthyear')
            if seekmonth == "":
                rows = Task.objects.all().filter(PMId=User.objects.get(id=request.session['userid'])).order_by('startdate') 
            else:
                datetimeobject = datetime.datetime.strptime(seekmonth,'%m/%Y')
                rows = Task.objects.all().filter(PMId=User.objects.get(id=request.session['userid']),startdate__year=datetimeobject.year,startdate__month=datetimeobject.month).order_by('startdate') 
        else:
            date = datetime.date.today()
            new_format1 = str(date.strftime('%Y-%m'))
            if request.GET.get('sid'):
                rows = Task.objects.filter(startdate__contains=new_format1, PMId=User.objects.get(id=request.session['userid']),userid=User.objects.get(id=request.GET.get('sid')))
            else:
                rows = Task.objects.filter(startdate__contains=new_format1, PMId=User.objects.get(id=request.session['userid']))  

        #page = request.GET.get('page', 1)
        page = request.POST.get('pagep',1)#g_page_no
        paginator = Paginator(rows, g_page_no)
        
        try:
            tasklist = paginator.page(page)
        except PageNotAnInteger:
            tasklist = paginator.page(1)
        except EmptyPage:
            tasklist = paginator.page(paginator.num_pages)

        return render(request,'viewmemberstask.html',{'username':staff,'form':tasklist, 'seekmonth':seekmonth})
    else:
        return render(request,'403.html',{'username':staff})

def checkIfHoursExceededpm(request,hourInput): 
    date = datetime.date.today()
    new_format1 = str(date.strftime('%Y-%m'))
    rows = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate__contains=new_format1).aggregate(Sum('hours'))
    return rows['hours__sum']

def checkhourspm(request):
    hourInput = request.GET.get('hrs')
    send_date = request.GET.get('dta')
    taskidcur = request.GET.get('tid')
    if request.GET.get('tid'):
        taskhours = Task.objects.get(id=taskidcur)
        taskhoursforminus = int(taskhours.hours)
        
    else: 
        taskhoursforminus=0 

    date = datetime.date.today()
    new_format1 = str(date.strftime('%m-%Y'))
    tothours = WorkingHours.objects.get(monthyear=new_format1)
    totalhours = tothours.tothours
    collectedhours = checkIfHoursExceededpm(request,hourInput)
    if(collectedhours is None):
        collectedhours=0
   
    cumulative = int(hourInput) + int(collectedhours) - taskhoursforminus
    
    if  cumulative > int(totalhours):
        if int(collectedhours) <= 0:
            collectedhours = 1
        flagreturn = int(collectedhours)
    else:
        flagreturn = 0
    return HttpResponse(json.dumps(flagreturn), content_type="application/json")

@login_required(login_url='loginpage')
def myteamchart(request):
    selecteddate =  request.GET.get('mn_yr')
    passedpmid = request.session['userid']

    pm_query=Team.objects.filter(PMid=passedpmid)
    for x in pm_query:
        selectedteammates = x.members.all()

    datetimeobject = datetime.datetime.strptime(selecteddate,'%m/%Y')  
    staff = User.objects.get(id=request.session['userid']) 
    labels = []
    data = []

    user = User.objects.get(id=passedpmid)
    labels.append(user.first_name)
    queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=passedpmid).aggregate(Sum('hours'))
    data.append(queryset['hours__sum'])

    for tem in selectedteammates:
        userid = tem.id
        user = User.objects.get(id=userid)
        labels.append(user.first_name)
        queryset = Task.objects.filter(startdate__year=datetimeobject.year,startdate__month=datetimeobject.month,userid=userid).aggregate(Sum('hours'))
        data.append(queryset['hours__sum'])
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required(login_url='loginpage')
def taskupdatepm(request):
    staff = User.objects.get(id=request.session['userid'])     
    projects = PMProjects.objects.filter(PMId=request.session['userid'])
    category = TaskCategory.objects.filter(forpm=1)
    taskId = request.GET.get('taskId')

    whours = Task.objects.get(id=taskId)
    revdate = whours.startdate
    revdate1 = str(revdate)
    taskdatesub = revdate1.split('-')
    new_format1 = taskdatesub[1]+'-'+taskdatesub[0]

    tothours = WorkingHours.objects.get(monthyear = new_format1)
       
    tasks = Task.objects.get(id=taskId)
    subcategory = TaskSubCategory.objects.filter(CatId = tasks.catid)
    tothours1=tothours.tothours
    html = render_to_string('taskupdatepm.html', {'username':staff,'tasks':tasks,'listprojects':projects,'categorylist':category,'subcategorylist':subcategory,'tothours':tothours1},request = request)
    return HttpResponse(html)

@login_required(login_url='loginpage')
def taskeditedpm(request):
    staff = User.objects.get(id=request.session['userid'])
    if request.method == 'POST':
        taskId = request.POST.get('taskId')
        taskdate1 = Task.objects.get(id=taskId)
        if request.POST.get('taskId'):
            taskhours = Task.objects.get(id=taskId)
            taskhoursforminus = int(taskhours.hours)
        
        else: 
            taskhoursforminus=0 

        taskdate = taskdate1.startdate
        taskenddate = taskdate1.enddate
        taskdatestr = str(taskdate)
        datestart = taskdatestr[0:7]
        
        staffworkinghrs = Task.objects.filter(userid = User.objects.get(id=request.session['userid']),startdate__contains=datestart).aggregate(Sum('hours'))
        #totalhrsentered = staffworkinghrs['hours__sum']
        if(staffworkinghrs['hours__sum']):
            totalhrsentered = staffworkinghrs['hours__sum']
        else:
            totalhrsentered = 0

        duration = request.POST.get('duration')

        #sum of already entered hours and currently entered hours
        totalhrsemp = totalhrsentered + int(duration)-taskhoursforminus

        # fetch the total working  hours from workinghours table for the selected month
        dss = datestart.split('-')    
        new_format1 =  dss[1]+'-'+dss[0]
        totalworkinghrs = WorkingHours.objects.get(monthyear = new_format1)
        totalhours = totalworkinghrs.tothours

        if totalhrsemp <= totalhours:
            #insert intotask table
            projId = request.POST.get('projectid')
            catId = request.POST.get('id_category')
            subcatId = request.POST.get('id_subcategory')
            description = request.POST.get('description')
            comments = request.POST.get('comments')
            work_status = request.POST.get('work_status')        
            new_format1 = taskdate
            new_format2 = taskenddate

            objT = Task.objects.get(id=taskId)
            objT.startdate = new_format1
            objT.enddate = new_format2
            objT.hours = duration
            objT.description = description
            objT.comments = comments
            objT.work_status = work_status
            objT.catid = TaskCategory.objects.get(id=catId)
            objT.subcatid = TaskSubCategory.objects.get(id=subcatId)
            objT.projectid = Projects.objects.get(id=projId)
            objT.save()
            return redirect(taskspm)
         
