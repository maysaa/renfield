# Epoch Integrated solution for Royal Enfield Tracking system

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime

@frappe.whitelist()
def validate_serial_no(serial_no):

		
	doc_status = 0
	if not frappe.db.exists("Serial No", serial_no):
		doc_status = -1
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
	return doc_status


@frappe.whitelist()
def simply_return_message():
	return 'hello'


@frappe.whitelist()
def make_stock_entry(serial_no,destination_warehouse):

	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %s""", (serial_no))
	if records:
		return 'The stock entry for this serial no already exists'
	
	innerJson = ""
	
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		
		veh_status = record.vehicle_status
		company = record.company

	if item:
		item_record = frappe.get_doc("Item", item)

	
	#if veh_status == "Invoiced but not Received":

	newJson = {
		"company": company,
		"doctype": "Stock Entry",
		"title": "Material Receipt",
		"purpose": "Material Receipt",
		"items": [
		]
	}
		
	req_qty = 1
	allowzero_valuation = True
	innerJson =	{
				"doctype": "Stock Entry Detail",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,
				"allow_zero_valuation_rate": allowzero_valuation,
				"t_warehouse": destination_warehouse
			  }
		
	newJson["items"].append(innerJson)
	
	doc = frappe.new_doc("Stock Entry")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def submit_stock_entry(serial_no):
	
	new_status = "Received but not Allocated"
	ibnrstatus = "Invoiced but not Received"
	abndstatus = "Allocated but not Delivered"
	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.serial_no = %s and se.docstatus = 0 and sd.parent = se.name""", (serial_no))
	serialno_table = frappe.get_doc("Serial No", serial_no)
	if serialno_table:
		status = serialno_table.vehicle_status
		if serialno_table.vehicle_status == abndstatus:
			new_status = "Delivered"
	
	record = frappe.get_doc("Stock Entry", records[0][0])
	if record:
		name = record.name
		frappe.db.sql("""update `tabSerial No` sn set vehicle_status = %(string1)s where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %(string2)s)""", {'string1': new_status, 'string2': name})
		
		record.submit()
		frappe.db.commit()
		returnmsg = """Submitted the stock entry {stockentryname} successfully!""".format(stockentryname=record.name).encode('ascii')
		return returnmsg

@frappe.whitelist()
def cancel_stock_entry(serial_no):

	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %s""", (serial_no))
	record = frappe.get_doc("Stock Entry", records[0][0])
	
	frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Invoiced but not Received' where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %s)""", (record.name))
		
	record.cancel()


