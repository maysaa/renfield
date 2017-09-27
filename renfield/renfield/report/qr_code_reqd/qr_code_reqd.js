// Copyright (c) 2016, Epoch and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["QR Code Reqd"] = {
	"filters": [
		{
			"fieldname":"creation",
			"label": __("Created On"),
			"fieldtype": "Date",
			"reqd": 1
		}
		
	]
}
