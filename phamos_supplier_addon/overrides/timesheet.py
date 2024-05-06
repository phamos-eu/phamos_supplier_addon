import frappe


@frappe.whitelist()
def get_projectwise_timesheet_data(project=None, parent=None, from_time=None, to_time=None):
	condition = ""
	if project:
		condition += "AND tsd.project = %(project)s "
	if parent:
		condition += "AND tsd.parent = %(parent)s "
	if from_time and to_time:
		condition += "AND CAST(tsd.from_time as DATE) BETWEEN %(from_time)s AND %(to_time)s"

	query = f"""
		SELECT
			tsd.name as name,
			tsd.parent as time_sheet,
			tsd.from_time as from_time,
			tsd.to_time as to_time,
			tsd.billing_hours as billing_hours,
			tsd.billing_amount as billing_amount,
			tsd.activity_type as activity_type,
			tsd.description as description,
			ts.currency as currency,
			tsd.project as custom_project_id,
			ts.custom_phamos_project as custom_phamos_project,
			tsd.project_name as project_name
		FROM `tabTimesheet Detail` tsd
			INNER JOIN `tabTimesheet` ts
			ON ts.name = tsd.parent
		WHERE
			tsd.parenttype = 'Timesheet'
			AND tsd.docstatus = 1
			AND tsd.is_billable = 1
			AND COALESCE(tsd.sales_invoice, '') = ''
			{condition}
		ORDER BY tsd.from_time ASC
	"""

	filters = {"project": project, "parent": parent, "from_time": from_time, "to_time": to_time}

	return frappe.db.sql(query, filters, as_dict=1, debug=1)