from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    #FOR STAFF
    path('employee', views.employeehome, name='employee'),
    path('drawchart', views.drawchart, name='drawchart'),
    path('myprofile',views.myprofile, name='myprofile'),
    path('chgpwd',views.chgpwd, name='chgpwd'),
    path('task', views.tasks),
    path('addtask', views.addtask),
    path('taskdelete', views.taskdelete),
    path('taskupdate', views.taskupdate),
    path('taskedited', views.taskedited),
    #FOR ADMIN
    path('admin', views.adminhome, name='admin'),
    path('admindrawchart', views.admindrawchart, name='admindrawchart'),
    path('adminstaffchart',views.adminstaffchart, name='adminstaffchart'),
    path('exportcsv', views.exportcsv),
    path('exportmetric', views.exportmetric),
    #Employees
    path('employees', views.employee, name='employees'),
    path('activate/', views.activateEmp),
    path('deactivate/', views.deactivateEmp),
    path('empadd', views.addemployee, name='add'),
    path('empupdate', views.empupdate, name='empupdate'),
    path('empedited',views.empedited, name='empedited'),
    #Teams
    path('teams', views.teams, name='teams'),
    path('viewteam/<int:id>', views.viewteam),
    path('addTeam', views.addteam, name='addteams'),
    path('updTeam/<int:pk>', views.editteam),
    #Category and subcategory
    path('category', views.category),
    path('addcategory', views.addcategory),
    path('editcategory',views.editcategory,name='editcategory'),
    path('subcategory', views.subcategory),
    path('addsubcategory', views.addsubcategory),
    path('editsubcat', views.editsubcategory),
    #project
    path('projects', views.projects),
    path('addproject', views.addproject),
    path('editproject',views.editproject,name='editproject'),
    path('assignedpjts',views.assignedprojectlist),
    path('assignpjt/',views.assignProject),
    path('assgnprojdel/', views.assgnprojdel),
    path('updproj', views.updproj),
    path('edit', views.pmprojectsedit),
    #work hours
    path('workhrs', views.workhrs),
    path('addworkhrs', views.addworkhrs, name='addworkhrs'),
    path('editworkhrs', views.editworkhrs,name='editworkhrs'),
    #Task
    path('task_list', views.tasklist,name='tasklist'),

    #FOR HEAD OF DEPT
    path('hod', views.hodhome, name='hod'),
    path('pm', views.pmlist),
    path('pmteamchart', views.pmteamchart,name='pmteamchart'),
    path('barclick',views.barclick,name='barclick'),

      
    path('subcategories/', views.load_categories), 
    path('checkhours/', views.checkhours),
    path('teamdelete/', views.teamdelete),
    path('teamupd/', views.teamupd),
    path('editTm/', views.showeditpage),

    path('test',views.test,name='test'),

    path('pmhome', views.pmhome, name='pmhome'), 
    path('pmchart', views.pmchart, name='pmchart'),
    path('projectpmchart', views.projectpmchart, name='projectpmchart'),
    path('teamsforpm', views.teamsforpm),
    path('viewmemberstask', views.viewmemberstask),
    path('taskpm', views.taskspm),
    path('addtaskpm', views.addtaskpm),
    path('taskdeletepm', views.taskdeletepm),
    path('taskupdatepm', views.taskupdatepm),
    path('checkhourspm/', views.checkhourspm),
    path('teamchart', views.myteamchart, name='teamchart'),
]