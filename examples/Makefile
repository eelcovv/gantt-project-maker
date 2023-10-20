resources_dir = output_resources
planning_dir = output_planning
excel_dir = output_excel

# define targets
target_global = $(planning_dir)/projects_all_tasks.svg
target_excel = $(excel_dir)/projects.xlsx
target_resources = $(resources_dir)/projects_all_resources.svg
targets_emp1 = $(planning_dir)/projects_emp1_all_tasks.svg
targets_emp2 = $(planning_dir)/projects_emp2_all_tasks.svg
targets_emp3 = $(planning_dir)/projects_emp3_all_tasks.svg

targets_emp1_resources = $(resources_dir)/projects_emp1_all_resources.svg
targets_emp2_resources = $(resources_dir)/projects_emp2_all_resources.svg
targets_emp3_resources = $(resources_dir)/projects_emp3_all_resources.svg

all_targets_tasks = $(target_global) \
					$(targets_emp1) \
					$(targets_emp2) \
					$(targets_emp3) \
all_targets_resources = $(target_resources) \
						$(targets_emp1_resources) \
						$(targets_emp2_resources) \
						$(targets_emp3_resources) \

targets = $(all_targets_resources) $(all_targets_tasks) $(target_excel)

settings_file_global = projects.yml
settings_file_emp1 = projects_emp1.yml
settings_file_emp2 = projects_emp2.yml
settings_file_emp3 = projects_emp3.yml

settings_files = $(settings_file_global) \
				 $(settings_file_emp1) \
				 $(settings_file_emp2) \
				 $(settings_file_emp3)

executable = gantt_project_maker

# default wordt alleen de volledige tijdsperiode gemaakt. Wil je ook 'einde_jaar' hebben, geef dan
# OPTIONS="--period einde_jaar"
# mee op de command line
default_options = --period all

ifdef OPTIONS
	options=$(default_options) $(OPTIONS)
else
	options=$(default_options)
endif

default: all

all_tasks: global emp1 emp2 emp3 xlsx
all_resources: resources emp1_resources emp2_resources emp3_resources

all: all_tasks all_resources

resources: $(target_resources)
$(target_resources): $(settings_files)
	$(executable)  $(settings_file_global)  $(options) --resources


xlsx: $(target_excel)
$(target_excel): $(settings_files)
	$(executable)  $(settings_file_global)  $(options) --export

global: $(target_global)
$(target_global): $(settings_files)
	$(executable)  $(settings_file_global)  $(options)

emp1: $(targets_emp1)
$(targets_emp1): $(settings_file_emp1)
	$(executable)  $(settings_file_global)  $(options) --employee emp1

emp1_resources: $(targets_emp1_resources)
$(targets_emp1_resources): $(settings_file_emp1)
	$(executable)  $(settings_file_global)  $(options) --employee emp1 --resources

emp2: $(targets_emp2)
$(targets_emp2): $(settings_file_emp2)
	$(executable)  $(settings_file_global)  $(options) --employee emp2

emp2_resources: $(targets_emp2_resources)
$(targets_emp2_resources): $(settings_file_emp2)
	$(executable)  $(settings_file_global)  $(options) --employee emp2 --resources

emp3: $(targets_emp3)
$(targets_emp3): $(settings_file_emp3)
	$(executable)  $(settings_file_global)  $(options) --employee emp3

emp3_resources: $(targets_emp3_resources)
$(targets_emp3_resources): $(settings_file_emp3)
	$(executable)  $(settings_file_global)  $(options) --employee emp3 --resources

clean_task:
	@$(foreach file, $(all_targets_tasks), test -f $(file) && rm -v $(file) || echo No $(file);)

clean_resources:
	@$(foreach file, $(all_targets_resources), test -f $(file) && rm -v $(file) || echo No $(file);)

clean_excel:
	@$(foreach file, $(target_excel), test -f $(file) && rm -v $(file) || echo No $(file);)

clean: clean_resources clean_task clean_excel
