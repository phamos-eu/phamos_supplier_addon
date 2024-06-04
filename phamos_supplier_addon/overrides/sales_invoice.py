import json
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
        projects_name = json.loads(frappe.db.get_single_value("Remote Server Connector", "projects_name") or "{}") or {}
        work_summary = [
            {
                "project": project,
                "hours": hours,
                "project_bill": hours * hourly_rate,
                "project_name": get_project_name(project, projects_name, RSC)
            } for project, hours in work_summary if hours > 0 ]
        
        frappe.db.set_single_value("Remote Server Connector", "projects_name", json.dumps(projects_name), update_modified=False)
    return {"work_summary": work_summary}


def get_project_name(project, projects_name, RSC):
    if projects_name.get(project):
        return projects_name.get(project)
    else:
        project_doc = RSC.fetch_project(project)
        project_name = project_doc.get("project_name")
        projects_name[project] = project_name
        return project_name