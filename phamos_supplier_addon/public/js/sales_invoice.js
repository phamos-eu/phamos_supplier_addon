
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm){
		frm.add_custom_button(
			__('Fetch and process work summary'), 
			function () {
			frappe.prompt([
				{
					label: __("Timesheet Filters"),
					fieldname: "sec_brk_xt6tg",
					fieldtype: "Section Break",
				},
				{
					label: __("From"),
					fieldname: "from_date",
					fieldtype: "Date",
					default: frappe.datetime.month_start(),
					reqd: 1,
				},
				{
					fieldname: "col_brk_xt6tg",
					fieldtype: "Column Break",		
				},
				{
					label: __("To"),
					fieldname: "to_date",
					fieldtype: "Date",
					default: frappe.datetime.month_end(),
					reqd: 1,
				},
				{
					fieldname: "sec_brk_5b46",
					fieldtype: "Section Break",
				},
				{
					label: __("Item"),
					fieldname: "service_item",
					fieldtype: "Link",
					options: "Item",
					default: "Development Service",
					reqd: 1,
				},
				{
					label: __("Income Account"),
					fieldname: "income_account",
					fieldtype: "Link",
					options: "Account",
					default: "Service EU - BN",
					reqd: 1,
				},
				{
					fieldname: "col_brk_5b46",
					fieldtype: "Column Break",		
				},
				{
					label: __("Amount to Distribute"),
					fieldname: "amt_to_distribute",
					fieldtype: "Currency",
					reqd: 1,
				}
			],
			(values) => {
				let amount = values.amt_to_distribute;
				if (amount < 1) {
					frappe.throw(__("Please set amount greate then 0"))
				}
				frappe.call({
					method: "phamos_supplier_addon.overrides.sales_invoice.fetch_and_process_work_summary",
					args: {
						"from_date": values.from_date,
						"to_date": values.to_date,
						"amount": values.amt_to_distribute
					},
					freeze: true,
					callback: function (r) {
						let service_item = values.service_item;
						let income_account = values.income_account
						if (r.message.work_summary.length > 1) {
							let work_summary = r.message.work_summary;
							frm.clear_table("items");
							work_summary.forEach(row => {
								const item_row = frm.add_child("items");
								item_row.item_code = service_item;
								item_row.item_name = service_item + " " + row.project;
								item_row.description = service_item + " " + row.project;
								item_row.custom_phamos_project = row.project;
								item_row.custom_phamos_project_name = row.project_name;
								item_row.income_account = income_account;
								item_row.rate = row.project_bill;
								item_row.custom_billable_hours = row.hours;
								item_row.qty = 1;
								item_row.amount = row.hours;
								item_row.uom = "Hour";
							});
							frm.refresh_field("items");
						} else {
							frappe.throw(__("No Data Found!"))
						}
					},
				})
			},
			__("Fetch and process work summary"),
			__("Fetch and process")
			);
			},
			__("Get Items From")
	);
    },
})