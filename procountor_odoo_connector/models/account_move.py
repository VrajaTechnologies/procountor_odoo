import json
from odoo import fields, models
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    procountor_instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Procountor Instance'
    )

    def prepare_invoice_line_data(self,invoice_id):
        invoice_lines = []
        for invoice_line_id in invoice_id.line_ids:
            invoice_lines.append({
                "productId": invoice_line_id.product_id.code or '',
                "product": invoice_line_id.product_id.name or '',
                "productCode": invoice_line_id.product_id.default_code or '',
                "quantity": invoice_line_id.quantity,
                "unit": "CM",
                "unitPrice": 0,
                "discountPercent": 0,
                "vatPercent": 0,
                "vatStatus": 1,
                "comment": "string",
                "startDate": "2024-10-21",
                "endDate": "2024-10-21",
                "headerText": "string",
                "explanationText": "string"
            })
        return invoice_lines

    def prepare_customer_address_info(self, customer_id):
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

    def prepare_customer_api_request_data(self, invoice_id):
        """This method used for prepare api request data of export or update customer
            author - mithilesh lathiya """
        customer_id = invoice_id.partner_id
        customer_delivery_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'delivery')
        customer_invoice_address = customer_id.child_ids and customer_id.child_ids.filtered(
            lambda x: x.type == 'invoice')
        payload = {
            "partnerId": customer_id.procountor_customer_id,
            "type": "SALES_INVOICE",
            "status": "UNFINISHED",
            "date": invoice_id.invoice_data.strftime("%Y-%m-%d"),
            "counterParty": {
                "contactPersonName": customer_id.name or '',
                "identifier": "SALES_INVOICE",
                "customerNumber": customer_id.procountor_customer_id,
                "email": customer_id.email or '',
                "counterPartyAddress": self.prepare_customer_address_info(invoice_id.customer_id),
                # "bankAccount": {
                #     "accountNumber": invoice_id.customer_id.,
                #     "bic": "string"
                # },
                # "einvoiceAddress": {
                #     "operator": "string",
                #     "address": "string",
                #     "ediId": "string"
                # }
            },
            "billingAddress": self.prepare_customer_address_info(
                customer_invoice_address[0] if customer_invoice_address else customer_id),
            "deliveryAddress": self.prepare_customer_address_info(
                customer_delivery_address[0] if customer_delivery_address else customer_id),
            "paymentInfo": {
                "paymentMethod": customer_id.procountor_payment_method or '',
                "currency": customer_id.currency_id.name if customer_id.currency_id else customer_id.property_product_pricelist.currency_id.name,
                # "bankAccount": {
                #     "accountNumber": "FI7099899900012946",
                #     "bic": ""
                # },
                "dueDate": datetime.now().strftime("%Y-%m-%d"),
                "currencyRate": 1,
                "paymentTermPercentage": 0,
                "bankReferenceCode": "",
                "bankReferenceCodeType": "",  # "FI",
                "clearingCode": ""
            },
            "extraInfo": {
                "accountingByRow": "true",
                "unitPricesIncludeVat": "true"
            },
            "discountPercent": 0,  # Invoice discount percentage. Scale: 4.
            "orderReference": invoice_id.name or '',
            "invoiceRows": self.prepare_invoice_line_data(invoice_id),
            "vatStatus": 1,
            "originalInvoiceNumber": "string",
            "deliveryStartDate": "2024-10-21",
            "deliveryEndDate": "2024-10-21",
            "deliveryMethod": "MAILING",
            "deliveryInstructions": "string",
            "invoiceChannel": "EMAIL",
            "penaltyPercent": 0,
            "language": "DANISH",
            "invoiceTemplateId": 0,
            "additionalInformation": "string",
            "vatCountry": "FINLAND",
            "notes": "string",
            "factoringText": "string",
            "travelInformationItems": [
                {
                    "departure": "string",
                    "arrival": "string",
                    "places": "string",
                    "purpose": "string"
                }
            ],
            "invoiceApprovalInformation": {
                "acceptors": [
                    {
                        "userId": 0
                    }
                ],
                "verifiers": [
                    {
                        "userId": 0
                    }
                ]
            },
            "orderNumber": "string",
            "agreementNumber": "string",
            "accountingCode": "string",
            "deliverySite": "string",
            "tenderReference": "string",
            "version": "2024-10-21T12:06:18.251Z"
        }
        request_data = json.dumps(payload)
        return request_data

    def export_invoice_data_odoo_to_procountor(self, procountor_instance=False, active_invoice_ids=False, log_id=False):
        log_id = log_id if log_id else self.env['procountor.log'].generate_procountor_logs('invoice', 'export',
                                                                                           procountor_instance,
                                                                                           'Process Started')
        for invoice_id in active_invoice_ids:
            customer_api_request_data = self.prepare_customer_api_request_data(invoice_id)
            headers = {
                'accept': 'application/json',
                'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token),
                'Content-Type': 'application/json'
            }
            api_url = "{0}/businesspartners{1}".format(
                self.procountor_instance_id.procountor_api_url,
                "/{0}".format(invoice_id.procountor_customer_id) if invoice_id.procountor_customer_id else ""
            )
            request_type = 'PUT' if invoice_id.procountor_customer_id else 'POST'
            try:
                response_status, response_data = procountor_instance.procountor_api_calling(request_type, api_url,
                                                                                            customer_api_request_data,
                                                                                            headers)

                if response_status and response_data.get('id'):
                    invoice_id.procountor_customer_id = response_data.get('id')
                    invoice_id.procountor_instance_id = procountor_instance
                    message = 'Successfully Export Customer To Procountor : {}'.format(
                        invoice_id.name)
                    self.env['procountor.log.line'].generate_procountor_process_line('customer', 'export',
                                                                                     procountor_instance,
                                                                                     message,
                                                                                     customer_api_request_data,
                                                                                     response_data, log_id,
                                                                                     False)
                else:
                    is_error = True
                    error_msg = 'Getting some error when try to export customer {} from odoo to procountor.'.format(
                        invoice_id.name)
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
        pass
