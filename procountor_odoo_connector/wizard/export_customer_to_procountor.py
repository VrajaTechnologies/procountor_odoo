import logging
import json
from odoo import models, fields
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("Procountor")


class ExportCustomerToProcountor(models.TransientModel):
    """
    Model for adding customer into procountor.
    """
    _name = "export.customer.to.procountor"
    _description = "Export Customer To Procountor"

    procountor_instance_id = fields.Many2one("procountor.instance", string="Procountor Instance")

    def prepare_customer_info(self,customer_id):
        return {
            "name": customer_id.name or '',
            "specifier": "",
            "street": "{} {}".format(customer_id.street,
                                     customer_id.street2) if customer_id.street2 else customer_id.street,
            "zip": customer_id.zip or '',
            "city": customer_id.city or '',
            "country": customer_id.country_id and customer_id.country_id.name or '',
            "subdivision": ""
        },


    def export_customer_to_procountor(self):
        active_customer_ids = self.env["res.partner"].browse(self._context.get("active_ids", []))
        if active_customer_ids:
            try:
                for customer_id in active_customer_ids:
                    if customer_id.procountor_customer_id:
                        continue

                    customer_delivery_address = customer_id.child_ids and customer_id.child_ids.filtered(lambda x: x.type == 'delivery')
                    customer_invoice_address = customer_id.child_ids and customer_id.child_ids.filtered(lambda x: x.type == 'invoice')

                    url = "{0}/businesspartners".format(self.procountor_instance_id.procountor_api_url)

                    payload = json.dumps({
                        "name": customer_id.name or '',
                        "type": "CUSTOMER",
                        "address": self.prepare_customer_info(customer_id),
                        "billingAddress":self.prepare_customer_info(customer_invoice_address[0] if customer_invoice_address else customer_id),
                        "deliveryAddress": self.prepare_customer_info(customer_delivery_address[0] if customer_delivery_address else customer_id),
                        "paymentInfo": {
                            "paymentMethod": customer_id.procountor_payment_method,
                            "bankAccount": ""
                        },
                        "registryInfo": {
                            "phone": customer_id.phone or '',
                            "mobilePhone": customer_id.mobile or ''
                        },
                        "version": "2024-10-15T05:41:03.547Z"
                    })
                    headers = {
                        'accept': 'application/json',
                        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIyODM3NyIsImF1ZCI6Ik9kb29WcmFqYVRlc3RDbGllbnQiLCJhdXRoX3RpbWUiOjE3Mjg5NzA2NDMsInNjb3BlIjoibTJtIiwiaXNzIjoiaHR0cHM6Ly9wdHMtcHJvY291bnRvci5wdWJkZXYuYXp1cmUucHJvY291bnRvci5jb20iLCJleHAiOjE3MjkwNjI2NDksImlhdCI6MTcyOTA1OTA0OSwianRpIjoiOTg2Zjg4ZGYtMjJiYS00OTAyLWE3YmEtN2EyNzBlNGY3MTk4IiwiY2lkIjoxNTYwNX0.G6SCsm4-rGrkHG0zmdleYbZZ1SamRNagvthQM5bxZqA',
                        'Content-Type': 'application/json'
                    }

            except Exception as e:
                raise ValidationError(e)



