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
	docname = doc.name
	return """Stock entry {sle} created for vehicle with serial no {sln}""".format(sle = docname, sln = serial_no).encode('ascii')

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
			new_status = abndstatus
	
	for r in records:
		
		record = frappe.get_doc("Stock Entry", r[0])
		if record:
			name = record.name
			frappe.db.sql("""update `tabSerial No` sn set vehicle_status = %(string1)s where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %(string2)s)""", {'string1': new_status, 'string2': name})
		
			record.submit()
			frappe.db.commit()
			returnmsg = """Submitted the stock entry {stockentryname} for vehicle {sln} successfully!""".format(stockentryname=record.name, sln=serial_no).encode('ascii')
		else:
			returnmsg = """Could not find the stock entry for vehicle {sln} in the draft state to submit!""".format(sln=serial_no).encode('ascii')
		
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
	docname = doc.name
	frappe.db.commit()
	return """Stock entry {ste} created for vehicle {sln}""".format(ste=docname,sln=serial_no).encode('ascii')

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
	docname = doc.name
	frappe.db.commit()
	return """Stock entry {sle} is created for vehicle with serial no {sln}""".format(sle=docname,sln=serial_no).encode('ascii')

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
	tableheadings = """<table border ="1">
			   <col width = "50">
			   <col width = "120">
			   <col width = "120">
			   <tr>
			   <th>S.No</th>
			   <th>Serial No</th>
			   <th>Item Code</th>
			   </tr>
			   </table> """.encode('ascii')
	submessage = submessage+tableheadings
	items = frappe.db.sql("""SELECT sn.serial_no, sn.item_code FROM `tabSerial No` sn WHERE sn.vehicle_status=%(string1)s""",{'string1':input1})
	i = 1
	
	for row in items:
	
		serial_no = row[0].encode('ascii')
		item_code = row[1].encode('ascii')
		
		emailmsg = """<table border ="1">
			      <col width="50">
				<col width = "120">
				<col width = "120">
				<tr>
				<td>{SlNo}</td>
				<td>{serialNo}</td>
				<td>{itemCode}</td>
				</tr>
				</table>""".format(SlNo=i,serialNo=serial_no,itemCode=item_code).encode('ascii')
		i = i+1
	
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
def make_new_serial_no_entry(serial_no,item_code):
	
	newJson = {
		"serial_no": serial_no,
		"doctype": "Serial No",
		"item_code": item_code,
		"vehicle_status": "Invoiced but not Received"		
	}

	
	doc = frappe.new_doc("Serial No")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def submit_deliver_vehicle_stock_entry(serial_no):
	
	new_status = "Delivered"
	records = frappe.db.sql("""select sd.parent from `tabStock Entry Detail` sd, `tabStock Entry` se where sd.serial_no = %s and se.docstatus = 0 and sd.parent = se.name""", (serial_no))
	
	record = frappe.get_doc("Stock Entry", records[0][0])
	if record:
		name = record.name
		frappe.db.sql("""update `tabSerial No` sn set vehicle_status = %(string1)s where sn.name = (select se.serial_no from `tabStock Entry Detail` se where se.parent = %(string2)s)""", {'string1': new_status, 'string2': name})
		
		record.submit()
		frappe.db.commit()
		returnmsg = """Submitted the stock entry {stockentryname} successfully!""".format(stockentryname=record.name).encode('ascii')
		return returnmsg

@frappe.whitelist()
def make_sales_invoice(serial_no):

	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice	
	serialNoDoc = frappe.get_doc("Serial No", serial_no)
	if serialNoDoc:
		brn = serialNoDoc.booking_reference_number
		itemCode = serialNoDoc.item_code
		if itemCode:
			item_record = frappe.get_doc("Item", itemCode)
		
		record = frappe.db.sql("""select so.name from `tabSales Order` so where so.booking_reference_number = %s and so.docstatus = 1""", (brn))
		if record:
			salesorder = frappe.get_doc("Sales Order", record[0][0])
			if salesorder:
				salesinvoice = make_sales_invoice(salesorder.name)
				#salesinvoice.posting_date = frappe.utils.datetime.nowdate()
				salesinvoice.update_stock = True
				for itemrecords in salesinvoice.items:
					if itemrecords.item_code == itemCode:
						itemrecords.serial_no = serial_no
						itemrecords.warehouse = serialNoDoc.warehouse
						itemrecords.allow_zero_valuation_rate = True
						salesinvoice.insert()
						salesinvoice.save()
						#salesinvoice.submit()     #submit in the submit_sales_invoice methd
						frappe.db.commit()
						return 'sales invoice '+salesinvoice.name+' created for sales order '+salesorder.name+' with booking reference number '+brn
				
			else:
				return 'Couldnt find the matching salesorder that is ready to be billed'
		else:
			return 'The sales order for this vehicle doesnt exist'
	else:
		msg = """The vehicle with the serial no {sln} does not exist on ERPNext""".format(sln = serial_no).encode('ascii')		
		return msg

