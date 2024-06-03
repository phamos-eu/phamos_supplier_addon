import frappe
from frappe.utils import cstr, flt, cint
from phamos_supplier_addon.phamos_supplier_addon.doctype.remote_server_connector.remote_server_connector import RemoteServerConnector


@frappe.whitelist()
def fetch_and_process_work_summary(from_date, to_date, amount):
    RSC = RemoteServerConnector('Remote Server Connector', 'Remote Server Connector')
    work_summary = RSC.fetch_work_summary(from_date, to_date)

    total_hours = flt(sum([ project[1] for project in work_summary]))
    if total_hours > 0:
        hourly_rate = cint(amount)/ total_hours
        work_summary = [{"project": project, "hours": hours, "project_bill": hours * hourly_rate} for project, hours in work_summary if hours > 0 ]
        return {"work_summary": work_summary, "hourly_rate": hourly_rate}
