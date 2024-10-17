import logging
import json
from datetime import datetime
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("Procountor")


class ExportCustomerToProcountor(models.TransientModel):
    """
    Model for adding customer into procountor.
    """
    _name = "export.customer.to.procountor"
    _description = "Export Customer To Procountor"

    procountor_instance_id = fields.Many2one("procountor.instance", string="Procountor Instance")

    def prepare_customer_info(self, customer_id):
        """This method use for prepare customer address info
            author - mithilesh lathiya"""
        return {
            "name": customer_id.name or '',
            "specifier": "",
            "street": "{} {}".format(customer_id.street,
                                     customer_id.street2) if customer_id.street2 else customer_id.street,
            "zip": customer_id.zip or '',
            "city": customer_id.city or '',
            "country": (customer_id.country_id and customer_id.country_id.name).replace(' ', '_').upper() or '',
            "subdivision": ""
        }

    def prepare_customer_api_request_data(self, customer_id):
        """This method used for prepare api request data of export or update customer
            author - mithilesh lathiya """

        customer_delivery_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'delivery')
        customer_invoice_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'invoice')
        customer_child_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'contact')
        payload = {
            "name": customer_id.name or '',
            "type": customer_id.procountor_customer_type or '',
            "address": self.prepare_customer_info(customer_id),
            "billingAddress": self.prepare_customer_info(
                customer_invoice_address[0] if customer_invoice_address else customer_id),
            "deliveryAddress": self.prepare_customer_info(
                customer_delivery_address[0] if customer_delivery_address else customer_id),
            "invoicingInfo": {
                "email": customer_id.email or '',
            },
            "paymentInfo": {
                "paymentMethod": customer_id.procountor_payment_method,
                "bankAccount": customer_id.bank_ids and customer_id.bank_ids.mapped('acc_number')[0] or '',
                "currency": customer_id.currency_id.name if customer_id.currency_id else customer_id.property_product_pricelist.currency_id.name
            },
            "registryInfo": {
                "phone": customer_id.phone or '',
                "mobilePhone": customer_id.mobile or ''
            }
        }
        if customer_child_address:
            child_address_info = []
            for child_address in customer_child_address:
                child_address_info.append({
                    "name": child_address.name or '',
                    "email": child_address.email or '',
                    "phone": child_address.phone or ''
                })
            payload.update({"contactPersons": child_address_info})
        # if we try to update customer at that time below parameter was not support in request so thats the reason we update payload if customer has not customer id
        if not customer_id.procountor_customer_id:
            payload.update({"version": datetime.now().isoformat()})
        request_data = json.dumps(payload)
        return request_data

    def export_or_update_customer_to_procountor(self):
        """This method use for export or update customer from odoo to procountor
            author - mithilesh lathiya
            """
        procountor_instance = self.procountor_instance_id
        active_customer_ids = self.env["res.partner"].browse(self._context.get("active_ids", [])).filtered(
            lambda x: x.company_type == 'company')
        log_id = self.env['procountor.log'].generate_procountor_logs('customer', 'export', procountor_instance,
                                                                     'Process Started')
        is_error = False
        if active_customer_ids:
            for customer_id in active_customer_ids:
                customer_api_request_data = self.prepare_customer_api_request_data(customer_id)
                headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token),
                    'Content-Type': 'application/json'
                }
                api_url = "{0}/businesspartners{1}".format(
                    self.procountor_instance_id.procountor_api_url,
                    "/{0}".format(customer_id.procountor_customer_id) if customer_id.procountor_customer_id else ""
                )
                request_type = 'PUT' if customer_id.procountor_customer_id else 'POST'
                try:
                    response_status, response_data = procountor_instance.procountor_api_calling(request_type, api_url,
                                                                                                customer_api_request_data,
                                                                                                headers)

                    if response_status and response_data.get('id'):
                        customer_id.procountor_customer_id = response_data.get('id')
                        customer_id.procountor_instance_id = procountor_instance
                        message = 'Successfully Export Customer To Procountor : {}'.format(
                            customer_id.name)
                        self.env['procountor.log.line'].generate_procountor_process_line('customer', 'export',
                                                                                         procountor_instance,
                                                                                         message,
                                                                                         False, message, log_id,
                                                                                         False)
                    else:
                        is_error = True
                        error_msg = 'Getting some error when try to export customer {} from odoo to procountor.'.format(
                            customer_id.name)
                        self.env['procountor.log.line'].generate_procountor_process_line('customer', 'export',
                                                                                         procountor_instance,
                                                                                         error_msg,
                                                                                         customer_api_request_data,
                                                                                         response_data, log_id,
                                                                                         True)
                except Exception as error:
                    is_error = True
                    error_msg = 'Getting some error when try to export customer from odoo to procountor.'
                    self.env['procountor.log.line'].generate_procountor_process_line('customer', 'export',
                                                                                     procountor_instance,
                                                                                     error_msg,
                                                                                     customer_api_request_data, error,
                                                                                     log_id,
                                                                                     True)

        else:
            is_error = True
            message = "We did not find any customers with the customer type set as 'company'."
            self.env['procountor.log.line'].generate_procountor_process_line('customer', 'export',
                                                                             procountor_instance,
                                                                             message, False, message, log_id, True)
        if is_error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Getting some issue while export customer!',
                    'message': 'Please Check Following Log : {0}'.format(log_id.name),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        log_id.procountor_operation_message = 'Process Has Been Finished'
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
