# Copyright (c) 2024, phamos GmbH and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.utils import cstr
import requests
from frappe.model.document import Document

class TimesheetFetchingTool(Document):
	@frappe.whitelist()
	def fetch_timesheets_from_remote_server(self, company, from_date, to_date):
		self.authenticate()
		self.get_timesheet_records(from_date, to_date)

		timesheet_list = list(self.timesheet_timesheet_records_dict.keys())
		timesheet_record_list = list(self.timesheet_timesheet_records_dict.values())

		for phamos_timesheet in timesheet_list:
			phamos_timesheet_record = self.timesheet_timesheet_records_dict.get(phamos_timesheet)
			url = f"{self.url}/api/resource/Timesheet/{phamos_timesheet}"
			response = requests.request("GET", url, headers=self.cookie_headers)
			timesheet_data = response.json().get("data")

			phamos_project = timesheet_data.get("project")
			project_id = get_project_id(phamos_project, company, self) if phamos_project else ""			

			if not frappe.db.exists("Timesheet", {"custom_phamos_timesheet": phamos_timesheet, "custom_phamos_timesheet_record": phamos_timesheet_record}):
				new_timesheet = frappe.new_doc("Timesheet")
				new_timesheet.update(timesheet_data)
				new_timesheet.employee = get_employee(timesheet_data.get("employee"), company, self) if timesheet_data.get("employee") else ""
				new_timesheet.custom_phamos_timesheet_record = phamos_timesheet_record
				new_timesheet.custom_phamos_timesheet = phamos_timesheet
				new_timesheet.company = company
				new_timesheet.custom_phamos_project = phamos_project
				new_timesheet.custom_phamos_project_id = project_id
				new_timesheet.customer = ""
				new_timesheet.parent_project = ""
				new_timesheet.name = ""
				new_timesheet.docstatus = 0
				new_timesheet.status = "Draft"
				for log in new_timesheet.time_logs:
					log.custom_phamos_timesheet_record = phamos_timesheet_record
					log.custom_phamos_timesheet = phamos_timesheet
					log.custom_phamos_project = phamos_project
					log.project = get_project_id(log.project, company, self) if log.project else ""
					log.task = ""
					log.activity_type = get_activity_type(log.get("activity_type")) if log.activity_type else ""
					log.sales_invoice = ""
				
				new_timesheet.insert()

	def authenticate(self):
		url = f"{self.url}/api/method/login"

		payload = {
			"usr": self.usr,
			"pwd": self.get_password(fieldname="pwd")
		}
		headers = {
			"Content-Type": "application/json",
		}

		response = requests.request("POST", url, json=payload, headers=headers)
		cookies = response.cookies.get_dict()
		self.cookies = "; ".join([f"{key}={value}" for key, value in cookies.items()])
		self.cookie_headers = {"cookie": self.cookies}

	def get_timesheet_records(self, from_date, to_date):
		fields = json.dumps(["name","timesheet"])
		filters = json.dumps([["owner","=",self.usr], ["creation","Between",[from_date, to_date]],["docstatus","=","1"]])
		url = f"{self.url}/api/resource/Timesheet Record?fields={fields}&filters={filters}&limit_page_length=1000&order_by=creation"
		response = requests.request("GET", url, headers=self.cookie_headers)
		data = response.json().get("data")
		self.timesheet_records_count = len(data)
		self.timesheet_records = data

		self.timesheet_timesheet_records_dict = {}
		for item in self.timesheet_records:
			self.timesheet_timesheet_records_dict[item['timesheet']] = item['name']


def get_project_id(phamos_project, company, timesheet_fetching_tool_doc):
	project_id = frappe.db.exists("Project", {"custom_phamos_project": phamos_project})
	if not project_id:
		url = f"{timesheet_fetching_tool_doc.url}/api/resource/Project/{phamos_project}"
		response = requests.request("GET", url, headers=timesheet_fetching_tool_doc.cookie_headers)
		project_data = response.json().get("data")

		new_project = frappe.new_doc("Project")
		new_project.update(project_data)
		new_project.custom_phamos_project = phamos_project
		new_project.expected_start_date = ""
		new_project.expected_end_date = ""
		new_project.cost_center = ""
		new_project.sales_order = ""
		new_project.department = ""
		new_project.customer = ""
		new_project.name = ""
		new_project.company = company
		new_project.insert()
		project_id = new_project.name
	
	return project_id


def get_employee(phamos_employee, company, timesheet_fetching_tool_doc):
	employee_id = frappe.db.exists("Employee", {"custom_phamos_employee": phamos_employee})
	if not employee_id:
		url = f"{timesheet_fetching_tool_doc.url}/api/resource/Employee/{phamos_employee}"
		response = requests.request("GET", url, headers=timesheet_fetching_tool_doc.cookie_headers)
		employee_data = response.json().get("data")

		new_employee = frappe.new_doc("Employee")
		new_employee.update(employee_data)
		new_employee.custom_activity_type = get_activity_type(employee_data.get("activity_type")) if employee_data.get("activity_type") else ""
		new_employee.custom_phamos_employee = phamos_employee
		new_employee.company = company
		new_employee.leave_approver = ""
		new_employee.holiday_list = ""
		new_employee.reports_to = ""
		new_employee.department = ""
		new_employee.user_id = ""
		new_employee.name = ""
		new_employee.insert()
		employee_id = new_employee.name
	
	return employee_id


def get_activity_type(activity_type):
	if not frappe.db.exists("Activity Type", activity_type):
		new_activity = frappe.new_doc("Activity Type")
		new_activity.activity_type = activity_type
		new_activity.insert()
	
	return activity_type