@frappe.whitelist()
def change_status(serial_no, brn):

	current_item_code = ""	
	currentrecord = frappe.get_doc("Serial No", serial_no)
	if currentrecord:
		current_item_code = currentrecord.item_code	
		alreadyexistingrecord = frappe.db.sql("""select sn.name from `tabSerial No` sn where sn.booking_reference_number = %s and sn.vehicle_status = "Allocated but not Delivered" """,(brn))
		if alreadyexistingrecord:
			existingserialno = frappe.get_doc("Serial No", alreadyexistingrecord[0][0])
			item_code = existingserialno.item_code
			if existingserialno:
				existingserialno.booking_reference_number = ""
				existingserialno.vehicle_status = "Received but not Allocated"	#roll back the previous serial no with the brn
				existingserialno.save()
				
		currentrecord.booking_reference_number = brn
		currentrecord.vehicle_status = "Allocated but not Delivered"
		currentrecord.save()
		frappe.db.commit()
		msg = """Changed the status to Allocated but not Delivered for vehicle {vehicle} with booking reference number {bookrefno}""".format(vehicle=serial_no,bookrefno=brn).encode('ascii')
	else:
		msg = """"Could not find vehicle with serial no {vehicle} on ERPNext """.format(vehicle=serial_no).encode('ascii')
	return msg

@frappe.whitelist()
def allocate_vehicle(serial_no, brn):

	returnval = 0
	salesorder_record = frappe.db.sql("""select so.name from `tabSales Order` so where so.booking_reference_number = %(bookingrefno)s """,{'bookingrefno': brn})
	if not salesorder_record:
		returnval = -1
			
	if salesorder_record :
		serialno_record = frappe.get_doc("Serial No", serial_no)
		if serialno_record :
			item_code = serialno_record.item_code
			vehicle_status = serialno_record.vehicle_status
			record = frappe.db.sql("""select sd.parent from `tabSales Order Item` sd, `tabSales Order` se where sd.parent = se.name and sd.item_code = %(string1)s and se.booking_reference_number = %(string2)s""", {'string1': item_code, 'string2': brn })
			if record:
				if vehicle_status == "Received but not Allocated":				
					returnval = 1	#Sucess, all conditions are met
					#Check if there is another serial no allocated to this BRN
					alreadyexisitngserialno = frappe.db.sql("""select sn.name from `tabSerial No` sn where sn.booking_reference_number = %s""", brn)
					if alreadyexisitngserialno:
						return 2 #there already exists a serial no with this booking reference number
				else:
					if vehicle_status == "Allocated but not Delivered":
						returnval = -2	#Status is not RBNA, it is ABND, roll back previous allocation
					elif vehicle_status == "Invoiced but not Received":
						returnval = -5
					else:
						returnval = -6
			
			else:
				if vehicle_status == "Received but not Allocated":				
					returnval = -3	#Only item code not match
				else:
					returnval = -4	#Both item code and status doesnt match
				
	
	return returnval

@frappe.whitelist()
def submit_sales_invoice(serial_no):

	recordfoundandsubmitted = False	
	returnmsg = ""
	records = frappe.db.sql("""select sd.parent from `tabSales Invoice Item` sd, `tabSales Invoice` se where sd.serial_no = %s and se.docstatus = 0 and sd.parent = se.name""", (serial_no))
	
	for r in records:
		
		record = frappe.get_doc("Sales Invoice", r[0])
		if record:
		
			frappe.db.sql("""update `tabSerial No` sn set vehicle_status = 'Delivered' where sn.name = (select se.serial_no from `tabSales Invoice Item` se where se.parent = %s)""", (record.name))
		
			record.submit()
			recordfoundandsubmitted = True
			frappe.db.commit()
	if recordfoundandsubmitted:
		returnmsg = """Sales Invoice submitted for the vehicle with Serial No {sln}""".format(sln=serial_no).encode('ascii')
	else:
		returnmsg = """Sales Invoice for the vehicle with Serial No {sln} could not be found and submitted""".format(sln=serial_no).encode('ascii')
	return returnmsg
