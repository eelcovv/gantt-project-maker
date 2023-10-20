# Example project

In order to compile all project planning just run:

    make

To see just the call to gannt_project_maker, do:

    make -n

This will show the following output:

    gantt_project_maker  projects.yml  --period all
    gantt_project_maker  projects.yml  --period all --employee emp1
    gantt_project_maker  projects.yml  --period all --employee emp2
    gantt_project_maker  projects.yml  --period all --employee emp3
    gantt_project_maker  projects.yml  --period all --export
    gantt_project_maker  projects.yml  --period all --resources
    gantt_project_maker  projects.yml  --period all --employee emp1 --resources
    gantt_project_maker  projects.yml  --period all --employee emp2 --resources
    gantt_project_maker  projects.yml  --period all --employee emp3 --resources
