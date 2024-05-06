// Copyright (c) 2024, phamos GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on('Timesheet Fetching Tool', {
    refresh: function(frm){
		frm.add_custom_button(__('Fetch Timesheets'), function () {
			frappe.prompt(
				[
					{
						fieldname: "company",
						label: __("Company"),
						fieldtype: "Link",
						options: "Company",
						reqd: 1,
					},
					{
						fieldtype: "Column Break"
					},
					{
						fieldname: "from_date",
						label: __("From Date"),
						fieldtype: "Date",
						reqd: 1,
					},
					{
						fieldname: "to_date",
						label: __("To Date"),
						fieldtype: "Date",
						reqd: 1,
					}
				],
				function (data) {
					frappe.call({
						method: "fetch_timesheets_from_remote_server",
						doc:frm.doc,
						args: {
							company: data.company,
							from_date: data.from_date,
							to_date: data.to_date,
						},
						freeze: true,
						callback: function(r) {
							if(r.message) {
								// cur_frm.clear_table("closed_documents");
								// r.message.forEach(function(element) {
								// 	var c = frm.add_child("closed_documents");
								// 	c.document_type = element.document_type;
								// 	c.closed = element.closed;
								// });
								// refresh_field("closed_documents");
							}
						}
					});
				},
				__("Fetch Timesheets from remote server"),
				__("Fetch")
			);
		});
    }
});