@frappe.whitelist()
def make_movement_stock_entry(serial_no,source_warehouse):

		
	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %(string1)s and se.purpose = 'Material Transfer' and sd.t_warehouse = %(string2)s """, {'string1': serial_no, 'string2': source_warehouse})
	if records:
		return 'The stock entry for this serial no already exists'
	
	innerJson = ""
	
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		at_warehouse = record.warehouse
		veh_status = record.vehicle_status
		company = record.company

	if at_warehouse != source_warehouse:
		message = """The vehicle with serial no {vehicle} is not present in the warehouse {swh} for it to be moved on to the Truck. Cannot make a stock entry""".format(vehicle=serial_no,swh=source_warehouse).encode('ascii')
		return message

	if item:
		item_record = frappe.get_doc("Item", item)

	
	newJson = {
		"company": company,
		"doctype": "Stock Entry",
		"title": "Material Transfer",
		"purpose": "Material Transfer",
		"items": [
		]
	}
		
	req_qty = 1
	allowzero_valuation = True
	innerJson =	{
				"doctype": "Stock Entry Detail",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,
				"s_warehouse":source_warehouse,
				"t_warehouse": "Truck - RE",
				"allow_zero_valuation_rate": allowzero_valuation
			  }
		
	newJson["items"].append(innerJson)
	
	doc = frappe.new_doc("Stock Entry")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def make_unloadvehicle_stock_entry(serial_no,destination_warehouse):

	expected_sourcewh = "Truck - RE"	
	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %(string1)s and se.purpose = 'Material Transfer' and sd.t_warehouse = %(string2)s """, {'string1': serial_no, 'string2': destination_warehouse})
	if records:
		
		return 'The stock entry for this serial no already exists'
	
	innerJson = ""
	
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		at_warehouse = record.warehouse
		veh_status = record.vehicle_status
		company = record.company

	if at_warehouse == destination_warehouse:
		message = """The vehicle with serial no {vehicle} is already at the warehouse {swh}, cannot make a stock entry""".format(vehicle=serial_no,swh=destination_warehouse).encode('ascii')
		return message
	if at_warehouse != expected_sourcewh:
		errormsg = """The vehicle with serial no {vehicle} is not present at the warehouse {swh} for it to be moved to {dwh}. Cannot make a stock entry""".format(vehicle=serial_no,swh=expected_sourcewh,dwh=destination_warehouse).encode('ascii')
		return errormsg
	if item:
		item_record = frappe.get_doc("Item", item)

	
	#if veh_status == "Invoiced but not Received":

	newJson = {
		"company": company,
		"doctype": "Stock Entry",
		"title": "Material Transfer",
		"purpose": "Material Transfer",
		"items": [
		]
	}
		
	req_qty = 1
	allowzero_valuation = True
	innerJson =	{
				"doctype": "Stock Entry Detail",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,
				"s_warehouse": expected_sourcewh,
				"t_warehouse": destination_warehouse,
				"allow_zero_valuation_rate": allowzero_valuation
			  }
		
	newJson["items"].append(innerJson)
	
	doc = frappe.new_doc("Stock Entry")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

#to make delivery note and submit it


@frappe.whitelist()
def make_delivery_note(serial_no,customer_name=None):
	
	if(customer_name == None):
		customer_name = "Customer_1"

	records = frappe.db.sql("""select sd.parent from `tabDelivery Note Item` sd, `tabDelivery Note` se where sd.parent = se.name and sd.serial_no = %s""", (serial_no))
	if records:
		return 'The delivery note for this serial no already exists'
	
	innerJson = ""
	
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		
		veh_status = record.vehicle_status
		company = record.company
		warehouse_at = record.delivery_required_at

	if item:
		item_record = frappe.get_doc("Item", item)

	
	#if veh_status == "Invoiced but not Received":
	exchange_rate = 1.000

	newJson = {
		"company": company,
		"doctype": "Delivery Note",
		"title": customer_name,
		"customer": customer_name,
		"items": [
		]
	}
		
	req_qty = 1
	allowzero_valuation = True
	innerJson =	{
				"doctype": "Delivery Note Item",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,
				"allow_zero_valuation_rate": allowzero_valuation,
				"warehouse": warehouse_at				
			  }
		
	newJson["items"].append(innerJson)
	
	doc = frappe.new_doc("Delivery Note")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def submit_delivery_note(serial_no):

	records = frappe.db.sql("""select sd.parent from `tabDelivery Note Item` sd, `tabDelivery Note` se where sd.serial_no = %s and se.docstatus = 0 and sd.parent = se.name""", (serial_no))
	
	for r in records:
		
		record = frappe.get_doc("Delivery Note", r[0])
		
		frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Delivered' where sn.name = (select se.serial_no from `tabDelivery Note Item` se where se.parent = %s)""", (record.name))
		
		record.submit()
	frappe.db.commit()

@frappe.whitelist()
def cancel_delivery_note(serial_no):

	records = frappe.db.sql("""select sd.parent from `tabDelivery note Item` sd, `tabDelivery Note` se where sd.parent = se.name and sd.serial_no = %s""", (serial_no))
	record = frappe.get_doc("Delivery Note", records[0][0])
	
	frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Allocated but not Delivered' where sn.name = (select se.serial_no from `tabDelivery Note Item` se where se.parent = %s)""", (record.name))
		
	record.cancel()
	frappe.db.commit()

