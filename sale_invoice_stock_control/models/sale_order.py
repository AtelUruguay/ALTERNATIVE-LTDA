from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round

BYPASS_GROUP = 'sale_invoice_stock_control.group_invoice_without_stock'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stock_control_override_reason = fields.Text(
        string="Stock Control Exception",
        copy=False,
        groups=BYPASS_GROUP,
        help="Justification for invoicing this order without enough stock. "
             "Logged in the chatter for audit purposes.",
    )

    # ------------------------------------------------------------------
    # OVERRIDES
    # ------------------------------------------------------------------

    def _create_invoices(self, grouped=False, final=False, date=None):
        # Down payment invoices never reach this method: the advance payment
        # wizard builds them directly, so they are excluded by construction.
        self._check_stock_before_invoicing()
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    # ------------------------------------------------------------------
    # BUSINESS METHODS
    # ------------------------------------------------------------------

    def _get_stock_controlled_moves(self):
        """Pending outgoing moves of the lines that require a stock check."""
        self.ensure_one()
        lines = self.order_line.filtered(
            lambda line: not line.display_type
            and line.product_id.type == 'product'
            and line.product_id.check_stock_before_invoice
        )
        return lines.move_ids.filtered(
            lambda move: move.state not in ('done', 'cancel')
            and move.picking_code == 'outgoing'
        )

    def _get_stock_shortages(self, moves):
        """Lines whose pending quantity could not be reserved in full.

        :param moves: stock.move recordset already through ``_action_assign()``
        :return: list of dicts with product, demand, reserved, missing and uom
        """
        self.ensure_one()
        shortages = []
        for line in moves.sale_line_id:
            line_moves = moves.filtered(lambda move: move.sale_line_id == line)
            uom = line_moves[0].product_uom
            demand = sum(line_moves.mapped('product_uom_qty'))
            reserved = sum(line_moves.mapped('quantity'))
            if float_compare(reserved, demand, precision_rounding=uom.rounding) >= 0:
                continue
            shortages.append({
                'product': line.product_id,
                'demand': demand,
                'reserved': reserved,
                'missing': float_round(
                    demand - reserved, precision_rounding=uom.rounding),
                'uom': uom,
            })
        return shortages

    def _release_own_reservations(self, moves, reserved_before):
        """Undo only the reservation this check created.

        A move that the warehouse had already reserved by hand is left alone;
        we never take back what somebody else committed. Raising afterwards
        rolls the transaction back anyway, so this matters only if a caller
        swallows the error.

        :param reserved_before: {move id: reserved quantity before the check}
        """
        untouched = moves.filtered(
            lambda move: not reserved_before.get(move.id)
        )
        untouched._do_unreserve()

    def _is_stock_control_bypassed(self):
        """Whether an authorised user explicitly justified invoicing anyway."""
        self.ensure_one()
        if not self.env.user.has_group(BYPASS_GROUP):
            return False
        return bool(self.stock_control_override_reason)

    def _format_stock_shortages(self, shortages):
        return [
            _(
                "%(product)s: %(demand)s needed, %(reserved)s reserved, "
                "%(missing)s missing (%(uom)s)",
                product=shortage['product'].display_name,
                demand=shortage['demand'],
                reserved=shortage['reserved'],
                missing=shortage['missing'],
                uom=shortage['uom'].name,
            )
            for shortage in shortages
        ]

    def _log_stock_control_exception(self, shortages):
        """Trace the bypass in the chatter so the exception stays auditable."""
        self.ensure_one()
        self.message_post(body=Markup(
            "<p>{header}</p><ul>{shortages}</ul><p>{justification}</p>"
        ).format(
            header=_(
                "Stock control bypassed by %s when creating the invoice.",
                self.env.user.display_name,
            ),
            shortages=Markup().join(
                Markup("<li>{}</li>").format(line)
                for line in self._format_stock_shortages(shortages)
            ),
            justification=_(
                "Justification: %s", self.stock_control_override_reason,
            ),
        ))

    def _check_stock_before_invoicing(self):
        """Forbid invoicing an order whose flagged lines cannot be reserved."""
        for order in self:
            moves = order._get_stock_controlled_moves()
            if not moves:
                continue

            reserved_before = {move.id: move.quantity for move in moves}
            # Reservation happens here and nowhere else: the outgoing operation
            # types are set to manual reservation on purpose.
            moves._action_assign()

            shortages = order._get_stock_shortages(moves)
            if not shortages:
                continue

            if order._is_stock_control_bypassed():
                order._log_stock_control_exception(shortages)
                continue

            order._release_own_reservations(moves, reserved_before)
            message = _(
                "The order %s cannot be invoiced: there is not enough stock to "
                "reserve the full quantity of these lines.",
                order.name,
            )
            message += "\n\n" + "\n".join(
                "- %s" % line for line in order._format_stock_shortages(shortages))
            message += "\n\n" + _(
                "Adjust the quantities on the sales order, or ask for an "
                "authorisation to invoice without stock."
            )
            raise UserError(message)
