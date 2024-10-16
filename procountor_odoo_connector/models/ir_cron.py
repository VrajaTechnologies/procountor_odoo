from odoo import models, fields


class IrCron(models.Model):
    _inherit = 'ir.cron'

    procountor_instance = fields.Many2one(
        comodel_name='procountor.instance',
        string='Procountor Instance',
        copy=False
    )
