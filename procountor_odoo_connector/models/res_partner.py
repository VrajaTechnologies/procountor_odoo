from odoo import models, fields


class SalesOrder(models.Model):
    _inherit = 'res.partner'

    procountor_customer_id = fields.Char(string="Procountor Customer ID",
                                         help="This is just a reference of procountor customer identifier",
                                         tracking=True,copy=False)
    procountor_instance_id = fields.Many2one('procountor.instance', string="Procountor Instance",copy=False,
                                             help="This field show the instance details of shopify", tracking=True)
    procountor_payment_method = fields.Selection([('BANK_TRANSFER', 'BANK_TRANSFER'),
                                                  ('DIRECT_DEBIT', 'DIRECT_DEBIT'),
                                                  ('DIRECT_PAYMENT', 'DIRECT_PAYMENT'),
                                                  ('CLEARING', 'CLEARING'),
                                                  ('CREDIT_CARD_CHARGE', 'CREDIT_CARD_CHARGE'),
                                                  ('FOREIGN_PAYMENT', 'FOREIGN_PAYMENT'),
                                                  ('OTHER', 'OTHER'),
                                                  ('CASH', 'CASH'),
                                                  ('DOMESTIC_PAYMENT_PLUSGIRO', 'DOMESTIC_PAYMENT_PLUSGIRO'),
                                                  ('DOMESTIC_PAYMENT_BANKGIRO', 'DOMESTIC_PAYMENT_BANKGIRO'),
                                                  ('DOMESTIC_PAYMENT_CREDITOR', 'DOMESTIC_PAYMENT_CREDITOR'),
                                                  ('NETS', 'NETS')], string="Procountor Payment Method", copy=False,
                                                 tracking=True,
                                                 default="BANK_TRANSFER", help="Payment method of the partner")
    procountor_customer_type = fields.Selection([('CUSTOMER','CUSTOMER'),
                                                 ('PERSON','PERSON')],copy=False,default="CUSTOMER",tracking=True,help="Type of partner / customer")
