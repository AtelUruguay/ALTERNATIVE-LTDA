from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CREDIT_NOTE_REASON_SELECTION = [
    ('goods_return', "Goods Return"),
    ('price_adjustment', "Price Adjustment / Discount"),
    ('invoicing_error', "Invoicing Error"),
    ('cancellation', "Cancellation"),
    ('other', "Other"),
]

EXCEPTION_GROUP = 'magna_credit_note_return_control.group_credit_note_return_exception'


class AccountMove(models.Model):
    _inherit = 'account.move'

    credit_note_reason = fields.Selection(
        selection=CREDIT_NOTE_REASON_SELECTION,
        string="Credit Note Reason",
        compute='_compute_credit_note_reason',
        store=True,
        readonly=False,
        copy=False,
        tracking=True,
        help="Reason why this credit note is issued. Required on customer credit notes.",
    )
    return_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string="Return Receipt",
        compute='_compute_return_picking_id',
        store=True,
        readonly=False,
        copy=False,
        tracking=True,
        check_company=True,
        help="Validated receipt proving that the customer returned the goods this "
             "credit note is issued for.",
    )
    available_return_picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string="Available Return Receipts",
        compute='_compute_available_return_picking_ids',
        help="Technical field used to restrict the return receipts that may be selected.",
    )
    return_control_exception_reason = fields.Text(
        string="Return Control Exception",
        copy=False,
        groups=EXCEPTION_GROUP,
        help="Justification for posting a goods-return credit note without a valid "
             "return receipt. Logged in the chatter for audit purposes.",
    )

    # ------------------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------------------

    @api.depends('move_type')
    def _compute_credit_note_reason(self):
        for move in self:
            if move.move_type != 'out_refund':
                move.credit_note_reason = False
            else:
                move.credit_note_reason = move.credit_note_reason

    @api.depends('move_type', 'credit_note_reason')
    def _compute_return_picking_id(self):
        for move in self:
            if move.move_type != 'out_refund' or move.credit_note_reason != 'goods_return':
                move.return_picking_id = False
            else:
                move.return_picking_id = move.return_picking_id

    @api.depends('move_type', 'commercial_partner_id', 'company_id')
    def _compute_available_return_picking_ids(self):
        for move in self:
            if move.move_type == 'out_refund':
                move.available_return_picking_ids = self._get_available_return_pickings(
                    move.commercial_partner_id, move.company_id, credit_note=move,
                )
            else:
                move.available_return_picking_ids = False

    # ------------------------------------------------------------------
    # BUSINESS METHODS
    # ------------------------------------------------------------------

    @api.model
    def _get_available_return_pickings(self, partner, company, credit_note=None):
        """Return the receipts that may back a goods-return credit note.

        A receipt is eligible when it is done, belongs to ``partner`` (or one of
        its contacts) and is not already referenced by another posted credit note.

        :param partner: res.partner the credit note is issued to
        :param company: res.company of the credit note
        :param credit_note: account.move to exclude from the "already used" check
        :return: stock.picking recordset
        """
        pickings = self.env['stock.picking']
        if not partner or not company:
            return pickings
        pickings = pickings.search([
            ('picking_type_code', '=', 'incoming'),
            ('state', '=', 'done'),
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('company_id', '=', company.id),
        ])
        credit_note = credit_note or self.browse()
        return pickings.filtered(
            lambda picking: not picking._get_posted_credit_notes(exclude=credit_note)
        )

    def _get_return_control_errors(self):
        """List the unmet conditions preventing this credit note from being posted."""
        self.ensure_one()
        picking = self.return_picking_id
        if not picking:
            return [_("No return receipt is referenced.")]

        errors = []
        if picking.picking_type_code != 'incoming':
            errors.append(_(
                "Transfer %s is not a receipt.", picking.display_name,
            ))
        if picking.state != 'done':
            errors.append(_(
                "Return receipt %(picking)s is not done yet (current status: %(state)s).",
                picking=picking.display_name,
                state=dict(picking._fields['state']._description_selection(self.env))[picking.state],
            ))
        if picking.partner_id.commercial_partner_id != self.commercial_partner_id:
            errors.append(_(
                "Return receipt %(picking)s belongs to %(picking_partner)s instead of %(partner)s.",
                picking=picking.display_name,
                picking_partner=picking.partner_id.display_name or _("no customer"),
                partner=self.commercial_partner_id.display_name,
            ))
        conflicts = picking._get_posted_credit_notes(exclude=self)
        if conflicts:
            errors.append(_(
                "Return receipt %(picking)s already backs the posted credit note(s) %(credit_notes)s.",
                picking=picking.display_name,
                credit_notes=", ".join(conflicts.mapped('display_name')),
            ))
        return errors

    def _is_return_control_bypassed(self):
        """Whether a supervisor explicitly justified skipping the control."""
        self.ensure_one()
        if not self.env.user.has_group(EXCEPTION_GROUP):
            return False
        return bool(self.return_control_exception_reason)

    def _log_return_control_exception(self, errors):
        """Trace the bypass in the chatter so the exception stays auditable."""
        self.ensure_one()
        self.message_post(body=Markup("<p>{header}</p><ul>{errors}</ul><p>{justification}</p>").format(
            header=_(
                "Return control bypassed by %s.",
                self.env.user.display_name,
            ),
            errors=Markup().join(Markup("<li>{}</li>").format(error) for error in errors),
            justification=_(
                "Justification: %s",
                self.return_control_exception_reason,
            ),
        ))

    def _check_return_control(self):
        """Forbid posting a goods-return credit note without a valid return receipt."""
        for move in self.filtered(lambda move: move.move_type == 'out_refund'):
            if not move.credit_note_reason:
                raise ValidationError(_(
                    "The reason is missing on credit note %s. "
                    "Please set it before posting the credit note.",
                    move.display_name,
                ))
            if move.credit_note_reason != 'goods_return':
                continue
            errors = move._get_return_control_errors()
            if not errors:
                continue
            if move._is_return_control_bypassed():
                move._log_return_control_exception(errors)
                continue
            message = _(
                "Credit note %(move)s is issued for a goods return but the returned "
                "goods cannot be traced back to a valid receipt:",
                move=move.display_name,
            )
            message += "\n\n" + "\n".join("- %s" % error for error in errors)
            if self.env.user.has_group(EXCEPTION_GROUP):
                message += "\n\n" + _(
                    "Fill in the return control exception to post it anyway; the "
                    "justification will be logged in the chatter."
                )
            raise ValidationError(message)

    # ------------------------------------------------------------------
    # CONSTRAINTS
    # ------------------------------------------------------------------

    @api.constrains('return_picking_id', 'partner_id', 'move_type')
    def _check_return_picking_id(self):
        """Give immediate feedback on an inconsistent receipt, before posting."""
        for move in self.filtered('return_picking_id'):
            picking = move.return_picking_id
            if move.move_type != 'out_refund':
                raise ValidationError(_(
                    "A return receipt may only be set on a customer credit note."
                ))
            if picking.picking_type_code != 'incoming':
                raise ValidationError(_(
                    "Transfer %s is not a receipt and cannot back a credit note.",
                    picking.display_name,
                ))
            if picking.partner_id.commercial_partner_id != move.commercial_partner_id:
                raise ValidationError(_(
                    "Return receipt %(picking)s does not belong to %(partner)s.",
                    picking=picking.display_name,
                    partner=move.commercial_partner_id.display_name,
                ))

    # ------------------------------------------------------------------
    # OVERRIDES
    # ------------------------------------------------------------------

    def _post(self, soft=True):
        self._check_return_control()
        return super()._post(soft=soft)
