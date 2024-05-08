
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm){
		frm.remove_custom_button(__("Fetch Timesheet"));
		if (frm.doc.docstatus === 0 && !frm.doc.is_return) {
			frm.add_custom_button(__("Fetch Timesheet"), function () {
				let d = new frappe.ui.Dialog({
					title: __("Fetch Timesheet"),
					fields: [
						{
							label: __("From"),
							fieldname: "from_time",
							fieldtype: "Date",
							reqd: 1,
						},
						{
							fieldtype: "Column Break",
							fieldname: "col_break_1",
						},
						{
							label: __("To"),
							fieldname: "to_time",
							fieldtype: "Date",
							reqd: 1,
						},
						{
							label: __("Project"),
							fieldname: "project",
							fieldtype: "Link",
							options: "Project",
							default: frm.doc.project,
						},
					],
					primary_action: function () {
						const data = d.get_values();
						frm.events.add_timesheet_data(frm, {
							from_time: data.from_time,
							to_time: data.to_time,
							project: data.project,
						});
						d.hide();
					},
					primary_action_label: __("Get Timesheets"),
				});
				d.show();
			}, __("Fetch Timesheet"));
		}

		frm.add_custom_button(__('Fetch and distribute Timesheet'), function () {
			frappe.prompt([
				{
					label: __("Timesheet Filters"),
					fieldname: "sec_brk_xt6tg",
					fieldtype: "Section Break",
				},
				{
					label: __("From"),
					fieldname: "from_time",
					fieldtype: "Date",
					reqd: 1,
				},
				{
					fieldname: "col_brk_xt6tg",
					fieldtype: "Column Break",		
				},
				{
					label: __("To"),
					fieldname: "to_time",
					fieldtype: "Date",
					reqd: 1,
				},
				{
					label: __("Distrubute timesheet Projectwise"),
					fieldname: "sec_brk_5b46",
					fieldtype: "Section Break",
				},
				{
					label: __("Item"),
					fieldname: "service_item",
					fieldtype: "Link",
					options: "Item",
					reqd: 1,
				},
				{
					label: __("Income Account"),
					fieldname: "income_account",
					fieldtype: "Link",
					options: "Account",
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
				frm.events.fetchtimesheet_and_distribute(frm, values);
			},
			__("Fetch and distribute Timesheet"),
			__("Distribute")
			);
		},
		__("Fetch Timesheet"));
    },

	fetchtimesheet_and_distribute: function (frm, kwargs) {
		debugger;

		frappe.call({
			method: "phamos_supplier_addon.overrides.timesheet.get_projectwise_timesheet_data",
			args: kwargs
		})
		.then((r) => {
			let timesheets = [];
			if (!r.exc && r.message.length > 0) {
				timesheets = r.message;
			} else {
				timesheets = [];
			}

			frm.clear_table("timesheets");
			timesheets.forEach(async (timesheet) => {
				if (frm.doc.currency != timesheet.currency) {
					const exchange_rate = await frm.events.get_exchange_rate(
						frm,
						timesheet.currency,
						frm.doc.currency
					);
					frm.events.custom_append_time_log(frm, timesheet, exchange_rate);
				} else {
					frm.events.custom_append_time_log(frm, timesheet, 1.0);
				}
			});
			frm.trigger("calculate_timesheet_totals");
			frm.refresh();
			frm.events.projectwise_costing_breakdown(frm, kwargs);
		});
	},

	projectwise_costing_breakdown: function(frm, kwargs){
		if (!frm.doc.timesheets.length > 0) {
			frappe.throw("Timesheet data is missing!");
		}
		
		let billingHoursByProject = {};
		let distributedAmountByProject = {};
		let service_item = kwargs.service_item;
		let timesheets = frm.doc.timesheets;
		let amt_to_distribute = kwargs.amt_to_distribute;
		let totalBillingHours = timesheets.reduce((total, timesheet) => total + timesheet.billing_hours, 0);

		timesheets.forEach(timesheet => {
			let projectId = timesheet.custom_project_id;
			if (!billingHoursByProject[projectId]) {
				billingHoursByProject[projectId] = 0;
			}
			billingHoursByProject[projectId] += timesheet.billing_hours;
		});
		
		// Distribute amount to each project based on their billing hours
		Object.keys(billingHoursByProject).forEach(projectId => {
			let projectBillingHours = billingHoursByProject[projectId];
			let projectRatio = projectBillingHours / totalBillingHours;
			let projectAmount = amt_to_distribute * projectRatio;
			distributedAmountByProject[projectId] = projectAmount;
		});

		let rows = Object.keys(distributedAmountByProject).map(key => {
			return {
				project: key,
				amount: distributedAmountByProject[key],
				billable_hours: billingHoursByProject[key]
			};
		});

		frm.clear_table("items");
		rows.forEach(row => {
			if (row.project && row.amount) {
				const item_row = frm.add_child("items");
				item_row.item_code = service_item;
				item_row.item_name = service_item + " " + row.project;
				item_row.description = service_item + " " + row.project;
				item_row.custom_billable_hours = row.billable_hours
				item_row.project = row.project;
				item_row.rate = row.amount;
				item_row.income_account = kwargs.income_account
				item_row.qty = 1
				item_row.uom = "Nos"
			}
		});
		frm.refresh_field("items");
	},

	custom_append_time_log: function (frm, time_log, exchange_rate) {
		const row = frm.add_child("timesheets");
		row.activity_type = time_log.activity_type;
		row.description = time_log.description;
		row.time_sheet = time_log.time_sheet;
		row.from_time = time_log.from_time;
		row.to_time = time_log.to_time;
		row.billing_hours = time_log.billing_hours;
		row.billing_amount = flt(time_log.billing_amount) * flt(exchange_rate);
		row.timesheet_detail = time_log.name;
		row.custom_project_id = time_log.custom_project_id;
		row.custom_phamos_project = time_log.custom_phamos_project;
		row.project_name = time_log.project_name;
	},
})