from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.tools import float_compare, float_is_zero


class AccountMove(models.Model):
    _inherit = 'account.move'

    release_stock_reservation = fields.Boolean(
        string="Release Stock Reservation",
        copy=False,
        help="When this credit note is posted, release the stock reserved for "
             "the credited quantities in the pending deliveries of the sales order.",
    )

    # ------------------------------------------------------------------
    # OVERRIDES
    # ------------------------------------------------------------------

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered(
            lambda move: move.move_type == 'out_refund' and move.release_stock_reservation
        )._release_stock_reservation()
        return posted

    # ------------------------------------------------------------------
    # BUSINESS METHODS
    # ------------------------------------------------------------------

    def _get_stock_controlled_sale_lines(self):
        """Sales order lines of these invoices whose product requires stock to invoice."""
        return self.invoice_line_ids.sale_line_ids.filtered(
            lambda line: not line.display_type
            and line.product_id.type == 'product'
            and line.product_id.check_stock_before_invoice
        )

    @api.model
    def _get_releasable_moves(self, sale_lines):
        """Pending outgoing moves that hold a reservation that may be released.

        Moves already picked by the warehouse are left alone: the goods are
        being prepared and the reservation is no longer only an accounting matter.
        """
        return sale_lines.move_ids.filtered(
            lambda move: move.state not in ('done', 'cancel')
            and move.picking_code == 'outgoing'
            and not move.picked
            and not float_is_zero(move.quantity, precision_rounding=move.product_uom.rounding)
        )

    def _get_stock_reserved_moves(self):
        """Moves reserved for the controlled lines of these customer invoices."""
        return self._get_releasable_moves(
            self.filtered(lambda move: move.move_type == 'out_invoice')
            ._get_stock_controlled_sale_lines()
        )

    def _release_stock_reservation(self):
        """Release the reservation of the credited quantities.

        For each controlled sales order line, the reservation is reduced by the
        quantity credited, but never below the quantity that is still invoiced
        and not yet delivered: that part is still owed to the customer.
        """
        for credit_note in self:
            released = []
            for sale_line in credit_note._get_stock_controlled_sale_lines():
                uom = sale_line.product_uom
                moves = self._get_releasable_moves(sale_line)
                if not moves:
                    continue
                credited = sum(
                    aml.product_uom_id._compute_quantity(aml.quantity, uom)
                    for aml in credit_note.invoice_line_ids
                    if sale_line in aml.sale_line_ids
                )
                reserved = sum(
                    move.product_uom._compute_quantity(move.quantity, uom)
                    for move in moves
                )
                still_owed = max(sale_line.qty_invoiced - sale_line.qty_delivered, 0.0)
                to_keep = min(reserved, max(reserved - credited, still_owed))
                to_release = reserved - to_keep
                if float_compare(to_release, 0.0, precision_rounding=uom.rounding) <= 0:
                    continue
                credit_note._unreserve_quantity(moves, to_release, uom)
                released.append((sale_line, to_release, moves.picking_id))
            if released:
                credit_note._log_stock_reservation_release(released)

    @api.model
    def _unreserve_quantity(self, moves, quantity, uom):
        """Take ``quantity`` (expressed in ``uom``) back from ``moves``, newest first."""
        remaining = quantity
        for move in moves.sorted('id', reverse=True):
            if float_compare(remaining, 0.0, precision_rounding=uom.rounding) <= 0:
                break
            move_reserved = move.product_uom._compute_quantity(move.quantity, uom)
            if float_compare(remaining, move_reserved, precision_rounding=uom.rounding) >= 0:
                move._do_unreserve()
                remaining -= move_reserved
            else:
                to_take = uom._compute_quantity(remaining, move.product_uom)
                move.with_context(unreserve_unpicked_only=True).quantity = move.quantity - to_take
                move._recompute_state()
                remaining = 0.0

    def _log_stock_reservation_release(self, released):
        """Trace the release on the credit note and on the sales orders."""
        self.ensure_one()
        body = Markup("<p>{header}</p><ul>{lines}</ul>").format(
            header=_(
                "Stock reservation released by %(user)s when posting credit note %(credit_note)s.",
                user=self.env.user.display_name,
                credit_note=self.display_name,
            ),
            lines=Markup().join(
                Markup("<li>{}</li>").format(_(
                    "%(product)s: %(quantity)s %(uom)s released (%(pickings)s)",
                    product=sale_line.product_id.display_name,
                    quantity=quantity,
                    uom=sale_line.product_uom.name,
                    pickings=", ".join(pickings.mapped('name')),
                ))
                for sale_line, quantity, pickings in released
            ),
        )
        self.message_post(body=body)
        orders = self.env['sale.order']
        for sale_line, _quantity, _pickings in released:
            orders |= sale_line.order_id
        for order in orders:
            order.message_post(body=body)
