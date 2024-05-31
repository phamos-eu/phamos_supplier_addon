# Copyright (c) 2024, phamos GmbH and contributors
# For license information, please see license.txt

import json
import frappe
import requests
from frappe import _
from frappe.utils import cstr
from frappe.model.document import Document

class RemoteServerConnector(Document):
	def __init__(self, *args, **kwargs):
		super(RemoteServerConnector, self).__init__(*args, **kwargs)
		self.enable = 0
		if self.url and self.usr and self.pwd:
			self.authenticate()
			self.enable = 1

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
		if response.ok and response.status_code == 200:
			frappe.msgprint(_("Successfully Authenticated"))
			cookies = response.cookies.get_dict()
			self.cookies = "; ".join([f"{key}={value}" for key, value in cookies.items()])
			self.cookie_headers = {"cookie": self.cookies}

		else:
			frappe.throw(_("Authentication Failed"))

	def fetch_timesheet_summary(self, from_date, to_date):
		url = f"{self.url}/api/method/frappe.desk.reportview.get"

		filters = json.dumps([["Timesheet","owner","=",self.usr],["Timesheet","creation","Between",[from_date,to_date]]])

		data = {
			'doctype': 'Timesheet',
			'fields': '["`tabTimesheet`.`project`"]',
			'filters': filters,
			'order_by': '_aggregate_column desc',
			'start': '0',
			'page_length': '1000',
			'view': 'Report',
			'with_comment_count': 'false',
			'aggregate_on_field': 'total_billable_hours',
			'aggregate_on_doctype': 'Timesheet',
			'aggregate_function': 'sum',
			'group_by': '`tabTimesheet`.`project`'
		}

		response = requests.request("POST", url, headers=self.cookie_headers, data=data)
		response_json = response.json().get("message").get("values")
		return response_json
