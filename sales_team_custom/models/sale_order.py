# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_group_sale_salesman = fields.Boolean(compute='_compute_is_group_sale_salesman',
                                            default=lambda self: self._compute_is_group_sale_salesman(is_default=True))

    def _compute_is_group_sale_salesman(self, is_default=False):
        result = self.user_has_groups(
            'sales_team.group_sale_salesman,'
            'sales_team.group_sale_salesman_all_leads,'
            '!sales_team.group_sale_manager')
        if is_default:
            return result
        for rec in self:
            rec.is_group_sale_salesman = result
