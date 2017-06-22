# Epoch Integrated solution for Royal Enfield Tracking system

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime


@frappe.whitelist()
def make_stock_entry(serial_no):
	
	innerJson = ""
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		veh_status = record.vehicle_status
		company = record.company

	if item:
		item_record = frappe.get_doc("Item", item)

	
	if veh_status == "Invoiced but not Received":

		newJson = {
			"company": company,
			"doctype": "Stock Entry",
			"title": "Material Receipt",
			"purpose": "Material Receipt",
	
			"items": [
			]
		}

	
		req_qty = 1
	
	
		innerJson =	{

				"doctype": "Stock Entry Detail",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,

				"t_warehouse": "Finished Goods - ES"
				  }
	
		newJson["items"].append(innerJson)

	
		doc = frappe.new_doc("Stock Entry")
		doc.update(newJson)
		doc.save()


		return doc.name
