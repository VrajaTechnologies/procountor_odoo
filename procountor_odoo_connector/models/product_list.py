from odoo import fields, models
import logging
import re

_logger = logging.getLogger("Procountor Product:")


class ProcountorProductListing(models.Model):
    _name = 'procountor.product.listing'
    _description = 'Procountor Product'
    _rec_name = 'procountor_product_name'

    procountor_product_id = fields.Char(
        string="Procountor Product ID",
        help="This is just a reference of Procountor Product identifier"
    )
    procountor_product_type = fields.Selection(
        selection=[('PURCHASE', 'PURCHASE'), ('SALES', 'SALES'), ('TRAVEL', 'TRAVEL')],
        string="Product Type"
    )
    procountor_product_name = fields.Char(
        string="Name"
    )
    procountor_product_code = fields.Char(
        string="Code"
    )
    procountor_product_unit = fields.Char(
        string="Unit"
    )
    procountor_product_discount = fields.Float(
        string="Discount"
    )
    procountor_product_price = fields.Float(
        string="Price"
    )
    procountor_product_vat = fields.Float(
        string="Vat"
    )
    procountor_product_active = fields.Boolean(
        string="Active",
        default=False
    )
    procountor_product_vat_status = fields.Many2one(
        comodel_name='procountor.vat.status',
        string="Vat Status"
    )
    procountor_product_currency = fields.Char(
        string="Currency",
        default=False
    )
    instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Instance',
        help='Select Instance Id'
    )
    product_template_id = fields.Many2one(
        comodel_name='product.template'
    )
    is_product_synced = fields.Boolean(
        string='Is Product Synced?',
        default=False
    )

    def procountor_import_product_list(self, procountor_instance, procountor_product_ids=False):
        """
        This method is used to import Products from procountor to odoo.
        """
        last_synced_date = fields.Datetime.now()
        log_id = self.env['procountor.log'].generate_procountor_logs('product', 'import', procountor_instance,
                                                                     'Process Started')
        msg = ''
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {0}'.format(procountor_instance.procountor_api_access_token),
            'Content-Type': 'application/json'
        }

        is_error = False
        if procountor_product_ids:
            """
            If product IDS given by user.
            """
            product_ids_list = list(set(re.findall(re.compile(r"(\d+)"), procountor_product_ids)))
            for product_id in product_ids_list:
                api_url = "{0}/products/{1}".format(procountor_instance.procountor_api_url, product_id)
                try:
                    response_status, response_data = procountor_instance.procountor_api_calling('GET', api_url,
                                                                                                '', headers)
                    if response_status and response_data.get('id'):
                        self.create_product_from_procountor_to_odoo(response_data, procountor_instance, log_id)
                    else:
                        is_error = True
                        error_msg = 'Getting some error when try to import product {}'.format(product_id)
                        self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                         procountor_instance, error_msg,
                                                                                         False, response_data, log_id,
                                                                                         True)
                except Exception as error:
                    is_error = True
                    error_msg = 'Getting some error when try to import product from odoo to procountor.'
                    self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                     procountor_instance, error_msg,
                                                                                     False, error, log_id, True)
        else:
            """
            All products fetch.
            """
            api_url = "{0}/products".format(procountor_instance.procountor_api_url)
            try:
                response_status, response_data = procountor_instance.procountor_api_calling('GET', api_url, '', headers)
                if response_status and response_data.get('results'):
                    self.create_product_from_procountor_to_odoo(response_data.get('results'), procountor_instance,
                                                                log_id)
                else:
                    is_error = True
                    error_msg = 'Getting some error when try to import products'
                    self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                     procountor_instance, error_msg,
                                                                                     False, response_data, log_id,
                                                                                     True)
            except Exception as error:
                is_error = True
                error_msg = 'Getting some error when try to import product from odoo to procountor.'
                self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                 procountor_instance, error_msg,
                                                                                 False, error, log_id, True)

        if is_error:
            log_id.procountor_operation_message = 'Process Has Been Finished'
            msg = 'Getting some issue while import product!'
            return False, log_id.name, msg
        log_id.procountor_operation_message = 'Process Has Been Finished'
        procountor_instance.last_product_synced_date = last_synced_date
        if not log_id.procountor_operation_line_ids:
            log_id.unlink()
        return True, log_id.name, msg

    def create_product_from_procountor_to_odoo(self, response_data, instance, log_id):
        if not isinstance(response_data, list):
            response_data = [response_data]
        for item in response_data:
            try:
                is_product_list_exist = self.search([('procountor_product_id', '=', item.get("id"))])
                product_template = self.env['product.template'].search([('default_code', '=', item.get("code"))])
                if not product_template:
                    product_temp_data = {
                        'name': item.get("name"),
                        'list_price': item.get("price"),
                        'default_code': item.get('code'),
                        'detailed_type': 'product'
                    }
                    product_template = self.env['product.template'].create(product_temp_data)
                if not is_product_list_exist:
                    procountor_vat_status = self.env['procountor.vat.status'].search(
                        [('procountor_vat_status', '=', item.get('vatStatus'))], limit=1)
                    product_listing_vals = {
                        "procountor_product_id": item.get("id"),
                        "procountor_product_type": item.get("type"),
                        "procountor_product_name": item.get("name"),
                        "procountor_product_code": item.get("code"),
                        "procountor_product_unit": item.get("unit"),
                        "procountor_product_price": item.get("price"),
                        "procountor_product_discount": item.get("discount"),
                        "procountor_product_vat": item.get("vat"),
                        "procountor_product_active": item.get("active"),
                        "procountor_product_vat_status": procountor_vat_status and procountor_vat_status.id,
                        "procountor_product_currency": item.get("currency"),
                        "instance_id": instance.id,
                        "product_template_id": product_template and product_template.id,
                        "is_product_synced": True,
                    }
                    created_product = self.create(product_listing_vals)
                    if created_product:
                        message = 'Product successfully created in Odoo from Procountor : {}'.format(
                            item.get('name'))
                        self.env['procountor.log.line'].generate_procountor_process_line('product', 'import',
                                                                                         instance, message, False,
                                                                                         item, log_id, False)
                else:
                    is_product_list_exist.product_template_id = product_template.id
                    message = 'Product [{0}] Already Exist In Odoo.'.format(item.get('name'))
                    self.env['procountor.log.line'].generate_procountor_process_line('product', 'import', instance,
                                                                                     message, False, item,
                                                                                     log_id, False)
            except Exception as error:
                error_msg = 'Getting some error when try to import product from odoo to procountor.'
                self.env['procountor.log.line'].generate_procountor_process_line('product', 'import', instance,
                                                                                 error_msg, False, error, log_id, True)
