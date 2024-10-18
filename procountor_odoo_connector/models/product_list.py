from odoo import fields, models
import logging

_logger = logging.getLogger("Procountor Product:")


class ProcountorProductListing(models.Model):
    _name = 'procountor.product.listing'
    _description = 'Procountor Product'
    _rec_name = 'procountor_product_name'

    procountor_product_id = fields.Char(
        string="Zoho Product ID",
        help="This is just a reference of Procountor Product identifier"
    )
    procountor_product_name = fields.Char(
        string="Name"
    )
    procountor_product_unit = fields.Char(
        string="Unit"
    )
    procountor_product_status = fields.Char(
        string="Status"
    )
    procountor_product_rate = fields.Char(
        string="Rate"
    )
    procountor_product_sku = fields.Char(
        string="SKU"
    )
    procountor_hs_code = fields.Char(
        string="HS Code"
    )
    procountor_product_description = fields.Char(
        string="description"
    )
    instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Instance',
        help='Select Instance Id'
    )
    is_product_list = fields.Boolean(
        string="Is Product List"
    )
    product_template_id = fields.Many2one(
        comodel_name='product.template'
    )

    def procountor_import_product_list(self, instance, from_date=False, to_date=False, procountor_product_ids=False):
        """
        This method is used to import Products from procountor to odoo.
        """
        pass