@frappe.whitelist()
def send_IBNR_mail(emailadd=[]):

	sender = frappe.session.user
	subject = "Invoiced but not received list"
	submessage = ""
	input1 = "Invoiced but not Received"
	tableheadings = """<table border ="0">
			   <tr>
			   <th>Serial No</th>
			   <th>Item Code</th>
			   </tr>
			   </table> """.encode('ascii')
	submessage = submessage+tableheadings
	items = frappe.db.sql("""SELECT sn.serial_no, sn.item_code FROM `tabSerial No` sn WHERE sn.vehicle_status=%(string1)s""",{'string1':input1})
	
	for row in items:
	
		serial_no = row[0].encode('ascii')
		item_code = row[1].encode('ascii')
		
		emailmsg = """<table border ="0">
				<tr>
				<td>{serialNo}</td>
				<td>{itemCode}</td>
				</tr>
				</table>""".format(serialNo=serial_no,itemCode=item_code).encode('ascii')
	
		submessage = submessage+emailmsg
	message = """<p>
			{dear_system_manager} <br><br>
			{invoiced_message}<br><br>
			</p>""".format(
			dear_system_manager=_("Dear User,"),
			invoiced_message=_("Invoiced but not Received list is as follows <p>  {invoicedlist}</p>").format(invoicedlist=submessage)	
			)	
	frappe.sendmail(recipients=emailadd, sender=sender, subject=subject,message=message, delayed=False)
	return emailadd

@frappe.whitelist()
def change_status(serial_no):

	record = frappe.get_doc("Serial No", serial_no)
	if record:	
		veh_status = record.vehicle_status
	if veh_status == "Received but not Allocated":
		record.vehicle_status = "Allocated but not Delivered"
		record.save()
		frappe.db.commit()
		msg = """Changed the status to Allocated but not Delivered for vehicle {vehicle}""".format(vehicle=serial_no).encode('ascii')
		return msg
	else:
		return 'The vehicle status is not Received but not Allocated, exiting without making any status change'

@frappe.whitelist()
def make_delivervehicle_stock_entry(serial_no,source_warehouse):

	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.parent = se.name and sd.serial_no = %(string1)s and se.purpose = 'Material Issue' and sd.s_warehouse = %(string2)s """, {'string1': serial_no, 'string2': source_warehouse})
	if records:
		return 'The stock entry for this serial no already exists'
	
	innerJson = ""
	
	record = frappe.get_doc("Serial No", serial_no)
	if record:
		item = record.item_code
		at_warehouse = record.warehouse
		veh_status = record.vehicle_status
		company = record.company

	if at_warehouse != source_warehouse:
		message = """The vehicle with serial no {vehicle} is not present in the warehouse {swh} for it to be delivered. Cannot make a stock entry""".format(vehicle=serial_no,swh=source_warehouse).encode('ascii')
		return message

	if item:
		item_record = frappe.get_doc("Item", item)

	
	newJson = {
		"company": company,
		"doctype": "Stock Entry",
		"title": "Material Issue",
		"purpose": "Material Issue",
		"items": [
		]
	}
		
	req_qty = 1
	allowzero_valuation = True
	innerJson =	{
				"doctype": "Stock Entry Detail",
				"item_code": item,
				"description": item_record.description,
				"uom": item_record.stock_uom,
				"qty": req_qty,
				"serial_no": serial_no,
				"s_warehouse":source_warehouse,
				"allow_zero_valuation_rate": allowzero_valuation
			  }
		
	newJson["items"].append(innerJson)
	
	doc = frappe.new_doc("Stock Entry")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def make_new_serial_no_entry(serial_no,item_code,delivery_req_at,delivery_req_on):
	
	newJson = {
		"serial_no": serial_no,
		"doctype": "Serial No",
		"item_code": item_code,
		"vehicle_status": "Invoiced but not Received",
		"delivery_required_at": delivery_req_at,
		"delivery_required_on": delivery_req_on,
	}

	
	doc = frappe.new_doc("Serial No")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

