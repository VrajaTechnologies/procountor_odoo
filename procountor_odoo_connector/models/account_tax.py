from odoo import models, fields

class AccountTax(models.Model):
    _inherit = 'account.tax'

    procountor_vat_percent_id = fields.Many2one(comodel_name="procountor.vat.percent",string="Procountor Vat Percent")
    procountor_vat_status_id = fields.Many2one(comodel_name="procountor.vat.status",string="Procountor Vat Status")
