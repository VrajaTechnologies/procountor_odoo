from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    procountor_instance_id = fields.Many2one(
        comodel_name='procountor.instance',
        string='Procountor Instance'
    )