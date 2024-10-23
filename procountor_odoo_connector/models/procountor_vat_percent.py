import logging
from odoo import models, fields, _, api


_logger = logging.getLogger("Procountor")


class ProcountorVatPercent(models.Model):
    _name = 'procountor.vat.percent'
    _description = 'Procountor Vat Percent'
    _rec_name = "procountor_vat_percent"

    procountor_vat_percent = fields.Float(string="Procountor Vat Percent", copy=False,
                                          help="Procountor Vat Configured Percent")

