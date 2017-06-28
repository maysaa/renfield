# Epoch Integrated solution for Royal Enfield Tracking system

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime

@frappe.whitelist()
def validate_serial_no(serial_no):

		
	doc_status = 0
	if not frappe.db.exists("Serial No", serial_no):
		doc_status = 0
	else:
	
		record = frappe.get_doc("Serial No", serial_no)
		if record:
			item = record.item_code
			veh_status = record.vehicle_status
			company = record.company
	
	
			if veh_status == "Invoiced but not Received":
				doc_status = 1
			else:
				doc_status = 2
	
	msgprint(_(doc_status))
	return doc_status

@frappe.whitelist()
def make_stock_entry(serial_no):
	
	innerJson = ""
	
	if frappe.db.exists("Serial No", serial_no):
		
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

				"t_warehouse": "Finished Goods - PISPL"
				  }
	
			newJson["items"].append(innerJson)

	
			doc = frappe.new_doc("Stock Entry")
			doc.update(newJson)
			doc.save()


		return doc.name

@frappe.whitelist()
def submit_stock_entry(item):

	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.item_code = %s and se.docstatus = 0 and sd.parent = se.name""", (item))
	
	for r in records:
		
		record = frappe.get_doc("Stock Entry", r[0])
		frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Received but not Allocated' where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %s)""", (record.name))
		
		record.submit()


@frappe.whitelist()
def cancel_stock_entry(serial_no):

	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %s""", (serial_no))
	record = frappe.get_doc("Stock Entry", records[0][0])
	
	frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Invoiced but not Received' where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %s)""", (record.name))
		
	record.cancel()


